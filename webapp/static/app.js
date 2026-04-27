/* FinQuantum Bank — Internet Banking Application Logic */

const KMS = '';  // same-origin — served from FastAPI
let qberHistory = [];
let qberChart = null;

// ─── Helpers ──────────────────────────────────────────
function formatINR(num) {
  return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ─── Navigation ───────────────────────────────────────
function showPage(page) {
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  document.getElementById('nav-' + page).classList.add('active');
  if (page === 'security') initChart();
  if (page === 'sessions') refreshSessions();
  if (page === 'transactions') loadTransactions();
}

// ─── Toast ────────────────────────────────────────────
function toast(msg, type = 'info') {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const container = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = 'toast toast-' + type;
  el.innerHTML = `<span>${icons[type]||''}</span> <span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 400); }, 5000);
}

// ─── API ──────────────────────────────────────────────
async function api(method, path, body) {
  try {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(KMS + path, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      return { _error: err.detail || err.message || res.statusText, status: 'ERROR' };
    }
    return await res.json();
  } catch (e) {
    return { _error: e.message, status: 'OFFLINE' };
  }
}

// ─── Load Accounts ────────────────────────────────────
async function loadAccounts() {
  const d = await api('GET', '/accounts');
  if (!d.accounts) return;

  // Dashboard account cards
  const grid = document.getElementById('accountsGrid');
  grid.innerHTML = d.accounts.map(acc => `
    <div class="account-card">
      <div class="acc-top">
        <div class="acc-type">${acc.name}</div>
        <div class="acc-badge">Active</div>
      </div>
      <div class="acc-number">${acc.id} • IFSC: ${acc.ifsc}</div>
      <div class="acc-balance-label">Available Balance</div>
      <div class="acc-balance"><span class="rupee">₹</span> ${formatINR(acc.balance)}</div>
    </div>
  `).join('');

  // Transfer form dropdowns
  const fromSel = document.getElementById('fromAccount');
  const toSel = document.getElementById('toAccount');
  if (fromSel && toSel) {
    fromSel.innerHTML = '';
    toSel.innerHTML = '';
    d.accounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc.id;
      opt.textContent = `${acc.name} (₹${formatINR(acc.balance)})`;
      fromSel.appendChild(opt.cloneNode(true));
      toSel.appendChild(opt.cloneNode(true));
    });
  }
}

// ─── Refresh Status ───────────────────────────────────
async function refreshStatus() {
  const d = await api('GET', '/link_status');
  if (d._error) return;

  const qber = d.qber || 0;
  const qberPct = (qber * 100).toFixed(2);

  // Header security indicator
  const secDot = document.getElementById('secDot');
  const secText = document.getElementById('secText');
  if (d.status === 'RED') {
    secDot.className = 'sec-dot red';
    secText.textContent = 'Channel Compromised';
  } else {
    secDot.className = 'sec-dot';
    secText.textContent = 'Quantum Secured';
  }

  // Dashboard alert bar
  const alertBar = document.getElementById('alertBar');
  if (d.status === 'RED') {
    alertBar.className = 'alert-bar danger';
    alertBar.innerHTML = '<span>🚨</span><span>SECURITY ALERT: Quantum channel interception detected. QBER: <strong>' + qberPct + '%</strong>. Transactions may be blocked.</span>';
  } else if (qber >= 0.05) {
    alertBar.className = 'alert-bar warning';
    alertBar.innerHTML = '<span>⚠️</span><span>Elevated noise on quantum channel. QBER: <strong>' + qberPct + '%</strong>. Monitoring closely.</span>';
  } else {
    alertBar.className = 'alert-bar success';
    alertBar.innerHTML = '<span>🛡️</span><span>All transactions are protected by <strong>quantum key distribution (BB84)</strong>. Channel status: <strong>SECURE</strong></span>';
  }

  // Transfer alert
  const transferAlert = document.getElementById('transferAlert');
  if (transferAlert) {
    if (d.status === 'RED') {
      transferAlert.className = 'alert-bar danger';
      transferAlert.innerHTML = '<span>🚫</span><span>Fund transfers are currently <strong>blocked</strong> due to quantum channel compromise. QBER: ' + qberPct + '%</span>';
    } else {
      transferAlert.className = 'alert-bar info';
      transferAlert.innerHTML = '<span>🔐</span><span>Each transfer initiates a fresh <strong>BB84 quantum key exchange</strong> on Qiskit AerSimulator for end-to-end encryption</span>';
    }
  }

  // Send button
  const sendBtn = document.getElementById('sendBtn');
  if (sendBtn && !sendBtn._busy) {
    if (d.status === 'RED') {
      sendBtn.disabled = true;
      sendBtn.textContent = '🚫 Transfers Temporarily Suspended';
      sendBtn.style.background = '#d32f2f';
    } else {
      sendBtn.disabled = false;
      sendBtn.textContent = '🔐 Send Quantum-Secured Transfer';
      sendBtn.style.background = '';
    }
  }

  // Escalation strip
  const level = d.escalation_level || 0;
  const escLabels = {
    0: '🛡️ Security Level: NORMAL — All quantum channels operational',
    1: '🛡️ Security Level: NORMAL — Port rotation active (1919–1925)',
    2: '⚠️ Security Level: ELEVATED — IP failover activated',
    3: '🚨 Security Level: HIGH — Interface switching in progress',
    4: '🔒 Security Level: CRITICAL — EMERGENCY LOCKDOWN'
  };
  const escStrip = document.getElementById('escStrip');
  if (escStrip) {
    escStrip.className = 'escalation-strip l' + Math.min(level, 4);
    escStrip.textContent = escLabels[level] || escLabels[0];
  }

  // Security center metrics
  const el = id => document.getElementById(id);
  if (el('secQber')) {
    el('secQber').textContent = qberPct + '%';
    el('secQber').style.color = qber >= 0.11 ? 'var(--danger)' : qber >= 0.05 ? 'var(--warning)' : 'var(--success)';
  }
  const eveActive = d.eve_mode || d.eve_active;
  if (el('secEve')) {
    el('secEve').textContent = eveActive ? '⚠ THREAT DETECTED' : '✓ SECURE';
    el('secEve').style.color = eveActive ? 'var(--danger)' : 'var(--success)';
  }
  if (el('secAttacks')) el('secAttacks').textContent = d.attacks_detected || 0;
  if (el('secLevel')) el('secLevel').textContent = 'L' + level;
  if (el('secPort')) el('secPort').textContent = d.current_port || '—';
  if (el('secIP')) el('secIP').textContent = d.current_ip || '—';
  if (el('secNet')) el('secNet').textContent = d.current_network || '—';
  if (el('secSessions')) el('secSessions').textContent = d.active_sessions || 0;

  // QBER chart data
  qberHistory.push(qber);
  if (qberHistory.length > 50) qberHistory.shift();
  updateChart();

  // Lockdown
  const overlay = document.getElementById('lockdownOverlay');
  if (overlay) overlay.classList.toggle('active', level >= 4);

  // Notification bell
  const attacks = d.attacks_detected || 0;
  const bellBadge = document.getElementById('bellBadge');
  if (bellBadge) {
    if (attacks > 0) {
      bellBadge.style.display = 'flex';
      bellBadge.textContent = attacks;
    } else {
      bellBadge.style.display = 'none';
    }
  }
}

// ─── Send Transfer (uses POST /transfer) ──────────────
async function doTransfer(e) {
  e.preventDefault();
  const fromAcc = document.getElementById('fromAccount').value;
  const toAcc = document.getElementById('toAccount').value;
  const amount = parseFloat(document.getElementById('amount').value);
  const note = (document.getElementById('note') || {}).value || 'Transfer';

  if (fromAcc === toAcc) { toast('Cannot transfer to same account', 'error'); return; }
  if (!amount || amount <= 0) { toast('Enter valid amount', 'error'); return; }

  const btn = document.getElementById('sendBtn');
  btn.disabled = true;
  btn._busy = true;
  btn.textContent = '⏳ Processing quantum key exchange...';

  try {
    const r = await api('POST', '/transfer', { from_acc: fromAcc, to_acc: toAcc, amount, note });

    if (r._error) {
      toast(`Transfer failed: ${r._error}`, 'error');
    } else {
      toast(`✅ ₹${formatINR(amount)} transferred | QBER: ${(r.qber*100).toFixed(2)}%`, 'success');

      // Show quantum proof panel
      const proofEl = document.getElementById('txProof');
      if (proofEl) {
        proofEl.innerHTML = `
          <div style="background:var(--bg-light);border:1px solid var(--border);border-radius:8px;padding:16px;font-size:12px;line-height:1.8">
            <h4 style="font-size:13px;font-weight:700;color:var(--text-dark);margin-bottom:8px">🔐 Quantum Security Proof</h4>
            <p><b>TX ID:</b> <code>${r.tx_id}</code></p>
            <p><b>Session:</b> <code>${r.session_id.slice(0,16)}...</code></p>
            <p><b>QBER:</b> <span style="color:${r.qber < 0.05 ? 'var(--success)' : 'var(--warning)'}; font-weight:700">${(r.qber*100).toFixed(3)}%</span> ${r.qber < 0.05 ? '✅ Secure' : '⚠ Elevated'}</p>
            <p><b>Encryption:</b> ${r.encryption}</p>
            <p><b>Key Source:</b> ${r.key_source}</p>
            <p><b>Encrypted Payload:</b><br><code style="word-break:break-all;font-size:10px">${r.encrypted_payload_preview}</code></p>
            <p><b>Nonce:</b> <code style="font-size:10px">${r.nonce}</code></p>
            <p><b>New Balance:</b> ₹${formatINR(r.new_balance)}</p>
          </div>
        `;
      }

      // Update seal
      const sealDetails = document.getElementById('sealDetails');
      if (sealDetails) {
        sealDetails.textContent = `Session: ${r.session_id.slice(0,12)}... | QBER: ${(r.qber*100).toFixed(2)}%`;
      }

      // Refresh accounts to show updated balances
      await loadAccounts();
      await loadRecentTx();

      // Clear form
      document.getElementById('amount').value = '';
      if (document.getElementById('note')) document.getElementById('note').value = '';
    }
  } catch (err) {
    toast('Network error: ' + err.message, 'error');
  }

  btn.disabled = false;
  btn._busy = false;
  btn.textContent = '🔐 Send Quantum-Secured Transfer';
}

// ─── Load Recent Transactions (dashboard) ─────────────
async function loadRecentTx() {
  const d = await api('GET', '/transactions');
  if (!d.transactions) return;
  const recentBody = document.getElementById('recentTxBody');
  if (!recentBody) return;

  if (d.transactions.length === 0) {
    recentBody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:40px">No recent transactions. Start by making a fund transfer.</td></tr>';
    return;
  }

  recentBody.innerHTML = d.transactions.slice(0, 5).map(tx => {
    const qColor = tx.qber < 0.05 ? 'var(--success)' : tx.qber < 0.11 ? 'var(--warning)' : 'var(--danger)';
    return `<tr>
      <td>
        <div class="tx-details">
          <div class="tx-icon debit">💸</div>
          <div>
            <div class="tx-name">${tx.from_name} → ${tx.to_name}</div>
            <div class="tx-ref">${tx.note || 'Transfer'}</div>
          </div>
        </div>
      </td>
      <td style="color:var(--text-muted);font-size:12px">${new Date(tx.timestamp * 1000).toLocaleString('en-IN')}</td>
      <td style="font-family:monospace;font-size:11px;color:var(--text-muted)">${tx.tx_id.slice(0,12)}...</td>
      <td><span class="badge badge-success" style="color:${qColor}">${(tx.qber*100).toFixed(2)}%</span></td>
      <td class="amount-debit">-₹${formatINR(tx.amount)}</td>
      <td><span class="badge badge-success">✓ ${tx.status}</span></td>
    </tr>`;
  }).join('');
}

// ─── Load All Transactions (transactions page) ────────
async function loadTransactions() {
  const d = await api('GET', '/transactions');
  if (!d.transactions) return;
  const tbody = document.getElementById('txBody');
  if (!tbody) return;

  if (d.transactions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:40px">No transactions found.</td></tr>';
    return;
  }

  const badge = document.getElementById('txTotalBadge');
  if (badge) badge.textContent = d.transactions.length + ' transactions';

  tbody.innerHTML = d.transactions.map(tx => `
    <tr>
      <td><code style="font-size:11px">${tx.tx_id.slice(0,12)}...</code></td>
      <td>${tx.from_name}</td>
      <td>${tx.to_name}</td>
      <td style="font-weight:600">₹${formatINR(tx.amount)}</td>
      <td style="color:${tx.qber < 0.05 ? 'var(--success)' : 'var(--warning)'}; font-weight:600">${(tx.qber*100).toFixed(3)}%</td>
      <td><code style="font-size:10px;word-break:break-all">${tx.encrypted_payload}</code></td>
      <td><span class="badge badge-success">${tx.status}</span></td>
    </tr>
  `).join('');
}

// ─── Sessions ─────────────────────────────────────────
async function refreshSessions() {
  const d = await api('GET', '/sessions');
  const body = document.getElementById('sessionsBody');
  if (!body) return;
  const list = d.sessions || [];
  if (list.length === 0) {
    body.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:40px">No key sessions recorded.</td></tr>';
    return;
  }
  body.innerHTML = list.map(s => {
    const clients = (s.clients || []).join(' ↔ ');
    const statusBadge = s.status === 'GREEN'
      ? '<span class="badge badge-success">GREEN</span>'
      : s.status === 'YELLOW'
      ? '<span class="badge badge-warning">YELLOW</span>'
      : '<span class="badge badge-danger">RED</span>';
    const qColor = s.qber < 0.05 ? 'var(--success)' : s.qber < 0.11 ? 'var(--warning)' : 'var(--danger)';
    return `<tr>
      <td style="font-family:monospace;font-size:12px">${s.session_id.slice(0,20)}...</td>
      <td>${clients}</td>
      <td style="color:${qColor};font-weight:600">${(s.qber*100).toFixed(2)}%</td>
      <td>${statusBadge}</td>
    </tr>`;
  }).join('');
}

// ─── QBER Chart ───────────────────────────────────────
function initChart() {
  const canvas = document.getElementById('qberChart');
  if (!canvas) return;
  if (qberChart) { updateChart(); return; }

  const ctx = canvas.getContext('2d');
  qberChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: qberHistory.map((_, i) => i + 1),
      datasets: [{
        label: 'QBER',
        data: qberHistory,
        borderColor: '#00d4ff',
        backgroundColor: 'rgba(0,212,255,0.06)',
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointRadius: 3,
        pointBackgroundColor: '#00d4ff',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', font: { size: 10 } },
        },
        y: {
          min: 0,
          max: 0.4,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', font: { size: 10 }, callback: v => (v*100).toFixed(0) + '%' },
        },
      },
    },
  });

  const thresholdPlugin = {
    id: 'thresholds',
    afterDraw(chart) {
      const { ctx, chartArea: { left, right }, scales: { y } } = chart;
      const y11 = y.getPixelForValue(0.11);
      ctx.save();
      ctx.strokeStyle = '#d32f2f';
      ctx.lineWidth = 1;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(left, y11);
      ctx.lineTo(right, y11);
      ctx.stroke();
      ctx.fillStyle = '#d32f2f';
      ctx.font = '10px Inter';
      ctx.fillText('11% Attack Threshold', left + 4, y11 - 4);

      const y5 = y.getPixelForValue(0.05);
      ctx.strokeStyle = '#f9a825';
      ctx.beginPath();
      ctx.moveTo(left, y5);
      ctx.lineTo(right, y5);
      ctx.stroke();
      ctx.fillStyle = '#f9a825';
      ctx.fillText('5% Warning', left + 4, y5 - 4);
      ctx.restore();
    }
  };
  qberChart.config.plugins = [thresholdPlugin];
  qberChart.update();
}

function updateChart() {
  if (!qberChart) return;
  qberChart.data.labels = qberHistory.map((_, i) => i + 1);
  qberChart.data.datasets[0].data = [...qberHistory];
  qberChart.update('none');
}

// ─── WebSocket ────────────────────────────────────────
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}/ws/events`);
  ws.onmessage = (e) => {
    try {
      const ev = JSON.parse(e.data);
      if (ev.event === 'attack') {
        toast('⚠️ Quantum channel interception detected! QBER: ' + ((ev.qber||0)*100).toFixed(1) + '%', 'error');
      } else if (ev.event === 'lockdown') {
        toast('🔒 EMERGENCY: All banking services suspended', 'error');
      } else if (ev.event === 'escalation') {
        const labels = {0:'Normal',1:'Port Rotation',2:'IP Failover',3:'Interface Switch',4:'LOCKDOWN'};
        toast('Security escalated to L' + ev.level + ': ' + (labels[ev.level]||''), 'warning');
      } else if (ev.event === 'transaction') {
        toast(`💸 ₹${formatINR(ev.amount)} | ${ev.from} → ${ev.to} | QBER: ${(ev.qber*100).toFixed(2)}%`, 'info');
        loadRecentTx();
        loadAccounts();
      }
      refreshStatus();
    } catch (err) {}
  };
  ws.onclose = () => setTimeout(connectWS, 3000);
  ws.onerror = () => {};
}

// ─── Init ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadAccounts();
  loadRecentTx();
  refreshStatus();
  setInterval(refreshStatus, 3000);
  connectWS();
});
