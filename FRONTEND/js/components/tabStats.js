import { api } from '../api.js';
import { parseMarkdown } from './dashboard.js';

let charts = {
    actChart: null,
    empChart: null,
    timeChart: null
};

export function renderTabStats(container, data, showToast) {
    container.innerHTML = `
        <div class="card" style="margin-top: 1rem; margin-bottom: 2rem;">
            <h3>📊 Indicadores de Eficiencia Operativa</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">
                Analiza las cargas de trabajo, distribución de actividades y fluctuaciones del volumen en el tiempo.
            </p>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">Frecuencia de Actividades</div>
                    <div class="chart-wrapper">
                        <canvas id="chart-activities"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">Carga de Trabajo por Empleado</div>
                    <div class="chart-wrapper">
                        <canvas id="chart-employees"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="chart-container" style="height: 380px; margin-top: 1.5rem;">
                <div class="chart-title">📈 Volumen de Eventos en el Tiempo</div>
                <div class="chart-wrapper">
                    <canvas id="chart-timeline"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Gemini Interpretation Section -->
        <div class="card" style="margin-bottom: 2rem; border-left: 4px solid var(--success);">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                🤖 Interpretación Inteligente de Gráficos (Gemini)
            </h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.25rem;">
                Genera una explicación fácil de entender sobre lo que nos dicen las gráficas, sin tecnicismos ni complicaciones.
            </p>
            
            <button class="btn btn-primary" id="btn-interpret-stats" style="width: 100%;">
                Explicar Gráficos con Gemini 🧠
            </button>
            
            <div id="gemini-stats-container" style="margin-top: 1.5rem; display: none;">
                <!-- Resultados Gemini cargados dinámicamente -->
            </div>
        </div>
    `;

    if (charts.actChart) charts.actChart.destroy();
    if (charts.empChart) charts.empChart.destroy();
    if (charts.timeChart) charts.timeChart.destroy();

    const actCtx = document.getElementById('chart-activities').getContext('2d');
    const actLabels = Object.keys(data.act_counts);
    const actValues = Object.values(data.act_counts);

    charts.actChart = new Chart(actCtx, {
        type: 'bar',
        data: {
            labels: actLabels,
            datasets: [{
                label: 'Cantidad',
                data: actValues,
                backgroundColor: '#8b5cf6',
                borderRadius: 4,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    const empCtx = document.getElementById('chart-employees').getContext('2d');
    const empLabels = Object.keys(data.emp_counts);
    const empValues = Object.values(data.emp_counts);

    charts.empChart = new Chart(empCtx, {
        type: 'bar',
        data: {
            labels: empLabels,
            datasets: [{
                label: 'Cantidad',
                data: empValues,
                backgroundColor: '#ff7f0e',
                borderRadius: 4,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    const timeCtx = document.getElementById('chart-timeline').getContext('2d');

    const timeGroup = {};
    data.datos_crudos.forEach(ev => {
        const tsField = ev.timestamp || ev.fecha_hora;
        if (tsField) {
            const dateStr = tsField.substring(0, 10);
            timeGroup[dateStr] = (timeGroup[dateStr] || 0) + 1;
        }
    });

    const sortedDates = Object.keys(timeGroup).sort();
    const timeValues = sortedDates.map(d => timeGroup[d]);

    charts.timeChart = new Chart(timeCtx, {
        type: 'line',
        data: {
            labels: sortedDates,
            datasets: [{
                label: 'Eventos',
                data: timeValues,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.05)',
                borderWidth: 2,
                fill: true,
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    const interpretBtn = document.getElementById('btn-interpret-stats');
    const interpretContainer = document.getElementById('gemini-stats-container');

    interpretBtn.addEventListener('click', async () => {
        interpretBtn.disabled = true;
        interpretBtn.innerText = 'Analizando distribución y picos temporales... ⏳';
        interpretContainer.style.display = 'block';
        interpretContainer.innerHTML = `
            <div class="spinner-container" style="padding: 1.5rem 0;">
                <div class="spinner" style="width: 30px; height: 30px;"></div>
                <span class="spinner-text">Gemini está analizando los gráficos estadísticos...</span>
            </div>
        `;

        try {
            const actContext = actLabels.map(act => `- ${act}: ${data.act_counts[act]} veces`).join('\n');
            const empContext = empLabels.map(emp => `- ${emp}: ${data.emp_counts[emp]} eventos`).join('\n');
            const tempContext = data.picos_trabajo;

            const reqPayload = {
                act_context: actContext,
                emp_context: empContext,
                temp_context: tempContext
            };

            const res = await api.getGeminiTrends(reqPayload);
            interpretContainer.innerHTML = `
                <div class="alert alert-success" style="border: none; margin-bottom: 0;">
                    <div style="font-size: 0.95rem; line-height: 1.6;">
                        ${parseMarkdown(res.trends)}
                    </div>
                </div>
            `;
        } catch (error) {
            interpretContainer.innerHTML = `
                <p style="color: var(--error);">Error al conectar con la API de Gemini: ${error.message}</p>
            `;
        } finally {
            interpretBtn.disabled = false;
            interpretBtn.innerText = 'Explicar Gráficos con Gemini 🧠';
        }
    });
}
