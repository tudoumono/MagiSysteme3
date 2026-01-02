# Requirements Document

## Introduction

MAGIシステムは、3つのAIエージェント（MELCHIOR、BALTHASAR、CASPER）による多角的判定・対話システムである。フロントエンド（Streamlit）とバックエンド（Strands Agents + AgentCore Runtime）で構成され、ユーザーの問いかけに対して3つの異なる観点から分析し、判定または対話を提供する。

### 開発フェーズ

| Phase | 機能 | 説明 |
|-------|------|------|
| 1 | 判定モード | 3エージェント判定 + 最終判定 + ストリーミング + 思考表示 |
| 2 | 会話モード | 判定なしの自由対話 + モード切り替え |
| 3 | ロール設定 | 各エージェントのペルソナカスタマイズ |
| 4 | モデル設定 | 各エージェントの使用モデル選択 |
| 5 | インタリーブ思考 | Claude選択時のインタリーブ思考ON/OFF切り替え |

### 実装分担

| Part | 担当 | 内容 |
|------|------|------|
| Part A | Kiro実装 | フロントエンド（Streamlit UI） |
| Part B | 学習用：自己実装 | バックエンド（AgentCore + Strands Agents） |

> 💡 Part B（バックエンド）は学習用として自己実装しますが、Kiroがサポートします。
> 質問、コードレビュー、デバッグなど、いつでも相談可能です。

## Glossary

- **MAGI_System**: 3つのAIエージェントによる多角的判定システム全体
- **MELCHIOR**: 科学者の人格を持つエージェント。論理的・科学的観点から分析を行う
- **BALTHASAR**: 母親の人格を持つエージェント。保護的・安全重視の観点から分析を行う
- **CASPER**: 女性の人格を持つエージェント。人間的・感情的観点から分析を行う
- **JUDGE**: 3エージェントの判定を統合し最終判定を下すコンポーネント
- **AgentCore_Runtime**: Amazon Bedrock AgentCoreで実行されるバックエンドサービス
- **Strands_Agent**: Strands Agents SDKで作成されたAIエージェント
- **Verdict**: 各エージェントの判定結果（賛成/反対）
- **Final_Verdict**: 3エージェントの判定を統合した最終判定（承認/否決/保留）
- **Streamlit_App**: フロントエンドUIアプリケーション
- **Backend_Service**: AgentCore Runtime上で動作するバックエンドサービス
- **Interleaved_Thinking**: Claude 4モデルのインタリーブ思考機能。ツール呼び出し間で思考し、結果を評価して動的に処理を調整する
- **Extended_Thinking**: 拡張思考。モデルが回答前に深く推論するための思考予算を設定する機能

## Requirements

### Requirement 1: MELCHIORエージェント

**User Story:** As a ユーザー, I want to 科学的・論理的観点からの分析を得る, so that データに基づいた判断材料を得られる。

#### Acceptance Criteria

1. THE MELCHIOR SHALL 科学者の人格を持つStrands_Agentとして実装される
2. WHEN 問いかけを受信する THEN THE MELCHIOR SHALL 論理的・科学的観点から分析を行う
3. THE MELCHIOR SHALL 判定（賛成/反対）と理由を返却する
4. THE MELCHIOR SHALL Amazon Bedrock Claude Sonnetを使用する

### Requirement 2: BALTHASARエージェント

**User Story:** As a ユーザー, I want to 保護的・安全重視の観点からの分析を得る, so that リスクを考慮した判断材料を得られる。

#### Acceptance Criteria

1. THE BALTHASAR SHALL 母親の人格を持つStrands_Agentとして実装される
2. WHEN 問いかけを受信する THEN THE BALTHASAR SHALL 保護的・安全重視の観点から分析を行う
3. THE BALTHASAR SHALL 判定（賛成/反対）と理由を返却する
4. THE BALTHASAR SHALL Amazon Bedrock Claude Sonnetを使用する

### Requirement 3: CASPERエージェント

**User Story:** As a ユーザー, I want to 人間的・感情的観点からの分析を得る, so that 感情面を考慮した判断材料を得られる。

#### Acceptance Criteria

1. THE CASPER SHALL 女性の人格を持つStrands_Agentとして実装される
2. WHEN 問いかけを受信する THEN THE CASPER SHALL 人間的・感情的観点から分析を行う
3. THE CASPER SHALL 判定（賛成/反対）と理由を返却する
4. THE CASPER SHALL Amazon Bedrock Claude Sonnetを使用する

### Requirement 4: JUDGE統合判定と対話

**User Story:** As a ユーザー, I want to 3エージェントの判定を統合した最終判定を得て、さらに深掘りできる, so that 総合的な結論を把握し、疑問点を解消できる。

#### Acceptance Criteria

1. WHEN 3エージェント全ての判定が完了する THEN THE JUDGE SHALL 最終判定を生成する
2. THE JUDGE SHALL 多数決に基づいて最終判定（承認/否決）を決定する
3. THE JUDGE SHALL 各エージェントの判定理由を統合したサマリーを生成する
4. IF 判定が分かれる場合 THEN THE JUDGE SHALL 各観点の違いを説明する
5. WHEN ユーザーが判定に対して追加質問をする THEN THE JUDGE SHALL 該当エージェントの観点から詳細を説明する
6. THE JUDGE SHALL 会話の文脈を理解し、一貫性のある対話を維持する

### Requirement 5: バックエンドAPI（対話対応）

**User Story:** As a フロントエンド, I want to AgentCore Runtimeを呼び出す, so that MAGIエージェントと対話できる。

#### Acceptance Criteria

1. THE Backend_Service SHALL AgentCore Runtimeとしてデプロイ可能である
2. WHEN 問いかけを受信する THEN THE Backend_Service SHALL 3エージェントを実行する
3. THE Backend_Service SHALL ストリーミングレスポンスを返却する
4. THE Backend_Service SHALL JSON形式で各エージェントの判定と最終判定を返却する
5. THE Backend_Service SHALL 会話履歴を受け取り、コンテキストを維持した応答を生成する
6. WHEN フォローアップ質問を受信する THEN THE Backend_Service SHALL 前回の判定を踏まえた応答を返却する
7. THE Backend_Service SHALL modeパラメータで判定モード/会話モードを切り替える
8. THE Backend_Service SHALL 各エージェントの思考プロセスをストリーミングで返却する

### Requirement 6: 対話型チャットUI

**User Story:** As a ユーザー, I want to MAGIシステムと対話形式でやり取りする, so that 判断だけでなく追加の質問や深掘りができる。

#### Acceptance Criteria

1. WHEN ユーザーがページにアクセスする THEN THE Streamlit_App SHALL チャット入力フィールドを表示する
2. WHEN ユーザーが質問を入力してEnterを押す THEN THE Streamlit_App SHALL 質問をチャット履歴に追加する
3. WHEN 質問が送信される THEN THE Streamlit_App SHALL バックエンドへリクエストを送信する
4. THE Streamlit_App SHALL チャット履歴をセッション内で保持する
5. THE Streamlit_App SHALL 認知負荷を軽減するシンプルなインターフェースを提供する
6. THE Streamlit_App SHALL 美的ユーザビリティ効果を考慮した洗練されたデザインを適用する
7. THE Streamlit_App SHALL 過去の会話コンテキストを保持し、フォローアップ質問に対応する
8. WHEN ユーザーが追加質問をする THEN THE MAGI_System SHALL 前回の判定を踏まえた回答を提供する
9. THE Streamlit_App SHALL ユーザーとMAGIの会話を時系列で表示する
10. THE Streamlit_App SHALL 各メッセージにタイムスタンプを表示する

### Requirement 6.1: モード切り替え機能

**User Story:** As a ユーザー, I want to 判定モードと会話モードを切り替える, so that 目的に応じた使い方ができる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL 「判定モード」と「会話モード」の2つのモードを提供する
2. THE Streamlit_App SHALL サイドバーでモード切り替えを可能にする
3. WHEN 判定モードが選択されている THEN THE Streamlit_App SHALL 3エージェントの判定と最終判定を表示する
4. WHEN 会話モードが選択されている THEN THE Streamlit_App SHALL 3賢者との自由な対話を提供する
5. WHEN 会話モードで質問する THEN THE MAGI_System SHALL 3エージェントがそれぞれの観点から回答する
6. THE Streamlit_App SHALL 会話モードでも3カラム表示で各エージェントの回答を表示する

### Requirement 7: 3カラムエージェント表示

**User Story:** As a ユーザー, I want to 3つのエージェントの判定を並列で確認する, so that 各観点からの分析を比較できる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL MELCHIOR、BALTHASAR、CASPERの3カラムを横並びで表示する
2. WHEN エージェントの判定結果を受信する THEN THE Streamlit_App SHALL 該当カラムに判定（賛成/反対）と理由を表示する
3. THE Streamlit_App SHALL 各エージェントのカラムを視覚的に区別できるスタイルで表示する（視覚的階層・ビジュアルアンカー適用）
4. THE Streamlit_App SHALL 各エージェントの役割（科学者/母親/女性）を表示する
5. THE Streamlit_App SHALL 系列位置効果を考慮し、最も重要な情報を各カラムの最初と最後に配置する

### Requirement 8: 最終判定表示

**User Story:** As a ユーザー, I want to MAGIの最終判定を確認する, so that 総合的な結論を把握できる。

#### Acceptance Criteria

1. WHEN 全エージェントの判定が完了する THEN THE Streamlit_App SHALL 最終判定（承認/否決/保留）を表示する
2. THE Streamlit_App SHALL 最終判定の根拠サマリーを表示する
3. THE Streamlit_App SHALL 最終判定を視覚的に目立つスタイルで表示する（ビジュアルアンカー適用）
4. THE Streamlit_App SHALL ピーク・エンドの法則を適用し、最終判定表示を印象的な体験として設計する

### Requirement 9: ストリーミング対応

**User Story:** As a ユーザー, I want to 応答をリアルタイムで確認する, so that 待ち時間中も進捗を把握できる。

#### Acceptance Criteria

1. WHEN バックエンドからストリーミングレスポンスを受信する THEN THE Streamlit_App SHALL テキストを逐次表示する
2. WHEN 処理中である THEN THE Streamlit_App SHALL ローディング状態を表示する（労働の錯覚適用）
3. IF エラーが発生する THEN THE Streamlit_App SHALL エラーメッセージを表示する
4. THE Streamlit_App SHALL ドハティの閾値（0.4秒）を意識し、即座にフィードバックを提供する
5. THE Streamlit_App SHALL 目標勾配効果を適用し、処理進捗を可視化する
6. THE Streamlit_App SHALL 各エージェントの思考プロセスをストリーミング表示する

### Requirement 9.1: ロール設定機能

**User Story:** As a ユーザー, I want to 3賢者のロール（人格）をカスタマイズする, so that 目的に応じた観点から分析を得られる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL 各エージェントのロール（ペルソナ）を設定するUIを提供する
2. THE Streamlit_App SHALL デフォルトロールプリセット（科学者/母親/女性）を提供する
3. THE Streamlit_App SHALL カスタムロールの入力を可能にする
4. WHEN ロール設定が変更される THEN THE Backend_Service SHALL 次回の質問から新しいロールを適用する
5. THE Backend_Service SHALL ロール設定をシステムプロンプトに反映する

### Requirement 9.2: モデル設定機能

**User Story:** As a ユーザー, I want to 各賢者の使用モデルを変更する, so that コストや性能を調整できる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL 各エージェントの使用モデルを選択するUIを提供する
2. THE Streamlit_App SHALL 利用可能なモデルリスト（Claude Sonnet, Haiku等）を表示する
3. THE Streamlit_App SHALL 各モデルの特徴やコスト目安を表示する
4. WHEN モデル設定が変更される THEN THE Backend_Service SHALL 次回の質問から新しいモデルを使用する
5. THE Backend_Service SHALL 各エージェントごとに異なるモデルを使用可能にする

### Requirement 9.3: インタリーブ思考機能

**User Story:** As a ユーザー, I want to Claudeモデル選択時にインタリーブ思考のON/OFFを切り替える, so that より高度な推論や動的な処理調整を活用できる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL Claudeモデル選択時にインタリーブ思考のトグルスイッチを表示する
2. WHEN 非Claudeモデルが選択されている THEN THE Streamlit_App SHALL インタリーブ思考トグルを非表示または無効化する
3. THE Streamlit_App SHALL インタリーブ思考の説明（ツールキップまたはヘルプテキスト）を表示する
4. WHEN インタリーブ思考がONである THEN THE Backend_Service SHALL `anthropic_beta: ['interleaved-thinking-2025-05-14']`を設定する
5. WHEN インタリーブ思考がONである THEN THE Backend_Service SHALL `thinking: {'type': 'enabled', 'budget_tokens': N}`を設定する
6. THE Streamlit_App SHALL 思考予算（budget_tokens）を設定するスライダーまたは入力フィールドを提供する
7. THE Backend_Service SHALL インタリーブ思考有効時、ツール実行結果を評価して動的に処理を調整する
8. THE Streamlit_App SHALL インタリーブ思考の思考プロセスをストリーミング表示する

### Requirement 10: 設定とデモモード

**User Story:** As a 開発者, I want to AgentCore RuntimeのARNを設定する, so that バックエンドと接続できる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL サイドバーにAgentCore Runtime ARN入力フィールドを提供する
2. WHEN ARNが設定されていない THEN THE Streamlit_App SHALL 警告メッセージを表示する
3. THE Streamlit_App SHALL デモモード（モックレスポンス）を提供する
4. WHEN デモモードが有効である THEN THE Streamlit_App SHALL バックエンド接続なしで動作する

### Requirement 11: デプロイ対応

**User Story:** As a 運用者, I want to システムをAWSにデプロイする, so that 本番環境で運用できる。

#### Acceptance Criteria

1. THE Backend_Service SHALL ECR + CodeBuildでデプロイ可能である
2. THE Streamlit_App SHALL Dockerfileを提供する
3. THE Streamlit_App SHALL Lightsail Containerにデプロイ可能である
4. THE Streamlit_App SHALL ポート8501で起動する


### Requirement 12: UX心理学に基づくデザイン原則

**User Story:** As a ユーザー, I want to 心理学的に最適化されたUIを使用する, so that 直感的で快適な体験ができる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL 視覚的階層（Visual Hierarchy）を適用し、情報の優先順位を明確にする
2. THE Streamlit_App SHALL ビジュアルアンカー（Visual Anchor）を使用し、重要な要素（判定結果、CTAボタン）を強調する
3. THE Streamlit_App SHALL 認知負荷（Cognitive Load）を最小化するシンプルなレイアウトを採用する
4. THE Streamlit_App SHALL 美的ユーザビリティ効果（Aesthetic-Usability Effect）を考慮した洗練されたデザインを適用する
5. THE Streamlit_App SHALL 系列位置効果（Serial Position Effect）を活用し、重要情報を最初と最後に配置する
6. THE Streamlit_App SHALL 労働の錯覚（Labor Illusion）を適用し、処理中のアニメーションで価値を演出する
7. THE Streamlit_App SHALL ドハティの閾値（Doherty Threshold）を遵守し、0.4秒以内のフィードバックを提供する
8. THE Streamlit_App SHALL ピーク・エンドの法則（Peak-End Rule）を適用し、最終判定を印象的に演出する
9. THE Streamlit_App SHALL 目標勾配効果（Goal Gradient Effect）を活用し、処理進捗を可視化する
10. THE Streamlit_App SHALL ユーザー歓喜効果（User Delight）を取り入れ、マイクロインタラクションで喜びを提供する

### Requirement 13: UIスタイルとビジュアルデザイン

**User Story:** As a ユーザー, I want to 視覚的に魅力的なUIを使用する, so that MAGIシステムの世界観に没入できる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL ライトモードをベースに採用する（背景 #F8FAFC、カード #FFFFFF）
2. THE Streamlit_App SHALL 各エージェントカードに2pxの色付きボーダーを適用する
3. THE Streamlit_App SHALL Evangelion風のアクセントカラーを取り入れる（NERV Orange #F97316）
4. THE Streamlit_App SHALL 各エージェントに固有のアクセントカラーを設定する（MELCHIOR: Cyan #0891B2、BALTHASAR: Red #DC2626、CASPER: Purple #7C3AED）
5. THE Streamlit_App SHALL カード配置で各エージェントの境界を明確に表示する

### Requirement 14: UXガイドラインの遵守

**User Story:** As a ユーザー, I want to ベストプラクティスに基づいたUIを使用する, so that ストレスなく操作できる。

#### Acceptance Criteria

1. THE Streamlit_App SHALL スムーズスクロールを実装する（scroll-behavior: smooth）
2. THE Streamlit_App SHALL アニメーション時間を150-300msに設定する（micro-interactions）
3. THE Streamlit_App SHALL prefers-reduced-motionを尊重する
4. THE Streamlit_App SHALL ローディング状態にスケルトンスクリーンまたはスピナーを表示する
5. THE Streamlit_App SHALL フォーカス状態を視覚的に明示する（focus:ring-2）
6. THE Streamlit_App SHALL エラーメッセージを明確に表示する（赤色 + アイコン）
7. THE Streamlit_App SHALL 成功フィードバックを提供する（トースト通知またはチェックマーク）
8. THE Streamlit_App SHALL 色のコントラスト比4.5:1以上を確保する（WCAG AA準拠）
9. THE Streamlit_App SHALL タッチターゲットを最小44x44pxに設定する
