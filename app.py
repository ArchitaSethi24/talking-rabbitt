import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import json, re, io

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Talking Rabbitt",
    page_icon="🐇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS (dark premium theme) ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    background-color: #0a0a0f !important;
    color: #e8e8e8 !important;
    font-family: 'DM Serif Display', serif;
}
.stApp { background: #0a0a0f; }

/* Header */
.rabbitt-header {
    display: flex; align-items: center; gap: 14px;
    padding: 0 0 24px 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 32px;
}
.rabbitt-logo {
    width: 42px; height: 42px; border-radius: 10px;
    background: linear-gradient(135deg, #00ff9d, #00c8ff);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; box-shadow: 0 0 24px rgba(0,255,157,0.3);
}
.rabbitt-title { font-family: 'DM Mono', monospace; font-size: 20px; color: #fff; letter-spacing: 2px; }
.rabbitt-title span { color: #00ff9d; }
.rabbitt-sub { font-family: 'DM Mono', monospace; font-size: 10px; color: #444; letter-spacing: 4px; text-transform: uppercase; }

/* Insight cards */
.insight-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 3px solid #00ff9d;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 10px;
    font-size: 14px; line-height: 1.7; color: #ccc;
}
.insight-num { font-family: 'DM Mono', monospace; font-size: 11px; color: #00ff9d; margin-right: 8px; }
.briefing-label {
    font-family: 'DM Mono', monospace; font-size: 11px;
    color: #00ff9d; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 8px;
}

/* Chat messages */
.user-msg {
    background: rgba(0,255,157,0.06);
    border: 1px solid rgba(0,255,157,0.2);
    border-radius: 18px 18px 4px 18px;
    padding: 14px 18px; margin: 8px 0 8px 20%;
    font-size: 14px; line-height: 1.7; color: #e8e8e8;
}
.ai-msg {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px 18px 18px 4px;
    padding: 14px 18px; margin: 8px 20% 8px 0;
    font-size: 14px; line-height: 1.7; color: #e0e0e0;
}
.ai-label {
    font-family: 'DM Mono', monospace; font-size: 11px;
    color: #00ff9d; margin-bottom: 6px; letter-spacing: 1px;
}

/* Inputs */
.stTextInput > div > div > input, .stTextArea textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #e8e8e8 !important;
    font-family: 'DM Serif Display', serif !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00ff9d, #00c8ff) !important;
    color: #000 !important; border: none !important;
    border-radius: 10px !important; font-family: 'DM Mono', monospace !important;
    font-weight: 700 !important; letter-spacing: 1px !important;
    padding: 10px 24px !important;
}
.stFileUploader {
    background: rgba(0,255,157,0.03) !important;
    border: 1.5px dashed rgba(0,255,157,0.3) !important;
    border-radius: 16px !important;
}
/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rabbitt-header">
  <div class="rabbitt-logo">🐇</div>
  <div>
    <div class="rabbitt-title">TALKING <span>RABBITT</span></div>
    <div class="rabbitt-sub">Conversational Intelligence Layer</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "briefing_done" not in st.session_state:
    st.session_state.briefing_done = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_df_summary(df: pd.DataFrame) -> str:
    """Compact summary injected into every LLM prompt."""
    buf = io.StringIO()
    df.info(buf=buf)
    return (
        f"Columns: {list(df.columns)}\n"
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
        f"Dtypes:\n{df.dtypes.to_string()}\n"
        f"Sample (first 5 rows):\n{df.head(5).to_string(index=False)}\n"
        f"Numeric stats:\n{df.describe().to_string()}"
    )

def ask_llm(question: str, df: pd.DataFrame, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        "You are Talking Rabbitt — a sharp, senior business analyst embedded inside an enterprise data platform. "
        "You answer questions about a dataset in 2-4 sentences: clear, direct, and insight-driven. "
        "Never say 'I cannot' — always derive the best possible answer from the data context given. "
        "End each answer with one short follow-up question the executive should consider next.\n\n"
        f"DATASET CONTEXT:\n{get_df_summary(df)}\n\n"
        f"QUESTION: {question}"
    )
    resp = model.generate_content(prompt)
    return resp.text.strip()

def generate_briefing_v2(df: pd.DataFrame, api_key: str) -> list[str]:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        "You are a senior data analyst. Given this dataset, produce EXACTLY 3 executive insights a CEO would care about. "
        "Return ONLY a JSON array of 3 strings. No markdown, no backticks, no extra text.\n\n"
        f"DATASET:\n{get_df_summary(df)}"
    )
    resp = model.generate_content(prompt)
    text = resp.text.strip()
    try:
        arr = json.loads(re.search(r'\[.*\]', text, re.DOTALL).group())
        return arr[:3]
    except Exception:
        return [s.strip("•-– 0123456789.").strip() for s in text.split("\n") if s.strip()][:3]

def smart_chart(df: pd.DataFrame, question: str):
    """Pick best chart based on question keywords."""
    q = question.lower()
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    if not num_cols:
        return None

    y_col = num_cols[0]
    # pick best y col from question
    for col in num_cols:
        if col.lower() in q:
            y_col = col
            break

    if "trend" in q or "over time" in q or "month" in q or "week" in q or "day" in q:
        time_col = next((c for c in df.columns if any(t in c.lower() for t in ["date","month","week","time","day","quarter"])), cat_cols[0] if cat_cols else None)
        if time_col:
            agg = df.groupby(time_col)[y_col].sum().reset_index()
            fig = px.line(agg, x=time_col, y=y_col, title=f"{y_col} over {time_col}",
                          color_discrete_sequence=["#00ff9d"])
        else:
            return None
    elif cat_cols:
        x_col = cat_cols[0]
        for col in cat_cols:
            if col.lower() in q:
                x_col = col
                break
        agg = df.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False).head(10)
        fig = px.bar(agg, x=x_col, y=y_col, title=f"{y_col} by {x_col}",
                     color_discrete_sequence=["#00ff9d"])
    else:
        return None

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(color="#aaa", family="DM Mono, monospace"),
        title_font=dict(color="#fff", size=13),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
        margin=dict(t=40, b=20, l=10, r=10),
    )
    return fig

# ── Sidebar: API Key ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key,
                             placeholder="AIza...")
    if api_key:
        st.session_state.api_key = api_key
    st.markdown("---")
    st.markdown("**Suggested Questions:**")
    suggestions = [
        "Which region had highest revenue?",
        "Who is the top sales rep?",
        "Show me the monthly trend",
        "What product sells the most?",
        "Compare performance across categories",
    ]
    for s in suggestions:
        if st.button(s, key=f"sug_{s}"):
            st.session_state._pending_question = s

# ── Step 1: Upload ─────────────────────────────────────────────────────────────
if st.session_state.df is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 20px 0 32px;">
          <div style="font-size:52px; margin-bottom:12px;">🐇</div>
          <h1 style="font-size:34px; font-weight:400; margin:0; letter-spacing:-1px;">
            Talk to your <span style="background:linear-gradient(90deg,#00ff9d,#00c8ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">data</span>
          </h1>
          <p style="color:#555; margin-top:10px; font-size:14px; line-height:1.7;">
            Upload a sales CSV. Ask questions in plain English.<br>No filters. No dashboards. Just answers.
          </p>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader("Drop your CSV here", type=["csv"], label_visibility="collapsed")

        if not uploaded:
            st.markdown("<div style='text-align:center;color:#444;font-size:13px;margin-top:8px;font-family:monospace;'>↑ or use a demo file →</div>", unsafe_allow_html=True)
            if st.button("Load Demo Data  →"):
                import numpy as np
                np.random.seed(42)
                demo = pd.DataFrame({
                    "Month": ["Jan","Feb","Mar","Apr","May","Jun"] * 4,
                    "Region": (["North"]*6 + ["South"]*6 + ["East"]*6 + ["West"]*6),
                    "Sales_Rep": [f"Rep_{i%8+1}" for i in range(24)],
                    "Product": ["SKU-001","SKU-002","SKU-003","SKU-007"] * 6,
                    "Revenue": np.random.randint(120000, 420000, 24),
                    "Units_Sold": np.random.randint(80, 350, 24),
                    "Returns": np.random.randint(2, 30, 24),
                })
                st.session_state.df = demo
                st.session_state.filename = "demo_sales_q1.csv"
                st.rerun()

        if uploaded:
            df = pd.read_csv(uploaded)
            st.session_state.df = df
            st.session_state.filename = uploaded.name
            st.rerun()

# ── Step 2: Briefing ───────────────────────────────────────────────────────────
elif not st.session_state.briefing_done:
    df = st.session_state.df
    fname = st.session_state.get("filename", "your file")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"""
        <div class="briefing-label">◆ Executive Briefing</div>
        <h2 style="font-size:26px;font-weight:400;margin:0 0 6px;">I've analyzed <span style="color:#00ff9d">{fname}</span></h2>
        <p style="color:#555;font-size:13px;margin-bottom:24px;">Here's what I found before you even asked:</p>
        """, unsafe_allow_html=True)

        if st.session_state.api_key:
            with st.spinner(""):
                insights = generate_briefing_v2(df, st.session_state.api_key)
        else:
            insights = [
                f"Your dataset has {df.shape[0]} records across {df.shape[1]} dimensions — ready for analysis.",
                f"Top numeric metric detected: {df.select_dtypes(include='number').columns[0] if len(df.select_dtypes(include='number').columns) else 'N/A'}",
                "Add your Gemini API key in the sidebar to unlock AI-powered insights.",
            ]

        for i, insight in enumerate(insights):
            st.markdown(f"""
            <div class="insight-card">
              <span class="insight-num">0{i+1}</span>{insight}
            </div>
            """, unsafe_allow_html=True)

        if st.button("Start asking questions  →"):
            st.session_state.briefing_done = True
            st.rerun()

    with col2:
        num_cols = df.select_dtypes(include="number").columns
        cat_cols = df.select_dtypes(exclude="number").columns
        if len(num_cols) > 0 and len(cat_cols) > 0:
            agg = df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index().sort_values(num_cols[0], ascending=False).head(8)
            fig = px.bar(agg, x=cat_cols[0], y=num_cols[0],
                         title=f"Auto-detected: {num_cols[0]} by {cat_cols[0]}",
                         color_discrete_sequence=["#00ff9d"])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                font=dict(color="#aaa", family="monospace"), title_font=dict(color="#ccc", size=12),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(t=36,b=10,l=10,r=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
        border-radius:12px;padding:16px 20px;font-family:monospace;font-size:12px;color:#666;">
          <div style="color:#00ff9d;margin-bottom:8px;letter-spacing:2px;">DATASET STATS</div>
          Rows: <span style="color:#ccc">{df.shape[0]}</span><br>
          Columns: <span style="color:#ccc">{df.shape[1]}</span><br>
          Numeric cols: <span style="color:#ccc">{len(df.select_dtypes(include='number').columns)}</span><br>
          File: <span style="color:#ccc">{st.session_state.get('filename','—')}</span>
        </div>
        """, unsafe_allow_html=True)

# ── Step 3: Chat ───────────────────────────────────────────────────────────────
else:
    df = st.session_state.df

    # File indicator
    st.markdown(f"""
    <div style="display:inline-flex;align-items:center;gap:8px;
    background:rgba(0,255,157,0.07);border:1px solid rgba(0,255,157,0.2);
    border-radius:20px;padding:5px 16px;font-family:monospace;
    font-size:11px;color:#00ff9d;margin-bottom:20px;">
      <span style="width:6px;height:6px;border-radius:50%;background:#00ff9d;display:inline-block;"></span>
      {st.session_state.get('filename','data loaded')} · {df.shape[0]} rows
    </div>
    """, unsafe_allow_html=True)

    # Render chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-label">🐇 RABBITT</div><div class="ai-msg">{msg["content"]}</div>', unsafe_allow_html=True)
            if "chart" in msg and msg["chart"] is not None:
                st.plotly_chart(msg["chart"], use_container_width=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Handle pending question from sidebar
    pending = st.session_state.pop("_pending_question", None)

    # Input
    col_input, col_btn = st.columns([6, 1])
    with col_input:
        question = st.text_input("", placeholder="Ask anything about your data...",
                                  label_visibility="collapsed", key="chat_input",
                                  value=pending or "")
    with col_btn:
        send = st.button("↑ Send")

    if (send or pending) and (question or pending):
        q = question or pending
        st.session_state.messages.append({"role": "user", "content": q})

        if not st.session_state.api_key:
            answer = "⚠️ Please add your Gemini API key in the sidebar to enable AI responses."
            chart = None
        else:
            with st.spinner("Analyzing..."):
                answer = ask_llm(q, df, st.session_state.api_key)
                chart = smart_chart(df, q)

        st.session_state.messages.append({"role": "assistant", "content": answer, "chart": chart})
        st.rerun()

    # Reset button
    if st.session_state.messages:
        if st.button("↺ New conversation", key="reset"):
            st.session_state.messages = []
            st.rerun()
