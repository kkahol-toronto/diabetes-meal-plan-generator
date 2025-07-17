import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  Avatar,
  IconButton,
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
  Close as CloseIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  BarChart as BarChartIcon,
  ShowChart as ShowChartIcon,
  PieChart as PieChartIcon,
  DonutLarge as DonutLargeIcon,
  TrendingUp as AreaChartIcon,
  BubbleChart as ScatterPlotIcon,
  Assessment as CompareIcon,
} from '@mui/icons-material';
import { useApp } from '../contexts/AppContext';
import { Line, Doughnut, Radar, Bar, Pie, Scatter } from 'react-chartjs-2';
// Timezone utilities - temporarily commented out due to import issues
// import { 
//   getUserTimezone, 
//   getUserLocalDate, 
//   isToday, 
//   calculateDailyTotalsFromRecords, 
//   filterTodayRecords,
//   debugTimezone 
// } from '../utils/timezone';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  Filler,
  ScatterController,
  RadialLinearScale
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  Filler,
  ScatterController,
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
  type: 'bar' | 'line' | 'pie' | 'doughnut' | 'area' | 'scatter' | 'comparison';
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

// Profile completion calculation function
const getProfileCompletionStatus = (userProfile: any) => {
  if (!userProfile) return { percentage: 0, status: 'Not Started', color: 'default' as const };
  
  // Comprehensive profile completion checking
  const profileSections = {
    demographics: {
      fields: ['name', 'age', 'gender'],
      weight: 0.2
    },
    vitals: {
      fields: ['height', 'weight'],
      weight: 0.15
    },
    medical: {
      fields: ['medicalConditions', 'currentMedications'],
      arrayFields: true,
      weight: 0.25
    },
    dietary: {
      fields: ['dietType', 'dietaryRestrictions', 'allergies', 'foodPreferences'],
      arrayFields: true,
      weight: 0.2
    },
    lifestyle: {
      fields: ['exerciseFrequency', 'mealPrepCapability'],
      weight: 0.1
    },
    goals: {
      fields: ['primaryGoals', 'calorieTarget', 'readinessToChange'],
      arrayFields: ['primaryGoals'], // Only primaryGoals is an array
      weight: 0.1
    }
  };

  let totalScore = 0;
  let maxScore = 0;

  Object.entries(profileSections).forEach(([sectionName, section]) => {
    const sectionWeight = section.weight;
    maxScore += sectionWeight;
    
    let sectionCompletedFields = 0;
    const totalFields = section.fields.length;
    
    section.fields.forEach(field => {
      const value = userProfile[field];
      if ('arrayFields' in section && Array.isArray(section.arrayFields) && section.arrayFields.includes(field)) {
        // For array fields, check if array exists and has items
        if (Array.isArray(value) && value.length > 0) {
          sectionCompletedFields++;
        }
      } else if ('arrayFields' in section && section.arrayFields === true) {
        // For sections where all fields are arrays (old logic)
        if (Array.isArray(value) && value.length > 0) {
          sectionCompletedFields++;
        }
      } else {
        // For regular fields, check if value exists and is not empty
        if (value && value !== '' && value !== 0) {
          sectionCompletedFields++;
        }
      }
    });
    
    const sectionCompletion = totalFields > 0 ? sectionCompletedFields / totalFields : 0;
    totalScore += sectionCompletion * sectionWeight;
  });

  const percentage = Math.round((totalScore / maxScore) * 100);
  
  let status = 'Incomplete';
  let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'error';
  
  if (percentage === 100) {
    status = 'Complete';
    color = 'success';
  } else if (percentage >= 80) {
    status = 'Nearly Complete';
    color = 'info';
  } else if (percentage >= 50) {
    status = 'In Progress';
    color = 'warning';
  } else if (percentage > 0) {
    status = 'Started';
    color = 'warning';
  }
  
  return { percentage, status, color };
};

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { showNotification, setLoading, state } = useApp();
  const [loading, setLocalLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [progressData, setProgressData] = useState<any>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [todaysMealPlan, setTodaysMealPlan] = useState<any>(null);
  const [hasGeneratedMealPlans, setHasGeneratedMealPlans] = useState<boolean>(false);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [showProfileAlert, setShowProfileAlert] = useState(false);
  const [showQuickLogDialog, setShowQuickLogDialog] = useState(false);
  const [quickLogFood, setQuickLogFood] = useState('');
  const [quickLogMealType, setQuickLogMealType] = useState('');
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
  const [consumptionHistory, setConsumptionHistory] = useState<any[]>([]);
  
  // Adaptive Plan Dialog state
  const [showAdaptivePlanDialog, setShowAdaptivePlanDialog] = useState(false);
  const [adaptivePlanDays, setAdaptivePlanDays] = useState(3);
  
  // Analytics chart state
  const [analyticsChartType, setAnalyticsChartType] = useState<'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter' | 'comparison'>('line');
  
  // Carousel state
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const carouselImages = [
    '/photos/middle-eastern-cooking-meze-2025-02-12-05-24-20-utc.jpg',
    '/photos/top-view-tasty-salad-with-greens-on-dark-backgroun-2025-02-10-08-46-48-utc.jpg',
    '/photos/vegetarian-buddha-s-bowl-a-mix-of-vegetables-2024-10-18-02-08-30-utc.jpg',
    '/photos/portion-cups-of-healthy-ingredients-on-wooden-tabl-2025-04-03-08-07-00-utc.jpg'
  ];

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
      // Fetch extra consumption history (3 days) to handle timezone differences
      const [
        dailyInsightsResponse,
        analyticsResponse,
        progressResponse,
        notificationsResponse,
        mealPlanResponse,
        userProfileResponse,
        mealPlanHistoryResponse,
        consumptionHistoryResponse,
      ] = await Promise.all([
        fetch(`${config.API_URL}/coach/daily-insights`, { headers }),
        fetch(`${config.API_URL}/consumption/analytics?days=30`, { headers }), // Fetching 30 days for initial analytics
        fetch(`${config.API_URL}/consumption/progress`, { headers }),
        fetch(`${config.API_URL}/coach/notifications`, { headers }),
        fetch(`${config.API_URL}/coach/todays-meal-plan`, { headers }),
        fetch(`${config.API_URL}/user/profile`, { headers }),
        fetch(`${config.API_URL}/meal_plans`, { headers }),
        fetch(`${config.API_URL}/consumption/history?limit=100`, { headers }) // Fetch more records for timezone filtering
      ]);

      if (dailyInsightsResponse.status === 401 ||
          analyticsResponse.status === 401 ||
          progressResponse.status === 401 ||
          notificationsResponse.status === 401 ||
          mealPlanResponse.status === 401 ||
          userProfileResponse.status === 401 ||
          mealPlanHistoryResponse.status === 401 ||
          consumptionHistoryResponse.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      const [dailyData, analytics, progress, notifs, mealPlan, profileData, mealPlanHistory, consumptionHistoryData] = await Promise.all([
        dailyInsightsResponse.ok ? dailyInsightsResponse.json() : null,
        analyticsResponse.ok ? analyticsResponse.json() : null,
        progressResponse.ok ? progressResponse.json() : [],
        notificationsResponse.ok ? notificationsResponse.json() : null,
        mealPlanResponse.ok ? mealPlanResponse.json() : null,
        userProfileResponse.ok ? userProfileResponse.json() : {},
        mealPlanHistoryResponse.ok ? mealPlanHistoryResponse.json() : null,
        consumptionHistoryResponse.ok ? consumptionHistoryResponse.json() : []
      ]);

      // Store consumption history for other components that need it
      const consumptionRecords = consumptionHistoryData || [];
      setConsumptionHistory(consumptionRecords);
      
      // Use daily insights data as the single source of truth for today's totals
      // This ensures consistency with the consumption history page
      setDashboardData(dailyData);
      setAnalyticsData(analytics); // Existing analytics data, consider renaming for clarity
      setProgressData(progress);
      setNotifications(notifs);
      setTodaysMealPlan(mealPlan);
      const userProfileData = (profileData as any)?.profile || {};
      setUserProfile(userProfileData);
      
      // Check if user has generated any meal plans
      const hasMealPlans = mealPlanHistory?.meal_plans?.length > 0;
      setHasGeneratedMealPlans(hasMealPlans);
      
      // Check if profile needs completion
      const completionStatus = getProfileCompletionStatus(userProfileData);
      // Show alert if profile is incomplete (less than 80% complete)
      // This ensures users with partial profiles get prompted to complete them
      const profileAlertDismissed = localStorage.getItem('profileAlertDismissed');
      
      // Clear dismissal flag if profile is now complete (80%+)
      if (completionStatus.percentage >= 80) {
        localStorage.removeItem('profileAlertDismissed');
      }
      
      // Only show alert if user hasn't generated any meal plans yet
      const shouldShowAlert = completionStatus.percentage < 80 && !profileAlertDismissed && !hasMealPlans;
      setShowProfileAlert(shouldShowAlert);

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
      const response = await fetch(`${config.API_URL}/consumption/analytics?days=${days}`, { headers });
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
      const response = await fetch(`${config.API_URL}/consumption/analytics?days=${days}`, { headers });
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

  // Listen for food logging events and refresh data
  useEffect(() => {
    if (state.foodLoggedTrigger > 0) {
      console.log('Food logged event detected, refreshing homepage data...');
      fetchAllData();
      fetchConsumptionAnalytics(selectedTimeRange);
      fetchMacroConsumptionAnalytics(macroTimeRange);
    }
  }, [state.foodLoggedTrigger, fetchAllData, fetchConsumptionAnalytics, selectedTimeRange, fetchMacroConsumptionAnalytics, macroTimeRange]);

  // Carousel auto-cycling effect
  useEffect(() => {
    const carouselInterval = setInterval(() => {
      setCurrentImageIndex((prevIndex) => 
        (prevIndex + 1) % carouselImages.length
      );
    }, 3000); // Change image every 3 seconds

    return () => clearInterval(carouselInterval);
  }, [carouselImages.length]);

  const handleQuickLogFood = async () => {
    if (!quickLogFood.trim()) return;
    
    // Auto-determine meal type based on current time if not explicitly selected
    const determineMealType = () => {
      if (quickLogMealType) return quickLogMealType;
      
      const hour = new Date().getHours();
      if (hour >= 5 && hour < 11) return 'breakfast';
      if (hour >= 11 && hour < 16) return 'lunch';
      if (hour >= 16 && hour < 22) return 'dinner';
      return 'snack';
    };

    const mealType = determineMealType();
    
    try {
      setLoading(true, 'Analyzing and logging food...');
      
      const response = await fetch(`${config.API_URL}/coach/quick-log`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          food_name: quickLogFood, 
          portion: 'medium portion',
          meal_type: mealType
        }),
      });

      if (response.ok) {
        const result = await response.json();
        showNotification(`✅ Successfully logged: ${quickLogFood} (${mealType})`, 'success');
        
        // Show meal plan update notification if the meal plan was updated
        if (result.meal_plan_updated && result.remaining_calories !== undefined) {
          showNotification(
            `🍽️ Your meal plan has been updated! You have ${result.remaining_calories} calories remaining for today.`,
            'info'
          );
        }
        
        setQuickLogFood('');
        setQuickLogMealType('');
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
    try {
      setAdaptivePlanLoading(true);
      setLoading(true, 'Creating your personalized meal plan...');
      
      // SAFEGUARD: Preserve deleted meal plan IDs before creating adaptive plan
      const deletedMealPlanIds = localStorage.getItem('deleted_meal_plan_ids');
      console.log('Preserving deleted meal plan IDs before adaptive plan creation:', deletedMealPlanIds);
      
      // Prepare profile data for meal plan generation
      const profileData = {
        dietary_restrictions: userProfile?.dietaryRestrictions || [],
        food_allergies: userProfile?.foodAllergies || [],
        foods_to_avoid: userProfile?.foodsToAvoid || [],
        strong_dislikes: userProfile?.strongDislikes || [],
        diet_type: userProfile?.dietType || [],
        health_conditions: userProfile?.healthConditions || [],
        activity_level: userProfile?.activityLevel || 'moderate',
        age: userProfile?.age || 30,
        gender: userProfile?.gender || 'other',
        height: userProfile?.height || 170,
        weight: userProfile?.weight || 70,
        diabetes_type: userProfile?.diabetesType || 'type2',
        medication: userProfile?.medication || [],
        meal_preferences: userProfile?.mealPreferences || {},
        cuisine_preferences: userProfile?.cuisinePreferences || [],
        cooking_time: userProfile?.cookingTime || 'medium',
        budget: userProfile?.budget || 'moderate'
      };
      
      const response = await fetch(`${config.API_URL}/coach/adaptive-meal-plan`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          days: adaptivePlanDays,
          profile_data: profileData
        }),
      });

      if (response.ok) {
        await response.json();
        
        // SAFEGUARD: Restore deleted meal plan IDs after adaptive plan creation
        if (deletedMealPlanIds) {
          try {
            const currentDeletedIds = localStorage.getItem('deleted_meal_plan_ids');
            if (currentDeletedIds !== deletedMealPlanIds) {
              console.log('Detected change in deleted meal plan IDs, restoring original ones...');
              localStorage.setItem('deleted_meal_plan_ids', deletedMealPlanIds);
            }
          } catch (error) {
            console.error('Failed to restore deleted meal plan IDs:', error);
          }
        }
        
        showNotification('🎉 Your adaptive meal plan has been created using your complete profile!', 'success');
        navigate('/meal_plans');
        setShowAdaptivePlanDialog(false);
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

  const handleOpenAdaptivePlanDialog = () => {
    setShowAdaptivePlanDialog(true);
    // Reset to default days
    setAdaptivePlanDays(3);
  };

  const handleGenerateRecipes = async () => {
    try {
      setLoading(true, 'Generating recipes from your meal plan...');
      
      // Check if user has a meal plan
      if (!todaysMealPlan && !hasGeneratedMealPlans) {
        showNotification('Please create a meal plan first to generate recipes.', 'warning');
        navigate('/meal-plan-request');
        return;
      }

      // Get the latest meal plan to generate recipes from
      const latestMealPlan = todaysMealPlan || {
        breakfast: ['Oatmeal with berries', 'Greek yogurt with nuts'],
        lunch: ['Grilled chicken salad', 'Quinoa bowl with vegetables'],
        dinner: ['Baked salmon with vegetables', 'Turkey stir-fry with brown rice'],
        snacks: ['Apple with almond butter', 'Mixed nuts']
      };

      const response = await fetch(`${config.API_URL}/generate-recipes`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ meal_plan: latestMealPlan }),
      });

      if (response.ok) {
        showNotification('🍳 Recipes generated successfully!', 'success');
        navigate('/my-recipes');
      } else {
        throw new Error('Failed to generate recipes');
      }
    } catch (err) {
      showNotification('Failed to generate recipes. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateShoppingList = async () => {
    try {
      setLoading(true, 'Creating your shopping list...');
      
      // Check if user has a meal plan
      if (!todaysMealPlan && !hasGeneratedMealPlans) {
        showNotification('Please create a meal plan first to generate a shopping list.', 'warning');
        navigate('/meal-plan-request');
        return;
      }

      // Get the latest meal plan to generate shopping list from
      const latestMealPlan = todaysMealPlan || {
        breakfast: ['Oatmeal with berries', 'Greek yogurt with nuts'],
        lunch: ['Grilled chicken salad', 'Quinoa bowl with vegetables'],
        dinner: ['Baked salmon with vegetables', 'Turkey stir-fry with brown rice'],
        snacks: ['Apple with almond butter', 'Mixed nuts']
      };

      const response = await fetch(`${config.API_URL}/generate-shopping-list`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ meal_plan: latestMealPlan }),
      });

      if (response.ok) {
        showNotification('🛒 Shopping list created successfully!', 'success');
        navigate('/my-shopping-lists');
      } else {
        throw new Error('Failed to generate shopping list');
      }
    } catch (err) {
      showNotification('Failed to create shopping list. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleInsightAction = async (action: string, category: string) => {
    try {
      setLoading(true, `Processing ${action}...`);
      
      switch (action) {
        case 'View Details':
          // Navigate to detailed analytics
          navigate('/consumption-history');
          break;
          
        case 'Keep Going':
          // Encourage the user and show progress
          showNotification(`Great job on your ${category}! Keep up the excellent work! 🎉`, 'success');
          break;
          
        case 'Get Recommendations':
          // Get AI recommendations for this category
          const response = await fetch(`${config.API_URL}/coach/recommendations`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ category, context: 'detailed_recommendations' }),
          });

          if (response.ok) {
            const result = await response.json();
            showNotification(`💡 AI Recommendation: ${result.recommendation || 'Keep following your current plan - you\'re doing great!'}`, 'info');
          } else {
            showNotification('Here\'s a tip: Focus on consistent meal timing and portion control for better diabetes management.', 'info');
          }
          break;
          
        default:
          showNotification('Feature coming soon!', 'info');
      }
    } catch (err) {
      showNotification('Unable to process request. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAICoachQuery = async () => {
    if (!aiCoachQuery.trim()) return;
    
    try {
      setAICoachLoading(true);
      setAICoachResponse(''); // Clear previous response
      
      const response = await fetch(`${config.API_URL}/coach/meal-suggestion`, {
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
  const generateChartData = (metric: keyof NutritionalInfo): any => {
    if (!consumptionAnalytics?.daily_nutrition_history) return null;

    const data = consumptionAnalytics.daily_nutrition_history;
    
    if (!data || data.length === 0) return null;

    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const color = chartConfig?.color || '#45B7D1';

        // Handle special chart types first (scatter and comparison work with all time ranges)
    if (analyticsChartType === 'scatter') {
      const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      const scatterData = sortedData.map(day => ({
        x: day.calories || 0,
        y: (day as any)[metric] || 0
      })).filter(point => point.x > 0 || point.y > 0); // Filter out zero values for better visualization

      if (scatterData.length === 0) return null;

      return {
        datasets: [{
          label: `${chartConfig?.title || metric} vs Calories`,
          data: scatterData,
          backgroundColor: color,
          borderColor: color,
          borderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          showLine: false
        }]
      };
    }

    if (analyticsChartType === 'comparison') {
      const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      
      // For daily view, use meal-based labels, otherwise use dates
      const labels = selectedTimeRange === 'daily' ? 
        ['Breakfast', 'Lunch', 'Dinner', 'Snack'] : 
        sortedData.map(day => formatDate(day.date));
      
      let values: number[];
      
      if (selectedTimeRange === 'daily') {
        // Use meal distribution for daily view
        const mealDistribution = consumptionAnalytics.meal_distribution || {};
        const totalMeals = Object.values(mealDistribution).reduce((a: number, b: unknown) => a + (b as number), 0);
        const todayData = data.length > 0 ? data[data.length - 1] : null;
        const todayTotal = todayData ? (todayData as any)[metric] || 0 : 0;
        
        if (totalMeals === 0) return null;
        
        values = ['breakfast', 'lunch', 'dinner', 'snack'].map(mealType => {
          const mealCount = (mealDistribution as any)[mealType] || 0;
          const proportion = mealCount / totalMeals;
          return todayTotal * proportion;
        });
      } else {
        values = sortedData.map(day => (day as any)[metric] || 0);
      }
      
      if (labels.length === 0) return null;
      
      // Calculate target values based on typical recommendations
      const getTargetValue = (metric: keyof NutritionalInfo) => {
        switch (metric) {
          case 'calories': return selectedTimeRange === 'daily' ? 500 : 2000; // 500 per meal for daily
          case 'protein': return selectedTimeRange === 'daily' ? 25 : 150; // 25g per meal for daily
          case 'carbohydrates': return selectedTimeRange === 'daily' ? 45 : 250; // 45g per meal for daily
          case 'fat': return selectedTimeRange === 'daily' ? 15 : 65; // 15g per meal for daily
          case 'fiber': return selectedTimeRange === 'daily' ? 6 : 25; // 6g per meal for daily
          case 'sugar': return selectedTimeRange === 'daily' ? 10 : 50; // 10g per meal for daily
          case 'sodium': return selectedTimeRange === 'daily' ? 575 : 2300; // 575mg per meal for daily
          default: return selectedTimeRange === 'daily' ? 25 : 100;
        }
      };

      const targetValue = getTargetValue(metric);
      const targetValues = Array(labels.length).fill(targetValue);

      return {
        labels,
        datasets: [{
          label: `Actual ${chartConfig?.title || metric}`,
          data: values,
          backgroundColor: `${color}80`,
          borderColor: color,
          borderWidth: 2,
          fill: false,
          tension: 0.4,
          pointBackgroundColor: color,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }, {
          label: `Target ${chartConfig?.title || metric}`,
          data: targetValues,
          backgroundColor: 'transparent',
          borderColor: '#FF6B6B',
          borderWidth: 2,
          borderDash: [5, 5],
          fill: false,
          tension: 0,
          pointRadius: 0,
          pointHoverRadius: 0
        }]
      };
    }

    // For daily view, show meal types instead of dates (for regular charts)
    if (selectedTimeRange === 'daily') {
      if (analyticsChartType === 'pie' || analyticsChartType === 'doughnut') {
        // For pie charts, show distribution across meal types
        const mealDistribution = consumptionAnalytics.meal_distribution || {};
        const labels = Object.keys(mealDistribution);
        const values = Object.values(mealDistribution);
        
        if (labels.length === 0) return null;

        return {
          labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
          datasets: [{
            data: values,
            backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'],
            borderWidth: 2,
            borderColor: '#fff',
            hoverOffset: 4
          }]
        };
      }

      // For daily view, show meal types on x-axis
      const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'];
      const mealLabels = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];
      const mealColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'];
      
      // Get today's data or most recent day's data
      const todayData = data.length > 0 ? data[data.length - 1] : null;
      
      if (!todayData) return null;

      // For daily view, we need to fetch meal-level data
      // Since we don't have meal-level breakdown in the current data structure,
      // we'll use the meal distribution to estimate values
      const mealDistribution = consumptionAnalytics.meal_distribution || {};
      const totalMeals = Object.values(mealDistribution).reduce((a: number, b: unknown) => a + (b as number), 0);
      
      if (totalMeals === 0) return null;

      const todayTotal = (todayData as any)[metric] || 0;
      const values = mealTypes.map(mealType => {
        const mealCount = (mealDistribution as any)[mealType] || 0;
        const proportion = mealCount / totalMeals;
        return todayTotal * proportion;
      });

      return {
        labels: mealLabels,
        datasets: [{
          label: `${chartConfig?.title || metric} by Meal`,
          data: values,
          backgroundColor: analyticsChartType === 'line' ? 'rgba(0,0,0,0.05)' : 
                           analyticsChartType === 'area' ? mealColors.map(c => `${c}30`) : mealColors,
          borderColor: analyticsChartType === 'line' ? color : mealColors,
          borderWidth: 2,
          fill: analyticsChartType === 'area',
          tension: 0.4,
          pointBackgroundColor: analyticsChartType === 'line' ? color : mealColors,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      };
    }

    // For non-daily views, continue with date-based charts
    if (analyticsChartType === 'pie' || analyticsChartType === 'doughnut') {
      // For pie charts, show distribution across meal types
      const mealDistribution = consumptionAnalytics.meal_distribution || {};
      const labels = Object.keys(mealDistribution);
      const values = Object.values(mealDistribution);
      
      if (labels.length === 0) return null;

      return {
        labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
        datasets: [{
          data: values,
          backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'],
          borderWidth: 2,
          borderColor: '#fff',
          hoverOffset: 4
        }]
      };
    }



    // For line, bar, and area charts, sort data by date and show time series
    const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    const labels = sortedData.map(day => formatDate(day.date));
    const values = sortedData.map(day => (day as any)[metric] || 0);

    if (labels.length === 0) return null;

    // For better visualization, if we have only one data point, create a couple more with the same value
    if (labels.length === 1) {
      const singleValue = values[0];
      const singleLabel = labels[0];
      const baseDate = new Date(sortedData[0].date);
      
      // Create previous and next day entries with same value for better line visualization
      const prevDate = new Date(baseDate);
      prevDate.setDate(baseDate.getDate() - 1);
      const nextDate = new Date(baseDate);
      nextDate.setDate(baseDate.getDate() + 1);
      
      labels.unshift(formatDate(prevDate.toISOString()));
      labels.push(formatDate(nextDate.toISOString()));
      values.unshift(singleValue);
      values.push(singleValue);
    }

    return {
      labels,
      datasets: [{
        label: chartConfig?.title || metric,
        data: values,
        backgroundColor: analyticsChartType === 'line' ? 'rgba(0,0,0,0.05)' : 
                         analyticsChartType === 'area' ? `${color}30` : color,
        borderColor: color,
        borderWidth: 2,
        fill: analyticsChartType === 'area',
        tension: 0.4,
        pointBackgroundColor: color,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    };
  };

  const getChartOptions = (metric: keyof NutritionalInfo) => {
    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const selectedTimeRangeLabel = selectedTimeRange.charAt(0).toUpperCase() + selectedTimeRange.slice(1);
    
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index' as const,
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            usePointStyle: true,
            padding: 20,
            font: {
              size: 12
            }
          }
        },
        title: {
          display: true,
          text: `${chartConfig?.title || metric} - ${selectedTimeRangeLabel} Analysis`,
          font: {
            size: 16,
            weight: 'bold' as const
          },
          padding: 20
        },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: chartConfig?.color || '#45B7D1',
          borderWidth: 1,
          cornerRadius: 6,
          displayColors: true,
          callbacks: {
            label: function(context: any) {
              const label = context.dataset.label || '';
              
              // Special handling for scatter plots
              if (analyticsChartType === 'scatter') {
                const unit = metric === 'calories' ? 'kcal' : 
                            metric === 'sodium' ? 'mg' : 'g';
                const xValue = context.parsed.x || 0;
                const yValue = context.parsed.y || 0;
                const numXValue = typeof xValue === 'number' ? xValue : 0;
                const numYValue = typeof yValue === 'number' ? yValue : 0;
                return `${label}: ${numXValue.toFixed(1)} kcal → ${numYValue.toFixed(1)} ${unit}`;
              }
              
              // Regular charts
              const value = context.parsed.y || context.parsed || 0;
              const numValue = typeof value === 'number' ? value : 0;
              const unit = metric === 'calories' ? 'kcal' : 
                          metric === 'sodium' ? 'mg' : 'g';
              return `${label}: ${numValue.toFixed(1)} ${unit}`;
            }
          }
        }
      }
    };

    // Add scales only for bar and line charts
    if (analyticsChartType !== 'pie' && analyticsChartType !== 'doughnut') {
      const unit = metric === 'calories' ? 'kcal' : 
                   metric === 'sodium' ? 'mg' : 'g';
      
      // Special handling for scatter plots
      if (analyticsChartType === 'scatter') {
        return {
          ...baseOptions,
          scales: {
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0,0,0,0.1)',
                borderDash: [5, 5]
              },
              ticks: {
                font: {
                  size: 12
                },
                callback: function(value: any) {
                  return `${value} ${unit}`;
                }
              },
              title: {
                display: true,
                text: `${chartConfig?.title || metric} (${unit})`,
                font: {
                  size: 14,
                  weight: 'bold' as const
                }
              }
            },
            x: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0,0,0,0.1)',
                borderDash: [5, 5]
              },
              ticks: {
                font: {
                  size: 12
                },
                callback: function(value: any) {
                  return `${value} kcal`;
                }
              },
              title: {
                display: true,
                text: 'Calories (kcal)',
                font: {
                  size: 14,
                  weight: 'bold' as const
                }
              }
            }
          }
        };
      }
      
      // Regular time series charts
      return {
        ...baseOptions,
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0,0,0,0.1)',
              borderDash: [5, 5]
            },
            ticks: {
              font: {
                size: 12
              },
              callback: function(value: any) {
                return `${value} ${unit}`;
              }
            },
            title: {
              display: true,
              text: `${chartConfig?.title || metric} (${unit})`,
              font: {
                size: 14,
                weight: 'bold' as const
              }
            }
          },
          x: {
            grid: {
              color: 'rgba(0,0,0,0.1)',
              borderDash: [5, 5]
            },
            ticks: {
              font: {
                size: 12
              },
              maxRotation: 45,
              minRotation: 0
            },
            title: {
              display: true,
              text: 'Time Period',
              font: {
                size: 14,
                weight: 'bold' as const
              }
            }
          }
        }
      };
    }

    return baseOptions;
  };

  const renderChart = (metric: keyof NutritionalInfo) => {
    const data = generateChartData(metric);
    if (!data) return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <Typography variant="body1" color="text.secondary">No data available</Typography>
      </Box>
    );

    const options = getChartOptions(metric);
    
    // Create a unique key to force chart re-rendering when chart type changes
    const chartKey = `${selectedTimeRange}-${analyticsChartType}-${metric}`;

    return (
      <Box sx={{ height: 400, width: '100%' }}>
        {(() => {
          switch (analyticsChartType) {
            case 'bar':
              return <Bar key={chartKey} data={data} options={options} />;
            case 'line':
              return <Line key={chartKey} data={data} options={options} />;
            case 'area':
              return <Line key={chartKey} data={data} options={{
                ...options,
                elements: {
                  line: {
                    fill: true,
                    tension: 0.4
                  }
                },
                plugins: {
                  ...options.plugins,
                  filler: {
                    propagate: true
                  }
                }
              }} />;
            case 'scatter':
              return <Scatter key={chartKey} data={data} options={{
                ...options,
                elements: {
                  point: {
                    radius: 6,
                    hoverRadius: 8
                  }
                },
                plugins: {
                  ...options.plugins,
                  legend: {
                    ...options.plugins?.legend,
                    display: true
                  }
                }
              }} />;
            case 'comparison':
              return <Line key={chartKey} data={data} options={{
                ...options,
                plugins: {
                  ...options.plugins,
                  legend: {
                    ...options.plugins?.legend,
                    display: true
                  }
                }
              }} />;
            case 'pie':
              return <Pie key={chartKey} data={data} options={options} />;
            case 'doughnut':
              return <Doughnut key={chartKey} data={data} options={options} />;
            default:
              return <Line key={chartKey} data={data} options={options} />;
          }
        })()}
      </Box>
    );
  };

  // Additional chart rendering functions
  const renderNutritionalSummaryChart = () => {
    if (!consumptionAnalytics?.daily_nutrition_history) return <Typography>No data available</Typography>;
    
    const data = consumptionAnalytics.daily_nutrition_history;
    const latest = data[data.length - 1];
    
    if (!latest) return <Typography>No data available</Typography>;
    
    // Normalize values for radar chart (scale to 0-100 range)
    const normalizeValue = (value: number, maxValue: number) => {
      return Math.min((value / maxValue) * 100, 100);
    };
    
    const summaryData = {
      labels: ['Calories', 'Protein', 'Carbs', 'Fat', 'Fiber', 'Sugar', 'Sodium'],
      datasets: [{
        label: 'Daily Values (%)',
        data: [
          normalizeValue(latest.calories || 0, 2000),
          normalizeValue(latest.protein || 0, 150),
          normalizeValue(latest.carbohydrates || 0, 250),
          normalizeValue(latest.fat || 0, 70),
          normalizeValue((latest as any).fiber || 0, 25),
          normalizeValue((latest as any).sugar || 0, 50),
          normalizeValue((latest as any).sodium || 0, 2300)
        ],
        backgroundColor: 'rgba(78, 205, 196, 0.2)',
        borderColor: '#4ECDC4',
        borderWidth: 2,
        pointBackgroundColor: '#4ECDC4',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4
      }]
    };
    
    const radarKey = `radar-${selectedTimeRange}`;
    
    return <Radar 
      key={radarKey}
      data={summaryData} 
      options={{
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            grid: { color: 'rgba(0,0,0,0.1)' },
            pointLabels: { font: { size: 12 } },
            ticks: {
              callback: function(value) {
                return value + '%';
              }
            }
          }
        },
        plugins: {
          legend: { display: true, position: 'bottom' },
          title: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                const value = context.parsed.r;
                const numValue = typeof value === 'number' ? value : 0;
                return `${context.label}: ${numValue.toFixed(1)}%`;
              }
            }
          }
        }
      }} 
    />;
  };

  const renderWeeklyPatternChart = () => {
    if (!consumptionAnalytics?.daily_nutrition_history) return <Typography>No data available</Typography>;
    
    const data = consumptionAnalytics.daily_nutrition_history;
    const weeklyData = data.slice(-7);
    
    if (weeklyData.length === 0) return <Typography>No data available</Typography>;
    
    // Sort by date to ensure proper ordering
    const sortedData = [...weeklyData].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    
    const chartData = {
      labels: sortedData.map((day: any) => {
        try {
          return new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        } catch {
          return 'Invalid Date';
        }
      }),
      datasets: [{
        label: 'Calories',
        data: sortedData.map((day: any) => day.calories || 0),
        borderColor: '#FF6B6B',
        backgroundColor: 'rgba(255, 107, 107, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#FF6B6B',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4
      }, {
        label: 'Protein (g)',
        data: sortedData.map((day: any) => day.protein || 0),
        borderColor: '#4ECDC4',
        backgroundColor: 'rgba(78, 205, 196, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#4ECDC4',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4
      }]
    };
    
    const weeklyKey = `weekly-${selectedTimeRange}`;
    
    return <Line 
      key={weeklyKey}
      data={chartData} 
      options={{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
          title: { display: false },
                      tooltip: {
              mode: 'index',
              intersect: false,
              callbacks: {
                label: function(context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    const value = context.parsed.y;
                    const numValue = typeof value === 'number' ? value : 0;
                    label += numValue.toFixed(1);
                    if (context.dataset.label === 'Protein (g)') {
                      label += 'g';
                    } else if (context.dataset.label === 'Calories') {
                      label += ' kcal';
                    }
                  }
                  return label;
                }
              }
            }
        },
        scales: {
          y: { 
            beginAtZero: true,
            grid: { color: 'rgba(0,0,0,0.1)' }
          },
          x: {
            grid: { color: 'rgba(0,0,0,0.1)' }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        }
      }} 
    />;
  };

  const renderMacroDistributionChart = () => {
    if (!consumptionAnalytics?.daily_nutrition_history) return <Typography>No data available</Typography>;
    
    const data = consumptionAnalytics.daily_nutrition_history;
    const recentData = data.slice(-7);
    
    if (recentData.length === 0) return <Typography>No data available</Typography>;
    
    const avgData = recentData.reduce((acc: any, day: any) => ({
      protein: acc.protein + (day.protein || 0),
      carbs: acc.carbs + (day.carbohydrates || 0),
      fat: acc.fat + (day.fat || 0)
    }), { protein: 0, carbs: 0, fat: 0 });
    
    // Calculate averages
    const numDays = recentData.length;
    avgData.protein = avgData.protein / numDays;
    avgData.carbs = avgData.carbs / numDays;
    avgData.fat = avgData.fat / numDays;
    
    const total = avgData.protein + avgData.carbs + avgData.fat;
    if (total === 0) return <Typography>No data available</Typography>;
    
    const chartData = {
      labels: ['Protein', 'Carbohydrates', 'Fat'],
      datasets: [{
        data: [avgData.protein, avgData.carbs, avgData.fat],
        backgroundColor: ['#4ECDC4', '#45B7D1', '#FFA07A'],
        borderWidth: 2,
        borderColor: '#fff',
        hoverOffset: 4
      }]
    };
    
    const macroKey = `macro-${selectedTimeRange}`;
    
    return <Doughnut 
      key={macroKey}
      data={chartData} 
      options={{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true
            }
          },
          title: { display: false },
                      tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.label || '';
                  const value = context.parsed;
                  const numValue = typeof value === 'number' ? value : 0;
                  const percentage = total > 0 ? ((numValue / total) * 100).toFixed(1) : 0;
                  return `${label}: ${numValue.toFixed(1)}g (${percentage}%)`;
                }
              }
            }
        }
      }} 
    />;
  };

  const renderAdherenceChart = () => {
    if (!consumptionAnalytics?.adherence_stats) return <Typography>No data available</Typography>;
    
    const adherenceData = consumptionAnalytics.adherence_stats;
    
    const chartData = {
      labels: ['Diabetes Suitable', 'Calorie Goals', 'Protein Goals', 'Carb Goals'],
      datasets: [{
        label: 'Adherence %',
        data: [
          adherenceData.diabetes_suitable_percentage || 0,
          adherenceData.calorie_goal_adherence || 0,
          adherenceData.protein_goal_adherence || 0,
          adherenceData.carb_goal_adherence || 0
        ],
        backgroundColor: ['#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'],
        borderWidth: 2,
        borderColor: '#fff',
        borderRadius: 8,
        borderSkipped: false
      }]
    };
    
    const adherenceKey = `adherence-${selectedTimeRange}`;
    
    return <Bar 
      key={adherenceKey}
      data={chartData} 
      options={{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: false },
                      tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.label || '';
                  const value = context.parsed.y;
                  const numValue = typeof value === 'number' ? value : 0;
                  return `${label}: ${numValue.toFixed(1)}%`;
                }
              }
            }
        },
        scales: {
          y: { 
            beginAtZero: true,
            max: 100,
            grid: { color: 'rgba(0,0,0,0.1)' },
            ticks: {
              callback: function(value) {
                return value + '%';
              }
            }
          },
          x: {
            grid: { display: false }
          }
        }
      }} 
    />;
  };

  // Chart configurations with beautiful styling - memoized to prevent unnecessary re-renders
  const createMacroChart = useMemo(() => {
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
  }, [macroTimeRange, dashboardData?.today_totals, macroConsumptionAnalytics, theme]);

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
          label: 'Nutrition Score',
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
              labels: ['Calories', 'Protein', 'Carbs', 'Fiber', 'Nutrition Score', 'Consistency'],
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
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
            <img 
              src="/dietra_logo.png" 
              alt="Dietra Logo" 
              style={{ 
                height: '80px', 
                width: 'auto', 
                marginRight: '20px' 
              }} 
            />
            <Typography variant="h3" component="h1" sx={{ color: 'white', fontWeight: 'bold' }}>
              AI Nutrition Coach
            </Typography>
          </Box>
          
          {/* Image Carousel */}
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center' }}>
            <Box sx={{ 
              width: '600px', 
              height: '300px', 
              borderRadius: 3, 
              overflow: 'hidden',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
              position: 'relative'
            }}>
              <img
                src={carouselImages[currentImageIndex]}
                alt={`Healthy meal ${currentImageIndex + 1}`}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transition: 'opacity 0.5s ease-in-out'
                }}
              />
              {/* Carousel indicators */}
              <Box sx={{ 
                position: 'absolute', 
                bottom: 16, 
                left: '50%', 
                transform: 'translateX(-50%)',
                display: 'flex',
                gap: 1
              }}>
                {carouselImages.map((_, index) => (
                  <Box
                    key={index}
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: currentImageIndex === index ? 'white' : alpha('#fff', 0.5),
                      cursor: 'pointer',
                      transition: 'background-color 0.3s ease'
                    }}
                    onClick={() => setCurrentImageIndex(index)}
                  />
                ))}
              </Box>
            </Box>
          </Box>
          
          <Typography variant="h6" sx={{ color: 'white', mb: 3, opacity: 0.9, maxWidth: '800px', mx: 'auto', lineHeight: 1.6 }}>
            Welcome to Dietra. Dietra provides personalized meal plans and shopping lists tailored to your medical and behavioral profile. Simply snap photos of your meals, and our AI automatically analyzes nutritional intake to adapt your plan in real time. With continuous tracking and intelligent adjustments, plus an AI-powered Nutrition Coach to answer your dietary questions, Dietra makes achieving health goals effortless and smart.
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/login')}
              sx={{ 
                bgcolor: alpha('#fff', 0.2), 
                color: 'white',
                border: '1px solid white',
                '&:hover': { bgcolor: alpha('#fff', 0.3) }
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
          🤖 AI Nutrition Coach Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Your intelligent health companion • Last updated: {new Date().toLocaleTimeString()}
        </Typography>
      </Box>

      {/* Profile Completion Alert */}
      {showProfileAlert && (
        <Alert 
          severity="info" 
          sx={{ 
            mb: 3,
            background: 'linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%)',
            border: '2px solid #2196f3',
            borderRadius: 3,
            '& .MuiAlert-icon': {
              fontSize: '1.5rem',
            },
          }}
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                variant="contained" 
                size="small"
                onClick={() => navigate('/meal-plan')}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  textTransform: 'none',
                  fontWeight: 'bold',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                  }
                }}
              >
                Complete Profile 📝
              </Button>
              <Button 
                size="small" 
                onClick={() => {
                  setShowProfileAlert(false);
                  localStorage.setItem('profileAlertDismissed', 'true');
                }}
                sx={{ color: '#666' }}
              >
                Dismiss
              </Button>
            </Box>
          }
        >
          <Box>
            {userProfile && getProfileCompletionStatus(userProfile).percentage > 0 ? (
              <>
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#1976d2', mb: 1 }}>
                  🏥 Welcome! Your doctor's office has partially completed your profile
                </Typography>
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  To generate your personalized starter meal plan, please complete your full health profile by clicking the button above. 
                  Your doctor has already filled out some information to get you started.
                </Typography>
              </>
            ) : (
              <>
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#1976d2', mb: 1 }}>
                  👋 Welcome! Let's complete your health profile
                </Typography>
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  To generate your personalized starter meal plan, please complete your health profile by clicking the button above. 
                  This will help us create nutrition recommendations tailored specifically to your needs and medical conditions.
                </Typography>
              </>
            )}
            {userProfile && (
              <Typography variant="body2" sx={{ mt: 1, color: '#666', fontStyle: 'italic' }}>
                Current profile completion: {getProfileCompletionStatus(userProfile).percentage}% • 
                Status: {getProfileCompletionStatus(userProfile).status}
              </Typography>
            )}
          </Box>
        </Alert>
      )}

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
                  <Typography variant="h6">Nutrition Score</Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {getScoreEmoji(dashboardData?.diabetes_adherence || 0)} {Math.round(dashboardData?.diabetes_adherence || 0)}%
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  {dashboardData?.diabetes_adherence === 0 ? 'Start logging meals' :
                   dashboardData?.diabetes_adherence >= 80 ? 'Excellent!' : 
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
                {createMacroChart && (
                  <Box sx={{ height: 300 }}>
                    <Doughnut 
                      key={`macro-${macroTimeRange}`}
                      data={createMacroChart} 
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
                                  const value = context.parsed;
                                  const numValue = typeof value === 'number' ? value : 0;
                                  label += numValue.toFixed(1) + 'g'; // Display actual value
                                }
                                return label;
                              },
                              afterLabel: function(context) {
                                const total = context.dataset.data.reduce((sum: number, value: number) => sum + value, 0);
                                const value = context.parsed;
                                const numValue = typeof value === 'number' ? value : 0;
                                const percentage = total > 0 ? (numValue / total * 100) : 0;
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
                        {Object.entries(planData.meals || {}).map(([mealType, mealDesc]: [string, any]) => {
                          // Extract just the recipe name from the meal description
                          const extractRecipeName = (desc: string): string => {
                            if (!desc || typeof desc !== 'string') return 'No meal planned';
                            
                            // Remove "Day X:" prefix
                            let cleaned = desc.replace(/^Day\s+\d+:\s*/, '');
                            
                            // Extract recipe name before any parentheses (which contain ingredients)
                            const parenIndex = cleaned.indexOf('(');
                            if (parenIndex !== -1) {
                              cleaned = cleaned.substring(0, parenIndex).trim();
                            }
                            
                            // Remove any extra descriptive text after the recipe name
                            const patterns = [
                              /\s*\(.*?\)/g,  // Remove parentheses and content
                              /\s*\d+\s*(cups?|tbsp|tsp|oz|g|ml|cloves?|slices?|pieces?)\s.*$/i,  // Remove quantities and ingredients
                              /\s*with\s+.*$/i,  // Remove "with ..." descriptions
                              /\s*\+\s+.*$/i,    // Remove "+ ..." additions
                              /\s*-\s+.*$/i,     // Remove "- ..." descriptions
                              /\s*,\s*.*$/i,     // Remove comma-separated additions
                              /\s*served\s+with.*$/i, // Remove "served with..." descriptions
                              /\s*\(.*$/i,       // Remove unclosed parentheses
                              /\s*\bserved\b.*$/i, // Remove "served..." descriptions
                              /\s*\band\b.*$/i,    // Remove "and..." descriptions
                              /\s*\bincluding\b.*$/i, // Remove "including..." descriptions
                              /\s*\brecommended\b[\s:]*\brecommended\b[\s:]*\brecommended\b[\s:]*/gi, // Remove repeated "Recommended:" text
                              /\s*\brecommended\b[\s:]*\brecommended\b[\s:]*/gi, // Remove repeated "Recommended:" text
                              /\s*\brecommended\b[\s:]*/gi // Remove single "Recommended:" text
                            ];
                            
                            patterns.forEach(pattern => {
                              cleaned = cleaned.replace(pattern, '');
                            });
                            
                            // Clean up any remaining artifacts
                            cleaned = cleaned.trim();
                            
                            // If the cleaned name is too short or empty, try to extract from original
                            if (cleaned.length < 3) {
                              // Try to extract a reasonable recipe name
                              const words = desc.replace(/^Day\s+\d+:\s*/, '').split(/\s+/);
                              const meaningfulWords = words.filter(word => 
                                word.length > 2 && 
                                !word.match(/^\d+$/) && 
                                !word.match(/^(with|and|or|the|a|an|in|on|at|to|from|for|of|by)$/i)
                              );
                              cleaned = meaningfulWords.slice(0, 4).join(' ');
                            }
                            
                            return cleaned || 'Recipe';
                          };
                          
                          const recipeName = extractRecipeName(
                            typeof mealDesc === 'string' ? mealDesc : mealDesc?.description || ''
                          );
                          
                          return (
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
                                    {recipeName}
                                  </Typography>
                                </CardContent>
                              </Card>
                            </Grid>
                          );
                        })}
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
          
          <ToggleButtonGroup
            value={analyticsChartType}
            exclusive
            onChange={(e, newChartType) => newChartType && setAnalyticsChartType(newChartType)}
            aria-label="chart type selection"
            size="small"
            color="secondary"
            sx={{ mb: 2, ml: 2 }}
          >
            <ToggleButton value="line">
              <ShowChartIcon sx={{ mr: 1 }} />
              Line
            </ToggleButton>
            <ToggleButton value="bar">
              <BarChartIcon sx={{ mr: 1 }} />
              Bar
            </ToggleButton>
            <ToggleButton value="area">
              <AreaChartIcon sx={{ mr: 1 }} />
              Area
            </ToggleButton>
            <ToggleButton value="scatter">
              <ScatterPlotIcon sx={{ mr: 1 }} />
              Scatter
            </ToggleButton>
            <ToggleButton value="comparison">
              <CompareIcon sx={{ mr: 1 }} />
              Target
            </ToggleButton>
            <ToggleButton value="pie">
              <PieChartIcon sx={{ mr: 1 }} />
              Pie
            </ToggleButton>
            <ToggleButton value="doughnut">
              <DonutLargeIcon sx={{ mr: 1 }} />
              Doughnut
            </ToggleButton>
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
        
        {/* Additional Analysis Charts */}
        {consumptionAnalytics && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <AnalyticsIcon sx={{ mr: 1 }} />
              Advanced Nutritional Analysis
            </Typography>
            <Grid container spacing={3}>
              {/* Nutritional Summary Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Daily Nutritional Summary
                    </Typography>
                    <Box sx={{ height: 300, width: '100%' }}>
                      {renderNutritionalSummaryChart()}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Weekly Pattern Analysis */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Weekly Intake Patterns
                    </Typography>
                    <Box sx={{ height: 300, width: '100%' }}>
                      {renderWeeklyPatternChart()}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Macro Distribution Over Time */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Macro Distribution Trends
                    </Typography>
                    <Box sx={{ height: 300, width: '100%' }}>
                      {renderMacroDistributionChart()}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Adherence Score Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Adherence Score Analysis
                    </Typography>
                    <Box sx={{ height: 300, width: '100%' }}>
                      {renderAdherenceChart()}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
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
                  onClick={handleOpenAdaptivePlanDialog}
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
                  <Button onClick={handleGenerateRecipes}>Generate Recipes</Button>
                  <Button onClick={handleGenerateShoppingList}>Shopping List</Button>
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
                          <Button 
                            size="small" 
                            sx={{ mt: 1 }}
                            onClick={() => handleInsightAction(insight.action, insight.category)}
                          >
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
            onKeyPress={(e) => e.key === 'Enter' && !quickLogMealType && handleQuickLogFood()}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth variant="outlined" sx={{ mb: 1 }}>
            <InputLabel>Meal Type</InputLabel>
            <Select
              value={quickLogMealType}
              onChange={(e) => setQuickLogMealType(e.target.value)}
              label="Meal Type"
              onKeyPress={(e) => e.key === 'Enter' && handleQuickLogFood()}
            >
              <MenuItem value="">
                <em>Auto-detect from time</em>
              </MenuItem>
              <MenuItem value="breakfast">Breakfast</MenuItem>
              <MenuItem value="lunch">Lunch</MenuItem>
              <MenuItem value="dinner">Dinner</MenuItem>
              <MenuItem value="snack">Snack</MenuItem>
            </Select>
          </FormControl>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Our AI will analyze the nutrition and diabetes suitability automatically. 
            {!quickLogMealType && ' Meal type will be auto-detected based on current time.'}
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

      {/* Adaptive Plan Dialog */}
      <Dialog open={showAdaptivePlanDialog} onClose={() => setShowAdaptivePlanDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <PlanIcon sx={{ mr: 1 }} />
          Create Adaptive Meal Plan
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Number of Days"
            type="number"
            fullWidth
            value={adaptivePlanDays}
            onChange={(e) => setAdaptivePlanDays(Math.max(1, parseInt(e.target.value || '1', 10)))}
            InputProps={{ inputProps: { min: 1, max: 7 } }}
            sx={{ mb: 2 }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            We'll create a personalized {adaptivePlanDays}-day meal plan using your complete profile data including:
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" component="div">
              • Dietary restrictions and food allergies
              • Foods to avoid and strong dislikes
              • Diet type and cuisine preferences
              • Health conditions and diabetes type
              • Activity level and personal goals
              • Cooking time and budget preferences
            </Typography>
          </Box>
          <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
            Your meal plan will automatically adapt to all your preferences and restrictions!
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAdaptivePlanDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateAdaptivePlan} 
            variant="contained"
            disabled={adaptivePlanLoading}
            startIcon={adaptivePlanLoading ? <CircularProgress size={20} /> : <PlanIcon />}
          >
            {adaptivePlanLoading ? 'Creating...' : 'Create Plan'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default HomePage; 