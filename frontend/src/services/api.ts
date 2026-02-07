import axios from 'axios';
import type {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  User,
  ProfileData,
  UserProfile,
  AnalysisRequest,
  Analysis,
  AnalysisSummary,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// Profile API
export const profileAPI = {
  get: async (): Promise<UserProfile | null> => {
    const response = await api.get<UserProfile>('/profile/');
    return response.data;
  },

  createOrUpdate: async (data: ProfileData): Promise<UserProfile> => {
    const response = await api.post<UserProfile>('/profile/', data);
    return response.data;
  },

  update: async (data: ProfileData): Promise<UserProfile> => {
    const response = await api.put<UserProfile>('/profile/', data);
    return response.data;
  },
};

// Analysis API
export const analysisAPI = {
  create: async (data: AnalysisRequest): Promise<Analysis> => {
    const response = await api.post<Analysis>('/analysis/', data);
    return response.data;
  },

  getAll: async (): Promise<AnalysisSummary[]> => {
    const response = await api.get<AnalysisSummary[]>('/analysis/');
    return response.data;
  },

  getById: async (id: number): Promise<Analysis> => {
    const response = await api.get<Analysis>(`/analysis/${id}`);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/analysis/${id}`);
  },
};

export default api;