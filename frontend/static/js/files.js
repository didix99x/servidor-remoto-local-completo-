/**
 * File sharing page controller.
 */
const Files = (() => {

  let _shares = [];
  let _selectedShare = null;
  let _currentPath = '';

  // ----------------------------------------------------------------
  // LOAD
  // ----------------------------------------------------------------
  async function load() {
    await loadShares();
    setupDragDrop();
  }

  async function loadShares() {
    const container = document.getElementById('shares-list');
    if (!container) return;

    try {
      _shares = await API.listShares();

      if (_shares.length === 0) {
        container.innerHTML = `
          <div style="text-align:center;padding:32px;color:var(--text-muted)">
            <div style="font-size:2.5rem;margin-bottom:12px">📁</div>
            <p>Nenhum compartilhamento criado.</p>
            <button class="btn btn-primary" style="margin-top:16px" onclick="Files.showNewShareModal()">Criar compartilhamento</button>
          </div>`;
        return;
      }

      container.innerHTML = _shares.map(share => `
        <div class="file-item ${_selectedShare?.id === share.id ? 'selected' : ''}" onclick="Files.selectShare(${share.id})">
          <span class="file-icon">📁</span>
          <div style="flex:1;min-width:0">
            <div class="file-name">${share.name}</div>
            <div class="text-small text-muted">${share.path}</div>
          </div>
          <div class="flex gap-8">
            <button class="icon-btn" title="Permissões" onclick="event.stopPropagation();Files.managePermissions(${share.id})">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </button>
            <button class="icon-btn" title="Excluir compartilhamento" style="color:var(--accent-red)" onclick="event.stopPropagation();Files.deleteShare(${share.id})">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            </button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  // ----------------------------------------------------------------
  // SHARE SELECTION / FILE BROWSER
  // ----------------------------------------------------------------
  async function selectShare(id) {
    _selectedShare = _shares.find(s => s.id === id);
    _currentPath = '';

    // Enable upload / new folder buttons
    const uploadBtn = document.getElementById('upload-btn');
    const newFolderBtn = document.getElementById('new-folder-btn');
    if (uploadBtn) uploadBtn.disabled = false;
    if (newFolderBtn) newFolderBtn.disabled = false;

    await loadShares(); // re-render to show selected
    await browseDirectory('');
  }

  async function browseDirectory(path) {
    if (!_selectedShare) return;
    _currentPath = path;

    const browser = document.getElementById('file-browser');
    const title = document.getElementById('file-browser-title');

    if (title) title.textContent = `📁 ${_selectedShare.name}`;
    browser.innerHTML = '<div style="text-align:center;padding:24px"><div class="loading-spinner"></div></div>';

    updateBreadcrumb(path);

    try {
      const contents = await API.listShareContents(_selectedShare.id, path);
      renderFileList(contents);
    } catch (err) {
      browser.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  function updateBreadcrumb(path) {
    const bc = document.getElementById('file-breadcrumb');
    if (!bc) return;
    bc.style.display = 'flex';

    const parts = path ? path.split('/').filter(Boolean) : [];
    const items = [
      `<span class="breadcrumb-item" onclick="Files.browseDirectory('')">📁 ${_selectedShare?.name}</span>`,
    ];

    let cumPath = '';
    parts.forEach((part, i) => {
      cumPath += (cumPath ? '/' : '') + part;
      const isLast = i === parts.length - 1;
      items.push('<span class="breadcrumb-sep"> / </span>');
      if (isLast) {
        items.push(`<span class="breadcrumb-current">${part}</span>`);
      } else {
        const cp = cumPath;
        items.push(`<span class="breadcrumb-item" onclick="Files.browseDirectory('${cp}')">${part}</span>`);
      }
    });

    bc.innerHTML = items.join('');
  }

  function renderFileList(contents) {
    const browser = document.getElementById('file-browser');
    const items = contents.items || [];

    if (items.length === 0) {
      browser.innerHTML = `
        <div style="text-align:center;padding:32px;color:var(--text-muted)">
          <div style="font-size:2rem;margin-bottom:8px">📂</div>
          <p class="text-small">Pasta vazia</p>
        </div>`;
      return;
    }

    browser.innerHTML = items.map(item => {
      const icon = item.is_dir ? '📁' : getFileIcon(item.name, item.mime_type);
      const size = item.is_dir ? '' : App.formatBytes(item.size);

      return `
        <div class="file-item" ondblclick="Files.onItemDblClick('${escJs(item.path)}', ${item.is_dir})">
          <span class="file-icon">${icon}</span>
          <span class="file-name" title="${item.name}">${item.name}</span>
          <span class="file-size">${size}</span>
          <div class="flex gap-8" onclick="event.stopPropagation()">
            ${!item.is_dir ? `
              <a class="icon-btn" href="${API.downloadFile(_selectedShare.id, item.path)}" download="${item.name}" title="Download">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </a>` : ''}
            <button class="icon-btn" title="Excluir" style="color:var(--accent-red)"
              onclick="Files.deleteItem('${escJs(item.path)}', ${item.is_dir})">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
            </button>
          </div>
        </div>`;
    }).join('');
  }

  function onItemDblClick(path, isDir) {
    if (isDir) {
      browseDirectory(path);
    }
  }

  // ----------------------------------------------------------------
  // FILE ACTIONS
  // ----------------------------------------------------------------
  async function deleteItem(path, isDir) {
    const label = isDir ? 'pasta' : 'arquivo';
    if (!confirm(`Excluir este ${label}? Esta ação é irreversível.`)) return;

    try {
      await API.deleteFile(_selectedShare.id, path);
      App.showToast('success', 'Item excluído');
      browseDirectory(_currentPath);
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  async function newFolder() {
    if (!_selectedShare) { App.showToast('warning', 'Selecione um compartilhamento primeiro'); return; }
    const name = prompt('Nome da nova pasta:');
    if (!name) return;

    // We upload a placeholder; actually we rename  after creating a virtual folder
    // The backend creates folders on share creation, so we use rename trick
    const newPath = _currentPath ? `${_currentPath}/${name}` : name;
    try {
      // Create by uploading an empty file then deleting it, OR call mkdir via upload
      const formData = new FormData();
      formData.append('file', new Blob([''], { type: 'text/plain' }), '.gitkeep');
      formData.append('path', newPath);
      await API.uploadFile(_selectedShare.id, formData);
      App.showToast('success', `Pasta "${name}" criada`);
      browseDirectory(_currentPath);
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  // ----------------------------------------------------------------
  // UPLOAD
  // ----------------------------------------------------------------
  function setupDragDrop() {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('file-input');
    if (!zone || !input) return;

    zone.addEventListener('click', () => {
      if (!_selectedShare) { App.showToast('warning', 'Selecione um compartilhamento primeiro'); return; }
      input.click();
    });

    input.addEventListener('change', () => handleFiles(Array.from(input.files)));

    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.classList.remove('dragover');
      if (!_selectedShare) { App.showToast('warning', 'Selecione um compartilhamento primeiro'); return; }
      handleFiles(Array.from(e.dataTransfer.files));
    });
  }

  async function handleFiles(files) {
    if (!files.length) return;
    if (!_selectedShare) { App.showToast('warning', 'Selecione um compartilhamento primeiro'); return; }

    const statusEl = document.getElementById('upload-status');
    let uploaded = 0;

    for (const file of files) {
      if (statusEl) statusEl.textContent = `Enviando ${file.name}...`;
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', _currentPath);
        await API.uploadFile(_selectedShare.id, formData);
        uploaded++;
      } catch (err) {
        App.showToast('error', `Erro ao enviar ${file.name}: ${err.message}`);
      }
    }

    if (statusEl) statusEl.textContent = '';
    if (uploaded > 0) {
      App.showToast('success', `${uploaded} arquivo(s) enviado(s) com sucesso`);
      browseDirectory(_currentPath);
    }
  }

  function uploadFile() {
    if (!_selectedShare) { App.showToast('warning', 'Selecione um compartilhamento primeiro'); return; }
    document.getElementById('file-input')?.click();
  }

  // ----------------------------------------------------------------
  // NEW SHARE MODAL
  // ----------------------------------------------------------------
  function showNewShareModal() {
    document.getElementById('new-share-modal').classList.add('active');
  }

  function closeNewShareModal() {
    document.getElementById('new-share-modal').classList.remove('active');
  }

  document.getElementById('new-share-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('share-name').value.trim();
    const path = document.getElementById('share-path').value.trim();

    try {
      await API.createShare({ name, path, share_type: 'folder' });
      App.showToast('success', `Compartilhamento "${name}" criado`);
      closeNewShareModal();
      await loadShares();
    } catch (err) {
      App.showToast('error', err.message);
    }
  });

  async function deleteShare(id) {
    if (!confirm('Excluir este compartilhamento? (Os arquivos não serão excluídos)')) return;
    try {
      await API.deleteShare(id);
      if (_selectedShare?.id === id) { _selectedShare = null; }
      App.showToast('success', 'Compartilhamento removido');
      await loadShares();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  function managePermissions(shareId) {
    App.showToast('info', 'Use a seção Dispositivos para gerenciar permissões por dispositivo.');
  }

  // ----------------------------------------------------------------
  // UTILS
  // ----------------------------------------------------------------
  function getFileIcon(name, mime) {
    const ext = name.split('.').pop().toLowerCase();
    const map = {
      mp4:'🎬', mkv:'🎬', avi:'🎬', mov:'🎬', webm:'🎬', m4v:'🎬',
      mp3:'🎵', flac:'🎵', wav:'🎵', ogg:'🎵', m4a:'🎵',
      jpg:'🖼️', jpeg:'🖼️', png:'🖼️', gif:'🖼️', webp:'🖼️',
      pdf:'📄', doc:'📝', docx:'📝', xls:'📊', xlsx:'📊', ppt:'📋', pptx:'📋',
      zip:'🗜️', rar:'🗜️', '7z':'🗜️', tar:'🗜️', gz:'🗜️',
      txt:'📄', md:'📄', json:'💻', js:'💻', py:'💻', html:'💻', css:'💻',
      exe:'⚙️', msi:'⚙️', deb:'⚙️', rpm:'⚙️',
    };
    return map[ext] || '📄';
  }

  function escJs(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"');
  }

  return {
    load, loadShares, selectShare, browseDirectory,
    onItemDblClick, deleteItem, newFolder, uploadFile, handleFiles,
    showNewShareModal, closeNewShareModal, deleteShare, managePermissions,
  };

})();
