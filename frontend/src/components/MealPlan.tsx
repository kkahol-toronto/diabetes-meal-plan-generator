import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Divider,
  Paper,
  ListItemIcon,
  Chip,
} from '@mui/material';
import { Theme } from '@mui/material/styles';
import { MealPlanData } from '../types';

// Import icons for meal types
import BreakfastIcon from '@mui/icons-material/FreeBreakfast';
import LunchIcon from '@mui/icons-material/LunchDining';
import DinnerIcon from '@mui/icons-material/DinnerDining';
import SnackIcon from '@mui/icons-material/Icecream'; // Placeholder, find a better snack icon if needed
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter'; // For calories
import BoltIcon from '@mui/icons-material/Bolt'; // For Protein
import GrainIcon from '@mui/icons-material/Grain'; // For Carbs
import OilIcon from '@mui/icons-material/Opacity'; // For Fats

interface MealPlanProps {
  mealPlan: MealPlanData;
}

const MealPlan = ({ mealPlan }: MealPlanProps) => {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const mealTypes: Array<{ name: keyof Pick<MealPlanData, 'breakfast' | 'lunch' | 'dinner' | 'snacks'>; icon: JSX.Element; label: string }> = [
    { name: 'breakfast', icon: <BreakfastIcon />, label: 'Breakfast' },
    { name: 'lunch', icon: <LunchIcon />, label: 'Lunch' },
    { name: 'dinner', icon: <DinnerIcon />, label: 'Dinner' },
    { name: 'snacks', icon: <SnackIcon />, label: 'Snacks' },
  ];

  return (
    <Box sx={{ p: 1 }}>
      <Typography variant="h5" component="h2" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 3 }}>
        Your Weekly Meal Plan
      </Typography>

      <Card sx={{ mb: 4, borderRadius: '12px', boxShadow: 3 }}>
        <CardContent sx={{ backgroundColor: 'primary.main', color: 'primary.contrastText', borderTopLeftRadius: '12px', borderTopRightRadius: '12px'}}>
          <Typography variant="h6" component="div" align="center">
            Daily Nutritional Goals
          </Typography>
        </CardContent>
        <CardContent>
          <Grid container spacing={2} justifyContent="center" alignItems="center">
            <Grid item xs={6} sm={3} sx={{ textAlign: 'center' }}>
              <Chip icon={<FitnessCenterIcon />} label={`Calories: ${mealPlan.dailyCalories} kcal`} variant="outlined" color="primary" sx={{ width: '100%' }}/>
            </Grid>
            <Grid item xs={6} sm={3} sx={{ textAlign: 'center' }}>
              <Chip icon={<BoltIcon />} label={`Protein: ${mealPlan.macronutrients.protein}g`} variant="outlined" color="secondary" sx={{ width: '100%' }}/>
            </Grid>
            <Grid item xs={6} sm={3} sx={{ textAlign: 'center' }}>
              <Chip icon={<GrainIcon />} label={`Carbs: ${mealPlan.macronutrients.carbs}g`} variant="outlined" color="success" sx={{ width: '100%' }}/>
            </Grid>
            <Grid item xs={6} sm={3} sx={{ textAlign: 'center' }}>
              <Chip icon={<OilIcon />} label={`Fats: ${mealPlan.macronutrients.fats}g`} variant="outlined" color="warning" sx={{ width: '100%' }}/>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {days.map((day, dayIndex) => (
          <Grid item xs={12} md={6} lg={4} key={day}>
            <Card sx={{ borderRadius: '12px', boxShadow: 3, height: '100%' }}>
              <CardContent sx={{ backgroundColor: 'secondary.main', color: 'secondary.contrastText', borderTopLeftRadius: '12px', borderTopRightRadius: '12px'}}>
                <Typography variant="h6" component="div" align="center">
                  {day}
                </Typography>
              </CardContent>
              <CardContent>
                {mealTypes.map((mealTypeDetail) => (
                  <Paper 
                    elevation={1} 
                    key={mealTypeDetail.name} 
                    sx={{
                      mb: 2, 
                      p: 2, 
                      borderRadius: '8px', 
                      borderLeft: `5px solid ${(theme: Theme) => theme.palette.primary.light}`
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1}}>
                      <ListItemIcon sx={{ minWidth: 'auto', mr: 1, color: 'primary.main' }}>
                        {mealTypeDetail.icon}
                      </ListItemIcon>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'medium', textTransform: 'capitalize' }}>
                        {mealTypeDetail.label}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {mealPlan[mealTypeDetail.name][dayIndex] || 'Not specified'}
                    </Typography>
                  </Paper>
                ))}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default MealPlan; 