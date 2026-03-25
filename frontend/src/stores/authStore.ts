import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { authAPI } from '@/services/api';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  hasHydrated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  setHasHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      hasHydrated: false,

      login: async (email, password) => {
        try {
          set({ isLoading: true, error: null });
          await authAPI.login({ email, password });
          const user = await authAPI.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Login failed',
            isLoading: false,
          });
          throw error;
        }
      },

      register: async (email, password, name) => {
        try {
          set({ isLoading: true, error: null });
          await authAPI.register({ email, password, name });
          const user = await authAPI.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Registration failed',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: () => {
        import('@/stores/analysisStore').then(({ useAnalysisStore }) => {
          useAnalysisStore.getState().clearAnalyses();
        });
        set({ token: null, user: null, isAuthenticated: false });
      },

      fetchUser: async () => {
        try {
          const user = await authAPI.getCurrentUser();
          set({ user, isAuthenticated: true });
        } catch (error: any) {
          if (error.response?.status === 401) {
            set({ token: null, user: null, isAuthenticated: false });
          }
        }
      },

      clearError: () => set({ error: null }),
      setHasHydrated: (hydrated) => set({ hasHydrated: hydrated }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);