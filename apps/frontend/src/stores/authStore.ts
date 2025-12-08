import { create } from 'zustand';
import type { User, LoginRequest, RegisterRequest } from '@/types/auth';
import { authService } from '@/services/authService';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login(credentials);
      localStorage.setItem('access_token', response.access_token);

      // Transform backend response to User object
      const user: User = {
        id: response.user_id,
        username: response.username,
        email: response.email,
      };
      localStorage.setItem('user', JSON.stringify(user));

      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  register: async (data: RegisterRequest) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.register(data);
      localStorage.setItem('access_token', response.access_token);

      // Transform backend response to User object
      const user: User = {
        id: response.user_id,
        username: response.username,
        email: response.email,
      };
      localStorage.setItem('user', JSON.stringify(user));

      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    set({
      user: null,
      isAuthenticated: false,
      error: null,
    });
  },

  checkAuth: () => {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({
          user,
          isAuthenticated: true,
        });
      } catch (error) {
        // Invalid user data, clear storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        set({
          user: null,
          isAuthenticated: false,
        });
      }
    }
  },

  clearError: () => set({ error: null }),
}));
