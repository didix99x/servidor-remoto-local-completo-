/**
 * API client — centralized fetch wrapper with auth token handling.
 */
const API = (() => {
  const BASE = '/api';
  let _token = null;

  function setToken(t) { _token = t; }
  function getToken()  { return _token; }
  function clearToken() { _token = null; }

  async function request(method, path, body = null, opts = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (_token) headers['Authorization'] = `Bearer ${_token}`;

    const config = { method, headers, ...opts };
    if (body && !(body instanceof FormData)) {
      config.body = JSON.stringify(body);
    } else if (body instanceof FormData) {
      delete headers['Content-Type'];
      config.body = body;
    }

    const res = await fetch(`${BASE}${path}`, config);

    if (res.status === 401) {
      clearToken();
      localStorage.removeItem('hncc_token');
      if (window.App) App.showLogin();
      throw new Error('Sessão expirada. Faça login novamente.');
    }

    if (!res.ok) {
      let msg = `Erro ${res.status}`;
      try { const d = await res.json(); msg = d.detail || msg; } catch (_) {}
      throw new Error(msg);
    }

    // Some endpoints return no body (204)
    if (res.status === 204) return null;

    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) return res.json();
    return res;
  }

  return {
    setToken, getToken, clearToken,
    get:    (p, opts) => request('GET',    p, null, opts),
    post:   (p, b)    => request('POST',   p, b),
    put:    (p, b)    => request('PUT',    p, b),
    delete: (p)       => request('DELETE', p),

    // Auth
    login: (username, password, rememberMe = false) =>
      request('POST', '/auth/login', { username, password, remember_me: rememberMe }),

    // System
    sysInfo: () => request('GET', '/system/info'),

    // Network
    networkStatus: () => request('GET', '/network/status'),
    listDevices: (params = '') => request('GET', `/network/devices${params}`),
    getDevice: (id) => request('GET', `/network/devices/${id}`),
    updateDevice: (id, body) => request('PUT', `/network/devices/${id}`, body),
    deleteDevice: (id) => request('DELETE', `/network/devices/${id}`),
    deviceHistory: (id, limit=30) => request('GET', `/network/devices/${id}/history?limit=${limit}`),
    networkMap: () => request('GET', '/network/map'),
    triggerScan: () => request('POST', '/network/scan', {}),
    localIP: () => request('GET', '/network/local-ip'),

    // Files
    listShares: () => request('GET', '/files/shares'),
    createShare: (body) => request('POST', '/files/shares', body),
    deleteShare: (id) => request('DELETE', `/files/shares/${id}`),
    listShareContents: (id, path='') => request('GET', `/files/shares/${id}/contents?path=${encodeURIComponent(path)}`),
    uploadFile: (shareId, formData) => request('POST', `/files/shares/${shareId}/upload`, formData),
    downloadFile: (shareId, path) => `${BASE}/files/shares/${shareId}/download?path=${encodeURIComponent(path)}&token=${_token}`,
    deleteFile: (shareId, path) => request('DELETE', `/files/shares/${shareId}/delete?path=${encodeURIComponent(path)}`),
    renameFile: (shareId, path, newName) => request('POST', `/files/shares/${shareId}/rename?path=${encodeURIComponent(path)}&new_name=${encodeURIComponent(newName)}`),
    grantPermission: (shareId, body) => request('POST', `/files/shares/${shareId}/permissions`, body),
    revokePermission: (shareId, deviceId) => request('DELETE', `/files/shares/${shareId}/permissions/${deviceId}`),
    diskUsage: () => request('GET', '/files/disk-usage'),

    // Media
    mediaLibrary: () => request('GET', '/media/library'),
    streamUrl: (shareId, path) => `${BASE}/media/stream?share_id=${shareId}&path=${encodeURIComponent(path)}&token=${_token}`,
    thumbnailUrl: (shareId, path) => `${BASE}/media/thumbnail?share_id=${shareId}&path=${encodeURIComponent(path)}&token=${_token}`,

    // Devices
    listPairingRequests: (status='') => request('GET', `/devices/pairing/requests${status ? '?status_filter='+status : ''}`),
    respondPairing: (id, action, notes='') => request('POST', `/devices/pairing/requests/${id}/action`, { action, notes }),
    authorizeDevice: (id) => request('POST', `/devices/${id}/authorize`),
    revokeDevice: (id) => request('POST', `/devices/${id}/revoke`),
    blockDevice: (id) => request('POST', `/devices/${id}/block`),

    // Security
    getAlerts: (limit=50) => request('GET', `/security/alerts?limit=${limit}`),
    getAuditLogs: (limit=100) => request('GET', `/security/audit-logs?limit=${limit}`),
    getSecurityOverview: () => request('GET', '/security/overview'),
    getEvents: (hours=24) => request('GET', `/security/events?hours=${hours}`),
    scanPorts: (deviceId) => request('POST', `/security/scan-ports/${deviceId}`),

    // Auth management
    listUsers: () => request('GET', '/auth/users'),
    createUser: (body) => request('POST', '/auth/users', body),
    updateUser: (id, body) => request('PUT', `/auth/users/${id}`, body),
    deleteUser: (id) => request('DELETE', `/auth/users/${id}`),
    changePassword: (cur, nw) => request('PUT', '/auth/me/password', { current_password: cur, new_password: nw }),
    getMe: () => request('GET', '/auth/me'),

    // Computing / Central de Computação
    computingStatus: () => request('GET', '/computing/status'),
    sunshineConfig: () => request('GET', '/computing/sunshine/config'),
    updateSunshineConfig: (body) => request('PUT', '/computing/sunshine/config', body),
    startSunshine: () => request('POST', '/computing/sunshine/start', {}),
    stopSunshine: () => request('POST', '/computing/sunshine/stop', {}),
    discoveredApps: () => request('GET', '/computing/apps'),
    qualityProfiles: () => request('GET', '/computing/quality-profiles'),
    generateStreamUrl: (body) => request('POST', '/computing/stream-url', body),
  };
})();
