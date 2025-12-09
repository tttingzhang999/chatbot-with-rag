import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  PromptProfile,
  ProfileSummary,
  ProfileCreateRequest,
  ProfileUpdateRequest,
} from '@/types/profile';
import { profileService } from '@/services/profileService';

// Import queryClient to invalidate queries
let queryClientInstance: any = null;

export function setQueryClient(queryClient: any) {
  queryClientInstance = queryClient;
}

interface ProfileState {
  profiles: ProfileSummary[];
  currentProfile: PromptProfile | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchProfiles: () => Promise<void>;
  fetchDefaultProfile: () => Promise<void>;
  setCurrentProfile: (profileId: string) => Promise<void>;
  createProfile: (data: ProfileCreateRequest) => Promise<PromptProfile>;
  updateProfile: (profileId: string, data: ProfileUpdateRequest) => Promise<PromptProfile>;
  deleteProfile: (profileId: string) => Promise<void>;
  setDefaultProfile: (profileId: string) => Promise<void>;
  clearError: () => void;
}

export const useProfileStore = create<ProfileState>()(
  persist(
    (set, get) => ({
      profiles: [],
      currentProfile: null,
      isLoading: false,
      error: null,

      fetchProfiles: async () => {
        set({ isLoading: true, error: null });
        try {
          const profiles = await profileService.getProfiles();
          set({ profiles, isLoading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch profiles';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      fetchDefaultProfile: async () => {
        set({ isLoading: true, error: null });
        try {
          const profile = await profileService.getDefaultProfile();
          set({ currentProfile: profile, isLoading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch default profile';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      setCurrentProfile: async (profileId: string) => {
        set({ isLoading: true, error: null });
        try {
          const profile = await profileService.getProfileById(profileId);
          set({ currentProfile: profile, isLoading: false });

          // Invalidate queries to trigger refetch with new profile filter
          if (queryClientInstance) {
            queryClientInstance.invalidateQueries({ queryKey: ['conversations'] });
            queryClientInstance.invalidateQueries({ queryKey: ['documents'] });
          }
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to set current profile';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      createProfile: async (data: ProfileCreateRequest) => {
        set({ isLoading: true, error: null });
        try {
          const profile = await profileService.createProfile(data);

          // Refresh profiles list
          const profiles = await profileService.getProfiles();
          set({ profiles, isLoading: false });

          return profile;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to create profile';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      updateProfile: async (profileId: string, data: ProfileUpdateRequest) => {
        set({ isLoading: true, error: null });
        try {
          const profile = await profileService.updateProfile(profileId, data);

          // Update current profile if it's the one being updated
          const { currentProfile } = get();
          if (currentProfile?.id === profileId) {
            set({ currentProfile: profile });
          }

          // Refresh profiles list
          const profiles = await profileService.getProfiles();
          set({ profiles, isLoading: false });

          return profile;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to update profile';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      deleteProfile: async (profileId: string) => {
        set({ isLoading: true, error: null });
        try {
          await profileService.deleteProfile(profileId);

          // Refresh profiles list
          const profiles = await profileService.getProfiles();
          set({ profiles, isLoading: false });

          // If deleted profile was current, switch to default
          const { currentProfile } = get();
          if (currentProfile?.id === profileId) {
            await get().fetchDefaultProfile();
          }
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to delete profile';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      setDefaultProfile: async (profileId: string) => {
        set({ isLoading: true, error: null });
        try {
          await profileService.setDefaultProfile(profileId);

          // Refresh profiles list to update is_default flags
          const profiles = await profileService.getProfiles();
          set({ profiles, isLoading: false });

          // Update current profile
          await get().setCurrentProfile(profileId);
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to set default profile';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'profile-storage',
      partialize: (state) => ({
        currentProfile: state.currentProfile,
      }),
    }
  )
);
