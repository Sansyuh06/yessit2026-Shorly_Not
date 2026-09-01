// SOC Live Feed Polling & UI Updater
document.addEventListener('DOMContentLoaded', () => {
  const stageSElem = document.getElementById('soc-stage-s');
  const stageQElem = document.getElementById('soc-stage-q');
  const stageSDescElem = document.getElementById('soc-stage-s-desc');
  const stageQDescElem = document.getElementById('soc-stage-q-desc');
  const lastThreatElem = document.getElementById('soc-last-threat');
  const mismatchValElem = document.getElementById('soc-mismatch-val');
  const tauValElem = document.getElementById('soc-tau-val');
  const meterFillElem = document.getElementById('soc-meter-fill');
  const tauMarkerElem = document.getElementById('soc-tau-marker');
  const feedBodyElem = document.getElementById('soc-feed-body');
  const backendBadgeElem = document.getElementById('soc-backend-badge');

  const pforgeBadgeElem = document.getElementById('soc-pforge-badge');
  const tauParamValElem = document.getElementById('soc-tau-param-val');

  function calculatePForge(n, tau) {
    const kMax = Math.floor(tau * n);
    let sum = 0.0;
    for (let k = 0; k <= kMax; k++) {
      let logComb = 0;
      for (let i = 1; i <= k; i++) {
        logComb += Math.log(n - i + 1) - Math.log(i);
      }
      const prob = Math.exp(logComb - n * Math.LN2);
      sum += prob;
    }
    return sum;
  }

  const iptablesOutputElem = document.getElementById('iptables-terminal-output');
  const iptablesBadgeElem = document.getElementById('iptables-mode-badge');
  const iptablesDotElem = document.getElementById('iptables-status-dot');
  const iptablesDropElem = document.getElementById('iptables-drop-counter');

  let simulatedDropPackets = 0;

  function renderIPTables(stageS, stageQ, lastThreat) {
    if (!iptablesOutputElem) return;

    if (stageS === 0) {
      simulatedDropPackets = 0;
      if (iptablesDotElem) iptablesDotElem.style.backgroundColor = 'var(--soc-green)';
      if (iptablesBadgeElem) {
        iptablesBadgeElem.innerHTML = 'POLICY: ACCEPT (S0)';
        iptablesBadgeElem.style.color = 'var(--soc-green)';
        iptablesBadgeElem.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        iptablesBadgeElem.style.background = 'rgba(16, 185, 129, 0.15)';
      }
      if (iptablesDropElem) iptablesDropElem.textContent = 'DROPPED PKTS: 0';

      iptablesOutputElem.innerHTML = 
`<span class="term-cyan">Chain INPUT (policy ACCEPT 8,421 packets, 5.2M bytes)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1     8.4K  5.2M <span class="term-green">ACCEPT</span>     tcp  --  eth0   *       0.0.0.0/0       10.0.0.80       dpt:8080 state:ESTABLISHED

<span class="term-cyan">Chain FORWARD (policy ACCEPT 14.8K packets, 11.2M bytes)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1    14.8K 11.2M <span class="term-green">ACCEPT</span>     tcp  --  eth0   eth1    192.168.1.0/24  10.0.0.80       dpt:8080/tx <span class="term-dim">[QDS-T1 PASS: p̂ ≤ τ]</span>

<span class="term-cyan">Chain OUTPUT (policy ACCEPT 9,120 packets, 6.4M bytes)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1     9.1K  6.4M <span class="term-green">ACCEPT</span>     all  --  *      *       0.0.0.0/0       0.0.0.0/0`;
    } else if (stageS === 1) {
      simulatedDropPackets += 1;
      if (iptablesDotElem) iptablesDotElem.style.backgroundColor = 'var(--soc-yellow)';
      if (iptablesBadgeElem) {
        iptablesBadgeElem.innerHTML = 'POLICY: RATE-LIMIT (S1)';
        iptablesBadgeElem.style.color = 'var(--soc-yellow)';
        iptablesBadgeElem.style.borderColor = 'rgba(245, 158, 11, 0.4)';
        iptablesBadgeElem.style.background = 'rgba(245, 158, 11, 0.15)';
      }
      if (iptablesDropElem) iptablesDropElem.textContent = `DROPPED PKTS: ${simulatedDropPackets}`;

      iptablesOutputElem.innerHTML = 
`<span class="term-cyan">Chain FORWARD (policy ACCEPT 15.2K packets, 11.6M bytes)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1       64  4.2K <span class="term-yellow">LOG</span>        tcp  --  eth0   eth1    0.0.0.0/0       10.0.0.80       LOG "Q-STDF: Anomaly p̂ elevated"
 2    15.1K 11.5M <span class="term-yellow">LIMIT</span>      tcp  --  eth0   eth1    0.0.0.0/0       10.0.0.80       dpt:8080 limit: avg 5/min <span class="term-dim">[ANOMALY WATCH]</span>`;
    } else if (stageS === 2) {
      simulatedDropPackets += Math.floor(Math.random() * 8) + 12;
      if (iptablesDotElem) iptablesDotElem.style.backgroundColor = '#f97316';
      if (iptablesBadgeElem) {
        iptablesBadgeElem.innerHTML = 'POLICY: REJECT / SUSPEND (S2)';
        iptablesBadgeElem.style.color = '#f97316';
        iptablesBadgeElem.style.borderColor = 'rgba(249, 115, 22, 0.4)';
        iptablesBadgeElem.style.background = 'rgba(249, 115, 22, 0.15)';
      }
      if (iptablesDropElem) iptablesDropElem.textContent = `DROPPED PKTS: ${simulatedDropPackets}`;

      iptablesOutputElem.innerHTML = 
`<span class="term-cyan">Chain FORWARD (policy DROP ${simulatedDropPackets} packets)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1      <span class="term-orange">${simulatedDropPackets}</span>  ${(simulatedDropPackets * 0.6).toFixed(1)}K <span class="term-orange">REJECT</span>     tcp  --  eth0   eth1    0.0.0.0/0       10.0.0.80/tx    <span class="term-orange">reject-with tcp-reset [THREAT: ${lastThreat}]</span>
 2     2.4K  1.8M <span class="term-green">ACCEPT</span>     tcp  --  eth0   eth1    0.0.0.0/0       10.0.0.80       dpt:8080/history,soc <span class="term-dim">(READ-ONLY)</span>`;
    } else if (stageS === 3) {
      simulatedDropPackets += Math.floor(Math.random() * 15) + 35;
      if (iptablesDotElem) iptablesDotElem.style.backgroundColor = 'var(--soc-red)';
      if (iptablesBadgeElem) {
        iptablesBadgeElem.innerHTML = 'POLICY: DROP TRANSACTIONS (S3)';
        iptablesBadgeElem.style.color = 'var(--soc-red)';
        iptablesBadgeElem.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        iptablesBadgeElem.style.background = 'rgba(239, 68, 68, 0.15)';
      }
      if (iptablesDropElem) iptablesDropElem.textContent = `DROPPED PKTS: ${simulatedDropPackets}`;

      iptablesOutputElem.innerHTML = 
`<span class="term-cyan">Chain FORWARD (policy DROP ${simulatedDropPackets} packets)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1      <span class="term-red">${simulatedDropPackets}</span>  ${(simulatedDropPackets * 0.7).toFixed(1)}K <span class="term-red">DROP</span>       tcp  --  eth0   eth1    0.0.0.0/0       10.0.0.80/tx    <span class="term-red">[REPLAY/PARAM ISOLATION MODE]</span>
 2      680  420K <span class="term-green">ACCEPT</span>     tcp  --  eth0   eth1    0.0.0.0/0       10.0.0.80/audit <span class="term-dim">(AUDIT STREAM ONLY)</span>`;
    } else { // S4
      simulatedDropPackets += Math.floor(Math.random() * 30) + 95;
      if (iptablesDotElem) iptablesDotElem.style.backgroundColor = '#ff0055';
      if (iptablesBadgeElem) {
        iptablesBadgeElem.innerHTML = 'POLICY: CRITICAL GATEWAY LOCKDOWN (S4)';
        iptablesBadgeElem.style.color = '#ff0055';
        iptablesBadgeElem.style.borderColor = 'rgba(255, 0, 85, 0.5)';
        iptablesBadgeElem.style.background = 'rgba(255, 0, 85, 0.2)';
      }
      if (iptablesDropElem) iptablesDropElem.textContent = `DROPPED PKTS: ${simulatedDropPackets}`;

      iptablesOutputElem.innerHTML = 
`<span class="term-red">Chain INPUT (policy DROP ${simulatedDropPackets} packets)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1      <span class="term-red">${simulatedDropPackets}</span>  ${(simulatedDropPackets * 0.8).toFixed(1)}K <span class="term-red">DROP</span>       all  --  *      *       0.0.0.0/0       0.0.0.0/0       <span class="term-red">[CRITICAL: FULL QUANTUM CUTOFF]</span>

<span class="term-red">Chain FORWARD (policy DROP)</span>
 num   pkts bytes target     prot opt in     out     source          destination     info
 1      <span class="term-red">${simulatedDropPackets}</span>  ${(simulatedDropPackets * 0.8).toFixed(1)}K <span class="term-red">DROP</span>       all  --  *      *       0.0.0.0/0       0.0.0.0/0       <span class="term-red">[BANK LOCKED: S4]</span>`;
    }
  }

  async function fetchSocFeed() {
    try {
      const res = await fetch('/api/soc/feed');
      if (!res.ok) return;
      const data = await res.json();

      // Update Stages
      const s = data.stages.stage_s;
      const q = data.stages.stage_q;
      
      stageSElem.textContent = `S${s}`;
      stageSElem.className = `stage-value stage-s${s}`;

      const sDescriptions = {
        0: 'Normal · All Services Operational',
        1: 'Anomaly Warning · Transfers Allowed',
        2: 'Active Threat · Transfers Blocked',
        3: 'Pattern Attack · Read-Only Mode',
        4: 'CRITICAL LOCKDOWN · Bank Locked'
      };
      stageSDescElem.textContent = sDescriptions[s] || 'Unknown';

      stageQElem.textContent = `Q${q}`;
      const qDescriptions = {
        0: 'QBER < 5% (Optimal Link)',
        1: 'QBER 5-8% (Watch)',
        2: 'QBER 8-11% (Elevated Noise)',
        3: 'QBER 11-20% (Compromised)',
        4: 'QBER >= 20% (Eve Interception)'
      };
      stageQDescElem.textContent = qDescriptions[q] || 'Link Active';

      // Update Mismatch and Tau
      const mismatch = data.stages.last_mismatch || 0.0;
      const tau = data.stages.tau || 0.2097;
      const n = data.stages.n || 64;
      mismatchValElem.textContent = mismatch.toFixed(4);
      tauValElem.textContent = tau.toFixed(4);
      if (tauParamValElem) tauParamValElem.textContent = tau.toFixed(4);

      // Compute and update P_forge
      if (pforgeBadgeElem) {
        const pForgeVal = calculatePForge(n, tau);
        if (pForgeVal < 1e-12) {
          pforgeBadgeElem.innerHTML = `P_forge: &lt; 10<sup>-12</sup>`;
        } else {
          pforgeBadgeElem.innerHTML = `P_forge: ${pForgeVal.toExponential(2)}`;
        }
      }

      // Meter fill (scale to 0.70 max)
      const fillPct = Math.min(100, Math.max(2, (mismatch / 0.60) * 100));
      const tauPct = Math.min(100, Math.max(5, (tau / 0.60) * 100));

      meterFillElem.style.width = `${fillPct}%`;
      if (mismatch > tau) {
        meterFillElem.classList.add('danger');
      } else {
        meterFillElem.classList.remove('danger');
      }
      tauMarkerElem.style.left = `${tauPct}%`;

      // Update Threat Label
      const threat = data.stages.last_threat || 'OK';
      lastThreatElem.textContent = threat;
      lastThreatElem.className = `soc-tag tag-${threat.toLowerCase().replace('_', '-')}`;

      // Update IPTables Live Simulation
      renderIPTables(s, q, threat);

      // Update Feed Table
      if (data.events && data.events.length > 0) {
        feedBodyElem.innerHTML = data.events.map(e => {
          const isThreat = (e.threat_label !== 'OK');
          const rowClass = isThreat ? 'feed-row-threat' : '';
          const tagClass = `tag-${e.threat_label.toLowerCase().replace('_', '-')}`;
          const timeShort = e.timestamp.split('T')[1].substring(0, 8);
          return `
            <tr class="${rowClass}">
              <td>${timeShort}</td>
              <td><span class="soc-tag ${tagClass}">${e.threat_label}</span></td>
              <td>S${e.stage_s} / Q${e.stage_q}</td>
              <td>${e.mismatch_rate.toFixed(4)}</td>
              <td>${e.tau.toFixed(4)}</td>
              <td>${e.actor || 'system'}</td>
              <td title="${e.details}">${e.details.substring(0, 45)}${e.details.length > 45 ? '...' : ''}</td>
            </tr>
          `;
        }).join('');
      }

    } catch (err) {
      console.error('Error polling SOC feed:', err);
    }
  }

  // Poll every 1000ms
  fetchSocFeed();
  setInterval(fetchSocFeed, 1000);

  // Attack buttons handling
  const attackButtons = document.querySelectorAll('.btn-attack');
  attackButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const atkType = btn.getAttribute('data-attack');
      btn.textContent = 'Triggering...';
      try {
        const resp = await fetch(`/soc/attack/${atkType}`, { method: 'POST' });
        if (resp.status === 401) {
          alert('Operator authentication required. Please log in with ops / ops123.');
        }
        await fetchSocFeed();
      } catch (err) {
        console.error(err);
      } finally {
        btn.textContent = atkType.toUpperCase();
      }
    });
  });

  // Reset button handling
  const resetBtn = document.getElementById('soc-reset-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      resetBtn.textContent = 'Resetting...';
      try {
        const resp = await fetch('/soc/reset', { method: 'POST' });
        if (resp.status === 401) {
          alert('Operator authentication required. Please log in with ops / ops123.');
        }
        await fetchSocFeed();
      } catch (err) {
        console.error(err);
      } finally {
        resetBtn.textContent = 'RESET SECURITY STAGES (S0, Q0)';
      }
    });
  }
});

