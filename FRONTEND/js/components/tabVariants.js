let varChart = null;

export function renderTabVariants(container, data) {
    const variants = data.variantes_filtradas || [];

    container.innerHTML = `
        <div class="card" style="margin-top: 1rem; margin-bottom: 2rem;">
            <h3>🔄 Análisis de Variantes de Proceso</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">
                Una <strong>variante</strong> es un camino específico (secuencia ordenada de actividades) que sigue un lote de principio a fin.
            </p>
            
            <div class="kpi-grid" style="margin-bottom: 1.5rem;">
                <div class="card kpi-card" style="background-color: rgba(255,255,255,0.01);">
                    <span class="kpi-label">Variantes Únicas Descubiertas</span>
                    <span class="kpi-value">${variants.length}</span>
                    <span class="kpi-footer">Rutas diferentes seguidas en el lote actual</span>
                </div>
            </div>
            
            <div class="table-responsive" style="margin-bottom: 2rem;">
                <table>
                    <thead>
                        <tr>
                            <th>ID Variante</th>
                            <th>Secuencia de Actividades</th>
                            <th>Casos</th>
                            <th>Cobertura (%)</th>
                        </tr>
                    </thead>
                    <tbody id="variants-table-body">
                        ${variants.map(v => `
                            <tr>
                                <td style="font-weight: 700; color: var(--primary-hover);">${v.id}</td>
                                <td style="font-size: 0.85rem;">${v.actividades}</td>
                                <td>${v.casos}</td>
                                <td><strong>${v.cobertura}%</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            <div class="chart-container" style="height: 350px; margin-bottom: 1.5rem;">
                <div class="chart-title">📊 Cobertura por Variante</div>
                <div class="chart-wrapper">
                    <canvas id="chart-variants-coverage"></canvas>
                </div>
            </div>
            
            ${data && data.interpretaciones && data.interpretaciones.variantes ? `
            <div class="business-interpretation" style="padding: 1.25rem; background-color: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-left: 4px solid var(--primary); border-radius: 8px;">
                <h4 style="margin-top: 0; color: var(--primary-hover); display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">
                    💡 Interpretación de Variantes
                </h4>
                <p style="margin-bottom: 0; font-size: 0.95rem; line-height: 1.6; color: var(--text-main);">${data.interpretaciones.variantes}</p>
            </div>
            ` : ''}
        </div>
    `;

    if (varChart) varChart.destroy();

    const varCtx = document.getElementById('chart-variants-coverage').getContext('2d');
    const varLabels = variants.map(v => v.id);
    const varValues = variants.map(v => v.cobertura);

    varChart = new Chart(varCtx, {
        type: 'bar',
        data: {
            labels: varLabels,
            datasets: [{
                label: 'Cobertura (%)',
                data: varValues,
                backgroundColor: '#9467bd',
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
}
