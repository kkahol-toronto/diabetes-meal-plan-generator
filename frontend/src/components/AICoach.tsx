import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  Alert,
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
  Chip,
  Divider,
  Avatar,
  IconButton,
  Tooltip,
  Fab,
  Slide,
  Fade,
  useTheme,
  alpha,
  CardActions,
  ButtonGroup,
  Tab,
  Tabs,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Psychology as CoachIcon,
  AutoAwesome as AIIcon,
  Timeline as TimelineIcon,
  Assignment as PlanIcon,
  Lightbulb as LightbulbIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  LocalFireDepartment as CaloriesIcon,
  FitnessCenter as ProteinIcon,
  Grain as CarbsIcon,
  Favorite as HeartIcon,
  Speed as SpeedIcon,
  EmojiEvents as TrophyIcon,
  Restaurant as RestaurantIcon,
  Chat as ChatIcon,
  Analytics as AnalyticsIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Star as StarIcon,
  Schedule as ScheduleIcon,
  MenuBook as RecipeIcon,
  ShoppingCart as ShoppingIcon,
  Notifications as NotificationIcon,
  Settings as SettingsIcon,
  RestaurantMenu as MealIcon,
  AccessTime as TimeIcon,
  LocalDining as DiningIcon,
} from '@mui/icons-material';
import { useApp } from '../contexts/AppContext';
import { Line, Doughnut, Bar, Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement,
  RadialLinearScale,
} from 'chart.js';
import { api } from '../utils/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement,
  RadialLinearScale
);

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function CustomTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`coach-tabpanel-${index}`}
      aria-labelledby={`coach-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Define interfaces for API responses
interface DailyInsights {
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
}

interface MealHistoryItem {
  food_name: string;
  timestamp: string;
  nutritional_info: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
  };
  meal_type: string;
}

interface MealSuggestionResponse {
  success: boolean;
  suggestion: string;
  error?: string;
}

interface MealTimeContext {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  time: number;
  isLate: boolean;
}

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  success: boolean;
}

const AICoach: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { showNotification, setLoading } = useApp();
  const [loading, setLocalLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [coachData, setCoachData] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [progressData, setProgressData] = useState<any>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [tabValue, setTabValue] = useState(0);
  const [adaptivePlanLoading, setAdaptivePlanLoading] = useState(false);
  const [showAIDialog, setShowAIDialog] = useState(false);
  const [aiQuery, setAIQuery] = useState('');
  const [aiResponse, setAIResponse] = useState('');
  const [aiLoading, setAILoading] = useState(false);
  const [insights, setInsights] = useState<any[]>([]);
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [dailyInsights, setDailyInsights] = useState<DailyInsights | null>(null);
  const [mealHistory, setMealHistory] = useState<MealHistoryItem[]>([]);

  const token = localStorage.getItem('token');
  const isLoggedIn = !!token;

  const fetchDailyInsights = async () => {
    try {
      const responseData = await api.get<ApiResponse<DailyInsights>>('/coach/daily-insights');
      if (responseData.data) {
        setDailyInsights(responseData.data);
      }
    } catch (err) {
      console.error('Error fetching daily insights:', err);
      setError('Failed to fetch daily insights');
    }
  };

  const fetchMealHistory = async () => {
    try {
      const responseData = await api.get<ApiResponse<MealHistoryItem[]>>('/consumption/history?limit=20');
      if (responseData.data) {
        setMealHistory(responseData.data);
      }
    } catch (err) {
      console.error('Error fetching meal history:', err);
    }
  };

  const fetchAllCoachData = useCallback(async () => {
    if (!isLoggedIn) {
      setLocalLoading(false);
      return;
    }

    try {
      setLocalLoading(true);
      setError(null);

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Fetch comprehensive coaching data
      const [
        dailyInsightsResponse,
        analyticsResponse,
        progressResponse,
        notificationsResponse,
        consumptionInsightsResponse
      ] = await Promise.all([
        fetch('/coach/daily-insights', { headers }),
        fetch('/consumption/analytics?days=30', { headers }),
        fetch('/consumption/progress', { headers }),
        fetch('/coach/notifications', { headers }),
        fetch('/coach/consumption-insights?days=30', { headers })
      ]);

      if (dailyInsightsResponse.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      const [dailyData, analytics, progress, notifs, consumptionInsights] = await Promise.all([
        dailyInsightsResponse.ok ? dailyInsightsResponse.json() : null,
        analyticsResponse.ok ? analyticsResponse.json() : null,
        progressResponse.ok ? progressResponse.json() : null,
        notificationsResponse.ok ? notificationsResponse.json() : [],
        consumptionInsightsResponse.ok ? consumptionInsightsResponse.json() : null
      ]);

      setCoachData(dailyData);
      setAnalyticsData(analytics);
      setProgressData(progress);
      setNotifications(notifs);

      // Derive insights from dailyData if available, otherwise transform consumptionInsights object to array
      if (Array.isArray(dailyData?.insights)) {
        setInsights(dailyData.insights);
      } else if (consumptionInsights?.insights && typeof consumptionInsights.insights === 'object') {
        const transformed = Object.entries(consumptionInsights.insights).map(([key, value]) => ({
          category: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
          message: typeof value === 'object' ? JSON.stringify(value) : String(value),
        }));
        setInsights(transformed);
      } else {
        setInsights([]);
      }

    } catch (err) {
      console.error('Error fetching coach data:', err);
      setError('Unable to load AI coach data. Please try again.');
    } finally {
      setLocalLoading(false);
    }
  }, [fetchDailyInsights, fetchMealHistory]);

  useEffect(() => {
    fetchAllCoachData();
    const interval = setInterval(fetchAllCoachData, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchAllCoachData]);

  const handleCreateAdaptivePlan = async () => {
    try {
      setAdaptivePlanLoading(true);
      setLoading(true, 'Creating your personalized meal plan...');
      
      const response = await fetch('/coach/adaptive-meal-plan', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        showNotification('🎉 Your adaptive meal plan has been created!', 'success');
        navigate('/meal_plans');
      } else {
        throw new Error('Failed to create adaptive meal plan');
      }
    } catch (err) {
      showNotification('Failed to create meal plan. Please try again.', 'error');
    } finally {
      setAdaptivePlanLoading(false);
      setLoading(false);
    }
  };

  const handleAIQuery = async () => {
    const inputElement = document.querySelector<HTMLInputElement>('input[placeholder="Ask your AI coach"]');
    if (!inputElement || !inputElement.value.trim()) return;

    const userQuery = inputElement.value.trim();
    setLocalLoading(true);
    setError(null);

    try {
      // Get meal context from query
      const mealContext = determineMealContext(userQuery);
      
          // Get daily insights for calorie context
    const insightsResponse = await api.get<ApiResponse<DailyInsights>>('/coach/daily-insights');
    if (!insightsResponse.data) {
      throw new Error('Failed to get daily insights');
    }
    const insights = insightsResponse.data;
    const dailyGoal = insights.goals.calories || 2000;
    const consumedCalories = insights.today_totals.calories || 0;
    const remainingCalories = Math.max(0, dailyGoal - consumedCalories);

    // Get meal history for context
    const historyResponse = await api.get<ApiResponse<MealHistoryItem[]>>('/consumption/history?limit=20');
    if (!historyResponse.data) {
      throw new Error('Failed to get meal history');
    }
    const mealHistory = historyResponse.data;
    const todaysMeals = mealHistory
      .filter((meal: MealHistoryItem) => {
        const mealDate = new Date(meal.timestamp);
        const today = new Date();
        return mealDate.toDateString() === today.toDateString();
      })
      .map((meal: MealHistoryItem) => ({
        name: meal.food_name,
        type: meal.meal_type,
        calories: meal.nutritional_info.calories
      }));

          // Get meal suggestion
    const response = await api.post<ApiResponse<MealSuggestionResponse>>('/coach/meal-suggestion', {
      meal_type: mealContext.type,
      remaining_calories: remainingCalories,
      preferences: mealContext.isLate ? 'prefer lighter meals' : '',
      context: {
        query_context: userQuery,
        current_hour: mealContext.time,
        is_late_meal: mealContext.isLate,
        todays_meals: todaysMeals,
        total_calories_consumed: consumedCalories,
        remaining_daily_calories: remainingCalories
      }
    });

    if (response.success && response.data) {
      setSuggestion(response.data.suggestion);
    } else {
      setError(response.error || 'Failed to get meal suggestion');
    }
    } catch (err) {
      console.error('Error processing AI query:', err);
      setError('Failed to process your request. Please try again.');
    } finally {
      setLocalLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'info';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high': return <WarningIcon />;
      case 'medium': return <InfoIcon />;
      case 'low': return <CheckCircleIcon />;
      default: return <LightbulbIcon />;
    }
  };

  const getScoreEmoji = (score: number) => {
    if (score >= 90) return '🏆';
    if (score >= 80) return '⭐';
    if (score >= 70) return '👍';
    if (score >= 60) return '📈';
    return '💪';
  };

  const createHealthRadarChart = () => {
    if (!progressData) return null;

    return {
              labels: ['Calories', 'Protein', 'Carbs', 'Fiber', 'Nutrition Score', 'Consistency'],
      datasets: [
        {
          label: 'Your Health Metrics',
          data: [
            (progressData.calorie_progress || 0),
            (progressData.protein_progress || 0),
            (progressData.carb_progress || 0),
            (progressData.fiber_progress || 0) * 10,
            (progressData.diabetes_adherence || 0),
            (progressData.consistency_score || 0)
          ],
          backgroundColor: alpha(theme.palette.primary.main, 0.2),
          borderColor: theme.palette.primary.main,
          borderWidth: 2,
          pointBackgroundColor: theme.palette.primary.main,
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: theme.palette.primary.main,
        }
      ]
    };
  };

  const createProgressChart = () => {
    if (!analyticsData?.daily_breakdown) return null;

    const last7Days = analyticsData.daily_breakdown.slice(-7);
    
    return {
      labels: last7Days.map((day: any) => new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })),
      datasets: [
        {
                      label: 'Nutrition Score',
          data: last7Days.map((day: any) => day.diabetes_score || 0),
          borderColor: theme.palette.success.main,
          backgroundColor: alpha(theme.palette.success.main, 0.1),
          tension: 0.4,
          fill: true,
        },
        {
          label: 'Calorie Goal %',
          data: last7Days.map((day: any) => Math.min(100, (day.calories / 2000) * 100)),
          borderColor: theme.palette.warning.main,
          backgroundColor: alpha(theme.palette.warning.main, 0.1),
          tension: 0.4,
          fill: true,
        }
      ]
    };
  };

  // Helper function to determine meal context from user query
  const determineMealContext = (query: string): MealTimeContext => {
    const currentHour = new Date().getHours();
    const queryLower = query.toLowerCase();
    
    // Check for explicit meal type mentions
    if (queryLower.includes('breakfast')) {
      return { type: 'breakfast', time: currentHour, isLate: currentHour >= 10 };
    }
    if (queryLower.includes('lunch')) {
      return { type: 'lunch', time: currentHour, isLate: currentHour >= 15 };
    }
    if (queryLower.includes('dinner')) {
      return { type: 'dinner', time: currentHour, isLate: currentHour >= 20 };
    }
    if (queryLower.includes('snack')) {
      return { type: 'snack', time: currentHour, isLate: false };
    }

    // If no explicit mention, determine based on time
    if (currentHour >= 4 && currentHour < 11) {
      return { type: 'breakfast', time: currentHour, isLate: currentHour >= 10 };
    }
    if (currentHour >= 11 && currentHour < 16) {
      return { type: 'lunch', time: currentHour, isLate: currentHour >= 15 };
    }
    if (currentHour >= 16 && currentHour < 22) {
      return { type: 'dinner', time: currentHour, isLate: currentHour >= 20 };
    }
    return { type: 'snack', time: currentHour, isLate: false };
  };

  const getMealSuggestion = async (userQuery: string) => {
    setLoading(true);
    setError(null);
    try {
      const mealContext = determineMealContext(userQuery);
      const dailyGoal = dailyInsights?.goals?.calories || 2000;
      const consumedCalories = dailyInsights?.today_totals?.calories || 0;
      const remainingCalories = Math.max(0, dailyGoal - consumedCalories);

      // Get today's meals for context
      const todaysMeals = mealHistory
        .filter(meal => {
          const mealDate = new Date(meal.timestamp);
          const today = new Date();
          return mealDate.toDateString() === today.toDateString();
        })
        .map(meal => ({
          name: meal.food_name,
          type: meal.meal_type,
          calories: meal.nutritional_info.calories
        }));

      const response = await api.post<ApiResponse<MealSuggestionResponse>>('/coach/meal-suggestion', {
        meal_type: mealContext.type,
        remaining_calories: remainingCalories,
        preferences: mealContext.isLate ? 'prefer lighter meals' : '',
        context: {
          is_late_meal: mealContext.isLate,
          current_hour: mealContext.time,
          todays_meals: todaysMeals,
          total_calories_consumed: consumedCalories,
          remaining_daily_calories: remainingCalories,
          query_context: userQuery // Send original query for better context
        }
      });

      if (response.success && response.data) {
        setSuggestion(response.data.suggestion);
      } else {
        setError(response.error || 'Failed to get meal suggestion');
      }
    } catch (err) {
      console.error('Error getting meal suggestion:', err);
      setError('Failed to get meal suggestion');
    } finally {
      setLoading(false);
    }
  };

  // Update the suggestion button click handler
  const handleGetSuggestion = () => {
    const userInput = document.querySelector<HTMLInputElement>('input[placeholder="Ask your AI coach"]')?.value || '';
    getMealSuggestion(userInput);
  };

  if (!isLoggedIn) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
          <Typography variant="h3" component="h1" gutterBottom sx={{ color: 'white', fontWeight: 'bold' }}>
            🤖 AI Health Coach
          </Typography>
          <Typography variant="h6" sx={{ color: 'white', mb: 3, opacity: 0.9 }}>
            Your intelligent diabetes management companion
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/login')}
            sx={{ 
              bgcolor: 'white', 
              color: 'primary.main',
              '&:hover': { bgcolor: alpha('#fff', 0.9) }
            }}
          >
            Sign In to Access AI Coach
          </Button>
        </Paper>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading your AI health coach...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert 
          severity="error" 
          action={
            <Button color="inherit" size="small" onClick={fetchAllCoachData}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      {/* Header Section */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ 
          fontWeight: 'bold',
          background: 'linear-gradient(45deg, #667eea, #764ba2)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          🤖 AI Health Coach
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Your intelligent diabetes management companion • Personalized insights and recommendations
        </Typography>
      </Box>

      {/* Quick Actions Floating Button */}
      <Box sx={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}>
        <Tooltip title="Ask AI Coach">
          <Fab 
            color="primary" 
            onClick={() => setShowAIDialog(true)}
            sx={{ mr: 1, mb: 1 }}
          >
            <CoachIcon />
          </Fab>
        </Tooltip>
        <Tooltip title="Refresh Data">
          <Fab 
            size="small"
            onClick={fetchAllCoachData}
            sx={{ mr: 1, mb: 1, bgcolor: 'info.main', '&:hover': { bgcolor: 'info.dark' } }}
          >
            <RefreshIcon />
          </Fab>
        </Tooltip>
      </Box>

      {/* Tabs Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} aria-label="coach tabs">
          <Tab icon={<CoachIcon />} label="AI Insights" />
          <Tab icon={<AnalyticsIcon />} label="Progress Analysis" />
          <Tab icon={<PlanIcon />} label="Adaptive Planning" />
          <Tab icon={<NotificationIcon />} label={`Recommendations ${notifications.length > 0 ? `(${notifications.length})` : ''}`} />
        </Tabs>
      </Box>

      {/* AI Insights Tab */}
      <CustomTabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          {/* Health Score Cards */}
          <Grid item xs={12} md={4}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #A8EDEA, #FED6E3)',
              color: '#333',
              height: '100%'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <HeartIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Nutrition Score</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {getScoreEmoji(coachData?.diabetes_adherence || 0)} {Math.round(coachData?.diabetes_adherence || 0)}%
                </Typography>
                                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  {coachData?.diabetes_adherence === 0 ? 'Start logging meals' :
                   coachData?.diabetes_adherence >= 80 ? 'Excellent management!' :
                   coachData?.diabetes_adherence >= 60 ? 'Good progress' : 'Room for improvement'}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={coachData?.diabetes_adherence || 0}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              color: 'white',
              height: '100%'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrophyIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Consistency Streak</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {coachData?.consistency_streak || 0}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  Days of consistent tracking
                </Typography>
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                  <StarIcon sx={{ mr: 0.5, fontSize: 16 }} />
                  <Typography variant="body2">
                    {coachData?.consistency_streak >= 7 ? 'Amazing streak!' : 'Keep building!'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #4ECDC4, #44A08D)',
              color: 'white',
              height: '100%'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <SpeedIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Overall Progress</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {Math.round(progressData?.overall_score || 0)}%
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  Comprehensive health score
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={progressData?.overall_score || 0}
                  sx={{ mt: 1, bgcolor: alpha('#fff', 0.3), '& .MuiLinearProgress-bar': { bgcolor: 'white' } }}
                />
              </CardContent>
            </Card>
          </Grid>

          {/* AI Recommendations */}
          <Grid item xs={12} md={8}>
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <AIIcon sx={{ mr: 1 }} />
                  Personalized AI Recommendations
                </Typography>
                <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {coachData?.recommendations?.map((rec: any, index: number) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon>
                        {getPriorityIcon(rec.priority)}
                      </ListItemIcon>
                      <ListItemText
                        primary={rec.message}
                        secondary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                            <Chip 
                              label={rec.priority} 
                              color={getPriorityColor(rec.priority)}
                              size="small"
                            />
                            {rec.action && (
                              <Chip 
                                label={rec.action} 
                                variant="outlined"
                                size="small"
                                clickable
                              />
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  )) || (
                    <ListItem>
                      <ListItemText primary="Great job! No specific recommendations at the moment. Keep up the excellent work!" />
                    </ListItem>
                  )}
                </List>
                <CardActions>
                  <Button 
                    variant="contained" 
                    startIcon={<CoachIcon />}
                    onClick={() => setShowAIDialog(true)}
                    fullWidth
                  >
                    Ask AI Coach Anything
                  </Button>
                </CardActions>
              </CardContent>
            </Card>
          </Grid>

          {/* Health Radar Chart */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <SpeedIcon sx={{ mr: 1 }} />
                  Health Metrics Radar
                </Typography>
                {createHealthRadarChart() && (
                  <Box sx={{ height: 300 }}>
                    <Radar 
                      data={createHealthRadarChart()!} 
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          r: {
                            beginAtZero: true,
                            max: 100,
                          },
                        },
                      }}
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Today's Insights */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <LightbulbIcon sx={{ mr: 1 }} />
                  Today's AI Insights
                </Typography>
                <Grid container spacing={2}>
                  {insights.map((insight: any, index: number) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Paper sx={{ p: 2, bgcolor: 'primary.50' }}>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                          {insight.category}
                        </Typography>
                        <Typography variant="body2">
                          {insight.message}
                        </Typography>
                        {insight.action && (
                          <Button size="small" sx={{ mt: 1 }}>
                            {insight.action}
                          </Button>
                        )}
                      </Paper>
                    </Grid>
                  )) || (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        Keep logging your meals to get personalized AI insights!
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CustomTabPanel>

      {/* Progress Analysis Tab */}
      <CustomTabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          {/* Progress Chart */}
          <Grid item xs={12} md={8}>
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <TimelineIcon sx={{ mr: 1 }} />
                  Weekly Progress Trends
                </Typography>
                {createProgressChart() && (
                  <Box sx={{ height: 300 }}>
                    <Line 
                      data={createProgressChart()!} 
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'top',
                          },
                        },
                        scales: {
                          y: {
                            beginAtZero: true,
                            max: 100,
                          },
                        },
                      }}
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Progress Stats */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Progress Statistics
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Calorie Goal Achievement
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={progressData?.calorie_progress || 0}
                      sx={{ mt: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption">
                      {Math.round(progressData?.calorie_progress || 0)}%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Protein Goal Achievement
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={progressData?.protein_progress || 0}
                      color="success"
                      sx={{ mt: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption">
                      {Math.round(progressData?.protein_progress || 0)}%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Carb Management
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={progressData?.carb_progress || 0}
                      color="warning"
                      sx={{ mt: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption">
                      {Math.round(progressData?.carb_progress || 0)}%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Consistency Score
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={progressData?.consistency_score || 0}
                      color="info"
                      sx={{ mt: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption">
                      {Math.round(progressData?.consistency_score || 0)}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Detailed Analytics */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Comprehensive Health Analysis
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h4" color="primary">
                        {analyticsData?.total_meals || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Meals Logged
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h4" color="success.main">
                        {Math.round(analyticsData?.avg_diabetes_score || 0)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Nutrition Score
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h4" color="warning.main">
                        {Math.round(analyticsData?.avg_calories || 0)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Daily Calories
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h4" color="info.main">
                        {analyticsData?.consistency_days || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Consistent Days
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CustomTabPanel>

      {/* Adaptive Planning Tab */}
      <CustomTabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <PlanIcon sx={{ mr: 1 }} />
                  Adaptive Meal Planning
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create a personalized meal plan based on your eating history, preferences, and health goals.
                </Typography>
                <Button
                  variant="contained"
                  onClick={handleCreateAdaptivePlan}
                  disabled={adaptivePlanLoading}
                  startIcon={adaptivePlanLoading ? <CircularProgress size={20} /> : <PlanIcon />}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  {adaptivePlanLoading ? 'Creating Adaptive Plan...' : 'Create Adaptive Meal Plan'}
                </Button>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>
                  Quick Actions:
                </Typography>
                <ButtonGroup variant="outlined" fullWidth>
                  <Button onClick={() => navigate('/meal_plans')}>View Plans</Button>
                  <Button onClick={() => navigate('/my-recipes')}>Recipes</Button>
                  <Button onClick={() => navigate('/my-shopping-lists')}>Shopping</Button>
                </ButtonGroup>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <ChatIcon sx={{ mr: 1 }} />
                  AI Chat Assistant
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Chat with your AI health coach for personalized advice and meal suggestions.
                </Typography>
                <Button
                  variant="contained"
                  onClick={() => navigate('/chat')}
                  startIcon={<ChatIcon />}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  Open AI Chat
                </Button>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>
                  Recent Chat Topics:
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Meal suggestions for dinner" secondary="2 hours ago" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Diabetes-friendly snacks" secondary="Yesterday" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Exercise recommendations" secondary="2 days ago" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Planning Features */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Intelligent Planning Features
                </Typography>
                <Grid container spacing={2}>
                  {[
                    {
                      title: 'Smart Meal Suggestions',
                      description: 'AI-powered meal recommendations based on your preferences and health goals',
                      icon: <RestaurantIcon />,
                      action: () => setShowAIDialog(true)
                    },
                    {
                      title: 'Adaptive Recipes',
                      description: 'Personalized recipes that adapt to your dietary needs and restrictions',
                      icon: <RecipeIcon />,
                      action: () => navigate('/my-recipes')
                    },
                    {
                      title: 'Smart Shopping Lists',
                      description: 'Automatically generated shopping lists based on your meal plans',
                      icon: <ShoppingIcon />,
                      action: () => navigate('/my-shopping-lists')
                    },
                    {
                      title: 'Progress Tracking',
                      description: 'Comprehensive tracking of your health metrics and goals',
                      icon: <AnalyticsIcon />,
                      action: () => navigate('/consumption-history')
                    }
                  ].map((feature, index) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                      <Paper 
                        sx={{ 
                          p: 2, 
                          textAlign: 'center', 
                          cursor: 'pointer',
                          '&:hover': { 
                            transform: 'translateY(-2px)',
                            boxShadow: 4
                          },
                          transition: 'all 0.2s ease-in-out'
                        }}
                        onClick={feature.action}
                      >
                        <Box sx={{ color: 'primary.main', mb: 1 }}>
                          {feature.icon}
                        </Box>
                        <Typography variant="subtitle2" gutterBottom>
                          {feature.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {feature.description}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CustomTabPanel>

      {/* Recommendations Tab */}
      <CustomTabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <NotificationIcon sx={{ mr: 1 }} />
                  AI-Powered Recommendations
                </Typography>
                {notifications.length > 0 ? (
                  <List>
                    {notifications.map((notification: any, index: number) => (
                      <Accordion key={index}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                            {getPriorityIcon(notification.priority)}
                            <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                              {notification.message}
                            </Typography>
                            <Chip 
                              label={notification.priority} 
                              color={getPriorityColor(notification.priority)}
                              size="small"
                            />
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {notification.details || 'No additional details available.'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Generated: {new Date(notification.timestamp).toLocaleString()}
                          </Typography>
                          {notification.action && (
                            <Box sx={{ mt: 2 }}>
                              <Button variant="outlined" size="small">
                                {notification.action}
                              </Button>
                            </Box>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No recommendations at the moment. You're doing great! 🎉
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CustomTabPanel>

      {/* AI Coach Dialog */}
      <Dialog open={showAIDialog} onClose={() => setShowAIDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <CoachIcon sx={{ mr: 1 }} />
          AI Health Coach
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Ask your AI coach"
            placeholder="What should I eat for dinner? How can I improve my diabetes management?"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={aiQuery}
            onChange={(e) => setAIQuery(e.target.value)}
          />
          {aiResponse && (
            <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
              <Typography variant="body1">
                {aiResponse}
              </Typography>
            </Paper>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAIDialog(false)}>Close</Button>
          <Button 
            onClick={handleGetSuggestion} 
            variant="contained"
            disabled={aiLoading || !aiQuery.trim()}
            startIcon={aiLoading ? <CircularProgress size={20} /> : <CoachIcon />}
          >
            {aiLoading ? 'Thinking...' : 'Ask AI Coach'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Daily Progress Summary */}
      {dailyInsights && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Today's Progress
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MealIcon />
                  <Typography>
                    Calories: {dailyInsights.today_totals.calories}/{dailyInsights.goals.calories}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TimeIcon />
                  <Typography>
                    Meals Today: {dailyInsights.meals_logged_today}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingUpIcon />
                  <Typography>
                    Weekly Progress: {dailyInsights.weekly_stats.diabetes_suitable_percentage.toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HeartIcon />
                  <Typography>
                    Health Score: {calculateHealthScore(dailyInsights)}%
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Meal Suggestion Section */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <DiningIcon />
            <Typography variant="h6">
              Dinner Suggestions
            </Typography>
            {new Date().getHours() >= 20 && (
              <Chip 
                label="Late Dinner Mode" 
                color="warning" 
                size="small" 
                sx={{ ml: 'auto' }}
              />
            )}
          </Box>

          <Button
            variant="contained"
            onClick={() => getMealSuggestion('dinner')}
            disabled={loading}
            sx={{ mb: 2 }}
          >
            Get Dinner Suggestion
          </Button>

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
              <CircularProgress />
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {suggestion && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography 
                component="div" 
                sx={{ 
                  whiteSpace: 'pre-wrap',
                  '& strong': { color: 'primary.main' }
                }}
              >
                {suggestion}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

// Helper function to calculate health score based on daily insights
const calculateHealthScore = (insights: DailyInsights | null): number => {
  if (!insights) return 0;

  const factors = {
    calorieAdherence: insights.adherence.calories / 100,
    proteinAdherence: insights.adherence.protein / 100,
    carbAdherence: insights.adherence.carbohydrates / 100,
    diabetesSuitable: insights.weekly_stats.diabetes_suitable_percentage / 100,
    mealsLogged: Math.min(insights.meals_logged_today / 3, 1) // Assuming 3 meals is ideal
  };

  const weights = {
    calorieAdherence: 0.25,
    proteinAdherence: 0.2,
    carbAdherence: 0.2,
    diabetesSuitable: 0.25,
    mealsLogged: 0.1
  };

  const score = Object.entries(factors).reduce((total, [key, value]) => {
    return total + (value * weights[key as keyof typeof weights] * 100);
  }, 0);

  return Math.round(score);
};

export default AICoach; 