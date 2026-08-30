"""
Streamlit Monitoring Dashboard
================================
ShorlyNot — Banking Security Operations Dashboard v4.0

Network-aware dashboard connecting to the KMS Server via HTTP API.
Displays real-time link health, QBER history chart, escalation status,
network state tiles, session info, and BB84 visualization.

Run with:
    streamlit run dashboard/dashboard_ui.py

Author: ShorlyNot Team
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
except ImportError:
    st.error("Missing dependency: pip install httpx")
    st.stop()

try:
    import plotly.graph_objects as go
except ImportError:
    st.error("Missing dependency: pip install plotly")
    st.stop()

from quantum_engine.bb84_simulator import run_bb84_session


# =============================================================================
# CONFIG
# =============================================================================

st.set_page_config(
    page_title="ShorlyNot",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
<style>
    /* Global dark theme overrides */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    body { 
        background: radial-gradient(circle at 15% 50%, #0d1321, #000000 70%); 
        color: #E2E8F0; 
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: transparent;
    }
    
    /* Header Styling */
    .main-header { 
        font-size: 2.5rem; 
        font-weight: 800; 
        color: #FFFFFF; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(0, 255, 163, 0.2);
    }
    .main-header span { 
        background: linear-gradient(90deg, #00FFA3, #00B8FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header { 
        font-size: 1.1rem; 
        color: #94A3B8; 
        margin-bottom: 2.5rem; 
        border-bottom: 1px solid rgba(255,255,255,0.1); 
        padding-bottom: 1rem; 
        font-weight: 300;
    }
    
    /* Glassmorphic Metric Cards */
    div[data-testid="metric-container"] {
        background: rgba(26, 34, 53, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(0, 255, 163, 0.15);
        border-color: rgba(0, 255, 163, 0.3);
    }
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700 !important;
        font-size: 2rem !important;
        background: linear-gradient(90deg, #00FFA3, #00B8FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: none; /* Text shadow doesn't work well with gradient text */
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        letter-spacing: 1px;
        color: #94A3B8;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    
    /* Premium Buttons */
    div.stButton > button:first-child {
        background: rgba(0, 255, 163, 0.05);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(0, 255, 163, 0.5);
        color: #00FFA3;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        padding: 0.5rem 1rem;
        letter-spacing: 0.5px;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 20px rgba(0, 255, 163, 0.4), inset 0 0 10px rgba(0, 255, 163, 0.2);
        background: rgba(0, 255, 163, 0.1);
        transform: scale(1.02);
        border-color: #00FFA3;
    }
    
    /* FSM Strip - Cyberpunk Style */
    .fsm-strip {
        display: flex; justify-content: space-between; align-items: stretch;
        background: rgba(11, 15, 25, 0.8); 
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05); 
        border-radius: 12px;
        padding: 15px; margin-bottom: 25px;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }
    .fsm-node {
        flex: 1; text-align: center; padding: 12px 10px; margin: 0 5px;
        border-radius: 8px; font-weight: 800; color: #475569;
        background: rgba(30, 41, 59, 0.5); 
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        font-size: 0.9rem;
        letter-spacing: 1px;
        position: relative;
        overflow: hidden;
    }
    .fsm-node small {
        display: block;
        font-size: 0.7rem;
        font-weight: 400;
        margin-top: 4px;
        opacity: 0.7;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Active FSM States */
    .fsm-active {
        color: #0B0F19;
        transform: scale(1.05);
        z-index: 2;
    }
    .fsm-active::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; width: 50%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        animation: shine 2s infinite;
    }
    @keyframes shine {
        100% { left: 200%; }
    }
    
    .fsm-active.l1 { 
        background: linear-gradient(135deg, #00FFA3, #00B8FF); 
        box-shadow: 0 0 25px rgba(0, 255, 163, 0.5); 
        border-color: #00FFA3; 
    }
    .fsm-active.l2 { 
        background: linear-gradient(135deg, #FFD700, #FFA500); 
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.5); 
        border-color: #FFD700; 
    }
    .fsm-active.l3 { 
        background: linear-gradient(135deg, #FF3366, #FF0055);
        box-shadow: 0 0 25px rgba(255, 51, 102, 0.5);
        border-color: #FF3366;
        color: white;
    }
    .fsm-active.l4 { 
        background: linear-gradient(135deg, #FF0000, #990000); 
        box-shadow: 0 0 35px rgba(255, 0, 0, 0.8); 
        color: white; 
        border-color: #FF0000; 
        animation: pulse-danger 1s infinite alternate;
    }
    @keyframes pulse-danger {
        0% { box-shadow: 0 0 20px rgba(255, 0, 0, 0.6); }
        100% { box-shadow: 0 0 40px rgba(255, 0, 0, 1); transform: scale(1.08); }
    }
    
    /* Sleek QBER Bar */
    .qber-container {
        width: 100%; height: 8px; 
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden; margin-top: 8px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
    }
    .qber-fill {
        height: 100%; 
        transition: width 0.8s cubic-bezier(0.22, 1, 0.36, 1), background-color 0.5s;
        border-radius: 10px;
        box-shadow: 0 0 10px currentColor;
    }
    
    /* Code Blocks */
    .stCodeBlock {
        background: rgba(11, 15, 25, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 20, 35, 0.95);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# STATE
# =============================================================================

if "kms_url" not in st.session_state:
    st.session_state.kms_url = "http://localhost:8000"
if "qber_history" not in st.session_state:
    st.session_state.qber_history = []
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True


# =============================================================================
# API HELPERS
# =============================================================================


def api(method, path, **kwargs):
    url = st.session_state.kms_url + path
    try:
        with httpx.Client(timeout=5) as c:
            if method == "GET":
                return c.get(url).json()
            else:
                return c.post(url, **kwargs).json()
    except Exception as e:
        return {"_error": str(e), "status": "OFFLINE"}


# =============================================================================
# HEADER
# =============================================================================

st.markdown(
    """
<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 5px;">
    <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #00FFA3, #00B8FF); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; box-shadow: 0 0 25px rgba(0, 255, 163, 0.3);">🛡️</div>
    <p class="main-header" style="margin:0;"><span>ShorlyNot</span></p>
</div>
<p class="sub-header">Quantum-Safe Transaction Security &nbsp;·&nbsp; Real-Time SOC Monitoring &nbsp;·&nbsp; v4.0</p>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    st.session_state.kms_url = st.text_input("KMS URL", st.session_state.kms_url)

    st.divider()
    st.header("🔑 Key Exchange")

    s_init = st.text_input("Initiator", "Bank_HQ")
    s_peer = st.text_input("Peer", "Branch_001")
    pqc = st.toggle("🧬 Hybrid PQC (Kyber + BB84)")

    if st.button("Create Secure Session", use_container_width=True):
        r = api(
            "POST",
            "/create_session",
            json={"initiator": s_init, "peer": s_peer, "pqc": pqc},
        )
        if "error" in r:
            st.error(f"❌ {r['error']}")
        elif "session_id" in r:
            st.success(
                f"✅ Session `{r['session_id'][:12]}...` | QBER={r.get('qber', 0):.2%}"
            )
            st.code(r["session_id"])
        else:
            st.warning(str(r))

    st.divider()
    st.header("🚨 Attack Control")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 Eve OFF", use_container_width=True):
            api("POST", "/deactivate_eve")
            st.success("Eve deactivated")
    with col2:
        if st.button("🔴 Eve ON", use_container_width=True):
            api("POST", "/activate_eve")
            st.error("Eve active!")

    if st.button("💥 Trigger Attack", use_container_width=True):
        r = api("POST", "/trigger_attack")
        st.error(
            f"🔴 Status: {r.get('status')} | QBER: {r.get('qber', 0):.2%} | "
            f"L{r.get('escalation_level', '?')}"
        )

    if st.button("🔄 Reset System", use_container_width=True):
        api("POST", "/reset")
        st.session_state.qber_history = []
        st.success("System reset → GREEN")

    st.divider()
    st.header("🤖 Automation")
    if st.button("▶️ Execute Demo Sequence", use_container_width=True):
        import time

        with st.status("Running Demo Sequence...", expanded=True) as status:
            st.write("1. System Reset...")
            api("POST", "/reset")
            time.sleep(1.5)

            st.write("2. Initiating Clean Transfer...")
            r = api(
                "POST",
                "/transfer",
                json={
                    "from_acc": "ACC001",
                    "to_acc": "ACC002",
                    "amount": 1000,
                    "note": "Demo Clean",
                },
            )
            if "_error" not in r:
                st.write(f"✅ Transfer Success (QBER: {r.get('qber', 0):.2%})")
            else:
                st.write(f"⚠️ {r['_error']}")

            time.sleep(2)
            st.write("3. Activating Quantum Eavesdropper (Eve)...")
            api("POST", "/activate_eve")
            time.sleep(1.5)

            st.write("4. Attempting Compromised Transfer...")
            r = api(
                "POST",
                "/transfer",
                json={
                    "from_acc": "ACC001",
                    "to_acc": "ACC002",
                    "amount": 2500,
                    "note": "Demo Attack",
                },
            )
            st.write("🚫 Transfer Blocked! Channel compromised.")

            time.sleep(2)
            st.write("5. Triggering Escalation Level 4...")
            for _ in range(4):
                api("POST", "/trigger_attack")
                time.sleep(0.5)
            st.write("💥 L4 LOCKDOWN ACTIVE!")

            time.sleep(2)
            status.update(
                label="Demo Sequence Complete!", state="complete", expanded=False
            )

    st.divider()
    st.session_state.auto_refresh = st.toggle("Auto Refresh (3s)", value=True)


# =============================================================================
# MAIN — LINK STATUS
# =============================================================================

health = api("GET", "/link_status")

if "_error" in health:
    st.error(f"⚠️ KMS offline: {health['_error']}")
    st.info("Start the KMS server: `python kms_server.py`")
    st.stop()

# Track QBER history
current_qber = health.get("qber", 0)
st.session_state.qber_history.append(current_qber)
if len(st.session_state.qber_history) > 50:
    st.session_state.qber_history.pop(0)


# Status row — glassmorphic status badge + metrics
status = health.get("status", "?")
qber = health.get("qber", 0)
entropy = health.get("entropy_score", 0)

# Hero status card
status_cfg = {
    "GREEN": {
        "emoji": "🟢",
        "label": "SECURE",
        "color": "#00FFA3",
        "glow": "rgba(0,255,163,0.25)",
    },
    "YELLOW": {
        "emoji": "🟡",
        "label": "ELEVATED",
        "color": "#FFD700",
        "glow": "rgba(255,215,0,0.25)",
    },
    "RED": {
        "emoji": "🔴",
        "label": "COMPROMISED",
        "color": "#FF3366",
        "glow": "rgba(255,51,102,0.35)",
    },
}.get(
    status,
    {
        "emoji": "⚪",
        "label": "OFFLINE",
        "color": "#475569",
        "glow": "rgba(71,85,105,0.2)",
    },
)

qber_pct = min(100, qber * 100)
fill_color = "#00FFA3" if qber < 0.11 else "#FF3366"

st.markdown(
    f"""
<div style="
    display: flex; align-items: center; gap: 20px;
    background: rgba(26, 34, 53, 0.5); backdrop-filter: blur(12px);
    border: 1px solid {status_cfg["color"]}30; border-radius: 14px;
    padding: 18px 28px; margin-bottom: 20px;
    box-shadow: 0 0 30px {status_cfg["glow"]}, inset 0 0 40px rgba(0,0,0,0.3);
">
    <div style="font-size: 2.8rem; line-height:1;">{status_cfg["emoji"]}</div>
    <div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 800; color: {status_cfg["color"]}; letter-spacing: 3px;">{status_cfg["label"]}</div>
        <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 2px;">Quantum Channel Status</div>
    </div>
    <div style="margin-left: auto; text-align: right;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: {fill_color};">{qber:.2%}</div>
        <div style="color: #94A3B8; font-size: 0.8rem;">QBER &nbsp;|&nbsp; Threshold 11%</div>
        <div class="qber-container" style="width: 180px; margin-top: 6px;">
            <div class="qber-fill" style="width: {qber_pct}%; background: linear-gradient(90deg, {fill_color}, {fill_color}80);"></div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

col2, col3, col4 = st.columns(3)
with col2:
    st.metric("🔑 Keys Issued", health.get("total_keys_issued", 0))
with col3:
    st.metric("🔗 Sessions", health.get("total_sessions", 0))
with col4:
    st.metric("⚠️ Attacks Detected", health.get("attacks_detected", 0))


# =============================================================================
# ESCALATION LEVEL DISPLAY
# =============================================================================

level = health.get("escalation_level", 0)
active_l1 = "fsm-active l1" if level <= 1 else ""
active_l2 = "fsm-active l2" if level == 2 else ""
active_l3 = "fsm-active l3" if level == 3 else ""
active_l4 = "fsm-active l4" if level >= 4 else ""

st.markdown(
    f"""
<div class="fsm-strip">
    <div class="fsm-node {active_l1}">L1: Normal<br><small>Port Rotation</small></div>
    <div style="color: #475569; font-size: 1.2rem; display:flex; align-items:center;">▸</div>
    <div class="fsm-node {active_l2}">L2: Elevated<br><small>IP Failover</small></div>
    <div style="color: #475569; font-size: 1.2rem; display:flex; align-items:center;">▸</div>
    <div class="fsm-node {active_l3}">L3: Critical<br><small>Interface Switch</small></div>
    <div style="color: #475569; font-size: 1.2rem; display:flex; align-items:center;">▸</div>
    <div class="fsm-node {active_l4}">L4: LOCKDOWN<br><small>System Halt</small></div>
</div>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# NETWORK STATE TILES
# =============================================================================

port_val = health.get("current_port", "?")
ip_val = health.get("current_ip", "?")
net_val = health.get("current_network", "?")

st.markdown(
    f"""
<div style="display: flex; gap: 15px; margin-bottom: 10px;">
    <div style="
        flex: 1; padding: 18px 20px; border-radius: 12px;
        background: rgba(26, 34, 53, 0.4); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.06);
    ">
        <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">🔌 Active Port</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #00FFA3;">{port_val}</div>
    </div>
    <div style="
        flex: 1; padding: 18px 20px; border-radius: 12px;
        background: rgba(26, 34, 53, 0.4); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.06);
    ">
        <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">🌐 Active IP</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #00B8FF;">{ip_val}</div>
    </div>
    <div style="
        flex: 1; padding: 18px 20px; border-radius: 12px;
        background: rgba(26, 34, 53, 0.4); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.06);
    ">
        <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">📡 Active Network</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #A78BFA;">{net_val}</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# QBER HISTORY CHART (Plotly)
# =============================================================================

st.markdown("<br>", unsafe_allow_html=True)

col_chart, col_gauge = st.columns([3, 1])

with col_chart:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=st.session_state.qber_history,
            mode="lines+markers",
            name="QBER",
            line=dict(
                color="#00FFA3",
                width=3,
                shape="spline",
                smoothing=1.2,
            ),
            marker=dict(
                size=6,
                color="#00FFA3",
                line=dict(color="#0B0F19", width=2),
                symbol="circle",
            ),
            fill="tozeroy",
            fillcolor="rgba(0, 255, 163, 0.08)",
            hovertemplate="Session %{x}<br>QBER: %{y:.4%}<extra></extra>",
        )
    )
    # Danger zone fill
    fig.add_hrect(
        y0=0.11,
        y1=0.35,
        fillcolor="rgba(255, 51, 102, 0.05)",
        line_width=0,
    )
    fig.add_hline(
        y=0.11,
        line_dash="dot",
        line_color="#FF3366",
        line_width=1.5,
        annotation_text="11% — ABORT THRESHOLD",
        annotation_position="top left",
        annotation_font=dict(color="#FF3366", size=11, family="JetBrains Mono"),
    )
    fig.add_hline(
        y=0.05,
        line_dash="dot",
        line_color="#FFD700",
        line_width=1,
        annotation_text="5% — WARNING",
        annotation_position="bottom left",
        annotation_font=dict(color="#FFD700", size=10, family="JetBrains Mono"),
    )
    fig.update_layout(
        title=dict(
            text="<b>LIVE QBER HISTORY</b>",
            font=dict(size=14, color="#94A3B8", family="Inter"),
            x=0.02,
        ),
        yaxis_title=None,
        xaxis_title=None,
        height=360,
        margin=dict(t=50, b=20, l=50, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8", family="Inter"),
        yaxis=dict(
            range=[
                0,
                max(0.35, max(st.session_state.qber_history) * 1.2)
                if st.session_state.qber_history
                else 0.35,
            ],
            tickformat=".1%",
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
        ),
        hoverlabel=dict(
            bgcolor="#1A2235",
            bordercolor="#00FFA3",
            font_color="#E2E8F0",
            font_family="JetBrains Mono",
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_gauge:
    entropy = health.get("entropy_score", 0)
    fig2 = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=entropy,
            number=dict(
                font=dict(size=42, color="#00FFA3", family="JetBrains Mono"),
                suffix="",
            ),
            title=dict(
                text="<b>ENTROPY</b>",
                font=dict(size=13, color="#94A3B8", family="Inter"),
            ),
            gauge=dict(
                axis=dict(range=[None, 100], tickcolor="#475569", tickwidth=1),
                bar=dict(color="#00FFA3" if entropy > 50 else "#FF3366", thickness=0.3),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                steps=[
                    {"range": [0, 30], "color": "rgba(255, 51, 102, 0.15)"},
                    {"range": [30, 60], "color": "rgba(255, 215, 0, 0.1)"},
                    {"range": [60, 100], "color": "rgba(0, 255, 163, 0.1)"},
                ],
                threshold=dict(
                    line=dict(color="#FF3366", width=2),
                    thickness=0.8,
                    value=50,
                ),
            ),
        )
    )
    fig2.update_layout(
        height=360,
        margin=dict(t=60, b=20, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"),
    )
    st.plotly_chart(fig2, use_container_width=True)


# =============================================================================
# ROUTER STATUS
# =============================================================================

if status == "GREEN":
    st.markdown(
        """
    <div style="
        padding: 14px 20px; border-radius: 10px; margin-bottom: 10px;
        background: rgba(0, 255, 163, 0.06); border-left: 4px solid #00FFA3;
        color: #00FFA3; font-weight: 500;
    ">
        <strong>📡 Quantum Channel:</strong> Secure — QBER within normal parameters. All banking transactions protected.
    </div>
    """,
        unsafe_allow_html=True,
    )
elif status == "RED":
    eve_label = (
        "ACTIVE" if health.get("eve_active") or health.get("eve_mode") else "was active"
    )
    st.markdown(
        f"""
    <div style="
        padding: 14px 20px; border-radius: 10px; margin-bottom: 8px;
        background: rgba(255, 51, 102, 0.08); border-left: 4px solid #FF3366;
        color: #FF3366; font-weight: 500;
    ">
        <strong>📡 Quantum Channel:</strong> COMPROMISED — QBER={qber:.2%} exceeds 11% threshold. Transactions HALTED.
    </div>
    <div style="
        padding: 10px 20px; border-radius: 8px;
        background: rgba(255, 215, 0, 0.06); border-left: 4px solid #FFD700;
        color: #FFD700; font-size: 0.9rem;
    ">
        Eve {eve_label} &nbsp;|&nbsp; Escalation Level {level}
    </div>
    """,
        unsafe_allow_html=True,
    )
elif status == "YELLOW":
    st.markdown(
        """
    <div style="
        padding: 14px 20px; border-radius: 10px; margin-bottom: 10px;
        background: rgba(255, 215, 0, 0.06); border-left: 4px solid #FFD700;
        color: #FFD700; font-weight: 500;
    ">
        <strong>📡 Quantum Channel:</strong> Elevated QBER — monitoring for potential compromise
    </div>
    """,
        unsafe_allow_html=True,
    )


# =============================================================================
# SESSIONS TABLE
# =============================================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
<div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
    <div style="font-size:1.4rem;">📋</div>
    <div style="font-family:'Inter',sans-serif; font-weight:700; font-size:1.2rem; color:#E2E8F0; letter-spacing:1px; text-transform:uppercase;">Active Sessions</div>
</div>
""",
    unsafe_allow_html=True,
)

sessions = api("GET", "/sessions")
sess_list = sessions.get("sessions", [])

if sess_list:
    for s in sess_list:
        sid = s.get("session_id", "?")
        clients = s.get("clients", [])
        client_str = " ↔ ".join(clients[:2]) if clients else "Unknown"
        s_status = s.get("status", "?")
        s_color = (
            "#00FFA3"
            if s_status == "GREEN"
            else ("#FFD700" if s_status == "YELLOW" else "#FF3366")
        )
        with st.expander(f"🔐 {sid[:12]}… — {client_str}", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.metric("QBER", f"{s.get('qber', 0):.2%}")
            c2.metric("Status", s_status)
            c3.metric("Clients", len(clients))
else:
    st.markdown(
        """
    <div style="
        text-align: center; padding: 30px;
        background: rgba(26, 34, 53, 0.3); border-radius: 12px;
        border: 1px dashed rgba(255,255,255,0.1); color: #475569;
    ">
        <div style="font-size: 2rem; margin-bottom: 8px;">🔒</div>
        <div style="font-family: 'Inter', sans-serif;">No active sessions. Create one from the sidebar.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# =============================================================================
# BB84 VISUALIZATION
# =============================================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
<div style="display:flex; align-items:center; gap:10px; margin-bottom:15px;">
    <div style="width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(135deg, #A78BFA, #6D28D9); display: flex; align-items: center; justify-content: center; font-size: 1.1rem; box-shadow: 0 0 15px rgba(167, 139, 250, 0.3);">🔬</div>
    <div style="font-family:'Inter',sans-serif; font-weight:700; font-size:1.2rem; color:#E2E8F0; letter-spacing:1px; text-transform:uppercase;">BB84 Protocol Simulator</div>
</div>
""",
    unsafe_allow_html=True,
)

v1, v2 = st.columns(2)

with v1:
    num_qubits = st.slider(
        "Qubits",
        128,
        512,
        256,
        64,
        help="Higher counts increase accuracy but take longer",
    )
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🟢 Clean Channel", use_container_width=True):
            try:
                with st.spinner("Running BB84 on AerSimulator..."):
                    res = run_bb84_session(num_bits=num_qubits, eve=False)
                    key = res["raw_key"]
                    qber_val = res["qber"]
                st.success(f"QBER: {qber_val:.2%}")
                st.code(f"Key: {key.hex()[:32]}...")
            except Exception as e:
                st.error(
                    f"Qiskit session error — try again or reduce qubit count. ({e})"
                )
    with b2:
        if st.button("🔴 With Eve", use_container_width=True):
            try:
                with st.spinner("Running BB84 with Eve intercept..."):
                    res = run_bb84_session(num_bits=num_qubits, eve=True)
                    qber_val = res["qber"]
                st.error(f"QBER: {qber_val:.2%} — ATTACK DETECTED")
            except Exception as e:
                st.error(
                    f"Qiskit session error — try again or reduce qubit count. ({e})"
                )

    st.markdown("### Quantum Circuit View")

    def render_circuit_viz():
        try:
            from qiskit import QuantumCircuit

            qc = QuantumCircuit(4, 4)
            # Alice prepares qubits
            qc.x(1)
            qc.x(2)
            qc.h(2)
            qc.h(3)
            # Bob measures
            qc.h(1)
            qc.h(3)
            qc.measure_all()
            circuit_text = str(qc.draw(output="text"))
            st.code(circuit_text, language=None)
            st.caption(
                "Representative 4-qubit BB84 circuit. "
                "Alice prepares in 4 states: |0⟩, |1⟩, |+⟩, |−⟩. "
                "Bob measures in a random basis."
            )
        except Exception as e:
            st.error(f"Could not render circuit: {e}")

    render_circuit_viz()

with v2:
    st.markdown(
        """
<div style="
    background: rgba(26, 34, 53, 0.4); backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;
    padding: 24px; font-size: 0.92rem; line-height: 1.6;
">
<div style="font-weight: 700; font-size: 1rem; color: #E2E8F0; margin-bottom: 12px; letter-spacing: 0.5px;">BB84 Protocol <span style="color: #A78BFA;">(Real Qiskit Circuits)</span></div>

<div style="color: #94A3B8;">
<div style="display: flex; gap: 8px; margin-bottom: 6px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">01</span> Alice picks random bits + random bases (Z or X)</div>
<div style="display: flex; gap: 8px; margin-bottom: 6px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">02</span> Qubits prepared via <code style="color:#A78BFA;">QuantumCircuit</code> (X, H gates)</div>
<div style="display: flex; gap: 8px; margin-bottom: 6px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">03</span> <code style="color:#A78BFA;">AerSimulator</code> executes with depolarizing noise</div>
<div style="display: flex; gap: 8px; margin-bottom: 6px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">04</span> Bob measures in random bases</div>
<div style="display: flex; gap: 8px; margin-bottom: 6px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">05</span> Sift: keep bits where bases matched (~50%)</div>
<div style="display: flex; gap: 8px; margin-bottom: 6px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">06</span> Compare sample → compute QBER from <strong>real measurements</strong></div>
<div style="display: flex; gap: 8px; margin-bottom: 6px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">07</span> <strong>Privacy Amplification</strong> via Toeplitz matrix hashing</div>
<div style="display: flex; gap: 8px; margin-bottom: 12px;"><span style="color: #00FFA3; font-family: 'JetBrains Mono', monospace; min-width: 18px;">08</span> QBER < 11% → <span style="color:#00FFA3;">secure key</span>. QBER ≥ 11% → <span style="color:#FF3366;">abort</span></div>
</div>

<div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 4px;">
<div style="color: #FF3366; font-weight: 600; margin-bottom: 4px;">🎯 Eve's Problem</div>
<div style="color: #94A3B8;">Measuring a qubit disturbs it. Her interception causes ~25% QBER → always detected.</div>
</div>

<div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 12px;">
<div style="color: #00B8FF; font-weight: 600; margin-bottom: 4px;">🏦 Banking Application</div>
<div style="color: #94A3B8;">Each transaction session runs a fresh BB84 key exchange. The derived AES-256-GCM key encrypts all financial data with information-theoretic security guarantees.</div>
</div>
</div>
    """,
        unsafe_allow_html=True,
    )


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
<div style="
    text-align: center; padding: 20px 0; margin-top: 20px;
    border-top: 1px solid rgba(255,255,255,0.06);
    color: #475569; font-size: 0.85rem; font-family: 'Inter', sans-serif;
">
    <span style="background: linear-gradient(90deg, #00FFA3, #00B8FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;">ShorlyNot</span>
    &nbsp;v4.0 &nbsp;·&nbsp; Qiskit BB84 QKD &nbsp;·&nbsp; Privacy Amplification &nbsp;·&nbsp;
    AES-256-GCM &nbsp;·&nbsp; HKDF-SHA256 &nbsp;·&nbsp; Escalation FSM
    <br><span style="font-size: 0.75rem; opacity: 0.6;">YESIST 2026 &nbsp;·&nbsp; Secured by Physics</span>
</div>
""",
    unsafe_allow_html=True,
)

# Auto-refresh
if st.session_state.auto_refresh:
    import time

    time.sleep(3)
    st.rerun()
