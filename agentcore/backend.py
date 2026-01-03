# =============================================================================
# backend.py - MAGIシステム バックエンド
# =============================================================================
#
# このモジュールは、MAGIシステムのバックエンド処理を提供します。
# 3つのエージェント（MELCHIOR, BALTHASAR, CASPER）を実行し、
# JudgeComponentで最終判定を統合します。
#
# 主要関数:
# - run_judge_mode(): 同期版判定モード（Step 1）
# - run_judge_mode_stream(): 非同期ストリーミング版判定モード（Step 2）
# - main(): テスト実行用エントリーポイント
#
# 実行方法:
#   cd agentcore && python backend.py
#
# =============================================================================
# LLM呼び出しフロー（このファイル視点）
# =============================================================================
#
# run_judge_mode() / run_judge_mode_stream() は以下の順序でLLMを呼び出す:
#
# 1. MELCHIOR-1 の analyze() / analyze_stream() → 【LLM呼び出し 1回目】
# 2. BALTHASAR-2 の analyze() / analyze_stream() → 【LLM呼び出し 2回目】
# 3. CASPER-3 の analyze() / analyze_stream() → 【LLM呼び出し 3回目】
# 4. JudgeComponent.integrate() → LLM呼び出しなし（多数決ロジックのみ）
#
# 合計: 3回のLLM呼び出し（各エージェントで1回ずつ）
#
# =============================================================================

from agents.base import (
    MelchiorAgent,
    BalthasarAgent,
    CasperAgent,
    JudgeComponent,
    FinalVerdict,
    AgentVerdict
)

import asyncio
from typing import AsyncGenerator

# AgentCoreAppのインポート
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# AgentCoreAppのインスタンス化
app = BedrockAgentCoreApp()  

# =============================================================================
# Step 1: 同期版判定モード
# =============================================================================

def run_judge_mode(question: str) -> FinalVerdict:
    """
    同期判定モード: 3エージェント → JUDGE → 最終判定

    各エージェントが順番に分析を行い、全員の判定が揃ったら
    JudgeComponentで多数決により最終判定を出します。

    処理フロー:
    1. 3エージェント作成（MELCHIOR, BALTHASAR, CASPER）
    2. 各エージェントで analyze() を実行
    3. 全員の判定を収集
    4. JUDGEで統合 → FinalVerdict

    Args:
        question: 分析対象の問いかけ

    Returns:
        FinalVerdict: 最終判定結果
    """
    # -------------------------------------------------------------------------
    # 1. エージェント作成
    # -------------------------------------------------------------------------
    # 各エージェントは固有のペルソナを持つ
    melchior = MelchiorAgent()   # 科学者
    balthasar = BalthasarAgent()  # 母親
    casper = CasperAgent()        # 女性

    # -------------------------------------------------------------------------
    # 2. 各エージェントで分析
    # -------------------------------------------------------------------------
    # リストにまとめてforループで処理
    agents = [melchior, balthasar, casper]
    verdicts = []
    for agent in agents:
        # =================================================================
        # 【LLM呼び出し】ここで agent.analyze() を実行
        # =================================================================
        # - 呼び出し先: agents/base.py の MAGIAgent.analyze()
        # - 内部処理: self.agent.structured_output() で Bedrock Claude を呼び出し
        # - 送信内容: question（ユーザーの問いかけ）+ システムプロンプト
        # - 受信内容: AgentVerdict（判定結果の構造化データ）
        verdict = agent.analyze(question)
        verdicts.append(verdict)

    # -------------------------------------------------------------------------
    # 3. JUDGEで統合
    # -------------------------------------------------------------------------
    # ※ここではLLMを呼び出していない（多数決ロジックのみ）
    # - 3エージェントの判定を集計
    # - 賛成 > 反対 → 承認、賛成 < 反対 → 否決、同数 → 保留
    judge = JudgeComponent()
    final_verdict = judge.integrate(verdicts)

    # -------------------------------------------------------------------------
    # 4. 結果を返す
    # -------------------------------------------------------------------------
    return final_verdict


# =============================================================================
# Step 2: 非同期ストリーミング版判定モード
# =============================================================================

async def run_judge_mode_stream(question: str) -> AsyncGenerator[dict, None]:
    """
    非同期判定モード: 3エージェント → JUDGE → 最終判定（ストリーミング版）

    各エージェントの思考プロセスをリアルタイムでyieldしながら、
    最終的にJUDGEで判定を統合します。

    処理フロー:
    1. 3エージェント作成
    2. 各エージェントで analyze_stream() を実行
       - 思考プロセスをリアルタイムでyield
       - 判定結果をverdictsリストに収集
    3. 全員完了後に JUDGE で統合

    イベントフロー:
    ┌─────────────────────────────────────────────────────────────┐
    │ agent_start → thinking... → verdict → agent_complete       │
    │ agent_start → thinking... → verdict → agent_complete       │
    │ agent_start → thinking... → verdict → agent_complete       │
    │ final                                                       │
    └─────────────────────────────────────────────────────────────┘

    Args:
        question: 分析対象の問いかけ

    Yields:
        dict: イベント辞書
            - {"type": "agent_start", "agent": "MELCHIOR-1"}: エージェント開始
            - {"type": "thinking", "content": "..."}: 思考プロセス（リアルタイム）
            - {"type": "verdict", "data": {...}}: エージェント判定
            - {"type": "agent_complete", "agent": "..."}: エージェント完了
            - {"type": "final", "data": {...}}: 最終判定
    """
    # -------------------------------------------------------------------------
    # 1. エージェント作成
    # -------------------------------------------------------------------------
    melchior = MelchiorAgent()
    balthasar = BalthasarAgent()
    casper = CasperAgent()
    agents = [melchior, balthasar, casper]

    # -------------------------------------------------------------------------
    # 2. 判定結果を収集するリスト
    # -------------------------------------------------------------------------
    # 各エージェントの verdict イベントから AgentVerdict を収集
    verdicts: list[AgentVerdict] = []

    # -------------------------------------------------------------------------
    # 3. 各エージェントで分析（ストリーミング）
    # -------------------------------------------------------------------------
    for agent in agents:
        # エージェント開始イベント
        yield {"type": "agent_start", "agent": agent.name}

        # =================================================================
        # 【LLM呼び出し】ここで agent.analyze_stream() を実行
        # =================================================================
        # - 呼び出し先: agents/base.py の MAGIAgent.analyze_stream()
        # - 内部処理: self.agent.stream_async() で Bedrock Claude を呼び出し
        # - 送信内容: question（ユーザーの問いかけ）+ システムプロンプト
        # - 受信内容: イベントのストリーム（thinking → verdict）
        # - 注意: question を analyze_stream に渡す（ハードコードではなく）
        async for event in agent.analyze_stream(question):
            # -----------------------------------------------------------------
            # イベントをそのまま転送（UIで表示するため）
            # -----------------------------------------------------------------
            yield event

            # -----------------------------------------------------------------
            # verdict イベントから判定を収集
            # -----------------------------------------------------------------
            # analyze_stream() からは {"type": "verdict", "data": {...}} が来る
            # data は AgentVerdict.model_dump() の結果（辞書）
            if event["type"] == "verdict":
                # 辞書から AgentVerdict を再構築
                verdict_data = event["data"]
                verdict = AgentVerdict(**verdict_data)
                verdicts.append(verdict)

        # エージェント完了イベント
        yield {"type": "agent_complete", "agent": agent.name}

    # -------------------------------------------------------------------------
    # 4. JUDGEで統合
    # -------------------------------------------------------------------------
    # ※ここではLLMを呼び出していない（多数決ロジックのみ）
    # - 3エージェントの判定を集計
    # - 賛成 > 反対 → 承認、賛成 < 反対 → 否決、同数 → 保留
    judge = JudgeComponent()
    final_verdict = judge.integrate(verdicts)

    # 最終判定イベント
    # model_dump(): Pydanticモデルを辞書に変換（JSON化可能）
    yield {"type": "final", "data": final_verdict.model_dump()}


# =============================================================================
# テスト実行用エントリーポイント
# =============================================================================

async def main():
    """
    ストリーミング版のテスト実行

    run_judge_mode_stream() を呼び出し、各イベントをコンソールに表示します。
    このテストにより、以下を確認できます:
    - 3エージェントが順番に思考プロセスを出力
    - 各エージェントが判定を返す
    - JUDGEが最終判定を出す

    実行方法:
        cd agentcore && python backend.py
    """
    # run_judge_mode_stream() は AsyncGenerator を返す
    # async for でイベントを順次取得
    async for event in run_judge_mode_stream("AIを業務に導入すべきか？"):
        # ---------------------------------------------------------------------
        # イベントタイプ別に表示
        # ---------------------------------------------------------------------
        if event["type"] == "agent_start":
            # エージェント開始: ヘッダー表示
            print(f"\n=== {event['agent']} ===")

        elif event["type"] == "thinking":
            # 思考プロセス: リアルタイム表示（改行なし）
            print(event["content"], end="")

        elif event["type"] == "verdict":
            # 判定結果: 構造化データ表示
            print(f"\n[判定] {event['data']}")

        elif event["type"] == "agent_complete":
            # エージェント完了: 区切り線
            print(f"\n--- {event['agent']} 完了 ---")

        elif event["type"] == "final":
            # 最終判定: 強調表示
            print(f"\n\n========== 最終判定 ==========")
            print(event["data"])


# ============ エントリーポイント ============
@app.entrypoint
async def invoke(payload: dict):
    """
    AgentCore エントリーポイント（ストリーミング版）
    
    Args:
        payload: {"question": "AIを導入すべきか？"}
    
    Yields:
        各イベント（thinking, verdict, final など）
    """
    # 1. payloadから question を取り出す
    question = payload.get("question", "")
    
    # 2. ストリーミング版を呼び出し、イベントをそのまま yield
    async for event in run_judge_mode_stream(question):
        yield event




# =============================================================================
# スクリプト実行時のエントリーポイント
# =============================================================================

if __name__ == "__main__":
    # asyncio.run() で非同期関数を実行
    # main() は async def なので、同期コンテキストから呼び出すには asyncio.run() が必要
    app.run()                 # ← appを使う
