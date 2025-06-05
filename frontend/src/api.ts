import { UserProfile } from './types/UserProfile';

const BASE_URL = 'http://localhost:8000';

export async function getPatientProfile() {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('No authentication token found');
  }
  return fetch(`${BASE_URL}/user/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

export async function savePatientProfile(profile: UserProfile) {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('No authentication token found');
  }
  return fetch(`${BASE_URL}/user/profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ profile }),
  });
} 