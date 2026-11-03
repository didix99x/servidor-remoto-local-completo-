/**
 * Settings page controller.
 */
const Settings = (() => {

  // ----------------------------------------------------------------
  // LOAD
  // ----------------------------------------------------------------
  async function load() {
    await Promise.all([loadServerInfo(), loadUsers()]);
  }

  // ----------------------------------------------------------------
  // SERVER INFO
  // ----------------------------------------------------------------
  async function loadServerInfo() {
    const container = document.getElementById('server-info-container');
    if (!container) return;

    try {
      const [info, localIp] = await Promise.all([
        API.sysInfo(),
        API.localIP(),
      ]);

      container.innerHTML = `
        <div style="display:grid;gap:10px">
          ${infoRow('Endereço da HUD', `<a href="http://${localIp.ip}:${location.port || 8000}" target="_blank" style="color:var(--accent-primary)">http://${localIp.ip}:${location.port || 8000}</a>`)}
          ${infoRow('Plataforma', info.platform)}
          ${infoRow('Python', info.python_version)}
          ${infoRow('CPU', `${info.cpu_count} núcleo(s) — ${info.cpu_percent?.toFixed(1)}% em uso`)}
          ${infoRow('Memória', `${info.memory_used_gb?.toFixed(1)} GB / ${info.memory_total_gb?.toFixed(1)} GB`)}
          ${infoRow('Disco Livre', `${info.disk_free_gb?.toFixed(1)} GB`)}
          ${infoRow('Uptime do Servidor', formatUptime(info.uptime_seconds))}
        </div>`;
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red)">Erro: ${err.message}</div>`;
    }
  }

  function infoRow(label, value) {
    return `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border-color)">
        <span class="text-small text-muted">${label}</span>
        <span class="text-small">${value}</span>
      </div>`;
  }

  function formatUptime(seconds) {
    if (!seconds) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}h ${m}m ${s}s`;
  }

  // ----------------------------------------------------------------
  // USERS
  // ----------------------------------------------------------------
  async function loadUsers() {
    const container = document.getElementById('users-list-container');
    if (!container) return;

    try {
      const users = await API.listUsers();
      const currentUser = App.currentUser;

      container.innerHTML = `
        <table class="data-table">
          <thead><tr><th>Usuário</th><th>Email</th><th>Papel</th><th>Status</th><th>Ações</th></tr></thead>
          <tbody>
            ${users.map(u => `
              <tr>
                <td>
                  <div class="flex items-center gap-8">
                    <div class="user-avatar" style="width:28px;height:28px;font-size:0.75rem">${u.username[0].toUpperCase()}</div>
                    <span style="font-weight:600">${u.username}</span>
                  </div>
                </td>
                <td class="text-small text-muted">${u.email}</td>
                <td><span class="badge ${u.role === 'admin' ? 'badge-authorized' : 'badge-pending'}">${roleLabel(u.role)}</span></td>
                <td><span class="badge ${u.is_active ? 'badge-online' : 'badge-offline'}">${u.is_active ? 'Ativo' : 'Inativo'}</span></td>
                <td>
                  ${u.id !== currentUser?.id ? `
                    <div class="flex gap-8">
                      <button class="icon-btn" title="${u.is_active ? 'Desativar' : 'Ativar'}"
                        onclick="Settings.toggleUser(${u.id}, ${!u.is_active})"
                        style="color:${u.is_active ? 'var(--accent-orange)' : 'var(--accent-green)'}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>
                      </button>
                      <button class="icon-btn" title="Excluir" style="color:var(--accent-red)"
                        onclick="Settings.deleteUser(${u.id}, '${u.username}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
                      </button>
                    </div>` : '<span class="text-small text-muted">(você)</span>'}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>`;
    } catch (err) {
      container.innerHTML = `<div style="color:var(--accent-red);padding:16px">Erro: ${err.message}</div>`;
    }
  }

  function roleLabel(role) {
    const map = { admin: 'Admin', user: 'Usuário', viewer: 'Visualizador' };
    return map[role] || role;
  }

  // ----------------------------------------------------------------
  // USER ACTIONS
  // ----------------------------------------------------------------
  async function toggleUser(id, active) {
    try {
      await API.updateUser(id, { is_active: active });
      App.showToast('success', active ? 'Usuário ativado' : 'Usuário desativado');
      await loadUsers();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  async function deleteUser(id, username) {
    if (!confirm(`Excluir o usuário "${username}"?`)) return;
    try {
      await API.deleteUser(id);
      App.showToast('success', 'Usuário excluído');
      await loadUsers();
    } catch (err) {
      App.showToast('error', err.message);
    }
  }

  // ----------------------------------------------------------------
  // NEW USER MODAL
  // ----------------------------------------------------------------
  function showNewUserModal() {
    document.getElementById('new-user-modal').classList.add('active');
  }

  function closeNewUserModal() {
    document.getElementById('new-user-modal').classList.remove('active');
  }

  document.getElementById('new-user-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = {
      username: document.getElementById('new-user-username').value.trim(),
      email:    document.getElementById('new-user-email').value.trim(),
      password: document.getElementById('new-user-password').value,
      role:     document.getElementById('new-user-role').value,
    };
    try {
      await API.createUser(body);
      App.showToast('success', `Usuário "${body.username}" criado`);
      closeNewUserModal();
      await loadUsers();
      e.target.reset();
    } catch (err) {
      App.showToast('error', err.message);
    }
  });

  // ----------------------------------------------------------------
  // CHANGE PASSWORD
  // ----------------------------------------------------------------
  document.getElementById('change-password-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const cur  = document.getElementById('cur-password').value;
    const nw   = document.getElementById('new-password').value;
    const conf = document.getElementById('confirm-password').value;

    if (nw !== conf) {
      App.showToast('error', 'As senhas não coincidem');
      return;
    }

    try {
      await API.changePassword(cur, nw);
      App.showToast('success', '✅ Senha alterada com sucesso');
      e.target.reset();
    } catch (err) {
      App.showToast('error', err.message);
    }
  });

  return { load, loadServerInfo, loadUsers, toggleUser, deleteUser, showNewUserModal, closeNewUserModal };

})();
