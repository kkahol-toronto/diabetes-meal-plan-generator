import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Divider,
} from '@mui/material';
import { MealPlanData } from '../types';

interface MealPlanProps {
  mealPlan: MealPlanData;
}

const MealPlan = ({ mealPlan }: MealPlanProps) => {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const mealTypes = ['breakfast', 'lunch', 'dinner', 'snacks'] as const;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Weekly Meal Plan
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Daily Nutritional Goals
          </Typography>
          <Typography>
            Daily Calories: {mealPlan.dailyCalories} kcal
          </Typography>
          <Typography>
            Protein: {mealPlan.macronutrients.protein}g
          </Typography>
          <Typography>
            Carbs: {mealPlan.macronutrients.carbs}g
          </Typography>
          <Typography>
            Fats: {mealPlan.macronutrients.fats}g
          </Typography>
        </CardContent>
      </Card>

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
                      {mealPlan[mealType][dayIndex] || 'Not specified'}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default MealPlan; 