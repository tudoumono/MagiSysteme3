# CLAUDE.md

## プロジェクト概要

MAGIシステム - エヴァンゲリオンのMAGIシステムをモチーフにした多角的判定AIシステム。3つの異なる人格を持つAIエージェント（MELCHIOR、BALTHASAR、CASPER）がユーザーの問いかけを分析し、最終的な統合判定を提供する。

## 技術スタック

- **言語**: Python 3.13+
- **パッケージマネージャー**: uv
- **バックエンド**: Strands Agents SDK + Amazon Bedrock AgentCore Runtime
- **フロントエンド**: Streamlit
- **AIモデル**: Claude Sonnet 4 (Amazon Bedrock経由、us-east-1リージョン)
- **監視**: CloudWatch (AgentCore Observability)
- **デプロイ**:
  - フロントエンド: Lightsail Container
  - バックエンド: ECR + CodeBuild

## プロジェクト構成

```
MagiSysteme3/
├── agentcore/              # バックエンド (Strands + AgentCore Runtime)
│   ├── agents/             # エージェント定義
│   │   └── base.py         # 基底エージェントクラス
│   ├── backend.py         # メインエントリーポイント
│   └── requirements.txt    # バックエンド依存関係
├── frontend/               # Streamlit UI
│   ├── frontend.py         # メインUIアプリケーション
│   ├── Dockerfile          # コンテナ定義
│   └── requirements.txt    # フロントエンド依存関係
├── .kiro/                  # Kiro仕様書
│   └── specs/magi-system/
│       ├── requirements.md # 要件定義（14の要件、受け入れ基準）
│       ├── design.md       # 設計書（コンポーネント、データモデル、API仕様）
│       └── tasks.md        # 実装タスク（Part A: フロントエンド、Part B: バックエンド）
├── main.py                 # エントリーポイント（プレースホルダー）
├── pyproject.toml          # プロジェクト設定
├── magi-architecture.md    # アーキテクチャドキュメント
└── uv.lock                 # 依存関係ロックファイル
```

## アーキテクチャ

```
ユーザー → Streamlit UI → AgentCore Runtime → [MELCHIOR | BALTHASAR | CASPER] → JUDGE → レスポンス
                                                    ↓
                                              Amazon Bedrock (Claude)
```

### MAGIエージェント

| エージェント | ペルソナ | 分析観点 |
|-------------|---------|---------|
| **MELCHIOR-1** | 科学者 | 論理的整合性、科学的根拠、データに基づく客観的判断 |
| **BALTHASAR-2** | 母親 | 安全性と保護、長期的影響、リスク回避 |
| **CASPER-3** | 女性 | 人間的感情、社会的影響、倫理的配慮、共感 |

### 開発フェーズ

| フェーズ | 機能 | Strands SDK機能 |
|---------|------|-----------------|
| 1 | 判定モード + ストリーミング | Structured Output, stream_async |
| 2 | 会話モード | Conversation Manager |
| 3 | ロール設定 | - |
| 4 | モデル設定 | - |
| 5 | インタリーブ思考 | Interleaved Thinking |

## 開発コマンド

```bash
# 依存関係のインストール
uv sync

# メインエントリーポイントの実行
uv run python main.py

# Streamlitフロントエンドの起動（プロジェクトルートから）
uv run streamlit run frontend/frontend.py

# バックエンドのローカル実行（AgentCore）
cd agentcore && python backeend.py
```

## 主要な規約

### 構造化出力モデル（Pydantic）

- `AgentVerdict`: 判定結果（agent_name, verdict, reasoning, confidence）
- `AgentResponse`: 会話モード回答（agent_name, response）
- `FinalVerdict`: 最終判定（verdict, summary, vote_count, agent_verdicts）

### 判定値

- エージェント判定: "賛成" | "反対"
- 最終判定: "承認" | "否決" | "保留"

### ストリーミングイベントタイプ

| イベント | 説明 |
|---------|------|
| `agent_start` | エージェント処理開始 |
| `thinking` | 思考プロセステキスト |
| `tool_use` | ツール使用中 |
| `reasoning` | インタリーブ思考出力 |
| `verdict` | エージェント判定結果 |
| `agent_complete` | エージェント処理完了 |
| `final` | 最終統合判定 |

## UIテーマ（ライトモード + エヴァンゲリオン風）

```python
COLORS = {
    "melchior": "#0891B2",   # シアン（科学者）
    "balthasar": "#DC2626",  # レッド（母親）
    "casper": "#7C3AED",     # パープル（女性）
    "nerv_accent": "#F97316" # オレンジ（NERV風）
}
```

## 実装分担

| Part | 担当 | 内容 |
|------|------|------|
| Part A | Kiro実装 | フロントエンド（Streamlit UI） |
| Part B | 学習用：自己実装 | バックエンド（AgentCore + Strands Agents） |

> Part B（バックエンド）は学習用として自己実装。Kiroがサポート（質問、コードレビュー、デバッグ対応可）。

## 仕様書の参照

詳細な仕様は `.kiro/specs/magi-system/` を参照：

- **requirements.md**: 14の要件と受け入れ基準（UX心理学原則を含む）
- **design.md**: コンポーネント設計、Pydanticモデル、API仕様、ストリーミングスキーマ
- **tasks.md**: Phase 1〜5の実装タスクと動作確認チェックリスト

## 備考

- プロンプトとUIは日本語を使用
- 参考資料はgitignore対象（`Reference/`ディレクトリ参照）
- UX心理学原則を適用（視覚的階層、認知負荷軽減、ドハティの閾値0.4秒など）
