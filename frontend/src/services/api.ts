/**
 * Centralized REST API Client for Smart Pantry Management System.
 * Pure HTTP async client consuming environment-configured VITE_API_BASE_URL.
 * No SQLite, No local Python dependencies, 100% Netlify compatible.
 */

const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim() !== '') {
    return envUrl.replace(/\/$/, '');
  }
  return 'http://127.0.0.1:8000';
};

const API_BASE = getApiBase();

export interface Item {
  id: number;
  name: string;
  unit: string;
  initial_quantity: number;
  current_quantity: number;
  minimum_quantity: number;
  high_intake_threshold: number;
  availability_status: 'AVAILABLE' | 'LOW' | 'UNAVAILABLE';
  intake_status: 'NORMAL' | 'HIGH' | 'INSUFFICIENT_DATA';
  average_daily_intake: number | null;
  remaining_days: number | null;
  category?: string;
  rfid_uid?: string | null;
  storage_location?: string;
  calories_per_100g?: number;
  carbs_per_100g?: number;
  protein_per_100g?: number;
  fat_per_100g?: number;
  sugar_per_100g?: number;
  sodium_per_100g?: number;
  fiber_per_100g?: number;
  updated_at?: string;
}

export interface DashboardSummary {
  items: Item[];
  total_items: number;
  available_count: number;
  low_count: number;
  unavailable_count: number;
  high_intake_count: number;
}

export interface HouseholdProfile {
  id: number;
  household_name: string;
  family_size: number;
  adults_count: number;
  children_count: number;
  elderly_count: number;
  activity_profile?: string;
  dietary_preference?: string;
  adults?: number;
  children?: number;
  elderly?: number;
  daily_calorie_target?: number | null;
  dietary_preferences?: string[] | null;
  dietary_goal?: string | null;
  notes?: string | null;
}

export interface Prediction {
  item_id: number;
  item_name: string;
  current_quantity: number;
  historical_average_daily: number | null;
  predicted_daily_consumption: number;
  prediction_range_90_low: number;
  prediction_range_90_high: number;
  predicted_7d_consumption: number;
  predicted_14d_consumption: number;
  predicted_30d_consumption: number;
  remaining_days_math: number | null;
  remaining_days_ml: number | null;
  predicted_depletion_date: string | null;
  model_used: string;
}

export interface MacroNutrients {
  calories_kcal: number;
  carbohydrates_g: number;
  protein_g: number;
  fat_g: number;
  sugar_g: number;
  sodium_mg: number;
  fiber_g: number;
}

export interface DietSummary {
  disclaimer: string;
  period: string;
  days_analyzed: number;
  tracked_pantry_intake: MacroNutrients;
  manual_logged_intake: MacroNutrients;
  total_combined_intake: MacroNutrients;
  dietary_pattern: string;
  dietary_pattern_description: string;
}

export interface MealLog {
  id: number;
  meal_name: string;
  meal_type?: string;
  calories: number;
  carbohydrates: number;
  protein: number;
  fat: number;
  sugar: number;
  sodium: number;
  fiber: number;
  timestamp: string;
}

export interface RecipeIngredient {
  item_name: string;
  scaled_quantity: number;
  unit: string;
  is_in_stock: boolean;
  current_stock: number | null;
}

export interface Recipe {
  id: number;
  name: string;
  category: string;
  cuisine: string;
  base_servings: number;
  target_servings: number;
  description: string;
  prep_time_minutes: number;
  cook_time_minutes: number;
  instructions: string;
  estimated_calories_per_serving: number;
  tags: string[];
  ingredients: RecipeIngredient[];
}

export interface RecipeRecommendations {
  household_id: number;
  family_size: number;
  ready_to_cook: Recipe[];
  missing_ingredients: Recipe[];
  pantry_clearers: Recipe[];
  healthier_alternatives: Recipe[];
}

export interface ShoppingItem {
  id: number;
  household_id: number;
  item_id: number;
  item_name: string;
  suggested_quantity: number;
  current_quantity: number;
  unit: string;
  priority: 'URGENT' | 'HIGH' | 'MEDIUM' | 'LOW';
  reason: string;
  status: 'PENDING' | 'PURCHASED';
  predicted_depletion_days: number | null;
  created_at: string;
  updated_at: string;
}

export interface AlertLog {
  id: number;
  alert_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  title: string;
  message: string;
  item_id?: number | null;
  item_name?: string | null;
  created_at: string;
  is_resolved: boolean;
  resolved_at?: string | null;
}

export interface RegressionBenchmark {
  model_name: string;
  mae: number;
  rmse: number;
  r2: number;
  is_baseline: boolean;
}

export interface MLEvaluation {
  notice: string;
  dataset_size_records: number;
  train_size: number;
  val_size: number;
  test_size: number;
  regression_benchmarks: RegressionBenchmark[];
  classification_metrics: {
    accuracy: number;
    macro_precision: number;
    macro_recall: number;
    macro_f1: number;
    classes: string[];
    confusion_matrix: number[][];
  };
  feature_importance: Record<string, number>;
}

export interface ConsumptionRecord {
  id: number;
  item_id: number;
  timestamp: string;
  previous_weight: number;
  current_weight: number;
  consumption: number;
  refill_amount: number;
}

export interface ItemConsumptionHistory {
  item_id: number;
  item_name: string;
  unit: string;
  current_weight: number;
  initial_capacity: number;
  total_consumption: number;
  total_refill: number;
  days_with_data: number;
  records: ConsumptionRecord[];
}

// ==========================================
// Centralized Fetch Helper
// ==========================================

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`API Error ${res.status}: ${errText || res.statusText}`);
    }
    return await res.json() as T;
  } catch (err: any) {
    console.error(`Request to ${url} failed:`, err);
    throw err;
  }
}

// ==========================================
// API Client Methods
// ==========================================

export const api = {
  // System Health
  getHealth: () => request<{ status: string; service: string; version: string }>('/health'),

  // Dashboard & Items
  getDashboardSummary: () => request<DashboardSummary>('/dashboard'),
  getItems: () => request<Item[]>('/items'),
  getItemDetail: (id: number) => request<Item & { recent_weight_history?: Array<{ id: number; weight: number; timestamp: string }> }>(`/items/${id}`),
  getItemConsumption: (id: number) => request<ItemConsumptionHistory>(`/items/${id}/consumption`),
  postWeightReading: (itemId: number, weight: number) =>
    request<{ status: string; weight: number }>(`/items/${itemId}/weight`, {
      method: 'POST',
      body: JSON.stringify({ weight }),
    }),

  // Household Profile
  getHousehold: () => request<HouseholdProfile>('/household'),
  updateHousehold: (data: Partial<HouseholdProfile>) =>
    request<HouseholdProfile>('/household', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // ML Predictions
  getPredictions: () => request<Prediction[]>('/predictions'),
  getPredictionForItem: (id: number) => request<Prediction>(`/predictions/${id}`),

  // Nutrition & Meals
  getDietSummary: (period = 'today') => request<DietSummary>(`/diet/summary?period=${period}`),
  getDietTrends: () => request<Array<{ date: string; calories: number; carbohydrates: number; protein: number; fat: number; sugar: number; sodium: number }>>('/diet/trends'),
  logMeal: (meal: Omit<MealLog, 'id' | 'timestamp'>) =>
    request<MealLog>('/meals', {
      method: 'POST',
      body: JSON.stringify(meal),
    }),
  getMealLogs: () => request<MealLog[]>('/meals'),

  // Recipes
  getRecipeRecommendations: () => request<RecipeRecommendations>('/recipes/recommendations'),

  // Shopping List
  getShoppingList: () => request<ShoppingItem[]>('/shopping-list'),
  generateShoppingList: () =>
    request<{ status: string; count: number }>('/shopping-list/generate', { method: 'POST' }),
  
  // NOTE: Mark as Purchased changes status only (record_refill=false per business logic correction)
  markShoppingItemPurchased: (id: number) =>
    request<{ status: string; message: string }>(`/shopping-list/${id}/purchase?record_refill=false`, {
      method: 'POST',
    }),

  // Separate Restock Action to update pantry container stock
  restockPantryFromShopping: async (itemId: number, restockGrams: number) => {
    // Read current weight and add the restock quantity
    const detail = await api.getItemDetail(itemId);
    const newWeight = (detail.current_quantity || 0) + restockGrams;
    return api.postWeightReading(itemId, newWeight);
  },

  // Alerts
  getAlerts: (unresolvedOnly = false) =>
    request<AlertLog[]>(`/alerts?unresolved_only=${unresolvedOnly}`),
  resolveAlert: (id: number) =>
    request<{ status: string; message: string }>(`/alerts/${id}/resolve`, { method: 'POST' }),

  // ML Evaluation
  getMLEvaluation: () => request<MLEvaluation>('/ml/evaluation'),

  // Simulation
  simulateAdvanceDays: (numDays: number) =>
    request<{ status: string; days_advanced: number; readings_logged: number }>(`/simulation/simulate-days?num_days=${numDays}`, {
      method: 'POST',
    }),
  resetDemoDatabase: () =>
    request<{ status: string; message: string }>('/simulation/reset', { method: 'POST' }),
};
