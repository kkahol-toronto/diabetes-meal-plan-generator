import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
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
  TextField,
  InputAdornment,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import { Recipe } from '../types';

const RecipesPage: React.FC = () => {
  const [recipes, setRecipes] = useState<{ recipes: Recipe[]; created_at: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('No authentication token found');
        }

        const response = await fetch('http://localhost:8000/user/recipes', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!response.ok) throw new Error('Failed to fetch recipes');
        const data = await response.json();
        setRecipes(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchRecipes();
  }, []);

  const handleExport = async (recipes: Recipe[]) => {
    try {
      const response = await fetch('http://localhost:8000/export/recipes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ recipes }),
      });

      if (!response.ok) throw new Error('Failed to export recipes');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recipes-${new Date().toISOString()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const filteredRecipes = recipes.map(recipeSet => ({
    ...recipeSet,
    recipes: recipeSet.recipes.filter(recipe =>
      recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      recipe.ingredients.some(ing => ing.toLowerCase().includes(searchTerm.toLowerCase()))
    )
  })).filter(recipeSet => recipeSet.recipes.length > 0);

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
            My Recipes
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search recipes by name or ingredients..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 3 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          {filteredRecipes.length === 0 ? (
            <Typography>
              {searchTerm ? 'No recipes match your search' : 'No recipes found'}
            </Typography>
          ) : (
            filteredRecipes.map((recipeSet, index) => (
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
                          <Box sx={{ width: '100%' }}>
                            <Typography variant="h6" gutterBottom>
                              {recipe.name}
                            </Typography>
                            <Typography variant="subtitle2" gutterBottom>
                              Nutritional Information:
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Calories: {recipe.nutritional_info.calories} | 
                              Protein: {recipe.nutritional_info.protein} | 
                              Carbs: {recipe.nutritional_info.carbs} | 
                              Fat: {recipe.nutritional_info.fat}
                            </Typography>
                            <Typography variant="subtitle2" gutterBottom>
                              Ingredients:
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              {recipe.ingredients.join(', ')}
                            </Typography>
                            <Typography variant="subtitle2" gutterBottom>
                              Instructions:
                            </Typography>
                            <List dense>
                              {recipe.instructions.map((instruction, idx) => (
                                <ListItem key={idx}>
                                  <Typography variant="body2" color="text.secondary">
                                    {idx + 1}. {instruction}
                                  </Typography>
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        </ListItem>
                        {recipeIndex < recipeSet.recipes.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                  <Button
                    variant="outlined"
                    onClick={() => handleExport(recipeSet.recipes)}
                    sx={{ mt: 2 }}
                  >
                    Export PDF
                  </Button>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default RecipesPage; 