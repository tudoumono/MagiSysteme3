# Strands Agents SDK 学習ガイド - Part 1: 基礎編

## 概要

このドキュメントは、MAGIシステムのバックエンド実装を通じてStrands Agents SDKを学ぶためのチュートリアルです。

---

## 1. プロジェクト構成

```
agentcore/
├── agents/
│   └── base.py      # エージェント定義（Pydanticモデル、基底クラス、3エージェント）
├── backend.py       # メインハンドラー（これから実装）
└── requirements.txt # 依存関係
```

---

## 2. Strands SDKの基本構造

### 2.1 必要なインポート

```python
from strands import Agent
from strands.models.bedrock import BedrockModel
from pydantic import BaseModel, Field
```

### 2.2 BedrockModelの作成

Amazon Bedrockを使う場合、`BedrockModel`クラスでモデルを作成します。

```python
model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="ap-northeast-1"  # 東京リージョン
)
```

### 2.3 Agentの作成

`Agent`クラスにモデルとシステムプロンプトを渡します。

```python
agent = Agent(
    model=model,
    system_prompt="あなたは〇〇です..."
)
```

---

## 3. Structured Output（構造化出力）

### 3.1 概念

通常のLLM呼び出しはテキストを返しますが、`structured_output()`を使うと**Pydanticモデルに沿った構造化データ**が返ります。

```
┌─────────────────────────────────────────────────────────────┐
│  structured_output(AgentVerdict, "質問...")                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  1. プロンプトをLLM（Claude）に送信                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  2. LLMが推論を実行し、JSON形式で回答を生成                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Pydanticでパース＆バリデーション                          │
│     → 型チェック、範囲チェック等を自動実行                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              Pydanticモデル型で返却
```

### 3.2 Pydanticモデルの定義

```python
class AgentVerdict(BaseModel):
    """エージェントの判定結果"""
    agent_name: str = Field(description="エージェント名")
    verdict: str = Field(description="賛成 または 反対")
    reasoning: str = Field(description="判定理由（200文字以内）")
    confidence: float = Field(ge=0.0, le=1.0, description="確信度")
```

**ポイント:**
- `Field()`でバリデーションルールを定義
- `ge=0.0, le=1.0` は「0以上1以下」を意味
- `description`はLLMへのヒントになる

### 3.3 structured_output()の使い方

```python
result = self.agent.structured_output(
    AgentVerdict,                              # 第1引数: 出力の型
    f"以下の問いかけを分析してください: {question}"  # 第2引数: プロンプト
)

# resultはAgentVerdict型
print(result.agent_name)   # "MELCHIOR-1"
print(result.verdict)      # "賛成"
print(result.reasoning)    # "論理的に考えると..."
print(result.confidence)   # 0.85
```

---

## 4. MAGIAgentクラスの実装

### 4.1 基底クラス

```python
class MAGIAgent:
    """MAGIエージェントの基底クラス"""

    def __init__(self, name: str, persona: str, model_id: str = "anthropic.claude-sonnet-4-20250514-v1:0"):
        self.name = name
        self.persona = persona
        self.model_id = model_id

        # BedrockModelを作成してAgentに渡す
        model = BedrockModel(
            model_id=model_id,
            region_name="ap-northeast-1"
        )

        self.agent = Agent(
            model=model,
            system_prompt=self._build_system_prompt()
        )

    def _build_system_prompt(self) -> str:
        """ペルソナに基づくシステムプロンプトを構築"""
        return f"""あなたはMAGIシステムの{self.name}です。
        {self.persona}
        ...
        """

    def analyze(self, question: str) -> AgentVerdict:
        """問いかけを分析し判定を返す"""
        return self.agent.structured_output(
            AgentVerdict,
            f"以下の問いかけを分析してください: {question}"
        )
```

### 4.2 サブクラス（継承パターン）

各エージェントは基底クラスを継承し、独自の`SYSTEM_PROMPT`を持ちます。

```python
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
            name="MELCHIOR-1",
            persona="赤木ナオコ博士の科学者としての人格を持ちます。"
        )

    def _build_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
```

---

## 5. 3エージェントの役割

| エージェント | name | 人格 | 分析観点 |
|-------------|------|------|---------|
| **MELCHIOR** | MELCHIOR-1 | 科学者 | 論理的整合性、科学的根拠、データに基づく客観的判断、リスクの定量的評価 |
| **BALTHASAR** | BALTHASAR-2 | 母親 | 安全性と保護、長期的な影響、関係者への配慮、リスク回避 |
| **CASPER** | CASPER-3 | 女性 | 人間的な感情、社会的影響、倫理的配慮、共感と理解 |

---

## 6. 次のステップ

1. **FinalVerdictモデルの追加** - 最終判定用のPydanticモデル
2. **JUDGEコンポーネントの実装** - 多数決ロジック
3. **backend.pyの実装** - judge_modeハンドラー

→ `02_judge_and_backend.md` に続く
