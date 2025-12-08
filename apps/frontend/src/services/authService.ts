import { api } from '@/lib/api';
import { API_ENDPOINTS } from '@/lib/apiEndpoints';
import type { LoginRequest, RegisterRequest, TokenResponse } from '@/types/auth';

export const authService = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>(
      API_ENDPOINTS.AUTH_LOGIN,
      credentials
    );
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>(
      API_ENDPOINTS.AUTH_REGISTER,
      data
    );
    return response.data;
  },
};
