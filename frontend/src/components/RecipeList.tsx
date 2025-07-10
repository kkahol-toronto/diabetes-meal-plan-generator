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
  Divider,
  Chip,
  Grid,
  ListItemIcon
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Recipe } from '../types';

// Import icons for sections and nutrition
import RestaurantIcon from '@mui/icons-material/Restaurant';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import ListAltIcon from '@mui/icons-material/ListAlt';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import SpaIcon from '@mui/icons-material/Spa';
import HealingIcon from '@mui/icons-material/Healing';

interface RecipeListProps {
  recipes: Recipe[];
}

const RecipeList: React.FC<RecipeListProps> = ({ recipes }) => {
  if (!recipes || recipes.length === 0) {
    return (
      <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6">No recipes generated yet.</Typography>
        <Typography variant="body1">Please generate recipes to see them here.</Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={0} sx={{ p: {xs: 1, sm: 2}, backgroundColor: 'transparent' }}>
      <Typography variant="h5" component="h2" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 3 }}>
        Your Generated Recipes
      </Typography>
      {recipes.map((recipe, index) => (
        <Accordion 
          key={index} 
          sx={{ 
            mb: 2, 
            borderRadius: '12px', 
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            '&:before': { display: 'none' },
          }}
          defaultExpanded={index === 0}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />} 
            aria-controls={`recipe-content-${index}`} 
            id={`recipe-header-${index}`}
            sx={{ 
              borderTopLeftRadius: '12px', 
              borderTopRightRadius: '12px', 
              borderBottomLeftRadius: index === recipes.length -1 || !recipe ? '12px' : 0,
              borderBottomRightRadius: index === recipes.length -1 || !recipe ? '12px' : 0,
              backgroundColor: 'grey.100',
              '&:hover': {
                backgroundColor: 'grey.200'
              }
            }}
          >
            <ListItemIcon sx={{minWidth: 'auto', mr: 1.5, color: 'primary.main'}}><RestaurantIcon /></ListItemIcon>
            <Typography variant="h6" component="div" sx={{ fontWeight: 500 }}>
              {recipe.name}
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ p: {xs: 2, sm: 3}, backgroundColor: 'white'}}>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', fontWeight: 'medium' }}>
                <ListItemIcon sx={{minWidth: 'auto', mr: 1, color: 'secondary.main'}}><LocalFireDepartmentIcon /></ListItemIcon>
                Nutritional Highlights
              </Typography>
              <Grid container spacing={1} sx={{ mt: 1 }}>
                <Grid item xs={6} sm={3}>
                  <Chip icon={<LocalFireDepartmentIcon fontSize="small" />} label={`Calories: ${recipe.nutritional_info?.calories || 'N/A'}`} variant="outlined" color="warning" size="small" sx={{width: '100%'}} />
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Chip icon={<FitnessCenterIcon fontSize="small"/>} label={`Protein: ${recipe.nutritional_info?.protein || 'N/A'}`} variant="outlined" color="info" size="small" sx={{width: '100%'}} />
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Chip icon={<SpaIcon fontSize="small"/>} label={`Carbs: ${recipe.nutritional_info?.carbs || 'N/A'}`} variant="outlined" color="success" size="small" sx={{width: '100%'}} />
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Chip icon={<HealingIcon fontSize="small"/>} label={`Fat: ${recipe.nutritional_info?.fat || 'N/A'}`} variant="outlined" color="default" size="small" sx={{width: '100%'}} />
                </Grid>
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
                  <ListItem key={idx} sx={{ py: 0.5}}>
                    <ListItemText primaryTypographyProps={{ variant: 'body2' }} primary={`• ${ingredient}`} />
                  </ListItem>
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
                {recipe.instructions.map((instruction, idx) => {
                  // Remove leading numbering (e.g., '1. ', '2) ', etc.)
                  const cleaned = instruction.replace(/^\s*\d+\s*[\.|\)]?\s*/, '');
                  return (
                    <ListItem key={idx} sx={{ py: 0.5, alignItems: 'flex-start' }}>
                      <ListItemText 
                        primaryTypographyProps={{ variant: 'body2' }} 
                        primary={`${idx + 1}. ${cleaned}`}
                      />
                </ListItem>
                  );
                })}
              </List>
            </Box>

          </AccordionDetails>
        </Accordion>
      ))}
    </Paper>
  );
};

export default RecipeList; 