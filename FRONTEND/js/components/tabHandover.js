export function renderTabHandover(container, data) {
    const matrix = data.matriz_traspaso || {};

    if (!matrix.index || matrix.index.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info" style="margin-top: 1rem;">
                <h4>🤝 Sin Traspasos Registrados</h4>
                <p>No se registraron traspasos de trabajo entre diferentes operarios en los datos actuales.</p>
            </div>
        `;
        return;
    }

    let maxVal = 0;
    matrix.values.forEach(row => {
        row.forEach(val => {
            if (val > maxVal) maxVal = val;
        });
    });
    if (maxVal === 0) maxVal = 1;

    const headerHtml = `
        <th>Entrega \\ Recibe</th>
        ${matrix.columns.map(col => `<th style="text-align: center; font-size: 0.85rem; font-weight: 700;">${col}</th>`).join('')}
    `;

    const rowsHtml = matrix.index.map((rowName, rIdx) => {
        const cellsHtml = matrix.values[rIdx].map((val, cIdx) => {
            let style = 'background-color: transparent;';
            let cellText = val;

            if (val > 0) {
                const ratio = val / maxVal;
                style = `background-color: rgba(139, 92, 246, ${0.15 + ratio * 0.85}); font-weight: 700; color: white;`;
            } else {
                style = 'color: var(--text-muted); opacity: 0.4;';
                cellText = '0';
            }

            return `
                <td class="heatmap-cell" style="${style} text-align: center; padding: 0.75rem 0.5rem; border: 1px solid rgba(255,255,255,0.03);">
                    ${cellText}
                </td>
            `;
        }).join('');

        return `
            <tr>
                <td style="font-weight: 700; font-size: 0.85rem; background-color: rgba(255,255,255,0.01);">${rowName}</td>
                ${cellsHtml}
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        <div class="card" style="margin-top: 1rem;">
            <h3>🤝 Matriz de Traspaso de Trabajo (Handover of Work)</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">
                Esta matriz muestra cómo se transfiere la responsabilidad de los lotes entre los operarios. Las filas representan quién <strong>entrega</strong> el trabajo y las columnas quién lo <strong>recibe</strong>.
            </p>
            
            <div class="table-responsive" style="margin-bottom: 1.5rem;">
                <table class="heatmap-table" style="border: 1px solid var(--border-color);">
                    <thead>
                        <tr>${headerHtml}</tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>
            </div>
            
            <div class="alert alert-info" style="margin-bottom: 0;">
                <h4>💡 Cómo interpretar esta matriz</h4>
                <p>Los números representan traspasos de tareas entre personas en casos idénticos. Celdas con números altos (fondos púrpuras más intensos) denotan dependencias directas o cargas concentradas. Celdas vacías indican que no hay interacción directa en las secuencias observadas.</p>
            </div>
            
            ${data && data.interpretaciones && data.interpretaciones.matriz_traspaso ? `
            <div class="business-interpretation" style="margin-top: 1.5rem; padding: 1.25rem; background-color: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-left: 4px solid var(--primary); border-radius: 8px;">
                <h4 style="margin-top: 0; color: var(--primary-hover); display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">
                    💡 Interpretación del Traspaso de Tareas
                </h4>
                <p style="margin-bottom: 0; font-size: 0.95rem; line-height: 1.6; color: var(--text-main);">${data.interpretaciones.matriz_traspaso}</p>
            </div>
            ` : ''}
        </div>
    `;
}
