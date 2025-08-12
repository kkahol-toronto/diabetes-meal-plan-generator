import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../config/environment';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  AlertTitle,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Restaurant as RestaurantIcon,
  Add as AddIcon,
  Analytics as AnalyticsIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';

interface DailyInsights {
  date: string;
  goals: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
  };
  today_totals: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
    fiber: number;
    sugar: number;
    sodium: number;
  };
  adherence: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
  };
  meals_logged_today: number;
  weekly_stats: {
    total_meals: number;
    diabetes_suitable_percentage: number;
    average_daily_calories: number;
  };
  recommendations: Array<{
    type: string;
    priority: string;
    message: string;
    action: string;
  }>;
  has_meal_plan: boolean;
  latest_meal_plan_date: string | null;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dailyInsights, setDailyInsights] = useState<DailyInsights | null>(null);
  const [showQuickLogDialog, setShowQuickLogDialog] = useState(false);
  const [quickLogFood, setQuickLogFood] = useState('');

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication token not found. Please log in.');
      }

              const insightsResponse = await fetch(`${config.API_URL}/coach/daily-insights`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!insightsResponse.ok) {
        if (insightsResponse.status === 401) throw new Error('Unauthorized. Please log in again.');
        const errorText = await insightsResponse.text();
        console.error("Backend Error:", errorText);
        throw new Error('Failed to fetch daily insights from the server.');
      }
        
      const insightsData = await insightsResponse.json();
      setDailyInsights(insightsData);

    } catch (err) {
      if (err instanceof Error && err.message.includes('Failed to fetch')) {
        setError("Could not connect to the backend. Please check your internet connection.");
      } else {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleQuickLogFood = async () => {
    if (!quickLogFood.trim()) return;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication token not found. Please log in.');
      }

              const response = await fetch(`${config.API_URL}/coach/quick-log`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ food_name: quickLogFood, portion: '1 serving' }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to log food.' }));
        throw new Error(errorData.detail);
      }
      
      setQuickLogFood('');
      setShowQuickLogDialog(false);
      await fetchAllData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to log food');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={fetchAllData}>
            RETRY
          </Button>
        }>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: 'primary.main', color: 'white' }}>
            <Typography variant="h4" gutterBottom>
              Welcome to Your Diabetes Meal Planner
            </Typography>
            <Typography variant="subtitle1">
              Track your meals, monitor your progress, and stay on top of your health goals.
            </Typography>
          </Paper>
        </Grid>
                
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                fullWidth
                sx={{ mb: 2 }}
                onClick={() => setShowQuickLogDialog(true)}
              >
                Log Food
              </Button>
              <Button
                variant="outlined"
                startIcon={<RestaurantIcon />}
                fullWidth
                sx={{ mb: 2 }}
                onClick={() => navigate('/meal-plan')}
              >
                View Meal Plan
              </Button>
              <Button
                variant="outlined"
                startIcon={<AnalyticsIcon />}
                fullWidth
                onClick={() => navigate('/analytics')}
              >
                View Analytics
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Today's Summary
              </Typography>
              {dailyInsights ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Calories
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(dailyInsights.today_totals.calories / (dailyInsights.goals.calories || 1)) * 100}
                        sx={{ height: 10, borderRadius: 5 }}
                      />
                      <Typography variant="body2">
                        {dailyInsights.today_totals.calories} / {dailyInsights.goals.calories || 'N/A'} kcal
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Meals Logged
                      </Typography>
                      <Typography variant="h4">
                        {dailyInsights.meals_logged_today}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Typography>No insights available for today.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {dailyInsights?.recommendations && dailyInsights.recommendations.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recommendations
                </Typography>
                <List>
                  {dailyInsights.recommendations.map((rec, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <LightbulbIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={rec.message}
                        secondary={rec.action}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      <Dialog open={showQuickLogDialog} onClose={() => setShowQuickLogDialog(false)}>
        <DialogTitle>Quick Log Food</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Food Item"
            placeholder="e.g., Grilled chicken salad with olive oil dressing"
            type="text"
            fullWidth
            value={quickLogFood}
            onChange={(e) => setQuickLogFood(e.target.value)}
          />
          <Alert severity="success" variant="outlined" sx={{ mt: 2, alignItems: 'flex-start' }}>
            <AlertTitle>No meal plan required</AlertTitle>
            <Typography variant="body2" color="text.primary">
              Our AI will analyze nutrition and diabetes suitability automatically. Food logging works independently and updates your daily nutrition score. Meal type will be auto-detected based on the current time.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowQuickLogDialog(false)}>Cancel</Button>
          <Button onClick={handleQuickLogFood} variant="contained">
            Log
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default HomePage;