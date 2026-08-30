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

from quantum_engine.bb84_simulator import simulate_bb84, QBER_SECURITY_THRESHOLD


# =============================================================================
# CONFIG
# =============================================================================

st.set_page_config(
    page_title="ShorlyNot",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
    /* Global dark theme overrides */
    body { background-color: #0B0F19; color: #E2E8F0; }
    .main-header { font-size: 2.2rem; font-weight: 800; color: #E2E8F0; text-transform: uppercase; letter-spacing: 1px; }
    .main-header span { color: #00FFA3; }
    .sub-header { font-size: 1rem; color: #94A3B8; margin-bottom: 2rem; border-bottom: 1px solid #1A2235; padding-bottom: 1rem; }
    
    /* Neon Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1A2235;
        border: 1px solid #2A3B5C;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
    }
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: #00FFA3 !important;
        text-shadow: 0 0 10px rgba(0, 255, 163, 0.3);
    }
    
    /* Buttons */
    div.stButton > button:first-child {
        background-color: #1A2235;
        border: 1px solid #00FFA3;
        color: #00FFA3;
        font-weight: 600;
        transition: all 0.3s;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 15px rgba(0, 255, 163, 0.4);
        background-color: #00FFA3;
        color: #0B0F19;
    }
    
    /* FSM Strip */
    .fsm-strip {
        display: flex; justify-content: space-between; align-items: center;
        background: #1A2235; border: 1px solid #2A3B5C; border-radius: 8px;
        padding: 15px; margin-bottom: 20px;
    }
    .fsm-node {
        flex: 1; text-align: center; padding: 10px; margin: 0 5px;
        border-radius: 6px; font-weight: bold; color: #475569;
        background: #0B0F19; border: 1px solid #1E293B;
        transition: all 0.3s ease;
    }
    .fsm-active {
        color: #0B0F19;
        box-shadow: 0 0 15px rgba(255, 51, 102, 0.6);
        border-color: #FF3366;
    }
    .fsm-active.l1 { background: #00FFA3; box-shadow: 0 0 15px rgba(0, 255, 163, 0.4); border-color: #00FFA3; }
    .fsm-active.l2 { background: #FFD700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.4); border-color: #FFD700; }
    .fsm-active.l3 { background: #FF3366; }
    .fsm-active.l4 { background: #FF0000; box-shadow: 0 0 20px rgba(255, 0, 0, 0.8); color: white; border-color: #FF0000; }

    /* QBER Bar */
    .qber-container {
        width: 100%; height: 16px; background-color: #0B0F19;
        border-radius: 8px; border: 1px solid #2A3B5C;
        overflow: hidden; margin-top: 5px;
    }
    .qber-fill {
        height: 100%; transition: width 0.5s ease-in-out, background-color 0.5s;
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
    '<p class="main-header">🛡️ <span>ShorlyNot</span> — Banking Security Dashboard</p>',
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
    st.header("🤖 Automation")
    if st.button("▶️ Execute Demo Sequence", use_container_width=True):
        import time
        with st.status("Running Demo Sequence...", expanded=True) as status:
            st.write("1. System Reset...")
            api("POST", "/reset")
            time.sleep(1.5)
            
            st.write("2. Initiating Clean Transfer...")
            r = api("POST", "/transfer", json={"from_acc": "ACC001", "to_acc": "ACC002", "amount": 1000, "note": "Demo Clean"})
            if "_error" not in r:
                st.write(f"✅ Transfer Success (QBER: {r.get('qber',0):.2%})")
            else:
                st.write(f"⚠️ {r['_error']}")
            
            time.sleep(2)
            st.write("3. Activating Quantum Eavesdropper (Eve)...")
            api("POST", "/activate_eve")
            time.sleep(1.5)
            
            st.write("4. Attempting Compromised Transfer...")
            r = api("POST", "/transfer", json={"from_acc": "ACC001", "to_acc": "ACC002", "amount": 2500, "note": "Demo Attack"})
            st.write("🚫 Transfer Blocked! Channel compromised.")
            
            time.sleep(2)
            st.write("5. Triggering Escalation Level 4...")
            for _ in range(4):
                api("POST", "/trigger_attack")
                time.sleep(0.5)
            st.write("💥 L4 LOCKDOWN ACTIVE!")
            
            time.sleep(2)
            status.update(label="Demo Sequence Complete!", state="complete", expanded=False)

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
    entropy = health.get("entropy_score", 0)
    qber_pct = min(100, qber * 100)
    fill_color = "#00FFA3" if qber < 0.11 else "#FF3366"
    st.markdown(f"""
        <div style="margin-bottom: 5px; font-weight: bold; color: #94A3B8;">QBER Level</div>
        <div class="qber-container">
            <div class="qber-fill" style="width: {qber_pct}%; background-color: {fill_color};"></div>
        </div>
        <div style="text-align: right; font-size: 0.9em; margin-top: 5px; color: {fill_color}; font-weight: bold;">
            {qber:.2%} (Threshold: 11%)
        </div>
    """, unsafe_allow_html=True)
    
    if entropy > 0:
        st.markdown(f"**Entropy Score: {entropy}/100**")


# =============================================================================
# ESCALATION LEVEL DISPLAY
# =============================================================================

level = health.get("escalation_level", 0)
active_l1 = "fsm-active l1" if level <= 1 else ""
active_l2 = "fsm-active l2" if level == 2 else ""
active_l3 = "fsm-active l3" if level == 3 else ""
active_l4 = "fsm-active l4" if level >= 4 else ""

st.markdown(f"""
<div class="fsm-strip">
    <div class="fsm-node {active_l1}">L1: Normal<br><small>Port Rotation</small></div>
    <div class="fsm-node {active_l2}">L2: Elevated<br><small>IP Failover</small></div>
    <div class="fsm-node {active_l3}">L3: Critical<br><small>Interface Switch</small></div>
    <div class="fsm-node {active_l4}">L4: LOCKDOWN<br><small>System Halt</small></div>
</div>
""", unsafe_allow_html=True)


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

col_chart, col_gauge = st.columns([3, 1])

with col_chart:
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
    plot_bgcolor="#1A2235",
    paper_bgcolor="#0B0F19",
    font=dict(color="#E2E8F0"),
    yaxis=dict(range=[0, max(0.35, max(st.session_state.qber_history) * 1.2) if st.session_state.qber_history else 0.35]),
)
st.plotly_chart(fig, use_container_width=True)

with col_gauge:
    entropy = health.get("entropy_score", 0)
    fig2 = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = entropy,
        title = {'text': "Quantum Entropy Score"},
        gauge = {'axis': {'range': [None, 100]},
                 'bar': {'color': "#00FFA3" if entropy > 50 else "#FF3366"},
                 'steps' : [
                     {'range': [0, 50], 'color': "rgba(255, 51, 102, 0.2)"},
                     {'range': [50, 100], 'color': "rgba(0, 255, 163, 0.2)"}]}
    ))
    fig2.update_layout(
        height=320,
        margin=dict(t=50, b=30, l=20, r=20),
        plot_bgcolor="#1A2235",
        paper_bgcolor="#0B0F19",
        font=dict(color="#E2E8F0"),
    )
    st.plotly_chart(fig2, use_container_width=True)


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
            circuit_text = str(qc.draw(output='text'))
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
    "ShorlyNot v4.0 | Qiskit BB84 QKD | Privacy Amplification | "
    "AES-256-GCM | HKDF-SHA256 | Escalation FSM"
)

# Auto-refresh
if st.session_state.auto_refresh:
    import time
    time.sleep(3)
    st.rerun()
