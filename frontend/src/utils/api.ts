import { isValidToken, logout } from './auth';
import config from '../config/environment';

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  success: boolean;
}

interface ApiConfig {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

const BASE_URL = config.API_URL;
const DEFAULT_TIMEOUT = config.API_TIMEOUT;
const DEFAULT_RETRIES = config.RETRY_ATTEMPTS;
const DEFAULT_RETRY_DELAY = 1000; // 1 second

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const sleep = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('token');
  return token && isValidToken(token)
    ? { 'Authorization': `Bearer ${token}` }
    : {};
};

const handleResponse = async <T>(response: Response): Promise<T> => {
  const contentType = response.headers.get('content-type');
  
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    
    try {
      if (contentType?.includes('application/json')) {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } else {
        errorMessage = await response.text() || errorMessage;
      }
    } catch {
      // Fallback to status text if parsing fails
      errorMessage = response.statusText || errorMessage;
    }

    // Handle authentication errors
    if (response.status === 401) {
      logout();
      throw new ApiError('Authentication required. Please log in again.', 401, 'UNAUTHORIZED');
    }

    throw new ApiError(errorMessage, response.status);
  }

  // Handle empty responses
  if (response.status === 204 || contentType === null) {
    return null as T;
  }

  // Parse JSON response
  if (contentType?.includes('application/json')) {
    return response.json();
  }

  // Return text for non-JSON responses
  return response.text() as T;
};

const makeRequest = async <T>(
  url: string,
  options: RequestInit = {},
  config: ApiConfig = {}
): Promise<T> => {
  const {
    timeout = DEFAULT_TIMEOUT,
    retries = DEFAULT_RETRIES,
    retryDelay = DEFAULT_RETRY_DELAY,
  } = config;

  const fullUrl = url.startsWith('http') ? url : `${BASE_URL}${url}`;
  
  const requestOptions: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
  };

  let lastError: Error = new Error('Request failed');

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(fullUrl, {
        ...requestOptions,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return await handleResponse<T>(response);
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry for certain errors
      if (error instanceof ApiError) {
        if (error.status === 401 || error.status === 403 || error.status === 404) {
          throw error;
        }
      }

      // Don't retry on the last attempt
      if (attempt === retries) {
        break;
      }

      // Wait before retrying
      await sleep(retryDelay * Math.pow(2, attempt)); // Exponential backoff
    }
  }

  throw lastError;
};

// Convenience methods
export const api = {
  get: <T>(url: string, config?: ApiConfig): Promise<T> =>
    makeRequest<T>(url, { method: 'GET' }, config),

  post: <T>(url: string, data?: any, config?: ApiConfig): Promise<T> =>
    makeRequest<T>(url, {
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data),
      headers: data instanceof FormData ? {} : { 'Content-Type': 'application/json' },
    }, config),

  put: <T>(url: string, data?: any, config?: ApiConfig): Promise<T> =>
    makeRequest<T>(url, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, config),

  patch: <T>(url: string, data?: any, config?: ApiConfig): Promise<T> =>
    makeRequest<T>(url, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }, config),

  delete: <T>(url: string, config?: ApiConfig): Promise<T> =>
    makeRequest<T>(url, { method: 'DELETE' }, config),
};

// Specific API methods for common operations
export const authApi = {
  login: (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return api.post<{ access_token: string; token_type: string }>('/login', formData);
  },

  register: (userData: {
    username: string;
    password: string;
    email?: string;
    name?: string;
  }) => api.post<{ message: string }>('/register', userData),

  getUserProfile: () => api.get<any>('/user/profile'),
};

export const mealPlanApi = {
  generate: (data: any) => api.post('/generate-meal-plan', data, { timeout: 60000 }),
  getHistory: () => api.get('/meal_plans'),
  getById: (id: string) => api.get(`/meal_plans/${id}`),
  delete: (ids: string[]) => api.post('/meal_plans/bulk_delete', { plan_ids: ids }),
  deleteAll: () => api.delete('/meal_plans/all'),
};

export const recipeApi = {
  generate: (data: any) => api.post('/generate-recipes', data, { timeout: 45000 }),
  generateShoppingList: (recipes: any[]) => api.post('/generate-shopping-list', recipes, { timeout: 30000 }),
};

export const consumptionApi = {
  getHistory: (limit = 50) => api.get(`/consumption/history?limit=${limit}`),
  getAnalytics: (days = 7) => api.get(`/consumption/analytics?days=${days}`),
};

export { ApiError }; 