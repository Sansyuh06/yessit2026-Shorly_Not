const KMS = '';
let qberHistory = [];

function formatINR(num) {
  return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function toast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const el = document.createElement('div');
  const bg = type === 'error' ? 'bg-bank-red' : (type === 'success' ? 'bg-bank-green' : 'bg-bank-blue');
  el.className = `${bg} text-white px-4 py-2 rounded-sm shadow-md transition-opacity duration-300`;
  el.innerHTML = `<span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 5000);
}

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

async function loadAccounts() {
  const d = await api('GET', '/accounts');
  if (!d.accounts) return;
  
  const grid = document.getElementById('accountsGrid');
  if (grid) {
    grid.innerHTML = d.accounts.map((acc, i) => `
      <tr class="hover:bg-blue-50/50 transition-colors ${i % 2 !== 0 ? 'bg-[#FAFAFA]' : ''}">
        <td class="py-3 px-4">
          <div class="font-semibold text-bank-blue">${acc.name}</div>
          <div class="text-[11px] text-bank-muted">${acc.id}</div>
        </td>
        <td class="py-3 px-4 text-bank-text">IFSC: ${acc.ifsc}</td>
        <td class="py-3 px-4 text-right font-bold text-[14px]">₹ ${formatINR(acc.balance)}</td>
        <td class="py-3 px-4 text-center">
          <button class="bg-bank-cyan text-white px-3 py-1 text-[11px] rounded-sm hover:bg-teal-600 transition-colors shadow-sm">View Details</button>
        </td>
      </tr>
    `).join('');
  }

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

async function loadRecentTx() {
  const d = await api('GET', '/transactions');
  if (!d.transactions) return;
  const tbody = document.getElementById('recentTxBody');
  if (!tbody) return;

  if (d.transactions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-bank-muted">No transactions found.</td></tr>';
    return;
  }

  tbody.innerHTML = d.transactions.slice(0, 5).map((tx, i) => {
    const dateStr = new Date(tx.timestamp * 1000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    return `
      <tr class="hover:bg-blue-50/30 ${i % 2 !== 0 ? 'bg-[#FAFAFA]' : ''}">
        <td class="py-2 px-3 whitespace-nowrap text-bank-muted">${dateStr}</td>
        <td class="py-2 px-3">${tx.note || 'Transfer to ' + tx.to_name}</td>
        <td class="py-2 px-3 text-bank-muted">${tx.tx_id.slice(0,8)}</td>
        <td class="py-2 px-3 text-right text-bank-red font-medium">${formatINR(tx.amount)}</td>
        <td class="py-2 px-3 text-right"></td>
        <td class="py-2 px-3 text-right font-semibold">QBER: ${(tx.qber*100).toFixed(2)}%</td>
      </tr>
    `;
  }).join('');
}

async function refreshStatus() {
  const d = await api('GET', '/link_status');
  if (d._error) return;

  const topBar = document.getElementById('topBar');
  if (topBar) {
    if (d.status === 'RED') {
      topBar.className = "bg-bank-red text-white w-full py-1.5 text-[11px] animate-pulse";
      topBar.querySelector('.flex.gap-4').innerHTML = "🚨 SECURITY ALERT: QUANTUM CHANNEL COMPROMISED";
    } else {
      topBar.className = "bg-bank-navy text-white w-full py-1.5 text-[11px]";
      topBar.querySelector('.flex.gap-4').innerHTML = `<a class="hover:underline" href="#">Skip to Main Content</a><span>|</span><a class="hover:underline" href="#">Contact Us</a><span>|</span><a class="hover:underline" href="#">Branches/ATMs</a>`;
    }
  }

  const sendBtn = document.getElementById('sendBtn');
  if (sendBtn && !sendBtn.disabled_by_user) {
    if (d.status === 'RED') {
      sendBtn.disabled = true;
      sendBtn.textContent = '🚫 Transfers Blocked';
      sendBtn.className = 'bg-bank-red text-white px-4 py-2 rounded-sm font-semibold opacity-50 self-start mt-2';
    } else {
      sendBtn.disabled = false;
      sendBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">lock</span> Transfer Now';
      sendBtn.className = 'bg-bank-navy text-white px-4 py-2 rounded-sm font-semibold hover:bg-blue-900 transition-colors self-start flex items-center gap-2 mt-2';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadAccounts();
  loadRecentTx();
  refreshStatus();
  setInterval(refreshStatus, 3000);

  const tForm = document.getElementById('transferForm');
  if (tForm) {
    tForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fromAcc = document.getElementById('fromAccount').value;
      const toAcc = document.getElementById('toAccount').value;
      const amount = parseFloat(document.getElementById('amount').value);
      const note = document.getElementById('note').value || 'Transfer';

      if (fromAcc === toAcc) { toast('Cannot transfer to same account', 'error'); return; }
      
      const btn = document.getElementById('sendBtn');
      btn.disabled = true;
      btn.disabled_by_user = true;
      btn.textContent = 'Processing...';
      
      try {
        const r = await api('POST', '/transfer', { from_acc: fromAcc, to_acc: toAcc, amount, note });
        if (r._error) {
          toast(`Transfer failed: ${r._error}`, 'error');
        } else {
          toast(`✅ ₹${formatINR(amount)} transferred | QBER: ${(r.qber*100).toFixed(2)}%`, 'success');
          await loadAccounts();
          await loadRecentTx();
        }
      } catch (err) {
        toast('Error: ' + err.message, 'error');
      }
      btn.disabled = false;
      btn.disabled_by_user = false;
      btn.innerHTML = '<span class="material-symbols-outlined text-[16px]">lock</span> Transfer Now';
    });
  }

  // WebSocket
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}/ws/events`);
  ws.onmessage = (e) => {
    try {
      const ev = JSON.parse(e.data);
      if (ev.event === 'attack') {
        toast('⚠️ Channel interception! QBER: ' + ((ev.qber||0)*100).toFixed(1) + '%', 'error');
      } else if (ev.event === 'lockdown') {
        toast('🔒 EMERGENCY: All services suspended', 'error');
      }
      refreshStatus();
      loadRecentTx();
      loadAccounts();
    } catch(e){}
  };
});
