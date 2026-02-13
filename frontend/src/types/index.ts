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

// Analysis types - UPDATED for new components

export interface AnalysisRequest {
  current_address: string;
  destination_address: string;
}

// Crime Data - Enhanced
export interface CrimeData {
  current: {
    total_crimes: number;
    daily_average: number;
    crime_rate: number;
    safety_score: number;
    categories?: {
      violent?: number;
      property?: number;
      theft?: number;
      vandalism?: number;
    };
    temporal_analysis?: {
      hourly_distribution?: number[];
      peak_hours?: string[];
      crimes_during_sleep_hours?: number;
      crimes_during_work_hours?: number;
      crimes_during_commute?: number;
    };
    data_source?: string;
  };
  destination: {
    total_crimes: number;
    daily_average: number;
    crime_rate: number;
    safety_score: number;
    categories?: {
      violent?: number;
      property?: number;
      theft?: number;
      vandalism?: number;
    };
    temporal_analysis?: {
      hourly_distribution?: number[];
      peak_hours?: string[];
      crimes_during_sleep_hours?: number;
      crimes_during_work_hours?: number;
      crimes_during_commute?: number;
    };
    data_source?: string;
  };
  comparison: {
    crime_change_percent: number;
    is_safer: boolean;
    score_difference: number;
    recommendation: string;
  };
}

// Amenities Data - Enhanced
export interface AmenitiesData {
  current_amenities: Record<string, number>;
  destination_amenities: Record<string, number>;
  destination_locations: Record<string, Array<{
    name: string;
    lat: number;
    lng: number;
    type: string;
    address?: string;
  }>>;
  destination_lat: number;
  destination_lng: number;
  current_lat?: number;
  current_lng?: number;
  destination: {
    total_count: number;
    by_type: Record<string, number>;
  };
  current: {
    total_count: number;
    by_type: Record<string, number>;
  };
  comparison_text: string;
  search_radius?: string;
  note?: string;
  same_location?: boolean;
}

// Cost Data - Enhanced
export interface CostData {
  current: {
    total_monthly: number;
    total_annual: number;
    affordability_score: number;
    housing?: {
      monthly_rent: number;
    };
    expenses?: {
      utilities: number;
      groceries: number;
      transportation: number;
      healthcare: number;
      entertainment: number;
      miscellaneous: number;
    };
    cost_index?: number;
    data_source?: string;
  };
  destination: {
    total_monthly: number;
    total_annual: number;
    affordability_score: number;
    housing?: {
      monthly_rent: number;
    };
    expenses?: {
      utilities: number;
      groceries: number;
      transportation: number;
      healthcare: number;
      entertainment: number;
      miscellaneous: number;
    };
    cost_index?: number;
    data_source?: string;
  };
  comparison: {
    monthly_difference: number;
    annual_difference: number;
    percent_change: number;
    is_more_expensive: boolean;
    score_difference: number;
    recommendation: string;
  };
}

// Noise Data - Enhanced
export interface NoiseData {
  current: {
    estimated_db: number;
    noise_score: number;
    noise_category: string;
    description?: string;
    road_breakdown?: Record<string, number>;
    dominant_noise_source?: string;
    indicators?: string[];
  };
  destination: {
    estimated_db: number;
    noise_score: number;
    noise_category: string;
    description?: string;
    road_breakdown?: Record<string, number>;
    dominant_noise_source?: string;
    indicators?: string[];
    recommendations?: string[];
  };
  comparison: {
    db_difference: number;
    is_quieter: boolean;
    category_change: string;
    score_difference: number;
    recommendation: string;
    preference_match?: {
      is_good_match: boolean;
      reason?: string;
    };
  };
}

// Commute Data - Enhanced
export interface CommuteData {
  duration_minutes?: number;
  method?: string;
  distance?: string;
  description?: string;
}

// Full Analysis - Enhanced
export interface Analysis {
  id: number;
  current_address: string;
  destination_address: string;
  
  // Scores
  overall_score: number;
  safety_score: number;
  affordability_score: number;
  environment_score: number;
  lifestyle_score: number;
  convenience_score: number;
  
  // Data sections
  crime_data: CrimeData | null;
  amenities_data: AmenitiesData | null;
  cost_data: CostData | null;
  noise_data: NoiseData | null;
  commute_data: CommuteData | null;
  
  // AI insights
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