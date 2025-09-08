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
  ListItemIcon,
  keyframes,
  Fade,
  Slide,
  Card,
  CardContent,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// Import icons for sections and nutrition
import RestaurantIcon from '@mui/icons-material/Restaurant';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import ListAltIcon from '@mui/icons-material/ListAlt';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import SpaIcon from '@mui/icons-material/Spa';
import HealingIcon from '@mui/icons-material/Healing';
import { Recipe } from '../types';

// Enhanced mobile animations
const slideInUp = keyframes`
  0% { 
    opacity: 0;
    transform: translateY(30px);
  }
  100% { 
    opacity: 1;
    transform: translateY(0);
  }
`;

const fadeInScale = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.95);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

interface RecipeListProps {
  recipes: Recipe[];
}

const RecipeList: React.FC<RecipeListProps> = ({ recipes }) => {
  if (!recipes || recipes.length === 0) {
    return (
      <Fade in={true} timeout={800}>
        <Card
          sx={{
            p: 4,
            textAlign: 'center',
            borderRadius: '20px',
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
          }}
        >
          <Typography variant="h6" sx={{ color: '#667eea', fontWeight: 600, mb: 1 }}>
            No recipes generated yet.
          </Typography>
          <Typography variant="body1" sx={{ color: 'rgba(102, 126, 234, 0.7)' }}>
            Please generate recipes to see them here.
          </Typography>
        </Card>
      </Fade>
    );
  }

  return (
    <Box sx={{ p: { xs: 1, sm: 2 } }}>
      <Fade in={true} timeout={1000}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography 
            variant="h5" 
            component="h2" 
            sx={{ 
              fontWeight: 700, 
              color: 'white',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              mb: 1,
              fontSize: { xs: '1.25rem', sm: '1.5rem' }
            }}
          >
            🍳 Your Generated Recipes
          </Typography>
          <Typography 
            variant="body2" 
            sx={{ 
              color: 'rgba(255, 255, 255, 0.8)',
              fontWeight: 500
            }}
          >
            Delicious meals crafted just for you
          </Typography>
        </Box>
      </Fade>
      {recipes.map((recipe, index) => (
        <Slide direction="up" in={true} timeout={800 + index * 200} key={index}>
          <Accordion 
            sx={{ 
              mb: 3,
              borderRadius: '20px',
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
              overflow: 'hidden',
              transition: 'all 0.3s ease',
              '&:before': { display: 'none' },
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 12px 40px rgba(31, 38, 135, 0.2)',
              },
              '&.Mui-expanded': {
                boxShadow: '0 12px 40px rgba(102, 126, 234, 0.25)',
              }
            }}
            defaultExpanded={index === 0}
          >
            <AccordionSummary 
              expandIcon={<ExpandMoreIcon sx={{ color: 'white' }} />} 
              aria-controls={`recipe-content-${index}`} 
              id={`recipe-header-${index}`}
              sx={{ 
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.8) 0%, rgba(118, 75, 162, 0.8) 100%)',
                color: 'white',
                minHeight: '72px',
                '&:hover': {
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%)',
                },
                '& .MuiAccordionSummary-expandIconWrapper': {
                  color: 'white',
                  transition: 'transform 0.3s ease',
                },
                '& .MuiAccordionSummary-expandIconWrapper.Mui-expanded': {
                  transform: 'rotate(180deg)',
                }
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ 
                  background: 'rgba(255, 255, 255, 0.2)', 
                  borderRadius: '12px', 
                  p: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <RestaurantIcon sx={{ color: 'white' }} />
                </Box>
                <Typography variant="h6" component="div" sx={{ 
                  fontWeight: 600,
                  color: 'white',
                  textShadow: '0 1px 3px rgba(0,0,0,0.3)',
                  fontSize: { xs: '1rem', sm: '1.25rem' }
                }}>
                  {recipe.name}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails sx={{ p: { xs: 2, sm: 3 }, backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
            
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
        </Slide>
      ))}
    </Box>
  );
};

export default RecipeList; 