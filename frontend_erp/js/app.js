import { renderLogin } from './components/login.js';
import { renderLotes } from './components/lotes.js';
import { renderEventos } from './components/eventos.js';

const state = {
    currentView: 'login',
};

export function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `alert-toast alert-toast-${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button class="alert-toast-close">&times;</button>
    `;

    container.appendChild(toast);

    const timer = setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);

    toast.querySelector('.alert-toast-close').addEventListener('click', () => {
        clearTimeout(timer);
        toast.remove();
    });
}

export async function navigateTo(viewName) {
    const appElement = document.getElementById('app');
    const isLoggedIn = sessionStorage.getItem('logeado_erp') === 'true';

    if (viewName !== 'login' && !isLoggedIn) {
        state.currentView = 'login';
        renderLogin(appElement, navigateTo, showToast);
        return;
    }

    if (viewName === 'login' && isLoggedIn) {
        viewName = 'lotes';
    }

    state.currentView = viewName;

    if (viewName === 'login') {
        renderLogin(appElement, navigateTo, showToast);
        return;
    }

    const usuario = sessionStorage.getItem('usuario_erp') || 'Usuario';
    const rol = sessionStorage.getItem('rol_erp') || 'usuario';

    appElement.innerHTML = `
        <header class="navbar">
            <div class="navbar-brand">
                <span class="navbar-logo">📦 Valer's ERP</span>
            </div>
            <div class="navbar-menu">
                <button class="nav-link ${viewName === 'lotes' ? 'active' : ''}" id="nav-lotes">📦 Lotes</button>
                <button class="nav-link ${viewName === 'eventos' ? 'active' : ''}" id="nav-eventos">🔄 Eventos</button>
            </div>
            <div class="navbar-user">
                <span>👤 Usuario: <strong>${usuario}</strong> (${rol})</span>
                <button class="btn btn-secondary" id="nav-logout" style="padding: 0.35rem 0.75rem; font-size: 0.85rem; border: 1px solid rgba(239, 68, 68, 0.2); color: var(--error);">🚪 Salir</button>
            </div>
        </header>
        <div id="erp-content" class="container"></div>
    `;

    const erpContent = document.getElementById('erp-content');

    document.getElementById('nav-lotes').addEventListener('click', () => navigateTo('lotes'));
    document.getElementById('nav-eventos').addEventListener('click', () => navigateTo('eventos'));
    document.getElementById('nav-logout').addEventListener('click', () => {
        sessionStorage.clear();
        navigateTo('login');
    });

    if (viewName === 'lotes') {
        await renderLotes(erpContent, showToast);
    } else if (viewName === 'eventos') {
        await renderEventos(erpContent, showToast);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const isLoggedIn = sessionStorage.getItem('logeado_erp') === 'true';
    if (isLoggedIn) {
        navigateTo('lotes');
    } else {
        navigateTo('login');
    }
});
