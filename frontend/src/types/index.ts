// User types
export interface User {
  id: number;
  email: string;
  name: string | null;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Profile types
export interface UserProfile {
  id: number;
  user_id: number;
  work_hours: string | null;
  work_address: string | null;
  commute_preference: string | null;
  sleep_hours: string | null;
  noise_preference: string | null;
  hobbies: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileData {
  work_hours?: string;
  work_address?: string;
  commute_preference?: string;
  sleep_hours?: string;
  noise_preference?: string;
  hobbies?: string[];
}

// Analysis types
export interface AnalysisRequest {
  current_address: string;
  destination_address: string;
}

export interface CrimeData {
  current_crime_rate: number;
  destination_crime_rate: number;
  comparison: string;
  data_source: string;
}

export interface AmenitiesData {
  current_amenities: Record<string, number>;
  destination_amenities: Record<string, number>;
  comparison_text: string;
}

export interface CostData {
  current_cost: number;
  destination_cost: number;
  change_percentage: number;
  monthly_difference: number;
  annual_difference: number;
  current_breakdown: Record<string, number>;
  destination_breakdown: Record<string, number>;
  tip: string;
  data_source: string;
}

export interface NoiseData {
  current_noise_level: string;
  current_score: number;
  current_description: string;
  current_indicators: string[];
  destination_noise_level: string;
  destination_score: number;
  destination_description: string;
  destination_indicators: string[];
  score_difference: number;
  impact: string;
  analysis: string;
  data_source: string;
}

export interface CommuteData {
  duration_minutes?: number;
  method?: string;
  distance?: string;
  description?: string;
}

export interface Analysis {
  id: number;
  current_address: string;
  destination_address: string;
  crime_data: CrimeData | null;
  amenities_data: AmenitiesData | null;
  cost_data: CostData | null;
  noise_data: NoiseData | null;
  commute_data: CommuteData | null;
  overview_summary: string | null;
  lifestyle_changes: string[] | null;
  ai_insights: string | null;
  created_at: string;
}

export interface AnalysisSummary {
  id: number;
  current_address: string;
  destination_address: string;
  created_at: string;
}