/**
 * Computing module — Central de Computação / Game Streaming
 */
const Computing = (() => {
  let _currentTab = 'dashboard';
  let _qualityProfiles = [];
  let _discoveredApps = [];
  let _sunshineConfig = null;
  let _streamingSessions = [];

  // ----------------------------------------------------------------
  // INIT / LOAD
  // ----------------------------------------------------------------
  async function load() {
    try {
      // Load quality profiles first (needed for stream URL generation)
      await loadQualityProfiles();

      // Load dashboard data
      await loadDashboard();

      // Load apps
      await loadApps();

      // Load sunshine config
      await loadSunshineConfig();

      // Load sessions
      await loadSessions();

    } catch (err) {
      App.showToast('error', `Erro ao carregar Central de Computação: ${err.message}`);
    }
  }

  async function loadDashboard() {
    try {
      const status = await API.computingStatus();
      renderDashboard(status);
    } catch (err) {
      console.error('Failed to load computing status:', err);
    }
  }

  async function loadQualityProfiles() {
    try {
      const data = await API.qualityProfiles();
      _qualityProfiles = data.profiles || [];
    } catch (err) {
      console.error('Failed to load quality profiles:', err);
    }
  }

  async function loadApps() {
    try {
      const apps = await API.discoveredApps();
      _discoveredApps = apps || [];
      renderAppsList();
    } catch (err) {
      console.error('Failed to load apps:', err);
    }
  }

  async function loadSunshineConfig() {
    try {
      _sunshineConfig = await API.sunshineConfig();
      renderSunshineConfig();
    } catch (err) {
      // Config might not exist yet (404)
      _sunshineConfig = null;
      renderSunshineConfig();
    }
  }

  async function loadSessions() {
    try {
      // For now, we'll use the status endpoint which includes active sessions
      // In the future, we might have a dedicated sessions endpoint
      const status = await API.computingStatus();
      _streamingSessions = [];
      if (status.sunshine_status && status.sunshine_status.active_sessions > 0) {
        // Placeholder - would need a dedicated sessions endpoint
        _streamingSessions = [{ count: status.sunshine_status.active_sessions }];
      }
      renderSessions();
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }

  // ----------------------------------------------------------------
  // RENDER FUNCTIONS
  // ----------------------------------------------------------------
  function renderDashboard(status) {
    // System info
    document.getElementById('comp-cpu').textContent = `${status.cpu_percent.toFixed(1)}%`;
    document.getElementById('comp-cpu-bar').style.width = `${status.cpu_percent}%`;
    document.getElementById('comp-ram').textContent = `${status.memory_percent.toFixed(1)}%`;
    document.getElementById('comp-ram-bar').style.width = `${status.memory_percent}%`;
    document.getElementById('comp-ram-detail').textContent = `${status.memory_used_gb.toFixed(1)} / ${status.memory_total_gb.toFixed(1)} GB`;
    document.getElementById('comp-disk').textContent = `${status.disk_percent.toFixed(1)}%`;
    document.getElementById('comp-disk-bar').style.width = `${status.disk_percent}%`;
    document.getElementById('comp-disk-detail').textContent = `${status.disk_used_gb.toFixed(1)} / ${status.disk_total_gb.toFixed(1)} GB`;

    // GPU info
    const gpuContainer = document.getElementById('comp-gpu-list');
    if (status.gpus && status.gpus.length > 0) {
      gpuContainer.innerHTML = status.gpus.map(gpu => `
        <div class="gpu-item">
          <div class="gpu-name">${gpu.name}</div>
          <div class="gpu-details">
            <span class="gpu-vram">${gpu.memory_used ? `${gpu.memory_used}/${gpu.memory_total} MB` : 'N/A'}</span>
            <span class="gpu-encoder">${getEncoderBadge(gpu.encoder || 'unknown')}</span>
          </div>
        </div>
      `).join('');
    } else {
      gpuContainer.innerHTML = '<div class="text-small text-muted">Nenhuma GPU detectada</div>';
    }

    // Recommended encoder
    document.getElementById('comp-recommended-encoder').textContent = status.recommended_encoder || 'nvenc';

    // Sunshine status
    const sunshine = status.sunshine_status || {};
    const isRunning = sunshine.is_running || false;
    document.getElementById('comp-sunshine-status').innerHTML = `
      <span class="status-badge ${isRunning ? 'running' : 'stopped'}">
        <span class="status-dot ${isRunning ? '' : 'offline'}"></span>
        ${isRunning ? 'Rodando' : 'Parado'}
      </span>
    `;
    document.getElementById('comp-sunshine-version').textContent = sunshine.version || '—';
    document.getElementById('comp-sunshine-uptime').textContent = sunshine.uptime_seconds ? formatUptime(sunshine.uptime_seconds) : '—';
    document.getElementById('comp-active-sessions').textContent = sunshine.active_sessions || 0;
    document.getElementById('comp-max-sessions').textContent = sunshine.max_sessions || 0;

    // Update buttons
    const startBtn = document.getElementById('comp-start-sunshine');
    const stopBtn = document.getElementById('comp-stop-sunshine');
    if (startBtn && stopBtn) {
      startBtn.disabled = isRunning;
      stopBtn.disabled = !isRunning;
    }
  }

  function renderSunshineConfig() {
    const container = document.getElementById('comp-config-form');
    if (!_sunshineConfig) {
      container.innerHTML = `
        <div class="config-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48" style="margin:0 auto 16px;display:block;opacity:0.3"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <p>Nenhuma configuração do Sunshine encontrada.</p>
          <button class="btn btn-primary" onclick="Computing.createSunshineConfig()">Criar Configuração</button>
        </div>
      `;
      return;
    }

    const c = _sunshineConfig;
    container.innerHTML = `
      <form id="sunshine-config-form" onsubmit="Computing.saveSunshineConfig(event)">
        <div class="form-row">
          <div class="form-group">
            <label>Host</label>
            <input type="text" class="form-control" name="host" value="${c.host}" />
          </div>
          <div class="form-group">
            <label>Porta Stream</label>
            <input type="number" class="form-control" name="port" value="${c.port}" min="1" max="65535" />
          </div>
          <div class="form-group">
            <label>Porta Web UI</label>
            <input type="number" class="form-control" name="web_port" value="${c.web_port}" min="1" max="65535" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Usuário</label>
            <input type="text" class="form-control" name="username" value="${c.username}" />
          </div>
          <div class="form-group">
            <label>Senha (deixe vazio para não alterar)</label>
            <input type="password" class="form-control" name="password" placeholder="••••••••" autocomplete="new-password" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Video Encoder</label>
            <select class="form-control" name="video_encoder">
              <option value="nvenc" ${c.video_encoder === 'nvenc' ? 'selected' : ''}>NVENC (NVIDIA)</option>
              <option value="amf" ${c.video_encoder === 'amf' ? 'selected' : ''}>AMF (AMD)</option>
              <option value="qsv" ${c.video_encoder === 'qsv' ? 'selected' : ''}>QSV (Intel)</option>
              <option value="vaapi" ${c.video_encoder === 'vaapi' ? 'selected' : ''}>VAAPI (Linux)</option>
              <option value="software" ${c.video_encoder === 'software' ? 'selected' : ''}>Software (CPU)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Audio Encoder</label>
            <input type="text" class="form-control" name="audio_encoder" value="${c.audio_encoder}" />
          </div>
          <div class="form-group">
            <label>Max Bitrate (kbps)</label>
            <input type="number" class="form-control" name="max_bitrate" value="${c.max_bitrate}" min="1000" max="200000" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Max FPS</label>
            <input type="number" class="form-control" name="max_fps" value="${c.max_fps}" min="1" max="240" />
          </div>
          <div class="form-group">
            <label>Resolução</label>
            <input type="text" class="form-control" name="resolution" value="${c.resolution}" placeholder="1920x1080" />
          </div>
          <div class="form-group">
            <label>GPU Device ID (opcional)</label>
            <input type="text" class="form-control" name="gpu_device_id" value="${c.gpu_device_id || ''}" placeholder="Auto" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" name="is_enabled" ${c.is_enabled ? 'checked' : ''} />
              <span>Habilitado</span>
            </label>
          </div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" name="auto_start" ${c.auto_start ? 'checked' : ''} />
              <span>Auto-iniciar com o servidor</span>
            </label>
          </div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" name="enable_hevc" ${c.enable_hevc ? 'checked' : ''} />
              <span>Habilitar HEVC (H.265)</span>
            </label>
          </div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" name="enable_av1" ${c.enable_av1 ? 'checked' : ''} />
              <span>Habilitar AV1</span>
            </label>
          </div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:20px">
          <button type="button" class="btn btn-secondary" onclick="Computing.testConnection()">Testar Conexão</button>
          <button type="submit" class="btn btn-primary">Salvar Configuração</button>
        </div>
      </form>
    `;
  }

  function renderAppsList() {
    const container = document.getElementById('comp-apps-list');
    if (!_discoveredApps || _discoveredApps.length === 0) {
      container.innerHTML = `
        <div class="text-center" style="padding:40px;color:var(--text-muted)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48" style="margin:0 auto 16px;display:block;opacity:0.4"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          <p>Nenhum aplicativo descoberto.</p>
          <p class="text-small">Inicie o Sunshine para descobrir jogos e aplicativos.</p>
          <button class="btn btn-secondary" style="margin-top:16px" onclick="Computing.refreshApps()">Atualizar</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="apps-grid">
        ${_discoveredApps.map(app => `
          <div class="app-card" data-app-id="${app.id}">
            <div class="app-icon">
              ${app.sunshine_image_url ?
                `<img src="${app.sunshine_image_url}" alt="${app.name}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" />` :
                ''}
              <div class="app-icon-placeholder" style="${app.sunshine_image_url ? 'display:none' : ''}">${getAppTypeIcon(app.app_type)}</div>
            </div>
            <div class="app-info">
              <div class="app-name">${app.name}</div>
              <div class="app-meta">
                <span class="app-type-badge ${app.app_type || ''}">${app.app_type || 'Desconhecido'}</span>
                ${app.publisher ? `<span class="app-publisher">${app.publisher}</span>` : ''}
              </div>
            </div>
            <div class="app-actions">
              <button class="btn btn-primary btn-sm" onclick="Computing.launchApp('${app.id}', 'app')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Iniciar
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderSessions() {
    const container = document.getElementById('comp-sessions-list');
    if (!_streamingSessions || _streamingSessions.length === 0) {
      container.innerHTML = `
        <div class="text-center" style="padding:40px;color:var(--text-muted)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48" style="margin:0 auto 16px;display:block;opacity:0.4"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <p>Nenhuma sessão ativa.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="sessions-list">
        ${_streamingSessions.map(session => `
          <div class="session-item">
            <div class="session-info">
              <div class="session-type">${session.session_type || 'Desktop'}</div>
              <div class="session-details">${session.client_ip || 'Local'} • ${formatBytes(session.bitrate || 0)}/s • ${session.resolution || '1920x1080'} @ ${session.fps || 60}fps</div>
            </div>
            <div class="session-status active">Ativa</div>
            <button class="btn btn-danger btn-sm" onclick="Computing.endSession('${session.id}')">Encerrar</button>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderQualityProfiles() {
    const container = document.getElementById('comp-quality-list');
    container.innerHTML = `
      <div class="quality-profiles-grid">
        ${_qualityProfiles.map(profile => `
          <div class="quality-profile-card">
            <div class="quality-header">
              <div class="quality-name">${profile.label}</div>
              <div class="quality-codec">${profile.codec.toUpperCase()}</div>
            </div>
            <div class="quality-specs">
              <div class="quality-spec"><span class="spec-label">Resolução</span><span class="spec-value">${profile.resolution}</span></div>
              <div class="quality-spec"><span class="spec-label">FPS</span><span class="spec-value">${profile.fps}</span></div>
              <div class="quality-spec"><span class="spec-label">Bitrate</span><span class="spec-value">${(profile.bitrate_kbps / 1000).toFixed(0)} Mbps</span></div>
            </div>
            <div class="quality-desc">${profile.description}</div>
            <button class="btn btn-primary btn-sm quality-use" onclick="Computing.generateStreamUrl('${profile.name}')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="5 3 19 12 5 21 5 3"/></svg>
              Gerar Link
            </button>
          </div>
        `).join('')}
      </div>
    `;
  }

  // ----------------------------------------------------------------
  // ACTIONS
  // ----------------------------------------------------------------
  async function switchTab(tab, element) {
    _currentTab = tab;

    // Update tab buttons
    document.querySelectorAll('#comp-tabs .tab').forEach(t => t.classList.remove('active'));
    if (element) element.classList.add('active');

    // Hide all panels
    document.querySelectorAll('.comp-panel').forEach(p => p.style.display = 'none');

    // Show target panel
    const panel = document.getElementById(`comp-panel-${tab}`);
    if (panel) panel.style.display = 'block';

    // Load data if needed
    switch (tab) {
      case 'apps':
        if (_discoveredApps.length === 0) await loadApps();
        break;
      case 'config':
        if (!_sunshineConfig) await loadSunshineConfig();
        break;
      case 'sessions':
        await loadSessions();
        break;
      case 'quality':
        renderQualityProfiles();
        break;
    }
  }

  async function createSunshineConfig() {
    try {
      App.showToast('info', 'Criando configuração padrão...');
      const config = {
        host: '0.0.0.0',
        port: 47989,
        web_port: 47990,
        username: 'admin',
        password: 'admin123', // Will need to be changed
        is_enabled: true,
        auto_start: false,
        video_encoder: 'nvenc',
        audio_encoder: 'opus',
        max_bitrate: 50000,
        max_fps: 60,
        resolution: '1920x1080',
        enable_hevc: true,
        enable_av1: false,
      };
      _sunshineConfig = await API.updateSunshineConfig(config);
      renderSunshineConfig();
      App.showToast('success', 'Configuração criada! Altere a senha padrão.');
    } catch (err) {
      App.showToast('error', `Erro ao criar configuração: ${err.message}`);
    }
  }

  async function saveSunshineConfig(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const config = {
      host: formData.get('host'),
      port: parseInt(formData.get('port')),
      web_port: parseInt(formData.get('web_port')),
      username: formData.get('username'),
      video_encoder: formData.get('video_encoder'),
      audio_encoder: formData.get('audio_encoder'),
      max_bitrate: parseInt(formData.get('max_bitrate')),
      max_fps: parseInt(formData.get('max_fps')),
      resolution: formData.get('resolution'),
      gpu_device_id: formData.get('gpu_device_id') || null,
      is_enabled: formData.has('is_enabled'),
      auto_start: formData.has('auto_start'),
      enable_hevc: formData.has('enable_hevc'),
      enable_av1: formData.has('enable_av1'),
    };

    const password = formData.get('password');
    if (password) config.password = password;

    try {
      App.showToast('info', 'Salvando configuração...');
      _sunshineConfig = await API.updateSunshineConfig(config);
      renderSunshineConfig();
      App.showToast('success', 'Configuração salva com sucesso!');
    } catch (err) {
      App.showToast('error', `Erro ao salvar: ${err.message}`);
    }
  }

  async function startSunshine() {
    try {
      const btn = document.getElementById('comp-start-sunshine');
      btn.disabled = true;
      btn.textContent = 'Iniciando...';

      await API.startSunshine();
      App.showToast('success', 'Sunshine iniciado!');
      await loadDashboard();
    } catch (err) {
      App.showToast('error', `Erro ao iniciar: ${err.message}`);
      await loadDashboard();
    }
  }

  async function stopSunshine() {
    try {
      const btn = document.getElementById('comp-stop-sunshine');
      btn.disabled = true;
      btn.textContent = 'Parando...';

      await API.stopSunshine();
      App.showToast('success', 'Sunshine parado!');
      await loadDashboard();
    } catch (err) {
      App.showToast('error', `Erro ao parar: ${err.message}`);
      await loadDashboard();
    }
  }

  async function refreshApps() {
    App.showToast('info', 'Atualizando lista de aplicativos...');
    await loadApps();
    App.showToast('success', 'Lista atualizada!');
  }

  async function launchApp(appId, sessionType) {
    try {
      App.showToast('info', 'Iniciando aplicativo...');
      // Generate stream URL for the app
      const streamData = await API.generateStreamUrl({
        session_type: sessionType,
        quality: 'balanced',
        app_id: appId,
      });

      // Show the stream URL modal
      showStreamUrlModal(streamData);
    } catch (err) {
      App.showToast('error', `Erro ao iniciar: ${err.message}`);
    }
  }

  async function generateStreamUrl(qualityName) {
    try {
      App.showToast('info', 'Gerando link de streaming...');
      const streamData = await API.generateStreamUrl({
        session_type: 'desktop',
        quality: qualityName,
      });
      showStreamUrlModal(streamData);
    } catch (err) {
      App.showToast('error', `Erro ao gerar link: ${err.message}`);
    }
  }

  function showStreamUrlModal(data) {
    const modalHtml = `
      <div class="modal-overlay" id="stream-url-modal">
        <div class="modal modal-lg">
          <div class="modal-header">
            <div class="modal-title">Link de Streaming Gerado</div>
            <button class="modal-close" onclick="closeStreamUrlModal()">✕</button>
          </div>
          <div style="padding:20px">
            <div class="stream-url-section">
              <h4>Moonlight (Recomendado)</h4>
              <div class="url-input-group">
                <input type="text" class="form-control" id="moonlight-url" value="${data.moonlight_url}" readonly />
                <button class="btn btn-secondary" onclick="copyToClipboard('moonlight-url')">Copiar</button>
              </div>
              <p class="text-small text-muted">Abra no app Moonlight (Android/iOS/PC) ou digite no navegador</p>
            </div>
            <div class="stream-url-section">
              <h4>Sunshine</h4>
              <div class="url-input-group">
                <input type="text" class="form-control" id="sunshine-url" value="${data.sunshine_url}" readonly />
                <button class="btn btn-secondary" onclick="copyToClipboard('sunshine-url')">Copiar</button>
              </div>
              <p class="text-small text-muted">Para clientes compatíveis com protocolo Sunshine</p>
            </div>
            <div class="stream-url-section">
              <h4>QR Code (Moonlight)</h4>
              <div style="text-align:center;margin:16px 0">
                <img src="data:image/png;base64,${data.qr_code_base64}" alt="QR Code" style="max-width:256px;border-radius:8px;background:white;padding:8px" />
              </div>
              <p class="text-small text-muted">Escaneie com o app Moonlight no celular/TV</p>
            </div>
            <div class="stream-url-section">
              <h4>Informações da Conexão</h4>
              <div class="grid grid-2">
                <div><strong>Host:</strong> ${data.connection_info.host}</div>
                <div><strong>Porta:</strong> ${data.connection_info.port}</div>
                <div><strong>Qualidade:</strong> ${data.connection_info.quality_profile}</div>
                <div><strong>Resolução:</strong> ${data.connection_info.resolution}</div>
                <div><strong>FPS:</strong> ${data.connection_info.fps}</div>
                <div><strong>Bitrate:</strong> ${data.connection_info.bitrate_kbps} kbps</div>
                <div><strong>Codec:</strong> ${data.connection_info.codec}</div>
              </div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:20px">
              <button class="btn btn-primary" onclick="closeStreamUrlModal()">Fechar</button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Remove existing modal if any
    const existing = document.getElementById('stream-url-modal');
    if (existing) existing.remove();

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('stream-url-modal').style.display = 'flex';
  }

  function closeStreamUrlModal() {
    const modal = document.getElementById('stream-url-modal');
    if (modal) modal.remove();
  }

  async function testConnection() {
    App.showToast('info', 'Testando conexão com Sunshine...');
    try {
      const status = await API.computingStatus();
      if (status.sunshine_status && status.sunshine_status.is_running) {
        App.showToast('success', 'Sunshine está rodando e acessível!');
      } else {
        App.showToast('warning', 'Sunshine não está rodando. Inicie-o para testar.');
      }
    } catch (err) {
      App.showToast('error', `Erro no teste: ${err.message}`);
    }
  }

  async function endSession(sessionId) {
    if (!confirm('Encerrar esta sessão de streaming?')) return;
    App.showToast('info', 'Encerrando sessão...');
    // Would need a dedicated endpoint for this
    App.showToast('warning', 'Funcionalidade de encerrar sessão em desenvolvimento');
  }

  // ----------------------------------------------------------------
  // UTILS
  // ----------------------------------------------------------------
  function getEncoderBadge(encoder) {
    const badges = {
      nvenc: '<span class="badge badge-nvenc">NVENC</span>',
      amf: '<span class="badge badge-amf">AMF</span>',
      qsv: '<span class="badge badge-qsv">QSV</span>',
      vaapi: '<span class="badge badge-vaapi">VAAPI</span>',
      software: '<span class="badge badge-software">Software</span>',
    };
    return badges[encoder.toLowerCase()] || `<span class="badge">${encoder}</span>`;
  }

  function getAppTypeIcon(type) {
    const icons = {
      game: '🎮',
      browser: '🌐',
      utility: '🔧',
      system: '⚙️',
    };
    return icons[type] || '📱';
  }

  function formatUptime(seconds) {
    if (!seconds) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
  }

  function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
      el.select();
      document.execCommand('copy');
      App.showToast('success', 'Copiado para a área de transferência!');
    }
  }

  // ----------------------------------------------------------------
  // PUBLIC API
  // ----------------------------------------------------------------
  return {
    load,
    switchTab,
    createSunshineConfig,
    saveSunshineConfig,
    startSunshine,
    stopSunshine,
    refreshApps,
    launchApp,
    generateStreamUrl,
    testConnection,
    closeStreamUrlModal,
  };
})();