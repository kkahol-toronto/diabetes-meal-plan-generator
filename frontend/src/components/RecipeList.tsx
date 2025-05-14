import React from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Recipe } from '../types';

interface RecipeListProps {
  recipes: Recipe[];
}

const RecipeList: React.FC<RecipeListProps> = ({ recipes }) => {
  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Recipe List
      </Typography>
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
  );
};

export default RecipeList; 