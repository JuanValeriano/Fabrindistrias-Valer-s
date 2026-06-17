import { api } from '../api.js';

export function renderLogin(container, navigateTo, showToast) {
    container.innerHTML = `
        <div class="login-layout">
            <div class="card login-card">
                <div class="login-logo" style="text-align: center; margin-bottom: 2rem;">
                    <h2 style="font-size: 2.25rem; font-weight: 800; background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        📦 Valer's ERP
                    </h2>
                    <p style="color: var(--text-muted);">Registro de Operaciones de Inventario</p>
                </div>
                
                <form id="login-form">
                    <div class="form-group">
                        <label for="username">Usuario</label>
                        <input type="text" id="username" class="form-control" placeholder="Ingresa tu usuario" required autocomplete="username">
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Contraseña</label>
                        <input type="password" id="password" class="form-control" placeholder="Ingresa tu contraseña" required autocomplete="current-password">
                    </div>
                    
                    <button type="submit" class="btn btn-primary btn-block" style="margin-top: 1.5rem;">
                        Acceder al ERP 🚀
                    </button>
                </form>
            </div>
        </div>
    `;
    
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const u = document.getElementById('username').value.trim();
        const p = document.getElementById('password').value;
        
        try {
            const data = await api.login(u, p);
            if (data.success) {
                sessionStorage.setItem('logeado_erp', 'true');
                sessionStorage.setItem('usuario_erp', data.usuario);
                sessionStorage.setItem('rol_erp', data.rol);
                
                showToast(`¡Bienvenido al ERP, ${data.usuario}!`, 'success');
                navigateTo('lotes');
            }
        } catch (error) {
            showToast(error.message || 'Error al iniciar sesión', 'error');
        }
    });
}
