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
