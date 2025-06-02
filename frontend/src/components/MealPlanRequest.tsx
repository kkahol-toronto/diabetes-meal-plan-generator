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
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
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

const steps = ['Profile', 'Meal Plan', 'Recipes', 'Shopping List'];

type EditableMealType = 'breakfast' | 'lunch' | 'dinner' | 'snacks';
const editableMealTypes: EditableMealType[] = ['breakfast', 'lunch', 'dinner', 'snacks'];

const MealPlanRequest: React.FC = () => {
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
  const navigate = useNavigate();

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
    // Immediately trigger meal plan generation
    await handleMealPlanGenerate(profile);
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

      const response = await fetch('http://localhost:8000/generate-meal-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ user_profile: profileToUse }),
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

  const handleConfirmMealPlan = async () => {
    setMealPlan(editableMealPlan);
    setActiveStep(2);
    // await handleRecipeGenerate(); // Temporarily commented out due to backend error - User to click button
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

      // Step 2: Save the generated shopping list
      if (shoppingListData && shoppingListData.length > 0) {
        try {
          const saveResponse = await fetch('http://localhost:8000/user/shopping-list', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ items: shoppingListData }), 
          });
          if (!saveResponse.ok) {
            const errorText = await saveResponse.text().catch(() => 'Failed to parse error from saving shopping list');
            throw new Error(`Failed to save shopping list: ${errorText}`);
          }
          setSaveStatus({ message: 'Shopping list generated and saved successfully!', severity: 'success' });
        } catch (saveErr) {
          const errorMessage = saveErr instanceof Error ? saveErr.message : 'Failed to save shopping list';
          setSaveStatus({ message: `Error saving shopping list: ${errorMessage}`, severity: 'error' });
        }
      } else {
         // If list is generated but empty, it's not an error, but inform the user.
        setSaveStatus({ message: 'Shopping list generated, but it was empty. Nothing to save.', severity: 'info' });
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred while processing the shopping list';
      setError(errorMessage);
      setSaveStatus({ message: errorMessage, severity: 'error' });
    } finally {
      setLoading(false);
      setTimeout(() => setSaveStatus(null), 7000);
    }
  };

  // New function to save the full meal plan including recipes and shopping list
  const handleSaveFullMealPlan = async () => {
    if (!mealPlan || !recipes || !shoppingList) {
      setError('Meal plan, recipes, or shopping list not available to save.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const fullMealPlan = {
        ...mealPlan,
        recipes: recipes,
        shopping_list: shoppingList,
      };

      console.log('Saving full meal plan:', fullMealPlan);

      // Assuming a backend endpoint exists to handle saving the full meal plan
      const response = await fetch('http://localhost:8000/save-full-meal-plan', { // NOTE: This endpoint needs to exist on the backend
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(fullMealPlan),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to save full meal plan: ${errorText}`);
      }

      console.log('Full meal plan saved successfully.');
      // Optionally navigate or show a success message
      // navigate('/meal-plan/history'); // Example navigation after saving

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
      case 0: // Profile Step
        // The UserProfileForm itself should handle its submission and enable navigation.
        // The main "Next" button in the footer will be used after profile is submitted.
        return null; // No specific action buttons here, handled by form + main nav
      case 1: // Meal Plan Step
        return (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center', mb: 2 }}>
            <Button
              variant="outlined"
              onClick={() => handleMealPlanGenerate()}
              disabled={loading}
              startIcon={loading && activeStep === 1 ? <CircularProgress size={20} color="inherit" /> : <ReplayIcon />}
              sx={{ borderRadius: '20px', px: 3 }}
            >
              {loading && activeStep === 1 ? 'Generating...' : 'Re-generate Meal Plan'}
            </Button>
            <Button
              variant="contained"
              onClick={handleConfirmMealPlan}
              disabled={!editableMealPlan || loading}
              endIcon={<PlaylistAddCheckIcon />}
              sx={{ borderRadius: '20px', px: 3 }}
            >
              Proceed to Recipe Generation
            </Button>
            <Button
              variant="text"
              onClick={() => handleExport('meal-plan')}
              disabled={!mealPlan || loading}
              startIcon={<DownloadIcon />}
              sx={{ borderRadius: '20px', px: 3 }}
            >
              Export Meal Plan
            </Button>
          </Box>
        );
      case 2: // Recipes Step
        return (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center', mb: 2 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleRecipeGenerate}
              disabled={generatingRecipes || !mealPlan}
              startIcon={generatingRecipes ? <CircularProgress size={20} color="inherit" /> : <RestaurantMenuIcon />}
              sx={{ borderRadius: '20px', px: 3 }}
            >
              {generatingRecipes
                ? 'Generating Recipes...'
                : recipes && recipes.length > 0
                  ? 'Re-generate Recipes'
                  : 'Try Generating Recipes'}
            </Button>
            {recipes && recipes.length > 0 && (
              <>
                <Button
                  variant="text"
                  onClick={() => handleExport('recipes')}
                  disabled={loading}
                  startIcon={<DownloadIcon />}
                  sx={{ borderRadius: '20px', px: 3 }}
                >
                  Export Recipes
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={handleNext}
                  disabled={loading || generatingRecipes}
                  endIcon={<NavigateNextIcon />}
                  sx={{ borderRadius: '20px', px: 3 }}
                >
                  Proceed to Shopping List
                </Button>
              </>
            )}
          </Box>
        );
      case 3: // Shopping List Step
        return (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center', mb: 2 }}>
            <Button
              variant="contained"
              onClick={handleShoppingListGenerate}
              disabled={loading || !recipes || recipes.length === 0}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ShoppingCartIcon />}
              sx={{ borderRadius: '20px', px: 3 }}
            >
              {loading ? 'Generating...' : 'Generate Shopping List'}
            </Button>
            {shoppingList && shoppingList.length > 0 && (
              <>
                <Button
                  variant="text"
                  onClick={() => handleExport('shopping-list')}
                  disabled={loading}
                  startIcon={<DownloadIcon />}
                  sx={{ borderRadius: '20px', px: 3 }}
                >
                  Export Shopping List
                </Button>
<<<<<<< HEAD
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleDownloadConsolidatedPDF}
                  disabled={loading || !mealPlan || !recipes || !shoppingList}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <DownloadIcon />}
                  sx={{ borderRadius: '20px', px: 3 }}
                >
                  Download Consolidated PDF
                </Button>
              </>
            )}
=======
              )}
              <Button
                variant="contained"
                color="secondary"
                onClick={handleDownloadConsolidatedPDF}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Download Consolidated PDF'}
              </Button>
              {/* Add Save Full Meal Plan button */}
              <Button
                variant="contained"
                color="primary"
                onClick={handleSaveFullMealPlan}
                disabled={loading || !mealPlan || !recipes || !shoppingList}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Meal Plan'}
              </Button>
            </Box>
>>>>>>> origin/changed_ui_backend_ram
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 }, borderRadius: '16px' }}>
        <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 4 }}>
          Personalized Meal Plan Generator
        </Typography>
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: '8px' }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {saveStatus && (
          <Alert severity={saveStatus.severity} sx={{ mt: 2, mb: 2, borderRadius: '8px' }} onClose={() => setSaveStatus(null)}>
            {saveStatus.message}
          </Alert>
        )}

        <Box sx={{ mt: 3, mb: 3, p: 2, border: '1px dashed grey', borderRadius: '8px', minHeight: '300px' }}>
          {renderStepContent(activeStep)}
        </Box>
        
        {generatingRecipes && activeStep === 2 && (
          <Box sx={{ width: '100%', my: 2 }}>
            <Typography variant="caption" display="block" gutterBottom align="center">
              Generating recipes... {recipeProgress.toFixed(0)}%
            </Typography>
            <LinearProgress variant="determinate" value={recipeProgress} />
          </Box>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3, p: 2, backgroundColor: 'action.hover', borderRadius: '8px' }}>
          <Button
            color="inherit"
            disabled={activeStep === 0 || loading || generatingRecipes}
            onClick={handleBack}
            variant="outlined"
            startIcon={<NavigateBeforeIcon />}
            sx={{ borderRadius: '20px', px: 3 }}
          >
            Back
          </Button>
          <Box>
            {renderActionButtons()}
          </Box>
          {/* Show Next button only if not on Profile step (handled by form) and not on the last step */}
          {activeStep !== 0 && activeStep < steps.length - 1 && ( 
             <Button
                variant="contained"
                onClick={handleNext}
                disabled={loading || generatingRecipes || 
                    (activeStep === 0 && !userProfile) || // Ensure profile is set before allowing next from step 0 if it were shown
                    (activeStep === 1 && (!editableMealPlan || !mealPlan)) || // Disable if on meal plan step and no meal plan confirmed
                    (activeStep === 2 && (!recipes || recipes.length === 0)) // Disable if on recipe step and no recipes
                }
                endIcon={<NavigateNextIcon />}
                sx={{ borderRadius: '20px', px: 3 }}
             >
                Next
             </Button>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default MealPlanRequest; 