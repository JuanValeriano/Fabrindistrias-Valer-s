import { api } from '../api.js';

export function renderLogin(container, navigateTo, showToast) {
    container.innerHTML = `
        <div class="login-container">
            <div class="card login-card">
                <div class="login-logo">
                    <h2>🔐 Acceso al Sistema Valer's</h2>
                    <p>Por favor, ingresa tus credenciales para acceder al análisis de procesos.</p>
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
                        Entrar 🚀
                    </button>
                </form>
            </div>
        </div>
    `;

    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const usuario = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        try {
            const data = await api.login(usuario, password);
            if (data.success) {
                sessionStorage.setItem('logeado', 'true');
                sessionStorage.setItem('usuario_actual', data.usuario);
                sessionStorage.setItem('rol', data.rol);

                showToast(`¡Bienvenido, ${data.usuario}!`, 'success');

                navigateTo('📜 Historial de Análisis');
            }
        } catch (error) {
            showToast(error.message || 'Error al iniciar sesión', 'error');
        }
    });
}
