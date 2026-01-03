# コードスナップショット（Step 2 完了時点）

このファイルは、Step 2（ストリーミング版）完了時点でのコードを保存しています。
後日参照用として使用してください。

**更新日:** Step 2 完了後

---

## agentcore/agents/base.py

```python
# MAGIエージェント基底クラス
# LLM呼び出しポイント:
# - analyze(): structured_output() 【LLM呼び出し①】
# - analyze_stream(): stream_async() 【LLM呼び出し②】

from strands import Agent
from strands.models.bedrock import BedrockModel
from pydantic import BaseModel, Field
from typing import AsyncGenerator


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

        # ※ここではLLMを呼び出していない（モデルの設定のみ）
        model = BedrockModel(
            model_id=model_id,
            region_name="ap-northeast-1"
        )

        # ※ここではLLMを呼び出していない（エージェントの設定のみ）
        # callback_handler=None: デフォルトのコンソール出力を無効化
        self.agent = Agent(
            model=model,
            system_prompt=self._build_system_prompt(),
            callback_handler=None
        )

    def _build_system_prompt(self) -> str:
        """ペルソナに基づくシステムプロンプトを構築"""
        return f"""あなたはMAGIシステムの{self.name}です。
        {self.persona}
        ...
        """

    def analyze(self, question: str) -> AgentVerdict:
        """問いかけを分析し判定を返す（同期版）"""
        prompt = f"以下の問いかけを分析してください: {question}"

        # =====================================================================
        # 【LLM呼び出し①】structured_output() で LLM を呼び出し
        # =====================================================================
        return self.agent.structured_output(AgentVerdict, prompt)

    async def analyze_stream(self, question: str) -> AsyncGenerator[dict, None]:
        """問いかけを分析（非同期ストリーミング版）"""
        prompt = f"以下の問いかけを分析してください: {question}"

        # =====================================================================
        # 【LLM呼び出し②】stream_async() で LLM を呼び出し（ストリーミング）
        # =====================================================================
        async for event in self.agent.stream_async(
            prompt,
            structured_output_model=AgentVerdict  # 1回のLLM呼び出しで両方取得
        ):
            if "data" in event:
                yield {"type": "thinking", "content": event["data"]}

            if "result" in event:
                result = event["result"]
                if hasattr(result, "structured_output") and result.structured_output:
                    yield {"type": "verdict", "data": result.structured_output.model_dump()}

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

## agentcore/backend.py（Step 2: 同期+ストリーミング版）

```python
# backend.py - MAGIシステム バックエンド
# LLM呼び出しフロー:
# 1. MELCHIOR-1 → 【LLM呼び出し 1回目】
# 2. BALTHASAR-2 → 【LLM呼び出し 2回目】
# 3. CASPER-3 → 【LLM呼び出し 3回目】
# 4. JudgeComponent.integrate() → LLM呼び出しなし
# 合計: 3回のLLM呼び出し

from agents.base import (
    MelchiorAgent, BalthasarAgent, CasperAgent,
    JudgeComponent, FinalVerdict, AgentVerdict
)
import asyncio
from typing import AsyncGenerator


def run_judge_mode(question: str) -> FinalVerdict:
    """同期版判定モード"""
    agents = [MelchiorAgent(), BalthasarAgent(), CasperAgent()]
    verdicts = []
    for agent in agents:
        # 【LLM呼び出し】ここで agent.analyze() を実行
        verdict = agent.analyze(question)
        verdicts.append(verdict)

    # ※ここではLLMを呼び出していない（多数決ロジックのみ）
    return JudgeComponent().integrate(verdicts)


async def run_judge_mode_stream(question: str) -> AsyncGenerator[dict, None]:
    """非同期ストリーミング版判定モード"""
    agents = [MelchiorAgent(), BalthasarAgent(), CasperAgent()]
    verdicts: list[AgentVerdict] = []

    for agent in agents:
        yield {"type": "agent_start", "agent": agent.name}

        # 【LLM呼び出し】ここで agent.analyze_stream() を実行
        async for event in agent.analyze_stream(question):
            yield event
            if event["type"] == "verdict":
                verdicts.append(AgentVerdict(**event["data"]))

        yield {"type": "agent_complete", "agent": agent.name}

    # ※ここではLLMを呼び出していない（多数決ロジックのみ）
    final_verdict = JudgeComponent().integrate(verdicts)
    yield {"type": "final", "data": final_verdict.model_dump()}


async def main():
    """ストリーミング版のテスト実行"""
    async for event in run_judge_mode_stream("AIを業務に導入すべきか？"):
        if event["type"] == "agent_start":
            print(f"\n=== {event['agent']} ===")
        elif event["type"] == "thinking":
            print(event["content"], end="")
        elif event["type"] == "verdict":
            print(f"\n[判定] {event['data']}")
        elif event["type"] == "final":
            print(f"\n\n========== 最終判定 ==========")
            print(event["data"])


if __name__ == "__main__":
    asyncio.run(main())
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

## Step 2 で学んだこと

### 1. callback_handler=None の重要性

```python
# Windowsでの文字化けエラーを回避
self.agent = Agent(
    model=model,
    system_prompt=prompt,
    callback_handler=None  # デフォルトのコンソール出力を無効化
)
```

### 2. SDK バージョンと structured_output

```bash
# バージョン確認
pip show strands-agents

# アップグレード（1.21.0以降が必要）
pip install --upgrade strands-agents
```

### 3. 1回のLLM呼び出しでストリーミング+構造化出力

```python
# structured_output_model パラメータがポイント
async for event in agent.stream_async(
    prompt,
    structured_output_model=AgentVerdict  # 1回のLLM呼び出しで両方取得
):
    if "result" in event:
        verdict = event["result"].structured_output
```

---

## 次のステップ

- **フロントエンド統合:** Streamlit UI でストリーミング表示を実装
