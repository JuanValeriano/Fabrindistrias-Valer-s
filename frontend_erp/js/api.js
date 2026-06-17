const API_BASE_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' || window.location.protocol === 'file:')
    ? 'http://127.0.0.1:8001'
    : 'https://juanvaleriano-valers-erp-backend.hf.space';

async function request(path, options = {}) {
    const url = `${API_BASE_URL}${path}`;

    options.headers = {
        ...options.headers,
    };

    if (options.body && typeof options.body === 'object') {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Error en la petición' }));
            throw new Error(errorData.detail || 'Ocurrió un error en el servidor del ERP');
        }
        return await response.json();
    } catch (error) {
        console.error(`ERP API Error on ${url}:`, error);
        throw error;
    }
}

export const api = {
    login: async (usuario, password) => {
        return request('/api/erp/auth/login', {
            method: 'POST',
            body: { usuario, password }
        });
    },

    getCatalogs: async () => {
        return request('/api/erp/catalogos');
    },

    createLote: async (loteData) => {
        return request('/api/erp/lotes', {
            method: 'POST',
            body: loteData
        });
    },

    getLotes: async () => {
        return request('/api/erp/lotes');
    },

    getTrazabilidad: async (id_caso) => {
        return request(`/api/erp/lotes/${id_caso}/trazabilidad`);
    },

    createEvento: async (eventoData) => {
        return request('/api/erp/eventos', {
            method: 'POST',
            body: eventoData
        });
    },

    injectSimulationData: async () => {
        return request('/api/erp/simulation/inject', {
            method: 'POST'
        });
    }
};
