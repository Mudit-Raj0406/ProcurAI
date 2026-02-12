import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Attach auth token to every request automatically
api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

// Auto-redirect to login on 401 (stale/invalid token)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            // Only redirect if not already on login page
            if (!window.location.pathname.includes('/login')) {
                localStorage.removeItem('token');
                localStorage.removeItem('role');
                localStorage.removeItem('email');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
