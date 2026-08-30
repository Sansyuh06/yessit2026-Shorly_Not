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
      mismatchValElem.textContent = mismatch.toFixed(4);
      tauValElem.textContent = tau.toFixed(4);

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
        await fetch(`/soc/attack/${atkType}`, { method: 'POST' });
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
        await fetch('/soc/reset', { method: 'POST' });
        await fetchSocFeed();
      } catch (err) {
        console.error(err);
      } finally {
        resetBtn.textContent = 'RESET SECURITY STAGES (S0, Q0)';
      }
    });
  }
});
