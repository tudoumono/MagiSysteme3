---
name: ux-psychology
description: UX心理学コンセプトの検索可能なデータベース。UI/UXデザイン、グロースハック、コンバージョン最適化、ユーザー行動分析に活用。トリガー：UI設計、UXデザイン、心理学的効果、バイアス、ユーザー行動、コンバージョン改善、価格設計、オンボーディング設計、フォーム最適化などのタスク時に使用。
---

# UX Psychology Skill

47個のUX心理学コンセプトを検索・活用するスキル。松下村塾株式会社のUX心理学コレクションを基に構成。

## ワークフロー

### 1. 自動トリガー

以下のタスクで自動的に発火：
- UI/UXデザインの作成・改善
- ランディングページ、フォーム、価格表の設計
- コンバージョン率の最適化
- オンボーディングフローの設計
- ユーザー行動の分析・改善提案

### 2. 検索の実行

```bash
python3 scripts/search.py "<クエリ>" [--category <category>] [-n <件数>]
```

**カテゴリ**:
- `pricing` - 価格・購買心理（アンカー効果、おとり効果、希少性など）
- `conversion` - コンバージョン最適化（損失回避、ナッジ、社会的証明など）
- `onboarding` - オンボーディング（段階的開示、目標勾配効果など）
- `cognitive` - 認知・注意（認知負荷、選択的注意、バナーブラインドネスなど）
- `engagement` - エンゲージメント（変動型報酬、ゲーミフィケーションなど）
- `visual` - ビジュアルデザイン（視覚的階層、ビジュアルアンカーなど）
- `bias` - バイアス・判断（確証バイアス、期待バイアスなど）
- `all` - 全カテゴリ（デフォルト）

### 3. 適用パターン

検索結果を基に、具体的なUI/UX改善を提案：

```
【コンセプト名】を適用
- 心理的効果: [なぜ機能するか]
- 実装方法: [具体的なUI/UXパターン]
- 実例: [Amazon、Airbnb等の事例]
```

## 検索例

```bash
# 価格ページの最適化
python3 scripts/search.py "価格 購入 コンバージョン" --category pricing

# オンボーディング改善
python3 scripts/search.py "初回 登録 継続" --category onboarding

# フォーム最適化
python3 scripts/search.py "入力 フォーム 離脱" --category cognitive

# 全文検索
python3 scripts/search.py "ユーザーの注意を引く方法"
```

## コンセプト一覧（カテゴリ別）

### 価格・購買心理 (Pricing)
- アンカー効果 (Anchor Effect)
- おとり効果 (Decoy Effect)
- 希少性効果 (Scarcity)
- 損失回避 (Loss Aversion)
- 授かり効果 (Endowment Effect)
- フレーミング効果 (Framing)

### コンバージョン最適化 (Conversion)
- 社会的証明 (Social Proof)
- ナッジ効果 (Nudge)
- デフォルト効果 (Default Bias)
- 段階的要請 (Foot in the Door Effect)
- 好奇心ギャップ (Curiosity Gap)
- 労働の錯覚 (Labor Illusion)

### オンボーディング (Onboarding)
- 段階的開示 (Progressive Disclosure)
- 目標勾配効果 (Goal Gradient Effect)
- ツァイガルニク効果 (Zeigarnik Effect)
- 反応型オンボーディング (Reactive Onboarding)
- ピグマリオン効果 (Pygmalion Effect)

### 認知・注意 (Cognitive)
- 認知負荷 (Cognitive Load)
- 選択的注意 (Selective Attention)
- バナー・ブラインドネス (Banner Blindness)
- 決断疲れ (Decision Fatigue)
- 系列位置効果 (Serial Position Effect)

### エンゲージメント (Engagement)
- 変動型報酬 (Variable Reward)
- ゲーミフィケーション (Gamification)
- サンクコスト効果 (Sunk Cost Effect)
- 誘惑の結びつけ (Temptation Bundling)
- ユーザー歓喜効果 (User Delight)

### ビジュアルデザイン (Visual)
- 視覚的階層 (Visual Hierarchy)
- ビジュアル・アンカー (Visual Anchor)
- 美的ユーザビリティ効果 (Aesthetic-Usability Effect)
- スキューモーフィズム (Skeuomorphism)

### バイアス・判断 (Bias)
- 確証バイアス (Confirmation Bias)
- 期待バイアス (Expectation Bias)
- 親近性バイアス (Familiarity Bias)
- 調査バイアス (Survey Bias)
- 共感ギャップ (Empathy Gap)

### その他
- ドハティの閾値 (Doherty Threshold) - 0.4秒の壁
- ピーク・エンドの法則 (Peak-End Rule)
- ハロー効果 (Halo Effect)
- 観察効果 (Hawthorne Effect)
- プライミング効果 (Priming)
- 誘導抵抗 (Reactance)
- 意図的な壁 (Intentional Friction)

## データソース

松下村塾株式会社 UX心理学コレクション
https://www.shokasonjuku.com/ux-psychology
