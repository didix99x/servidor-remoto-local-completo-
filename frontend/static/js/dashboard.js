/**
 * Dashboard page controller.
 */
const Dashboard = (() => {

  let _trafficChart = null;
  const _trafficData = { download: [], upload: [], labels: [] };
  const MAX_POINTS = 40;

  // ----------------------------------------------------------------
  // INIT CHART
  // ----------------------------------------------------------------
  function initTrafficChart() {
    const ctx = document.getElementById('chart-traffic');
    if (!ctx) return;
    if (_trafficChart) { _trafficChart.destroy(); _trafficChart = null; }

    const commonDataset = {
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
    };

    _trafficChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: _trafficData.labels,
        datasets: [
          {
            ...commonDataset,
            label: 'Download',
            data: _trafficData.download,
            borderColor: '#00d4ff',
            backgroundColor: 'rgba(0,212,255,0.08)',
          },
          {
            ...commonDataset,
            label: 'Upload',
            data: _trafficData.upload,
            borderColor: '#ff9500',
            backgroundColor: 'rgba(255,149,0,0.08)',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 200 },
        scales: {
          x: {
            display: false,
            grid: { display: false },
          },
          y: {
            display: true,
            grid: { color: 'rgba(30,48,80,0.5)', borderDash: [4,4] },
            ticks: {
              color: '#4a6278',
              font: { size: 10 },
              callback: (v) => App.formatSpeed(v),
            },
          },
        },
        plugins: {
          legend: {
            labels: {
              color: '#7a9ab8',
              font: { size: 11 },
              boxWidth: 12,
              usePointStyle: true,
            },
          },
          tooltip: {
            backgroundColor: '#111827',
            titleColor: '#e8f4fd',
            bodyColor: '#7a9ab8',
            borderColor: '#1e3050',
            borderWidth: 1,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${App.formatSpeed(ctx.raw)}`,
            },
          },
        },
      },
    });
  }

  // ----------------------------------------------------------------
  // UPDATE STATS (from WebSocket)
  // ----------------------------------------------------------------
  function updateStats(data) {
    // CPU
    const cpuPct = data.cpu_percent || 0;
    safeText('cpu-pct', `${cpuPct.toFixed(1)}%`);
    safeStyle('cpu-bar', 'width', `${cpuPct}%`);
    const cpuBar = document.getElementById('cpu-bar');
    if (cpuBar) {
      cpuBar.className = 'progress-fill ' + (cpuPct > 80 ? 'red' : cpuPct > 60 ? 'orange' : 'blue');
    }

    // Memory
    const memPct = data.memory_percent || 0;
    safeText('mem-pct', `${memPct.toFixed(1)}%`);
    safeStyle('mem-bar', 'width', `${memPct}%`);
    const memBar = document.getElementById('mem-bar');
    if (memBar) {
      memBar.className = 'progress-fill ' + (memPct > 90 ? 'red' : memPct > 70 ? 'orange' : 'green');
    }
    safeText('mem-detail', `${(data.memory_used_gb || 0).toFixed(1)}/${(data.memory_total_gb || 0).toFixed(1)} GB`);

    // Disk
    const diskPct = data.disk_percent || 0;
    safeText('disk-pct', `${diskPct.toFixed(1)}%`);
    safeStyle('disk-bar', 'width', `${diskPct}%`);
    const diskBar = document.getElementById('disk-bar');
    if (diskBar) {
      diskBar.className = 'progress-fill ' + (diskPct > 90 ? 'red' : diskPct > 70 ? 'orange' : 'orange');
    }
    safeText('disk-detail', `${(data.disk_free_gb || 0).toFixed(1)} GB livres`);

    // Network speed
    const down = data.download_bps || 0;
    const up = data.upload_bps || 0;
    safeText('stat-net-down', App.formatSpeed(down));
    safeText('stat-net-up', App.formatSpeed(up));

    // Update chart
    const label = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    _trafficData.download.push(down);
    _trafficData.upload.push(up);
    _trafficData.labels.push(label);

    if (_trafficData.download.length > MAX_POINTS) {
      _trafficData.download.shift();
      _trafficData.upload.shift();
      _trafficData.labels.shift();
    }

    if (_trafficChart) {
      _trafficChart.data.labels = _trafficData.labels;
      _trafficChart.data.datasets[0].data = _trafficData.download;
      _trafficChart.data.datasets[1].data = _trafficData.upload;
      _trafficChart.update('none');
    }
  }

  // ----------------------------------------------------------------
  // LOAD PAGE
  // ----------------------------------------------------------------
  async function load() {
    initTrafficChart();
    await Promise.all([
      loadNetworkStatus(),
      loadRecentDevices(),
      loadRecentAlerts(),
      loadSecurityScore(),
    ]);
  }

  async function loadNetworkStatus() {
    try {
      const status = await API.networkStatus();
      safeText('stat-devices-online', `${status.devices_online} / ${status.devices_total}`);
      App.updateBadge('badge-unknown', status.devices_unknown > 0 ? status.devices_unknown : '0');
    } catch (_) {}
  }

  async function loadSecurityScore() {
    try {
      const overview = await API.getSecurityOverview();
      safeText('stat-security-score', `${overview.security_score}%`);
    } catch (_) {}
  }

  async function loadRecentDevices() {
    const container = document.getElementById('recent-devices-list');
    if (!container) return;

    try {
      const devices = await API.listDevices('?online_only=false');
      const recent = devices.slice(0, 6);

      if (recent.length === 0) {
        container.innerHTML = '<div class="text-small text-muted" style="text-align:center;padding:16px">Nenhum dispositivo encontrado</div>';
        return;
      }

      container.innerHTML = recent.map(d => `
        <div class="flex items-center gap-12" style="padding:8px 0;border-bottom:1px solid var(--border-color)">
          <span class="online-dot ${d.is_online ? 'dot-online' : 'dot-offline'}"></span>
          <span style="font-size:1.1rem">${App.deviceTypeIcon(d.device_type)}</span>
          <div style="flex:1;min-width:0">
            <div class="text-small truncate">${d.hostname || d.ip_address || d.mac_address}</div>
            <div class="text-small text-muted">${d.ip_address || d.mac_address}</div>
          </div>
          ${d.is_authorized ? '<span class="badge badge-authorized">✓</span>' : (d.is_known ? '' : '<span class="badge badge-unknown">Novo</span>')}
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<div class="text-small text-muted" style="text-align:center;padding:16px">Erro: ${err.message}</div>`;
    }
  }

  async function loadRecentAlerts() {
    const container = document.getElementById('recent-alerts-list');
    if (!container) return;

    try {
      const data = await API.getAlerts(5);
      const alerts = data.alerts || [];

      if (alerts.length === 0) {
        container.innerHTML = '<div class="text-small text-muted" style="text-align:center;padding:16px">✅ Nenhum alerta recente</div>';
        return;
      }

      const sevIcon = { info: 'ℹ️', warning: '⚠️', critical: '🚨' };
      container.innerHTML = alerts.map(a => `
        <div class="alert-item alert-${a.severity || 'info'}" style="padding:8px 10px;margin-bottom:6px">
          <span class="alert-icon">${sevIcon[a.severity] || 'ℹ️'}</span>
          <div>
            <div class="alert-title">${a.title}</div>
            <div class="alert-msg">${a.message}</div>
            <div class="alert-time">${App.formatDateTime(a.created_at)}</div>
          </div>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<div class="text-small text-muted" style="text-align:center;padding:16px">Erro: ${err.message}</div>`;
    }
  }

  function safeText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function safeStyle(id, prop, val) {
    const el = document.getElementById(id);
    if (el) el.style[prop] = val;
  }

  return { load, updateStats, loadRecentDevices };

})();
