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
import config from '../config/environment';

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
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/coach/daily-insights`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const responseData = await response.json();
        if (responseData.data) {
          setDailyInsights(responseData.data);
        }
      }
    } catch (err) {
      console.error('Error fetching daily insights:', err);
      setError('Failed to fetch daily insights');
    }
  };

  const fetchMealHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/consumption/history?limit=20`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const responseData = await response.json();
        if (responseData.data) {
          setMealHistory(responseData.data);
        }
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
        fetch(`${config.API_URL}/coach/daily-insights`, { headers }),
        fetch(`${config.API_URL}/consumption/analytics?days=30`, { headers }),
        fetch(`${config.API_URL}/consumption/progress`, { headers }),
        fetch(`${config.API_URL}/coach/notifications`, { headers }),
        fetch(`${config.API_URL}/coach/consumption-insights?days=30`, { headers })
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
    const insightsResponse = await fetch(`${config.API_URL}/coach/daily-insights`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    if (!insightsResponse.ok) {
      throw new Error('Failed to get daily insights');
    }
    const insightsData = await insightsResponse.json();
    const insights = insightsData.data;
    const dailyGoal = insights.goals.calories || 2000;
    const consumedCalories = insights.today_totals.calories || 0;
    const remainingCalories = Math.max(0, dailyGoal - consumedCalories);

    // Get meal history for context
    const historyResponse = await fetch(`${config.API_URL}/consumption/history?limit=20`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    if (!historyResponse.ok) {
      throw new Error('Failed to get meal history');
    }
    const historyData = await historyResponse.json();
    const mealHistory = historyData.data;
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
    const response = await api.post<ApiResponse<MealSuggestionResponse>>('https://Dietra-backend.azurewebsites.net/coach/meal-suggestion', {
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

      const response = await api.post<ApiResponse<MealSuggestionResponse>>('https://Dietra-backend.azurewebsites.net/coach/meal-suggestion', {
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

          {/* AI Chat Interface - Made Much Bigger */}
          <Grid item xs={12}>
            <Card sx={{ minHeight: 800 }}>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <ChatIcon sx={{ mr: 2, fontSize: 32 }} />
                  💬 AI Health Coach Chat
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4, fontSize: '1.1rem' }}>
                  Get instant personalized advice, meal suggestions, and health insights from your AI coach. Ask anything about your diabetes management, nutrition, or meal planning!
                </Typography>
                
                {/* Enhanced Chat Interface - Much Bigger */}
                <Box sx={{ 
                  bgcolor: 'grey.50', 
                  p: 4, 
                  borderRadius: 3, 
                  border: '2px solid', 
                  borderColor: 'primary.light',
                  minHeight: 600,
                  display: 'flex',
                  flexDirection: 'column',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}>
                  <Box sx={{ 
                    flexGrow: 1, 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    flexDirection: 'column',
                    textAlign: 'center',
                    py: 4
                  }}>
                    <CoachIcon sx={{ fontSize: 80, color: 'primary.main', mb: 3 }} />
                    <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      Ready to help you achieve your health goals!
                    </Typography>
                    <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: 600, lineHeight: 1.6 }}>
                      Ask me about meal planning, nutrition advice, diabetes management, exercise recommendations, or any health-related questions. I'm here to provide personalized guidance based on your profile!
                    </Typography>
                    
                    {/* Quick suggestion buttons - Made Bigger */}
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', mb: 4, maxWidth: 800 }}>
                      {[
                        "What should I eat for dinner?",
                        "Suggest a healthy snack",
                        "Check my progress",
                        "Meal prep ideas",
                        "Help with portion control",
                        "Blood sugar management tips"
                      ].map((suggestion, index) => (
                        <Chip
                          key={index}
                          label={suggestion}
                          onClick={() => {
                            setAIQuery(suggestion);
                            setShowAIDialog(true);
                          }}
                          clickable
                          color="primary"
                          variant="outlined"
                          size="medium"
                          sx={{ 
                            py: 1.5, 
                            px: 2, 
                            fontSize: '0.95rem',
                            '&:hover': { 
                              bgcolor: 'primary.main', 
                              color: 'white',
                              transform: 'translateY(-2px)',
                              boxShadow: 2
                            },
                            transition: 'all 0.2s ease'
                          }}
                        />
                      ))}
                    </Box>
                  </Box>
                  
                  <Button 
                    variant="contained" 
                    size="large"
                    startIcon={<CoachIcon sx={{ fontSize: 28 }} />}
                    onClick={() => setShowAIDialog(true)}
                    sx={{ 
                      py: 3,
                      px: 6,
                      fontSize: '1.3rem',
                      fontWeight: 'bold',
                      borderRadius: 3,
                      maxWidth: 400,
                      boxShadow: 3,
                      '&:hover': {
                        boxShadow: 6,
                        transform: 'translateY(-2px)'
                      },
                      transition: 'all 0.2s ease'
                    }}
                  >
                    Start Chatting with AI Coach
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Condensed AI Recommendations and Health Metrics */}
          <Grid item xs={12}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Card sx={{ height: 300 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <AIIcon sx={{ mr: 1 }} />
                      Quick AI Recommendations
                    </Typography>
                    <List sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {coachData?.recommendations?.slice(0, 3).map((rec: any, index: number) => (
                        <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 35 }}>
                            {getPriorityIcon(rec.priority)}
                          </ListItemIcon>
                          <ListItemText
                            primary={<Typography variant="body2">{rec.message}</Typography>}
                            secondary={
                              <Chip 
                                label={rec.priority} 
                                color={getPriorityColor(rec.priority)}
                                size="small"
                                sx={{ mt: 0.5 }}
                              />
                            }
                          />
                        </ListItem>
                      )) || (
                        <ListItem sx={{ px: 0 }}>
                          <ListItemText 
                            primary={<Typography variant="body2">Great job! No specific recommendations at the moment. Keep up the excellent work!</Typography>} 
                          />
                        </ListItem>
                      )}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Card sx={{ height: 300 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <SpeedIcon sx={{ mr: 1 }} />
                      Health Overview
                    </Typography>
                    {createHealthRadarChart() && (
                      <Box sx={{ height: 200 }}>
                        <Radar 
                          key={`health-radar-${Date.now()}`}
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
                            plugins: {
                              legend: {
                                display: false
                              }
                            }
                          }}
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Today's Insights - Condensed */}
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ py: 2 }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <LightbulbIcon sx={{ mr: 1 }} />
                  Today's Quick Insights
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  {insights.slice(0, 4).map((insight: any, index: number) => (
                    <Paper key={index} sx={{ p: 1.5, bgcolor: 'primary.50', flex: '1 1 250px', minWidth: 200 }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontSize: '0.875rem' }}>
                        {insight.category}
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.825rem' }}>
                        {insight.message}
                      </Typography>
                    </Paper>
                  )) || (
                    <Typography variant="body2" color="text.secondary">
                      Keep logging your meals to get personalized AI insights!
                    </Typography>
                  )}
                </Box>
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
                      key={`weekly-progress-${Date.now()}`}
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
                      key={`calorie-progress-${Date.now()}`}
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
                      key={`protein-progress-${Date.now()}`}
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
                      key={`carb-progress-${Date.now()}`}
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
                      key={`consistency-score-${Date.now()}`}
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

      {/* Recommendations Tab */}
      <CustomTabPanel value={tabValue} index={2}>
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