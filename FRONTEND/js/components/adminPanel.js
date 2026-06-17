import { api } from '../api.js';

export async function renderAdminPanel(container, showToast) {
    container.innerHTML = `
        <h1>⚙️ Gestión del Sistema</h1>
        <p class="subtitle">Panel exclusivo para el Administrador de Procesos.</p>
        
        <div class="admin-tabs">
            <button class="admin-tab-btn active" id="btn-tab-usuarios">👥 Gestión de Usuarios</button>
            <button class="admin-tab-btn" id="btn-tab-sla">⏳ Configuración de Alertas (SLA)</button>
        </div>
        
        <div id="admin-tab-content-usuarios" class="admin-tab-content">
            <div class="admin-columns">
                <div class="admin-col">
                    <div class="card">
                        <h3>Crear Nuevo Usuario</h3>
                        <form id="create-user-form" style="margin-top: 1rem;">
                            <div class="form-group">
                                <label for="new-username">Nombre de Usuario</label>
                                <input type="text" id="new-username" class="form-control" placeholder="Nombre" required autocomplete="username">
                            </div>
                            
                            <div class="form-group">
                                <label for="new-password">Contraseña Temporal</label>
                                <input type="password" id="new-password" class="form-control" placeholder="Contraseña" required autocomplete="new-password">
                            </div>
                            
                            <div class="form-group">
                                <label for="new-role">Rol</label>
                                <select id="new-role" class="form-control">
                                    <option value="usuario">usuario</option>
                                    <option value="admin">admin</option>
                                </select>
                            </div>
                            
                            <button type="submit" class="btn btn-primary btn-block" style="margin-top: 1rem;">
                                Registrar
                            </button>
                        </form>
                    </div>
                </div>
                
                <div class="admin-col">
                    <div class="card" style="height: 100%; min-height: 380px;">
                        <h3>Usuarios Registrados</h3>
                        <div id="users-list-container" style="margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem; max-height: 300px; overflow-y: auto;">
                            <!-- La lista se cargará dinámicamente -->
                            <div class="spinner-container">
                                <div class="spinner" style="width: 30px; height: 30px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="admin-tab-content-sla" class="admin-tab-content" style="display: none;">
            <div class="card" style="max-width: 600px;">
                <h3>Meta Global de Operación</h3>
                <p class="subtitle" style="margin-bottom: 1.5rem; font-size: 0.9rem;">Define el tiempo máximo aceptable que debe tardar un caso/lote de principio a fin.</p>
                
                <form id="sla-config-form">
                    <div class="form-group">
                        <label for="meta-tiempo">Meta Máxima de Ciclo (Horas):</label>
                        <input type="number" id="meta-tiempo" class="form-control" step="0.5" required>
                    </div>
                    
                    <button type="submit" class="btn btn-primary" style="margin-top: 1rem;">
                        Guardar Configuración
                    </button>
                </form>
            </div>
        </div>
    `;

    const btnUsuarios = document.getElementById('btn-tab-usuarios');
    const btnSLA = document.getElementById('btn-tab-sla');
    const contentUsuarios = document.getElementById('admin-tab-content-usuarios');
    const contentSLA = document.getElementById('admin-tab-content-sla');

    btnUsuarios.addEventListener('click', () => {
        btnUsuarios.classList.add('active');
        btnSLA.classList.remove('active');
        contentUsuarios.style.display = 'block';
        contentSLA.style.display = 'none';
    });

    btnSLA.addEventListener('click', async () => {
        btnSLA.classList.add('active');
        btnUsuarios.classList.remove('active');
        contentSLA.style.display = 'block';
        contentUsuarios.style.display = 'none';
        await loadSlaConfig();
    });

    const usersContainer = document.getElementById('users-list-container');
    const currentUser = sessionStorage.getItem('usuario_actual');

    async function loadUsers() {
        try {
            usersContainer.innerHTML = '';
            const users = await api.getUsers();

            if (users.length === 0) {
                usersContainer.innerHTML = '<p style="color: var(--text-muted);">No hay usuarios registrados.</p>';
                return;
            }

            users.forEach(user => {
                const isSelf = user.usuario === currentUser;
                const actionHtml = isSelf
                    ? '<span style="font-size: 0.85rem; color: var(--text-muted); font-style: italic;">🔒 Tú (Protegido)</span>'
                    : `<button class="btn btn-danger btn-delete-user" data-username="${user.usuario}" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;">🗑️ Eliminar</button>`;

                const item = document.createElement('div');
                item.className = 'user-list-item';
                item.innerHTML = `
                    <div class="user-info">
                        <span class="user-username">👤 ${user.usuario}</span>
                        <span class="user-role">Rol: ${user.rol}</span>
                    </div>
                    <div>
                        ${actionHtml}
                    </div>
                `;
                usersContainer.appendChild(item);
            });

            document.querySelectorAll('.btn-delete-user').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const username = e.target.getAttribute('data-username');
                    if (confirm(`¿Estás seguro de eliminar al usuario '${username}'?`)) {
                        try {
                            const res = await api.deleteUser(username);
                            if (res.success) {
                                showToast(res.message, 'success');
                                await loadUsers();
                            }
                        } catch (err) {
                            showToast(err.message || 'Error al eliminar usuario.', 'error');
                        }
                    }
                });
            });

        } catch (error) {
            usersContainer.innerHTML = `<p style="color: var(--error);">Error al cargar la lista: ${error.message}</p>`;
        }
    }

    const createForm = document.getElementById('create-user-form');
    createForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('new-username').value.trim();
        const password = document.getElementById('new-password').value;
        const role = document.getElementById('new-role').value;

        try {
            const res = await api.createUser(username, password, role);
            if (res.success) {
                showToast(res.message, 'success');
                createForm.reset();
                await loadUsers();
            }
        } catch (error) {
            showToast(error.message || 'Error al crear usuario.', 'error');
        }
    });

    const slaInput = document.getElementById('meta-tiempo');
    const slaForm = document.getElementById('sla-config-form');

    async function loadSlaConfig() {
        try {
            const data = await api.getSlaMeta();
            slaInput.value = data.meta_horas;
        } catch (error) {
            showToast('Error al consultar configuración de SLA.', 'error');
        }
    }

    slaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const metaVal = parseFloat(slaInput.value);
        try {
            const res = await api.updateSlaMeta(metaVal);
            if (res.success) {
                showToast(res.message, 'success');
            }
        } catch (error) {
            showToast(error.message || 'Error al actualizar SLA.', 'error');
        }
    });

    await loadUsers();
}
