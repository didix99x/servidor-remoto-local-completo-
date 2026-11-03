/**
 * Device manager page controller.
 */
const Devices = (() => {

  let _currentTab = 'all';
  let _pairingRequests = [];

  // ----------------------------------------------------------------
  // LOAD
  // ----------------------------------------------------------------
  async function load() {
    await Promise.all([loadAllDevices(), loadPairingRequests()]);
  }

  // ----------------------------------------------------------------
  // TABS
  // ----------------------------------------------------------------
  function switchTab(tab, el) {
    _currentTab = tab;
    document.querySelectorAll('#page-devices .tab').forEach(t => t.classList.remove('active'));
    if (el) el.classList.add('active');

    document.getElementById('tab-all').style.display    = tab === 'all'     ? 'block' : 'none';
    document.getElementById('tab-pairing').style.display = tab === 'pairing' ? 'block' : 'none';

    if (tab === 'pairing') loadPairingRequests();
  }

  // ----------------------------------------------------------------
  // ALL DEVICES
  // ----------------------------------------------------------------
  async function loadAllDevices() {
    const container = document.getElementById('all-devices-container');
    if (!container) return;

    try {
      const devices = await API.listDevices();
      renderAllDevices(container, devices);
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  function renderAllDevices(container, devices) {
    if (devices.length === 0) {
      container.innerHTML = `
        <div style="text-align:center;padding:48px;color:var(--text-muted)">
          <div style="font-size:2.5rem;margin-bottom:12px">📱</div>
          <p>Nenhum dispositivo cadastrado.</p>
          <button class="btn btn-primary" style="margin-top:16px" onclick="App.triggerScan()">Escanear Rede</button>
        </div>`;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Dispositivo</th>
            <th>IP / MAC</th>
            <th>Status</th>
            <th>Autorização</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          ${devices.map(d => `
            <tr>
              <td style="font-size:1.2rem;text-align:center">${App.deviceTypeIcon(d.device_type)}</td>
              <td>
                <div style="font-weight:600">${d.hostname || '—'}</div>
                <div class="text-small text-muted">${App.deviceTypeLabel(d.device_type)}</div>
              </td>
              <td>
                <div class="text-small">${d.ip_address || '—'}</div>
                <div class="text-small text-muted">${d.mac_address}</div>
              </td>
              <td>
                ${d.is_online
                  ? '<span class="badge badge-online">Online</span>'
                  : '<span class="badge badge-offline">Offline</span>'}
              </td>
              <td>
                ${d.is_authorized
                  ? '<span class="badge badge-authorized">✓ Autorizado</span>'
                  : (d.is_known
                      ? '<span class="badge badge-offline">Não autorizado</span>'
                      : '<span class="badge badge-unknown">Novo</span>')}
              </td>
              <td>
                <div class="flex gap-8">
                  ${!d.is_authorized
                    ? `<button class="btn btn-success" style="padding:4px 10px;font-size:0.78rem" onclick="Devices.authorize(${d.id})">✅ Autorizar</button>`
                    : `<button class="btn btn-warning" style="padding:4px 10px;font-size:0.78rem" onclick="Devices.revoke(${d.id})">Revogar</button>`}
                  <button class="btn btn-danger" style="padding:4px 10px;font-size:0.78rem" onclick="Devices.block(${d.id})">🚫</button>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  }

  // ----------------------------------------------------------------
  // ACTIONS
  // ----------------------------------------------------------------
  async function authorize(id) {
    try {
      await API.authorizeDevice(id);
      App.showToast('success', '✅ Dispositivo autorizado');
      await loadAllDevices();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  async function revoke(id) {
    if (!confirm('Revogar autorização deste dispositivo?')) return;
    try {
      await API.revokeDevice(id);
      App.showToast('success', 'Autorização revogada');
      await loadAllDevices();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  async function block(id) {
    if (!confirm('Bloquear este dispositivo?')) return;
    try {
      await API.blockDevice(id);
      App.showToast('warning', '🚫 Dispositivo bloqueado');
      await loadAllDevices();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  // ----------------------------------------------------------------
  // PAIRING
  // ----------------------------------------------------------------
  async function loadPairingRequests() {
    const container = document.getElementById('pairing-requests-container');
    if (!container) return;

    try {
      _pairingRequests = await API.listPairingRequests();
      const pending = _pairingRequests.filter(r => r.status === 'pending');

      // Update badge
      const badgeEl = document.getElementById('badge-pairing');
      const countEl = document.getElementById('pairing-tab-count');
      if (badgeEl) {
        if (pending.length > 0) {
          badgeEl.textContent = pending.length;
          badgeEl.classList.remove('hidden');
          document.getElementById('pending-pairing-badge').style.display = 'flex';
        } else {
          badgeEl.classList.add('hidden');
          document.getElementById('pending-pairing-badge').style.display = 'none';
        }
      }
      App.updateBadge('badge-pairing', pending.length > 0 ? pending.length : '0');
      if (countEl) countEl.textContent = pending.length > 0 ? `(${pending.length})` : '';

      renderPairingRequests(container, _pairingRequests);
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  function renderPairingRequests(container, requests) {
    if (requests.length === 0) {
      container.innerHTML = `
        <div style="text-align:center;padding:32px;color:var(--text-muted)">
          <div style="font-size:2rem;margin-bottom:8px">🔗</div>
          <p>Nenhuma solicitação de pareamento.</p>
        </div>`;
      return;
    }

    const statusBadge = { pending: 'badge-pending', approved: 'badge-authorized', rejected: 'badge-offline', expired: 'badge-offline' };
    const statusLabel = { pending: 'Pendente', approved: 'Aprovado', rejected: 'Rejeitado', expired: 'Expirado' };

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Dispositivo</th>
            <th>IP</th>
            <th>Solicitante</th>
            <th>Status</th>
            <th>Data</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          ${requests.map(r => `
            <tr>
              <td>
                <div style="font-weight:600">${r.device_hostname || '—'}</div>
                <div class="text-small text-muted">${r.device_mac}</div>
              </td>
              <td class="text-small">${r.device_ip || '—'}</td>
              <td class="text-small">${r.requester_name}</td>
              <td><span class="badge ${statusBadge[r.status] || ''}">${statusLabel[r.status] || r.status}</span></td>
              <td class="text-small text-muted">${App.formatDateTime(r.requested_at)}</td>
              <td>
                ${r.status === 'pending' ? `
                  <div class="flex gap-8">
                    <button class="btn btn-success" style="padding:4px 10px;font-size:0.78rem" onclick="Devices.respondPairing(${r.id}, 'approve')">✅ Aprovar</button>
                    <button class="btn btn-danger" style="padding:4px 10px;font-size:0.78rem" onclick="Devices.respondPairing(${r.id}, 'reject')">❌ Rejeitar</button>
                  </div>` : '—'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  }

  async function respondPairing(requestId, action) {
    const label = action === 'approve' ? 'aprovar' : 'rejeitar';
    if (!confirm(`Deseja ${label} esta solicitação?`)) return;

    try {
      await API.respondPairing(requestId, action);
      App.showToast('success', `Solicitação ${label === 'aprovar' ? 'aprovada' : 'rejeitada'}`);
      await loadPairingRequests();
      await loadAllDevices();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  return { load, switchTab, authorize, revoke, block, loadPairingRequests, respondPairing };

})();
