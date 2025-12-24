"""
MAGI System Frontend
Streamlit UI for the MAGI decision-making system
"""

import streamlit as st
import boto3
import json
from typing import Generator

# ページ設定
st.set_page_config(
    page_title="MAGI System",
    page_icon="🔮",
    layout="wide"
)

# カスタムCSS - ライトモード + エヴァンゲリオンカラー
st.markdown("""
<style>
    /* ベーススタイル */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* ヘッダー */
    .magi-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 2px solid #F97316;
        box-shadow: 0 4px 6px -1px rgba(249, 115, 22, 0.1);
    }
    .magi-title {
        color: #F97316;
        font-size: 2.5rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(249, 115, 22, 0.2);
    }
    .magi-subtitle {
        color: #64748B;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* エージェントカード - ライトモード */
    .agent-card {
        padding: 1.5rem;
        border-radius: 16px;
        min-height: 200px;
        background: #FFFFFF;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 2px solid #E2E8F0;
    }
    .agent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px -2px rgba(0, 0, 0, 0.15);
    }
    
    /* MELCHIOR - シアン/ブルー（科学者） */
    .melchior {
        border: 2px solid #0891B2;
        background: linear-gradient(135deg, #FFFFFF 0%, #ECFEFF 100%);
    }
    .melchior .agent-name {
        color: #0891B2;
    }
    
    /* BALTHASAR - レッド/オレンジ（母親） */
    .balthasar {
        border: 2px solid #DC2626;
        background: linear-gradient(135deg, #FFFFFF 0%, #FEF2F2 100%);
    }
    .balthasar .agent-name {
        color: #DC2626;
    }
    
    /* CASPER - パープル（女性） */
    .casper {
        border: 2px solid #7C3AED;
        background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%);
    }
    .casper .agent-name {
        color: #7C3AED;
    }
    
    .agent-name {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .agent-role {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #E2E8F0;
    }
    
    /* 判定理由 */
    .reasoning {
        color: #475569;
        font-size: 0.9rem;
        line-height: 1.6;
        margin-top: 0.5rem;
    }
    
    /* 会話モード用レスポンス */
    .chat-response {
        color: #1E293B;
        font-size: 0.95rem;
        line-height: 1.7;
        margin-top: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 8px;
    }
    
    /* モード選択ボタン */
    .mode-selector {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .mode-btn {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: 2px solid #E2E8F0;
        background: #FFFFFF;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .mode-btn.active {
        border-color: #F97316;
        background: #FFF7ED;
        color: #F97316;
    }
    
    /* 判定バッジ */
    .verdict {
        padding: 0.5rem 1.5rem;
        border-radius: 9999px;
        font-weight: bold;
        display: inline-block;
        font-size: 0.9rem;
    }
    .verdict-approve { 
        background: #059669; 
        color: white;
        box-shadow: 0 2px 4px rgba(5, 150, 105, 0.3);
    }
    .verdict-reject { 
        background: #DC2626; 
        color: white;
        box-shadow: 0 2px 4px rgba(220, 38, 38, 0.3);
    }
    .verdict-pending { 
        background: #F59E0B; 
        color: white;
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);
    }
    
    /* 最終判定 - NERVオレンジアクセント */
    .final-verdict {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFF7ED 100%);
        border-radius: 16px;
        margin-top: 2rem;
        border: 3px solid #F97316;
        box-shadow: 0 8px 16px -4px rgba(249, 115, 22, 0.2);
    }
    .final-verdict h2 {
        color: #0F172A;
        margin-bottom: 1rem;
    }
    .final-verdict p {
        color: #475569;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* サイドバー */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border-right: 1px solid #E2E8F0;
    }
    
    /* チャット入力 */
    .stChatInput {
        border-color: #F97316 !important;
    }
    .stChatInput:focus-within {
        border-color: #F97316 !important;
        box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """セッション状態の初期化"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "magi_results" not in st.session_state:
        st.session_state.magi_results = {
            "melchior": None,
            "balthasar": None,
            "casper": None,
            "final": None
        }


def render_header():
    """ヘッダー表示"""
    st.markdown("""
    <div class="magi-header">
        <div class="magi-title">🔮 MAGI SYSTEM</div>
        <div class="magi-subtitle">Multi-Agent Governance Intelligence | NERV</div>
    </div>
    """, unsafe_allow_html=True)


def render_agent_columns():
    """3カラムのエージェント表示"""
    col1, col2, col3 = st.columns(3)
    return col1, col2, col3


def render_agent_card(agent_name: str, agent_role: str, agent_class: str, verdict: str = None, reasoning: str = None):
    """エージェントカードを判定結果込みで表示"""
    verdict_html = ""
    reasoning_html = ""
    
    if verdict:
        verdict_class = "verdict-approve" if verdict == "賛成" else "verdict-reject" if verdict == "反対" else "verdict-pending"
        verdict_html = f'<div style="margin: 1rem 0;"><span class="verdict {verdict_class}">{verdict}</span></div>'
        reasoning_html = f'<div class="reasoning">{reasoning}</div>'
    
    st.markdown(f"""
    <div class="agent-card {agent_class}">
        <div class="agent-name">{agent_name}</div>
        <div class="agent-role">{agent_role}</div>
        {verdict_html}
        {reasoning_html}
    </div>
    """, unsafe_allow_html=True)


def render_verdict(verdict: str, reasoning: str, container):
    """判定結果の表示（後方互換性のため残す）"""
    verdict_class = "verdict-approve" if verdict == "賛成" else "verdict-reject" if verdict == "反対" else "verdict-pending"
    container.markdown(f"""
    <div style="padding: 1rem; border: 2px solid #E2E8F0; border-radius: 12px; background: #FFFFFF; margin-top: 0.5rem;">
        <div class="verdict {verdict_class}">{verdict}</div>
        <div class="reasoning" style="margin-top: 0.75rem; color: #475569; line-height: 1.6;">{reasoning}</div>
    </div>
    """, unsafe_allow_html=True)


def render_final_verdict(verdict: str, summary: str):
    """最終判定の表示"""
    verdict_color = '#059669' if verdict == '承認' else '#DC2626' if verdict == '否決' else '#F59E0B'
    st.markdown(f"""
    <div class="final-verdict">
        <h2>🔮 MAGI 最終判定</h2>
        <h1 style="color: {verdict_color}; font-size: 2.5rem; margin: 1rem 0;">
            {verdict}
        </h1>
        <p>{summary}</p>
    </div>
    """, unsafe_allow_html=True)


def invoke_magi_agent(question: str, runtime_arn: str) -> Generator:
    """
    AgentCore Runtimeを呼び出してMAGIエージェントを実行
    ストリーミングレスポンスを返す
    """
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    try:
        response = client.invoke_agent(
            agentId=runtime_arn,
            agentAliasId='TSTALIASID',
            sessionId=st.session_state.get('session_id', 'default-session'),
            inputText=question,
            enableTrace=True
        )
        
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk_data = event['chunk']
                if 'bytes' in chunk_data:
                    yield chunk_data['bytes'].decode('utf-8')
                    
    except Exception as e:
        yield f"エラーが発生しました: {str(e)}"


def mock_magi_response(question: str) -> dict:
    """
    デモ用のモックレスポンス（判定モード）
    実際のAgentCore接続前のテスト用
    """
    return {
        "melchior": {
            "verdict": "賛成",
            "reasoning": f"論理的観点から分析すると、「{question}」について科学的根拠に基づき賛成します。データと事実に基づいた判断です。"
        },
        "balthasar": {
            "verdict": "反対",
            "reasoning": f"保護的観点から、「{question}」にはリスクが伴います。安全性を最優先に考え、慎重な対応を推奨します。"
        },
        "casper": {
            "verdict": "賛成",
            "reasoning": f"人間的感情の観点から、「{question}」は人々の幸福に寄与する可能性があります。感情面でのメリットを重視します。"
        },
        "final": {
            "verdict": "承認",
            "summary": "2対1で承認されました。科学的妥当性と人間的価値を考慮し、適切なリスク管理のもとで実行を推奨します。"
        }
    }


def mock_chat_response(question: str) -> dict:
    """
    デモ用のモックレスポンス（会話モード）
    3賢者がそれぞれの観点から自由に回答
    """
    return {
        "melchior": {
            "response": f"科学的な観点からお答えします。「{question}」について、データや論理に基づいて考えると、まず事実関係を整理することが重要です。客観的な分析を行い、根拠に基づいた結論を導き出すことをお勧めします。"
        },
        "balthasar": {
            "response": f"安全性と保護の観点からお話しします。「{question}」については、関係者への影響やリスクを慎重に考慮する必要があります。長期的な視点で、皆が安心できる選択を心がけましょう。"
        },
        "casper": {
            "response": f"人間的な感情の観点からお伝えします。「{question}」について、人々の気持ちや社会的な影響を考えると、共感と理解が大切です。心に寄り添った判断ができるといいですね。"
        }
    }


def render_chat_card(agent_name: str, agent_role: str, agent_class: str, response: str):
    """会話モード用のエージェントカード"""
    st.markdown(f"""
    <div class="agent-card {agent_class}">
        <div class="agent-name">{agent_name}</div>
        <div class="agent-role">{agent_role}</div>
        <div class="chat-response">{response}</div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """メインアプリケーション"""
    init_session_state()
    render_header()
    
    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # モード選択
        st.subheader("🎯 モード選択")
        chat_mode = st.radio(
            "モードを選択",
            ["⚖️ 判定モード", "💬 会話モード"],
            index=0,
            help="判定モード: 3賢者が賛成/反対を判定\n会話モード: 3賢者と自由に対話"
        )
        is_judge_mode = chat_mode == "⚖️ 判定モード"
        
        st.divider()
        
        # AgentCore Runtime ARN設定
        runtime_arn = st.text_input(
            "AgentCore Runtime ARN",
            value=st.session_state.get('runtime_arn', ''),
            placeholder="arn:aws:bedrock:us-east-1:...",
            help="バックエンドのAgentCore Runtime ARNを入力してください"
        )
        st.session_state['runtime_arn'] = runtime_arn
        
        # デモモード切り替え
        demo_mode = st.checkbox(
            "デモモード",
            value=True,
            help="AgentCore接続なしでUIをテストできます"
        )
        
        st.divider()
        st.markdown("""
        ### 📖 MAGIシステムについて
        
        **MELCHIOR-1** (科学者)
        - 論理的・科学的分析
        - データに基づく判断
        
        **BALTHASAR-2** (母親)
        - 保護的・安全重視
        - リスク評価
        
        **CASPER-3** (女性)
        - 人間的・感情的観点
        - 社会的影響の考慮
        """)
    
    # メインコンテンツ
    if is_judge_mode:
        st.subheader("⚖️ MAGIに判定を仰ぐ")
        placeholder_text = "判断を仰ぎたい事項を入力してください..."
    else:
        st.subheader("💬 3賢者と対話する")
        placeholder_text = "3賢者に質問してください..."
    
    # チャット履歴表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 入力フォーム
    if question := st.chat_input(placeholder_text):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        
        # MAGIの応答
        with st.chat_message("assistant"):
            if is_judge_mode:
                st.write("🔮 MAGI 判定システム起動中...")
            else:
                st.write("🔮 3賢者が回答を準備中...")
            
            if demo_mode:
                # デモモード: モックレスポンス
                import time
                
                with st.spinner("分析中..."):
                    time.sleep(1)
                
                if is_judge_mode:
                    # 判定モード
                    response = mock_magi_response(question)
                    
                    # 3カラムで各エージェントの結果を表示（カード内に判定含む）
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        render_agent_card(
                            "MELCHIOR-1",
                            "🔬 科学者 - 論理的分析",
                            "melchior",
                            response["melchior"]["verdict"],
                            response["melchior"]["reasoning"]
                        )
                    
                    with col2:
                        render_agent_card(
                            "BALTHASAR-2",
                            "🛡️ 母親 - 保護的観点",
                            "balthasar",
                            response["balthasar"]["verdict"],
                            response["balthasar"]["reasoning"]
                        )
                    
                    with col3:
                        render_agent_card(
                            "CASPER-3",
                            "💜 女性 - 人間的感情",
                            "casper",
                            response["casper"]["verdict"],
                            response["casper"]["reasoning"]
                        )
                    
                    # 最終判定
                    render_final_verdict(
                        response["final"]["verdict"],
                        response["final"]["summary"]
                    )
                    
                    # 結果を保存
                    st.session_state.magi_results = response
                    
                else:
                    # 会話モード
                    response = mock_chat_response(question)
                    
                    # 3カラムで各エージェントの回答を表示
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        render_chat_card(
                            "MELCHIOR-1",
                            "🔬 科学者 - 論理的分析",
                            "melchior",
                            response["melchior"]["response"]
                        )
                    
                    with col2:
                        render_chat_card(
                            "BALTHASAR-2",
                            "🛡️ 母親 - 保護的観点",
                            "balthasar",
                            response["balthasar"]["response"]
                        )
                    
                    with col3:
                        render_chat_card(
                            "CASPER-3",
                            "💜 女性 - 人間的感情",
                            "casper",
                            response["casper"]["response"]
                        )
                
            else:
                # 本番モード: AgentCore呼び出し
                if not runtime_arn:
                    st.error("AgentCore Runtime ARNを設定してください")
                else:
                    response_text = ""
                    response_placeholder = st.empty()
                    
                    for chunk in invoke_magi_agent(question, runtime_arn):
                        response_text += chunk
                        response_placeholder.markdown(response_text)
                    
                    # レスポンスをパースして表示
                    try:
                        parsed = json.loads(response_text)
                        st.session_state.magi_results = parsed
                    except json.JSONDecodeError:
                        st.write(response_text)
        
        # アシスタントメッセージを履歴に追加
        st.session_state.messages.append({
            "role": "assistant",
            "content": "MAGI判定完了" if is_judge_mode else "3賢者の回答完了"
        })


if __name__ == "__main__":
    main()
