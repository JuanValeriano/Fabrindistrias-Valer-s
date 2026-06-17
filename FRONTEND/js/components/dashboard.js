import { api } from '../api.js';
import { renderTabs } from './tabs.js';
import { renderTabProcessMap } from './tabProcessMap.js';
import { renderTabStats } from './tabStats.js';
import { renderTabVariants } from './tabVariants.js';
import { renderTabSLA } from './tabSLA.js';
import { renderTabHandover } from './tabHandover.js';
import { renderTabRawData } from './tabRawData.js';

export function parseMarkdown(text) {
    if (!text) return '';
    let html = text
        .replace(/### (.*)/g, '<h3>$1</h3>')
        .replace(/## (.*)/g, '<h2>$1</h2>')
        .replace(/# (.*)/g, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^- (.*)/gm, '<li>$1</li>')
        .replace(/\r\n/g, '<br>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');

    if (html.includes('<li>')) {

        html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    }
    return html;
}

export function renderDashboard(container, data, id_ejecucion, currentFilters, showToast) {
    if (data.empty) {
        container.innerHTML = `
            <div class="alert alert-danger" style="margin-top: 2rem;">
                <h4>⚠️ No hay datos para mostrar</h4>
                <p>No se encontraron registros de eventos para los filtros seleccionados. Intenta cambiar el rango de fechas, marcar más operarios en el panel lateral o cambiar la variante seleccionada.</p>
            </div>
        `;
        return;
    }

    const kpis = data.kpis;
    const alert = data.sla_alert;

    const costoFormateado = new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(kpis.costo_total);

    let alertHtml = '';
    if (alert.num_retrasados > 0) {
        alertHtml = `
            <div class="alert alert-danger">
                <h4>🚨 ALERTA DE DESEMPEÑO: Se detectaron ${alert.num_retrasados} lotes que superaron la meta operativa de ${alert.meta_horas} horas.</h4>
                <blockquote>
                    <strong>💡 Diagnóstico del Sistema:</strong> El <strong>${alert.porcentaje_critico}%</strong> de los procesos analizados rompen la meta de tiempo establecida. 
                    El tiempo de ciclo promedio de estos lotes críticos es de <strong>${alert.promedio_retraso} horas</strong>. 
                    Te sugerimos observar el <strong>Mapa de Procesos (Grafo)</strong> en la pestaña inferior para identificar qué actividad específica está reteniendo el flujo.
                </blockquote>
            </div>
        `;
    } else {
        alertHtml = `
            <div class="alert alert-success">
                <h4>✅ PROCESO SALUDABLE: Todos los lotes procesados cumplen con la meta operativa de ${alert.meta_horas} horas.</h4>
                <p>No se detectan cuellos de botella críticos a nivel general en los lotes filtrados.</p>
            </div>
        `;
    }

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 0.5rem; gap: 1rem;">
            <div>
                <h1>📊 Cuadro de Mando de Procesos</h1>
                <p class="subtitle" style="margin-bottom: 0;">Visualiza y analiza el flujo de inventario, tiempos y cuellos de botella.</p>
            </div>
            <div style="display: flex; gap: 0.75rem; align-items: center;">
                <button class="btn btn-secondary" id="btn-export-pdf" style="display: flex; align-items: center; gap: 0.5rem; background-color: var(--primary); color: white; border: none; padding: 0.6rem 1.2rem; font-size: 0.9rem;">
                    📄 Exportar PDF
                </button>
                <button class="btn btn-secondary" id="btn-export-docx" style="display: flex; align-items: center; gap: 0.5rem; padding: 0.6rem 1.2rem; font-size: 0.9rem;">
                    📝 Exportar Word
                </button>
            </div>
        </div>
        
        <!-- KPIs Grid -->
        <div class="kpi-grid">
            <div class="card kpi-card">
                <span class="kpi-label">📦 Total de Lotes Procesados</span>
                <span class="kpi-value">${kpis.total_lotes}</span>
                <span class="kpi-footer">Lotes únicos en base de datos</span>
            </div>
            <div class="card kpi-card">
                <span class="kpi-label">🔄 Total de Eventos Registrados</span>
                <span class="kpi-value">${kpis.total_eventos}</span>
                <span class="kpi-footer">Transacciones y registros del historial</span>
            </div>
            <div class="card kpi-card">
                <span class="kpi-label">💰 Costo Total</span>
                <span class="kpi-value">${costoFormateado}</span>
                <span class="kpi-footer">Costo acumulado de lotes</span>
            </div>
        </div>
        
        <!-- SLA Alerts -->
        ${alertHtml}
        
        <!-- Cerebro Analítico Gemini -->
        <div class="card" style="margin-bottom: 2.5rem; border-left: 4px solid var(--primary);">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                🤖 Análisis Sencillo con Inteligencia Artificial (Gemini)
            </h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.25rem;">
                Obtén una explicación clara sobre por qué ocurren las demoras y cómo solucionarlas de forma simple.
            </p>
            
            <button class="btn btn-secondary" id="btn-generate-insights">
                Explicar Resultados con Gemini 🧠
            </button>
            
            <div id="gemini-insights-container" style="margin-top: 1.5rem; display: none;">
                <!-- Resultados cargados vía API -->
            </div>
        </div>
        
        <!-- Tabs Section -->
        <div class="tabs-navigation">
            <button class="tab-btn active" data-tab="tab-process-map">🗺️ Mapa de Procesos Real</button>
            <button class="tab-btn" data-tab="tab-stats">📊 Análisis Estadístico</button>
            <button class="tab-btn" data-tab="tab-variants">🔄 Análisis de Variantes</button>
            <button class="tab-btn" data-tab="tab-sla">⏱️ Tiempos de Ciclo y SLA</button>
            <button class="tab-btn" data-tab="tab-handover">🤝 Matriz de Traspaso (SNA)</button>
            <button class="tab-btn" data-tab="tab-raw-data">📋 Datos Crudos</button>
        </div>
        
        <!-- Tab Content Containers -->
        <div class="tab-panel active" id="tab-process-map"></div>
        <div class="tab-panel" id="tab-stats"></div>
        <div class="tab-panel" id="tab-variants"></div>
        <div class="tab-panel" id="tab-sla"></div>
        <div class="tab-panel" id="tab-handover"></div>
        <div class="tab-panel" id="tab-raw-data"></div>
    `;

    const geminiBtn = document.getElementById('btn-generate-insights');
    const geminiContainer = document.getElementById('gemini-insights-container');

    geminiBtn.addEventListener('click', async () => {
        geminiBtn.disabled = true;
        geminiBtn.innerText = 'Analizando salud del proceso... ⏳';
        geminiContainer.style.display = 'block';
        geminiContainer.innerHTML = `
            <div class="spinner-container" style="padding: 1.5rem 0;">
                <div class="spinner" style="width: 30px; height: 30px;"></div>
                <span class="spinner-text">Gemini está analizando los cuellos de botella...</span>
            </div>
        `;

        try {
            const reqPayload = {
                total_lotes: kpis.total_lotes,
                meta_horas: alert.meta_horas,
                num_retrasados: alert.num_retrasados,
                porcentaje_critico: alert.porcentaje_critico,
                promedio_retraso: alert.promedio_retraso,
                contexto_negocio: data.contexto_negocio
            };

            const res = await api.getGeminiInsights(reqPayload);
            geminiContainer.innerHTML = `
                <div class="alert alert-info" style="border: none; margin-bottom: 0;">
                    <div style="font-size: 0.95rem; line-height: 1.6;">
                        ${parseMarkdown(res.insights)}
                    </div>
                </div>
            `;
        } catch (error) {
            geminiContainer.innerHTML = `
                <p style="color: var(--error);">Error al conectar con la API de Gemini: ${error.message}</p>
            `;
        } finally {
            geminiBtn.disabled = false;
            geminiBtn.innerText = 'Explicar Resultados con Gemini 🧠';
        }
    });

    const btnPdf = document.getElementById('btn-export-pdf');
    const btnDocx = document.getElementById('btn-export-docx');

    async function handleExport(format, button) {
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `⏳ Generando ${format.toUpperCase()}...`;
        
        const insightsContainer = document.getElementById('gemini-insights-container');
        const insightsText = (insightsContainer && insightsContainer.style.display !== 'none') ? insightsContainer.innerText : null;
        
        try {
            const blob = await api.exportAnalysis(id_ejecucion, format, currentFilters, insightsText);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Reporte_${id_ejecucion}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showToast(`Reporte ${format.toUpperCase()} descargado con éxito.`, 'success');
        } catch (error) {
            console.error('Error exporting analysis:', error);
            showToast('Error al exportar el reporte.', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    if (btnPdf) btnPdf.addEventListener('click', () => handleExport('pdf', btnPdf));
    if (btnDocx) btnDocx.addEventListener('click', () => handleExport('docx', btnDocx));

    renderTabs();

    renderTabProcessMap(document.getElementById('tab-process-map'), id_ejecucion, currentFilters, showToast);
    renderTabStats(document.getElementById('tab-stats'), data, showToast);
    renderTabVariants(document.getElementById('tab-variants'), data);
    renderTabSLA(document.getElementById('tab-sla'), data);
    renderTabHandover(document.getElementById('tab-handover'), data);
    renderTabRawData(document.getElementById('tab-raw-data'), data);
}
