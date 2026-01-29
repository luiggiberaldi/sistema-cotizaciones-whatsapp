import axios from 'axios';
import { supabase } from '../lib/supabaseClient';

// Configuración de URL base de la API
// Forzamos el uso del proxy en desarrollo
const API_BASE_URL = '/api/v1';
// const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor para agregar el token de autenticación
api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// Interceptor para manejo de errores
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
    }
);

export const quotesAPI = {
    // Obtener todas las cotizaciones
    getAll: async () => {
        const response = await api.get('/quotes/');
        return response.data;
    },

    // Obtener cotización por ID
    getById: async (id) => {
        const response = await api.get(`/quotes/${id}`);
        return response.data;
    },

    // Crear cotización
    create: async (quoteData) => {
        const response = await api.post('/quotes', quoteData);
        return response.data;
    },

    // Eliminar cotización
    delete: async (id) => {
        const response = await api.delete(`/quotes/${id}`);
        return response.data;
    },
};

export const broadcastAPI = {
    // Enviar mensaje plantilla a múltiples clientes
    sendTemplate: async (clients, templateName, languageCode, parameters) => {
        const response = await api.post('/broadcast/send-template', {
            clients,
            template_name: templateName,
            language_code: languageCode,
            parameters,
        });
        return response.data;
    },
};

export const productsAPI = {
    getAll: async () => {
        const response = await api.get('/products/');
        return response.data;
    },
    create: async (product) => {
        const response = await api.post('/products/', product);
        return response.data;
    },
    update: async (id, product) => {
        const response = await api.put(`/products/${id}`, product);
        return response.data;
    },
    delete: async (id) => {
        const response = await api.delete(`/products/${id}`);
        return response.data;
    },
};

export const customersAPI = {
    getAll: async () => {
        const response = await api.get('/customers/');
        return response.data;
    },
    updateAddress: async (id, address) => {
        const response = await api.put(`/customers/${id}/address`, { main_address: address });
        return response.data;
    }
};

export const businessInfoAPI = {
    getBusinessInfo: async () => {
        try {
            const response = await api.get('/business-info/');
            return response.data;
        } catch (error) {
            console.error(error);
            throw error;
        }
    },

    updateBusinessInfo: async (updates) => {
        try {
            const response = await api.put('/business-info/', updates);
            return response.data;
        } catch (error) {
            console.error(error);
            throw error;
        }
    }
};

export default api;
