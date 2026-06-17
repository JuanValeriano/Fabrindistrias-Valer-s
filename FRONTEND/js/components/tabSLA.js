let slaChart = null;

export function renderTabSLA(container, data) {
    const stats = data.ciclo_stats || {};
    const alert = data.sla_alert || {};
    const histograma = data.histograma || { categorias: [], cantidades: [] };
    const slowestCases = data.slowest_cases || [];

    if (!stats.promedio) {
        container.innerHTML = `
            <div class="alert alert-warning" style="margin-top: 1rem;">
                <h4>⚠️ Sin Datos de Tiempo</h4>
                <p>No se encontraron suficientes datos temporales para calcular los tiempos de ciclo en el subconjunto de datos filtrados.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="card" style="margin-top: 1rem; margin-bottom: 2rem;">
            <h3>⏱️ Análisis de Tiempos de Ciclo (Cycle Time)</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">
                El tiempo de ciclo mide la duración total de un caso, desde su primera actividad hasta la última registrada.
            </p>
            
            <div class="kpi-grid">
                <div class="card kpi-card" style="background-color: rgba(255,255,255,0.01);">
                    <span class="kpi-label">⏱️ Duración Promedio</span>
                    <span class="kpi-value">${stats.promedio} hrs</span>
                </div>
                <div class="card kpi-card" style="background-color: rgba(255,255,255,0.01);">
                    <span class="kpi-label">🎯 Duración Mediana</span>
                    <span class="kpi-value">${stats.mediana} hrs</span>
                </div>
                <div class="card kpi-card" style="background-color: rgba(255,255,255,0.01);">
                    <span class="kpi-label">⚡ Duración Mínima</span>
                    <span class="kpi-value">${stats.minima} hrs</span>
                </div>
                <div class="card kpi-card" style="background-color: rgba(255,255,255,0.01);">
                    <span class="kpi-label">🐢 Duración Máxima</span>
                    <span class="kpi-value">${stats.maxima} hrs</span>
                </div>
            </div>
            
            <div class="divider"></div>
            
            <div class="admin-columns">
                <div class="admin-col" style="flex: 1 1 300px;">
                    <h3>Cumplimiento de SLA Operativo</h3>
                    <div class="card kpi-card" style="margin-top: 1rem; background-color: rgba(255,255,255,0.02); height: 100%;">
                        <span class="kpi-label">Tasa de Cumplimiento (%)</span>
                        <span class="kpi-value" style="color: ${data.sla_cumplimiento === 100 ? 'var(--success)' : 'var(--accent)'};">
                            ${data.sla_cumplimiento}%
                        </span>
                        <span class="kpi-footer" style="color: var(--text-muted);">
                            Meta: ${alert.meta_horas} hrs de ciclo por lote
                        </span>
                    </div>
                </div>
                
                <div class="admin-col" style="flex: 1 1 400px;">
                    <h3>Distribución de Duraciones (Frecuencia)</h3>
                    <div class="chart-container" style="height: 220px; border: none; padding: 0; background: none; margin-top: 1rem;">
                        <canvas id="chart-sla-histogram"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="divider"></div>
            
            <h3>🐢 Top 10 Casos más Lentos (Retrasos)</h3>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">
                Listado de los lotes que han registrado mayor tiempo de procesamiento.
            </p>
            
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>ID Caso</th>
                            <th>Fecha Inicio</th>
                            <th>Fecha Fin</th>
                            <th>Duración Total</th>
                            <th>SLA Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${slowestCases.map(c => `
                            <tr>
                                <td style="font-weight: 600;">${c.id_caso}</td>
                                <td>${c.inicio}</td>
                                <td>${c.fin}</td>
                                <td style="color: var(--accent); font-weight: 700;">${c.duracion}</td>
                                <td>
                                    <span style="color: ${c.status === 'Cumple SLA' ? 'var(--success)' : 'var(--error)'}; font-weight: 600;">
                                        ${c.status}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    if (slaChart) slaChart.destroy();

    const slaCtx = document.getElementById('chart-sla-histogram').getContext('2d');

    slaChart = new Chart(slaCtx, {
        type: 'bar',
        data: {
            labels: histograma.categorias,
            datasets: [{
                label: 'Cantidad',
                data: histograma.cantidades,
                backgroundColor: '#d62728',
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
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 9 } } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 9 } } }
            }
        }
    });
}
