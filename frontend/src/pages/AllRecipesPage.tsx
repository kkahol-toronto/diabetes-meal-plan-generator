import React, { useState, useEffect } from 'react';
import config from '../config/environment';
import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
  Grid,
  ListItemIcon,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Recipe } from '../types'; // Assuming Recipe type is in ../types
import { useNavigate } from 'react-router-dom';

// Icons (can reuse from RecipeList or import new ones)
import RestaurantIcon from '@mui/icons-material/Restaurant';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import ListAltIcon from '@mui/icons-material/ListAlt';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import SpaIcon from '@mui/icons-material/Spa'; // Consider GrainIcon
import HealingIcon from '@mui/icons-material/Healing'; // Consider Opacity/OilIcon

interface StoredRecipeSet {
  id: string; // Or a timestamp if that's how they are stored/differentiated
  createdAt: string; // Or Date
  recipes: Recipe[];
  // Add any other metadata for a recipe set, e.g., mealPlanId it was generated from
}

const AllRecipesPage: React.FC = () => {
  const [recipeSets, setRecipeSets] = useState<StoredRecipeSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAllRecipes = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }
        // Assuming backend endpoint /user/recipes returns an array of StoredRecipeSet
        // or an array of arrays of Recipe, which we'd then structure here.
        // For now, let's assume it returns StoredRecipeSet[] based on the interface above.
        const response = await fetch(`${config.API_URL}/user/recipes`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch recipes' }));
          throw new Error(errorData.detail || 'Failed to fetch recipes');
        }
        const data = await response.json();
        // The backend currently returns the latest set of recipes as { recipes: Recipe[] }
        // or an empty object/array if no recipes.
        // The target is for the backend to return StoredRecipeSet[]

        console.log('Fetched data from /user/recipes:', JSON.stringify(data, null, 2));

        if (Array.isArray(data) && data.length > 0 && data[0].recipes) { 
            // Ideal case: Backend returns StoredRecipeSet[]
            setRecipeSets(data);
        } else if (data && data.recipes && Array.isArray(data.recipes)) {
            // Temporary adaptation: Backend returns a single { recipes: Recipe[] }
            console.log('Adapting single recipe set to StoredRecipeSet array.');
            setRecipeSets([{
                id: new Date().toISOString() + '-current', // Placeholder ID
                createdAt: new Date().toLocaleString(), // Placeholder date
                recipes: data.recipes
            }]);
        } else if (Array.isArray(data) && data.length === 0) {
            // Backend returns an empty array, meaning no recipe sets found
            console.log('Backend returned an empty array for recipe sets.');
            setRecipeSets([]);
        } else if (typeof data === 'object' && data !== null && Object.keys(data).length === 0) {
            // Backend returns an empty object {}
             console.log('Backend returned an empty object for recipe sets.');
            setRecipeSets([]);
        } else if (data === null) {
            // Backend returns null
            console.log('Backend returned null for recipe sets.');
            setRecipeSets([]);
        }
        else {
            // Unexpected data structure
            console.warn('Unexpected data structure from /user/recipes:', data);
            setError('Received unexpected data format for recipes.');
            setRecipeSets([]); 
        }

      } catch (err) {
        console.error("Error in fetchAllRecipes:", err);
        setError(err instanceof Error ? err.message : 'An unexpected error occurred while fetching recipes.');
      } finally {
        setLoading(false);
      }
    };

    fetchAllRecipes();
  }, [navigate]);

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography>Loading your saved recipes...</Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (recipeSets.length === 0) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: 'center' }}>
        <Paper sx={{p:3, borderRadius: '12px'}}>
            <Typography variant="h6">No Saved Recipes Found</Typography>
            <Typography color="text.secondary">It looks like you haven't saved any recipes yet. Generate some from a meal plan or via the chat!</Typography>
        </Paper>
      </Container>
    );
  }

  // Reusing styling from RecipeList.tsx for individual recipe display
  const renderSingleRecipe = (recipe: Recipe, index: number, parentId: string) => (
    <Accordion 
        key={`${parentId}-${index}`} 
        sx={{ mb: 2, borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', '&:before': { display: 'none' }}}
    >
        <AccordionSummary 
            expandIcon={<ExpandMoreIcon />} 
            aria-controls={`recipe-content-${parentId}-${index}`} 
            id={`recipe-header-${parentId}-${index}`}
            sx={{ borderRadius: '12px', backgroundColor: 'grey.100', '&:hover': {backgroundColor: 'grey.200'} }}
        >
            <ListItemIcon sx={{minWidth: 'auto', mr: 1.5, color: 'primary.main'}}><RestaurantIcon /></ListItemIcon>
            <Typography variant="h6" component="div" sx={{ fontWeight: 500 }}>{recipe.name}</Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ p: {xs: 2, sm: 3}, backgroundColor: 'white'}}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', fontWeight: 'medium' }}>
                <ListItemIcon sx={{minWidth: 'auto', mr: 1, color: 'secondary.main'}}><LocalFireDepartmentIcon /></ListItemIcon>
                Nutritional Highlights
              </Typography>
              <Grid container spacing={1} sx={{ mt: 1 }}>
                <Grid item xs={6} sm={3}><Chip icon={<LocalFireDepartmentIcon fontSize="small" />} label={`Calories: ${recipe.nutritional_info.calories}`} variant="outlined" color="warning" size="small" sx={{width: '100%'}} /></Grid>
                <Grid item xs={6} sm={3}><Chip icon={<FitnessCenterIcon fontSize="small"/>} label={`Protein: ${recipe.nutritional_info.protein}`} variant="outlined" color="info" size="small" sx={{width: '100%'}} /></Grid>
                <Grid item xs={6} sm={3}><Chip icon={<SpaIcon fontSize="small"/>} label={`Carbs: ${recipe.nutritional_info.carbs}`} variant="outlined" color="success" size="small" sx={{width: '100%'}} /></Grid>
                <Grid item xs={6} sm={3}><Chip icon={<HealingIcon fontSize="small"/>} label={`Fat: ${recipe.nutritional_info.fat}`} variant="outlined" color="default" size="small" sx={{width: '100%'}} /></Grid>
              </Grid>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', fontWeight: 'medium' }}>
                <ListItemIcon sx={{minWidth: 'auto', mr: 1, color: 'secondary.main'}}><MenuBookIcon /></ListItemIcon>
                Ingredients
              </Typography>
              <List dense disablePadding>
                {recipe.ingredients.map((ingredient, idx) => (
                  <ListItem key={idx} sx={{ py: 0.5}}><ListItemText primaryTypographyProps={{ variant: 'body2' }} primary={`• ${ingredient}`} /></ListItem>
                ))}
              </List>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Box>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', fontWeight: 'medium' }}>
                <ListItemIcon sx={{minWidth: 'auto', mr: 1, color: 'secondary.main'}}><ListAltIcon /></ListItemIcon>
                Instructions
              </Typography>
              <List dense disablePadding>
                {recipe.instructions.map((instruction, idx) => (
                  <ListItem key={idx} sx={{ py: 0.5, alignItems: 'flex-start' }}><ListItemText primaryTypographyProps={{ variant: 'body2' }} primary={`${idx + 1}. ${instruction}`} /></ListItem>
                ))}
              </List>
            </Box>
        </AccordionDetails>
    </Accordion>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 4 }}>
        My Saved Recipes
      </Typography>
      {recipeSets.map((set) => (
        <Paper key={set.id} elevation={2} sx={{ p: {xs:2, sm:3}, mb: 3, borderRadius: '16px' }}>
          <Typography variant="h6" component="h3" gutterBottom sx={{borderBottom: '1px solid lightgrey', pb:1, mb:2}}>
            Recipes from: {set.createdAt} (ID: {set.id.substring(0,10)})
          </Typography>
          {set.recipes.map((recipe, index) => renderSingleRecipe(recipe, index, set.id))}
        </Paper>
      ))}
    </Container>
  );
};

export default AllRecipesPage; 