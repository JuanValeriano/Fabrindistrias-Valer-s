import { api } from './api.js';
import { renderLogin } from './components/login.js';
import { renderSidebar } from './components/sidebar.js';
import { renderProfile } from './components/profile.js';
import { renderAdminPanel } from './components/adminPanel.js';
import { renderDashboard } from './components/dashboard.js';

const state = {
    currentView: 'login',
    id_ejecucion: null,
    nombre_analisis: null,
    metadata: null,
    currentFilters: null,
    analysisData: null,
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
    const isLoggedIn = sessionStorage.getItem('logeado') === 'true';

    if (viewName !== 'login' && !isLoggedIn) {
        state.currentView = 'login';
        renderLogin(appElement, navigateTo, showToast);
        return;
    }

    if (viewName === 'login' && isLoggedIn) {
        viewName = '📜 Historial de Análisis';
    }

    state.currentView = viewName;

    if (viewName === 'login') {
        renderLogin(appElement, navigateTo, showToast);
        return;
    }

    appElement.innerHTML = `
        <div class="main-layout">
            <aside class="sidebar" id="app-sidebar"></aside>
            <main class="main-content" id="app-main-view"></main>
        </div>
    `;

    const sidebarContainer = document.getElementById('app-sidebar');
    const mainViewContainer = document.getElementById('app-main-view');

    updateSidebar(sidebarContainer);

    if (viewName === '📊 Nuevo Análisis') {
        navigateTo('📜 Historial de Análisis');
        return;
    } else if (viewName === '📜 Historial de Análisis') {
        if (state.id_ejecucion && state.analysisData) {
            renderDashboard(mainViewContainer, state.analysisData, state.id_ejecucion, state.currentFilters, showToast);
        } else {
            mainViewContainer.innerHTML = `
                <h1>📜 Historial de Análisis</h1>
                <p class="subtitle">Consulta modelos de procesos generados anteriormente.</p>
                <div class="alert alert-info" style="margin-top: 2rem;">
                    <h4>👋 Selecciona un análisis histórico</h4>
                    <p>Busca en el menú desplegable del panel lateral uno de los análisis previamente inyectados en la base de datos de PostgreSQL y haz clic en "Cargar Análisis" para cargar las variantes e indicadores de eficiencia.</p>
                </div>
            `;
        }
    } else if (viewName === '⚙️ Panel de Administrador') {
        await renderAdminPanel(mainViewContainer, showToast);
    } else if (viewName === '👤 Mi Perfil') {
        renderProfile(mainViewContainer, showToast);
    }
}

function updateSidebar(container) {
    renderSidebar(
        container,
        state.currentView,
        navigateTo,
        onAnalysisLoadSuccess,
        onApplyFilters,
        state.currentFilters,
        state.metadata
    );
}

async function onAnalysisLoadSuccess(id_ejecucion) {
    const mainViewContainer = document.getElementById('app-main-view');
    mainViewContainer.innerHTML = `
        <div class="spinner-container">
            <div class="spinner"></div>
            <span class="spinner-text">Cargando registros e inyectando datos de PostgreSQL...</span>
        </div>
    `;

    try {
        const data = await api.queryAnalysis(id_ejecucion, {});

        state.id_ejecucion = id_ejecucion;
        state.metadata = data.metadata;
        state.analysisData = data;

        state.currentFilters = {
            f_inicio: data.metadata.fecha_min,
            f_fin: data.metadata.fecha_max,
            var_seleccionada: 'Todas',
            emps_seleccionados: data.metadata.empleados
        };

        showToast('¡Análisis cargado correctamente!', 'success');

        navigateTo(state.currentView);

    } catch (error) {
        showToast(`Error al consultar datos del análisis: ${error.message}`, 'error');
        navigateTo(state.currentView);
    }
}

async function onApplyFilters(newFilters) {
    const mainViewContainer = document.getElementById('app-main-view');
    mainViewContainer.innerHTML = `
        <div class="spinner-container">
            <div class="spinner"></div>
            <span class="spinner-text">Filtrando y recalculando indicadores operativos...</span>
        </div>
    `;

    try {
        const data = await api.queryAnalysis(state.id_ejecucion, newFilters);

        state.analysisData = data;
        state.currentFilters = newFilters;

        showToast('Filtros aplicados correctamente.', 'success');

        navigateTo(state.currentView);

    } catch (error) {
        showToast(`Error al aplicar filtros: ${error.message}`, 'error');
        navigateTo(state.currentView);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const isLoggedIn = sessionStorage.getItem('logeado') === 'true';
    if (isLoggedIn) {
        navigateTo('📜 Historial de Análisis');
    } else {
        navigateTo('login');
    }
});
