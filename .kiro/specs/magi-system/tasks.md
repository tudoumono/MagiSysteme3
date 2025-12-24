# Implementation Plan: MAGI System

## Overview

MAGIシステムを4段階で開発する。各段階でAgentCoreをデプロイし、Streamlitローカル起動で動作確認を行う。ストリーミングレスポンスと思考表示に対応。

## 開発方針

- **バックエンド**: 学習用として自己実装（サポートあり）
- **フロントエンド**: Kiroが実装
- **レスポンス**: ストリーミング対応 + 思考プロセス表示
- **段階的リリース**: 各段階でデプロイ→動作確認→次段階へ

---

# Part A: フロントエンド（Kiro実装）

## Phase 1: 判定モードのフロントエンド

- [ ] 1.1 フロントエンド基盤構築
  - [ ] 1.1.1 プロジェクト構造を整理する
    - frontend/frontend.py の既存コードをベースに拡張
    - _Requirements: 6.1, 7.1_
  - [ ] 1.1.2 AgentCore API呼び出し関数を実装する
    - ストリーミング対応のAPI呼び出し
    - _Requirements: 5.3, 9.1_

- [ ] 1.2 判定モードUI実装
  - [ ] 1.2.1 ストリーミング受信を実装する
    - AgentCore APIからのストリーミング処理
    - _Requirements: 9.1, 9.4_
  - [ ] 1.2.2 思考プロセス表示UIを実装する
    - 各エージェントの思考を逐次表示
    - _Requirements: 9.6, 12.6_
  - [ ] 1.2.3 判定結果表示を更新する
    - ストリーミング対応の3カラム表示
    - _Requirements: 7.1, 7.2, 8.1_

- [ ] 1.3 Phase 1 動作確認
  - [ ] 1.3.1 デモモードで動作確認
    - モックレスポンスでUI動作を確認
    - _Requirements: 10.3, 10.4_
  - [ ] 1.3.2 AgentCore接続で動作確認
    - 実際のバックエンドと接続してE2Eテスト
    - _Requirements: 11.4_

---

## Phase 2: 会話モードのフロントエンド

- [ ] 2.1 会話モードUI実装
  - [ ] 2.1.1 モード切り替えUIを実装する
    - サイドバーでのモード選択
    - _Requirements: 6.1.2_
  - [ ] 2.1.2 会話モード表示を実装する
    - 3カラムでの回答表示（判定なし）
    - _Requirements: 6.1.6_
  - [ ] 2.1.3 会話履歴管理を実装する
    - セッション内での履歴保持
    - _Requirements: 6.4, 6.9_

- [ ] 2.2 Phase 2 動作確認
  - [ ] 2.2.1 デモモードで動作確認
  - [ ] 2.2.2 AgentCore接続で動作確認

---

## Phase 3: ロール設定のフロントエンド

- [ ] 3.1 ロール設定UI実装
  - [ ] 3.1.1 ロール設定UIを実装する
    - サイドバーでの各エージェントのロール選択/カスタマイズ
    - _Requirements: 9.1.1_
  - [ ] 3.1.2 ロールプリセット選択を実装する
    - プリセットからの選択、カスタム入力
    - _Requirements: 9.1.2, 9.1.3_
  - [ ] 3.1.3 ロール変更の即時反映を実装する
    - 設定変更後の次回質問から反映
    - _Requirements: 9.1.4_

- [ ] 3.2 Phase 3 動作確認
  - [ ] 3.2.1 デモモードで動作確認
  - [ ] 3.2.2 AgentCore接続で動作確認

---

## Phase 4: モデル設定のフロントエンド

- [ ] 4.1 モデル設定UI実装
  - [ ] 4.1.1 モデル設定UIを実装する
    - サイドバーでの各エージェントのモデル選択
    - _Requirements: 9.2.1_
  - [ ] 4.1.2 モデル情報表示を実装する
    - 各モデルの特徴、コスト目安の表示
    - _Requirements: 9.2.2, 9.2.3_
  - [ ] 4.1.3 モデル変更の即時反映を実装する
    - 設定変更後の次回質問から反映
    - _Requirements: 9.2.4_

- [ ] 4.2 Phase 4 動作確認
  - [ ] 4.2.1 デモモードで動作確認
  - [ ] 4.2.2 AgentCore接続で動作確認

---

# Part B: バックエンド（学習用：自己実装）

> 💡 **サポート方針**: 各タスクにはヒントとガイダンスを記載しています。
> 実装中に質問があれば、いつでもKiroに聞いてください。
> コードレビューやデバッグのサポートも可能です。

## Phase 1: 判定モードのバックエンド

- [ ] B1.1 プロジェクト構造を作成する
  - 📁 作成するファイル: `agentcore/backend.py`, `agentcore/agents/`, `agentcore/requirements.txt`
  - 💡 ヒント: Strands Agents SDKの基本構造を参考に
  - 📚 参考: design.mdの「Backend Components」セクション
  - _Requirements: 5.1_

- [ ] B1.2 エージェント基底クラスを実装する
  - 📁 作成: `agentcore/agents/base.py`
  - 💡 ヒント: `MAGIAgent`基底クラス、`AgentVerdict`データクラスを定義
  - 📚 参考: design.mdの「MAGIエージェント基底クラス」
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] B1.3 3エージェント（MELCHIOR/BALTHASAR/CASPER）を実装する
  - 📁 作成: `agentcore/agents/melchior.py`, `balthasar.py`, `casper.py`
  - 💡 ヒント: 各エージェントのシステムプロンプトがキー
  - 📚 参考: design.mdの各エージェント定義
  - _Requirements: 1.2, 1.3, 2.2, 2.3, 3.2, 3.3_

- [ ] B1.4 JUDGEコンポーネントを実装する
  - 📁 作成: `agentcore/judge.py`
  - 💡 ヒント: 多数決ロジック（賛成2以上→承認、反対2以上→否決、それ以外→保留）
  - 📚 参考: design.mdの「JUDGE（統合判定と対話）」
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] B1.5 判定モードハンドラーを実装する
  - 📁 作成: `agentcore/backend.py`のメインハンドラー
  - 💡 ヒント: `mode="judge"`時の処理フロー
  - 📚 参考: design.mdの「バックエンドエントリーポイント」
  - _Requirements: 5.2, 5.4_

- [ ] B1.6 ストリーミングレスポンスを実装する
  - 💡 ヒント: `AsyncGenerator`で`yield`を使用
  - 💡 形式: `{"type": "thinking/verdict/final", "agent": "...", "content/data": ...}`
  - 📚 参考: design.mdの「Streaming Response Schema」
  - _Requirements: 5.3, 9.1_

- [ ] B1.7 思考プロセス表示を実装する
  - 💡 ヒント: エージェントの分析過程を`type: "thinking"`でストリーミング
  - _Requirements: 5.8_

- [ ] B1.8 AgentCoreをデプロイする
  - 💡 コマンド: `agentcore configure` → `agentcore launch`
  - _Requirements: 5.1, 11.1_

---

## Phase 2: 会話モードのバックエンド

- [ ] B2.1 会話モードハンドラーを実装する
  - 💡 ヒント: `mode="chat"`時の処理フロー（判定なし、自由回答）
  - 📚 参考: design.mdの`run_chat_mode`関数
  - _Requirements: 6.1.4, 6.1.5_

- [ ] B2.2 会話コンテキスト管理を実装する
  - 💡 ヒント: `conversation_history`を受け取り、各エージェントに渡す
  - _Requirements: 5.5, 5.6_

- [ ] B2.3 会話モードのストリーミングを実装する
  - 💡 形式: `{"type": "response", "agent": "...", "content": "..."}`
  - _Requirements: 5.3, 9.1_

- [ ] B2.4 AgentCoreを更新デプロイする

---

## Phase 3: ロール設定のバックエンド

- [ ] B3.1 ロール設定データモデルを実装する
  - 💡 ヒント: `AgentConfig`に`role`と`role_description`を追加
  - 📚 参考: design.mdの「Agent Configuration Model」
  - _Requirements: 9.1.4, 9.1.5_

- [ ] B3.2 ロール設定APIを実装する
  - 💡 ヒント: `agent_configs`パラメータを受け取り、システムプロンプトを動的生成
  - _Requirements: 9.1.5_

- [ ] B3.3 デフォルトロールプリセットを作成する
  - 💡 プリセット例: 科学者/母親/女性（デフォルト）、ビジネス向け、技術向け
  - _Requirements: 9.1.2_

- [ ] B3.4 AgentCoreを更新デプロイする

---

## Phase 4: モデル設定のバックエンド

- [ ] B4.1 モデル設定データモデルを実装する
  - 💡 ヒント: `AgentConfig`に`model_id`を追加
  - _Requirements: 9.2.4, 9.2.5_

- [ ] B4.2 モデル設定APIを実装する
  - 💡 ヒント: 各エージェント初期化時に`model_id`を適用
  - _Requirements: 9.2.5_

- [ ] B4.3 利用可能モデルリストを定義する
  - 💡 モデル例:
    - `anthropic.claude-sonnet-4-20250514-v1:0` (Sonnet 4)
    - `anthropic.claude-3-5-haiku-20241022-v1:0` (Haiku 3.5)
    - `anthropic.claude-3-5-sonnet-20241022-v2:0` (Sonnet 3.5 v2)
  - _Requirements: 9.2.2_

- [ ] B4.4 AgentCoreを更新デプロイする

---

# 最終チェックポイント

- [ ] 5.1 全機能統合テスト
  - 判定モード + 会話モード + ロール設定 + モデル設定
  - ストリーミング + 思考表示の動作確認

- [ ] 5.2 ドキュメント整備
  - README.md、使用方法、設定ガイド

---

## Notes

- **Part A（フロントエンド）**: Kiroが実装
- **Part B（バックエンド）**: 学習用として自己実装、Kiroがサポート
- 各Phaseは独立してデプロイ可能
- Phase完了ごとに動作確認を実施
- バックエンド実装中に質問があれば、いつでもKiroに聞いてください
