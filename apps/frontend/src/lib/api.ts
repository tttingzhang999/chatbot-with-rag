import axios from 'axios';

// Auto-detect backend URL based on current hostname
// If VITE_API_BASE_URL is set, use it (for production)
// Otherwise, use current hostname with port 8000 (for local development across devices)
const getApiBaseUrl = (): string => {
  // If explicit env var is set, use it
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // For local development: use current hostname with backend port
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
};

const API_BASE_URL = getApiBaseUrl();

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[API] Token attached to request:', config.url);
    } else {
      console.warn('[API] No token found for request:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
