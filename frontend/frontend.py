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


def render_final_verdict(final_data: dict):
    """
    最終判定の詳細表示

    Args:
        final_data: FinalVerdictの辞書形式
            - verdict: "承認" | "否決" | "保留"
            - summary: JUDGE統合分析結果（サマリー、論点、推奨事項を含む）
            - vote_count: {"賛成": n, "反対": m}
            - agent_verdicts: 各エージェントの判定リスト
    """
    verdict = final_data.get("verdict", "")
    summary = final_data.get("summary", "")
    vote_count = final_data.get("vote_count", {})

    # 判定による色分け
    verdict_color = '#059669' if verdict == '承認' else '#DC2626' if verdict == '否決' else '#F59E0B'

    # 投票数
    approve_count = vote_count.get("賛成", 0)
    reject_count = vote_count.get("反対", 0)

    # メインの最終判定表示
    st.markdown(f"""
    <div class="final-verdict">
        <h2>⚖️ JUDGE 統合分析</h2>
        <h1 style="color: {verdict_color}; font-size: 2.5rem; margin: 1rem 0;">
            {verdict}
        </h1>
        <div style="display: flex; justify-content: center; gap: 2rem; margin: 1.5rem 0;">
            <div style="text-align: center;">
                <div style="font-size: 2rem; color: #059669; font-weight: bold;">{approve_count}</div>
                <div style="color: #64748B; font-size: 0.9rem;">賛成</div>
            </div>
            <div style="font-size: 2rem; color: #CBD5E1;">vs</div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; color: #DC2626; font-weight: bold;">{reject_count}</div>
                <div style="color: #64748B; font-size: 0.9rem;">反対</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # JUDGE統合分析結果を表示（サマリーに含まれる構造化されたテキスト）
    # summaryは以下の形式:
    # {分析サマリー}
    #
    # 【主要な論点】
    # ・論点1
    # ・論点2
    #
    # 【推奨事項】
    # {推奨事項}
    if summary:
        # サマリーをHTMLに変換（改行を<br>に、【】をスタイリング）
        summary_html = summary.replace("\n", "<br>")
        summary_html = summary_html.replace("【主要な論点】", '<strong style="color: #0891B2;">【主要な論点】</strong>')
        summary_html = summary_html.replace("【推奨事項】", '<strong style="color: #7C3AED;">【推奨事項】</strong>')

        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
            <div style="color: #475569; line-height: 1.8; font-size: 0.95rem;">
                {summary_html}
            </div>
        </div>
        """, unsafe_allow_html=True)



def invoke_magi_agent(question: str, runtime_arn: str) -> Generator:
    """
    AgentCore Runtimeを呼び出してMAGIエージェントを実行
    ストリーミングレスポンスを返す

    Args:
        question: ユーザーの問いかけ
        runtime_arn: AgentCore Runtime ARN
            例: arn:aws:bedrock-agentcore:ap-northeast-1:262152767881:runtime/backend-bLxzrQ5K5B

    Yields:
        dict: イベント辞書（agent_start, thinking, verdict, final など）
    """
    # AgentCore用クライアント（bedrock-agent-runtimeではない！）
    client = boto3.client('bedrock-agentcore', region_name='ap-northeast-1')

    try:
        # ペイロードをJSON → bytes に変換
        payload = json.dumps({"question": question}).encode('utf-8')

        # AgentCore Runtime を呼び出し
        response = client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            payload=payload,
            contentType='application/json',
            accept='application/json'
        )

        # StreamingBodyからデータを読み取り
        # AgentCoreはストリーミングレスポンスを返す
        streaming_body = response.get('response')
        if streaming_body:
            # ストリーミングデータを行単位で処理
            # バイト列バッファ（UTF-8マルチバイト文字の分割対策）
            byte_buffer = b""
            text_buffer = ""

            for chunk in streaming_body.iter_chunks():
                byte_buffer += chunk

                # デコード可能な部分だけデコード
                try:
                    decoded = byte_buffer.decode('utf-8')
                    byte_buffer = b""  # 成功したらバッファをクリア
                except UnicodeDecodeError as e:
                    # 途中で切れている場合は、有効な部分だけデコード
                    valid_end = e.start
                    decoded = byte_buffer[:valid_end].decode('utf-8')
                    byte_buffer = byte_buffer[valid_end:]  # 残りは次のチャンクで

                text_buffer += decoded

                # 改行区切りでイベントを分割
                # AgentCoreは SSE形式（data: {...}）で返す
                while '\n' in text_buffer:
                    line, text_buffer = text_buffer.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue

                    # SSE形式: "data: {...}" からJSONを抽出
                    if line.startswith("data: "):
                        json_str = line[6:]  # "data: " を除去
                        try:
                            event = json.loads(json_str)
                            yield event
                        except json.JSONDecodeError:
                            # JSONでない場合はテキストとしてyield
                            yield {"type": "text", "content": json_str}
                    else:
                        # data: で始まらない場合はそのままJSONを試行
                        try:
                            event = json.loads(line)
                            yield event
                        except json.JSONDecodeError:
                            yield {"type": "text", "content": line}

            # 残りのバッファを処理
            if byte_buffer:
                try:
                    text_buffer += byte_buffer.decode('utf-8')
                except UnicodeDecodeError:
                    pass  # デコードできない残りは無視

            if text_buffer.strip():
                line = text_buffer.strip()
                # SSE形式: "data: {...}" からJSONを抽出
                if line.startswith("data: "):
                    json_str = line[6:]
                    try:
                        event = json.loads(json_str)
                        yield event
                    except json.JSONDecodeError:
                        yield {"type": "text", "content": json_str}
                else:
                    try:
                        event = json.loads(line)
                        yield event
                    except json.JSONDecodeError:
                        yield {"type": "text", "content": line}

    except Exception as e:
        yield {"type": "error", "message": f"エラーが発生しました: {str(e)}"}


def mock_magi_response(question: str) -> dict:
    """
    デモ用のモックレスポンス（判定モード）
    実際のAgentCore接続前のテスト用

    FinalVerdict形式に合わせた構造を返す
    summaryはJUDGE統合分析の形式（サマリー、主要な論点、推奨事項）
    """
    judge_summary = f"""3つのエージェントの分析を総合すると、「{question}」については科学的・論理的な妥当性と人間的価値の両面から肯定的な評価が得られました。一方、安全性とリスク管理の観点からは慎重な対応が求められています。

【主要な論点】
・科学的根拠に基づく判断の重要性
・関係者への影響とリスク評価
・人間的感情と社会的影響への配慮

【推奨事項】
適切なリスク管理体制を整えた上で、段階的に実行することを推奨します。定期的な評価と必要に応じた軌道修正を行いながら進めてください。"""

    return {
        "melchior": {
            "verdict": "賛成",
            "reasoning": f"論理的観点から分析すると、「{question}」について科学的根拠に基づき賛成します。データと事実に基づいた判断です。",
            "confidence": 85
        },
        "balthasar": {
            "verdict": "反対",
            "reasoning": f"保護的観点から、「{question}」にはリスクが伴います。安全性を最優先に考え、慎重な対応を推奨します。",
            "confidence": 70
        },
        "casper": {
            "verdict": "賛成",
            "reasoning": f"人間的感情の観点から、「{question}」は人々の幸福に寄与する可能性があります。感情面でのメリットを重視します。",
            "confidence": 80
        },
        "final": {
            "verdict": "承認",
            "summary": judge_summary,
            "vote_count": {"賛成": 2, "反対": 1},
            "agent_verdicts": [
                {"agent_name": "MELCHIOR-1", "verdict": "賛成", "reasoning": f"論理的観点から分析すると、「{question}」について科学的根拠に基づき賛成します。", "confidence": 0.85},
                {"agent_name": "BALTHASAR-2", "verdict": "反対", "reasoning": f"保護的観点から、「{question}」にはリスクが伴います。", "confidence": 0.70},
                {"agent_name": "CASPER-3", "verdict": "賛成", "reasoning": f"人間的感情の観点から、「{question}」は人々の幸福に寄与する可能性があります。", "confidence": 0.80}
            ]
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
            value=st.session_state.get('runtime_arn', 'arn:aws:bedrock-agentcore:ap-northeast-1:262152767881:runtime/backend-bLxzrQ5K5B'),
            placeholder="arn:aws:bedrock-agentcore:ap-northeast-1:...",
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
                    render_final_verdict(response["final"])
                    
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
                    # -----------------------------------------------------
                    # ストリーミングイベントを処理
                    # -----------------------------------------------------
                    # 各エージェントの思考内容を蓄積
                    agent_thinking = {
                        "MELCHIOR-1": "",
                        "BALTHASAR-2": "",
                        "CASPER-3": ""
                    }

                    # 各エージェントの判定結果
                    agent_verdicts = {}

                    # 最終判定データ
                    final_data = None

                    # 現在処理中のエージェント
                    current_agent = None

                    # 処理中表示（ステータス用プレースホルダー）
                    status_placeholder = st.empty()
                    status_placeholder.info("🔮 MAGI システム分析中...")

                    # -----------------------------------------------------
                    # イベントループ（データ収集のみ）
                    # -----------------------------------------------------
                    for event in invoke_magi_agent(question, runtime_arn):
                        event_type = event.get("type")

                        if event_type == "agent_start":
                            current_agent = event.get("agent")
                            agent_thinking[current_agent] = ""
                            status_placeholder.info(f"🔮 {current_agent} 分析中...")

                        elif event_type == "thinking":
                            if current_agent:
                                agent_thinking[current_agent] += event.get("content", "")

                        elif event_type == "verdict":
                            if current_agent:
                                agent_verdicts[current_agent] = event.get("data", {})

                        elif event_type == "agent_complete":
                            current_agent = None

                        elif event_type == "judge_start":
                            status_placeholder.info("⚖️ JUDGE 統合分析中...")

                        elif event_type == "judge_complete":
                            status_placeholder.info("✅ 最終判定を生成中...")

                        elif event_type == "final":
                            final_data = event.get("data", {})
                            status_placeholder.empty()

                        elif event_type == "error":
                            status_placeholder.empty()
                            st.error(event.get("message", "不明なエラー"))

                    # -----------------------------------------------------
                    # 結果を表示（イベント収集完了後）
                    # -----------------------------------------------------
                    if agent_verdicts:
                        # 3カラムで各エージェントの結果を表示
                        col1, col2, col3 = st.columns(3)

                        agent_configs = [
                            ("MELCHIOR-1", "🔬 科学者 - 論理的分析", "melchior", col1),
                            ("BALTHASAR-2", "🛡️ 母親 - 保護的観点", "balthasar", col2),
                            ("CASPER-3", "💜 女性 - 人間的感情", "casper", col3),
                        ]

                        for agent_name, role, agent_class, col in agent_configs:
                            verdict_data = agent_verdicts.get(agent_name, {})
                            verdict = verdict_data.get("verdict", "")
                            reasoning = verdict_data.get("reasoning", "")
                            thinking = agent_thinking.get(agent_name, "")

                            verdict_css = "verdict-approve" if verdict == "賛成" else "verdict-reject"

                            with col:
                                # メインカード
                                st.markdown(f"""
                                <div class="agent-card {agent_class}">
                                    <div class="agent-name">{agent_name}</div>
                                    <div class="agent-role">{role}</div>
                                    <div style="margin: 1rem 0;">
                                        <span class="verdict {verdict_css}">{verdict}</span>
                                    </div>
                                    <div class="reasoning">{reasoning}</div>
                                </div>
                                """, unsafe_allow_html=True)

                                # 思考プロセスをエキスパンダーで表示
                                if thinking:
                                    with st.expander("💭 思考プロセスを見る"):
                                        st.markdown(thinking)

                    # 最終判定
                    if final_data:
                        render_final_verdict(final_data)

                        # セッション状態に保存
                        st.session_state.magi_results = {
                            "verdicts": agent_verdicts,
                            "thinking": agent_thinking,
                            "final": final_data
                        }
        
        # アシスタントメッセージを履歴に追加
        st.session_state.messages.append({
            "role": "assistant",
            "content": "MAGI判定完了" if is_judge_mode else "3賢者の回答完了"
        })


if __name__ == "__main__":
    main()
