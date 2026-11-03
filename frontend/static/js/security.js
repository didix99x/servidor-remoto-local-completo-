/**
 * Security center page controller.
 */
const Security = (() => {

  // ----------------------------------------------------------------
  // LOAD
  // ----------------------------------------------------------------
  async function load() {
    await Promise.all([
      loadOverview(),
      loadAlerts(),
      loadAuditLogs(),
      loadEvents(),
    ]);
  }

  // ----------------------------------------------------------------
  // OVERVIEW
  // ----------------------------------------------------------------
  async function loadOverview() {
    try {
      const data = await API.getSecurityOverview();

      setText('sec-score',      `${data.security_score || 0}%`);
      setText('sec-unknown',    data.unknown_online || 0);
      setText('sec-login-fail', data.login_failures_24h || 0);
      setText('sec-new-devices', data.new_devices_24h || 0);

      // Update main badge
      App.updateBadge('badge-alerts',
        (data.unknown_online || 0) + (data.login_failures_24h || 0) > 0
          ? (data.unknown_online || 0) + (data.login_failures_24h || 0)
          : '0'
      );

      // Color the score
      const scoreEl = document.getElementById('sec-score');
      if (scoreEl) {
        const score = data.security_score || 0;
        scoreEl.style.color = score >= 80 ? 'var(--accent-green)' : score >= 50 ? 'var(--accent-orange)' : 'var(--accent-red)';
      }
    } catch (_) {}
  }

  // ----------------------------------------------------------------
  // ALERTS
  // ----------------------------------------------------------------
  async function loadAlerts() {
    const container = document.getElementById('security-alerts-container');
    if (!container) return;

    try {
      const data = await API.getAlerts(30);
      const alerts = data.alerts || [];

      if (alerts.length === 0) {
        container.innerHTML = `
          <div style="text-align:center;padding:32px;color:var(--text-muted)">
            ✅ Nenhum alerta de segurança
          </div>`;
        return;
      }

      const sevIcon = { info: 'ℹ️', warning: '⚠️', critical: '🚨' };
      container.innerHTML = alerts.map(a => `
        <div class="alert-item alert-${a.severity || 'info'}">
          <span class="alert-icon">${sevIcon[a.severity] || 'ℹ️'}</span>
          <div style="flex:1">
            <div class="alert-title">${a.title}</div>
            <div class="alert-msg">${a.message}</div>
            <div class="alert-time">${App.formatDateTime(a.created_at)}</div>
          </div>
          ${a.device_id ? `
            <button class="icon-btn" title="Ver dispositivo" onclick="Network.showDeviceDetail(${a.device_id})">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </button>` : ''}
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  // ----------------------------------------------------------------
  // AUDIT LOGS
  // ----------------------------------------------------------------
  async function loadAuditLogs() {
    const container = document.getElementById('audit-log-container');
    if (!container) return;

    try {
      const logs = await API.getAuditLogs(50);

      if (logs.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-muted)">Sem registros</div>';
        return;
      }

      container.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Hora</th>
              <th>Ação</th>
              <th>Recurso</th>
              <th>Detalhes</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            ${logs.map(log => `
              <tr>
                <td class="text-small text-muted" style="white-space:nowrap">${App.formatDateTime(log.timestamp)}</td>
                <td>
                  <span class="badge ${actionBadgeClass(log.action)}">${log.action.replace(/_/g, ' ')}</span>
                </td>
                <td class="text-small truncate" style="max-width:150px">${log.resource}</td>
                <td class="text-small text-muted truncate" style="max-width:200px">${log.details || '—'}</td>
                <td class="text-small text-muted">${log.ip_address || '—'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>`;
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  function actionBadgeClass(action) {
    if (action.includes('fail') || action.includes('block') || action.includes('unauthorized')) return 'badge-offline';
    if (action.includes('login') && !action.includes('fail')) return 'badge-authorized';
    if (action.includes('upload') || action.includes('download')) return 'badge-online';
    return 'badge-pending';
  }

  // ----------------------------------------------------------------
  // EVENTS
  // ----------------------------------------------------------------
  async function loadEvents() {
    const container = document.getElementById('events-container');
    if (!container) return;

    try {
      const data = await API.getEvents(24);
      const events = data.events || [];

      if (events.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-muted)">Sem eventos</div>';
        return;
      }

      const eventIcon = {
        online: '🟢', offline: '🔴', discovered: '🔍',
        authorized: '✅', revoked: '❌', blocked: '🚫',
        paired: '🔗', ip_change: '🔄', service_scan: '🔎',
      };

      container.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th></th>
              <th>Evento</th>
              <th>IP</th>
              <th>Detalhes</th>
              <th>Hora</th>
            </tr>
          </thead>
          <tbody>
            ${events.map(e => `
              <tr>
                <td style="text-align:center;font-size:1.1rem">${eventIcon[e.event_type] || '📌'}</td>
                <td>
                  <span class="text-small">${e.event_type.replace(/_/g, ' ')}</span>
                  ${e.device_id ? `<div class="text-small text-muted">Dev #${e.device_id}</div>` : ''}
                </td>
                <td class="text-small text-muted">${e.ip_address || '—'}</td>
                <td class="text-small text-muted truncate" style="max-width:200px">${e.details || '—'}</td>
                <td class="text-small text-muted" style="white-space:nowrap">${App.formatDateTime(e.timestamp)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>`;
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  return { load, loadAlerts, loadAuditLogs, loadEvents };

})();
