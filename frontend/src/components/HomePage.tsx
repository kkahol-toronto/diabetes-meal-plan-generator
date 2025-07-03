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
  LinearProgress,
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
  Tooltip,
  Fab,
  useTheme,
  alpha,
  CardActions,
  ButtonGroup,
  Tab,
  Tabs,
  ToggleButtonGroup,
  ToggleButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Analytics as AnalyticsIcon,
  Lightbulb as LightbulbIcon,
  Chat as ChatIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  LocalFireDepartment as CaloriesIcon,
  FitnessCenter as ProteinIcon,
  AutoAwesome as AIIcon,
  Timeline as TimelineIcon,
  Assignment as PlanIcon,
  Refresh as RefreshIcon,
  NotificationsActive as NotificationIcon,
  Psychology as CoachIcon,
  History as HistoryIcon,
  Star as StarIcon,
  Favorite as HeartIcon,
  Speed as SpeedIcon,
  EmojiEvents as TrophyIcon,
  Grain as CarbsIcon,
  Opacity as FatIcon,
  Nature as FiberIcon,
  Cake as SugarIcon,
  WaterDrop as SodiumIcon,
} from '@mui/icons-material';
import { useApp } from '../contexts/AppContext';
import { Line, Doughnut, Radar } from 'react-chartjs-2';
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

// Enhanced types for comprehensive nutrition tracking (from ConsumptionHistory.tsx)
interface NutritionalInfo {
    calories: number;
    carbohydrates: number;
    protein: number;
    fat: number;
    fiber: number;
    sugar: number;
    sodium: number;
  // Additional micronutrients
  calcium?: number;
  iron?: number;
  potassium?: number;
  vitamin_c?: number;
  vitamin_d?: number;
  vitamin_b12?: number;
  folate?: number;
  magnesium?: number;
  zinc?: number;
  saturated_fat?: number;
  trans_fat?: number;
  cholesterol?: number;
}

interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'doughnut';
  metric: keyof NutritionalInfo;
  title: string;
  color: string;
  icon: React.ReactNode;
}

interface ConsumptionAnalytics {
  total_meals: number;
  date_range: {
    start_date: string;
    end_date: string;
  };
  daily_averages: NutritionalInfo;
  weekly_trends: {
    calories: number[];
    protein: number[];
    carbohydrates: number[];
    fat: number[];
  };
  meal_distribution: {
    breakfast: number;
    lunch: number;
    dinner: number;
    snack: number;
  };
  top_foods: Array<{
    food: string;
    frequency: number;
  total_calories: number;
  }>;
  adherence_stats: {
    diabetes_suitable_percentage: number;
    calorie_goal_adherence: number;
    protein_goal_adherence: number;
    carb_goal_adherence: number;
  };
  daily_nutrition_history: Array<{
    date: string;
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
    meals_count: number;
  }>;
}

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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
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

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { showNotification, setLoading } = useApp();
  const [loading, setLocalLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [progressData, setProgressData] = useState<any>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [todaysMealPlan, setTodaysMealPlan] = useState<any>(null);
  const [showQuickLogDialog, setShowQuickLogDialog] = useState(false);
  const [quickLogFood, setQuickLogFood] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [macroTimeRange, setMacroTimeRange] = useState<'daily' | 'weekly' | 'bi-weekly' | 'monthly'>('daily');
  const [macroConsumptionAnalytics, setMacroConsumptionAnalytics] = useState<any>(null);
  const [adaptivePlanLoading, setAdaptivePlanLoading] = useState(false);
  const [showAICoachDialog, setShowAICoachDialog] = useState(false);
  const [aiCoachQuery, setAICoachQuery] = useState('');
  const [aiCoachResponse, setAICoachResponse] = useState('');
  const [aiCoachLoading, setAICoachLoading] = useState(false);
  const [analyticsTabValue, setAnalyticsTabValue] = useState(0); // For Daily, Weekly, etc. tabs
  const [selectedTimeRange, setSelectedTimeRange] = useState<'daily' | 'weekly' | 'bi-weekly' | 'monthly'>('daily');
  const [consumptionAnalytics, setConsumptionAnalytics] = useState<any>(null);

  const token = localStorage.getItem('token');
  const isLoggedIn = !!token;

  const fetchAllData = useCallback(async () => {
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

      // Fetch all data in parallel for maximum efficiency
      const [
        dailyInsightsResponse,
        analyticsResponse,
        progressResponse,
        notificationsResponse,
        mealPlanResponse,
      ] = await Promise.all([
        fetch('/coach/daily-insights', { headers }),
        fetch('/consumption/analytics?days=30', { headers }), // Fetching 30 days for initial analytics
        fetch('/consumption/progress', { headers }),
        fetch('/coach/notifications', { headers }),
        fetch('/coach/todays-meal-plan', { headers })
      ]);

      if (dailyInsightsResponse.status === 401 ||
          analyticsResponse.status === 401 ||
          progressResponse.status === 401 ||
          notificationsResponse.status === 401 ||
          mealPlanResponse.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      const [dailyData, analytics, progress, notifs, mealPlan] = await Promise.all([
        dailyInsightsResponse.ok ? dailyInsightsResponse.json() : null,
        analyticsResponse.ok ? analyticsResponse.json() : null,
        progressResponse.ok ? progressResponse.json() : [],
        notificationsResponse.ok ? notificationsResponse.json() : null,
        mealPlanResponse.ok ? mealPlanResponse.json() : null
      ]);

      setDashboardData(dailyData);
      setAnalyticsData(analytics); // Existing analytics data, consider renaming for clarity
      setProgressData(progress);
      setNotifications(notifs);
      setTodaysMealPlan(mealPlan);

    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Unable to load dashboard. Please try again.');
    } finally {
      setLocalLoading(false);
    }
  }, [token, isLoggedIn, navigate]);

  const fetchConsumptionAnalytics = useCallback(async (timeRange: 'daily' | 'weekly' | 'bi-weekly' | 'monthly') => {
    if (!isLoggedIn) return;

    setLocalLoading(true);
    setError(null);

    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    let days = 0;
    switch (timeRange) {
      case 'daily': days = 1; break;
      case 'weekly': days = 7; break;
      case 'bi-weekly': days = 14; break;
      case 'monthly': days = 30; break;
      default: days = 30;
    }

    console.log(`Fetching consumption analytics for time range: ${timeRange} (days: ${days})`);

    try {
      const response = await fetch(`/consumption/analytics?days=${days}`, { headers });
      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }
      if (!response.ok) throw new Error('Failed to fetch consumption analytics');
      const data = await response.json();
      setConsumptionAnalytics(data);
    } catch (err) {
      console.error(`Error fetching ${timeRange} consumption analytics:`, err);
      setError(`Unable to load ${timeRange} analytics. Please try again.`);
    } finally {
      setLocalLoading(false);
    }
  }, [token, isLoggedIn, navigate]);

  const fetchMacroConsumptionAnalytics = useCallback(async (timeRange: 'daily' | 'weekly' | 'bi-weekly' | 'monthly') => {
    if (!isLoggedIn) return;

    // Do not set local loading/error for this specific fetch to avoid interfering with main dashboard loading state
    // setLocalLoading(true);
    // setError(null);

    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    let days = 0;
    switch (timeRange) {
      case 'daily': days = 1; break;
      case 'weekly': days = 7; break;
      case 'bi-weekly': days = 14; break;
      case 'monthly': days = 30; break;
      default: days = 30;
    }

    console.log(`Fetching macro analytics for time range: ${timeRange} (days: ${days})`);

    try {
      const response = await fetch(`/consumption/analytics?days=${days}`, { headers });
      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }
      if (!response.ok) throw new Error('Failed to fetch macro consumption analytics');
      const data = await response.json();
      setMacroConsumptionAnalytics(data);
    } catch (err) {
      console.error(`Error fetching ${timeRange} macro consumption analytics:`, err);
      // setError(`Unable to load ${timeRange} macro analytics. Please try again.`);
    }
  }, [token, isLoggedIn, navigate]);

  useEffect(() => {
    fetchAllData();
    fetchConsumptionAnalytics(selectedTimeRange); // Initial fetch for consumption analytics
    fetchMacroConsumptionAnalytics(macroTimeRange); // Initial fetch for macro analytics
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchAllData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchAllData, fetchConsumptionAnalytics, selectedTimeRange, fetchMacroConsumptionAnalytics, macroTimeRange]);

  const handleQuickLogFood = async () => {
    if (!quickLogFood.trim()) return;
    
    try {
      setLoading(true, 'Analyzing and logging food...');
      
      const response = await fetch('/coach/quick-log', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ food_name: quickLogFood, portion: 'medium portion' }),
      });

      if (response.ok) {
        await response.json();
        showNotification(`✅ Successfully logged: ${quickLogFood}`, 'success');
        setQuickLogFood('');
        setShowQuickLogDialog(false);
        fetchAllData(); // Refresh all data
      } else {
        throw new Error('Failed to log food');
      }
    } catch (err) {
      showNotification('Failed to log food. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAdaptivePlan = async () => {
    // Ask a couple of quick questions first (super-light UX – window.prompt for now)
    const daysStr = window.prompt('📅 How many days should the adaptive plan cover? (1-7)', '1');
    if (daysStr === null) return; // User cancelled
    const days = Math.min(Math.max(parseInt(daysStr || '1', 10) || 1, 1), 7);

    const cuisineType = window.prompt('🍽️ Preferred cuisine type (leave blank to use your profile preference):', '') || '';

    try {
      setAdaptivePlanLoading(true);
      setLoading(true, 'Creating your personalized meal plan...');
      
      const response = await fetch('/coach/adaptive-meal-plan', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ days, cuisine_type: cuisineType }),
      });

      if (response.ok) {
        await response.json();
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

  const handleAICoachQuery = async () => {
    if (!aiCoachQuery.trim()) return;
    
    try {
      setAICoachLoading(true);
      setAICoachResponse(''); // Clear previous response
      
      const response = await fetch('/coach/meal-suggestion', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: aiCoachQuery }),
      });

      if (response.ok) {
        const result = await response.json();
        const aiResponse = result.suggestion || result.response || 'No response available';
        setAICoachResponse(aiResponse);
        
        // Clear the query after successful response
        setAICoachQuery('');
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to get AI response');
      }
    } catch (err) {
      console.error('AI Coach Error:', err);
      setAICoachResponse(`Sorry, I encountered an error: ${err instanceof Error ? err.message : 'Please try again.'}`);
    } finally {
      setAICoachLoading(false);
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

  // Chart configurations for different metrics (from ConsumptionHistory.tsx)
  const chartConfigs: ChartConfig[] = [
    { type: 'bar', metric: 'calories', title: 'Calories', color: '#FF6B6B', icon: <CaloriesIcon /> },
    { type: 'bar', metric: 'protein', title: 'Protein (g)', color: '#4ECDC4', icon: <ProteinIcon /> },
    { type: 'bar', metric: 'carbohydrates', title: 'Carbohydrates (g)', color: '#45B7D1', icon: <CarbsIcon /> },
    { type: 'bar', metric: 'fat', title: 'Fat (g)', color: '#FFA07A', icon: <FatIcon /> },
    { type: 'bar', metric: 'fiber', title: 'Fiber (g)', color: '#98D8C8', icon: <FiberIcon /> },
    { type: 'bar', metric: 'sugar', title: 'Sugar (g)', color: '#F7DC6F', icon: <SugarIcon /> },
    { type: 'bar', metric: 'sodium', title: 'Sodium (mg)', color: '#BB8FCE', icon: <SodiumIcon /> }
  ];

  // Helper function to format date for charts
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return 'Invalid Date';
    }
  };

  // Helper functions for chart data generation
  const generateChartData = (metric: keyof NutritionalInfo) => {
    if (!consumptionAnalytics?.daily_nutrition_history) return null;

    const data = consumptionAnalytics.daily_nutrition_history;
    const labels = data.map((day: any) => formatDate(day.date));
    const values = data.map((day: any) => (day as any)[metric] || 0);

    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const color = chartConfig?.color || '#45B7D1';

    return {
      labels,
      datasets: [{
        label: chartConfig?.title || metric,
        data: values,
        backgroundColor: color,
        borderColor: color,
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        pointBackgroundColor: color,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4
      }]
    };
  };

  const getChartOptions = (metric: keyof NutritionalInfo) => {
    const chartConfig = chartConfigs.find(config => config.metric === metric);
    
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            usePointStyle: true,
            padding: 20
          }
        },
        title: {
          display: true,
          text: `${chartConfig?.title || metric} - ${selectedTimeRange.charAt(0).toUpperCase() + selectedTimeRange.slice(1)} Analysis`,
          font: {
            size: 16,
            weight: 'bold' as const
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: chartConfig?.color || '#45B7D1',
          borderWidth: 1
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0,0,0,0.1)'
          },
          ticks: {
            font: {
              size: 12
            }
          }
        },
        x: {
          grid: {
            color: 'rgba(0,0,0,0.1)'
          },
          ticks: {
            font: {
              size: 12
            }
          }
        }
      }
    };
  };

  const renderChart = (metric: keyof NutritionalInfo) => {
    const data = generateChartData(metric);
    if (!data) return <Typography>No data available</Typography>;

    const options = getChartOptions(metric);

    return <Line data={data} options={options} />;
  };

  // Chart configurations with beautiful styling
  const createMacroChart = () => {
    let protein = 0;
    let carbs = 0;
    let fat = 0;

    if (macroTimeRange === 'daily') {
      if (!dashboardData?.today_totals) return null;
      protein = dashboardData.today_totals.protein || 0;
      carbs = dashboardData.today_totals.carbohydrates || 0;
      fat = dashboardData.today_totals.fat || 0;
    } else { // macroTimeRange is 'weekly', 'bi-weekly', or 'monthly'
      if (!macroConsumptionAnalytics || !macroConsumptionAnalytics.daily_nutrition_history) {
        // If data is not yet loaded for the selected non-daily range, return null
        return null;
      }
      const history = macroConsumptionAnalytics.daily_nutrition_history;
      const daysToAverage = macroTimeRange === 'weekly' ? 7 : macroTimeRange === 'bi-weekly' ? 14 : 30;
      const relevantData = history.slice(-daysToAverage);

      if (relevantData.length === 0) return null;

      const totalProtein = relevantData.reduce((sum: number, day: any) => sum + (day.protein || 0), 0);
      const totalCarbs = relevantData.reduce((sum: number, day: any) => sum + (day.carbohydrates || 0), 0);
      const totalFat = relevantData.reduce((sum: number, day: any) => sum + (day.fat || 0), 0);

      protein = totalProtein / relevantData.length;
      carbs = totalCarbs / relevantData.length;
      fat = totalFat / relevantData.length;
    }

    if (protein === 0 && carbs === 0 && fat === 0) return null; // No data to display

    return {
      labels: ['Protein', 'Carbs', 'Fat'],
      datasets: [
        {
          label: 'Macros',
          data: [
            protein,
            carbs,
            fat
          ],
          backgroundColor: [
            alpha(theme.palette.success.main, 0.8),
            alpha(theme.palette.warning.main, 0.8),
            alpha(theme.palette.info.main, 0.8)
          ],
          borderColor: [
            theme.palette.success.main,
            theme.palette.warning.main,
            theme.palette.info.main
          ],
          borderWidth: 2,
        }
      ]
    };
  };

  const createWeeklyTrendChart = () => {
    if (!analyticsData?.daily_breakdown) return null;

    const last7Days = analyticsData.daily_breakdown.slice(-7);
    
    return {
      labels: last7Days.map((day: any) => new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })),
      datasets: [
        {
          label: 'Calories',
          data: last7Days.map((day: any) => day.calories || 0),
          borderColor: theme.palette.primary.main,
          backgroundColor: alpha(theme.palette.primary.main, 0.1),
          tension: 0.4,
          fill: true,
        },
        {
          label: 'Diabetes Score',
          data: last7Days.map((day: any) => (day.diabetes_score || 0) * 10), // Scale for visibility
          borderColor: theme.palette.success.main,
          backgroundColor: alpha(theme.palette.success.main, 0.1),
          tension: 0.4,
          fill: true,
        }
      ]
    };
  };

  const createHealthRadarChart = () => {
    if (!progressData) return null;

    return {
      labels: ['Calories', 'Protein', 'Carbs', 'Fiber', 'Diabetes Score', 'Consistency'],
      datasets: [
        {
          label: 'Your Health Metrics',
          data: [
            (progressData.calorie_progress || 0),
            (progressData.protein_progress || 0),
            (progressData.carb_progress || 0),
            (progressData.fiber_progress || 0) * 10, // Scale for visibility
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

  const getProgressColor = (value: number) => {
    if (value >= 90) return 'success';
    if (value >= 70) return 'warning';
    return 'error';
  };

  const getScoreEmoji = (score: number) => {
    if (score >= 90) return '🏆';
    if (score >= 80) return '⭐';
    if (score >= 70) return '👍';
    if (score >= 60) return '📈';
    return '💪';
  };

  if (!isLoggedIn) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
          <Typography variant="h3" component="h1" gutterBottom sx={{ color: 'white', fontWeight: 'bold' }}>
            🩺 AI Diabetes Coach
          </Typography>
          <Typography variant="h6" sx={{ color: 'white', mb: 3, opacity: 0.9 }}>
            Your intelligent companion for diabetes management
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
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
              Sign In
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/register')}
              sx={{ 
                borderColor: 'white', 
                color: 'white',
                '&:hover': { borderColor: 'white', bgcolor: alpha('#fff', 0.1) }
              }}
            >
              Get Started
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading your personalized dashboard...
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
            <Button color="inherit" size="small" onClick={fetchAllData}>
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
          background: 'linear-gradient(45deg, #2E7D32, #4CAF50)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          🤖 AI Diabetes Coach Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Your intelligent health companion • Last updated: {new Date().toLocaleTimeString()}
        </Typography>
      </Box>

      {/* Tabs Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} aria-label="dashboard tabs">
          <Tab icon={<AnalyticsIcon />} label="Overview" />
          <Tab icon={<TimelineIcon />} label="Analytics" />
          <Tab icon={<CoachIcon />} label="AI Insights" />
          <Tab icon={<NotificationIcon />} label={`Notifications ${notifications.length > 0 ? `(${notifications.length})` : ''}`} />
        </Tabs>
      </Box>

      {/* Overview Tab */}
      <CustomTabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          {/* Today's Summary Cards */}
          <Grid item xs={12} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
              color: 'white',
              height: '100%'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CaloriesIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Calories Today</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {dashboardData?.today_totals?.calories || 0}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  Goal: {dashboardData?.goals?.calories || 2000}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={Math.min(((dashboardData?.today_totals?.calories || 0) / (dashboardData?.goals?.calories || 2000)) * 100, 100)}
                  sx={{ mt: 1, bgcolor: alpha('#fff', 0.3), '& .MuiLinearProgress-bar': { bgcolor: 'white' } }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #4ECDC4, #44A08D)',
              color: 'white',
              height: '100%'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ProteinIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Protein</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {dashboardData?.today_totals?.protein || 0}g
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  Goal: {dashboardData?.goals?.protein || 150}g
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={Math.min(((dashboardData?.today_totals?.protein || 0) / (dashboardData?.goals?.protein || 150)) * 100, 100)}
                  sx={{ mt: 1, bgcolor: alpha('#fff', 0.3), '& .MuiLinearProgress-bar': { bgcolor: 'white' } }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #A8EDEA, #FED6E3)',
              color: '#333',
              height: '100%'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <HeartIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Diabetes Score</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {getScoreEmoji(dashboardData?.diabetes_adherence || 0)} {Math.round(dashboardData?.diabetes_adherence || 0)}%
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  {dashboardData?.diabetes_adherence >= 80 ? 'Excellent!' : 
                   dashboardData?.diabetes_adherence >= 60 ? 'Good progress' : 'Keep improving'}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={dashboardData?.diabetes_adherence || 0}
                  color={getProgressColor(dashboardData?.diabetes_adherence || 0)}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              color: 'white',
              height: '100%'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrophyIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Streak</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {dashboardData?.consistency_streak || 0}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  Days consistent
                </Typography>
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                  <StarIcon sx={{ mr: 0.5, fontSize: 16 }} />
                  <Typography variant="body2">
                    {dashboardData?.consistency_streak >= 7 ? 'Amazing!' : 'Keep going!'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Macro Distribution Chart */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <AnalyticsIcon sx={{ mr: 1 }} />
                  Macronutrients
                </Typography>
                <FormControl variant="outlined" size="small" sx={{ mb: 2, minWidth: 120 }}>
                  <InputLabel id="macro-time-range-label">Time Range</InputLabel>
                  <Select
                    labelId="macro-time-range-label"
                    id="macro-time-range-select"
                    value={macroTimeRange}
                    onChange={(e) => {
                      const newTimeRange = e.target.value as 'daily' | 'weekly' | 'bi-weekly' | 'monthly';
                      setMacroTimeRange(newTimeRange);
                      fetchMacroConsumptionAnalytics(newTimeRange); // Trigger fetch on change
                    }}
                    label="Time Range"
                  >
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="bi-weekly">Bi-Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                  </Select>
                </FormControl>
                {createMacroChart() && (
                  <Box sx={{ height: 300 }}>
                    <Doughnut 
                      data={createMacroChart()!} 
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                          },
                          tooltip: {
                            callbacks: {
                              label: function(context) {
                                let label = context.label || '';
                                if (label) {
                                  label += ': ';
                                }
                                if (context.parsed !== null) {
                                  label += context.parsed.toFixed(1) + 'g'; // Display actual value
                                }
                                return label;
                              },
                              afterLabel: function(context) {
                                const total = context.dataset.data.reduce((sum: number, value: number) => sum + value, 0);
                                const value = context.parsed;
                                const percentage = total > 0 ? (value / total * 100) : 0;
                                return `(${percentage.toFixed(1)}%)`; // Display percentage
                              }
                            }
                          }
                        },
                      }}
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* AI Recommendations */}
          <Grid item xs={12} md={6}>
            <Card sx={{ 
              height: 400,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', color: 'white' }}>
                  <AIIcon sx={{ mr: 1 }} />
                  AI Recommendations
                </Typography>
                <List>
                  {dashboardData?.recommendations?.slice(0, 4).map((rec: any, index: number) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon sx={{ color: 'white' }}>
                        {getPriorityIcon(rec.priority)}
                      </ListItemIcon>
                      <ListItemText
                        primary={rec.message}
                        secondary={`Priority: ${rec.priority}`}
                        sx={{ 
                          '& .MuiListItemText-primary': { color: 'white' },
                          '& .MuiListItemText-secondary': { color: 'rgba(255,255,255,0.8)' }
                        }}
                      />
                    </ListItem>
                  )) || (
                    <ListItem>
                      <ListItemText 
                        primary="No recommendations available. Keep logging your meals!" 
                        sx={{ '& .MuiListItemText-primary': { color: 'white' } }}
                      />
                    </ListItem>
                  )}
                </List>
                <CardActions>
                  <Button 
                    variant="contained" 
                    startIcon={<CoachIcon />}
                    onClick={() => setShowAICoachDialog(true)}
                    fullWidth
                    sx={{ 
                      bgcolor: 'rgba(255,255,255,0.2)', 
                      color: 'white',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
                    }}
                  >
                    Ask AI Coach
                  </Button>
                </CardActions>
              </CardContent>
            </Card>
          </Grid>

          {/* Today's Meal Plan */}
          <Grid item xs={12}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <PlanIcon sx={{ mr: 1 }} />
                  Today's Personalized Meal Plan
                  {todaysMealPlan?.is_adaptive && (
                    <Chip 
                      label="AI Adapted" 
                      size="small" 
                      sx={{ ml: 1, bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                    />
                  )}
                </Typography>
                
                {(() => {
                  const planData: any = todaysMealPlan?.meal_plan || todaysMealPlan;
                  if (!planData || !planData.meals) return null;
                  return (
                    <>
                      {planData.health_conditions?.length > 0 && (
                        <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                          Customized for: {planData.health_conditions.join(', ')}
                        </Typography>
                      )}
                      
                      <Grid container spacing={2}>
                        {Object.entries(planData.meals || {}).map(([mealType, mealDesc]: [string, any]) => (
                          <Grid item xs={12} sm={6} md={3} key={mealType}>
                            <Card sx={{ bgcolor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                              <CardContent sx={{ p: 2 }}>
                                <Typography variant="subtitle2" sx={{ 
                                  fontWeight: 'bold', 
                                  textTransform: 'capitalize',
                                  color: 'white',
                                  mb: 1
                                }}>
                                  {mealType}
                                </Typography>
                                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                                  {typeof mealDesc === 'string' ? mealDesc : mealDesc?.description || 'No meal planned'}
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        ))}
                      </Grid>
                      
                      {/* Removed automatic display of extra plan "notes" to keep UI succinct */}
                    </>
                  );
                })() || (
                  <Box sx={{ textAlign: 'center', py: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Generate a detailed meal plan from the Meal-Plan section.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Actions */}
          <Grid item xs={12}>
            <Card 
              elevation={8}
              sx={{ 
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                border: '1px solid rgba(0,0,0,0.08)',
                borderRadius: 3
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ textAlign: 'center', mb: 4 }}>
                  <Typography 
                    variant="h5" 
                    component="h2"
                    gutterBottom 
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      color: '#2c3e50',
                      mb: 1
                    }}
                  >
                    <SpeedIcon sx={{ mr: 2, fontSize: 28 }} />
                    Quick Actions
                  </Typography>
                  <Typography 
                    variant="body1" 
                    color="text.secondary"
                    sx={{ fontWeight: 300 }}
                  >
                    Take action on your health journey with these essential tools
                  </Typography>
                </Box>
                
                <Grid container spacing={3} justifyContent="center">
                  <Grid item xs={12} sm={6} md={4}>
                    <Card 
                      elevation={4}
                      sx={{ 
                        height: '100%',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease-in-out',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        '&:hover': {
                          transform: 'translateY(-8px)',
                          boxShadow: '0 12px 24px rgba(102, 126, 234, 0.3)',
                        }
                      }}
                      onClick={() => setShowQuickLogDialog(true)}
                    >
                      <CardContent sx={{ p: 3, textAlign: 'center', color: 'white' }}>
                        <Box sx={{ mb: 2 }}>
                          <AddIcon sx={{ fontSize: 48, color: 'white' }} />
                        </Box>
                        <Typography 
                          variant="h6" 
                          component="h3" 
                          gutterBottom
                          sx={{ fontWeight: 'bold', mb: 1 }}
                        >
                          LOG FOOD
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: 'rgba(255,255,255,0.9)',
                            lineHeight: 1.4,
                            fontSize: '0.9rem'
                          }}
                        >
                          Quickly record what you've eaten with AI-powered nutrition analysis
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={4}>
                    <Card 
                      elevation={4}
                      sx={{ 
                        height: '100%',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease-in-out',
                        background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                        '&:hover': {
                          transform: 'translateY(-8px)',
                          boxShadow: '0 12px 24px rgba(17, 153, 142, 0.3)',
                        }
                      }}
                      onClick={() => navigate('/chat')}
                    >
                      <CardContent sx={{ p: 3, textAlign: 'center', color: 'white' }}>
                        <Box sx={{ mb: 2 }}>
                          <ChatIcon sx={{ fontSize: 48, color: 'white' }} />
                        </Box>
                        <Typography 
                          variant="h6" 
                          component="h3" 
                          gutterBottom
                          sx={{ fontWeight: 'bold', mb: 1 }}
                        >
                          CHAT WITH AI
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: 'rgba(255,255,255,0.9)',
                            lineHeight: 1.4,
                            fontSize: '0.9rem'
                          }}
                        >
                          Get personalized health advice from your AI nutrition coach
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={4}>
                    <Card 
                      elevation={4}
                      sx={{ 
                        height: '100%',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease-in-out',
                        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        '&:hover': {
                          transform: 'translateY(-8px)',
                          boxShadow: '0 12px 24px rgba(240, 147, 251, 0.3)',
                        }
                      }}
                      onClick={() => navigate('/consumption-history')}
                    >
                      <CardContent sx={{ p: 3, textAlign: 'center', color: 'white' }}>
                        <Box sx={{ mb: 2 }}>
                          <HistoryIcon sx={{ fontSize: 48, color: 'white' }} />
                        </Box>
                        <Typography 
                          variant="h6" 
                          component="h3" 
                          gutterBottom
                          sx={{ fontWeight: 'bold', mb: 1 }}
                        >
                          VIEW HISTORY
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: 'rgba(255,255,255,0.9)',
                            lineHeight: 1.4,
                            fontSize: '0.9rem'
                          }}
                        >
                          Track your progress and review your nutrition journey
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CustomTabPanel>

      {/* Analytics Tab */}
      <CustomTabPanel value={tabValue} index={1}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" component="h2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <AnalyticsIcon sx={{ mr: 1 }} />
            Consumption Trends & Analysis
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
            Visualize your dietary intake over different periods to identify patterns and progress.
          </Typography>
          <ToggleButtonGroup
            value={selectedTimeRange}
            exclusive
            onChange={(e, newTimeRange) => newTimeRange && fetchConsumptionAnalytics(newTimeRange)}
            aria-label="time range selection"
            size="small"
            color="primary"
            sx={{ mb: 2 }}
          >
            <ToggleButton value="daily">Daily</ToggleButton>
            <ToggleButton value="weekly">Weekly</ToggleButton>
            <ToggleButton value="bi-weekly">Bi-Weekly</ToggleButton>
            <ToggleButton value="monthly">Monthly</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <CircularProgress />
            <Typography variant="h6" sx={{ ml: 2 }}>Loading analytics...</Typography>
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : consumptionAnalytics ? (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderChart('calories')}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderChart('protein')}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderChart('carbohydrates')}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderChart('fat')}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderChart('fiber')}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderChart('sugar')}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderChart('sodium')}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <Alert severity="info">No consumption data available for the selected period.</Alert>
        )}
      </CustomTabPanel>

      {/* AI Insights Tab */}
      <CustomTabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', color: 'white' }}>
                  <CoachIcon sx={{ mr: 1 }} />
                  AI Health Coach
                </Typography>
                <Typography variant="body2" sx={{ mb: 2, color: 'rgba(255,255,255,0.9)' }}>
                  Ask your AI coach anything about your diabetes management, nutrition, or meal planning.
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder="Ask me about your nutrition, meal suggestions, or health goals..."
                  value={aiCoachQuery}
                  onChange={(e) => setAICoachQuery(e.target.value)}
                  sx={{ 
                    mb: 2,
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.1)',
                      color: 'white',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                      '&.Mui-focused fieldset': { borderColor: 'white' }
                    },
                    '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.7)' }
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (!aiCoachLoading && aiCoachQuery.trim()) {
                        handleAICoachQuery();
                      }
                    }
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleAICoachQuery}
                  disabled={aiCoachLoading || !aiCoachQuery.trim()}
                  startIcon={aiCoachLoading ? <CircularProgress size={20} /> : <CoachIcon />}
                  fullWidth
                  sx={{ 
                    bgcolor: 'rgba(255,255,255,0.2)', 
                    color: 'white',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                    '&:disabled': { bgcolor: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.5)' }
                  }}
                >
                  {aiCoachLoading ? 'Thinking...' : 'Ask AI Coach'}
                </Button>
                {aiCoachResponse && (
                  <Paper sx={{ p: 2, mt: 2, bgcolor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', color: 'white' }}>
                      {aiCoachResponse}
                    </Typography>
                    <Button 
                      size="small" 
                      onClick={() => setAICoachResponse('')}
                      sx={{ 
                        mt: 1, 
                        color: 'white', 
                        borderColor: 'rgba(255,255,255,0.3)',
                        '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' }
                      }}
                      variant="outlined"
                    >
                      Clear Response
                    </Button>
                  </Paper>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <PlanIcon sx={{ mr: 1 }} />
                  Adaptive Meal Planning
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create a personalized meal plan based on your eating history and preferences.
                </Typography>
                <Button
                  variant="contained"
                  onClick={handleCreateAdaptivePlan}
                  disabled={adaptivePlanLoading}
                  startIcon={adaptivePlanLoading ? <CircularProgress size={20} /> : <PlanIcon />}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  {adaptivePlanLoading ? 'Creating Plan...' : 'Create Adaptive Plan'}
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

          {/* Today's Insights */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <LightbulbIcon sx={{ mr: 1 }} />
                  Today's AI Insights
                </Typography>
                <Grid container spacing={2}>
                  {dashboardData?.insights?.map((insight: any, index: number) => (
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
                        No insights available yet. Keep logging your meals to get personalized insights!
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CustomTabPanel>

      {/* Notifications Tab */}
      <CustomTabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <NotificationIcon sx={{ mr: 1 }} />
                  Your Notifications
                </Typography>
                {notifications.length > 0 ? (
                  <List>
                    {notifications.map((notification: any, index: number) => (
                      <React.Fragment key={index}>
                        <ListItem>
                          <ListItemIcon>
                            <Chip 
                              label={notification.priority} 
                              color={getPriorityColor(notification.priority)}
                              size="small"
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={notification.message}
                            secondary={new Date(notification.timestamp).toLocaleString()}
                          />
                        </ListItem>
                        {index < notifications.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No notifications at the moment. You're doing great! 🎉
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CustomTabPanel>

      {/* Quick Log Dialog */}
      <Dialog open={showQuickLogDialog} onClose={() => setShowQuickLogDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <AddIcon sx={{ mr: 1 }} />
          Quick Log Food
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="What did you eat?"
            placeholder="e.g., Grilled chicken salad with olive oil dressing"
            fullWidth
            variant="outlined"
            value={quickLogFood}
            onChange={(e) => setQuickLogFood(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleQuickLogFood()}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Our AI will analyze the nutrition and diabetes suitability automatically.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowQuickLogDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleQuickLogFood} 
            variant="contained"
            disabled={!quickLogFood.trim()}
          >
            Log Food
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Coach Dialog */}
      <Dialog open={showAICoachDialog} onClose={() => setShowAICoachDialog(false)} maxWidth="md" fullWidth>
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
            value={aiCoachQuery}
            onChange={(e) => setAICoachQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!aiCoachLoading && aiCoachQuery.trim()) {
                  handleAICoachQuery();
                }
              }
            }}
          />
          {aiCoachResponse && (
            <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {aiCoachResponse}
              </Typography>
              <Button 
                size="small" 
                onClick={() => setAICoachResponse('')}
                sx={{ mt: 1 }}
              >
                Clear Response
              </Button>
            </Paper>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setShowAICoachDialog(false);
            setAICoachResponse('');
            setAICoachQuery('');
          }}>Close</Button>
          <Button 
            onClick={handleAICoachQuery} 
            variant="contained"
            disabled={aiCoachLoading || !aiCoachQuery.trim()}
            startIcon={aiCoachLoading ? <CircularProgress size={20} /> : <CoachIcon />}
          >
            {aiCoachLoading ? 'Thinking...' : 'Ask'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default HomePage; 