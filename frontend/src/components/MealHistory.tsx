import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { SavedMealPlan, Recipe, ShoppingItem } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`history-tabpanel-${index}`}
      aria-labelledby={`history-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const MealHistory: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [mealPlans, setMealPlans] = useState<SavedMealPlan[]>([]);
  const [recipes, setRecipes] = useState<{ recipes: Recipe[]; created_at: string }[]>([]);
  const [shoppingLists, setShoppingLists] = useState<{ items: ShoppingItem[]; created_at: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('No authentication token found');
        }

        const headers = {
          'Authorization': `Bearer ${token}`,
        };

        // Fetch meal plans
        const mealPlansResponse = await fetch('http://localhost:8000/user/meal-plans', { headers });
        if (!mealPlansResponse.ok) throw new Error('Failed to fetch meal plans');
        const mealPlansData = await mealPlansResponse.json();
        setMealPlans(mealPlansData);

        // Fetch recipes
        const recipesResponse = await fetch('http://localhost:8000/user/recipes', { headers });
        if (!recipesResponse.ok) throw new Error('Failed to fetch recipes');
        const recipesData = await recipesResponse.json();
        setRecipes(recipesData);

        // Fetch shopping lists
        const shoppingListsResponse = await fetch('http://localhost:8000/user/shopping-list', { headers });
        if (!shoppingListsResponse.ok) throw new Error('Failed to fetch shopping lists');
        const shoppingListsData = await shoppingListsResponse.json();
        setShoppingLists(Array.isArray(shoppingListsData) ? shoppingListsData : [shoppingListsData]);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleExport = async (type: 'meal-plan' | 'recipes' | 'shopping-list', data: any) => {
    try {
      const response = await fetch(`http://localhost:8000/export/${type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          [type === 'meal-plan' ? 'meal_plan' : type]: data,
        }),
      });

      if (!response.ok) throw new Error(`Failed to export ${type}`);

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
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom color="primary">
            Meal History
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="history tabs">
              <Tab label="Meal Plans" />
              <Tab label="Recipes" />
              <Tab label="Shopping Lists" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            {mealPlans.length === 0 ? (
              <Typography>No meal plans found</Typography>
            ) : (
              mealPlans.map((plan, index) => (
                <Accordion key={plan.id || index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>
                      Meal Plan - {new Date(plan.created_at).toLocaleDateString()}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="h6" gutterBottom>Daily Calories: {plan.dailyCalories}</Typography>
                      <Typography variant="subtitle1" gutterBottom>Macronutrients:</Typography>
                      <List>
                        <ListItem>
                          <ListItemText primary={`Protein: ${plan.macronutrients.protein}g`} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary={`Carbs: ${plan.macronutrients.carbs}g`} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary={`Fats: ${plan.macronutrients.fats}g`} />
                        </ListItem>
                      </List>
                      <Button
                        variant="outlined"
                        onClick={() => handleExport('meal-plan', plan)}
                        sx={{ mt: 2 }}
                      >
                        Export PDF
                      </Button>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {recipes.length === 0 ? (
              <Typography>No recipes found</Typography>
            ) : (
              recipes.map((recipeSet, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>
                      Recipes - {new Date(recipeSet.created_at).toLocaleDateString()}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {recipeSet.recipes.map((recipe, recipeIndex) => (
                        <React.Fragment key={recipeIndex}>
                          <ListItem>
                            <ListItemText
                              primary={recipe.name}
                              secondary={`Calories: ${recipe.nutritional_info.calories}, Protein: ${recipe.nutritional_info.protein}, Carbs: ${recipe.nutritional_info.carbs}, Fat: ${recipe.nutritional_info.fat}`}
                            />
                          </ListItem>
                          {recipeIndex < recipeSet.recipes.length - 1 && <Divider />}
                        </React.Fragment>
                      ))}
                    </List>
                    <Button
                      variant="outlined"
                      onClick={() => handleExport('recipes', recipeSet.recipes)}
                      sx={{ mt: 2 }}
                    >
                      Export PDF
                    </Button>
                  </AccordionDetails>
                </Accordion>
              ))
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            {shoppingLists.length === 0 ? (
              <Typography>No shopping lists found</Typography>
            ) : (
              shoppingLists.map((list, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>
                      Shopping List - {new Date(list.created_at).toLocaleDateString()}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {list.items.map((item, itemIndex) => (
                        <React.Fragment key={itemIndex}>
                          <ListItem>
                            <ListItemText
                              primary={item.name}
                              secondary={`${item.amount} - ${item.category}`}
                            />
                          </ListItem>
                          {itemIndex < list.items.length - 1 && <Divider />}
                        </React.Fragment>
                      ))}
                    </List>
                    <Button
                      variant="outlined"
                      onClick={() => handleExport('shopping-list', list.items)}
                      sx={{ mt: 2 }}
                    >
                      Export PDF
                    </Button>
                  </AccordionDetails>
                </Accordion>
              ))
            )}
          </TabPanel>
        </Box>
      </Paper>
    </Container>
  );
};

export default MealHistory; 