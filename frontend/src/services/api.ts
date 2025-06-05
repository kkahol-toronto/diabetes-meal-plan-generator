import { PatientProfile } from '../types/PatientProfile';
import { debounce } from 'lodash';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Error class for API errors
class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

// Helper function to get user ID with proper type checking
const getUserId = (): string | null => {
  const userId = localStorage.getItem('userId');
  return userId || null;
};

// Helper function to check if user is authenticated
const isAuthenticated = (): boolean => {
  return !!getUserId() && !!localStorage.getItem('token');
};

// Helper function to handle authentication errors
const handleAuthError = () => {
  localStorage.removeItem('userId');
  localStorage.removeItem('token');
  window.location.href = '/login';
};

// Fetch with retry mechanism
const fetchWithRetry = async (url: string, options: RequestInit, retries = 3): Promise<Response> => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new APIError(response.status, `HTTP error! status: ${response.status}`);
      }
      return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
  throw new APIError(500, 'Failed to fetch after retries');
};

// Helper function to handle API responses
const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json();
  if (!response.ok) {
    throw new APIError(response.status, data.detail || 'An error occurred');
  }
  return data as T;
};

export const getPatientProfile = async (): Promise<PatientProfile | null> => {
  if (!isAuthenticated()) {
    handleAuthError();
    return null;
  }

  try {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/api/profile/get`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    const data = await handleResponse<{ profile: PatientProfile }>(response);
    return data.profile || null;
  } catch (error) {
    if (error instanceof APIError && error.status === 401) {
      handleAuthError();
    }
    console.error('Error fetching patient profile:', error);
    return null;
  }
};

// Create a debounced version of the save function with proper typing
const debouncedSave = debounce(async (profile: Partial<PatientProfile>): Promise<boolean> => {
  if (!isAuthenticated()) {
    handleAuthError();
    return false;
  }
  
  try {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/api/profile/save`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(profile),
      }
    );

    await handleResponse(response);
    return true;
  } catch (error) {
    if (error instanceof APIError && error.status === 401) {
      handleAuthError();
    }
    console.error('Error saving patient profile:', error);
    return false;
  }
}, 1000);

export const savePatientProfile = async (profile: Partial<PatientProfile>): Promise<boolean> => {
  if (!isAuthenticated()) {
    handleAuthError();
    return false;
  }

  try {
    const result = await debouncedSave(profile);
    return result ?? false;
  } catch (error) {
    console.error('Error in savePatientProfile:', error);
    return false;
  }
};

// Admin-specific API functions
export const getAdminUserProfile = async (userId: string): Promise<PatientProfile | null> => {
  if (!isAuthenticated()) {
    handleAuthError();
    return null;
  }

  try {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/api/admin/profile/${userId}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    const data = await handleResponse<{ profile: PatientProfile }>(response);
    return data.profile || null;
  } catch (error) {
    if (error instanceof APIError && error.status === 401) {
      handleAuthError();
    } else if (error instanceof APIError && error.status === 403) {
      throw new Error('You are not authorized to access user profiles');
    }
    console.error('Error fetching user profile for admin:', error);
    throw error;
  }
};

export const saveAdminUserProfile = async (userId: string, profile: Partial<PatientProfile>): Promise<boolean> => {
  if (!isAuthenticated()) {
    handleAuthError();
    return false;
  }
  
  try {
    console.log('🔍 DEBUG: Profile data being sent:', profile);
    console.log('🔍 DEBUG: Profile keys:', Object.keys(profile));
    
    // First try the debug endpoint to see what's wrong
    const debugResponse = await fetchWithRetry(
      `${API_BASE_URL}/debug/profile`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(profile),
      }
    );
    
    const debugResult = await handleResponse<any>(debugResponse);
    console.log('🔍 DEBUG: Debug endpoint response:', debugResult);
    
    if (debugResult.status === 'validation_error') {
      console.error('❌ Validation errors:', debugResult.errors);
      throw new Error(`Validation failed: ${JSON.stringify(debugResult.errors)}`);
    }
    
    // If debug passes, try the real endpoint
    const response = await fetchWithRetry(
      `${API_BASE_URL}/api/admin/profile/${userId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(profile),
      }
    );

    await handleResponse(response);
    return true;
  } catch (error) {
    if (error instanceof APIError && error.status === 401) {
      handleAuthError();
    } else if (error instanceof APIError && error.status === 403) {
      throw new Error('You are not authorized to modify user profiles');
    }
    console.error('Error saving user profile for admin:', error);
    throw error;
  }
}; 