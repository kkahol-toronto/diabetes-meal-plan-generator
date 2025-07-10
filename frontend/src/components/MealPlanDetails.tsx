import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Paper, Typography, Box, CircularProgress, Alert, Card, CardContent, Grid, Chip, Stack, Button, Accordion, AccordionSummary, AccordionDetails, List, ListItem, ListItemText } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { MealPlanData, Recipe, ShoppingItem } from '../types';
import { handleAuthError, getAuthHeaders } from '../utils/auth';
import config from '../config/environment';

const MealPlanDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [mealPlan, setMealPlan] = useState<MealPlanData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recipes, setRecipes] = useState<Recipe[] | null>(null);
  const [shoppingList, setShoppingList] = useState<ShoppingItem[] | null>(null);

  useEffect(() => {
    const fetchMealPlan = async () => {
      if (!id) {
        setError('Meal plan ID is missing.');
        setLoading(false);
        return;
      }

      try {
        const headers = getAuthHeaders();
        if (!headers) {
          navigate('/login');
          return;
        }

        const response = await fetch(`${config.API_URL}/meal_plans/${id}`, {
          headers,
        });

        if (!response.ok) {
          if (handleAuthError(response, navigate)) {
            return;
          }
          throw new Error('Failed to fetch meal plan details.');
        }

        const data = await response.json();
        setMealPlan(data.meal_plan);
        setRecipes(data.meal_plan.recipes || null);
        setShoppingList(data.meal_plan.shopping_list || null);
      } catch (err) {
        if (!handleAuthError(err, navigate)) {
          setError(err instanceof Error ? err.message : 'An error occurred');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchMealPlan();
  }, [id, navigate]);

  const formatDateTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays} days ago`;
      
      // Format as "Month Day, Year at HH:MM AM/PM"
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (e) {
      return 'Invalid Date';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
       <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
       </Container>
    );
  }

  if (!mealPlan) {
      return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
         <Alert severity="info">Meal plan not found.</Alert>
        </Container>
     );
  }

  // Determine the number of days based on the meal plan data
  const getNumberOfDays = () => {
    if (!mealPlan) return 7;
    // Check the length of any meal type array to determine the number of days
    const breakfastLength = mealPlan.breakfast?.length || 0;
    return Math.max(1, Math.min(7, breakfastLength)); // Ensure it's between 1 and 7
  };
  
  const numberOfDays = getNumberOfDays();
  const days = Array.from({ length: numberOfDays }, (_, i) => `Day ${i + 1}`);
  const mealTypes = ['breakfast', 'lunch', 'dinner', 'snacks'] as const;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ mb: 4 }}>
          Meal Plan Details
        </Typography>

        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Created on: {formatDateTime(mealPlan.created_at ?? '')}
          </Typography>
        </Box>

        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Nutritional Summary
          </Typography>
          <Chip
             label={`${mealPlan.dailyCalories ?? 'N/A'} kcal`}
             color="primary"
             sx={{ mr: 1, mb: 1 }}
          />
          <Chip
             label={`Protein: ${mealPlan.macronutrients?.protein ?? 'N/A'}g`}
             variant="outlined"
             size="small"
             sx={{ mr: 1, mb: 1 }}
          />
           <Chip
             label={`Carbs: ${mealPlan.macronutrients?.carbs ?? 'N/A'}g`}
             variant="outlined"
             size="small"
             sx={{ mr: 1, mb: 1 }}
          />
           <Chip
             label={`Fats: ${mealPlan.macronutrients?.fats ?? 'N/A'}g`}
             variant="outlined"
             size="small"
             sx={{ mr: 1, mb: 1 }}
          />
        </Box>

        <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
          Weekly Breakdown
        </Typography>

        {days.map((day, dayIndex) => (
          <Card key={day} sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {day}
              </Typography>
              <Grid container spacing={2}>
                {mealTypes.map((mealType) => (
                  <Grid item xs={12} sm={6} md={3} key={mealType}>
                    <Box>
                      <Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>
                        {mealType}
                      </Typography>
                      <Typography>
                        {(mealPlan as any)[mealType]?.[dayIndex] || 'Not specified'}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        ))}

        {recipes && (
          <>
            <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
              Recipes
            </Typography>
            <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
              {recipes.map((recipe, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">{recipe.name}</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Ingredients:
                      </Typography>
                      <List dense>
                        {recipe.ingredients.map((ingredient, idx) => (
                          <ListItem key={idx}>
                            <ListItemText primary={ingredient} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Instructions:
                      </Typography>
                      <List>
                        {recipe.instructions.map((instruction, idx) => (
                          <ListItem key={idx}>
                            <ListItemText primary={`${idx + 1}. ${instruction}`} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                    <Box>
                      <Typography variant="subtitle1" gutterBottom>
                        Nutritional Information:
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText primary={`Calories: ${recipe.nutritional_info.calories}`} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary={`Protein: ${recipe.nutritional_info.protein}`} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary={`Carbs: ${recipe.nutritional_info.carbs}`} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary={`Fat: ${recipe.nutritional_info.fat}`} />
                        </ListItem>
                      </List>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Paper>
          </>
        )}

        {shoppingList && (
          <>
            <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
              Shopping List
            </Typography>
            <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
              {Object.entries(
                shoppingList.reduce((acc, item) => {
                  if (!acc[item.category]) {
                    acc[item.category] = [];
                  }
                  acc[item.category].push(item);
                  return acc;
                }, {} as Record<string, ShoppingItem[]>)
              ).map(([category, items]) => (
                <Box key={category} sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    {category}
                  </Typography>
                  <List dense>
                    {items.map((item, index) => (
                      <ListItem key={index}>
                        <ListItemText
                          primary={item.name}
                          secondary={`Amount: ${item.amount}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              ))}
            </Paper>
          </>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/meal_plans')}
          >
            Back to History
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => {
              // Add export functionality here
              window.print();
            }}
          >
            Export PDF
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default MealPlanDetails; 