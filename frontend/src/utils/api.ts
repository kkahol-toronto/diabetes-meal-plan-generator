import { UserProfile } from '../types/UserProfile';

const BASE_URL = 'http://localhost:8000';

// Helper function to get the auth token
const getAuthToken = () => {
  return localStorage.getItem('token');
};

// Helper function to create headers with auth token
const getHeaders = () => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
};

export async function getPatientProfile(): Promise<Response> {
  return fetch(`${BASE_URL}/api/profile/get`, {
    headers: getHeaders(),
  });
}

export async function savePatientProfile(profile: UserProfile): Promise<Response> {
  return fetch(`${BASE_URL}/api/profile/save`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(profile),
  });
} 