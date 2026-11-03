/**
 * Media center page controller.
 */
const Media = (() => {

  let _library = null;
  let _currentTab = 'movies';
  let _filtered = { movies: [], series: [], music: [] };

  // ----------------------------------------------------------------
  // LOAD LIBRARY
  // ----------------------------------------------------------------
  async function loadLibrary() {
    showLoading();
    try {
      _library = await API.mediaLibrary();
      _filtered = {
        movies: _library.movies || [],
        series: _library.series || [],
        music: _library.music || [],
      };
      updateCounts();
      renderCurrentTab();
    } catch (err) {
      App.showToast('error', `Erro ao carregar mídia: ${err.message}`);
      document.getElementById('media-empty').style.display = 'block';
    }
  }

  function showLoading() {
    ['movies', 'series', 'music'].forEach(t => {
      const el = document.getElementById(`media-${t}`);
      if (el) el.innerHTML = '<div style="text-align:center;padding:32px"><div class="loading-spinner"></div></div>';
    });
  }

  function updateCounts() {
    if (!_library) return;
    document.getElementById('movies-count').textContent = (_library.movies || []).length;
    document.getElementById('series-count').textContent = (_library.series || []).length;
    document.getElementById('music-count').textContent  = (_library.music || []).length;
  }

  // ----------------------------------------------------------------
  // TABS
  // ----------------------------------------------------------------
  function switchTab(tab, el) {
    _currentTab = tab;
    document.querySelectorAll('#page-media .tab').forEach(t => t.classList.remove('active'));
    if (el) el.classList.add('active');

    document.getElementById('media-movies').style.display = tab === 'movies' ? 'grid' : 'none';
    document.getElementById('media-series').style.display = tab === 'series' ? 'grid' : 'none';
    document.getElementById('media-music').style.display  = tab === 'music'  ? 'block' : 'none';

    renderCurrentTab();
  }

  function renderCurrentTab() {
    if (_currentTab === 'movies') renderVideoGrid('media-movies', _filtered.movies);
    else if (_currentTab === 'series') renderVideoGrid('media-series', _filtered.series);
    else if (_currentTab === 'music') renderMusicList('media-music', _filtered.music);

    const empty = document.getElementById('media-empty');
    const current = _filtered[_currentTab] || [];
    if (empty) empty.style.display = current.length === 0 ? 'block' : 'none';
  }

  // ----------------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------------
  function renderVideoGrid(containerId, items) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!items || items.length === 0) {
      container.innerHTML = '';
      return;
    }

    container.innerHTML = items.map(item => `
      <div class="media-card" onclick="Media.playMedia(${JSON.stringify(JSON.stringify(item)).slice(1,-1)})">
        <div class="media-thumb">
          <img src="${item.thumbnail_url}" alt="${item.name}" loading="lazy"
            onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
            style="display:block" />
          <div style="display:none;align-items:center;justify-content:center;width:100%;height:100%;font-size:2.5rem">🎬</div>
          <div class="media-play-overlay">
            <div class="media-play-btn">
              <svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            </div>
          </div>
        </div>
        <div class="media-info">
          <div class="media-title" title="${item.name}">${item.name}</div>
          <div class="media-meta">${App.formatBytes(item.size)}</div>
        </div>
      </div>
    `).join('');
  }

  function renderMusicList(containerId, items) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!items || items.length === 0) {
      container.innerHTML = '';
      return;
    }

    container.innerHTML = `
      <div class="card">
        <table class="data-table">
          <thead><tr><th></th><th>Nome</th><th>Tamanho</th><th>Ações</th></tr></thead>
          <tbody>
            ${items.map(item => `
              <tr>
                <td>🎵</td>
                <td>
                  <div style="font-weight:500">${item.name}</div>
                  <div class="text-small text-muted">${item.share_name}</div>
                </td>
                <td class="text-small text-muted">${App.formatBytes(item.size)}</td>
                <td>
                  <button class="btn btn-secondary" style="padding:4px 12px;font-size:0.8rem"
                    onclick="Media.playAudio(${item.share_id}, '${escJs(item.path)}', '${escJs(item.name)}')">
                    ▶ Reproduzir
                  </button>
                </td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  }

  // ----------------------------------------------------------------
  // PLAYBACK
  // ----------------------------------------------------------------
  function playMedia(itemJson) {
    const item = typeof itemJson === 'string' ? JSON.parse(itemJson) : itemJson;
    const url = API.streamUrl(item.share_id, item.path);
    openVideoPlayer(url, item.name);
  }

  function playAudio(shareId, path, name) {
    const url = API.streamUrl(shareId, path);
    // Use audio tag for audio files
    const existing = document.getElementById('audio-player');
    if (existing) existing.remove();

    const audio = document.createElement('audio');
    audio.id = 'audio-player';
    audio.controls = true;
    audio.autoplay = true;
    audio.src = url;
    audio.style.cssText = 'position:fixed;bottom:0;left:0;right:0;width:100%;z-index:999;background:#111827;height:50px';

    document.body.appendChild(audio);
    App.showToast('info', `🎵 Reproduzindo: ${name}`);
  }

  function openVideoPlayer(url, title) {
    const container = document.getElementById('video-player-container');
    const player = document.getElementById('video-player');
    const titleEl = document.getElementById('player-title');

    if (!container || !player) return;

    titleEl.textContent = title;
    player.src = url;
    container.classList.add('active');
    player.play().catch(() => {});
  }

  function closePlayer() {
    const container = document.getElementById('video-player-container');
    const player = document.getElementById('video-player');
    if (player) { player.pause(); player.src = ''; }
    if (container) container.classList.remove('active');
  }

  // ----------------------------------------------------------------
  // FILTER
  // ----------------------------------------------------------------
  function filter() {
    if (!_library) return;
    const query = (document.getElementById('media-search')?.value || '').toLowerCase();

    _filtered = {
      movies: (_library.movies || []).filter(m => !query || m.name.toLowerCase().includes(query)),
      series: (_library.series || []).filter(s => !query || s.name.toLowerCase().includes(query)),
      music:  (_library.music  || []).filter(m => !query || m.name.toLowerCase().includes(query)),
    };

    updateCounts();
    renderCurrentTab();
  }

  function escJs(str) {
    return (str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  }

  // ----------------------------------------------------------------
  // KEYBOARD SHORTCUT (ESC closes player)
  // ----------------------------------------------------------------
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePlayer();
  });

  return { loadLibrary, switchTab, filter, playMedia, playAudio, closePlayer };

})();
