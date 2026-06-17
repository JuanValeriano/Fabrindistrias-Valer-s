import { api } from '../api.js';

export function renderSidebar(container, activeMenu, navigateTo, onUploadSuccess, onApplyFilters, currentFilters = null, metadata = null) {
    const usuario = sessionStorage.getItem('usuario_actual') || 'Usuario';
    const rol = sessionStorage.getItem('rol') || 'usuario';

    const menuItems = rol === 'admin'
        ? ["📜 Historial de Análisis", "⚙️ Panel de Administrador", "👤 Mi Perfil"]
        : ["📜 Historial de Análisis", "👤 Mi Perfil"];

    let sidebarHtml = `
        <div class="sidebar-header">
            <h2 class="sidebar-title">🧭 Valer's PM</h2>
        </div>
        <div class="user-badge">
            👤 Usuario: <strong>${usuario}</strong><br>
            Rol: <strong>${rol.charAt(0).toUpperCase() + rol.slice(1)}</strong>
        </div>
        
        <nav class="sidebar-menu">
            ${menuItems.map(item => `
                <button class="menu-item ${activeMenu === item ? 'active' : ''}" data-view="${item}">
                    ${item}
                </button>
            `).join('')}
            <button class="menu-item" id="btn-logout" style="margin-top: 1rem; border: 1px solid rgba(239, 68, 68, 0.2); color: var(--error);">
                🚪 Cerrar Sesión
            </button>
        </nav>
    `;

    if (activeMenu === '📊 Nuevo Análisis') {
        sidebarHtml += `
            <div class="filter-section">
                <div class="filter-group">
                    <label>📁 Carga de Datos</label>
                    <input type="file" id="analysis-file-input" accept=".csv,.xlsx,.xls" style="font-size: 0.85rem; padding: 0.5rem;">
                    <div id="file-info-label" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; display: none;"></div>
                </div>
                <button class="btn btn-primary btn-block" id="btn-save-analyze" disabled>
                    💾 Analizar y Guardar
                </button>
            </div>
        `;
    }

    if (activeMenu === '📜 Historial de Análisis') {
        sidebarHtml += `
            <div class="filter-section">
                <div class="filter-group">
                    <label>📥 Cargar Histórico</label>
                    <select id="select-history-analysis" class="form-control" style="font-size: 0.9rem;">
                        <option value="">Cargando historial...</option>
                    </select>
                </div>
                <button class="btn btn-primary btn-block" id="btn-load-history" disabled>
                    Cargar Análisis
                </button>
            </div>
        `;
    }

    const isAnalysisView = activeMenu === '📊 Nuevo Análisis' || activeMenu === '📜 Historial de Análisis';
    if (isAnalysisView && metadata) {
        const fInicio = currentFilters?.f_inicio || metadata.fecha_min;
        const fFin = currentFilters?.f_fin || metadata.fecha_max;
        const selectedVar = currentFilters?.var_seleccionada || 'Todas';
        const empsVal = currentFilters?.emps_seleccionados || metadata.empleados;

        sidebarHtml += `
            <div class="filter-section" id="data-filters-section">
                <label style="font-size: 0.9rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.25rem;">🔍 Filtros de Búsqueda</label>
                
                <div class="filter-group">
                    <label>📅 Rango de Fechas</label>
                    <div class="date-range-row">
                        <input type="date" id="filter-date-start" value="${fInicio}" min="${metadata.fecha_min}" max="${metadata.fecha_max}" style="padding: 0.5rem;">
                        <span>a</span>
                        <input type="date" id="filter-date-end" value="${fFin}" min="${metadata.fecha_min}" max="${metadata.fecha_max}" style="padding: 0.5rem;">
                    </div>
                </div>
                
                <div class="filter-group">
                    <label>🔄 Variantes de Proceso</label>
                    <select id="filter-variant" class="form-control" style="padding: 0.5rem; font-size: 0.9rem;">
                        <option value="Todas" ${selectedVar === 'Todas' ? 'selected' : ''}>Todas</option>
                        ${metadata.variantes.map(v => `
                            <option value="${v.id}" ${selectedVar === v.id ? 'selected' : ''}>${v.id}</option>
                        `).join('')}
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>👤 Filtrar por Empleado</label>
                    <input type="text" id="filter-employee-search" placeholder="Buscar..." style="padding: 0.5rem; font-size: 0.85rem; margin-bottom: 0.5rem;">
                    <div class="checkbox-list-container" id="employee-checkboxes-list">
                        <!-- Checkboxes cargados por JS -->
                    </div>
                </div>
                
                <button class="btn btn-primary btn-block" id="btn-apply-filters" style="margin-top: 0.5rem;">
                    Aplicar Filtros 🚀
                </button>
            </div>
        `;
    }

    container.innerHTML = sidebarHtml;

    container.querySelectorAll('.menu-item[data-view]').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetView = btn.getAttribute('data-view');
            navigateTo(targetView);
        });
    });

    document.getElementById('btn-logout').addEventListener('click', () => {
        sessionStorage.clear();
        navigateTo('login');
    });

    if (activeMenu === '📊 Nuevo Análisis') {
        const fileInput = document.getElementById('analysis-file-input');
        const saveBtn = document.getElementById('btn-save-analyze');
        const fileInfo = document.getElementById('file-info-label');

        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) {
                fileInfo.innerText = `Detectado: ${file.name}`;
                fileInfo.style.display = 'block';
                saveBtn.disabled = false;
            } else {
                fileInfo.style.display = 'none';
                saveBtn.disabled = true;
            }
        });

        saveBtn.addEventListener('click', async () => {
            const file = fileInput.files[0];
            if (file) {
                saveBtn.disabled = true;
                saveBtn.innerText = 'Cargando y procesando... ⏳';
                try {
                    const res = await api.uploadFile(file);
                    if (res.success) {
                        onUploadSuccess(res.id_ejecucion);
                    }
                } catch (error) {
                    alert(`Error al subir archivo: ${error.message}`);
                } finally {
                    saveBtn.disabled = false;
                    saveBtn.innerText = '💾 Analizar y Guardar';
                }
            }
        });
    }

    if (activeMenu === '📜 Historial de Análisis') {
        const selectHist = document.getElementById('select-history-analysis');
        const loadBtn = document.getElementById('btn-load-history');

        api.getHistory().then(history => {
            selectHist.innerHTML = '';
            if (history.length === 0) {
                selectHist.innerHTML = '<option value="">Sin análisis en historial</option>';
                return;
            }
            selectHist.innerHTML = '<option value="">Selecciona un análisis...</option>';
            history.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.id_ejecucion;
                opt.innerText = item.nombre_analisis;
                selectHist.appendChild(opt);
            });
        }).catch(err => {
            selectHist.innerHTML = '<option value="">Error al cargar historial</option>';
        });

        selectHist.addEventListener('change', () => {
            loadBtn.disabled = !selectHist.value;
        });

        loadBtn.addEventListener('click', () => {
            const idVal = selectHist.value;
            if (idVal) {
                onUploadSuccess(idVal);
            }
        });
    }

    if (isAnalysisView && metadata) {
        const searchInput = document.getElementById('filter-employee-search');
        const checkboxContainer = document.getElementById('employee-checkboxes-list');
        const applyBtn = document.getElementById('btn-apply-filters');

        const empsVal = currentFilters?.emps_seleccionados || metadata.empleados;

        function populateEmployees(filterText = '') {
            checkboxContainer.innerHTML = '';
            metadata.empleados.forEach(emp => {
                if (emp.toString().toLowerCase().includes(filterText.toLowerCase())) {
                    const isChecked = empsVal.includes(emp);
                    const label = document.createElement('label');
                    label.className = 'checkbox-item';
                    label.innerHTML = `
                        <input type="checkbox" class="emp-checkbox" value="${emp}" ${isChecked ? 'checked' : ''}>
                        <span>${emp}</span>
                    `;
                    checkboxContainer.appendChild(label);
                }
            });
        }

        searchInput.addEventListener('input', () => {
            populateEmployees(searchInput.value);
        });

        populateEmployees();

        applyBtn.addEventListener('click', () => {
            const startDate = document.getElementById('filter-date-start').value;
            const endDate = document.getElementById('filter-date-end').value;
            const variant = document.getElementById('filter-variant').value;

            const selectedEmps = [];
            checkboxContainer.querySelectorAll('.emp-checkbox:checked').forEach(chk => {
                selectedEmps.push(chk.value);
            });

            const filters = {
                f_inicio: startDate,
                f_fin: endDate,
                var_seleccionada: variant,
                emps_seleccionados: selectedEmps
            };

            onApplyFilters(filters);
        });
    }
}
