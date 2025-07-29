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
  Grid,
  Icon,
  LinearProgress,
  Switch,
  FormControlLabel,
  Checkbox,
  Fade,
  Slide,
  Zoom,
  useTheme,
  keyframes,
  Card,
  CardContent,
  Slider,
  Chip,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { isValidToken } from '../utils/auth';
import UserProfileForm from './UserProfileForm';
import RecipeList from './RecipeList';
import ShoppingList from './ShoppingList';
import { UserProfile, MealPlanData, Recipe, ShoppingItem } from '../types';
import config from '../config/environment';

// Import icons
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import DownloadIcon from '@mui/icons-material/Download';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import ReplayIcon from '@mui/icons-material/Replay';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import SendIcon from '@mui/icons-material/Send';

// Animations
const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
  100% { transform: translateY(0px); }
`;

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const shimmer = keyframes`
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
`;

const gradientShift = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

const steps = ['Profile', 'Meal Plan', 'Recipes', 'Shopping List'];

type EditableMealType = 'breakfast' | 'lunch' | 'dinner' | 'snacks';
const editableMealTypes: EditableMealType[] = ['breakfast', 'lunch', 'dinner', 'snacks'];

function stripDayPrefix(meal: string) {
  return meal.replace(/^Day \d+:\s*/, '');
}

const MealPlanRequest: React.FC = () => {
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [mealPlan, setMealPlan] = useState<MealPlanData | null>(null);
  const [recipes, setRecipes] = useState<Recipe[] | null>(null);
  const [shoppingList, setShoppingList] = useState<ShoppingItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editableMealPlan, setEditableMealPlan] = useState<MealPlanData | null>(null);
  const [recipeProgress, setRecipeProgress] = useState<number>(0);
  const [generatingRecipes, setGeneratingRecipes] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{ message: string; severity: 'success' | 'error' | 'info' } | null>(null);
  const [usePreviousPlan, setUsePreviousPlan] = useState(false);
  const [hasGeneratedMealPlan, setHasGeneratedMealPlan] = useState(false);
  const [selectedDays, setSelectedDays] = useState(7); // Default to 7 days
  const navigate = useNavigate();

  useEffect(() => {
    setLoaded(true);
  }, []);

  useEffect(() => {
    const loadSavedProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await fetch(`${config.API_URL}/user/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data && data.profile) {
            setUserProfile(data.profile);
          }
        }
      } catch (error) {
        console.error('Error loading profile:', error);
      }
    };

    loadSavedProfile();
  }, []);

  const handleProfileSubmit = async (profile: UserProfile) => {
    setUserProfile(profile);
    setActiveStep(1);
    setHasGeneratedMealPlan(false);
    setMealPlan(null);
    setEditableMealPlan(null);
    // Do NOT auto-generate meal plan here
  };

  const fetchPreviousMealPlan = async (): Promise<MealPlanData | null> => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return null;
      
      const response = await fetch(`${config.API_URL}/meal_plans`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (!response.ok) return null;
      
      const data = await response.json();
      console.log('Fetched meal plans for previous plan lookup:', data);
      
      // Get permanently deleted IDs (same logic as MealPlanHistory)
      const getDeletedIds = (): string[] => {
        try {
          const stored = localStorage.getItem('deleted_meal_plan_ids');
          return stored ? JSON.parse(stored) : [];
        } catch {
          return [];
        }
      };
      
      const deletedIds = getDeletedIds();
      console.log('Deleted IDs to filter out:', deletedIds);
      
      // Filter out permanently deleted meal plans
      const availablePlans = (data.meal_plans || []).filter((plan: MealPlanData) => {
        return plan.id && !deletedIds.includes(plan.id);
      });
      
      console.log('Available plans after filtering deleted ones:', availablePlans.length);
      
      // Sort by date (newest first)
      const sortedPlans = availablePlans.sort((a: MealPlanData, b: MealPlanData) => {
        const dateA = new Date(a.created_at || 0).getTime();
        const dateB = new Date(b.created_at || 0).getTime();
        return dateB - dateA; // Newest first
      });
      
      const mostRecentPlan = sortedPlans.length > 0 ? sortedPlans[0] : null; // First element = newest
      console.log('Most recent meal plan for reference:', mostRecentPlan ? mostRecentPlan.id : 'None');
      
      return mostRecentPlan;
    } catch (error) {
      console.error('Error fetching previous meal plan:', error);
      return null;
    }
  };

  const handleMealPlanGenerate = async (currentProfile?: UserProfile) => {
    setError(null);
    setLoading(true);
    setRecipeProgress(0);
    setGeneratingRecipes(false);

    const profileToUse = currentProfile || userProfile;

    if (!profileToUse) {
      setError('User profile is required');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      console.log('🔄 Starting meal plan generation...');
      console.log('Toggle state - usePreviousPlan:', usePreviousPlan);

      // Fetch previous meal plan if toggle is ON
      const previousMealPlan = usePreviousPlan ? await fetchPreviousMealPlan() : null;
      
      if (usePreviousPlan) {
        console.log('✅ Previous meal plan fetched:', previousMealPlan);
        if (previousMealPlan) {
          console.log('📋 Previous meal plan details:');
          console.log('- ID:', previousMealPlan.id);
          console.log('- Created:', previousMealPlan.created_at);
          console.log('- Breakfast:', previousMealPlan.breakfast);
          console.log('- Lunch:', previousMealPlan.lunch);
          console.log('- Dinner:', previousMealPlan.dinner);
          console.log('- Snacks:', previousMealPlan.snacks);
        } else {
          console.log('⚠️ No previous meal plan found, will create fresh one');
        }
      } else {
        console.log('🆕 Creating fresh meal plan (toggle is OFF)');
      }

      console.log('🚀 Sending request to backend with:');
      console.log('- User profile:', profileToUse);
      console.log('- Previous meal plan:', previousMealPlan);

              const response = await fetch(`${config.API_URL}/generate-meal-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          user_profile: profileToUse, 
          previous_meal_plan: previousMealPlan,
          days: selectedDays 
        }),
      });

      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate meal plan');
      }

      console.log('✅ Meal plan generated successfully:', data);

      // Validate the meal plan data structure
      const requiredKeys = ['breakfast', 'lunch', 'dinner', 'snacks', 'dailyCalories', 'macronutrients'];
      const missingKeys = requiredKeys.filter(key => !(key in data));
      
      if (missingKeys.length > 0) {
        throw new Error(`Invalid meal plan data. Missing: ${missingKeys.join(', ')}`);
      }

      // Validate array lengths
      const mealTypes = ['breakfast', 'lunch', 'dinner', 'snacks'];
      for (const type of mealTypes) {
        if (!Array.isArray(data[type])) {
          throw new Error(`Invalid meal plan data. ${type} should be an array`);
        }
      }

      // Validate macronutrients
      const macroKeys = ['protein', 'carbs', 'fats'];
      for (const key of macroKeys) {
        if (typeof data.macronutrients[key] !== 'number') {
          throw new Error(`Invalid meal plan data. macronutrients.${key} should be a number`);
        }
      }

      if (typeof data.dailyCalories !== 'number') {
        throw new Error('Invalid meal plan data. dailyCalories should be a number');
      }

      setMealPlan(data);
      setEditableMealPlan(data);
      setHasGeneratedMealPlan(true);
    } catch (err) {
      console.error('❌ Meal plan generation error:', err);
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

  const handleConfirmMealPlan = async () => {
    setMealPlan(editableMealPlan);
    setActiveStep(2);
    // Do NOT save to backend here
  };

  const handleRecipeGenerate = async () => {
    if (!mealPlan) return;
    setLoading(false);
    setGeneratingRecipes(true);
    setError(null);
    setSaveStatus(null);
    setRecipes([]);
    setRecipeProgress(0);
    
    const token = localStorage.getItem('token');
    if (!token) {
      setSaveStatus({ message: 'Authentication token not found. Please log in.', severity: 'error' });
      navigate('/login');
      setGeneratingRecipes(false);
      return;
    }

    try {
      console.log('Token used for /generate-recipe:', token);
      
      // 🔧 FIXED: Generate unique recipes only, not duplicates for each day
      const uniqueMeals = new Set<string>();
      
      // Collect all unique meals from the meal plan
      editableMealTypes.forEach((mealType) => {
        (mealPlan[mealType] as string[]).forEach((meal: string) => {
          // Remove any "Day X:" prefix first to get the raw meal name
          const withoutDayPrefix = stripDayPrefix(meal);

          const cleanMeal = withoutDayPrefix.trim()
            .replace(/\(.*?\)/g, '') // Remove parenthetical notes like "(smaller portion)"
            .replace(/\+.*$/g, '') // Remove additions like "+ Greek yogurt"
            .replace(/with extra.*$/g, '') // Remove "with extra vegetables" etc.
            .replace(/instead of.*$/g, '') // Remove "instead of rice/bread" etc.
            .trim();
          
          if (cleanMeal && cleanMeal !== "Not specified") {
            uniqueMeals.add(cleanMeal);
          }
        });
      });

      const mealItems = Array.from(uniqueMeals).map(meal => ({ name: meal }));
      console.log(`Generating recipes for ${mealItems.length} unique meals:`, mealItems.map(m => m.name));
      
      const total = mealItems.length;
      const newRecipes: Recipe[] = [];
      
      for (let i = 0; i < mealItems.length; i++) {
        const { name } = mealItems[i];
        console.log(`Requesting recipe for: ${name}`);
        
                  const response = await fetch(`${config.API_URL}/generate-recipe`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ meal_name: name, user_profile: userProfile }),
        });
        
        console.log(`Response status for ${name}:`, response.status);
        
        if (response.status === 401) {
          localStorage.removeItem('token');
          setError('Your session has expired. Please log in again.');
          setSaveStatus({ message: 'Session expired. Please log in again to continue generating recipes.', severity: 'error' });
          setGeneratingRecipes(false);
          navigate('/login');
          return;
        }
        
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
      
      // Save all recipes to backend
      try {
        const saveResponse = await fetch(`${config.API_URL}/user/recipes`, {
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
        
        setSaveStatus({ 
          message: `Successfully generated ${newRecipes.length} unique recipes!`, 
          severity: 'success' 
        });
      } catch (saveErr) {
        const errorMessage = saveErr instanceof Error ? saveErr.message : 'Failed to save recipes';
        setError(errorMessage);
        setSaveStatus({ message: `Error saving recipes: ${errorMessage}`, severity: 'error' });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred during recipe generation';
      setError(errorMessage);
      setSaveStatus({ message: errorMessage, severity: 'error' });
    } finally {
      setGeneratingRecipes(false);
      setTimeout(() => setSaveStatus(null), 7000);
    }
  };

  const handleShoppingListGenerate = async () => {
    if (!recipes || recipes.length === 0) {
      setError('No recipes available to generate a shopping list.');
      setSaveStatus({ message: 'Please generate recipes first.', severity: 'info' });
      setTimeout(() => setSaveStatus(null), 7000);
      return;
    }
    setLoading(true);
    setError(null);
    setSaveStatus(null);

    const token = localStorage.getItem('token');
    if (!token) {
      setSaveStatus({ message: 'Authentication token not found. Please log in.', severity: 'error' });
      navigate('/login');
      setLoading(false);
      return;
    }

    try {
      // Step 1: Generate the shopping list
              const generateResponse = await fetch(`${config.API_URL}/generate-shopping-list`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(recipes),
      });

      if (!generateResponse.ok) {
        const errorText = await generateResponse.text().catch(() => 'Failed to parse error from shopping list generation');
        throw new Error(`Failed to generate shopping list: ${errorText}`);
      }
      const shoppingListData: ShoppingItem[] = await generateResponse.json();
      setShoppingList(shoppingListData);

      // Do NOT save the shopping list to history here. Only display it.
      setSaveStatus({ message: 'Shopping list generated successfully!', severity: 'success' });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred while processing the shopping list';
      setError(errorMessage);
      setSaveStatus({ message: errorMessage, severity: 'error' });
    } finally {
      setLoading(false);
      setTimeout(() => setSaveStatus(null), 7000);
    }
  };

  // New function to save the full meal plan including recipes, shopping list, and consolidated PDF
  const handleSaveFullMealPlan = async () => {
    if (!mealPlan || !recipes || !shoppingList) {
      setError('Meal plan, recipes, or shopping list not available to save.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token || !isValidToken(token)) {
        localStorage.removeItem('token');
        localStorage.removeItem('isAdmin');
        setError('Your session has expired. Please refresh the page and log in again to save your meal plan.');
        setLoading(false);
        return;
      }

      // Step 1: Generate and save the consolidated PDF
      console.log('Generating consolidated PDF for saving...');
      let pdfInfo = null;
      
      try {
        const pdfResponse = await fetch(`${config.API_URL}/save-consolidated-pdf`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            meal_plan: mealPlan,
            recipes: recipes,
            shopping_list: shoppingList,
          }),
        });

        if (pdfResponse.ok) {
          const pdfResult = await pdfResponse.json();
          pdfInfo = pdfResult.pdf_info;
          console.log('Consolidated PDF saved:', pdfInfo);
        } else {
          console.warn('Failed to save consolidated PDF, continuing without it...');
        }
      } catch (pdfError) {
        console.warn('Error saving consolidated PDF:', pdfError);
        // Continue saving without PDF - don't let this stop the meal plan save
      }

      // Step 2: Save the full meal plan with PDF reference
      const fullMealPlan = {
        ...mealPlan,
        recipes: recipes,
        shopping_list: shoppingList,
        consolidated_pdf: pdfInfo, // Include PDF info if available
      };

      console.log('Saving full meal plan:', fullMealPlan);

              const response = await fetch(`${config.API_URL}/save-full-meal-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(fullMealPlan),
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token');
          localStorage.removeItem('isAdmin');
          setError('Your session has expired. Please refresh the page and log in again to save your meal plan.');
          setLoading(false);
          return;
        }
        
        const errorText = await response.text();
        let errorMessage = 'Failed to save meal plan';
        
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        
        throw new Error(errorMessage);
      }

      console.log('Full meal plan saved successfully with consolidated PDF.');
      navigate('/meal_plans'); // Redirect to history page after saving
    } catch (err) {
      console.error('Error saving full meal plan:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while saving the meal plan.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (type: 'meal-plan' | 'recipes' | 'shopping-list') => {
    setLoading(true);
    setError(null);
    try {
      let response;
      
      if (type === 'recipes') {
        // Use the new dedicated recipe export endpoint that fetches from database
        response = await fetch(`${config.API_URL}/export/recipes`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          // No body needed - the endpoint fetches recipes from database
        });
      } else {
        // Use the generic export endpoint for other types
        response = await fetch(`${config.API_URL}/export/${type}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({
            meal_plan: type === 'meal-plan' ? mealPlan : null,
            shopping_list: type === 'shopping-list' ? shoppingList : null,
          }),
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to export ${type}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Create more descriptive filenames
      const dateStr = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
      let filename;
      if (type === 'recipes') {
        filename = `recipe-collection-${dateStr}.pdf`;
      } else if (type === 'meal-plan') {
        filename = `meal-plan-${dateStr}.pdf`;
      } else if (type === 'shopping-list') {
        filename = `shopping-list-${dateStr}.pdf`;
      } else {
        filename = `${type}-${dateStr}.pdf`;
      }
      
      a.download = filename;
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
      
      // Send the current meal plan data instead of letting backend fetch from database
      const response = await fetch(`${config.API_URL}/export/consolidated-meal-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          meal_plan: mealPlan,
          recipes: recipes,
          shopping_list: shoppingList,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to download PDF' }));
        throw new Error(errorData.detail || 'Failed to download PDF');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // Extract filename from content-disposition header if available
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'consolidated-meal-plan.pdf';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch.length > 1) {
          filename = filenameMatch[1];
        }
      }
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while downloading the PDF.');
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const getMealArray = (plan: MealPlanData, mealType: keyof Pick<MealPlanData, 'breakfast' | 'lunch' | 'dinner' | 'snacks'>): string[] => {
    return Array.isArray(plan[mealType]) ? (plan[mealType] as string[]) : [];
  };

  const renderEditableMealPlan = () => {
    if (!editableMealPlan) return null;
    
    // Generate day labels with real dates starting from today
    const generateDayLabels = (numDays: number) => {
      const labels = [];
      const today = new Date();
      const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      
      for (let i = 0; i < numDays; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        const dayName = dayNames[date.getDay()];
        const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        labels.push({
          dayNumber: `Day ${i + 1}`,
          dayName: dayName,
          date: monthDay,
          fullLabel: i === 0 ? `Day 1 - Today (${dayName})` : `Day ${i + 1} - ${dayName}`,
          shortLabel: i === 0 ? `Day 1\nToday (${dayName})` : `Day ${i + 1}\n${dayName}`
        });
      }
      return labels;
    };
    
    const dayLabels = generateDayLabels(selectedDays);
    
    return (
      <Box sx={{ mt: 2, overflow: 'auto' }}>
        <Typography variant="h5" sx={{ mb: 3, textAlign: 'center', fontWeight: 'bold', color: 'primary.main' }}>
          📅 {selectedDays}-Day Meal Plan
        </Typography>
        
        <Card sx={{ 
          borderRadius: 3, 
          overflow: 'hidden',
          boxShadow: 3,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        }}>
          <Box sx={{ overflow: 'auto' }}>
            <table style={{ 
              width: '100%', 
              borderCollapse: 'collapse',
              minWidth: `${Math.max(600, selectedDays * 150)}px`
            }}>
              {/* Header Row */}
              <thead>
                <tr>
                  <th style={{
                    padding: '16px 12px',
                    backgroundColor: theme.palette.primary.main,
                    color: 'white',
                    fontWeight: 'bold',
                    textAlign: 'center',
                    border: '1px solid rgba(0,0,0,0.1)',
                    position: 'sticky',
                    left: 0,
                    zIndex: 10,
                    minWidth: '120px'
                  }}>
                    Meal
                  </th>
                                     {dayLabels.map((dayLabel) => (
                     <th key={dayLabel.dayNumber} style={{
                       padding: '16px 12px',
                       backgroundColor: theme.palette.primary.main,
                       color: 'white',
                       fontWeight: 'bold',
                       textAlign: 'center',
                       border: '1px solid rgba(0,0,0,0.1)',
                       minWidth: '200px',
                       whiteSpace: 'pre-line'
                     }}>
                       {dayLabel.shortLabel}
                     </th>
                   ))}
                </tr>
              </thead>
              
              {/* Body Rows */}
              <tbody>
                {editableMealTypes.map((mealType, mealIndex) => (
                  <tr key={mealType}>
                    <td style={{
                      padding: '12px',
                      backgroundColor: theme.palette.grey[100],
                      fontWeight: 'bold',
                      textTransform: 'capitalize',
                      border: '1px solid rgba(0,0,0,0.1)',
                      position: 'sticky',
                      left: 0,
                      zIndex: 5,
                      fontSize: '14px',
                      color: theme.palette.primary.main,
                      textAlign: 'center'
                    }}>
                      {mealType === 'breakfast' && '🍳'} 
                      {mealType === 'lunch' && '🥗'} 
                      {mealType === 'dinner' && '🍽️'} 
                      {mealType === 'snacks' && '🍎'} {' '}
                      {mealType.charAt(0).toUpperCase() + mealType.slice(1)}
                    </td>
                                         {dayLabels.map((dayLabel, dayIndex) => (
                       <td key={dayLabel.dayNumber} style={{
                         padding: '8px',
                         border: '1px solid rgba(0,0,0,0.1)',
                         backgroundColor: mealIndex % 2 === 0 ? '#ffffff' : '#fafafa'
                       }}>
                         <input
                           type="text"
                           value={stripDayPrefix(editableMealPlan[mealType][dayIndex] || '')}
                           onChange={e => handleMealPlanFieldChange(mealType, dayIndex, e.target.value)}
                           style={{ 
                             width: '100%', 
                             padding: '8px', 
                             borderRadius: '6px', 
                             border: '1px solid #ddd',
                             fontSize: '14px',
                             lineHeight: '1.4',
                             minHeight: '36px',
                             resize: 'vertical'
                           }}
                           placeholder={`Enter ${mealType} for ${dayLabel.dayName}`}
                         />
                       </td>
                     ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </Card>
        
        <Typography variant="caption" sx={{ mt: 2, display: 'block', textAlign: 'center', color: 'text.secondary' }}>
          💡 Click on any cell to edit your meal plan. The table scrolls horizontally for plans with many days.
        </Typography>
      </Box>
    );
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return <UserProfileForm onSubmit={handleProfileSubmit} initialProfile={userProfile || undefined} />;
      case 1:
        return (
          <Box>
            {editableMealPlan && renderEditableMealPlan()}
          </Box>
        );
      case 2:
        return (
          <Box>
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
            {shoppingList && <ShoppingList shoppingList={shoppingList} />}
          </Box>
        );
      default:
        return null;
    }
  };

  const renderActionButtons = () => {
    switch (activeStep) {
      case 0:
        return null;
      case 1:
        return (
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 1, 
            justifyContent: 'center',
            alignItems: 'center',
            width: '100%'
          }}>
            {!hasGeneratedMealPlan && (
              <Button
                variant="contained"
                color="primary"
                onClick={() => handleMealPlanGenerate()}
                disabled={loading}
                startIcon={loading && activeStep === 1 ? <CircularProgress size={20} color="inherit" /> : <RestaurantMenuIcon />}
                sx={{ 
                  borderRadius: 3, 
                  px: 3,
                  minWidth: { xs: '120px', sm: 'auto' },
                  fontSize: { xs: '0.8rem', sm: '0.875rem' },
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                  },
                }}
              >
                {loading && activeStep === 1 ? '⏳ Generating...' : '🚀 Generate Meal Plan Now'}
              </Button>
            )}
            {hasGeneratedMealPlan && (
              <Button
                variant="outlined"
                onClick={() => handleMealPlanGenerate()}
                disabled={loading}
                startIcon={loading && activeStep === 1 ? <CircularProgress size={20} color="inherit" /> : <ReplayIcon />}
                sx={{ 
                  borderRadius: 3, 
                  px: 3,
                  minWidth: { xs: '120px', sm: 'auto' },
                  fontSize: { xs: '0.8rem', sm: '0.875rem' },
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    backgroundColor: theme.palette.primary.main,
                    color: 'white',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
                  },
                }}
              >
                {loading && activeStep === 1 ? '⏳ Generating...' : '🔄 Re-generate Meal Plan'}
              </Button>
            )}
            {editableMealPlan && !loading && (
              <>
                <Button
                  variant="contained"
                  onClick={handleConfirmMealPlan}
                  disabled={!editableMealPlan || loading}
                  endIcon={<PlaylistAddCheckIcon />}
                  sx={{ 
                    borderRadius: 3, 
                    px: 3,
                    minWidth: { xs: '120px', sm: 'auto' },
                    fontSize: { xs: '0.8rem', sm: '0.875rem' },
                    color: 'white',
                    background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                    },
                  }}
                >
                  ✅ Proceed to Recipe Generation
                </Button>
                <Button
                  variant="text"
                  onClick={() => handleExport('meal-plan')}
                  disabled={!mealPlan || loading}
                  startIcon={<DownloadIcon />}
                  sx={{ 
                    borderRadius: 3, 
                    px: 3,
                    minWidth: { xs: '120px', sm: 'auto' },
                    fontSize: { xs: '0.8rem', sm: '0.875rem' },
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      backgroundColor: theme.palette.action.hover,
                    },
                  }}
                >
                  📄 Export Meal Plan
                </Button>
              </>
            )}
          </Box>
        );
      case 2: // Recipes Step
        return (
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 1, 
            justifyContent: 'center',
            alignItems: 'center',
            width: '100%'
          }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleRecipeGenerate}
              disabled={generatingRecipes || !mealPlan}
              startIcon={generatingRecipes ? <CircularProgress size={20} color="inherit" /> : <RestaurantMenuIcon />}
              sx={{ 
                borderRadius: 3, 
                px: 3,
                color: 'white',
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                },
              }}
            >
              {generatingRecipes
                ? '⏳ Generating Recipes...'
                : recipes && recipes.length > 0
                  ? '🔄 Re-generate Recipes'
                  : '🍳 Start Recipe Generation'}
            </Button>
            {recipes && recipes.length > 0 && (
              <>
                <Button
                  variant="text"
                  onClick={() => handleExport('recipes')}
                  disabled={loading}
                  startIcon={<DownloadIcon />}
                  sx={{ 
                    borderRadius: 3, 
                    px: 3,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      backgroundColor: theme.palette.action.hover,
                    },
                  }}
                >
                  📄 Export Recipes
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={handleNext}
                  disabled={loading || generatingRecipes}
                  endIcon={<NavigateNextIcon />}
                  sx={{ 
                    borderRadius: 3, 
                    px: 3,
                    color: 'white',
                    background: `linear-gradient(45deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                    },
                  }}
                >
                  🛒 Proceed to Shopping List
                </Button>
              </>
            )}
          </Box>
        );
      case 3: // Shopping List Step
        return (
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 1, 
            justifyContent: 'center',
            alignItems: 'center',
            width: '100%'
          }}>
            <Button
              variant="contained"
              onClick={handleShoppingListGenerate}
              disabled={loading || !recipes || recipes.length === 0}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ShoppingCartIcon />}
              sx={{ 
                borderRadius: 3, 
                px: 3,
                color: 'white',
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                },
              }}
            >
              {loading ? '⏳ Generating...' : '🛒 Start Shopping List Generation'}
            </Button>
            {shoppingList && shoppingList.length > 0 && (
              <>
                <Button
                  variant="text"
                  onClick={() => handleExport('shopping-list')}
                  disabled={loading}
                  startIcon={<DownloadIcon />}
                  sx={{ 
                    borderRadius: 3, 
                    px: 3,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      backgroundColor: theme.palette.action.hover,
                    },
                  }}
                >
                  📄 Export Shopping List
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleDownloadConsolidatedPDF}
                  disabled={loading || !mealPlan || !recipes || !shoppingList}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <DownloadIcon />}
                  sx={{ 
                    borderRadius: 3, 
                    px: 3,
                    background: `linear-gradient(45deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`,
                    color: 'white',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                    },
                  }}
                >
                  📦 Download Consolidated PDF
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSaveFullMealPlan}
                  disabled={loading || !mealPlan || !recipes || !shoppingList}
                  sx={{ 
                    borderRadius: 3, 
                    px: 3,
                    color: 'white',
                    background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                    },
                  }}
                >
                  {loading ? <CircularProgress size={24} /> : '💾 Save Meal Plan + PDF'}
                </Button>
              </>
            )}
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(-45deg, ${theme.palette.primary.main}08, ${theme.palette.secondary.main}08, ${theme.palette.primary.main}05, ${theme.palette.secondary.main}05)`,
        backgroundSize: '400% 400%',
        animation: `${gradientShift} 15s ease infinite`,
        py: 4,
      }}
    >
      <Container maxWidth="lg" sx={{ 
        px: { xs: 1, sm: 3 } // Reduce horizontal padding on mobile
      }}>
        <Fade in={loaded} timeout={1000}>
          <Paper 
            elevation={0}
            sx={{ 
              p: { xs: 1.5, sm: 3, md: 4 }, // Slightly reduce padding on mobile 
              borderRadius: 4,
              background: 'rgba(255,255,255,0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.3)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: '-200px',
                width: '200px',
                height: '100%',
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                animation: `${shimmer} 3s infinite`,
              },
            }}
          >
            <Slide direction="down" in={loaded} timeout={1200}>
              <Typography 
                variant="h3" 
                component="h1" 
                gutterBottom 
                align="center" 
                sx={{ 
                  fontWeight: 800,
                  mb: 4,
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  textShadow: '0 4px 8px rgba(0,0,0,0.1)',
                }}
              >
                🍽️ Personalized Meal Plan Generator
              </Typography>
            </Slide>

            <Zoom in={loaded} timeout={1500}>
              <Card
                sx={{
                  mb: 4,
                  borderRadius: 3,
                  background: 'rgba(255,255,255,0.8)',
                  border: `2px solid ${theme.palette.primary.main}20`,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
                  },
                }}
              >
                <CardContent>
                  <Stepper 
                    activeStep={activeStep} 
                    alternativeLabel 
                    sx={{ 
                      '& .MuiStepIcon-root': {
                        transition: 'all 0.3s ease',
                        '&.Mui-active': {
                          animation: `${pulse} 2s ease-in-out infinite`,
                        },
                      },
                    }}
                  >
                    {steps.map((label, index) => (
                      <Step key={label}>
                        <StepLabel
                          sx={{
                            '& .MuiStepLabel-label': {
                              fontWeight: activeStep === index ? 'bold' : 'normal',
                              transition: 'all 0.3s ease',
                            },
                          }}
                        >
                          {label}
                        </StepLabel>
                      </Step>
                    ))}
                  </Stepper>
                </CardContent>
              </Card>
            </Zoom>

            {/* Meal Plan Type Selection - only show on meal plan step */}
            {activeStep === 1 && (
              <Fade in={loaded} timeout={2000}>
                <Card
                  sx={{
                    mb: 3,
                    borderRadius: 4,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}15, ${theme.palette.primary.main}08)`,
                    border: `2px solid ${theme.palette.primary.main}30`,
                    transition: 'all 0.3s ease',
                    animation: `${float} 4s ease-in-out infinite`,
                    '&:hover': {
                      transform: 'translateY(-3px)',
                      boxShadow: `0 8px 20px ${theme.palette.primary.main}30`,
                    },
                  }}
                >
                  <CardContent sx={{ py: 3, px: 4 }}>
                    <Typography 
                      variant="h6" 
                      fontWeight="bold"
                      sx={{ 
                        color: theme.palette.primary.main,
                        mb: 3,
                        textAlign: 'center',
                      }}
                    >
                      🍽️ Choose Your Meal Plan Type
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <Card
                          sx={{
                            p: 2,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            border: !usePreviousPlan 
                              ? `2px solid ${theme.palette.info.main}` 
                              : `1px solid ${theme.palette.divider}`,
                            background: !usePreviousPlan 
                              ? `linear-gradient(135deg, ${theme.palette.info.main}15, ${theme.palette.info.main}08)` 
                              : theme.palette.background.paper,
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
                            },
                          }}
                          onClick={() => setUsePreviousPlan(false)}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                            <FormControlLabel
                              control={
                                <Checkbox
                                  checked={!usePreviousPlan}
                                  onChange={() => setUsePreviousPlan(false)}
                                  color="info"
                                />
                              }
                              label=""
                              sx={{ m: 0 }}
                            />
                            <Box sx={{ flex: 1 }}>
                              <Typography 
                                variant="subtitle1" 
                                fontWeight="bold"
                                sx={{ 
                                  color: !usePreviousPlan ? theme.palette.info.main : theme.palette.text.primary,
                                  mb: 1,
                                }}
                              >
                                🆕 Fresh Start
                              </Typography>
                              <Typography 
                                variant="body2" 
                                color="text.secondary"
                                sx={{ lineHeight: 1.5 }}
                              >
                                Create a completely new meal plan from scratch based on your preferences
                              </Typography>
                            </Box>
                          </Box>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Card
                          sx={{
                            p: 2,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            border: usePreviousPlan 
                              ? `2px solid ${theme.palette.success.main}` 
                              : `1px solid ${theme.palette.divider}`,
                            background: usePreviousPlan 
                              ? `linear-gradient(135deg, ${theme.palette.success.main}15, ${theme.palette.success.main}08)` 
                              : theme.palette.background.paper,
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
                            },
                          }}
                          onClick={() => setUsePreviousPlan(true)}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                            <FormControlLabel
                              control={
                                <Checkbox
                                  checked={usePreviousPlan}
                                  onChange={() => setUsePreviousPlan(true)}
                                  color="success"
                                />
                              }
                              label=""
                              sx={{ m: 0 }}
                            />
                            <Box sx={{ flex: 1 }}>
                              <Typography 
                                variant="subtitle1" 
                                fontWeight="bold"
                                sx={{ 
                                  color: usePreviousPlan ? theme.palette.success.main : theme.palette.text.primary,
                                  mb: 1,
                                }}
                              >
                                🔄 Similar to Previous Plan
                              </Typography>
                              <Typography 
                                variant="body2" 
                                color="text.secondary"
                                sx={{ lineHeight: 1.5 }}
                              >
                                Generate a new meal plan similar to your most recent plan, with some variety for new experiences
                              </Typography>
                            </Box>
                          </Box>
                        </Card>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Fade>
            )}

            {/* Day Selector - only show on meal plan step */}
            {activeStep === 1 && (
              <Fade in={loaded} timeout={2200}>
                <Card
                  sx={{
                    mb: 3,
                    borderRadius: 4,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}15, ${theme.palette.primary.main}08)`,
                    border: `2px solid ${theme.palette.primary.main}30`,
                    transition: 'all 0.3s ease',
                    animation: `${float} 4s ease-in-out infinite`,
                    '&:hover': {
                      transform: 'translateY(-3px)',
                      boxShadow: `0 8px 20px ${theme.palette.primary.main}30`,
                    },
                  }}
                >
                  <CardContent sx={{ py: 3, px: 4 }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Typography 
                        variant="h6" 
                        fontWeight="bold"
                        sx={{ 
                          color: theme.palette.primary.main,
                          mb: 2,
                          textAlign: 'center',
                        }}
                      >
                        📅 Select Meal Plan Duration
                      </Typography>
                      <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{ mb: 3, textAlign: 'center', lineHeight: 1.5 }}
                      >
                        Choose how many days you want your meal plan to cover (1-7 days)
                      </Typography>
                      
                      {/* Day Selector Slider */}
                      <Box sx={{ width: '100%', maxWidth: 400, px: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          {[1, 2, 3, 4, 5, 6, 7].map((day) => (
                            <Typography
                              key={day}
                              variant="caption"
                              sx={{
                                color: selectedDays === day ? theme.palette.primary.main : theme.palette.text.secondary,
                                fontWeight: selectedDays === day ? 'bold' : 'normal',
                                transition: 'all 0.2s ease',
                              }}
                            >
                              {day}
                            </Typography>
                          ))}
                        </Box>
                                                 <Slider
                           value={selectedDays}
                           onChange={(_: Event, newValue: number | number[]) => setSelectedDays(newValue as number)}
                           min={1}
                           max={7}
                           step={1}
                           marks
                           valueLabelDisplay="auto"
                           valueLabelFormat={(value: number) => `${value} day${value > 1 ? 's' : ''}`}
                          sx={{
                            color: theme.palette.primary.main,
                            '& .MuiSlider-thumb': {
                              backgroundColor: theme.palette.primary.main,
                              border: `3px solid ${theme.palette.background.paper}`,
                              boxShadow: `0 0 0 8px ${theme.palette.primary.main}20`,
                              '&:hover': {
                                boxShadow: `0 0 0 12px ${theme.palette.primary.main}30`,
                              },
                            },
                            '& .MuiSlider-track': {
                              backgroundColor: theme.palette.primary.main,
                              height: 6,
                            },
                            '& .MuiSlider-rail': {
                              backgroundColor: theme.palette.primary.light,
                              height: 6,
                            },
                            '& .MuiSlider-mark': {
                              backgroundColor: theme.palette.primary.main,
                              height: 8,
                              width: 8,
                              borderRadius: '50%',
                            },
                            '& .MuiSlider-markActive': {
                              backgroundColor: theme.palette.primary.dark,
                            },
                          }}
                        />
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                          <Chip
                            label={`${selectedDays} day${selectedDays > 1 ? 's' : ''} meal plan`}
                            color="primary"
                            variant="filled"
                            sx={{
                              fontWeight: 'bold',
                              fontSize: '0.9rem',
                              px: 2,
                              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                            }}
                          />
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Fade>
            )}

            {error && (
              <Slide direction="down" in={true} timeout={500}>
                <Alert 
                  severity="error" 
                  sx={{ 
                    mb: 2, 
                    borderRadius: 3,
                    animation: `${pulse} 1s ease`,
                  }} 
                  onClose={() => setError(null)}
                >
                  {error}
                </Alert>
              </Slide>
            )}

            {saveStatus && (
              <Slide direction="down" in={true} timeout={500}>
                <Alert 
                  severity={saveStatus.severity} 
                  sx={{ 
                    mt: 2, 
                    mb: 2, 
                    borderRadius: 3,
                    animation: `${pulse} 1s ease`,
                  }} 
                  onClose={() => setSaveStatus(null)}
                >
                  {saveStatus.message}
                </Alert>
              </Slide>
            )}

            <Fade in={loaded} timeout={2500}>
              <Card
                sx={{
                  mt: 3, 
                  mb: 3,
                  borderRadius: 4,
                  background: 'rgba(255,255,255,0.9)',
                  border: `1px solid ${theme.palette.divider}`,
                  minHeight: '400px',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
                  },
                }}
              >
                <CardContent sx={{ 
                  p: { xs: 1, sm: 2, md: 4 } // Mobile: 8px, Tablet: 16px, Desktop: 32px
                }}>
                  {renderStepContent(activeStep)}
                </CardContent>
              </Card>
            </Fade>
            
            {generatingRecipes && activeStep === 2 && (
              <Zoom in={true} timeout={300}>
                <Card
                  sx={{
                    mb: 3,
                    borderRadius: 3,
                    background: `linear-gradient(135deg, ${theme.palette.success.main}15, ${theme.palette.success.main}08)`,
                    border: `2px solid ${theme.palette.success.main}30`,
                  }}
                >
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography 
                      variant="h6" 
                      gutterBottom
                      sx={{ 
                        color: theme.palette.success.main,
                        fontWeight: 'bold',
                      }}
                    >
                      🍳 Generating Recipes... {recipeProgress.toFixed(0)}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={recipeProgress}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4,
                          background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.light})`,
                        },
                      }}
                    />
                  </CardContent>
                </Card>
              </Zoom>
            )}

            <Slide direction="up" in={loaded} timeout={3000}>
              <Card
                sx={{
                  borderRadius: 4,
                  background: `linear-gradient(135deg, ${theme.palette.grey[50]}, ${theme.palette.grey[100]})`,
                  border: `1px solid ${theme.palette.divider}`,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: { xs: 'column', sm: 'row' },
                    justifyContent: { xs: 'center', sm: 'space-between' }, 
                    alignItems: 'center', 
                    gap: 2, 
                    minHeight: '56px' 
                  }}>
                    {/* Back Button - Left Side */}
                    <Button
                      color="inherit"
                      disabled={activeStep === 0 || loading || generatingRecipes}
                      onClick={handleBack}
                      variant="outlined"
                      startIcon={<NavigateBeforeIcon />}
                      sx={{ 
                        borderRadius: 3, 
                        px: 3,
                        flexShrink: 0,
                        width: { xs: '100%', sm: 'auto' },
                        maxWidth: { xs: '200px', sm: 'none' },
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
                        },
                      }}
                    >
                      Back
                    </Button>
                    
                    {/* Generate Meal Plan Button - Center */}
                    <Box sx={{ 
                      display: 'flex', 
                      gap: 1, 
                      justifyContent: 'center', 
                      flexWrap: 'wrap',
                      width: { xs: '100%', sm: 'auto' },
                      maxWidth: { xs: '100%', sm: 'none' },
                      flex: { xs: 'none', sm: 1 }
                    }}>
                      {renderActionButtons()}
                    </Box>
                    
                    {/* Next Button - Right Side */}
                    {activeStep !== 0 && activeStep < steps.length - 1 && ( 
                      <Button
                        variant="contained"
                        onClick={handleNext}
                        disabled={loading || generatingRecipes || 
                          (activeStep === 0 && !userProfile) ||
                          (activeStep === 1 && (!editableMealPlan || !mealPlan)) ||
                          (activeStep === 2 && (!recipes || recipes.length === 0))
                        }
                        endIcon={<NavigateNextIcon />}
                        sx={{ 
                          borderRadius: 3, 
                          px: 3,
                          flexShrink: 0,
                          width: { xs: '100%', sm: 'auto' },
                          maxWidth: { xs: '200px', sm: 'none' },
                          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                          transition: 'all 0.3s ease',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                          },
                        }}
                      >
                        Next
                      </Button>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Slide>
          </Paper>
        </Fade>
      </Container>
    </Box>
  );
};

export default MealPlanRequest; 