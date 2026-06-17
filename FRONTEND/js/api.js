const API_BASE_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' || window.location.protocol === 'file:')
    ? 'http://127.0.0.1:8000'
    : 'https://juanvaleriano-valers-pm-backend.hf.space';

async function request(path, options = {}) {
    const url = `${API_BASE_URL}${path}`;

    options.headers = {
        ...options.headers,
    };

    if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Error en la petición' }));
            throw new Error(errorData.detail || 'Ocurrió un error en el servidor');
        }
        return await response.json();
    } catch (error) {
        console.error(`API Error on ${url}:`, error);
        throw error;
    }
}

export const api = {
    login: async (usuario, password) => {
        return request('/api/auth/login', {
            method: 'POST',
            body: { usuario, password }
        });
    },

    changePassword: async (usuario, pass_actual, pass_nueva) => {
        return request('/api/auth/change-password', {
            method: 'POST',
            body: { usuario, pass_actual, pass_nueva }
        });
    },

    getUsers: async () => {
        return request('/api/users');
    },

    createUser: async (usuario, password, rol) => {
        return request('/api/users', {
            method: 'POST',
            body: { usuario, password, rol }
        });
    },

    deleteUser: async (usuario) => {
        return request(`/api/users/${usuario}`, {
            method: 'DELETE'
        });
    },

    getSlaMeta: async () => {
        return request('/api/config/meta');
    },

    updateSlaMeta: async (meta_horas) => {
        return request('/api/config/meta', {
            method: 'POST',
            body: { meta_horas }
        });
    },

    uploadFile: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return request('/api/analysis/upload', {
            method: 'POST',
            body: formData
        });
    },

    getHistory: async () => {
        return request('/api/analysis/history');
    },

    queryAnalysis: async (id_ejecucion, filters) => {
        return request(`/api/analysis/query/${id_ejecucion}`, {
            method: 'POST',
            body: filters
        });
    },

    getGraphUrl: (id_ejecucion, tipoGrafo, filters = {}) => {
        const params = new URLSearchParams();
        params.append('tipo_grafo', tipoGrafo);
        if (filters.f_inicio) params.append('f_inicio', filters.f_inicio);
        if (filters.f_fin) params.append('f_fin', filters.f_fin);
        if (filters.var_seleccionada) params.append('var_seleccionada', filters.var_seleccionada);
        if (filters.emps_seleccionados) {
            filters.emps_seleccionados.forEach(emp => {
                params.append('emps_seleccionados', emp);
            });
        }
        return `${API_BASE_URL}/api/analysis/graph/${id_ejecucion}?${params.toString()}`;
    },

    getGeminiInsights: async (data) => {
        return request('/api/analysis/gemini/insights', {
            method: 'POST',
            body: data
        });
    },

    getGeminiTrends: async (data) => {
        return request('/api/analysis/gemini/trends', {
            method: 'POST',
            body: data
        });
    },

    exportAnalysis: async (id_ejecucion, format, filters, insights) => {
        const url = `${API_BASE_URL}/api/analysis/export/${id_ejecucion}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                format,
                filters,
                insights
            })
        });
        if (!response.ok) {
            throw new Error('Error al exportar el reporte');
        }
        return await response.blob();
    }
};
