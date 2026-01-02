# コードスナップショット（Step 1 完了時点）

このファイルは、Step 1（同期版）完了時点でのコードを保存しています。
後日参照用として使用してください。

**更新日:** Step 1 完了後

---

## agentcore/agents/base.py

```python
# MAGIエージェント基底クラス

from strands import Agent
from strands.models.bedrock import BedrockModel
from pydantic import BaseModel, Field


# =============================================================================
# Pydanticモデル（構造化出力用）
# =============================================================================

class AgentVerdict(BaseModel):
    """エージェントの判定結果"""
    agent_name: str = Field(description="エージェント名")
    verdict: str = Field(description="賛成 または 反対")
    reasoning: str = Field(description="判定理由（200文字以内）")
    confidence: float = Field(ge=0.0, le=1.0, description="確信度")


class AgentResponse(BaseModel):
    """エージェントの会話モード回答"""
    agent_name: str = Field(description="エージェント名")
    response: str = Field(description="回答内容")

class FinalVerdict(BaseModel):
    """最終判定結果"""
    verdict: str = Field(description="承認 | 否決 | 保留")
    summary: str = Field(description="統合サマリー")
    vote_count: dict = Field(description="投票数 {'賛成': n, '反対': m}")
    agent_verdicts: list[AgentVerdict] = Field(description="各エージェントの判定")


# =============================================================================
# MAGIエージェント基底クラス
# =============================================================================

class MAGIAgent:
    """MAGIエージェントの基底クラス"""

    def __init__(self, name: str, persona: str, model_id: str = "jp.anthropic.claude-haiku-4-5-20251001-v1:0"):
        self.name = name
        self.persona = persona
        self.model_id = model_id

        # BedrockModelを作成してAgentに渡す
        model = BedrockModel(
            model_id=model_id,
            region_name="ap-northeast-1"  # 東京リージョン
        )

        self.agent = Agent(
            model=model,
            system_prompt=self._build_system_prompt()
        )

    def _build_system_prompt(self) -> str:
        """ペルソナに基づくシステムプロンプトを構築"""
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

    def analyze(self, question: str) -> AgentVerdict:
        """問いかけを分析し判定を返す"""
        return self.agent.structured_output(
            AgentVerdict,                                      # 第1引数: 出力の型
            f"以下の問いかけを分析してください: {question}"      # 第2引数: プロンプト
            )

# =============================================================================
# MELCHIORエージェントクラス
# =============================================================================

class MelchiorAgent(MAGIAgent):
    """科学者の人格を持つエージェント"""

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
        super().__init__(
            name ="MELCHIOR-1",
            persona ="赤木ナオコ博士の科学者としての人格を持ちます。"
        )

    def _build_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

# =============================================================================
# BALTHASARエージェントクラス
# =============================================================================

class BalthasarAgent(MAGIAgent):
    """母親の人格を持つエージェント"""

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
        super().__init__(
            name="BALTHASAR-2",
            persona="赤木ナオコ博士の母親としての人格を持ちます。"
        )

    def _build_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

# =============================================================================
# CASPERエージェントクラス
# =============================================================================

class CasperAgent(MAGIAgent):
    """女性の人格を持つエージェント"""

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
        super().__init__(
            name="CASPER-3",
            persona="赤木ナオコ博士の女性としての人格を持ちます。"
        )

    def _build_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT




# =============================================================================
# LLM as a Judgeのエージェントクラス
# =============================================================================
class JudgeComponent:
    """3エージェントの判定を統合"""

    def integrate(self, verdicts: list[AgentVerdict]) -> FinalVerdict:
        """多数決で最終判定を決定"""
        # 1. 賛成/反対をカウント（部分一致で柔軟に検出）
        approve_count = 0
        reject_count = 0
        for v in verdicts:
            if "賛成" in v.verdict:
                approve_count += 1
            elif "反対" in v.verdict:
                reject_count += 1

        # 2. 多数決で判定
        if approve_count > reject_count:
            final = "承認"
        elif approve_count < reject_count:
            final = "否決"
        else:
            final = "保留"

        # 3. FinalVerdictを返す
        return FinalVerdict(
            verdict=final,
            summary="各エージェントの意見を統合しました。",
            vote_count={"賛成": approve_count, "反対": reject_count},
            agent_verdicts=verdicts
        )
```

---

## agentcore/backend.py（Step 1: 同期版）

```python
# backend.py - MAGIシステム バックエンド

from agents.base import (
    MelchiorAgent,
    BalthasarAgent,
    CasperAgent,
    JudgeComponent,
    FinalVerdict
)


def run_judge_mode(question: str) -> FinalVerdict:
    """判定モード: 3エージェント → JUDGE → 最終判定"""

    # 1. エージェント作成
    melchior = MelchiorAgent()
    balthasar = BalthasarAgent()
    casper = CasperAgent()


    # 2. 各エージェントで分析
    # リストとforループを使う
    agents = [melchior, balthasar, casper]
    verdicts = []
    for agent in agents:
        verdict = agent.analyze(question)
        verdicts.append(verdict)

    # 3. JUDGEで統合
    # JudgeComponent をインスタンス化して、integrate() を呼ぶ
    judge = JudgeComponent()
    # verdicts リストを渡す
    final_verdict = judge.integrate(verdicts)

    # 4. 結果を返す
    # integrate() の戻り値を return する
    return final_verdict


if __name__ == "__main__":
    result = run_judge_mode("AIを業務に導入すべきか？")

    # 各エージェントの判定を確認
    for v in result.agent_verdicts:
        print(f"{v.agent_name}: {v.verdict} ({v.confidence})")
        print(f"  理由: {v.reasoning}")
        print()

    print(f"最終判定: {result.verdict}")
    print(f"投票結果: {result.vote_count}")
    print(f"要約: {result.summary}")
```

---

## 学習メモ

### 1. `in`演算子の順序（重要！）

```python
# ❌ 間違い: 長い文字列が短い文字列に含まれるかチェック
if v.verdict in "賛成":       # "条件付き賛成" in "賛成" → False

# ✅ 正しい: 短い文字列が長い文字列に含まれるかチェック
if "賛成" in v.verdict:       # "賛成" in "条件付き賛成" → True
```

### 2. ジェネレータ式

```python
# この書き方
approve_count = sum(1 for v in verdicts if "賛成" in v.verdict)

# は、以下と同じ意味
approve_count = 0
for v in verdicts:
    if "賛成" in v.verdict:
        approve_count += 1
```

### 3. クラス継承の流れ

```
MelchiorAgent.__init__()
    ↓
super().__init__(name, persona)  # 親クラスを呼び出す
    ↓
MAGIAgent.__init__(name, persona, model_id)
    ↓
self._build_system_prompt()  # ← MelchiorAgentでオーバーライドされている！
    ↓
MelchiorAgent._build_system_prompt()  # 子クラスのメソッドが呼ばれる
```

### 4. 動作確認済みのモデル設定

```python
# 東京リージョン + Haiku 4.5 = 動作OK
model = BedrockModel(
    model_id="jp.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="ap-northeast-1"
)
```

---

## 次のステップ

- **Step 2:** ストリーミング版（`stream_async()`）
- **Step 3:** イベント処理（thinking, tool_use, reasoning）
