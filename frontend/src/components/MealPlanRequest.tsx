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
import { useNavigate } from 'react-router-dom';
import UserProfileForm from './UserProfileForm';
import MealPlan from './MealPlan';
import RecipeList from './RecipeList';
import ShoppingList from './ShoppingList';
import { UserProfile, MealPlanData, Recipe, ShoppingItem } from '../types';

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
  };

  const handleMealPlanGenerate = async () => {
    if (!userProfile) {
      setError('User profile is required');
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

      const response = await fetch('http://localhost:8000/generate-meal-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ user_profile: userProfile }),
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

  const handleConfirmMealPlan = () => {
    setMealPlan(editableMealPlan);
    setActiveStep(2);
  };

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
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
            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  onClick={handleMealPlanGenerate}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Generate Meal Plan'}
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
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                {editableMealPlan && (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleConfirmMealPlan}
                  >
                    Proceed to Recipe Generation
                  </Button>
                )}
              </Box>
            </Box>
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
            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  onClick={handleRecipeGenerate}
                  disabled={generatingRecipes}
                >
                  {generatingRecipes ? <CircularProgress size={24} /> : 'Generate Recipes'}
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
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                {recipes && (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => setActiveStep(3)}
                  >
                    Proceed to Shopping List Creation
                  </Button>
                )}
              </Box>
            </Box>
          </Box>
        );
      case 3:
        return (
          <Box>
            {shoppingList && <ShoppingList shoppingList={shoppingList} />}
            <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center' }}>
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