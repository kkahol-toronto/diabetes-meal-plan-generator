import React, { useState } from 'react';
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

  const handleProfileSubmit = async (profile: UserProfile) => {
    setUserProfile(profile);
    setActiveStep(1);
  };

  const handleMealPlanGenerate = async () => {
    if (!userProfile) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/generate-meal-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ user_profile: userProfile }),
      });
      if (!response.ok) {
        throw new Error('Failed to generate meal plan');
      }
      const data = await response.json();
      setMealPlan(data);
      setEditableMealPlan(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
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
        <Button
          variant="contained"
          color="primary"
          onClick={handleConfirmMealPlan}
          sx={{ mt: 2 }}
        >
          Proceed to Recipe Generation
        </Button>
      </Box>
    );
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return <UserProfileForm onSubmit={handleProfileSubmit} />;
      case 1:
        return (
          <Box>
            {editableMealPlan && renderEditableMealPlan()}
            <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                onClick={handleMealPlanGenerate}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Generate Meal Plan'}
              </Button>
              {mealPlan && (
                <Button
                  variant="outlined"
                  onClick={() => handleExport('meal-plan')}
                  disabled={loading}
                >
                  Export PDF
                </Button>
              )}
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
            <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                onClick={handleRecipeGenerate}
                disabled={generatingRecipes}
              >
                {generatingRecipes ? <CircularProgress size={24} /> : 'Generate Recipes'}
              </Button>
              {recipes && (
                <Button
                  variant="outlined"
                  onClick={() => handleExport('recipes')}
                  disabled={generatingRecipes}
                >
                  Export PDF
                </Button>
              )}
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

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
          >
            Back
          </Button>
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={activeStep === steps.length - 1}
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