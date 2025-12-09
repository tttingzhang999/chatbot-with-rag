import { api } from '@/lib/api';
import { API_ENDPOINTS } from '@/lib/apiEndpoints';
import type {
  PromptProfile,
  ProfileSummary,
  ProfileCreateRequest,
  ProfileUpdateRequest,
} from '@/types/profile';

export const profileService = {
  /**
   * Get all profiles for current user
   */
  getProfiles: async (): Promise<ProfileSummary[]> => {
    const response = await api.get<ProfileSummary[]>(API_ENDPOINTS.PROFILES);
    return response.data;
  },

  /**
   * Get default profile for current user
   */
  getDefaultProfile: async (): Promise<PromptProfile> => {
    const response = await api.get<PromptProfile>(API_ENDPOINTS.PROFILES_DEFAULT);
    return response.data;
  },

  /**
   * Get profile details by ID
   */
  getProfileById: async (id: string): Promise<PromptProfile> => {
    const response = await api.get<PromptProfile>(API_ENDPOINTS.PROFILE_BY_ID(id));
    return response.data;
  },

  /**
   * Create a new profile
   */
  createProfile: async (data: ProfileCreateRequest): Promise<PromptProfile> => {
    const response = await api.post<PromptProfile>(API_ENDPOINTS.PROFILES, data);
    return response.data;
  },

  /**
   * Update an existing profile
   */
  updateProfile: async (id: string, data: ProfileUpdateRequest): Promise<PromptProfile> => {
    const response = await api.put<PromptProfile>(
      API_ENDPOINTS.PROFILE_BY_ID(id),
      data
    );
    return response.data;
  },

  /**
   * Delete a profile
   */
  deleteProfile: async (id: string): Promise<void> => {
    await api.delete(API_ENDPOINTS.PROFILE_BY_ID(id));
  },

  /**
   * Set profile as default
   */
  setDefaultProfile: async (id: string): Promise<void> => {
    await api.post(API_ENDPOINTS.PROFILE_SET_DEFAULT(id));
  },
};
