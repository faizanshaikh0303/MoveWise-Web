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
  
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        try {
          set({ isLoading: true, error: null });
          const response = await authAPI.login({ email, password });
          
          localStorage.setItem('token', response.access_token);
          
          const user = await authAPI.getCurrentUser();
          
          set({
            token: response.access_token,
            user,
            isAuthenticated: true,
            isLoading: false,
          });
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
          const response = await authAPI.register({ email, password, name });
          
          localStorage.setItem('token', response.access_token);
          
          const user = await authAPI.getCurrentUser();
          
          set({
            token: response.access_token,
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Registration failed',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        });
      },

      fetchUser: async () => {
        try {
          const token = localStorage.getItem('token');
          if (!token) return;

          const user = await authAPI.getCurrentUser();
          set({ user, isAuthenticated: true, token });
        } catch (error) {
          localStorage.removeItem('token');
          set({ token: null, user: null, isAuthenticated: false });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);