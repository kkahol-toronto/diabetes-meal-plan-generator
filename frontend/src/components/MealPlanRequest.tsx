import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import ReplayIcon from '@mui/icons-material/Replay';
import { useNavigate } from 'react-router-dom';
import UserProfileForm from './UserProfileForm';
import MealPlan from './MealPlan';
import RecipeList from './RecipeList';
import ShoppingList from './ShoppingList';
import { UserProfile, MealPlanData, ShoppingItem, Recipe } from '../types/index';

const steps = ['Profile', 'Meal Plan', 'Recipes', 'Shopping List'];

type EditableMealType = 'breakfast' | 'lunch' | 'dinner' | 'snacks';
const editableMealTypes: EditableMealType[] = ['breakfast', 'lunch', 'dinner', 'snacks'];

function toCamelCase(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(toCamelCase);
  } else if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj).map(([key, value]) => [
        key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase()),
        toCamelCase(value)
      ])
    );
  }
  return obj;
}

function toSnakeCase(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(toSnakeCase);
  } else if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj).map(([key, value]) => [
        key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`),
        toSnakeCase(value)
      ])
    );
  }
  return obj;
}

// Function to validate and sanitize meal plan data (similar to what we did for UserProfile)
const validateMealPlanData = (data: any): MealPlanData | null => {
  if (!data || typeof data !== 'object') return null;

  const requiredStringArrayKeys: (keyof MealPlanData)[] = ['breakfast', 'lunch', 'dinner', 'snacks'];
  for (const key of requiredStringArrayKeys) {
    if (!Array.isArray(data[key]) || !data[key].every((item: any) => typeof item === 'string')) {
      // Attempt to fix or return null if critical
      console.warn(`MealPlanData: Missing or invalid ${key}.`);
      data[key] = []; // Default to empty array or handle error
    }
  }

  if (typeof data.dailyCalories !== 'number') {
    console.warn(`MealPlanData: Missing or invalid dailyCalories.`);
    data.dailyCalories = 0; // Default or handle error
  }

  if (!data.macronutrients || typeof data.macronutrients !== 'object') {
    console.warn(`MealPlanData: Missing macronutrients object.`);
    data.macronutrients = { protein: 0, carbs: 0, fats: 0 }; // Default
  }
  if (typeof data.macronutrients.protein !== 'number') data.macronutrients.protein = 0;
  if (typeof data.macronutrients.carbs !== 'number') data.macronutrients.carbs = 0;
  if (typeof data.macronutrients.fats !== 'number') data.macronutrients.fats = 0;
  
  // Add any other specific checks from your backend validation if necessary
  // e.g., ensuring meal arrays have 7 items for a weekly plan
  requiredStringArrayKeys.forEach(key => {
    if (Array.isArray(data[key])) {
        while (data[key].length < 7) {
            data[key].push("Not specified");
        }
        data[key] = data[key].slice(0, 7); // Ensure it's not more than 7
    }
  });

  return data as MealPlanData;
};

const MealPlanRequest: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(() => {
    const savedProfile = localStorage.getItem('userProfile');
    if (savedProfile) {
      try {
        const parsed = JSON.parse(savedProfile);
        // Ensure all necessary fields are present and correctly typed
        return {
          ...parsed,
          medicalConditions: parsed.medicalConditions || [],
          dietaryRestrictions: parsed.dietaryRestrictions || [],
          healthConditions: parsed.healthConditions || [],
          foodPreferences: parsed.foodPreferences || [],
          allergies: parsed.allergies || [],
          dietTypes: parsed.dietTypes || [],
          dietFeatures: parsed.dietFeatures || [],
          wantsWeightLoss: parsed.wantsWeightLoss || false,
          systolicBP: parsed.systolicBP ? Number(parsed.systolicBP) : undefined,
          diastolicBP: parsed.diastolicBP ? Number(parsed.diastolicBP) : undefined,
          heartRate: parsed.heartRate ? Number(parsed.heartRate) : undefined,
        };
      } catch (e) {
        console.error("Error parsing userProfile from localStorage", e);
        localStorage.removeItem('userProfile'); // Clear corrupted data
        return null;
      }
    }
    return null;
  });
  const [mealPlan, setMealPlan] = useState<MealPlanData | null>(() => {
    const savedMealPlanString = localStorage.getItem('mealPlan');
    if (savedMealPlanString) {
      try {
        const parsed = JSON.parse(savedMealPlanString);
        const validated = validateMealPlanData(parsed);
        if (validated) {
          console.log("Loaded validated meal plan from localStorage:", validated);
          return validated;
        }
      } catch (e) {
        console.error("Error parsing mealPlan from localStorage", e);
        localStorage.removeItem('mealPlan'); // Clear corrupted data
      }
    }
    return null;
  });
  const [recipes, setRecipes] = useState<Recipe[] | null>(() => {
    const savedRecipes = localStorage.getItem('recipes');
    return savedRecipes ? JSON.parse(savedRecipes) : null;
  });
  const [shoppingList, setShoppingList] = useState<ShoppingItem[] | null>(() => {
    const savedShoppingList = localStorage.getItem('shoppingList');
    return savedShoppingList ? JSON.parse(savedShoppingList) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editableMealPlan, setEditableMealPlan] = useState<MealPlanData | null>(null);
  const [recipeProgress, setRecipeProgress] = useState<number>(0);
  const [generatingRecipes, setGeneratingRecipes] = useState(false);
  const navigate = useNavigate();

  // Effect to sync state with localStorage
  useEffect(() => {
    if (userProfile) {
      localStorage.setItem('userProfile', JSON.stringify(userProfile));
    }
  }, [userProfile]);

  useEffect(() => {
    if (mealPlan) {
      localStorage.setItem('mealPlan', JSON.stringify(mealPlan));
    }
  }, [mealPlan]);

  useEffect(() => {
    if (recipes) {
      localStorage.setItem('recipes', JSON.stringify(recipes));
    }
  }, [recipes]);

  useEffect(() => {
    if (shoppingList) {
      localStorage.setItem('shoppingList', JSON.stringify(shoppingList));
    }
  }, [shoppingList]);

  useEffect(() => {
    const loadSavedProfile = async () => {
      // Only load from backend if not already populated from localStorage
      if (userProfile && Object.keys(userProfile).length > 0) {
        console.log("Profile already loaded from localStorage, skipping backend fetch initially.", userProfile);
        return; 
      }
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          console.log('No token found, using localStorage data if available');
          return;
        }
        
        const response = await fetch('http://localhost:8000/user/profile', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
        });
        
        if (response.ok) {
          const rawData = await response.json();
          const profileData = rawData.profile || rawData;
          if (profileData && Object.keys(profileData).length > 0) {
            const camelCaseData = toCamelCase(profileData);
            const validatedBackendProfile = {
              ...camelCaseData,
              medicalConditions: camelCaseData.medicalConditions || [],
              dietaryRestrictions: camelCaseData.dietaryRestrictions || [],
              healthConditions: camelCaseData.healthConditions || [],
              foodPreferences: camelCaseData.foodPreferences || [],
              allergies: camelCaseData.allergies || [],
              dietTypes: camelCaseData.dietTypes || [],
              dietFeatures: camelCaseData.dietFeatures || [],
              wantsWeightLoss: camelCaseData.wantsWeightLoss || false,
              systolicBP: camelCaseData.systolicBP ? Number(camelCaseData.systolicBP) : undefined,
              diastolicBP: camelCaseData.diastolicBP ? Number(camelCaseData.diastolicBP) : undefined,
              heartRate: camelCaseData.heartRate ? Number(camelCaseData.heartRate) : undefined,
            };
            setUserProfile(validatedBackendProfile);
            localStorage.setItem('userProfile', JSON.stringify(validatedBackendProfile));
          }
        } else {
          console.error('Failed to fetch profile from backend');
        }
      } catch (error) {
        console.error('Error in loadSavedProfile:', error);
      }
    };

    const loadLastMealPlanFromBackend = async () => {
      // Only fetch if not already populated from localStorage recently
      // Or if we want to prioritize backend on every load, remove this condition
      if (mealPlan && Object.keys(mealPlan).length > 0) {
         console.log("Meal plan already loaded from localStorage, skipping backend fetch initially.");
         return;
      }
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch('http://localhost:8000/user/meal-plans', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          if (data && data.length > 0) {
            const latestMealPlanFromBackend = data.sort((a: any, b: any) => 
              new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            )[0];
            const validatedAndCamelCased = validateMealPlanData(toCamelCase(latestMealPlanFromBackend));
            if (validatedAndCamelCased) {
              // Create a new object with only MealPlanData fields
              const strictlyTypedMealPlan: MealPlanData = {
                breakfast: validatedAndCamelCased.breakfast,
                lunch: validatedAndCamelCased.lunch,
                dinner: validatedAndCamelCased.dinner,
                snacks: validatedAndCamelCased.snacks,
                dailyCalories: validatedAndCamelCased.dailyCalories,
                macronutrients: validatedAndCamelCased.macronutrients,
              };
              console.log("Setting meal plan from backend (strictly typed):", strictlyTypedMealPlan);
              setMealPlan(strictlyTypedMealPlan);
            }
          }
        }
      } catch (error) {
        console.error('Error loading last meal plan from backend:', error);
      }
    };

    loadSavedProfile();
    loadLastMealPlanFromBackend(); // Renamed for clarity
  }, []); // Empty dependency array: runs once on mount

  // Effect to initialize/reset editableMealPlan when mealPlan is loaded/changed/cleared
  useEffect(() => {
    if (mealPlan) {
      console.log("Setting editableMealPlan FROM mealPlan:", JSON.stringify(mealPlan, null, 2));
      setEditableMealPlan(mealPlan); // mealPlan is now guaranteed to be strictly MealPlanData
    } else {
      console.log("Clearing editableMealPlan because mealPlan is null");
      setEditableMealPlan(null); // Clear editableMealPlan if mealPlan is null
    }
  }, [mealPlan]);

  // Callback to update userProfile from UserProfileForm
  const handleProfileUpdate = (updatedProfileData: Partial<UserProfile>) => {
    console.log("handleProfileUpdate - Received raw updatedProfileData:", JSON.stringify(updatedProfileData, null, 2));
    const camelCasedUpdate = toCamelCase(updatedProfileData);
    console.log("handleProfileUpdate - After toCamelCase(updatedProfileData):", JSON.stringify(camelCasedUpdate, null, 2));

    setUserProfile(prevProfile => {
      const baseProfile = prevProfile || {};
      console.log("handleProfileUpdate - prevProfile:", JSON.stringify(baseProfile, null, 2));
      
      // Merge camelCased updates. If there are direct UserProfile fields like `calorieTarget` vs `dailyCalories`,
      // explicit mapping might be needed if toCamelCase doesn't resolve it.
      const newProfile = { ...baseProfile, ...camelCasedUpdate } as UserProfile;
      console.log("handleProfileUpdate - newProfile (merged camelCasedUpdate with prevProfile):", JSON.stringify(newProfile, null, 2));

      // Validation and ensuring correct types, using ONLY camelCase keys from UserProfile type
      const validatedProfile: UserProfile = {
        name: newProfile.name || '',
        age: Number(newProfile.age) || 0,
        gender: newProfile.gender || '',
        weight: Number(newProfile.weight) || 0,
        height: Number(newProfile.height) || 0,
        ethnicity: newProfile.ethnicity || '',
        medicalConditions: Array.isArray(newProfile.medicalConditions) ? newProfile.medicalConditions : [],
        dietaryRestrictions: Array.isArray(newProfile.dietaryRestrictions) ? newProfile.dietaryRestrictions : [],
        healthConditions: Array.isArray(newProfile.healthConditions) ? newProfile.healthConditions : [],
        foodPreferences: Array.isArray(newProfile.foodPreferences) ? newProfile.foodPreferences : [],
        allergies: Array.isArray(newProfile.allergies) ? newProfile.allergies : [],
        dietTypes: Array.isArray(newProfile.dietTypes) ? newProfile.dietTypes : [], 
        dietFeatures: Array.isArray(newProfile.dietFeatures) ? newProfile.dietFeatures : [],
        wantsWeightLoss: typeof newProfile.wantsWeightLoss === 'boolean' ? newProfile.wantsWeightLoss : false,
        systolicBP: newProfile.systolicBP ? Number(newProfile.systolicBP) : undefined,
        diastolicBP: newProfile.diastolicBP ? Number(newProfile.diastolicBP) : undefined,
        heartRate: newProfile.heartRate ? Number(newProfile.heartRate) : undefined,
        calorieTarget: newProfile.calorieTarget ? Number(newProfile.calorieTarget) : undefined,
        waistCircumference: newProfile.waistCircumference ? Number(newProfile.waistCircumference) : undefined,
        // Ensure "other" fields are included as empty strings if not provided, assuming they are string type in UserProfile
        otherMedicalCondition: typeof newProfile.otherMedicalCondition === 'string' ? newProfile.otherMedicalCondition : '',
        otherDietaryRestriction: typeof newProfile.otherDietaryRestriction === 'string' ? newProfile.otherDietaryRestriction : '',
        otherHealthCondition: typeof newProfile.otherHealthCondition === 'string' ? newProfile.otherHealthCondition : '',
        otherFoodPreference: typeof newProfile.otherFoodPreference === 'string' ? newProfile.otherFoodPreference : '',
        otherAllergy: typeof newProfile.otherAllergy === 'string' ? newProfile.otherAllergy : '',
      } as UserProfile;

      console.log("handleProfileUpdate - validatedProfile (to be set and stored):", JSON.stringify(validatedProfile, null, 2));
      localStorage.setItem('userProfile', JSON.stringify(validatedProfile));
      return validatedProfile;
    });
  };

  const handleProfileSubmit = async (profileFromForm: UserProfile) => {
    console.log("handleProfileSubmit - Received profileFromForm:", JSON.stringify(profileFromForm, null, 2));
    setLoading(true);
    setError(null);

    // Call handleProfileUpdate to ensure the central state (userProfile) and localStorage
    // are updated with the latest data from the form.
    // handleProfileUpdate will internally camelCase and validate.
    handleProfileUpdate(profileFromForm); 

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        setLoading(false);
        return;
      }

      // For the backend submission, use profileFromForm (which is the form's current state,
      // assumed to be camelCased and structurally correct UserProfile).
      // Convert it to snake_case as expected by the backend.
      const profileToSend = toSnakeCase(profileFromForm); 
      console.log('Attempting to save profile (snake_case from profileFromForm):', JSON.stringify(profileToSend, null, 2));

      const response = await fetch('http://localhost:8000/user/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ profile: profileToSend }),
      });

      if (!response.ok) {
        const responseData = await response.json().catch(() => ({ detail: 'Failed to save profile and parse error response.' }));
        throw new Error(responseData.detail || `Failed to save profile. Status: ${response.status}`);
      }
      console.log("Profile saved successfully, advancing to step 1.");
      setActiveStep(1);
    } catch (err) {
      console.error('Error saving profile:', err);
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred while saving your profile.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleMealPlanGenerate = async () => {
    if (!userProfile) {
      setError('User profile is required');
      return;
    }
    console.log("handleMealPlanGenerate - Using userProfile from state:", JSON.stringify(userProfile, null, 2));

    setMealPlan(null);
    setEditableMealPlan(null);
    setLoading(true);
    setError(null);
    setRecipes([]);
    setRecipeProgress(0);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        setLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/generate-meal-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ user_profile: toSnakeCase(userProfile) }),
      });
      // Added log for sent body
      console.log("handleMealPlanGenerate - Sent body to backend:", JSON.stringify({ user_profile: toSnakeCase(userProfile) }, null, 2));

      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        setLoading(false);
        return;
      }

      const data = await response.json();
      console.log("Raw meal plan data from backend:", JSON.stringify(data, null, 2));
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate meal plan');
      }

      // Initial validation (already present)
      const requiredKeys = ['breakfast', 'lunch', 'dinner', 'snacks', 'dailyCalories', 'macronutrients'];
      const missingKeys = requiredKeys.filter(key => !(key in data));
      if (missingKeys.length > 0) {
        throw new Error(`Invalid meal plan data. Missing: ${missingKeys.join(', ')}`);
      }
      const mealTypes = ['breakfast', 'lunch', 'dinner', 'snacks'];
      for (const type of mealTypes) {
        if (!Array.isArray(data[type])) {
          throw new Error(`Invalid meal plan data. ${type} should be an array`);
        }
      }
      const macroKeys = ['protein', 'carbs', 'fats'];
      for (const key of macroKeys) {
        if (typeof data.macronutrients[key] !== 'number') {
          throw new Error(`Invalid meal plan data. macronutrients.${key} should be a number`);
        }
      }
      if (typeof data.dailyCalories !== 'number') {
        throw new Error('Invalid meal plan data. dailyCalories should be a number');
      }

      // After initial validations pass:
      const validatedRawData = validateMealPlanData(JSON.parse(JSON.stringify(data)));
      console.log("Validated raw meal plan data:", JSON.stringify(validatedRawData, null, 2));

      if (validatedRawData) {
        // Create a new object with only MealPlanData fields
        const strictlyTypedMealPlan: MealPlanData = {
          breakfast: validatedRawData.breakfast,
          lunch: validatedRawData.lunch,
          dinner: validatedRawData.dinner,
          snacks: validatedRawData.snacks,
          dailyCalories: validatedRawData.dailyCalories,
          macronutrients: validatedRawData.macronutrients,
        };
        setMealPlan(strictlyTypedMealPlan);
        console.log("Generated and set new meal plan state (strictly typed):", strictlyTypedMealPlan);
      } else {
        console.error("Meal plan validation returned null. Original data:", data);
        setError("Failed to process the generated meal plan after validation.");
      }
    } catch (err) {
      console.error('Meal plan generation error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while generating the meal plan');
    } finally {
      setLoading(false);
    }
  };

  const handleMealPlanFieldChange = (mealType: EditableMealType, index: number, value: string) => {
    if (!editableMealPlan) return;
    setEditableMealPlan(prev => {
      if (!prev) return prev;
      const updated = { ...prev };
      const arr = [...(prev[mealType] as string[])];
      arr[index] = value;
      updated[mealType] = arr as any;
      return updated;
    });
  };

  const handleConfirmMealPlan = () => {
    if (editableMealPlan) {
      const validatedEditable = validateMealPlanData({ ...editableMealPlan });
      if (validatedEditable) {
        // Create a new object with only MealPlanData fields
        const strictlyTypedMealPlan: MealPlanData = {
          breakfast: validatedEditable.breakfast,
          lunch: validatedEditable.lunch,
          dinner: validatedEditable.dinner,
          snacks: validatedEditable.snacks,
          dailyCalories: validatedEditable.dailyCalories,
          macronutrients: validatedEditable.macronutrients,
        };
        setMealPlan(strictlyTypedMealPlan);
        console.log("Confirmed editable meal plan (strictly typed):", strictlyTypedMealPlan);
        setActiveStep(2);
      } else {
        setError("Cannot confirm invalid meal plan. Please check the details.");
      }
    } else {
      setError("No meal plan to confirm.");
    }
  };

  // Function to save the last generated recipe to local storage
  const saveLastGeneratedRecipe = (recipe: Recipe[]) => {
    localStorage.setItem('lastGeneratedRecipe', JSON.stringify(recipe));
  };

  // Function to load the last generated recipe from local storage
  const loadLastGeneratedRecipe = () => {
    const storedRecipe = localStorage.getItem('lastGeneratedRecipe');
    return storedRecipe ? JSON.parse(storedRecipe) : null;
  };

  // Load the last generated recipe on component mount
  useEffect(() => {
    const lastRecipe = loadLastGeneratedRecipe();
    if (lastRecipe) {
      setRecipes(lastRecipe);
    }
  }, []);

  // Function to save the last generated shopping list to local storage
  const saveLastGeneratedShoppingList = (list: ShoppingItem[]) => {
    localStorage.setItem('lastGeneratedShoppingList', JSON.stringify(list));
  };

  // Function to load the last generated shopping list from local storage
  const loadLastGeneratedShoppingList = () => {
    const storedList = localStorage.getItem('lastGeneratedShoppingList');
    return storedList ? JSON.parse(storedList) : null;
  };

  // Load the last generated shopping list on component mount
  useEffect(() => {
    const lastShoppingList = loadLastGeneratedShoppingList();
    if (lastShoppingList) {
      setShoppingList(lastShoppingList);
    }
  }, []);

  const handleRecipeGenerate = async () => {
    if (!mealPlan) return;
    setLoading(false);
    setGeneratingRecipes(true);
    setError(null);
    setRecipes([]);
    setRecipeProgress(0);
    try {
      const token = localStorage.getItem('token');
      console.log('Token used for /generate-recipe:', token);
      const mealItems: { mealType: EditableMealType; name: string }[] = [];
      editableMealTypes.forEach((mealType) => {
        (mealPlan[mealType] as string[]).forEach((meal: string) => {
          meal.split(',').map(dish => dish.trim()).filter(Boolean).forEach(dish => {
            mealItems.push({ mealType, name: dish });
          });
        });
      });
      console.log('Meal items to generate recipes for:', mealItems);
      const total = mealItems.length;
      const newRecipes: Recipe[] = [];
      for (let i = 0; i < mealItems.length; i++) {
        const { name } = mealItems[i];
        console.log(`Requesting recipe for: ${name}`);
        const response = await fetch('http://localhost:8000/generate-recipe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ meal_name: name, user_profile: userProfile }),
        });
        console.log(`Response status for ${name}:`, response.status);
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Failed to generate recipe for ${name}:`, errorText);
          throw new Error(`Failed to generate recipe for ${name}`);
        }
        const data = await response.json();
        console.log(`Recipe for ${name}:`, data);
        newRecipes.push(data);
        setRecipes([...newRecipes]);
        setRecipeProgress(((i + 1) / total) * 100);
      }
      // Save the last generated recipe to local storage
      saveLastGeneratedRecipe(newRecipes);
      // Save all recipes to backend
      try {
        const saveResponse = await fetch('http://localhost:8000/user/recipes', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ recipes: newRecipes }),
        });
        if (!saveResponse.ok) {
          const errorText = await saveResponse.text();
          throw new Error(`Failed to save recipes: ${errorText}`);
        }
      } catch (saveErr) {
        setError(saveErr instanceof Error ? saveErr.message : 'Failed to save recipes');
      }
      // Do NOT advance to next step automatically
      // setActiveStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setGeneratingRecipes(false);
    }
  };

  const handleShoppingListGenerate = async () => {
    if (!recipes) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/generate-shopping-list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(recipes),
      });
      if (!response.ok) {
        throw new Error('Failed to generate shopping list');
      }
      const data = await response.json();
      setShoppingList(data);
      // Save the last generated shopping list to local storage
      saveLastGeneratedShoppingList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (type: 'meal-plan' | 'recipes' | 'shopping-list') => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/export/${type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          meal_plan: type === 'meal-plan' ? mealPlan : null,
          recipes: type === 'recipes' ? recipes : null,
          shopping_list: type === 'shopping-list' ? shoppingList : null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to export ${type}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}-${new Date().toISOString()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadConsolidatedPDF = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const endpoint = 'http://localhost:8000/export/consolidated-meal-plan';
      // Use the real session_id from the mealPlan if available
      const session_id = mealPlan && (mealPlan as any).session_id ? (mealPlan as any).session_id : 'dummy-session-id';
      console.log('Download Consolidated PDF: token =', token);
      console.log('Download Consolidated PDF: endpoint =', endpoint);
      console.log('Download Consolidated PDF: session_id =', session_id);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ session_id }),
      });
      console.log('Download Consolidated PDF: response status =', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to export consolidated meal plan:', errorText);
        throw new Error('Failed to export consolidated meal plan');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `consolidated_meal_plan_${new Date().toISOString().slice(0,10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Download Consolidated PDF: error =', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    // No need to specifically load userProfile here, UserProfileForm will re-init from userProfile prop
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleNext = () => {
    // No need to specifically save userProfile here, handleProfileUpdate does it continuously
    setActiveStep((prevStep) => prevStep + 1);
  };

  const getMealArray = (plan: MealPlanData, mealType: keyof Pick<MealPlanData, 'breakfast' | 'lunch' | 'dinner' | 'snacks'>): string[] => {
    return Array.isArray(plan[mealType]) ? (plan[mealType] as string[]) : [];
  };

  const renderEditableMealPlan = () => {
    if (!editableMealPlan) return null;
    return (
      <Box sx={{ mt: 2 }}>
        {editableMealTypes.map((mealType) => (
          <Box key={mealType} sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>{mealType}</Typography>
            {(editableMealPlan[mealType] as string[]).map((item, idx) => (
              <Box key={idx} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <input
                  type="text"
                  value={item}
                  onChange={e => handleMealPlanFieldChange(mealType, idx, e.target.value)}
                  style={{ width: '80%', padding: 6, fontSize: 16, marginRight: 8 }}
                />
              </Box>
            ))}
          </Box>
        ))}
      </Box>
    );
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <UserProfileForm 
            onSubmit={handleProfileSubmit} 
            initialProfile={userProfile || undefined}
            onProfileChange={handleProfileUpdate}
          />
        );
      case 1:
        return (
          <Box>
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleMealPlanGenerate}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : (
                  <>
                    Generate Again
                    <ReplayIcon sx={{ ml: 1 }} />
                  </>
                )}
              </Button>
              {mealPlan && (
                <Button
                  variant="contained"
                  onClick={() => handleExport('meal-plan')}
                  disabled={loading}
                >
                  Export PDF
                </Button>
              )}
            </Box>
            {editableMealPlan && renderEditableMealPlan()}
          </Box>
        );
      case 2:
        return (
          <Box>
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleRecipeGenerate}
                disabled={generatingRecipes}
              >
                {generatingRecipes ? <CircularProgress size={24} /> : (
                  <>
                    Generate Again
                    <ReplayIcon sx={{ ml: 1 }} />
                  </>
                )}
              </Button>
              {recipes && (
                <Button
                  variant="contained"
                  onClick={() => handleExport('recipes')}
                  disabled={generatingRecipes}
                >
                  Export PDF
                </Button>
              )}
            </Box>
            {generatingRecipes && (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
                <CircularProgress sx={{ mb: 1 }} />
                <Typography>Generating recipes... {Math.round(recipeProgress)}%</Typography>
              </Box>
            )}
            {recipes && <RecipeList recipes={recipes} />}
          </Box>
        );
      case 3:
        return (
          <Box>
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleShoppingListGenerate}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Generate Shopping List'}
              </Button>
              {shoppingList && (
                <Button
                  variant="outlined"
                  onClick={() => handleExport('shopping-list')}
                  disabled={loading}
                >
                  Export PDF
                </Button>
              )}
              <Button
                variant="contained"
                color="secondary"
                onClick={handleDownloadConsolidatedPDF}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Download Consolidated PDF'}
              </Button>
            </Box>
            {shoppingList && <ShoppingList shoppingList={shoppingList} />}
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Create Your Meal Plan
        </Typography>

        <Box sx={{ width: '100%', mb: 4 }}>
          <Stepper activeStep={activeStep}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            disabled={activeStep === 0}
            onClick={handleBack}
          >
            Back
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={activeStep === steps.length - 1 ? () => navigate('/thank-you') : handleNext}
            disabled={activeStep === steps.length - 1 && !shoppingList}
          >
            {activeStep === steps.length - 1 ? 'Finish' : 'Next'}
          </Button>
        </Box>

        {renderStepContent(activeStep)}
      </Paper>
    </Container>
  );
};

export default MealPlanRequest; 