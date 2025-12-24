#!/usr/bin/env python3
"""
UX Psychology Concept Search Script

Usage:
    python3 search.py "<query>" [--category <category>] [-n <max_results>]

Examples:
    python3 search.py "価格 コンバージョン"
    python3 search.py "オンボーディング" --category onboarding
    python3 search.py "ユーザー行動" -n 10
"""

import csv
import sys
import argparse
import re
from pathlib import Path
from collections import defaultdict


# カテゴリマッピング
CATEGORY_MAP = {
    'pricing': ['pricing'],
    'conversion': ['conversion'],
    'onboarding': ['onboarding'],
    'cognitive': ['cognitive'],
    'engagement': ['engagement'],
    'visual': ['visual'],
    'bias': ['bias'],
    'all': ['pricing', 'conversion', 'onboarding', 'cognitive', 'engagement', 'visual', 'bias']
}


def load_concepts(data_path: Path) -> list:
    """CSVからコンセプトデータを読み込む"""
    concepts = []
    csv_file = data_path / 'concepts.csv'
    
    if not csv_file.exists():
        print(f"Error: Data file not found: {csv_file}", file=sys.stderr)
        sys.exit(1)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            concepts.append(row)
    
    return concepts


def tokenize(text: str) -> set:
    """テキストをトークン化（日本語対応）"""
    # 英数字と日本語の両方を含むトークン抽出
    text = text.lower()
    # スペース、カンマ、句読点で分割
    tokens = re.split(r'[\s,、。]+', text)
    # 空文字を除去
    return set(t for t in tokens if t)


def calculate_score(concept: dict, query_tokens: set) -> float:
    """検索スコアを計算"""
    score = 0.0
    
    # 検索対象フィールドと重み
    fields = {
        'name_ja': 5.0,
        'name_en': 5.0,
        'keywords': 3.0,
        'definition': 2.0,
        'why_it_works': 1.5,
        'example': 1.0
    }
    
    for field, weight in fields.items():
        field_text = concept.get(field, '').lower()
        field_tokens = tokenize(field_text)
        
        for qt in query_tokens:
            # 完全一致
            if qt in field_tokens:
                score += weight * 2
            # 部分一致
            elif any(qt in ft or ft in qt for ft in field_tokens):
                score += weight
            # フィールド内に含まれる
            elif qt in field_text:
                score += weight * 0.5
    
    return score


def search(concepts: list, query: str, category: str = 'all', max_results: int = 5) -> list:
    """コンセプトを検索"""
    query_tokens = tokenize(query)
    
    if not query_tokens:
        return []
    
    # カテゴリフィルタ
    target_categories = CATEGORY_MAP.get(category, CATEGORY_MAP['all'])
    filtered_concepts = [c for c in concepts if c.get('category') in target_categories]
    
    # スコア計算
    scored = []
    for concept in filtered_concepts:
        score = calculate_score(concept, query_tokens)
        if score > 0:
            scored.append((concept, score))
    
    # スコア順にソート
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[:max_results]


def format_result(concept: dict, score: float, rank: int) -> str:
    """検索結果をフォーマット"""
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"#{rank} {concept['name_ja']} ({concept['name_en']})")
    output.append(f"カテゴリ: {concept['category']} | スコア: {score:.1f}")
    output.append(f"{'='*60}")
    output.append(f"\n【定義】\n{concept['definition']}")
    output.append(f"\n【なぜ機能するか】\n{concept['why_it_works']}")
    output.append(f"\n【実例】\n{concept['example']}")
    output.append(f"\n【関連キーワード】\n{concept['keywords']}")
    
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='UX心理学コンセプト検索')
    parser.add_argument('query', help='検索クエリ')
    parser.add_argument('--category', '-c', default='all',
                        choices=['pricing', 'conversion', 'onboarding', 'cognitive', 
                                'engagement', 'visual', 'bias', 'all'],
                        help='カテゴリフィルタ')
    parser.add_argument('-n', '--max-results', type=int, default=5,
                        help='最大結果数 (デフォルト: 5)')
    
    args = parser.parse_args()
    
    # データパスを取得（スクリプトの親ディレクトリ/data）
    script_dir = Path(__file__).parent.resolve()
    data_path = script_dir.parent / 'data'
    
    # コンセプトを読み込み
    concepts = load_concepts(data_path)
    
    # 検索実行
    results = search(concepts, args.query, args.category, args.max_results)
    
    if not results:
        print(f"\n検索結果なし: '{args.query}'")
        print("別のキーワードで検索してください。")
        return
    
    print(f"\n🔍 検索: '{args.query}' (カテゴリ: {args.category})")
    print(f"📊 {len(results)}件の結果")
    
    for i, (concept, score) in enumerate(results, 1):
        print(format_result(concept, score, i))
    
    print(f"\n{'='*60}")
    print("💡 活用のヒント:")
    print("- 複数のコンセプトを組み合わせてUI/UXを設計")
    print("- 「なぜ機能するか」を理解して適切に適用")
    print("- A/Bテストで効果を検証")


if __name__ == '__main__':
    main()
