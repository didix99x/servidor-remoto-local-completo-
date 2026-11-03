/**
 * Network monitor page controller.
 */
const Network = (() => {

  let _devices = [];
  let _filterStatus = '';
  let _selectedDevice = null;

  // ----------------------------------------------------------------
  // LOAD
  // ----------------------------------------------------------------
  async function load() {
    await Promise.all([loadDevices(), loadNetworkMap()]);
  }

  async function loadDevices() {
    const container = document.getElementById('devices-table-container');
    if (!container) return;

    try {
      _devices = await API.listDevices();
      renderDevicesTable(_devices);
      updateUnknownBadge();
    } catch (err) {
      container.innerHTML = `<div style="text-align:center;padding:32px;color:var(--accent-red)">Erro: ${err.message}</div>`;
    }
  }

  function updateUnknownBadge() {
    const unknown = _devices.filter(d => !d.is_known && d.is_online).length;
    App.updateBadge('badge-unknown', unknown || '0');
  }

  function renderDevicesTable(devices) {
    const container = document.getElementById('devices-table-container');
    if (!container) return;

    if (devices.length === 0) {
      container.innerHTML = `
        <div style="text-align:center;padding:48px;color:var(--text-muted)">
          <div style="font-size:2.5rem;margin-bottom:12px">📡</div>
          <p>Nenhum dispositivo encontrado.</p>
          <p class="text-small" style="margin-top:8px">Execute uma varredura de rede para descobrir dispositivos.</p>
          <button class="btn btn-primary" style="margin-top:16px" onclick="App.triggerScan()">Escanear Rede</button>
        </div>`;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th></th>
            <th>Dispositivo</th>
            <th>IP</th>
            <th>MAC</th>
            <th>Fabricante</th>
            <th>Tipo</th>
            <th>Status</th>
            <th>Autorizado</th>
            <th>Visto</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          ${devices.map(d => deviceRow(d)).join('')}
        </tbody>
      </table>`;
  }

  function deviceRow(d) {
    const statusBadge = d.is_online
      ? '<span class="badge badge-online"><span class="online-dot dot-online"></span> Online</span>'
      : '<span class="badge badge-offline"><span class="online-dot dot-offline"></span> Offline</span>';

    const authBadge = d.is_authorized
      ? '<span class="badge badge-authorized">✓ Sim</span>'
      : (d.is_known
          ? '<span class="badge badge-offline">Não</span>'
          : '<span class="badge badge-unknown">Novo</span>');

    const lastSeen = d.last_seen ? App.formatDateTime(d.last_seen) : '—';

    return `
      <tr>
        <td style="font-size:1.3rem;text-align:center;padding:8px 4px">${App.deviceTypeIcon(d.device_type)}</td>
        <td>
          <div style="font-weight:600">${d.hostname || '—'}</div>
          ${d.os_info ? `<div class="text-small text-muted">${d.os_info}</div>` : ''}
        </td>
        <td class="text-small">${d.ip_address || '—'}</td>
        <td class="text-small text-muted">${d.mac_address}</td>
        <td class="text-small">${d.vendor || '—'}</td>
        <td class="text-small text-muted">${App.deviceTypeLabel(d.device_type)}</td>
        <td>${statusBadge}</td>
        <td>${authBadge}</td>
        <td class="text-small text-muted">${lastSeen}</td>
        <td>
          <div class="flex gap-8">
            <button class="icon-btn" title="Detalhes" onclick="Network.showDeviceDetail(${d.id})">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </button>
            ${!d.is_authorized ? `
              <button class="icon-btn" title="Autorizar" style="color:var(--accent-green)" onclick="Network.authorizeDevice(${d.id})">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              </button>` : `
              <button class="icon-btn" title="Revogar Acesso" style="color:var(--accent-orange)" onclick="Network.revokeDevice(${d.id})">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              </button>`}
            <button class="icon-btn" title="Bloquear" style="color:var(--accent-red)" onclick="Network.blockDevice(${d.id})">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>
            </button>
          </div>
        </td>
      </tr>`;
  }

  // ----------------------------------------------------------------
  // FILTER
  // ----------------------------------------------------------------
  function filterDevices() {
    const search = (document.getElementById('device-search')?.value || '').toLowerCase();
    const filtered = _devices.filter(d => {
      const matchSearch = !search || [d.hostname, d.ip_address, d.mac_address, d.vendor]
        .some(v => v && v.toLowerCase().includes(search));
      const matchStatus = !_filterStatus ||
        (_filterStatus === 'online' && d.is_online) ||
        (_filterStatus === 'offline' && !d.is_online) ||
        (_filterStatus === 'unknown' && !d.is_known) ||
        (_filterStatus === 'authorized' && d.is_authorized);
      return matchSearch && matchStatus;
    });
    renderDevicesTable(filtered);
  }

  function filterByStatus(val) {
    _filterStatus = val;
    filterDevices();
  }

  // ----------------------------------------------------------------
  // ACTIONS
  // ----------------------------------------------------------------
  async function authorizeDevice(id) {
    try {
      await API.authorizeDevice(id);
      App.showToast('success', '✅ Dispositivo autorizado');
      await loadDevices();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  async function revokeDevice(id) {
    if (!confirm('Revogar autorização deste dispositivo?')) return;
    try {
      await API.revokeDevice(id);
      App.showToast('success', 'Acesso revogado');
      await loadDevices();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  async function blockDevice(id) {
    if (!confirm('Bloquear este dispositivo? Ele será marcado como não autorizado.')) return;
    try {
      await API.blockDevice(id);
      App.showToast('warning', '🚫 Dispositivo bloqueado');
      await loadDevices();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  // ----------------------------------------------------------------
  // DEVICE DETAIL MODAL
  // ----------------------------------------------------------------
  async function showDeviceDetail(id) {
    const modal = document.getElementById('device-detail-modal');
    const content = document.getElementById('device-detail-content');
    modal.classList.add('active');
    content.innerHTML = '<div style="text-align:center;padding:32px"><div class="loading-spinner"></div></div>';

    try {
      const [device, history] = await Promise.all([
        API.getDevice(id),
        API.deviceHistory(id, 20),
      ]);
      _selectedDevice = device;

      content.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
          ${infoRow('Hostname', device.hostname || '—')}
          ${infoRow('IP', device.ip_address || '—')}
          ${infoRow('MAC', device.mac_address)}
          ${infoRow('Fabricante', device.vendor || '—')}
          ${infoRow('Tipo', App.deviceTypeLabel(device.device_type))}
          ${infoRow('SO', device.os_info || '—')}
          ${infoRow('Status', device.is_online ? '🟢 Online' : '🔴 Offline')}
          ${infoRow('Autorizado', device.is_authorized ? '✅ Sim' : '❌ Não')}
          ${infoRow('Primeiro visto', App.formatDateTime(device.first_seen))}
          ${infoRow('Último visto', App.formatDateTime(device.last_seen))}
        </div>

        <div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap">
          ${!device.is_authorized
            ? `<button class="btn btn-success" onclick="Network.authorizeDevice(${id});Network.closeDeviceModal()">✅ Autorizar</button>`
            : `<button class="btn btn-warning" onclick="Network.revokeDevice(${id});Network.closeDeviceModal()">Revogar</button>`
          }
          <button class="btn btn-danger" onclick="Network.blockDevice(${id});Network.closeDeviceModal()">🚫 Bloquear</button>
        </div>

        <div class="card-title" style="margin-bottom:10px">Histórico de Conexões</div>
        <div style="max-height:200px;overflow-y:auto">
          ${history.length === 0
            ? '<div class="text-small text-muted">Sem histórico</div>'
            : history.map(h => `
                <div class="flex items-center gap-8" style="padding:6px 0;border-bottom:1px solid var(--border-color)">
                  <span class="text-small text-muted" style="width:130px;flex-shrink:0">${App.formatDateTime(h.timestamp)}</span>
                  <span class="badge ${eventBadgeClass(h.event_type)}">${h.event_type}</span>
                  <span class="text-small text-muted truncate">${h.details || ''}</span>
                </div>
              `).join('')
          }
        </div>`;
    } catch (err) {
      content.innerHTML = `<div style="color:var(--accent-red);text-align:center;padding:24px">Erro: ${err.message}</div>`;
    }
  }

  function infoRow(label, value) {
    return `
      <div style="background:var(--bg-secondary);border-radius:6px;padding:10px 12px">
        <div class="text-small text-muted">${label}</div>
        <div class="text-small" style="color:var(--text-primary);font-weight:500;margin-top:2px">${value}</div>
      </div>`;
  }

  function eventBadgeClass(type) {
    const map = {
      online: 'badge-online', offline: 'badge-offline', discovered: 'badge-unknown',
      authorized: 'badge-authorized', revoked: 'badge-offline', blocked: 'badge-offline',
    };
    return map[type] || 'badge-pending';
  }

  function closeDeviceModal() {
    document.getElementById('device-detail-modal').classList.remove('active');
  }

  // ----------------------------------------------------------------
  // NETWORK MAP
  // ----------------------------------------------------------------
  async function loadNetworkMap() {
    const container = document.getElementById('network-map-canvas');
    if (!container) return;

    try {
      const data = await API.networkMap();
      renderNetworkMap(container, data);
    } catch (_) {}
  }

  function renderNetworkMap(container, data) {
    const { nodes, edges } = data;
    if (!nodes || nodes.length === 0) {
      container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted)">Escaneie a rede para ver o mapa</div>';
      return;
    }

    const W = container.offsetWidth || 600;
    const H = 400;

    container.innerHTML = `<svg width="${W}" height="${H}" style="width:100%;height:100%"></svg>`;
    const svg = container.querySelector('svg');

    // Position nodes in a circular layout around the gateway
    const gateway = nodes.find(n => n.id === 'gateway');
    const server = nodes.find(n => n.id === 'server');
    const others = nodes.filter(n => n.id !== 'gateway' && n.id !== 'server');

    const positions = {};
    const cx = W / 2, cy = H / 2;

    if (gateway) positions[gateway.id] = { x: cx, y: cy };
    if (server)  positions[server.id]  = { x: cx, y: cy - 100 };

    const angleStep = (2 * Math.PI) / Math.max(others.length, 1);
    const radius = Math.min(W, H) * 0.35;

    others.forEach((node, i) => {
      const angle = angleStep * i - Math.PI / 2;
      positions[node.id] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });

    // Draw edges
    edges.forEach(edge => {
      const from = positions[edge.source];
      const to = positions[edge.target];
      if (!from || !to) return;
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', from.x); line.setAttribute('y1', from.y);
      line.setAttribute('x2', to.x);   line.setAttribute('y2', to.y);
      line.setAttribute('stroke', 'rgba(0,212,255,0.15)');
      line.setAttribute('stroke-width', '1');
      svg.appendChild(line);
    });

    // Draw nodes
    nodes.forEach(node => {
      const pos = positions[node.id];
      if (!pos) return;

      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('transform', `translate(${pos.x},${pos.y})`);
      g.style.cursor = node.id.startsWith('dev_') ? 'pointer' : 'default';

      // Circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('r', node.id === 'gateway' ? 22 : node.id === 'server' ? 18 : 16);

      let fill, stroke;
      if (node.id === 'gateway')      { fill = 'rgba(123,47,255,0.2)'; stroke = '#7b2fff'; }
      else if (node.id === 'server')  { fill = 'rgba(0,212,255,0.2)';  stroke = '#00d4ff'; }
      else if (node.is_online && node.is_authorized) { fill = 'rgba(0,212,255,0.1)'; stroke = '#00d4ff'; }
      else if (node.is_online)  { fill = 'rgba(255,149,0,0.1)';  stroke = '#ff9500'; }
      else                      { fill = 'rgba(255,255,255,0.03)'; stroke = '#4a6278'; }

      circle.setAttribute('fill', fill);
      circle.setAttribute('stroke', stroke);
      circle.setAttribute('stroke-width', '1.5');

      // Icon text
      const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      icon.setAttribute('text-anchor', 'middle');
      icon.setAttribute('dominant-baseline', 'central');
      icon.setAttribute('font-size', node.id === 'gateway' ? '14' : '12');
      icon.textContent = nodeIcon(node);

      // Label
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('text-anchor', 'middle');
      label.setAttribute('y', node.id === 'gateway' ? '32' : '26');
      label.setAttribute('font-size', '10');
      label.setAttribute('fill', '#7a9ab8');
      const labelText = (node.label || '').slice(0, 14);
      label.textContent = labelText;

      g.appendChild(circle);
      g.appendChild(icon);
      g.appendChild(label);

      if (node.id.startsWith('dev_')) {
        const devId = parseInt(node.id.replace('dev_', ''));
        g.addEventListener('click', () => showDeviceDetail(devId));
      }

      svg.appendChild(g);
    });
  }

  function nodeIcon(node) {
    if (node.id === 'gateway') return '📡';
    if (node.id === 'server')  return '🖥️';
    return App.deviceTypeIcon(node.type);
  }

  return {
    load, filterDevices, filterByStatus,
    authorizeDevice, revokeDevice, blockDevice,
    showDeviceDetail, closeDeviceModal,
  };

})();
