import { api } from '../api.js';

export function renderTabProcessMap(container, id_ejecucion, currentFilters, showToast, data) {
    const interpretationHtml = (data && data.interpretaciones && data.interpretaciones.mapa_procesos) ? `
        <div class="business-interpretation" style="margin-top: 1.5rem; padding: 1.25rem; background-color: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-left: 4px solid var(--primary); border-radius: 8px;">
            <h4 style="margin-top: 0; color: var(--primary-hover); display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">
                💡 Interpretación del Mapa de Procesos
            </h4>
            <p style="margin-bottom: 0; font-size: 0.95rem; line-height: 1.6; color: var(--text-main);">${data.interpretaciones.mapa_procesos}</p>
        </div>
    ` : '';

    container.innerHTML = `
        <div class="card" style="margin-top: 1rem;">
            <h3>🗺️ Descubrimiento del Flujo Real</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">
                Visualiza el modelo del proceso descubierto a partir del registro de eventos cargado.
            </p>
            
            <div class="graph-toggle-row">
                <label class="graph-toggle-item">
                    <input type="radio" name="graph-type-select" value="frecuencia" checked>
                    <span>Grafo de Frecuencias (Volumen)</span>
                </label>
                <label class="graph-toggle-item">
                    <input type="radio" name="graph-type-select" value="desempeño">
                    <span>Grafo de Desempeño (Tiempos - Cuellos de Botella)</span>
                </label>
            </div>
            
            <div class="graph-container" id="process-graph-viewport">
                <div class="spinner-container" id="graph-loading-spinner">
                    <div class="spinner"></div>
                    <span class="spinner-text">Generando modelo del proceso...</span>
                </div>
                <img id="process-graph-image" class="process-graph-img" style="display: none;" alt="Grafo de Procesos DFG">
            </div>
            
            <div id="graph-info-banner" class="alert alert-info" style="margin-top: 1.5rem; margin-bottom: 0;">
                <!-- Rellenado dinámicamente según el tipo de grafo -->
            </div>
            
            ${interpretationHtml}
        </div>
    `;

    const radioButtons = container.querySelectorAll('input[name="graph-type-select"]');
    const graphImg = container.querySelector('#process-graph-image');
    const loadingSpinner = container.querySelector('#graph-loading-spinner');
    const infoBanner = container.querySelector('#graph-info-banner');

    function updateGraph() {
        const selectedType = container.querySelector('input[name="graph-type-select"]:checked').value;

        loadingSpinner.style.display = 'flex';
        graphImg.style.display = 'none';

        const url = api.getGraphUrl(id_ejecucion, selectedType, currentFilters);
        graphImg.src = url;

        if (selectedType === 'desempeño') {
            infoBanner.innerHTML = `
                <h4>💡 Cómo leer el Grafo de Desempeño</h4>
                <p>Las flechas indican la dirección del flujo. Los números sobre las flechas muestran el <strong>tiempo promedio</strong> transcurrido entre las actividades. Las flechas más gruesas o de colores más intensos representan transiciones lentas; aquí es donde se encuentra el <strong>cuello de botella</strong> de tu proceso.</p>
            `;
        } else {
            infoBanner.innerHTML = `
                <h4>💡 Cómo leer el Grafo de Frecuencias</h4>
                <p>Los números muestran el número de veces que se realizó cada transición. Las líneas gruesas indican los caminos más recorridos de principio a fin.</p>
            `;
        }
    }

    graphImg.addEventListener('load', () => {
        loadingSpinner.style.display = 'none';
        graphImg.style.display = 'block';
    });

    graphImg.addEventListener('error', () => {
        loadingSpinner.style.display = 'none';
        showToast('Error al generar la visualización del grafo. Asegúrate de tener Graphviz instalado en el PATH del servidor.', 'error');
    });

    radioButtons.forEach(radio => {
        radio.addEventListener('change', updateGraph);
    });

    updateGraph();
}
