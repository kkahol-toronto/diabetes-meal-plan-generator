import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  Card,
  CardContent,
  Grid,
  Chip,
  Autocomplete,
  InputAdornment,
  Divider,
  Alert,
  Paper,
  useTheme,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  RadioGroup,
  Radio,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PersonIcon from '@mui/icons-material/Person';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import MedicationIcon from '@mui/icons-material/Medication';
import ScienceIcon from '@mui/icons-material/Science';
import FavoriteIcon from '@mui/icons-material/Favorite';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import FitnessIcon from '@mui/icons-material/FitnessCenter';
import HomeIcon from '@mui/icons-material/Home';
import TrackChangesIcon from '@mui/icons-material/TrackChanges';
import { UserProfile } from '../types';
import config from '../config/environment';
import { isTokenExpired } from '../utils/auth';

interface UserProfileFormProps {
  onSubmit: (profile: UserProfile) => void;
  initialProfile?: UserProfile;
  submitButtonText?: string;
  isAdminMode?: boolean;
}

const UserProfileForm: React.FC<UserProfileFormProps> = ({ 
  onSubmit, 
  initialProfile, 
  submitButtonText = "🚀 Generate My Personalized Meal Plan",
  isAdminMode = false 
}) => {
  const theme = useTheme();
  
  // Normalize profile data to handle old format
  const normalizeProfile = (profileData: any): Partial<UserProfile> => {
    if (!profileData) return {};
    
    const normalized = { ...profileData };
    
    // Convert old string fields to arrays
    if (typeof normalized.ethnicity === 'string') {
      normalized.ethnicity = normalized.ethnicity ? [normalized.ethnicity] : [];
    }
    if (typeof normalized.dietType === 'string') {
      normalized.dietType = normalized.dietType ? [normalized.dietType] : [];
    }
    if (typeof normalized.medicalConditions === 'string') {
      normalized.medicalConditions = normalized.medicalConditions ? [normalized.medicalConditions] : [];
    }
    if (typeof normalized.dietaryFeatures === 'string') {
      normalized.dietaryFeatures = normalized.dietaryFeatures ? [normalized.dietaryFeatures] : [];
    }
    if (typeof normalized.dietFeatures === 'string') {
      normalized.dietaryFeatures = normalized.dietFeatures ? [normalized.dietFeatures] : [];
    }
    
    // Ensure arrays exist
    normalized.ethnicity = normalized.ethnicity || [];
    normalized.dietType = normalized.dietType || [];
    normalized.medicalConditions = normalized.medicalConditions || [];
    normalized.currentMedications = normalized.currentMedications || [];
    normalized.dietaryFeatures = normalized.dietaryFeatures || [];
    normalized.dietaryRestrictions = normalized.dietaryRestrictions || [];
    normalized.foodPreferences = normalized.foodPreferences || [];
    normalized.allergies = normalized.allergies || [];
    normalized.avoids = normalized.avoids || [];
    normalized.strongDislikes = normalized.strongDislikes || [];
    normalized.exerciseTypes = normalized.exerciseTypes || [];
    // Set default appliances for new users and users with empty appliances array
    // All appliances are pre-selected by default, users can deselect what they don't have
    if (!normalized.availableAppliances || normalized.availableAppliances.length === 0) {
      normalized.availableAppliances = [
        'Fridge & Freezer',
        'Microwave',
        'Stove/Oven',
        'Instant Pot',
        'Air Fryer',
        'Slow Cooker',
        'Blender',
        'Food Processor',
        'Toaster'
      ];
    }
    normalized.primaryGoals = normalized.primaryGoals || [];
    
    // Ensure readinessToChange and wantsWeightLoss are properly handled
    if (typeof normalized.readinessToChange !== 'string') {
      normalized.readinessToChange = normalized.readinessToChange || '';
    }
    
    if (typeof normalized.wantsWeightLoss !== 'boolean') {
      normalized.wantsWeightLoss = Boolean(normalized.wantsWeightLoss) || false;
    }
    
    console.log(`[UserProfileForm] Normalized profile: readinessToChange=${normalized.readinessToChange}, wantsWeightLoss=${normalized.wantsWeightLoss}`);
    
    return normalized;
  };

  const [profile, setProfile] = useState<UserProfile>(() => {
    const defaultProfile = {
      name: '',
      dateOfBirth: '',
      age: undefined,
      gender: '',
      ethnicity: [],
      medicalConditions: [],
      currentMedications: [],
      labValues: {},
      height: 0,
      weight: 0,
      bmi: undefined,
      waistCircumference: undefined,
      systolicBP: undefined,
      diastolicBP: undefined,
      heartRate: undefined,
      dietType: [],
      dietaryFeatures: [],
      dietaryRestrictions: [],
      foodPreferences: [],
      allergies: [],
      avoids: [],
      strongDislikes: [],
      workActivityLevel: '',
      exerciseFrequency: '',
      exerciseTypes: [],
      mobilityIssues: false,
      mealPrepCapability: '',
      availableAppliances: [
        'Fridge & Freezer',
        'Microwave',
        'Stove/Oven',
        'Instant Pot',
        'Air Fryer',
        'Slow Cooker',
        'Blender',
        'Food Processor',
        'Toaster'
      ],
      eatingSchedule: '',
      primaryGoals: [],
      readinessToChange: '',
      wantsWeightLoss: false,
      calorieTarget: '',
      ...normalizeProfile(initialProfile),
    };
    
    console.log(`[UserProfileForm] Initial profile loaded with readinessToChange: ${defaultProfile.readinessToChange}, wantsWeightLoss: ${defaultProfile.wantsWeightLoss}`);
    
    return defaultProfile;
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Debug state for monitoring save issues
  const [debugInfo, setDebugInfo] = useState({
    lastSaveAttempt: null as string | null,
    lastSaveSuccess: null as string | null,
    lastSaveError: null as string | null,
    lastSaveTime: null as string | null,
    saveStatus: 'idle' as 'idle' | 'saving' | 'success' | 'error' | 'saved',
    saveAttempt: 0,
    profileCompleteness: 0,
    tokenValid: true,
  });
  
  // State for unit preferences
  const [unitPreferences, setUnitPreferences] = useState({
    height: 'metric', // 'metric' or 'imperial'
    weight: 'metric', // 'metric' or 'imperial'
    waistCircumference: 'metric' // 'metric' or 'imperial'
  });
  
  // State for imperial measurements
  const [imperialMeasurements, setImperialMeasurements] = useState({
    heightFeet: 0,
    heightInches: 0,
    weightPounds: 0,
    waistInches: 0
  });
  
  // State for "Other" text inputs
  const [otherValues, setOtherValues] = useState({
    ethnicity: '',
    medicalConditions: '',
    medications: '',
    dietType: '',
    exerciseTypes: '',
    appliances: '',
    goals: '',
    eatingSchedule: '',
    calorieTarget: '',
  });

  // State for text input fields that need comma processing
  const [textInputs, setTextInputs] = useState({
    allergies: '',
    avoids: '',
    strongDislikes: ''
  });

  // Auto-calculate age from date of birth
  useEffect(() => {
    if (profile.dateOfBirth) {
      const today = new Date();
      const birthDate = new Date(profile.dateOfBirth);
      const age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        setProfile(prev => ({ ...prev, age: age - 1 }));
      } else {
        setProfile(prev => ({ ...prev, age }));
      }
    }
  }, [profile.dateOfBirth]);

  // Auto-calculate BMI
  useEffect(() => {
    if (profile.height && profile.weight && profile.height > 0 && profile.weight > 0) {
      const heightInMeters = profile.height / 100;
      const bmi = profile.weight / (heightInMeters * heightInMeters);
      setProfile(prev => ({ ...prev, bmi: Math.round(bmi * 10) / 10 }));
    }
  }, [profile.height, profile.weight]);

  // Conversion functions
  const convertMetricToImperial = {
    heightToFeetInches: (cm: number) => {
      const totalInches = cm / 2.54;
      const feet = Math.floor(totalInches / 12);
      const inches = Math.round((totalInches % 12) * 10) / 10;
      return { feet, inches };
    },
    weightToPounds: (kg: number) => Math.round(kg * 2.20462 * 10) / 10,
    waistToInches: (cm: number) => Math.round(cm / 2.54 * 10) / 10
  };

  const convertImperialToMetric = {
    feetInchesToCm: (feet: number, inches: number) => 
      Math.round((feet * 12 + inches) * 2.54 * 10) / 10,
    poundsToKg: (pounds: number) => Math.round(pounds / 2.20462 * 10) / 10,
    inchesToCm: (inches: number) => Math.round(inches * 2.54 * 10) / 10
  };

  // Update imperial measurements when metric values change
  useEffect(() => {
    if (profile.height > 0) {
      const { feet, inches } = convertMetricToImperial.heightToFeetInches(profile.height);
      setImperialMeasurements(prev => ({
        ...prev,
        heightFeet: feet,
        heightInches: inches
      }));
    }
    
    if (profile.weight > 0) {
      const pounds = convertMetricToImperial.weightToPounds(profile.weight);
      setImperialMeasurements(prev => ({
        ...prev,
        weightPounds: pounds
      }));
    }
    
    if (profile.waistCircumference && profile.waistCircumference > 0) {
      const inches = convertMetricToImperial.waistToInches(profile.waistCircumference);
      setImperialMeasurements(prev => ({
        ...prev,
        waistInches: inches
      }));
    }
  }, [profile.height, profile.weight, profile.waistCircumference]);

  // Initialize text inputs from profile arrays
  useEffect(() => {
    setTextInputs({
      allergies: profile.allergies?.join(', ') || '',
      avoids: profile.avoids?.join(', ') || '',
      strongDislikes: profile.strongDislikes?.join(', ') || ''
    });
  }, [profile.allergies, profile.avoids, profile.strongDislikes]);

  // Handle unit preference changes
  const handleUnitPreferenceChange = (measurement: keyof typeof unitPreferences, unit: 'metric' | 'imperial') => {
    setUnitPreferences(prev => ({
      ...prev,
      [measurement]: unit
    }));
  };

  // Handle imperial measurement changes
  const handleImperialMeasurementChange = (field: keyof typeof imperialMeasurements, value: number) => {
    setImperialMeasurements(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Convert to metric and update profile
    if (field === 'heightFeet' || field === 'heightInches') {
      const feet = field === 'heightFeet' ? value : imperialMeasurements.heightFeet;
      const inches = field === 'heightInches' ? value : imperialMeasurements.heightInches;
      const cm = convertImperialToMetric.feetInchesToCm(feet, inches);
      handleInputChange('height', cm);
    } else if (field === 'weightPounds') {
      const kg = convertImperialToMetric.poundsToKg(value);
      handleInputChange('weight', kg);
    } else if (field === 'waistInches') {
      const cm = convertImperialToMetric.inchesToCm(value);
      handleInputChange('waistCircumference', cm);
    }
  };

  // Handle text input changes (for fields that need comma processing)
  const handleTextInputChange = (field: keyof typeof textInputs, value: string) => {
    setTextInputs(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Process comma-separated text into array and update profile
  const processTextInputToArray = (field: keyof typeof textInputs, profileField: keyof UserProfile) => {
    const textValue = textInputs[field];
    const processedArray = textValue.split(',').map(s => s.trim()).filter(Boolean);
    handleInputChange(profileField, processedArray);
  };

  // Auto-save functionality with debouncing and race condition prevention
  const [saveQueue, setSaveQueue] = useState<{isProcessing: boolean, pendingSave: UserProfile | null}>({
    isProcessing: false,
    pendingSave: null
  });
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSaveRef = useRef<string>('');

  useEffect(() => {
    // In admin mode, this form is used to edit a patient's profile.
    // We must NOT auto-save to the logged-in admin's own /user/profile.
    if (isAdminMode) {
      return;
    }
    // Debounced auto-save with race condition prevention
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Create a debounced save function
    saveTimeoutRef.current = setTimeout(async () => {
      const profileJson = JSON.stringify(profile);
      
      // Skip if profile hasn't changed since last save
      if (profileJson === lastSaveRef.current) {
        console.log('[UserProfileForm] Profile unchanged, skipping save');
        return;
      }

      // Skip if another save is already in progress
      if (saveQueue.isProcessing) {
        console.log('[UserProfileForm] Save already in progress, queueing this save');
        setSaveQueue(prev => ({ ...prev, pendingSave: profile }));
        return;
      }

      console.log(`[UserProfileForm] Auto-saving profile (debounced) with readinessToChange: ${profile.readinessToChange}, wantsWeightLoss: ${profile.wantsWeightLoss}`);
      await saveProfileToDatabase(profile);
    }, 2000); // Increased debounce delay to reduce race conditions

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [profile]);

  // Process queued saves
  useEffect(() => {
    const processQueuedSave = async () => {
      if (!saveQueue.isProcessing && saveQueue.pendingSave) {
        console.log('[UserProfileForm] Processing queued save');
        const profileToSave = saveQueue.pendingSave;
        setSaveQueue({ isProcessing: true, pendingSave: null });
        
        await saveProfileToDatabase(profileToSave);
        
        // Check if another save was queued while processing
        setSaveQueue(prev => ({ 
          isProcessing: false, 
          pendingSave: prev.pendingSave 
        }));
      }
    };

    processQueuedSave();
  }, [saveQueue.pendingSave, saveQueue.isProcessing]);

  const saveProfileToDatabase = async (profileData: UserProfile, retryCount: number = 0): Promise<void> => {
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 1000;

    try {
      // In admin mode, never save to /user/profile with the admin token
      if (isAdminMode) {
        console.log('[UserProfileForm] Admin mode: skipping save to /user/profile');
        setSaveQueue(prev => ({ ...prev, isProcessing: false }));
        setDebugInfo(prev => ({
          ...prev,
          saveStatus: 'idle',
        }));
        return;
      }
      // Mark save as in progress
      setSaveQueue(prev => ({ ...prev, isProcessing: true }));
      setDebugInfo(prev => ({
        ...prev,
        saveStatus: 'saving',
        saveAttempt: retryCount + 1
      }));

      const token = localStorage.getItem('token');
      if (!token) {
        console.log('[UserProfileForm] No token found, skipping database save');
        setDebugInfo(prev => ({
          ...prev,
          saveStatus: 'error',
          lastSaveError: 'No authentication token found',
          tokenValid: false
        }));
        setSaveQueue(prev => ({ ...prev, isProcessing: false }));
        return;
      }

      // Check if token is expired
      const isExpired = isTokenExpired(token);
      if (isExpired) {
        console.error('[UserProfileForm] Token is expired, cannot save profile');
        // Clear expired token and try to refresh
        localStorage.removeItem('token');
        setDebugInfo(prev => ({
          ...prev,
          saveStatus: 'error',
          lastSaveError: 'Token expired - session ended',
          tokenValid: false
        }));
        setSaveQueue(prev => ({ ...prev, isProcessing: false }));
        return;
      }

      setDebugInfo(prev => ({ ...prev, tokenValid: true }));

      console.log(`[UserProfileForm] Saving profile to database (attempt ${retryCount + 1}) with readinessToChange: ${profileData.readinessToChange}, wantsWeightLoss: ${profileData.wantsWeightLoss}`);
      console.log('[UserProfileForm] Full profile data being saved:', profileData);
      
      // Also save to localStorage as backup (skip in admin mode to avoid polluting admin's storage)
      if (!isAdminMode) {
        try {
          localStorage.setItem('userProfile_backup', JSON.stringify({
            profile: profileData,
            timestamp: new Date().toISOString(),
            version: Date.now()
          }));
          console.log('[UserProfileForm] Profile backed up to localStorage');
        } catch (backupError) {
          console.error('[UserProfileForm] Failed to backup to localStorage:', backupError);
        }
      }
      
      const response = await fetch(`${config.API_URL}/user/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ profile: profileData }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('[UserProfileForm] Profile saved successfully:', result);
        
        // Update last save reference to prevent unnecessary saves
        lastSaveRef.current = JSON.stringify(profileData);
        
        setDebugInfo(prev => ({
          ...prev,
          saveStatus: 'saved',
          lastSaveTime: new Date().toLocaleString(),
          lastSaveError: null,
          saveAttempt: retryCount + 1,
          profileCompleteness: result.profile_completeness || 0
        }));
        
        setSaveQueue(prev => ({ ...prev, isProcessing: false }));
      } else {
        const errorText = await response.text();
        console.error('[UserProfileForm] Failed to save profile:', response.status, errorText);
        
        if (response.status === 401) {
          console.error('[UserProfileForm] Authentication failed (401)');
          localStorage.removeItem('token');
          setDebugInfo(prev => ({
            ...prev,
            saveStatus: 'error',
            lastSaveError: 'Authentication failed (401)',
            tokenValid: false
          }));
          setSaveQueue(prev => ({ ...prev, isProcessing: false }));
        } else {
          // Retry on other errors
          if (retryCount < MAX_RETRIES) {
            console.log(`[UserProfileForm] Retrying save in ${RETRY_DELAY}ms (attempt ${retryCount + 2}/${MAX_RETRIES + 1})`);
            setTimeout(() => {
              saveProfileToDatabase(profileData, retryCount + 1);
            }, RETRY_DELAY * (retryCount + 1)); // Exponential backoff
          } else {
            setDebugInfo(prev => ({
              ...prev,
              saveStatus: 'error',
              lastSaveError: `HTTP ${response.status}: ${errorText} (Max retries exceeded)`,
              saveAttempt: retryCount + 1
            }));
            setSaveQueue(prev => ({ ...prev, isProcessing: false }));
          }
        }
      }
    } catch (error) {
      console.error('[UserProfileForm] Error saving profile to database:', error);
      
      // Retry on network errors
      if (retryCount < MAX_RETRIES) {
        console.log(`[UserProfileForm] Retrying save due to network error in ${RETRY_DELAY}ms (attempt ${retryCount + 2}/${MAX_RETRIES + 1})`);
        setTimeout(() => {
          saveProfileToDatabase(profileData, retryCount + 1);
        }, RETRY_DELAY * (retryCount + 1)); // Exponential backoff
      } else {
        setDebugInfo(prev => ({
          ...prev,
          saveStatus: 'error',
          lastSaveError: `Network error: ${error instanceof Error ? error.message : 'Unknown error'} (Max retries exceeded)`,
          saveAttempt: retryCount + 1
        }));
        setSaveQueue(prev => ({ ...prev, isProcessing: false }));
      }
    }
  };

  // Load saved profile on mount - try database first, then localStorage
  useEffect(() => {
    const loadProfile = async () => {
      // In admin mode, we rely on initialProfile passed from the admin patient loader.
      // Never load the logged-in admin's own profile here.
      if (isAdminMode) {
        return;
      }
      if (!initialProfile) {
        const token = localStorage.getItem('token');
        
        console.log('[UserProfileForm] Loading profile - token exists:', !!token);
        
        // Try to load from database first
        if (token) {
          const isExpired = isTokenExpired(token);
          console.log('[UserProfileForm] Token expired?', isExpired);
          
          if (isExpired) {
            localStorage.removeItem('token');
            console.error('[UserProfileForm] Token expired, cannot load profile from database');
          } else {
            try {
              console.log('[UserProfileForm] Attempting to load profile from database...');
              const response = await fetch(`${config.API_URL}/user/profile`, {
                method: 'GET',
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });

              console.log('[UserProfileForm] Database load response status:', response.status);

              if (response.ok) {
                const data = await response.json();
                console.log('[UserProfileForm] Raw profile data from database:', data);
                
                if (data && data.profile && Object.keys(data.profile).length > 0) {
                  console.log(`[UserProfileForm] Profile loaded from database successfully with readinessToChange: ${data.profile.readinessToChange}, wantsWeightLoss: ${data.profile.wantsWeightLoss}`);
                  const normalizedProfile = normalizeProfile(data.profile);
                  console.log('[UserProfileForm] Normalized profile:', normalizedProfile);
                  setProfile(prev => ({ ...prev, ...normalizedProfile }));
                  
                  // Update debug info with database response
                  setDebugInfo(prev => ({
                    ...prev,
                    profileCompleteness: data.profile_completeness || 0,
                    lastSaveTime: data.timestamp || new Date().toLocaleString(),
                    saveStatus: 'success'
                  }));
                  
                  // Update last save reference to prevent unnecessary saves
                  lastSaveRef.current = JSON.stringify(data.profile);
                  
                  return; // Exit early if database load was successful
                } else {
                  console.log('[UserProfileForm] Database returned empty profile, falling back to localStorage');
                }
              } else {
                const errorText = await response.text();
                console.error('[UserProfileForm] Failed to load profile from database:', response.status, errorText);
                if (response.status === 401) {
                  localStorage.removeItem('token');
                }
              }
            } catch (error) {
              console.error('Error loading profile from database:', error);
            }
          }
        }

        // Method 2: Try backup from localStorage (new backup format)
        const backupProfile = localStorage.getItem('userProfile_backup');
        console.log('[UserProfileForm] Backup profile exists:', !!backupProfile);
        
        if (backupProfile) {
          try {
            const backup = JSON.parse(backupProfile);
            if (backup.profile && Object.keys(backup.profile).length > 0) {
              console.log('[UserProfileForm] Profile loaded from backup:', backup);
              const normalizedProfile = normalizeProfile(backup.profile);
              setProfile(prev => ({ ...prev, ...normalizedProfile }));
              setDebugInfo(prev => ({
                ...prev,
                lastSaveTime: backup.timestamp || 'From backup',
                saveStatus: 'success'
              }));
              return; // Exit if backup load successful
            }
          } catch (error) {
            console.error('Error loading profile from backup:', error);
          }
        }

        // Method 3: Fallback to old localStorage format
        const savedProfile = localStorage.getItem('userProfile');
        console.log('[UserProfileForm] Old localStorage profile exists:', !!savedProfile);
        
        if (savedProfile) {
          try {
            const parsed = JSON.parse(savedProfile);
            console.log('[UserProfileForm] Profile loaded from old localStorage as fallback:', parsed);
            setProfile(prev => ({ ...prev, ...normalizeProfile(parsed) }));
          } catch (error) {
            console.error('Error loading saved profile from old localStorage:', error);
          }
        } else {
          console.log('[UserProfileForm] No profile found in localStorage either');
        }
      } else {
        console.log('[UserProfileForm] Using provided initialProfile:', initialProfile);
      }
    };

    loadProfile();
  }, [initialProfile]);

  const handleInputChange = (field: keyof UserProfile, value: any) => {
    console.log(`[UserProfileForm] Field changed: ${field} = ${value}`);
    setProfile(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    
    // For critical fields like readinessToChange and wantsWeightLoss, 
    // trigger immediate save to ensure they're not lost
    if (field === 'readinessToChange' || field === 'wantsWeightLoss') {
      console.log(`[UserProfileForm] Critical field ${field} changed, triggering immediate save`);
      setTimeout(() => saveProfileToDatabase({ ...profile, [field]: value }), 500);
    }
  };

  const handleLabValueChange = (field: string, value: string) => {
    setProfile(prev => ({
      ...prev,
      labValues: { ...prev.labValues, [field]: value }
    }));
  };

  const handleArrayChange = (field: keyof UserProfile, value: string, checked: boolean) => {
    const currentValue = profile[field];
    let currentArray: string[] = [];
    
    // Ensure we always work with an array
    if (Array.isArray(currentValue)) {
      currentArray = currentValue;
    } else if (typeof currentValue === 'string' && currentValue) {
      currentArray = [currentValue];
    }
    
    const newArray = checked
      ? [...currentArray, value]
      : currentArray.filter(item => item !== value);
    
    setProfile(prev => ({ ...prev, [field]: newArray }));
  };

  const handleOtherChange = (field: string, value: string) => {
    setOtherValues(prev => ({ ...prev, [field]: value }));
  };

  const addOtherOption = (profileField: keyof UserProfile, otherField: string) => {
    const otherValue = otherValues[otherField as keyof typeof otherValues];
    
    if (otherValue && otherValue.trim()) {
      const currentArray = (profile[profileField] as string[]) || [];
      const newCustomEntry = `Other: ${otherValue.trim()}`;
      
      // Check if this exact custom entry already exists to prevent duplicates
      if (!currentArray.includes(newCustomEntry)) {
        const newArray = [...currentArray, newCustomEntry];
        setProfile(prev => ({ ...prev, [profileField]: newArray }));
      }
      
      // Clear the input field
      setOtherValues(prev => ({ ...prev, [otherField]: '' }));
    }
  };

  const getBMICategory = (bmi: number): string => {
    if (bmi < 18.5) return '(Underweight)';
    if (bmi < 25) return '(Normal)';
    if (bmi < 30) return '(Overweight)';
    return '(Obese)';
  };

  const getBMIColor = (bmi: number): string => {
    if (bmi < 18.5) return '#2196f3'; // Blue
    if (bmi < 25) return '#4caf50'; // Green
    if (bmi < 30) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    // For admin mode, validation is more relaxed - only name is required
    if (isAdminMode) {
      if (!profile.name?.trim()) {
        newErrors.name = 'Patient name is required';
      }
    } else {
      // For patient mode, more strict validation
      if (!profile.name?.trim()) {
        newErrors.name = 'Full name is required';
      }
      
      if (!profile.height || profile.height <= 0) {
        newErrors.height = 'Please enter a valid height (e.g., 170 cm)';
      } else if (profile.height < 100 || profile.height > 250) {
        newErrors.height = 'Height should be between 100-250 cm';
      }
      
      if (!profile.weight || profile.weight <= 0) {
        newErrors.weight = 'Please enter a valid weight (e.g., 70 kg)';
      } else if (profile.weight < 30 || profile.weight > 300) {
        newErrors.weight = 'Weight should be between 30-300 kg';
      }
      
      if (!profile.gender) {
        newErrors.gender = 'Please select your sex';
      }
      
      // Warn if important fields are missing but don't block submission
      const warnings: string[] = [];
      if (!profile.age && !profile.dateOfBirth) {
        warnings.push('Age or date of birth');
      }
      if (!profile.medicalConditions?.length) {
        warnings.push('Medical conditions');
      }
      if (!profile.dietType?.length) {
        warnings.push('Diet type');
      }
      
      if (warnings.length > 0 && Object.keys(newErrors).length === 0) {
        // Show a gentle reminder but allow submission
        console.log('Optional fields that could improve meal planning:', warnings.join(', '));
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      console.log(`[UserProfileForm] Submitting profile with readinessToChange: ${profile.readinessToChange}, wantsWeightLoss: ${profile.wantsWeightLoss}`);
      
      // Ensure critical fields are included in the final submission
      const finalProfile = {
        ...profile,
        readinessToChange: profile.readinessToChange || '',
        wantsWeightLoss: Boolean(profile.wantsWeightLoss)
      };
      
      console.log(`[UserProfileForm] Final profile to submit: readinessToChange=${finalProfile.readinessToChange}, wantsWeightLoss=${finalProfile.wantsWeightLoss}`);
      
      onSubmit(finalProfile);
    }
  };

  // Option arrays
  const ethnicityOptions = [
    'South Asian – North Indian',
    'South Asian – Pakistani', 
    'South Asian – Sri Lankan',
    'South Asian – Bangladeshi',
    'East Asian – Chinese',
    'East Asian – Korean',
    'Filipino',
    'Caucasian / White',
    'Black / African / African-American',
    'Caribbean – Jamaican',
    'Caribbean – Guyanese',
    'Indigenous / First Nations',
    'Middle Eastern',
    'Hispanic / Latin American',
    'Other'
  ];

  const medicalConditionsOptions = [
    'Type 2 Diabetes',
    'Type 1 Diabetes',
    'Obesity',
    'Hypertension',
    'High Cholesterol',
    'High Triglycerides',
    'Coronary Artery Disease',
    'Stroke',
    'Peripheral Vascular Disease',
    'Fatty Liver',
    'Chronic Kidney Disease',
    'Proteinuria',
    'Elevated Potassium',
    'PCOS',
    'Hypothyroidism',
    'Osteoporosis',
    'GERD / acid reflux',
    'B12 deficiency',
    'Iron deficiency / anemia',
    'Other'
  ];

  const medicationsOptions = [
    'Metformin',
    'Insulin',
    'GLP-1 agonist (e.g., Ozempic, Trulicity)',
    'SGLT2 inhibitor (e.g., Jardiance, Farxiga)',
    'Statin',
    'Diuretic',
    'Thyroid hormone',
    'Antihypertensives',
    'Anticoagulants (e.g., Aspirin, Eliquis)',
    'Other'
  ];

  const dietTypeOptions = [
    'Western',
    'Mediterranean',
    'South Asian – North Indian',
    'South Asian – Pakistani',
    'South Asian – Sri Lankan',
    'South Asian – South Indian',
    'East Asian – Chinese / Korean',
    'Caribbean – Jamaican / Guyanese',
    'Filipino',
    'Other'
  ];

  const dietaryFeaturesOptions = [
    'Low Carb',
    'High Protein',
    'Normal Protein',
    'Low Saturated Fat',
    'Low Potassium',
    'Predominantly Plant-Based',
    'Plant-Based + Egg Whites / Chicken / Fish',
    'Vegetarian (with eggs)',
    'Vegetarian (no eggs)',
    'Soft Texture Required',
    'Gluten-Free',
    'Lactose-Free'
  ];

  const exerciseTypesOptions = [
    'Walking',
    'Jogging',
    'Running',
    'Hiking',
    'Resistance training / weights',
    'Weightlifting',
    'Yoga / Pilates',
    'Swimming',
    'Cycling (indoor/outdoor)',
    'Tennis',
    'Basketball',
    'Soccer / Football',
    'Badminton',
    'Volleyball',
    'Golf',
    'Dancing',
    'Martial arts / Boxing',
    'Rowing',
    'CrossFit',
    'Cardio machines (treadmill, elliptical)',
    'Fitness classes (e.g., Zumba, aerobics)',
    'Home workouts',
    'Other'
  ];

  const appliancesOptions = [
    'Fridge & Freezer',
    'Microwave',
    'Stove/Oven',
    'Instant Pot',
    'Air Fryer',
    'Slow Cooker',
    'Blender',
    'Food Processor',
    'Toaster',
    'Other'
  ];

  const primaryGoalsOptions = [
    'Improve A1C',
    'Lower cholesterol / triglycerides',
    'Improve energy / stamina',
    'Reduce blood pressure',
    'Improve digestion',
    'General wellness',
    'Other'
  ];

  const sectionStyle = {
    mb: 3,
    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
    borderRadius: 2,
    overflow: 'hidden',
  };

  const sectionHeaderStyle = {
    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
    color: 'white',
    py: 2,
    px: 3,
  };

  return (
    <Box sx={{ 
      maxWidth: 1200, 
      mx: 'auto', 
      p: { xs: 1, sm: 2, md: 3 } // Mobile: 8px, Tablet: 16px, Desktop: 24px
    }}>
      <Paper elevation={3} sx={{ 
        p: { xs: 2, sm: 3, md: 4 } // Mobile: 16px, Tablet: 24px, Desktop: 32px
      }}>
        <Typography variant="h4" align="center" gutterBottom sx={{ 
          color: theme.palette.primary.main,
          fontWeight: 'bold',
          mb: 3 
        }}>
          Comprehensive Health Profile
        </Typography>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          {isAdminMode ? (
            <>🏥 You are filling out this profile on behalf of the patient. The patient can complete any missing information later. Only the patient name is required.</>
          ) : (
            <>🔒 Your information is automatically saved as you type and stays private. The more details you provide, the more personalized your meal plan will be. All fields marked with * are required.</>
          )}
        </Alert>

        {/* Debug Section - only show if there are issues */}
        {(debugInfo.saveStatus === 'error' || !debugInfo.tokenValid) && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>🔧 Profile Save Diagnostics</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2"><strong>Save Status:</strong> {debugInfo.saveStatus}</Typography>
                <Typography variant="body2"><strong>Token Valid:</strong> {debugInfo.tokenValid ? 'Yes' : 'No'}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2"><strong>Last Attempt:</strong> {debugInfo.lastSaveAttempt ? new Date(debugInfo.lastSaveAttempt).toLocaleTimeString() : 'None'}</Typography>
                <Typography variant="body2"><strong>Last Success:</strong> {debugInfo.lastSaveSuccess ? new Date(debugInfo.lastSaveSuccess).toLocaleTimeString() : 'None'}</Typography>
              </Grid>
              {debugInfo.lastSaveError && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="error"><strong>Last Error:</strong> {debugInfo.lastSaveError}</Typography>
                </Grid>
              )}
            </Grid>
          </Alert>
        )}

        {/* Success indicator */}
        {debugInfo.saveStatus === 'success' && (
          <Alert severity="success" sx={{ mb: 3 }}>
            ✅ Profile saved successfully at {debugInfo.lastSaveSuccess ? new Date(debugInfo.lastSaveSuccess).toLocaleTimeString() : 'unknown time'}
          </Alert>
        )}

        {/* Saving indicator */}
        {debugInfo.saveStatus === 'saving' && (
          <Alert severity="info" sx={{ mb: 3 }}>
            💾 Saving profile to database...
          </Alert>
        )}

        {/* Patient Demographics */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PersonIcon />
              <Typography variant="h6">👤 Patient Demographics</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label={isAdminMode ? "Patient Name *" : "Full Name *"}
                  value={profile.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  error={!!errors.name}
                  helperText={errors.name}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Date of Birth"
                  type="date"
                  value={profile.dateOfBirth}
                  onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Age"
                  type="number"
                  value={profile.age || ''}
                  onChange={(e) => handleInputChange('age', parseInt(e.target.value) || undefined)}
                  variant="outlined"
                  InputProps={{ readOnly: !!profile.dateOfBirth }}
                  helperText={profile.dateOfBirth ? "Auto-calculated" : "Years"}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth error={!!errors.gender}>
                  <FormLabel>{isAdminMode ? "Sex" : "Sex *"}</FormLabel>
                  <RadioGroup
                    row
                    value={profile.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                  >
                    <FormControlLabel value="Male" control={<Radio />} label="Male" />
                    <FormControlLabel value="Female" control={<Radio />} label="Female" />
                    <FormControlLabel value="Other" control={<Radio />} label="Other" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  options={ethnicityOptions}
                  value={profile.ethnicity || []}
                  onChange={(_, newValue) => handleInputChange('ethnicity', newValue)}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip variant="outlined" label={option} {...getTagProps({ index })} key={option} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField {...params} label="Ethnicity (select all that apply)" variant="outlined" />
                  )}
                />
                {(profile.ethnicity || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other ethnicity"
                      value={otherValues.ethnicity}
                      onChange={(e) => handleOtherChange('ethnicity', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.ethnicity.trim()) {
                          addOtherOption('ethnicity', 'ethnicity');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('ethnicity', 'ethnicity')}
                      disabled={!otherValues.ethnicity?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom ethnicity values */}
                {(profile.ethnicity || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.ethnicity || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newEthnicity = (profile.ethnicity || []).filter(e => e !== item);
                          handleInputChange('ethnicity', newEthnicity);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Vital Signs */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FavoriteIcon />
              <Typography variant="h6">📏 Vital Signs</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              {/* Height Section */}
              <Grid item xs={12}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {isAdminMode ? "Height" : "Height *"}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Button
                      variant={unitPreferences.height === 'metric' ? 'contained' : 'outlined'}
                      size="small"
                      onClick={() => handleUnitPreferenceChange('height', 'metric')}
                    >
                      Metric (cm)
                    </Button>
                    <Button
                      variant={unitPreferences.height === 'imperial' ? 'contained' : 'outlined'}
                      size="small"
                      onClick={() => handleUnitPreferenceChange('height', 'imperial')}
                    >
                      Imperial (ft/in)
                    </Button>
                  </Box>
                  <Grid container spacing={2}>
                    {unitPreferences.height === 'metric' ? (
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Height (cm)"
                          type="number"
                          value={profile.height || ''}
                          onChange={(e) => handleInputChange('height', parseFloat(e.target.value) || 0)}
                          error={!!errors.height}
                          helperText={errors.height}
                          variant="outlined"
                          InputProps={{
                            endAdornment: <InputAdornment position="end">cm</InputAdornment>,
                          }}
                        />
                      </Grid>
                    ) : (
                      <>
                        <Grid item xs={6} md={3}>
                          <TextField
                            fullWidth
                            label="Feet"
                            type="number"
                            value={imperialMeasurements.heightFeet || ''}
                            onChange={(e) => handleImperialMeasurementChange('heightFeet', parseFloat(e.target.value) || 0)}
                            variant="outlined"
                            InputProps={{
                              endAdornment: <InputAdornment position="end">ft</InputAdornment>,
                            }}
                            inputProps={{ min: 0, max: 8 }}
                          />
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <TextField
                            fullWidth
                            label="Inches"
                            type="number"
                            value={imperialMeasurements.heightInches || ''}
                            onChange={(e) => handleImperialMeasurementChange('heightInches', parseFloat(e.target.value) || 0)}
                            variant="outlined"
                            InputProps={{
                              endAdornment: <InputAdornment position="end">in</InputAdornment>,
                            }}
                            inputProps={{ min: 0, max: 11.9, step: 0.1 }}
                          />
                        </Grid>
                      </>
                    )}
                    {profile.height > 0 && (
                      <Grid item xs={12} md={6}>
                        <Alert severity="info" sx={{ mt: 1 }}>
                          {unitPreferences.height === 'metric' 
                            ? `${profile.height} cm = ${imperialMeasurements.heightFeet}' ${imperialMeasurements.heightInches}"`
                            : `${imperialMeasurements.heightFeet}' ${imperialMeasurements.heightInches}" = ${profile.height} cm`
                          }
                        </Alert>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </Grid>

              {/* Weight Section */}
              <Grid item xs={12}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {isAdminMode ? "Weight" : "Weight *"}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Button
                      variant={unitPreferences.weight === 'metric' ? 'contained' : 'outlined'}
                      size="small"
                      onClick={() => handleUnitPreferenceChange('weight', 'metric')}
                    >
                      Metric (kg)
                    </Button>
                    <Button
                      variant={unitPreferences.weight === 'imperial' ? 'contained' : 'outlined'}
                      size="small"
                      onClick={() => handleUnitPreferenceChange('weight', 'imperial')}
                    >
                      Imperial (lbs)
                    </Button>
                  </Box>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label={unitPreferences.weight === 'metric' ? 'Weight (kg)' : 'Weight (lbs)'}
                        type="number"
                        value={unitPreferences.weight === 'metric' ? (profile.weight || '') : (imperialMeasurements.weightPounds || '')}
                        onChange={(e) => {
                          const value = parseFloat(e.target.value) || 0;
                          if (unitPreferences.weight === 'metric') {
                            handleInputChange('weight', value);
                          } else {
                            handleImperialMeasurementChange('weightPounds', value);
                          }
                        }}
                        error={!!errors.weight}
                        helperText={errors.weight}
                        variant="outlined"
                        InputProps={{
                          endAdornment: <InputAdornment position="end">
                            {unitPreferences.weight === 'metric' ? 'kg' : 'lbs'}
                          </InputAdornment>,
                        }}
                      />
                    </Grid>
                    {profile.weight > 0 && (
                      <Grid item xs={12} md={6}>
                        <Alert severity="info" sx={{ mt: 1 }}>
                          {unitPreferences.weight === 'metric' 
                            ? `${profile.weight} kg = ${imperialMeasurements.weightPounds} lbs`
                            : `${imperialMeasurements.weightPounds} lbs = ${profile.weight} kg`
                          }
                        </Alert>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </Grid>

              {/* BMI */}
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="BMI"
                  value={profile.bmi ? `${profile.bmi} ${getBMICategory(profile.bmi)}` : ''}
                  variant="outlined"
                  InputProps={{ 
                    readOnly: true,
                    style: { 
                      backgroundColor: '#f5f5f5',
                      color: getBMIColor(profile.bmi || 0)
                    }
                  }}
                  helperText="Auto-calculated from height & weight"
                />
              </Grid>

              {/* Waist Circumference Section */}
              <Grid item xs={12} md={8}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    Waist Circumference (Optional)
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Button
                      variant={unitPreferences.waistCircumference === 'metric' ? 'contained' : 'outlined'}
                      size="small"
                      onClick={() => handleUnitPreferenceChange('waistCircumference', 'metric')}
                    >
                      Metric (cm)
                    </Button>
                    <Button
                      variant={unitPreferences.waistCircumference === 'imperial' ? 'contained' : 'outlined'}
                      size="small"
                      onClick={() => handleUnitPreferenceChange('waistCircumference', 'imperial')}
                    >
                      Imperial (in)
                    </Button>
                  </Box>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label={unitPreferences.waistCircumference === 'metric' ? 'Waist Circumference (cm)' : 'Waist Circumference (in)'}
                        type="number"
                        value={unitPreferences.waistCircumference === 'metric' ? (profile.waistCircumference || '') : (imperialMeasurements.waistInches || '')}
                        onChange={(e) => {
                          const value = parseFloat(e.target.value) || 0;
                          if (unitPreferences.waistCircumference === 'metric') {
                            handleInputChange('waistCircumference', value || undefined);
                          } else {
                            handleImperialMeasurementChange('waistInches', value);
                          }
                        }}
                        variant="outlined"
                        InputProps={{
                          endAdornment: <InputAdornment position="end">
                            {unitPreferences.waistCircumference === 'metric' ? 'cm' : 'in'}
                          </InputAdornment>,
                        }}
                      />
                    </Grid>
                    {profile.waistCircumference && profile.waistCircumference > 0 && (
                      <Grid item xs={12} md={6}>
                        <Alert severity="info" sx={{ mt: 1 }}>
                          {unitPreferences.waistCircumference === 'metric' 
                            ? `${profile.waistCircumference} cm = ${imperialMeasurements.waistInches} in`
                            : `${imperialMeasurements.waistInches} in = ${profile.waistCircumference} cm`
                          }
                        </Alert>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </Grid>

              {/* Blood Pressure */}
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Blood Pressure (Systolic)"
                  type="number"
                  value={profile.systolicBP || ''}
                  onChange={(e) => handleInputChange('systolicBP', parseInt(e.target.value) || undefined)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">mmHg</InputAdornment>,
                  }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Blood Pressure (Diastolic)"
                  type="number"
                  value={profile.diastolicBP || ''}
                  onChange={(e) => handleInputChange('diastolicBP', parseInt(e.target.value) || undefined)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">mmHg</InputAdornment>,
                  }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Heart Rate"
                  type="number"
                  value={profile.heartRate || ''}
                  onChange={(e) => handleInputChange('heartRate', parseInt(e.target.value) || undefined)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">bpm</InputAdornment>,
                  }}
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Medical History */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LocalHospitalIcon />
              <Typography variant="h6">🩺 Medical History</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <FormControl component="fieldset" fullWidth>
              <FormLabel component="legend">Check all that apply</FormLabel>
              <FormGroup>
                <Grid container>
                  {medicalConditionsOptions.map((condition) => (
                    <Grid item xs={12} md={6} key={condition}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={(profile.medicalConditions || []).includes(condition)}
                            onChange={(e) => handleArrayChange('medicalConditions', condition, e.target.checked)}
                          />
                        }
                        label={condition}
                      />
                    </Grid>
                  ))}
                </Grid>
                {(profile.medicalConditions || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other medical condition"
                      value={otherValues.medicalConditions}
                      onChange={(e) => handleOtherChange('medicalConditions', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.medicalConditions?.trim()) {
                          addOtherOption('medicalConditions', 'medicalConditions');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('medicalConditions', 'medicalConditions')}
                      disabled={!otherValues.medicalConditions?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom medical conditions */}
                {(profile.medicalConditions || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.medicalConditions || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newConditions = (profile.medicalConditions || []).filter(c => c !== item);
                          handleInputChange('medicalConditions', newConditions);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </FormGroup>
            </FormControl>
          </AccordionDetails>
        </Accordion>

        {/* Current Medications */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MedicationIcon />
              <Typography variant="h6">💊 Current Medications</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <FormControl component="fieldset" fullWidth>
              <FormLabel component="legend">Check all that apply</FormLabel>
              <FormGroup>
                <Grid container>
                  {medicationsOptions.map((medication) => (
                    <Grid item xs={12} md={6} key={medication}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={(profile.currentMedications || []).includes(medication)}
                            onChange={(e) => handleArrayChange('currentMedications', medication, e.target.checked)}
                          />
                        }
                        label={medication}
                      />
                    </Grid>
                  ))}
                </Grid>
                {(profile.currentMedications || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other medication"
                      value={otherValues.medications}
                      onChange={(e) => handleOtherChange('medications', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.medications?.trim()) {
                          addOtherOption('currentMedications', 'medications');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('currentMedications', 'medications')}
                      disabled={!otherValues.medications?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom medications */}
                {(profile.currentMedications || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.currentMedications || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newMedications = (profile.currentMedications || []).filter(m => m !== item);
                          handleInputChange('currentMedications', newMedications);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </FormGroup>
            </FormControl>
          </AccordionDetails>
        </Accordion>

        {/* Lab Values */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ScienceIcon />
              <Typography variant="h6">🧪 Most Recent Lab Values (Optional)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="A1C"
                  value={profile.labValues?.a1c || ''}
                  onChange={(e) => handleLabValueChange('a1c', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">%</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Fasting Glucose"
                  value={profile.labValues?.fastingGlucose || ''}
                  onChange={(e) => handleLabValueChange('fastingGlucose', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="LDL-C"
                  value={profile.labValues?.ldlCholesterol || ''}
                  onChange={(e) => handleLabValueChange('ldlCholesterol', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="HDL-C"
                  value={profile.labValues?.hdlCholesterol || ''}
                  onChange={(e) => handleLabValueChange('hdlCholesterol', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Triglycerides"
                  value={profile.labValues?.triglycerides || ''}
                  onChange={(e) => handleLabValueChange('triglycerides', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Total Cholesterol"
                  value={profile.labValues?.totalCholesterol || ''}
                  onChange={(e) => handleLabValueChange('totalCholesterol', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="eGFR"
                  value={profile.labValues?.egfr || ''}
                  onChange={(e) => handleLabValueChange('egfr', e.target.value)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Creatinine"
                  value={profile.labValues?.creatinine || ''}
                  onChange={(e) => handleLabValueChange('creatinine', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">µmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Potassium"
                  value={profile.labValues?.potassium || ''}
                  onChange={(e) => handleLabValueChange('potassium', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="uACR / proteinuria"
                  value={profile.labValues?.uacr || ''}
                  onChange={(e) => handleLabValueChange('uacr', e.target.value)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="ALT / AST"
                  value={profile.labValues?.alt || ''}
                  onChange={(e) => handleLabValueChange('alt', e.target.value)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Vitamin D"
                  value={profile.labValues?.vitaminD || ''}
                  onChange={(e) => handleLabValueChange('vitaminD', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">nmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="B12"
                  value={profile.labValues?.b12 || ''}
                  onChange={(e) => handleLabValueChange('b12', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">pmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Dietary Information */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <RestaurantIcon />
              <Typography variant="h6">🍽️ Dietary Information</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Type of Diet (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {dietTypeOptions.map((diet) => (
                        <Grid item xs={12} md={6} key={diet}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.dietType || []).includes(diet)}
                                onChange={(e) => handleArrayChange('dietType', diet, e.target.checked)}
                              />
                            }
                            label={diet}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </FormGroup>
                </FormControl>
                {(profile.dietType || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other diet type"
                      value={otherValues.dietType}
                      onChange={(e) => handleOtherChange('dietType', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.dietType?.trim()) {
                          addOtherOption('dietType', 'dietType');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('dietType', 'dietType')}
                      disabled={!otherValues.dietType?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom diet types */}
                {(profile.dietType || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.dietType || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newDietTypes = (profile.dietType || []).filter(d => d !== item);
                          handleInputChange('dietType', newDietTypes);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </Grid>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Current Dietary Features (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {dietaryFeaturesOptions.map((feature) => (
                        <Grid item xs={12} md={6} key={feature}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.dietaryFeatures || []).includes(feature)}
                                onChange={(e) => handleArrayChange('dietaryFeatures', feature, e.target.checked)}
                              />
                            }
                            label={feature}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </FormGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Food Allergies"
                  value={textInputs.allergies}
                  onChange={(e) => handleTextInputChange('allergies', e.target.value)}
                  onBlur={() => processTextInputToArray('allergies', 'allergies')}
                  variant="outlined"
                  multiline
                  rows={2}
                  helperText="Separate multiple allergies with commas (e.g., peanuts, shellfish, dairy)"
                  placeholder="Enter allergies separated by commas..."
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Food Items You Avoid"
                  value={textInputs.avoids}
                  onChange={(e) => handleTextInputChange('avoids', e.target.value)}
                  onBlur={() => processTextInputToArray('avoids', 'avoids')}
                  variant="outlined"
                  multiline
                  rows={2}
                  helperText="Separate multiple items with commas (e.g., spicy food, red meat, fried foods)"
                  placeholder="Enter foods you avoid separated by commas..."
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Strong Dislikes"
                  value={textInputs.strongDislikes}
                  onChange={(e) => handleTextInputChange('strongDislikes', e.target.value)}
                  onBlur={() => processTextInputToArray('strongDislikes', 'strongDislikes')}
                  variant="outlined"
                  multiline
                  rows={2}
                  helperText="Separate multiple dislikes with commas (e.g., mushrooms, Brussels sprouts, liver)"
                  placeholder="Enter dislikes separated by commas..."
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Physical Activity */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FitnessIcon />
              <Typography variant="h6">🏃 Physical Activity Profile</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Work Activity Level</FormLabel>
                  <RadioGroup
                    value={profile.workActivityLevel}
                    onChange={(e) => handleInputChange('workActivityLevel', e.target.value)}
                  >
                    <FormControlLabel value="Sedentary" control={<Radio />} label="Sedentary (e.g., desk work)" />
                    <FormControlLabel value="Moderately Active" control={<Radio />} label="Moderately Active (e.g., walking, light lifting)" />
                    <FormControlLabel value="Active" control={<Radio />} label="Active / Physical Labor" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Exercise Frequency</FormLabel>
                  <RadioGroup
                    value={profile.exerciseFrequency}
                    onChange={(e) => handleInputChange('exerciseFrequency', e.target.value)}
                  >
                    <FormControlLabel value="None" control={<Radio />} label="None" />
                    <FormControlLabel value="30-60 min/week" control={<Radio />} label="<30–60 min/week" />
                    <FormControlLabel value="60-150 min/week" control={<Radio />} label="60–150 min/week" />
                    <FormControlLabel value=">150 min/week" control={<Radio />} label=">150 min/week" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Type of Exercise (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {exerciseTypesOptions.map((exercise) => (
                        <Grid item xs={12} md={6} key={exercise}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.exerciseTypes || []).includes(exercise)}
                                onChange={(e) => handleArrayChange('exerciseTypes', exercise, e.target.checked)}
                              />
                            }
                            label={exercise}
                          />
                        </Grid>
                      ))}
                    </Grid>
                    {(profile.exerciseTypes || []).includes('Other') && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Please specify other exercise type"
                          value={otherValues.exerciseTypes}
                          onChange={(e) => handleOtherChange('exerciseTypes', e.target.value)}
                          variant="outlined"
                          sx={{ flexGrow: 1 }}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.exerciseTypes?.trim()) {
                              addOtherOption('exerciseTypes', 'exerciseTypes');
                            }
                          }}
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => addOtherOption('exerciseTypes', 'exerciseTypes')}
                          disabled={!otherValues.exerciseTypes?.trim()}
                        >
                          Add
                        </Button>
                      </Box>
                    )}
                    
                    {/* Show current custom exercise types */}
                    {(profile.exerciseTypes || []).filter(item => item.startsWith('Other:')).length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                        {(profile.exerciseTypes || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                          <Chip
                            key={index}
                            label={item.replace('Other: ', '')}
                            size="small"
                            onDelete={() => {
                              const newExerciseTypes = (profile.exerciseTypes || []).filter(e => e !== item);
                              handleInputChange('exerciseTypes', newExerciseTypes);
                            }}
                            sx={{ mr: 1, mt: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </FormGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={profile.mobilityIssues || false}
                      onChange={(e) => handleInputChange('mobilityIssues', e.target.checked)}
                    />
                  }
                  label="I have mobility or joint issues"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Lifestyle & Preferences */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HomeIcon />
              <Typography variant="h6">🧭 Lifestyle & Preferences</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Meal Prep Capability</FormLabel>
                  <RadioGroup
                    value={profile.mealPrepCapability}
                    onChange={(e) => handleInputChange('mealPrepCapability', e.target.value)}
                  >
                    <FormControlLabel value="Prepares own meals" control={<Radio />} label="Prepares own meals" />
                    <FormControlLabel value="Cooks with assistance" control={<Radio />} label="Cooks with assistance" />
                    <FormControlLabel value="Caregiver-prepared" control={<Radio />} label="Caregiver-prepared" />
                    <FormControlLabel value="Uses meal delivery service" control={<Radio />} label="Uses meal delivery service" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Eating Schedule Preference</FormLabel>
                  <RadioGroup
                    value={profile.eatingSchedule}
                    onChange={(e) => handleInputChange('eatingSchedule', e.target.value)}
                  >
                    <FormControlLabel value="3 meals/day" control={<Radio />} label="3 meals/day" />
                    <FormControlLabel value="2 meals + 1 snack" control={<Radio />} label="2 meals + 1 snack" />
                    <FormControlLabel value="Intermittent Fasting" control={<Radio />} label="Intermittent Fasting" />
                    <FormControlLabel value="Night Shift" control={<Radio />} label="Night Shift (11 pm–7 am)" />
                    <FormControlLabel value="Other" control={<Radio />} label="Other" />
                  </RadioGroup>
                  {profile.eatingSchedule === 'Other' && (
                    <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                      <TextField
                        size="small"
                        label="Please specify eating schedule"
                        value={otherValues.eatingSchedule}
                        onChange={(e) => handleOtherChange('eatingSchedule', e.target.value)}
                        variant="outlined"
                        sx={{ flexGrow: 1 }}
                        placeholder="e.g., 5 small meals, 16:8 fasting, etc."
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && otherValues.eatingSchedule?.trim()) {
                            handleInputChange('eatingSchedule', `Other: ${otherValues.eatingSchedule.trim()}`);
                            setOtherValues(prev => ({ ...prev, eatingSchedule: '' }));
                          }
                        }}
                      />
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          if (otherValues.eatingSchedule?.trim()) {
                            handleInputChange('eatingSchedule', `Other: ${otherValues.eatingSchedule.trim()}`);
                            setOtherValues(prev => ({ ...prev, eatingSchedule: '' }));
                          }
                        }}
                        disabled={!otherValues.eatingSchedule?.trim()}
                      >
                        Set
                      </Button>
                    </Box>
                  )}
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Appliances Available (uncheck those you don't have)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {appliancesOptions.map((appliance) => (
                        <Grid item xs={12} md={6} key={appliance}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.availableAppliances || []).includes(appliance)}
                                onChange={(e) => handleArrayChange('availableAppliances', appliance, e.target.checked)}
                              />
                            }
                            label={appliance}
                          />
                        </Grid>
                      ))}
                    </Grid>
                    {(profile.availableAppliances || []).includes('Other') && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Please specify other appliance"
                          value={otherValues.appliances}
                          onChange={(e) => handleOtherChange('appliances', e.target.value)}
                          variant="outlined"
                          sx={{ flexGrow: 1 }}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.appliances?.trim()) {
                              addOtherOption('availableAppliances', 'appliances');
                            }
                          }}
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => addOtherOption('availableAppliances', 'appliances')}
                          disabled={!otherValues.appliances?.trim()}
                        >
                          Add
                        </Button>
                      </Box>
                    )}
                    
                    {/* Show current custom appliances */}
                    {(profile.availableAppliances || []).filter(item => item.startsWith('Other:')).length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                        {(profile.availableAppliances || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                          <Chip
                            key={index}
                            label={item.replace('Other: ', '')}
                            size="small"
                            onDelete={() => {
                              const newAppliances = (profile.availableAppliances || []).filter(a => a !== item);
                              handleInputChange('availableAppliances', newAppliances);
                            }}
                            sx={{ mr: 1, mt: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </FormGroup>
                </FormControl>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Goals & Readiness */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrackChangesIcon />
              <Typography variant="h6">🎯 Goals & Readiness to Change</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Primary Goals (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {primaryGoalsOptions.map((goal) => (
                        <Grid item xs={12} md={6} key={goal}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.primaryGoals || []).includes(goal)}
                                onChange={(e) => handleArrayChange('primaryGoals', goal, e.target.checked)}
                              />
                            }
                            label={goal}
                          />
                        </Grid>
                      ))}
                    </Grid>
                    {(profile.primaryGoals || []).includes('Other') && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Please specify other goal"
                          value={otherValues.goals}
                          onChange={(e) => handleOtherChange('goals', e.target.value)}
                          variant="outlined"
                          sx={{ flexGrow: 1 }}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.goals?.trim()) {
                              addOtherOption('primaryGoals', 'goals');
                            }
                          }}
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => addOtherOption('primaryGoals', 'goals')}
                          disabled={!otherValues.goals?.trim()}
                        >
                          Add
                        </Button>
                      </Box>
                    )}
                    
                    {/* Show current custom goals */}
                    {(profile.primaryGoals || []).filter(item => item.startsWith('Other:')).length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                        {(profile.primaryGoals || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                          <Chip
                            key={index}
                            label={item.replace('Other: ', '')}
                            size="small"
                            onDelete={() => {
                              const newGoals = (profile.primaryGoals || []).filter(g => g !== item);
                              handleInputChange('primaryGoals', newGoals);
                            }}
                            sx={{ mr: 1, mt: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </FormGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Readiness to Change</FormLabel>
                  <RadioGroup
                    value={profile.readinessToChange}
                    onChange={(e) => handleInputChange('readinessToChange', e.target.value)}
                  >
                    <FormControlLabel value="Not ready" control={<Radio />} label="Not ready" />
                    <FormControlLabel value="Thinking about it" control={<Radio />} label="Thinking about it" />
                    <FormControlLabel value="Ready to take action" control={<Radio />} label="Ready to take action" />
                    <FormControlLabel value="Already making changes" control={<Radio />} label="Already making changes" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={profile.wantsWeightLoss || false}
                        onChange={(e) => handleInputChange('wantsWeightLoss', e.target.checked)}
                      />
                    }
                    label="Patient wants weight loss"
                  />
                  <FormControl fullWidth sx={{ mt: 2 }}>
                    <FormLabel>Suggested Calorie Target</FormLabel>
                    <RadioGroup
                      value={profile.calorieTarget}
                      onChange={(e) => handleInputChange('calorieTarget', e.target.value)}
                    >
                      <FormControlLabel value="1500" control={<Radio />} label="1500 kcal" />
                      <FormControlLabel value="1800" control={<Radio />} label="1800 kcal" />
                      <FormControlLabel value="2000" control={<Radio />} label="2000 kcal" />
                      <FormControlLabel value="2200" control={<Radio />} label="2200 kcal" />
                      <FormControlLabel value="Other" control={<Radio />} label="Custom calorie target" />
                    </RadioGroup>
                    {profile.calorieTarget === 'Other' && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Custom calorie target"
                          value={otherValues.calorieTarget}
                          onChange={(e) => handleOtherChange('calorieTarget', e.target.value)}
                          variant="outlined"
                          type="number"
                          inputProps={{ min: 1000, max: 5000 }}
                          sx={{ width: 200 }}
                          placeholder="e.g., 2500"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.calorieTarget?.trim()) {
                              handleInputChange('calorieTarget', `${otherValues.calorieTarget.trim()}`);
                              setOtherValues(prev => ({ ...prev, calorieTarget: '' }));
                            }
                          }}
                        />
                        <Typography variant="body2" color="text.secondary">kcal/day</Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            if (otherValues.calorieTarget.trim()) {
                              handleInputChange('calorieTarget', `${otherValues.calorieTarget.trim()}`);
                              setOtherValues(prev => ({ ...prev, calorieTarget: '' }));
                            }
                          }}
                          disabled={!otherValues.calorieTarget?.trim()}
                        >
                          Set
                        </Button>
                      </Box>
                    )}
                  </FormControl>
                </Box>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit}
            sx={{
              px: 6,
              py: 2,
              fontSize: '1.2rem',
              fontWeight: 'bold',
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              '&:hover': {
                background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.primary.main})`,
                transform: 'translateY(-2px)',
                boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {submitButtonText}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default UserProfileForm; 