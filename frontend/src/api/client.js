// frontend/src/api/client.js
export const API = {
    base: '/api/v1',
    
    // Получение токена
    getToken() {
        return localStorage.getItem('seo_token');
    },
    
    // Базовый запрос
    async request(endpoint, options = {}) {
        const token = this.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${this.base}${endpoint}`, {
            ...options,
            headers
        });
        
        // Обработка 401/403
        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('seo_token');
            window.location.hash = 'login';
            throw new Error('Сессия истекла');
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail?.message || `HTTP ${response.status}`);
        }
        
        return response.json();
    },
    
    // GET-запрос
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    // POST-запрос
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // PUT-запрос
    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    // DELETE-запрос
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};
