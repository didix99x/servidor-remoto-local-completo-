/**
 * Core App controller — navigation, WebSocket, toast, auth.
 */
const App = (() => {

  let _ws = null;
  let _wsReconnectTimer = null;
  let _currentPage = 'dashboard';
  let _currentUser = null;
  let _notifications = [];

  // ----------------------------------------------------------------
  // AUTH
  // ----------------------------------------------------------------
  async function init() {
    // Check stored token
    const token = localStorage.getItem('hncc_token');
    if (token) {
      API.setToken(token);
      try {
        const me = await API.getMe();
        _currentUser = me;
        showApp(me);
        return;
      } catch (_) {
        localStorage.removeItem('hncc_token');
      }
    }
    showLogin();
  }

  function showLogin() {
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('app').style.display = 'none';
  }

  function showApp(user) {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('app').style.display = 'flex';

    // Set user info
    document.getElementById('user-display-name').textContent = user.username;
    document.getElementById('user-display-role').textContent =
      user.role === 'admin' ? 'Administrador' : user.role === 'user' ? 'Usuário' : 'Visualizador';
    document.getElementById('user-avatar-initial').textContent = user.username[0].toUpperCase();

    // Connect WebSocket
    connectWS();

    // Load current page
    loadPage(_currentPage);
  }

  function logout() {
    API.clearToken();
    localStorage.removeItem('hncc_token');
    if (_ws) { _ws.close(); _ws = null; }
    showLogin();
  }

  // ----------------------------------------------------------------
  // LOGIN FORM
  // ----------------------------------------------------------------
  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    const errEl = document.getElementById('login-error');
    errEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Entrando...';

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const rememberMe = document.getElementById('login-remember')?.checked || false;

    try {
      const data = await API.login(username, password, rememberMe);
      API.setToken(data.access_token);
      localStorage.setItem('hncc_token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('hncc_refresh_token', data.refresh_token);
      }

      const me = await API.getMe();
      _currentUser = me;
      showApp(me);
    } catch (err) {
      errEl.textContent = err.message || 'Falha no login';
      errEl.style.display = 'block';
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg> Entrar`;
    }
  });

  // ----------------------------------------------------------------
  // NAVIGATION
  // ----------------------------------------------------------------
  function navigate(page) {
    _currentPage = page;
    loadPage(page);

    // Close mobile menu
    document.getElementById('sidebar').classList.remove('mobile-open');
    document.getElementById('mobile-overlay').classList.remove('active');
  }

  function loadPage(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    // Show target
    const el = document.getElementById(`page-${page}`);
    if (el) el.classList.add('active');

    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => {
      n.classList.toggle('active', n.dataset.page === page);
    });

    // Update title
    const titles = {
      dashboard: 'Dashboard', network: 'Monitor de Rede', files: 'Gerenciador de Arquivos',
      media: 'Media Center', devices: 'Gerenciador de Dispositivos',
      security: 'Central de Segurança', settings: 'Configurações',
      computing: 'Central de Computação',
    };
    document.getElementById('page-title').textContent = titles[page] || page;

    // Load page data
    switch (page) {
      case 'dashboard': Dashboard.load(); break;
      case 'network':   Network.load(); break;
      case 'files':     Files.load(); break;
      case 'media':     Media.loadLibrary(); break;
      case 'devices':   Devices.load(); break;
      case 'security':  Security.load(); break;
      case 'settings':  Settings.load(); break;
      case 'computing': Computing.load(); break;
    }

    // Close notifications dropdown
    document.getElementById('notifications-dropdown').classList.remove('active');
  }

  // Nav click events
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const page = item.dataset.page;
      if (page) navigate(page);
    });
  });

  // Logout
  document.getElementById('sidebar-user-btn').addEventListener('click', () => {
    if (confirm('Deseja sair?')) logout();
  });

  // Mobile menu
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const mobileOverlay = document.getElementById('mobile-overlay');

  mobileBtn.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('mobile-open');
    mobileOverlay.classList.toggle('active');
  });

  mobileOverlay.addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('mobile-open');
    mobileOverlay.classList.remove('active');
  });

  // Show mobile menu button on small screens
  function checkMobile() {
    mobileBtn.style.display = window.innerWidth <= 768 ? 'flex' : 'none';
  }
  window.addEventListener('resize', checkMobile);
  checkMobile();

  // ----------------------------------------------------------------
  // WEBSOCKET
  // ----------------------------------------------------------------
  function connectWS() {
    const token = API.getToken();
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${location.host}/ws?token=${token}`;

    _ws = new WebSocket(url);

    _ws.addEventListener('open', () => {
      setWSStatus(true);
    });

    _ws.addEventListener('close', () => {
      setWSStatus(false);
      _wsReconnectTimer = setTimeout(connectWS, 5000);
    });

    _ws.addEventListener('error', () => {
      setWSStatus(false);
    });

    _ws.addEventListener('message', (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleWSMessage(msg);
      } catch (_) {}
    });

    // Ping every 30s to keep alive
    setInterval(() => {
      if (_ws && _ws.readyState === WebSocket.OPEN) {
        _ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  function setWSStatus(connected) {
    const dot = document.getElementById('ws-status-dot');
    const text = document.getElementById('ws-status-text');
    dot.className = 'status-dot' + (connected ? '' : ' offline');
    text.textContent = connected ? 'Conectado' : 'Reconectando...';
  }

  function handleWSMessage(msg) {
    switch (msg.type) {
      case 'system_stats':
        Dashboard.updateStats(msg.data);
        break;

      case 'device_status':
        addNotification('info',
          msg.data.is_online ? '📡 Dispositivo online' : '📴 Dispositivo offline',
          `Dispositivo #${msg.data.device_id} ${msg.data.is_online ? 'ficou online' : 'saiu da rede'}`
        );
        if (_currentPage === 'network') Network.load();
        if (_currentPage === 'dashboard') Dashboard.loadRecentDevices();
        break;

      case 'device_discovered':
        addNotification('warning',
          '🔍 Novo dispositivo detectado',
          `${msg.data.hostname || msg.data.ip_address || msg.data.mac_address} foi encontrado na rede`
        );
        updateBadge('badge-unknown', '!');
        if (_currentPage === 'network') Network.load();
        break;

      case 'security_alert':
        addNotification(
          msg.data.severity === 'critical' ? 'error' : 'warning',
          '🛡️ ' + (msg.data.alert_type || 'Alerta'),
          msg.data.message
        );
        break;

      case 'scan_started':
        showToast('info', '🔍 Varredura de rede iniciada...');
        break;

      case 'scan_completed':
        showToast('success', `✅ Varredura concluída: ${msg.data.devices_found} dispositivos encontrados`);
        if (_currentPage === 'network') Network.load();
        break;
    }
  }

  // ----------------------------------------------------------------
  // NOTIFICATIONS
  // ----------------------------------------------------------------
  function addNotification(type, title, message) {
    const notif = { type, title, message, time: new Date() };
    _notifications.unshift(notif);
    if (_notifications.length > 50) _notifications.pop();

    const count = _notifications.length;
    const countEl = document.getElementById('notif-count');
    countEl.textContent = count;
    countEl.classList.toggle('hidden', count === 0);

    renderNotifications();
  }

  function renderNotifications() {
    const list = document.getElementById('notifications-list');
    if (_notifications.length === 0) {
      list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:0.85rem">Sem alertas</div>';
      return;
    }
    list.innerHTML = _notifications.slice(0, 20).map(n => `
      <div class="notif-item">
        <div class="notif-title">${n.title}</div>
        <div class="notif-msg">${n.message}</div>
        <div class="notif-time">${formatTime(n.time)}</div>
      </div>
    `).join('');
  }

  function clearNotifications() {
    _notifications = [];
    const countEl = document.getElementById('notif-count');
    countEl.textContent = '0';
    countEl.classList.add('hidden');
    renderNotifications();
  }

  document.getElementById('notifications-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    document.getElementById('notifications-dropdown').classList.toggle('active');
  });

  document.addEventListener('click', () => {
    document.getElementById('notifications-dropdown').classList.remove('active');
  });

  // ----------------------------------------------------------------
  // SCAN BUTTON
  // ----------------------------------------------------------------
  async function triggerScan() {
    const btn = document.getElementById('scan-btn');
    const btn2 = document.getElementById('scan-now-btn');
    try {
      btn.style.opacity = '0.5';
      if (btn2) btn2.disabled = true;
      await API.triggerScan();
      showToast('info', 'Varredura de rede iniciada...');
    } catch (err) {
      showToast('error', err.message);
    } finally {
      btn.style.opacity = '1';
      if (btn2) btn2.disabled = false;
    }
  }

  document.getElementById('scan-btn').addEventListener('click', triggerScan);

  // ----------------------------------------------------------------
  // BADGE UPDATES
  // ----------------------------------------------------------------
  function updateBadge(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    if (value && value !== '0') {
      el.textContent = value;
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  }

  // ----------------------------------------------------------------
  // TOAST
  // ----------------------------------------------------------------
  function showToast(type, message, duration = 4000) {
    const container = document.getElementById('toast-container');
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-out');
      setTimeout(() => toast.remove(), 400);
    }, duration);
  }

  // ----------------------------------------------------------------
  // UTILS (shared)
  // ----------------------------------------------------------------
  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
  }

  function formatTime(date) {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }

  function formatDateTime(date) {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleString('pt-BR');
  }

  function formatSpeed(bps) {
    if (bps < 1024) return `${bps.toFixed(0)} B/s`;
    if (bps < 1024 * 1024) return `${(bps / 1024).toFixed(1)} KB/s`;
    return `${(bps / (1024 * 1024)).toFixed(2)} MB/s`;
  }

  function deviceTypeIcon(type) {
    const icons = {
      computer: '🖥️', phone: '📱', tablet: '⬜', smart_tv: '📺',
      printer: '🖨️', router: '📡', nas: '💾', iot: '🔌',
      gaming: '🎮', unknown: '❓',
    };
    return icons[type] || '❓';
  }

  function deviceTypeLabel(type) {
    const labels = {
      computer: 'Computador', phone: 'Celular', tablet: 'Tablet',
      smart_tv: 'Smart TV', printer: 'Impressora', router: 'Roteador',
      nas: 'NAS', iot: 'IoT', gaming: 'Videogame', unknown: 'Desconhecido',
    };
    return labels[type] || type;
  }

  // ----------------------------------------------------------------
  // START
  // ----------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', init);

  return {
    navigate, showLogin, showApp, logout, triggerScan,
    showToast, addNotification, clearNotifications,
    updateBadge, formatBytes, formatTime, formatDateTime,
    formatSpeed, deviceTypeIcon, deviceTypeLabel,
    get currentUser() { return _currentUser; },
  };

})();
