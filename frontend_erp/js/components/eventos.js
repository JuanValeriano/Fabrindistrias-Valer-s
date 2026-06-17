import { api } from '../api.js';

export async function renderEventos(container, showToast) {
    container.innerHTML = `
        <div class="spinner-container" id="eventos-init-spinner">
            <div class="spinner"></div>
            <span class="spinner-text">Cargando catálogos de base de datos...</span>
        </div>
        
        <div id="eventos-view-content" style="display: none;">
            <h1>🔄 Registro de Eventos</h1>
            <p class="subtitle">Registra el avance físico de los lotes y audita su trazabilidad histórica en tiempo real.</p>
            
            <div class="split-layout">
                <!-- Columna Izquierda: Formulario de Registro -->
                <div class="split-form">
                    <div class="card">
                        <h3>Registrar Evento Operativo</h3>
                        <form id="create-event-form" style="margin-top: 1rem;">
                            <div class="form-group">
                                <label for="event-lote">Lote a Registrar</label>
                                <select id="event-lote" required>
                                    <option value="">Selecciona un lote...</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="event-actividad">Actividad / Paso Operativo</label>
                                <select id="event-actividad" required>
                                    <option value="">Selecciona una actividad...</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="event-empleado">Operario (Empleado)</label>
                                <select id="event-empleado" required>
                                    <option value="">Selecciona un operario...</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="event-calidad">Control de Calidad (QA Status)</label>
                                <select id="event-calidad" required>
                                    <option value="Pendiente">Pendiente (Por Defecto)</option>
                                    <option value="Aprobado">Aprobado</option>
                                    <option value="Rechazado">Rechazado</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="event-ubicacion">Ubicación Física Actual</label>
                                <select id="event-ubicacion" required>
                                    <option value="">Selecciona una ubicación...</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="event-time">Fecha y Hora de Registro</label>
                                <input type="datetime-local" id="event-time" required>
                            </div>
                            
                            <button type="submit" class="btn btn-primary btn-block" style="margin-top: 1rem;">
                                Registrar Evento 🚀
                            </button>
                        </form>
                    </div>
                </div>
                
                <!-- Columna Derecha: Trazabilidad y Línea de Tiempo -->
                <div class="split-view">
                    <div class="card" style="min-height: 500px;">
                        <h3>Línea de Tiempo del Lote (Trazabilidad)</h3>
                        <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;" id="timeline-lote-desc">
                            Selecciona un lote para auditar el historial de movimientos.
                        </p>
                        
                        <div id="timeline-viewport" class="timeline-container">
                            <div style="text-align: center; color: var(--text-muted); padding: 4rem 1rem;">
                                📅 Selecciona un lote a la izquierda para cargar su línea de tiempo.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    const initSpinner = document.getElementById('eventos-init-spinner');
    const viewContent = document.getElementById('eventos-view-content');

    const selectLote = document.getElementById('event-lote');
    const selectAct = document.getElementById('event-actividad');
    const selectEmp = document.getElementById('event-empleado');
    const selectLoc = document.getElementById('event-ubicacion');
    const selectCal = document.getElementById('event-calidad');

    const tzoffset = (new Date()).getTimezoneOffset() * 60000;
    const localISOTime = (new Date(Date.now() - tzoffset)).toISOString().slice(0, 16);
    document.getElementById('event-time').value = localISOTime;

    try {
        const catalogs = await api.getCatalogs();

        catalogs.actividades.forEach(act => {
            const opt = document.createElement('option');
            opt.value = act.id;
            opt.innerText = act.nombre;
            selectAct.appendChild(opt);
        });

        catalogs.empleados.forEach(emp => {
            const opt = document.createElement('option');
            opt.value = emp.id;
            opt.innerText = `${emp.nombre} (${emp.rol} - ${emp.turno})`;
            selectEmp.appendChild(opt);
        });

        catalogs.ubicaciones.forEach(loc => {
            const opt = document.createElement('option');
            opt.value = loc.id;
            opt.innerText = loc.nombre;
            selectLoc.appendChild(opt);
        });

        await reloadLotesList();

        initSpinner.style.display = 'none';
        viewContent.style.display = 'block';

    } catch (error) {
        showToast('Error al cargar la pantalla de eventos: ' + error.message, 'error');
    }

    selectLote.addEventListener('change', () => {
        const idCaso = selectLote.value;
        loadTimeline(idCaso);
    });

    const form = document.getElementById('create-event-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const idCaso = selectLote.value;
        const payload = {
            id_caso: idCaso,
            id_actividad: parseInt(selectAct.value),
            timestamp: document.getElementById('event-time').value,
            id_empleado: parseInt(selectEmp.value),
            estado_calidad: selectCal.value,
            id_ubicacion: parseInt(selectLoc.value)
        };

        try {
            const res = await api.createEvento(payload);
            if (res.success) {
                showToast(res.message, 'success');
                selectAct.value = '';
                await loadTimeline(idCaso);
            }
        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    async function reloadLotesList() {
        const selectedVal = selectLote.value;
        selectLote.innerHTML = '<option value="">Selecciona un lote...</option>';
        try {
            const lotes = await api.getLotes();
            lotes.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id_caso;
                opt.innerText = `${l.id_caso} - ${l.sku_descripcion} (${l.proveedor})`;
                if (l.id_caso === selectedVal) opt.selected = true;
                selectLote.appendChild(opt);
            });
        } catch (err) {
            console.error('Error cargando lotes desplegables:', err);
        }
    }

    async function loadTimeline(idCaso) {
        const timelineViewport = document.getElementById('timeline-viewport');
        const descText = document.getElementById('timeline-lote-desc');

        if (!idCaso) {
            descText.innerText = 'Selecciona un lote para auditar el historial de movimientos.';
            timelineViewport.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 4rem 1rem;">
                    📅 Selecciona un lote a la izquierda para cargar su línea de tiempo.
                </div>
            `;
            return;
        }

        descText.innerText = `Mostrando auditoría del lote ${idCaso}.`;
        timelineViewport.innerHTML = `
            <div class="spinner-container" style="padding: 2rem 0;">
                <div class="spinner" style="width: 25px; height: 25px;"></div>
                <span class="spinner-text" style="font-size: 0.8rem;">Cargando trazabilidad...</span>
            </div>
        `;

        try {
            const events = await api.getTrazabilidad(idCaso);

            if (events.length === 0) {
                timelineViewport.innerHTML = `
                    <div style="text-align: center; color: var(--text-muted); padding: 4rem 1rem;">
                        ⚠️ Este lote no tiene eventos registrados. Registra el paso 'Recepción en Puerta' para comenzar.
                    </div>
                `;
                return;
            }

            let timelineHtml = '<div class="timeline">';

            events.forEach(ev => {
                let badgeClass = 'badge-info';
                let itemClass = '';

                if (ev.estado_calidad === 'Aprobado') {
                    badgeClass = 'badge-success';
                    itemClass = 'completed';
                } else if (ev.estado_calidad === 'Rechazado') {
                    badgeClass = 'badge-error';
                    itemClass = 'rejected';
                } else if (ev.estado_calidad === 'Pendiente') {
                    badgeClass = 'badge-warning';
                }

                timelineHtml += `
                    <div class="timeline-item ${itemClass}">
                        <div class="timeline-date">${ev.timestamp}</div>
                        <div class="timeline-title">${ev.actividad}</div>
                        <div class="timeline-detail">
                            <span class="timeline-meta-badge">📍 ${ev.ubicacion}</span>
                            <span class="timeline-meta-badge">👤 ${ev.empleado} (${ev.rol})</span>
                            <span class="badge ${badgeClass}">${ev.estado_calidad}</span>
                        </div>
                    </div>
                `;
            });

            timelineHtml += '</div>';
            timelineViewport.innerHTML = timelineHtml;

        } catch (error) {
            timelineViewport.innerHTML = `
                <div style="text-align: center; color: var(--error); padding: 4rem 1rem;">
                    Error al consultar trazabilidad: ${error.message}
                </div>
            `;
        }
    }
}
