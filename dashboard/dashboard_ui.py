"""
Streamlit Monitoring Dashboard
================================
FinQuantum Shield — Banking Security Operations Dashboard v4.0

Network-aware dashboard connecting to the KMS Server via HTTP API.
Displays real-time link health, QBER history chart, escalation status,
network state tiles, session info, and BB84 visualization.

Run with:
    streamlit run dashboard/dashboard_ui.py

Author: FinQuantum Shield Team
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

from quantum_engine.bb84_simulator import simulate_bb84, QBER_SECURITY_THRESHOLD


# =============================================================================
# CONFIG
# =============================================================================

st.set_page_config(
    page_title="FinQuantum Shield",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: bold; color: #1e40af; }
    .sub-header { font-size: 1rem; color: #6b7280; margin-bottom: 1.5rem; }
    .stMetric .css-1wivap2, .stMetric [data-testid="stMetricValue"] {
        font-weight: 700;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


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
    '<p class="main-header">🛡️ FinQuantum Shield — Banking Security Dashboard</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-header">Quantum-Safe Transaction Security | Real-Time Monitoring | v4.0</p>',
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


# Status row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    status = health.get("status", "?")
    if status == "GREEN":
        st.markdown("### 🟢 SECURE")
    elif status == "YELLOW":
        st.markdown("### 🟡 ELEVATED")
    elif status == "RED":
        st.markdown("### 🔴 COMPROMISED")
    else:
        st.markdown("### ⚪ OFFLINE")

with col2:
    st.metric("Keys Issued", health.get("total_keys_issued", 0))

with col3:
    st.metric("Sessions", health.get("total_sessions", 0))

with col4:
    st.metric("Attacks", health.get("attacks_detected", 0))

with col5:
    qber = health.get("qber", 0)
    st.metric("QBER", f"{qber:.2%}" if qber > 0 else "N/A")


# =============================================================================
# ESCALATION LEVEL DISPLAY
# =============================================================================

level = health.get("escalation_level", 0)
level_colors = {0: "#059669", 1: "#059669", 2: "#d97706", 3: "#dc2626", 4: "#7f1d1d"}
level_labels = {
    0: "L0 — Normal / All Systems Operational",
    1: "L1 — Port Rotation (1919–1925 cycling)",
    2: "L2 — IP Failover (192.168.1.100 → 192.168.1.150)",
    3: "L3 — Interface Switch (192.168.1.x → 192.168.2.x)",
    4: "L4 — ⚠ EMERGENCY LOCKDOWN ⚠",
}

bg_color = level_colors.get(level, "#059669")
label_text = level_labels.get(level, "Unknown")

st.markdown(
    f"""
    <div style='background:{bg_color};color:white;
                padding:14px;border-radius:10px;font-weight:bold;
                font-size:16px;margin:8px 0;text-align:center'>
      ESCALATION: {label_text}
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# NETWORK STATE TILES
# =============================================================================

ncol1, ncol2, ncol3 = st.columns(3)
ncol1.metric("🔌 Active Port", health.get("current_port", "?"))
ncol2.metric("🌐 Active IP", health.get("current_ip", "?"))
ncol3.metric("📡 Active Network", health.get("current_network", "?"))


# =============================================================================
# QBER HISTORY CHART (Plotly)
# =============================================================================

st.divider()

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        y=st.session_state.qber_history,
        mode="lines+markers",
        name="QBER",
        line=dict(color="#2563EB", width=2),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.1)",
    )
)
fig.add_hline(
    y=0.11,
    line_dash="dash",
    line_color="red",
    annotation_text="11% Threshold (Attack proof)",
    annotation_position="top left",
)
fig.add_hline(
    y=0.05,
    line_dash="dash",
    line_color="orange",
    annotation_text="5% Warning",
    annotation_position="bottom left",
)
fig.update_layout(
    title="Live QBER History",
    yaxis_title="QBER",
    xaxis_title="Session",
    height=320,
    margin=dict(t=50, b=30, l=40, r=20),
    plot_bgcolor="#f8fafc",
    paper_bgcolor="white",
    yaxis=dict(range=[0, max(0.35, max(st.session_state.qber_history) * 1.2) if st.session_state.qber_history else 0.35]),
)
st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# ROUTER STATUS
# =============================================================================

if status == "GREEN":
    st.success(
        "**📡 Quantum Channel:** Secure — QBER within normal parameters. "
        "All banking transactions protected."
    )
elif status == "RED":
    st.error(
        f"**📡 Quantum Channel:** COMPROMISED — QBER={qber:.2%} exceeds 11% threshold. "
        f"Transactions HALTED."
    )
    st.warning(
        f"Eve {'ACTIVE' if health.get('eve_active') or health.get('eve_mode') else 'was active'} | "
        f"Escalation Level {level}"
    )
elif status == "YELLOW":
    st.warning(
        "**📡 Quantum Channel:** Elevated QBER — monitoring for potential compromise"
    )


# =============================================================================
# SESSIONS TABLE
# =============================================================================

st.divider()
st.header("📋 Active Sessions")

sessions = api("GET", "/sessions")
sess_list = sessions.get("sessions", [])

if sess_list:
    for s in sess_list:
        sid = s.get("session_id", "?")
        clients = s.get("clients", [])
        client_str = " ↔ ".join(clients[:2]) if clients else "Unknown"
        with st.expander(
            f"Session `{sid[:12]}...` — {client_str}", expanded=False
        ):
            c1, c2 = st.columns(2)
            c1.metric("QBER", f"{s.get('qber', 0):.2%}")
            c2.metric("Status", s.get("status", "?"))
else:
    st.info("No active sessions. Create one from the sidebar.")


# =============================================================================
# BB84 VISUALIZATION
# =============================================================================

st.divider()
st.header("🔬 BB84 Protocol Simulator")

v1, v2 = st.columns(2)

with v1:
    num_qubits = st.slider("Qubits", 128, 512, 256, 64,
                           help="Higher counts increase accuracy but take longer")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🟢 Clean Channel", use_container_width=True):
            try:
                with st.spinner("Running BB84 on AerSimulator..."):
                    key, qber_val, _ = simulate_bb84(
                        num_bits=num_qubits, eve_present=False
                    )
                st.success(f"QBER: {qber_val:.2%}")
                st.code(f"Key: {key.hex()[:32]}...")
            except Exception as e:
                st.error(f"Qiskit session error — try again or reduce qubit count. ({e})")
    with b2:
        if st.button("🔴 With Eve", use_container_width=True):
            try:
                with st.spinner("Running BB84 with Eve intercept..."):
                    key, qber_val, _ = simulate_bb84(
                        num_bits=num_qubits, eve_present=True
                    )
                st.error(f"QBER: {qber_val:.2%} — ATTACK DETECTED")
            except Exception as e:
                st.error(f"Qiskit session error — try again or reduce qubit count. ({e})")

with v2:
    st.markdown(
        """
    **BB84 Protocol (Real Qiskit Circuits):**
    1. Alice picks random bits + random bases (Z or X)
    2. Qubits are prepared via **QuantumCircuit** (X, H gates)
    3. **AerSimulator** executes circuits with depolarizing noise
    4. Bob measures in random bases
    5. Sift: keep bits where bases matched (~50%)
    6. Compare sample → compute QBER from **real measurements**
    7. **Privacy Amplification** via Toeplitz matrix hashing
    8. QBER < 11% → secure key. QBER ≥ 11% → abort.

    **Eve's problem:** Measuring a qubit disturbs it.
    Her interception causes ~25% QBER → always detected.

    **Banking application:** Each transaction session runs a fresh
    BB84 key exchange. The derived AES-256-GCM key encrypts all
    financial data with information-theoretic security guarantees.
    """
    )


# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption(
    "FinQuantum Shield v4.0 | Qiskit BB84 QKD | Privacy Amplification | "
    "AES-256-GCM | HKDF-SHA256 | Escalation FSM"
)

# Auto-refresh
if st.session_state.auto_refresh:
    import time
    time.sleep(3)
    st.rerun()
