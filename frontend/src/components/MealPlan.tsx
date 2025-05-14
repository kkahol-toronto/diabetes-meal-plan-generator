import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Box,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { MealPlanData } from '../types';

type MealPlanProps = {
  mealPlan: MealPlanData;
};

const MealPlan = ({ mealPlan }: MealPlanProps) => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Your Personalized Meal Plan
        </Typography>

        <Grid container spacing={4}>
          {/* Daily Summary */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Daily Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="subtitle1">Total Calories</Typography>
                    <Typography variant="h6">{mealPlan.dailyCalories} kcal</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="subtitle1">Protein</Typography>
                    <Typography variant="h6">{mealPlan.macronutrients.protein}g</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="subtitle1">Carbs</Typography>
                    <Typography variant="h6">{mealPlan.macronutrients.carbs}g</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="subtitle1">Fats</Typography>
                    <Typography variant="h6">{mealPlan.macronutrients.fats}g</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Meals */}
          {Object.entries(mealPlan.meals).map(([mealTime, meals]) => (
            <Grid item xs={12} key={mealTime}>
              <Typography variant="h5" gutterBottom>
                {mealTime}
              </Typography>
              <Grid container spacing={2}>
                {meals.map((meal, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6">{meal.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {meal.calories} kcal
                        </Typography>
                        <Typography variant="body2">
                          P: {meal.macronutrients.protein}g | C: {meal.macronutrients.carbs}g | F: {meal.macronutrients.fats}g
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Grid>
          ))}

          {/* Action Buttons */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Button
                variant="outlined"
                color="primary"
                onClick={() => navigate('/')}
              >
                Back to Form
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={() => navigate('/recipes')}
              >
                View Recipes
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default MealPlan; 