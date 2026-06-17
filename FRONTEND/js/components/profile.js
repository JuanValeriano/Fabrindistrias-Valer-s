import { api } from '../api.js';

export function renderProfile(container, showToast) {
    const usuario = sessionStorage.getItem('usuario_actual') || 'Usuario';
    const rol = sessionStorage.getItem('rol') || 'usuario';
    
    container.innerHTML = `
        <h1>👤 Mi Perfil de Usuario</h1>
        <p class="subtitle">Gestiona tus credenciales y visualiza tu información de acceso.</p>
        
        <div class="card" style="margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">Información de Cuenta</h3>
            <p style="margin-bottom: 0.5rem;"><strong>Usuario Logeado:</strong> ${usuario}</p>
            <p style="margin-bottom: 0.5rem;"><strong>Nivel de Acceso:</strong> ${rol.charAt(0).toUpperCase() + rol.slice(1)}</p>
        </div>
        
        <div class="card" style="max-width: 600px;">
            <h3 style="margin-bottom: 0.5rem;">🔑 Cambiar Contraseña</h3>
            <p class="subtitle" style="margin-bottom: 1.5rem; font-size: 0.9rem;">Por seguridad, necesitas ingresar tu contraseña actual para establecer una nueva.</p>
            
            <form id="change-pass-form">
                <div class="form-group">
                    <label for="pass-actual">Contraseña Actual</label>
                    <input type="password" id="pass-actual" class="form-control" placeholder="Contraseña actual" required autocomplete="current-password">
                </div>
                
                <div class="form-group">
                    <label for="pass-nueva">Nueva Contraseña</label>
                    <input type="password" id="pass-nueva" class="form-control" placeholder="Nueva contraseña" required autocomplete="new-password">
                </div>
                
                <div class="form-group">
                    <label for="pass-confirmar">Confirmar Nueva Contraseña</label>
                    <input type="password" id="pass-confirmar" class="form-control" placeholder="Confirmar nueva contraseña" required autocomplete="new-password">
                </div>
                
                <button type="submit" class="btn btn-primary" style="margin-top: 1rem;">
                    Actualizar Contraseña
                </button>
            </form>
        </div>
    `;
    
    const form = document.getElementById('change-pass-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const passActual = document.getElementById('pass-actual').value;
        const passNueva = document.getElementById('pass-nueva').value;
        const passConfirmar = document.getElementById('pass-confirmar').value;
        
        if (passNueva !== passConfirmar) {
            showToast('Las contraseñas nuevas no coinciden.', 'error');
            return;
        }
        
        try {
            const res = await api.changePassword(usuario, passActual, passNueva);
            if (res.success) {
                showToast(res.message, 'success');
                form.reset();
            }
        } catch (error) {
            showToast(error.message || 'Error al cambiar contraseña.', 'error');
        }
    });
}
