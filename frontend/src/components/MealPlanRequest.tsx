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
  Fade,
  Slide,
  Zoom,
  useTheme,
  keyframes,
  Card,
  CardContent,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { isValidToken } from '../utils/auth';
import UserProfileForm from './UserProfileForm';
import MealPlan from './MealPlan';
import RecipeList from './RecipeList';
import ShoppingList from './ShoppingList';
import { UserProfile, MealPlanData, Recipe, ShoppingItem } from '../types';

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
  const navigate = useNavigate();

  useEffect(() => {
    setLoaded(true);
  }, []);

  useEffect(() => {
    const loadSavedProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await fetch('http://localhost:8000/user/profile', {
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
      
      const response = await fetch('http://localhost:8000/meal_plans', {
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

      const response = await fetch('http://localhost:8000/generate-meal-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ user_profile: profileToUse, previous_meal_plan: previousMealPlan }),
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
        if (response.status === 401) {
          // Token expired or invalid
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
        setSaveStatus({ message: 'Recipes generated and saved successfully!', severity: 'success' });
      } catch (saveErr) {
        const errorMessage = saveErr instanceof Error ? saveErr.message : 'Failed to save recipes';
        setError(errorMessage);
        setSaveStatus({ message: `Error saving recipes: ${errorMessage}`, severity: 'error' });
      }
      // Do NOT advance to next step automatically
      // setActiveStep(3);
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
      const generateResponse = await fetch('http://localhost:8000/generate-shopping-list', {
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
        const pdfResponse = await fetch('http://localhost:8000/save-consolidated-pdf', {
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

      const response = await fetch('http://localhost:8000/save-full-meal-plan', {
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
      navigate('/meal-plan/history'); // Redirect to history to see the saved plan
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
      const response = await fetch('http://localhost:8000/export/consolidated-meal-plan', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
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
    const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return (
      <Box sx={{ mt: 2 }}>
        {editableMealTypes.map((mealType) => (
          <Box key={mealType} sx={{ mb: 4 }}>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 'bold',
                textTransform: 'capitalize',
                mb: 2,
                color: 'primary.main',
                letterSpacing: 1,
                borderBottom: '2px solid',
                borderColor: 'primary.light',
                pb: 1,
                pl: 1,
                background: 'linear-gradient(90deg, #e3f2fd 0%, #fff 100%)',
                borderRadius: '8px 8px 0 0',
                boxShadow: 1,
                width: 'fit-content',
                display: 'inline-block',
              }}
            >
              {mealType.charAt(0).toUpperCase() + mealType.slice(1)}
            </Typography>
            {daysOfWeek.map((day, idx) => (
              <Box key={day} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography sx={{ width: 100, fontWeight: 500 }}>{day}:</Typography>
                <input
                  type="text"
                  value={stripDayPrefix(editableMealPlan[mealType][idx] || '')}
                  onChange={e => handleMealPlanFieldChange(mealType, idx, e.target.value)}
                  style={{ flex: 1, padding: 6, borderRadius: 4, border: '1px solid #ccc' }}
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
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center' }}>
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
            <Button
              variant="contained"
              onClick={handleConfirmMealPlan}
              disabled={!editableMealPlan || loading}
              endIcon={<PlaylistAddCheckIcon />}
              sx={{ 
                borderRadius: 3, 
                px: 3,
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
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  backgroundColor: theme.palette.action.hover,
                },
              }}
            >
              📄 Export Meal Plan
            </Button>
          </Box>
        );
      case 2: // Recipes Step
        return (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleRecipeGenerate}
              disabled={generatingRecipes || !mealPlan}
              startIcon={generatingRecipes ? <CircularProgress size={20} color="inherit" /> : <RestaurantMenuIcon />}
              sx={{ 
                borderRadius: 3, 
                px: 3,
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
                  : '🍳 Try Generating Recipes'}
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
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              onClick={handleShoppingListGenerate}
              disabled={loading || !recipes || recipes.length === 0}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ShoppingCartIcon />}
              sx={{ 
                borderRadius: 3, 
                px: 3,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                },
              }}
            >
              {loading ? '⏳ Generating...' : '🛒 Generate Shopping List'}
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
      <Container maxWidth="lg">
        <Fade in={loaded} timeout={1000}>
          <Paper 
            elevation={0}
            sx={{ 
              p: { xs: 2, sm: 3, md: 4 }, 
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

            {/* Toggle for 70/30 similarity - only show on meal plan step */}
            {activeStep === 1 && (
              <Fade in={loaded} timeout={2000}>
                <Card
                  sx={{
                    mb: 3,
                    borderRadius: 4,
                    background: usePreviousPlan 
                      ? `linear-gradient(135deg, ${theme.palette.success.main}20, ${theme.palette.success.main}10)`
                      : `linear-gradient(135deg, ${theme.palette.info.main}15, ${theme.palette.info.main}08)`,
                    border: usePreviousPlan
                      ? `2px solid ${theme.palette.success.main}40`
                      : `2px solid ${theme.palette.info.main}30`,
                    transition: 'all 0.3s ease',
                    animation: `${float} 4s ease-in-out infinite`,
                    '&:hover': {
                      transform: 'translateY(-3px)',
                      boxShadow: usePreviousPlan
                        ? `0 8px 20px ${theme.palette.success.main}30`
                        : `0 8px 20px ${theme.palette.info.main}30`,
                    },
                  }}
                >
                  <CardContent sx={{ py: 3, px: 4 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography 
                          variant="h6" 
                          fontWeight="bold"
                          sx={{ 
                            color: usePreviousPlan ? theme.palette.success.main : theme.palette.info.main,
                            mb: 1,
                          }}
                        >
                          {usePreviousPlan ? '🔄 Similar to Previous Plan' : '🆕 Fresh Start'}
                        </Typography>
                        <Typography 
                          variant="body2" 
                          color="text.secondary"
                          sx={{ lineHeight: 1.5 }}
                        >
                          {usePreviousPlan 
                            ? 'Generate a new meal plan similar to your most recent plan, with some variety for new experiences'
                            : 'Create a completely new meal plan from scratch based on your preferences'
                          }
                        </Typography>
                      </Box>
                      <Switch 
                        checked={usePreviousPlan}
                        onChange={(e) => setUsePreviousPlan(e.target.checked)}
                        color="primary"
                        sx={{
                          ml: 3,
                          transform: 'scale(1.2)',
                          '& .MuiSwitch-thumb': {
                            backgroundColor: usePreviousPlan ? theme.palette.success.main : theme.palette.info.main,
                          },
                          '& .MuiSwitch-track': {
                            backgroundColor: usePreviousPlan ? theme.palette.success.light : theme.palette.info.light,
                          },
                        }}
                      />
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
                <CardContent sx={{ p: 4 }}>
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
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
                    <Button
                      color="inherit"
                      disabled={activeStep === 0 || loading || generatingRecipes}
                      onClick={handleBack}
                      variant="outlined"
                      startIcon={<NavigateBeforeIcon />}
                      sx={{ 
                        borderRadius: 3, 
                        px: 3,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
                        },
                      }}
                    >
                      Back
                    </Button>
                    
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
                      {renderActionButtons()}
                    </Box>
                    
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