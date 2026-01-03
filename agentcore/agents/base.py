# =============================================================================
# MAGIエージェント基底クラス
# =============================================================================
#
# このモジュールは、MAGIシステムの3つのエージェント（MELCHIOR, BALTHASAR, CASPER）の
# 基底クラスと、判定結果を統合するJudgeComponentを提供します。
#
# 主要コンポーネント:
# - AgentVerdict: エージェントの判定結果（Pydanticモデル）
# - AgentResponse: 会話モード回答（Pydanticモデル、Phase 2で使用）
# - FinalVerdict: 最終統合判定（Pydanticモデル）
# - JudgeSummary: JUDGE統合分析結果（Pydanticモデル）
# - MAGIAgent: エージェント基底クラス（同期/非同期分析メソッド）
# - MelchiorAgent: 科学者エージェント
# - BalthasarAgent: 母親エージェント
# - CasperAgent: 女性エージェント
# - JudgeComponent: 多数決＋LLM統合分析による判定統合
#
# 使用するStrands SDK機能:
# - BedrockModel: Amazon BedrockのLLMモデルラッパー
# - Agent: LLMエージェントの基本単位
# - structured_output(): 構造化出力（同期版）
# - stream_async(): ストリーミング出力（非同期版）
#
# =============================================================================
# LLM呼び出しポイント一覧
# =============================================================================
#
# このファイルでLLMが呼び出される箇所:
#
# 1. MAGIAgent.analyze() メソッド（同期版）
#    - 呼び出し: self.agent.structured_output(AgentVerdict, prompt)
#    - 処理: プロンプトをLLMに送信 → 構造化された判定結果を取得
#    - 用途: 各エージェント（MELCHIOR/BALTHASAR/CASPER）の判定
#    - LLM呼び出し回数: 1回
#
# 2. MAGIAgent.analyze_stream() メソッド（非同期版）
#    - 呼び出し: self.agent.stream_async(prompt, structured_output_model=AgentVerdict)
#    - 処理: プロンプトをLLMに送信 → イベントをストリーミングで取得
#    - 用途: 各エージェントの判定（思考プロセス表示付き）
#    - LLM呼び出し回数: 1回（SDK 1.21.0以降）
#
# 3. JudgeComponent.integrate_with_analysis() メソッド
#    - 呼び出し: self.agent.structured_output(JudgeSummary, prompt)
#    - 処理: 3エージェントの判定を受け取り、統合分析を実行
#    - 用途: 最終判定のサマリー・論点・推奨事項を生成
#    - LLM呼び出し回数: 1回
#
# =============================================================================
# 全体のLLM呼び出しフロー（backend.py視点）
# =============================================================================
#
# run_judge_mode_stream() では以下の順序でLLMを呼び出す:
#
# 1. MELCHIOR-1.analyze_stream() → 【LLM呼び出し 1回目】
# 2. BALTHASAR-2.analyze_stream() → 【LLM呼び出し 2回目】
# 3. CASPER-3.analyze_stream() → 【LLM呼び出し 3回目】
# 4. JudgeComponent.integrate_with_analysis() → 【LLM呼び出し 4回目】
#
# 合計: 4回のLLM呼び出し
#
# 注意: SDK 1.13.0以前では stream_async() 後に structured_output() を
#       別途呼び出す必要があり、LLM呼び出しが2回になる問題があった
# =============================================================================

from strands import Agent
from strands.models.bedrock import BedrockModel
from pydantic import BaseModel, Field
from typing import AsyncGenerator


# =============================================================================
# Pydanticモデル（構造化出力用）
# =============================================================================
#
# これらのモデルは、LLMの出力を構造化するために使用されます。
# Field(description=...) でLLMに出力形式を伝えます。
# =============================================================================

class AgentVerdict(BaseModel):
    """
    エージェントの判定結果

    LLMがこの形式で出力するよう、structured_output_model として指定します。
    descriptionはLLMへのヒントとして機能します。

    Attributes:
        agent_name: エージェント名（例: "MELCHIOR-1"）
        verdict: 判定結果（"賛成" または "反対"）
        reasoning: 判定理由（200文字以内）
        confidence: 確信度（0.0〜1.0）
    """
    agent_name: str = Field(description="エージェント名")
    verdict: str = Field(description="賛成 または 反対")
    reasoning: str = Field(description="判定理由（200文字以内）")
    confidence: float = Field(ge=0.0, le=1.0, description="確信度")


class AgentResponse(BaseModel):
    """
    エージェントの会話モード回答（Phase 2で使用予定）

    Attributes:
        agent_name: エージェント名
        response: 回答内容
    """
    agent_name: str = Field(description="エージェント名")
    response: str = Field(description="回答内容")


class FinalVerdict(BaseModel):
    """
    最終判定結果（JudgeComponentが生成）

    3エージェントの判定を多数決で統合した結果を格納します。

    Attributes:
        verdict: 最終判定（"承認" | "否決" | "保留"）
        summary: 統合サマリー
        vote_count: 投票数 {'賛成': n, '反対': m}
        agent_verdicts: 各エージェントの判定リスト
    """
    verdict: str = Field(description="承認 | 否決 | 保留")
    summary: str = Field(description="統合サマリー")
    vote_count: dict = Field(description="投票数 {'賛成': n, '反対': m}")
    agent_verdicts: list[AgentVerdict] = Field(description="各エージェントの判定")


# =============================================================================
# MAGIエージェント基底クラス
# =============================================================================

class MAGIAgent:
    """
    MAGIエージェントの基底クラス

    3つのエージェント（MELCHIOR, BALTHASAR, CASPER）の共通機能を提供します。
    サブクラスは _build_system_prompt() をオーバーライドして
    固有のペルソナを定義します。

    Attributes:
        name: エージェント名
        persona: ペルソナ説明文
        model_id: 使用するBedrockモデルID
        agent: Strands Agentインスタンス

    Methods:
        analyze(): 同期版の分析（Step 1で実装）
        analyze_stream(): 非同期ストリーミング版の分析（Step 2で実装）
    """

    def __init__(
        self,
        name: str,
        persona: str,
        model_id: str = "jp.anthropic.claude-haiku-4-5-20251001-v1:0"
    ):
        """
        エージェントを初期化

        Args:
            name: エージェント名（例: "MELCHIOR-1"）
            persona: ペルソナ説明文
            model_id: BedrockモデルID（デフォルト: Claude Haiku）
        """
        self.name = name
        self.persona = persona
        self.model_id = model_id

        # ---------------------------------------------------------------------
        # BedrockModelの作成
        # ---------------------------------------------------------------------
        # ※ここではLLMを呼び出していない（モデルの設定のみ）
        # Amazon BedrockのLLMモデルをラップするクラス
        # region_name: AWSリージョン（東京リージョンを使用）
        model = BedrockModel(
            model_id=model_id,
            region_name="ap-northeast-1"  # 東京リージョン
        )

        # ---------------------------------------------------------------------
        # Agentの作成
        # ---------------------------------------------------------------------
        # ※ここではLLMを呼び出していない（エージェントの設定のみ）
        # callback_handler=None:
        #   デフォルトのコンソール出力を無効化
        #   これにより、stream_async()のイベントを自分で制御できる
        #   Windowsでの文字化け・絵文字エラーも回避できる
        self.agent = Agent(
            model=model,
            system_prompt=self._build_system_prompt(),
            callback_handler=None  # ストリーミング時はデフォルトコールバックを無効化
        )

    def _build_system_prompt(self) -> str:
        """
        ペルソナに基づくシステムプロンプトを構築

        サブクラスでオーバーライドして、固有のプロンプトを返すことも可能。

        Returns:
            システムプロンプト文字列
        """
        return f"""あなたはMAGIシステムの{self.name}です。
        {self.persona}

        ## 分析の指針
        - あなたの人格・立場に基づいた独自の視点で判断してください
        - 論理的な理由を明確に述べてください
        - 他のエージェントとは異なる観点を大切にしてください

        ## 出力形式
        判定は「賛成」または「反対」のいずれかで回答してください。
        理由は200文字以内で簡潔に述べてください。
        確信度は0.0〜1.0の数値で示してください。
        """

    # =========================================================================
    # Step 1: 同期版分析メソッド
    # =========================================================================

    def analyze(self, question: str) -> AgentVerdict:
        """
        問いかけを分析し判定を返す（同期版）

        structured_output() を使用して、LLMの出力をAgentVerdict形式で取得します。
        ストリーミングなしで、完了まで待機します。

        Args:
            question: 分析対象の問いかけ

        Returns:
            AgentVerdict: 構造化された判定結果
        """
        prompt = f"以下の問いかけを分析してください: {question}"

        # =====================================================================
        # 【LLM呼び出し①】structured_output() で LLM を呼び出し
        # =====================================================================
        # ここで Amazon Bedrock の Claude モデルに対してリクエストを送信
        # - 送信内容: prompt（ユーザーの問いかけ）+ system_prompt（エージェントのペルソナ）
        # - 受信内容: AgentVerdict 形式の構造化された判定結果
        # - 呼び出し回数: 1回
        # - 待機: レスポンスが返るまでブロッキング
        return self.agent.structured_output(
            AgentVerdict,  # 出力の型（LLMにこの形式で返すよう指示）
            prompt         # プロンプト（LLMへの入力）
        )

    # =========================================================================
    # Step 2: 非同期ストリーミング版分析メソッド
    # =========================================================================

    async def analyze_stream(self, question: str) -> AsyncGenerator[dict, None]:
        """
        問いかけを分析し、思考プロセスをリアルタイムで返す（非同期ストリーミング版）

        SDK 1.21.0以降の機能:
        - stream_async() に structured_output_model を渡すことで
        - 1回のLLM呼び出しでストリーミング＋構造化出力を取得
        - result イベントから .structured_output で判定結果を取得

        イベントフロー:
        1. init_event_loop → {"type": "init"}
        2. start_event_loop → {"type": "loop_start"}
        3. data → {"type": "thinking", "content": "..."} (複数回)
        4. complete → {"type": "complete"}
        5. result → {"type": "verdict", "data": {...}}

        Args:
            question: 分析対象の問いかけ

        Yields:
            dict: イベント辞書
                - {"type": "init"}: 初期化
                - {"type": "loop_start"}: ループ開始
                - {"type": "thinking", "content": str}: 思考プロセス（リアルタイム）
                - {"type": "reasoning", "content": str}: 推論（Interleaved Thinking時）
                - {"type": "tool_use", "name": str}: ツール使用
                - {"type": "complete"}: 完了
                - {"type": "verdict", "data": dict}: 最終判定（AgentVerdict形式）
        """
        prompt = f"以下の問いかけを分析してください: {question}"

        # =====================================================================
        # 【LLM呼び出し②】stream_async() で LLM を呼び出し（ストリーミング）
        # =====================================================================
        # ここで Amazon Bedrock の Claude モデルに対してリクエストを送信
        # - 送信内容: prompt（ユーザーの問いかけ）+ system_prompt（エージェントのペルソナ）
        # - 受信内容: イベントのストリーム（思考プロセス → 判定結果）
        # - 呼び出し回数: 1回（SDK 1.21.0以降）
        # - 待機: async for で各イベントを順次受信
        #
        # structured_output_model パラメータ:
        #   - LLMの出力をAgentVerdict形式に制約
        #   - result イベントで .structured_output として取得可能
        async for event in self.agent.stream_async(
            prompt,
            structured_output_model=AgentVerdict
        ):
            # -----------------------------------------------------------------
            # SDKイベント → カスタムイベントに変換
            # -----------------------------------------------------------------

            # init_event_loop: エージェント呼び出し開始時に発火
            if event.get("init_event_loop"):
                yield {"type": "init"}

            # start_event_loop: イベントループ開始時に発火
            if event.get("start_event_loop"):
                yield {"type": "loop_start"}

            # data: テキストチャンク（LLMからのリアルタイム出力）
            # ※ここで思考プロセスがストリーミングで届く
            if "data" in event:
                yield {"type": "thinking", "content": event["data"]}

            # reasoning: 推論イベント（Interleaved Thinking有効時のみ）
            if event.get("reasoning") and "reasoningText" in event:
                yield {"type": "reasoning", "content": event["reasoningText"]}

            # current_tool_use: ツール使用情報
            if "current_tool_use" in event:
                tool_info = event["current_tool_use"]
                if tool_info.get("name"):
                    yield {"type": "tool_use", "name": tool_info["name"]}

            # complete: サイクル完了時に発火
            if event.get("complete"):
                yield {"type": "complete"}

            # result: 最終結果イベント（ストリーミング終了時）
            # ※ここで構造化された判定結果を取得
            if "result" in event:
                result = event["result"]
                # SDK 1.21.0以降: structured_output 属性で判定結果を取得
                if hasattr(result, "structured_output") and result.structured_output:
                    # model_dump(): Pydanticモデルを辞書に変換
                    yield {"type": "verdict", "data": result.structured_output.model_dump()}


# =============================================================================
# MELCHIORエージェントクラス
# =============================================================================

class MelchiorAgent(MAGIAgent):
    """
    科学者の人格を持つエージェント（MELCHIOR-1）

    赤木ナオコ博士の科学者としての側面を表現。
    論理的整合性、科学的根拠、データに基づく客観的判断を重視。
    """

    SYSTEM_PROMPT = """
    あなたはMAGIシステムのMELCHIOR-1です。
    赤木ナオコ博士の科学者としての人格を持ちます。

    分析の観点：
    - 論理的整合性
    - 科学的根拠
    - データに基づく客観的判断
    - リスクの定量的評価
    """

    def __init__(self):
        """科学者エージェントを初期化"""
        super().__init__(
            name="MELCHIOR-1",
            persona="赤木ナオコ博士の科学者としての人格を持ちます。"
        )

    def _build_system_prompt(self) -> str:
        """固有のシステムプロンプトを返す"""
        return self.SYSTEM_PROMPT


# =============================================================================
# BALTHASARエージェントクラス
# =============================================================================

class BalthasarAgent(MAGIAgent):
    """
    母親の人格を持つエージェント（BALTHASAR-2）

    赤木ナオコ博士の母親としての側面を表現。
    安全性と保護、長期的な影響、関係者への配慮を重視。
    """

    SYSTEM_PROMPT = """
    あなたはMAGIシステムのBALTHASAR-2です。
    赤木ナオコ博士の母親としての人格を持ちます。

    分析の観点：
    - 安全性と保護
    - 長期的な影響
    - 関係者への配慮
    - リスク回避
    """

    def __init__(self):
        """母親エージェントを初期化"""
        super().__init__(
            name="BALTHASAR-2",
            persona="赤木ナオコ博士の母親としての人格を持ちます。"
        )

    def _build_system_prompt(self) -> str:
        """固有のシステムプロンプトを返す"""
        return self.SYSTEM_PROMPT


# =============================================================================
# CASPERエージェントクラス
# =============================================================================

class CasperAgent(MAGIAgent):
    """
    女性の人格を持つエージェント（CASPER-3）

    赤木ナオコ博士の女性としての側面を表現。
    人間的な感情、社会的影響、倫理的配慮、共感と理解を重視。
    """

    SYSTEM_PROMPT = """
    あなたはMAGIシステムのCASPER-3です。
    赤木ナオコ博士の女性としての人格を持ちます。

    分析の観点：
    - 人間的な感情
    - 社会的影響
    - 倫理的配慮
    - 共感と理解
    """

    def __init__(self):
        """女性エージェントを初期化"""
        super().__init__(
            name="CASPER-3",
            persona="赤木ナオコ博士の女性としての人格を持ちます。"
        )

    def _build_system_prompt(self) -> str:
        """固有のシステムプロンプトを返す"""
        return self.SYSTEM_PROMPT


# =============================================================================
# JudgeSummary（JUDGE統合分析結果）
# =============================================================================

class JudgeSummary(BaseModel):
    """
    JUDGEによる統合分析結果（LLMが生成）

    Attributes:
        summary: 3エージェントの意見を踏まえた統合的な分析サマリー
        key_points: 主要な論点（箇条書き）
        recommendation: 最終的な推奨事項
    """
    summary: str = Field(description="3エージェントの意見を踏まえた統合的な分析サマリー（200文字程度）")
    key_points: list[str] = Field(description="主要な論点を3つ程度の箇条書きで")
    recommendation: str = Field(description="最終的な推奨事項（100文字程度）")


# =============================================================================
# JudgeComponent（LLM as a Judge）
# =============================================================================

class JudgeComponent:
    """
    3エージェントの判定を統合するコンポーネント

    機能:
    1. 多数決ロジックで最終判定（承認/否決/保留）を決定
    2. LLMを使って3エージェントの意見を統合分析

    Attributes:
        agent: JUDGE用のLLMエージェント（統合分析用）
    """

    SYSTEM_PROMPT = """
    あなたはMAGIシステムのJUDGE（統合判定官）です。
    3つのエージェント（MELCHIOR-1: 科学者、BALTHASAR-2: 母親、CASPER-3: 女性）の
    判定結果を受け取り、それらを統合的に分析します。

    あなたの役割:
    - 各エージェントの観点を公平に考慮する
    - 共通点と相違点を明確にする
    - 建設的な統合サマリーを作成する
    - 具体的で実行可能な推奨事項を提示する

    注意:
    - 最終判定（承認/否決/保留）は多数決で既に決定されています
    - あなたの役割はその判定を踏まえた分析と推奨事項の提示です
    """

    def __init__(self, model_id: str = "jp.anthropic.claude-haiku-4-5-20251001-v1:0"):
        """
        JUDGEコンポーネントを初期化

        Args:
            model_id: 使用するBedrockモデルID
        """
        model = BedrockModel(
            model_id=model_id,
            region_name="ap-northeast-1"
        )
        self.agent = Agent(
            model=model,
            system_prompt=self.SYSTEM_PROMPT,
            callback_handler=None
        )

    def _count_votes(self, verdicts: list[AgentVerdict]) -> tuple[int, int, str]:
        """
        投票をカウントして最終判定を決定

        Returns:
            tuple: (賛成数, 反対数, 最終判定)
        """
        approve_count = 0
        reject_count = 0
        for v in verdicts:
            if "賛成" in v.verdict:
                approve_count += 1
            elif "反対" in v.verdict:
                reject_count += 1

        if approve_count > reject_count:
            final = "承認"
        elif approve_count < reject_count:
            final = "否決"
        else:
            final = "保留"

        return approve_count, reject_count, final

    def integrate(self, verdicts: list[AgentVerdict]) -> FinalVerdict:
        """
        多数決で最終判定を決定（LLMなしの軽量版）

        Args:
            verdicts: 各エージェントの判定リスト

        Returns:
            FinalVerdict: 統合された最終判定
        """
        approve_count, reject_count, final = self._count_votes(verdicts)

        return FinalVerdict(
            verdict=final,
            summary="各エージェントの意見を統合しました。",
            vote_count={"賛成": approve_count, "反対": reject_count},
            agent_verdicts=verdicts
        )

    def integrate_with_analysis(self, question: str, verdicts: list[AgentVerdict]) -> FinalVerdict:
        """
        LLMを使って3エージェントの意見を統合分析

        多数決で最終判定（承認/否決/保留）を決定した後、
        LLMを使って統合的な分析サマリーを生成します。

        処理フロー:
        1. _count_votes() で多数決判定
        2. 各エージェントの判定をプロンプトに整形
        3. LLM（structured_output）で JudgeSummary を生成
        4. JudgeSummary を FinalVerdict.summary にフォーマット

        Args:
            question: 元の問いかけ（ユーザーの質問）
            verdicts: 各エージェントの判定リスト（3つ）

        Returns:
            FinalVerdict: LLMによる統合分析を含む最終判定
                - verdict: "承認" | "否決" | "保留"（多数決）
                - summary: 統合サマリー + 主要な論点 + 推奨事項（LLM生成）
                - vote_count: {"賛成": n, "反対": m}
                - agent_verdicts: 各エージェントの判定
        """
        # ---------------------------------------------------------------------
        # 1. 多数決で最終判定を決定
        # ---------------------------------------------------------------------
        approve_count, reject_count, final = self._count_votes(verdicts)

        # ---------------------------------------------------------------------
        # 2. LLMに統合分析を依頼
        # ---------------------------------------------------------------------
        # 各エージェントの判定を文字列にフォーマット
        verdicts_text = ""
        for v in verdicts:
            verdicts_text += f"""
【{v.agent_name}】
- 判定: {v.verdict}
- 理由: {v.reasoning}
- 確信度: {v.confidence}
"""

        prompt = f"""
以下の問いかけに対する3エージェントの判定を統合分析してください。

## 問いかけ
{question}

## 各エージェントの判定
{verdicts_text}

## 多数決結果
- 賛成: {approve_count}票
- 反対: {reject_count}票
- 最終判定: {final}

上記を踏まえ、統合的な分析サマリー、主要な論点、推奨事項を作成してください。
"""

        # =====================================================================
        # 【LLM呼び出し④】JUDGE統合分析
        # =====================================================================
        # ここで Amazon Bedrock の Claude モデルに対してリクエストを送信
        # - 送信内容: prompt（3エージェントの判定結果）+ system_prompt（JUDGE役割）
        # - 受信内容: JudgeSummary 形式の構造化された統合分析
        # - 出力: summary（サマリー）, key_points（論点）, recommendation（推奨事項）
        # - 呼び出し回数: 1回
        # - 待機: レスポンスが返るまでブロッキング
        judge_summary = self.agent.structured_output(JudgeSummary, prompt)

        # ---------------------------------------------------------------------
        # 3. 統合サマリーを作成
        # ---------------------------------------------------------------------
        # key_pointsを箇条書きに変換
        key_points_text = "\n".join([f"・{point}" for point in judge_summary.key_points])

        full_summary = f"""{judge_summary.summary}

【主要な論点】
{key_points_text}

【推奨事項】
{judge_summary.recommendation}"""

        return FinalVerdict(
            verdict=final,
            summary=full_summary,
            vote_count={"賛成": approve_count, "反対": reject_count},
            agent_verdicts=verdicts
        )
