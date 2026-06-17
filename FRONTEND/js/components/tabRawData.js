export function renderTabRawData(container, data) {
    const rawData = data.datos_crudos || [];

    if (rawData.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info" style="margin-top: 1rem;">
                <h4>📋 Sin Registros</h4>
                <p>No hay eventos disponibles en este momento.</p>
            </div>
        `;
        return;
    }

    const PAGE_SIZE = 20;
    let currentPage = 1;
    const totalPages = Math.ceil(rawData.length / PAGE_SIZE);

    const columns = Object.keys(rawData[0]);

    function getReadableHeader(colName) {
        return colName
            .replace(/_/g, ' ')
            .split(' ')
            .map(w => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ');
    }

    container.innerHTML = `
        <div class="card" style="margin-top: 1rem;">
            <h3>📋 Base de Datos Completa (Datos Filtrados)</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">
                Listado completo de eventos y transacciones que coinciden con los filtros aplicados.
            </p>
            
            <div class="table-responsive">
                <table id="raw-data-table">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${getReadableHeader(col)}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody id="raw-table-body">
                        <!-- Las filas se renderizan por JS -->
                    </tbody>
                </table>
            </div>
            
            <div class="pagination-controls">
                <span class="pagination-info" id="raw-pagination-info">
                    Mostrando 0-0 de 0 registros
                </span>
                <div class="pagination-buttons">
                    <button class="btn btn-secondary" id="btn-prev-page" style="padding: 0.5rem 1rem; font-size: 0.85rem;">◀ Anterior</button>
                    <button class="btn btn-secondary" id="btn-next-page" style="padding: 0.5rem 1rem; font-size: 0.85rem;">Siguiente ▶</button>
                </div>
            </div>
        </div>
    `;

    const tbody = container.querySelector('#raw-table-body');
    const pageInfo = container.querySelector('#raw-pagination-info');
    const btnPrev = container.querySelector('#btn-prev-page');
    const btnNext = container.querySelector('#btn-next-page');

    function renderPage() {
        const startIndex = (currentPage - 1) * PAGE_SIZE;
        const endIndex = Math.min(startIndex + PAGE_SIZE, rawData.length);
        const pageData = rawData.slice(startIndex, endIndex);

        tbody.innerHTML = pageData.map(row => {
            return `
                <tr>
                    ${columns.map(col => {
                const val = row[col];
                return `<td>${val !== null && val !== undefined ? val : ''}</td>`;
            }).join('')}
                </tr>
            `;
        }).join('');

        pageInfo.innerText = `Mostrando ${startIndex + 1}-${endIndex} de ${rawData.length} registros (Pág. ${currentPage}/${totalPages})`;

        btnPrev.disabled = currentPage === 1;
        btnNext.disabled = currentPage === totalPages;
    }

    btnPrev.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage();
        }
    });

    btnNext.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderPage();
        }
    });

    renderPage();
}
