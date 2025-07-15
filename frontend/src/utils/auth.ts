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
    return payload.exp < currentTime;
  } catch {
    return true;
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
  localStorage.removeItem('token');
  localStorage.removeItem('isAdmin');
  window.location.href = '/login';
};

export const requireAuth = (): boolean => {
  const token = localStorage.getItem('token');
  if (!token || !isValidToken(token)) {
    logout();
    return false;
  }

  const user = getTokenPayload(token);
  if (!user?.consent_given) {
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

// Token refresh utility (for future implementation)
export const refreshToken = async (): Promise<string | null> => {
  try {
    const response = await fetch('/api/refresh-token', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      return data.access_token;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }
  
  return null;
};

export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  if (!token || isTokenExpired(token)) {
    return null;
  }
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}; 