import { PatientProfile } from '../types/PatientProfile';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const getPatientProfile = async (): Promise<PatientProfile | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/get`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Add any authentication headers if needed
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch patient profile');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching patient profile:', error);
    return null;
  }
};

export const savePatientProfile = async (profile: Partial<PatientProfile>): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add any authentication headers if needed
      },
      body: JSON.stringify(profile),
    });

    if (!response.ok) {
      throw new Error('Failed to save patient profile');
    }

    return true;
  } catch (error) {
    console.error('Error saving patient profile:', error);
    return false;
  }
}; 