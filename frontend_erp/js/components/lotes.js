import { api } from '../api.js';

export async function renderLotes(container, showToast) {
    container.innerHTML = `
        <div class="spinner-container" id="lotes-init-spinner">
            <div class="spinner"></div>
            <span class="spinner-text">Cargando catálogos de base de datos...</span>
        </div>
        
        <div id="lotes-view-content" style="display: none;">
            <h1>📦 Lotes de Inventario</h1>
            <p class="subtitle">Registra nuevos lotes y visualiza el catálogo de órdenes en vivo.</p>
            
            <div class="split-layout">
                <!-- Columna Izquierda: Formulario de Registro -->
                <div class="split-form">
                    <div class="card">
                        <h3>Registrar Nuevo Lote</h3>
                        <form id="create-lote-form" style="margin-top: 1rem;">
                            <div class="form-group">
                                <label for="lote-id">Código de Lote (ID Caso)</label>
                                <input type="text" id="lote-id" placeholder="ej. ENT-26-9001" required pattern="^[A-Za-z0-9-]+$" title="Solo letras, números y guiones">
                            </div>
                            
                            <div class="form-group">
                                <label for="lote-material">Material (SKU)</label>
                                <select id="lote-material" required>
                                    <option value="">Selecciona un material...</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="lote-cantidad">Cantidad</label>
                                <input type="number" id="lote-cantidad" min="1" placeholder="ej. 500" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="lote-proveedor">Proveedor</label>
                                <select id="lote-proveedor" required>
                                    <option value="">Selecciona un proveedor...</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="lote-costo">Costo del Lote (S/.)</label>
                                <input type="number" id="lote-costo" min="0" step="0.01" placeholder="ej. 1250.50" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="lote-prioridad">Prioridad de Producción</label>
                                <select id="lote-prioridad" required>
                                    <option value="Normal">Normal</option>
                                    <option value="Alta">Alta</option>
                                    <option value="Urgente">Urgente</option>
                                </select>
                            </div>
                            
                            <button type="submit" class="btn btn-primary btn-block" style="margin-top: 1rem;">
                                Registrar Lote 💾
                            </button>
                        </form>
                    </div>
                </div>
                
                <!-- Columna Derecha: Tabla de Lotes Existentes -->
                <div class="split-view">
                    <div class="card" style="min-height: 500px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; gap: 1rem; flex-wrap: wrap;">
                            <h3>Lotes Registrados en Vivo</h3>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <button class="btn btn-secondary" id="btn-inject-simulated" style="font-size: 0.85rem; padding: 0.5rem 1rem;">
                                    ⚡ Simular Datos (1000 Eventos)
                                </button>
                                <input type="text" id="lotes-search-input" placeholder="Buscar por código o material..." style="width: 250px; padding: 0.5rem; font-size: 0.85rem; margin-bottom: 0;">
                            </div>
                        </div>
                        
                        <div class="table-responsive">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Código</th>
                                        <th>Material</th>
                                        <th>Cant.</th>
                                        <th>Proveedor</th>
                                        <th>Costo (S/.)</th>
                                        <th>Prio.</th>
                                    </tr>
                                </thead>
                                <tbody id="lotes-table-body">
                                    <!-- Cargado por JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    const initSpinner = document.getElementById('lotes-init-spinner');
    const viewContent = document.getElementById('lotes-view-content');

    const selectMat = document.getElementById('lote-material');
    const selectProv = document.getElementById('lote-proveedor');

    let lotesList = [];

    try {
        const catalogs = await api.getCatalogs();

        catalogs.materiales.forEach(mat => {
            const opt = document.createElement('option');
            opt.value = mat.id;
            opt.innerText = `${mat.sku_descripcion} (${mat.categoria} - ${mat.unidad_medida})`;
            selectMat.appendChild(opt);
        });

        catalogs.proveedores.forEach(prov => {
            const opt = document.createElement('option');
            opt.value = prov.id;
            opt.innerText = prov.nombre;
            selectProv.appendChild(opt);
        });

        initSpinner.style.display = 'none';
        viewContent.style.display = 'block';

        await loadLotesTable();

    } catch (error) {
        showToast('Error al inicializar la pantalla de lotes: ' + error.message, 'error');
    }

    const form = document.getElementById('create-lote-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const loteData = {
            id_caso: document.getElementById('lote-id').value.trim(),
            id_material: parseInt(selectMat.value),
            cantidad: parseInt(document.getElementById('lote-cantidad').value),
            id_proveedor: parseInt(selectProv.value),
            costo_lote_soles: parseFloat(document.getElementById('lote-costo').value),
            prioridad_produccion: document.getElementById('lote-prioridad').value
        };

        try {
            const res = await api.createLote(loteData);
            if (res.success) {
                showToast(res.message, 'success');
                form.reset();
                await loadLotesTable();
            }
        } catch (error) {
            showToast(error.message || 'Error al guardar el lote.', 'error');
        }
    });

    async function loadLotesTable() {
        const tbody = document.getElementById('lotes-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center;">Cargando catálogo...</td>
            </tr>
        `;

        try {
            lotesList = await api.getLotes();
            renderLotesRows(lotesList);
        } catch (error) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: var(--error);">Error al cargar lotes: ${error.message}</td>
                </tr>
            `;
        }
    }

    function renderLotesRows(list) {
        const tbody = document.getElementById('lotes-table-body');
        if (list.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: var(--text-muted);">No hay lotes en vivo registrados aún.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = list.map(l => {
            const badgeClass = l.prioridad_produccion === 'Urgente' ? 'badge-error'
                : l.prioridad_produccion === 'Alta' ? 'badge-warning' : 'badge-success';
            return `
                <tr>
                    <td style="font-weight: 700; color: var(--primary);">${l.id_caso}</td>
                    <td>
                        <div style="font-weight: 600;">${l.sku_descripcion}</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">${l.categoria}</div>
                    </td>
                    <td>${l.cantidad} <span style="font-size: 0.8rem; color: var(--text-muted);">${l.unidad_medida}</span></td>
                    <td>${l.proveedor}</td>
                    <td>S/. ${l.costo_lote_soles.toFixed(2)}</td>
                    <td><span class="badge ${badgeClass}">${l.prioridad_produccion}</span></td>
                </tr>
            `;
        }).join('');
    }

    const searchInput = document.getElementById('lotes-search-input');
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase().trim();
        const filtered = lotesList.filter(l =>
            l.id_caso.toLowerCase().includes(query) ||
            l.sku_descripcion.toLowerCase().includes(query) ||
            l.proveedor.toLowerCase().includes(query)
        );
        renderLotesRows(filtered);
    });

    const injectBtn = document.getElementById('btn-inject-simulated');
    injectBtn.addEventListener('click', async () => {
        if (!confirm('¿Estás seguro de inyectar aproximadamente 1000 eventos distribuidos en múltiples lotes aleatorios?')) return;
        injectBtn.disabled = true;
        injectBtn.innerText = 'Inyectando... ⏳';
        try {
            const res = await api.injectSimulationData();
            if (res.success) {
                showToast(res.message, 'success');
                await loadLotesTable();
            }
        } catch (error) {
            showToast(error.message || 'Error al inyectar simulación.', 'error');
        } finally {
            injectBtn.disabled = false;
            injectBtn.innerText = '⚡ Simular Datos (1000 Eventos)';
        }
    });
}
