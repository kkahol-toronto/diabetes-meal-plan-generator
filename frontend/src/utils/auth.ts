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

export const isTokenExpired = (token: string): boolean => {
  try {
    const tokenParts = token.split('.');
    if (tokenParts.length !== 3) {
      return true;
    }
    const payload = JSON.parse(atob(tokenParts[1]));
    return payload.exp * 1000 < Date.now();
  } catch (e) {
    return true;
  }
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