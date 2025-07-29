import { useNavigate } from 'react-router-dom';

export const handleAuthError = (error: any, navigate: ReturnType<typeof useNavigate>) => {
  if (error instanceof Response && error.status === 401) {
    // Clear invalid token
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    
    // Show alert and redirect to login
    alert('Your session has expired. Please log in again.');
    navigate('/login');
    return true;
  }
  return false;
};

interface TokenPayload {
  sub: string;
  exp: number;
  is_admin?: boolean;
  name?: string;
  email?: string;
  consent_given?: boolean;
  consent_timestamp?: string;
  policy_version?: string;
}

export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    // Add 60 second buffer to prevent race conditions where token expires during API calls
    return payload.exp < (currentTime + 60);
  } catch {
    return true;
  }
};

export const isTokenNearExpiry = (token: string, minutesBeforeExpiry: number = 5): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    const expiryBuffer = minutesBeforeExpiry * 60;
    return payload.exp < (currentTime + expiryBuffer);
  } catch {
    return true;
  }
};

export const getTokenTimeRemaining = (token: string): number => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    return Math.max(0, payload.exp - currentTime);
  } catch {
    return 0;
  }
};

export const getTokenPayload = (token: string): TokenPayload | null => {
  try {
    const tokenParts = token.split('.');
    if (tokenParts.length !== 3) {
      throw new Error('Invalid token format');
    }
    return JSON.parse(atob(tokenParts[1]));
  } catch {
    return null;
  }
};

export const isValidToken = (token: string): boolean => {
  if (!token) return false;
  
  const payload = getTokenPayload(token);
  if (!payload) return false;
  
  return !isTokenExpired(token);
};

export const getUserFromToken = (): TokenPayload | null => {
  const token = localStorage.getItem('token');
  if (!token || !isValidToken(token)) {
    return null;
  }
  return getTokenPayload(token);
};

export const logout = (): void => {
  // Clear all auth-related data
  localStorage.removeItem('token');
  localStorage.removeItem('isAdmin');
  
  // Also clear any cached profile data to prevent stale data issues
  localStorage.removeItem('userProfile');
  localStorage.removeItem('userProfile_backup');
  
  console.log('[Auth] User logged out and all data cleared');
  window.location.href = '/login';
};

export const requireAuth = (): boolean => {
  const token = localStorage.getItem('token');
  if (!token || !isValidToken(token)) {
    console.log('[Auth] Authentication required - redirecting to login');
    logout();
    return false;
  }

  const user = getTokenPayload(token);
  if (!user?.consent_given) {
    console.log('[Auth] User consent required - redirecting to login');
    logout();
    alert('You must provide consent to access this application. Please register again.');
    return false;
  }

  return true;
};

export const isAdmin = (): boolean => {
  const user = getUserFromToken();
  return user?.is_admin || false;
};

// Enhanced token refresh utility with better error handling
export const refreshToken = async (): Promise<string | null> => {
  try {
    const currentToken = localStorage.getItem('token');
    if (!currentToken) {
      console.log('[Auth] No current token to refresh');
      return null;
    }

    // Check if token is completely expired (can't refresh)
    if (isTokenExpired(currentToken)) {
      console.log('[Auth] Token completely expired, cannot refresh');
      logout();
      return null;
    }

    const response = await fetch('/api/refresh-token', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${currentToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      console.log('[Auth] Token refreshed successfully');
      return data.access_token;
    } else {
      console.log('[Auth] Token refresh failed, logging out');
      logout();
    }
  } catch (error) {
    console.error('[Auth] Token refresh failed:', error);
    logout();
  }
  
  return null;
};

export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  if (!token || isTokenExpired(token)) {
    console.log('[Auth] No valid token available for request');
    return null;
  }
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

// Enhanced auth check with automatic cleanup
export const checkAuthStatus = (): { isValid: boolean, timeRemaining: number, nearExpiry: boolean } => {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return { isValid: false, timeRemaining: 0, nearExpiry: false };
  }
  
  const isValid = isValidToken(token);
  const timeRemaining = getTokenTimeRemaining(token);
  const nearExpiry = isTokenNearExpiry(token);
  
  // Auto-cleanup if token is invalid
  if (!isValid) {
    console.log('[Auth] Invalid token detected, cleaning up');
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
  }
  
  return { isValid, timeRemaining, nearExpiry };
}; 