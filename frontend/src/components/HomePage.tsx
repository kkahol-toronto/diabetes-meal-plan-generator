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
  Restaurant as RestaurantIcon,
} from '@mui/icons-material';
import PendingConsumptionDialog from './PendingConsumptionDialog';
import { useApp } from '../contexts/AppContext';
import { formatConsumptionText, getTotalNutrition, isConsumptionMatchingPlan, getMealEmoji } from '../utils/consumptionUtils';
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
  type: 'bar' | 'line' | 'pie' | 'doughnut' | 'area' | 'scatter' | 'comparison' | 'cumulative' | 'ratio' | 'distribution' | 'heatmap';
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


// Smart Daily Meal Plan Component - Rebuilt v2.0
interface SmartDailyMealPlanProps {
  dashboardData?: any;
}

const SmartDailyMealPlan: React.FC<SmartDailyMealPlanProps> = ({ dashboardData }) => {
  const [smartMealPlan, setSmartMealPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSmartMealPlan = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${config.API_URL}/coach/smart-daily-meal-plan`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch smart meal plan: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('=== SMART DAILY MEAL PLAN V2.0 ===');
      console.log('Full API response:', data);
      console.log('Smart meal plan:', data?.smart_meal_plan);
      console.log('Consumption by meal:', data?.consumption_by_meal);
      console.log('Snack handling support:', data?.personalization_factors?.snack_history_support);
      console.log('=====================================');
      setSmartMealPlan(data);
      
    } catch (err) {
      console.error('Error fetching smart meal plan:', err);
      setError('Unable to load meal plan. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSmartMealPlan();
  }, [fetchSmartMealPlan]);

  if (loading) {
    return (
      <Card sx={{ 
        background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        borderRadius: '16px',
        backdropFilter: 'blur(10px)'
      }}>
        <CardContent sx={{ p: 3, textAlign: 'center' }}>
          <CircularProgress sx={{ color: 'white' }} />
          <Typography variant="h6" sx={{ color: 'white', mt: 2 }}>
            Loading Your Smart Daily Meal Plan...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ 
        background: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        borderRadius: '16px'
      }}>
        <CardContent sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
            Smart Daily Meal Plan
          </Typography>
          <Typography sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
            {error}
          </Typography>
          <Button
            onClick={fetchSmartMealPlan}
            sx={{
              mt: 2,
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.3)'
              }
            }}
          >
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ 
      background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
      border: '1px solid rgba(255, 255, 255, 0.2)',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
      borderRadius: '16px',
      backdropFilter: 'blur(10px)'
    }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                p: 1.5,
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <RestaurantIcon sx={{ color: 'white', fontSize: '1.8rem' }} />
            </Box>
            <Box>
              <Typography 
                variant="h5" 
                sx={{ 
                  color: 'white', 
                  fontWeight: 'bold',
                  mb: 0.5
                }}
              >
                🍽️ Smart Daily Meal Plan
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '0.85rem'
                }}
              >
                Personalized • History-Adaptive • Real-time Recalibration
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Macro Progress Display - Synchronized with Homepage Dashboard */}
        <Box sx={{ mb: 3, p: 2, backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '12px' }}>
          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 2, fontWeight: 'bold' }}>
            📊 Today's Progress (Synced with Dashboard)
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                📊 Calories: {dashboardData?.today_totals?.calories || 0} / {dashboardData?.goals?.calories || 2000}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                💪 Protein: {dashboardData?.today_totals?.protein || 0}g / {dashboardData?.goals?.protein || 150}g
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                🎯 Remaining: {Math.max(0, (dashboardData?.goals?.calories || 2000) - (dashboardData?.today_totals?.calories || 0))} cal, {Math.max(0, (dashboardData?.goals?.protein || 150) - (dashboardData?.today_totals?.protein || 0))}g protein
              </Typography>
            </Grid>
          </Grid>
        </Box>

        {/* Meal Cards with Full Consumption Integration */}
        <Grid container spacing={2}>
          {(smartMealPlan?.meal_configuration?.active_meals || ['breakfast', 'lunch', 'dinner', 'snack']).map((mealType: string) => {
            const plannedMeal = smartMealPlan?.smart_meal_plan?.[mealType];
            const consumptionRecords = smartMealPlan?.consumption_by_meal?.[mealType] || [];
            const isConsumed = consumptionRecords.length > 0;
            const consumptionText = formatConsumptionText(consumptionRecords);
            const totalNutrition = getTotalNutrition(consumptionRecords);

            // Check if consumption matches the planned meal
            const isMatchingPlan = plannedMeal && isConsumed 
              ? isConsumptionMatchingPlan(plannedMeal.meal_name || '', consumptionText)
              : false;

            return (
              <Grid item xs={12} sm={6} key={mealType}>
                <Card sx={{ 
                  bgcolor: isConsumed 
                    ? (isMatchingPlan ? 'rgba(76, 175, 80, 0.2)' : 'rgba(255, 193, 7, 0.2)')
                    : 'rgba(255, 255, 255, 0.15)',
                  border: isConsumed 
                    ? (isMatchingPlan ? '2px solid rgba(76, 175, 80, 0.8)' : '2px solid rgba(255, 193, 7, 0.8)')
                    : '1px solid rgba(255, 255, 255, 0.3)',
                  height: '100%',
                  minHeight: '200px'
                }}>
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Typography 
                        variant="subtitle2" 
                        sx={{ 
                          color: 'white',
                          fontWeight: 'bold',
                          textTransform: 'capitalize',
                          flexGrow: 1,
                          fontSize: '1rem'
                        }}
                      >
                        {getMealEmoji(mealType)} {mealType}
                      </Typography>
                      {isConsumed && (
                        <Chip
                          size="small"
                          label={isMatchingPlan ? "✅ On Plan" : "⚠️ Off Plan"}
                          sx={{
                            backgroundColor: isMatchingPlan ? 'rgba(76, 175, 80, 0.8)' : 'rgba(255, 193, 7, 0.8)',
                            color: 'white',
                            fontSize: '0.7rem',
                            fontWeight: 'bold'
                          }}
                        />
                      )}
                    </Box>

                    {/* Planned Meal Section */}
                    {plannedMeal ? (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.75rem', mb: 0.5 }}>
                          🎯 PLANNED:
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'white', fontWeight: 'bold', fontSize: '0.85rem' }}>
                          {plannedMeal.meal_name || `Planned ${mealType}`}
                        </Typography>
                        {plannedMeal.description && (
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.75rem', mt: 0.5 }}>
                            {plannedMeal.description}
                          </Typography>
                        )}
                        {plannedMeal.nutritional_info && (
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.7rem', mt: 0.5 }}>
                            📊 {plannedMeal.nutritional_info.calories || 0} cal, {plannedMeal.nutritional_info.protein || 0}g protein
                          </Typography>
                        )}
                        {plannedMeal.source && (
                          <Chip
                            size="small"
                            label={plannedMeal.source === 'adapted_from_history' ? 'From History' : 'Generated'}
                            sx={{
                              backgroundColor: plannedMeal.source === 'adapted_from_history' ? 'rgba(76, 175, 80, 0.6)' : 'rgba(33, 150, 243, 0.6)',
                              color: 'white',
                              fontSize: '0.6rem',
                              mt: 0.5,
                              height: '18px'
                            }}
                          />
                        )}
                      </Box>
                    ) : (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.8rem', fontStyle: 'italic' }}>
                          🔄 No planned meal for {mealType}
                        </Typography>
                      </Box>
                    )}

                    {/* Consumption Section */}
                    {isConsumed ? (
                      <Box>
                        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.75rem', mb: 0.5 }}>
                          ✅ CONSUMED:
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'white', fontWeight: 'bold', fontSize: '0.85rem' }}>
                          {consumptionText}
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.7rem', mt: 0.5 }}>
                          📊 {totalNutrition.calories} cal, {totalNutrition.protein}g protein
                        </Typography>
                      </Box>
                    ) : (
                      <Box>
                        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '0.8rem', fontStyle: 'italic' }}>
                          ⏳ Nothing logged yet for {mealType}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>

        {/* Plan Info & Refresh */}
        <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            {smartMealPlan?.personalization_factors?.snack_history_support && (
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.8rem' }}>
                ✨ Enhanced snack history support enabled
              </Typography>
            )}
            {smartMealPlan?.recalibration_history?.length > 0 ? (
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.8rem' }}>
                🔄 Plan recalibrated {smartMealPlan.recalibration_history.length} time(s) today
              </Typography>
            ) : (
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.8rem' }}>
                ✅ No recalibrations needed
              </Typography>
            )}
          </Box>
          <Button
            onClick={fetchSmartMealPlan}
            size="small"
            sx={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              fontSize: '0.75rem',
              px: 2,
              py: 0.5,
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.3)'
              }
            }}
          >
            {loading ? <CircularProgress size={14} /> : 'REFRESH'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
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

  const [showAICoachDialog, setShowAICoachDialog] = useState(false);
  const [aiCoachQuery, setAICoachQuery] = useState('');
  const [aiCoachResponse, setAICoachResponse] = useState('');
  const [aiCoachLoading, setAICoachLoading] = useState(false);
  const [analyticsTabValue, setAnalyticsTabValue] = useState(0); // For Daily, Weekly, etc. tabs
  const [selectedTimeRange, setSelectedTimeRange] = useState<'daily' | 'weekly' | 'bi-weekly' | 'monthly'>('daily');
  const [consumptionAnalytics, setConsumptionAnalytics] = useState<any>(null);
  const [consumptionHistory, setConsumptionHistory] = useState<any[]>([]);
  const [mealAnalytics, setMealAnalytics] = useState<any>(null);
  
  // Pending consumption dialog state
  const [showPendingDialog, setShowPendingDialog] = useState(false);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [pendingAnalysis, setPendingAnalysis] = useState<any>(null);
  


  
  // Analytics chart state
  const [analyticsChartType, setAnalyticsChartType] = useState<'auto' | 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter' | 'comparison'>('auto');
  
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

  const fetchMealAnalytics = useCallback(async (timeRange: 'daily' | 'weekly' | 'bi-weekly' | 'monthly') => {
    if (!isLoggedIn) return;

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
      default: days = 1;
    }

    console.log(`Fetching meal analytics for time range: ${timeRange} (days: ${days})`);

    try {
      const response = await fetch(`${config.API_URL}/consumption/meal-analytics?days=${days}`, { headers });
      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }
      if (!response.ok) throw new Error('Failed to fetch meal analytics');
      const data = await response.json();
      setMealAnalytics(data);
      console.log('Meal analytics data:', data);
    } catch (err) {
      console.error(`Error fetching ${timeRange} meal analytics:`, err);
    }
  }, [token, isLoggedIn, navigate]);

  useEffect(() => {
    fetchAllData();
    fetchConsumptionAnalytics(selectedTimeRange); // Initial fetch for consumption analytics
    fetchMacroConsumptionAnalytics(macroTimeRange); // Initial fetch for macro analytics
    fetchMealAnalytics(selectedTimeRange); // Fix: Use selectedTimeRange for Advanced Nutritional Analysis
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchAllData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchAllData, fetchConsumptionAnalytics, selectedTimeRange, fetchMacroConsumptionAnalytics, macroTimeRange, fetchMealAnalytics]);

  // Listen for food logging events and refresh data
  useEffect(() => {
    if (state.foodLoggedTrigger > 0) {
      console.log('Food logged event detected, refreshing homepage data...');
      fetchAllData();
      fetchConsumptionAnalytics(selectedTimeRange);
      fetchMacroConsumptionAnalytics(macroTimeRange);
      fetchMealAnalytics(selectedTimeRange); // Fix: Also refresh meal analytics with correct time range
    }
  }, [state.foodLoggedTrigger, fetchAllData, fetchConsumptionAnalytics, selectedTimeRange, fetchMacroConsumptionAnalytics, macroTimeRange, fetchMealAnalytics]);

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
      setLoading(true, 'Analyzing food...');
      
      const response = await fetch(`${config.API_URL}/consumption/analyze-text-only`, {
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
        
        // Store pending data and show dialog
        setPendingId(result.pending_id);
        setPendingAnalysis(result.analysis);
        setShowPendingDialog(true);
        setShowQuickLogDialog(false);
        
      } else {
        throw new Error('Failed to analyze food');
      }
    } catch (err) {
      showNotification('Failed to analyze food. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePendingAccept = () => {
    // Close dialog and reset quick log form
    setQuickLogFood('');
    setQuickLogMealType('');
    setPendingId(null);
    setPendingAnalysis(null);
    fetchAllData(); // Refresh all data
  };

  const handlePendingDelete = () => {
    // Reset quick log form
    setQuickLogFood('');
    setQuickLogMealType('');
    setPendingId(null);
    setPendingAnalysis(null);
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

  // Enhanced chart configurations with diverse visualization types
  const chartConfigs: ChartConfig[] = [
    { type: 'line', metric: 'calories', title: 'Calories Daily Trend', color: '#FF6B6B', icon: <CaloriesIcon /> },
    { type: 'comparison', metric: 'protein', title: 'Protein vs Goal', color: '#4ECDC4', icon: <ProteinIcon /> },
    { type: 'cumulative', metric: 'carbohydrates', title: 'Carbs Throughout Day', color: '#45B7D1', icon: <CarbsIcon /> },
    { type: 'ratio', metric: 'fat', title: 'Fat vs Other Macros', color: '#FFA07A', icon: <FatIcon /> },
    { type: 'area', metric: 'fiber', title: 'Fiber Intake Pattern', color: '#98D8C8', icon: <FiberIcon /> },
    { type: 'distribution', metric: 'sugar', title: 'Sugar by Meal Type', color: '#F7DC6F', icon: <SugarIcon /> },
    { type: 'heatmap', metric: 'sodium', title: 'Sodium Intensity', color: '#BB8FCE', icon: <SodiumIcon /> }
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

  // Recommended daily values for different nutrients
  const dailyRecommendations: Record<string, number> = {
    calories: 2000,
    protein: 50,
    carbohydrates: 300,
    fat: 65,
    fiber: 25,
    sugar: 50,
    sodium: 2300
  };

  // Helper functions for diverse chart data generation
  const generateChartData = (metric: keyof NutritionalInfo): any => {
    if (!consumptionAnalytics?.daily_nutrition_history) return null;

    const data = consumptionAnalytics.daily_nutrition_history;
    
    if (!data || data.length === 0) return null;

    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const color = chartConfig?.color || '#45B7D1';
    const chartType = chartConfig?.type || 'line';

    // Handle special chart types from the chart type selector
    if (analyticsChartType === 'scatter') {
      const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      const scatterData = sortedData.map(day => ({
        x: day.calories || 0,
        y: (day as any)[metric] || 0
      })).filter(point => point.x > 0 || point.y > 0);

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

    // Generate diverse chart types based on nutrient with fallback
    let chartData = null;
    
    switch (chartType) {
      case 'cumulative':
        chartData = generateCumulativeChartData(metric, data, color);
        break;
      case 'ratio':
        chartData = generateRatioChartData(metric, data, color);
        break;
      case 'distribution':
        chartData = generateDistributionChartData(metric, data, color);
        break;
      case 'heatmap':
        chartData = generateHeatmapChartData(metric, data, color);
        break;
      case 'comparison':
      case 'area':
      default:
        // Use default chart generation for comparison, area, and other types
        chartData = generateDefaultChartData(metric, data, color);
        break;
    }
    
    // If special chart type failed, fall back to default chart
    if (!chartData || !chartData.datasets || chartData.datasets.length === 0) {
      chartData = generateDefaultChartData(metric, data, color);
    }
    
    return chartData;
  };



  // Cumulative intake throughout the day (for carbohydrates) - FIXED TO USE REAL MEAL DATA
  const generateCumulativeChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    if (!mealAnalytics?.meal_breakdown) return null;
    
    const mealBreakdown = mealAnalytics.meal_breakdown;
    const mealTimes = ['6:00 AM', '9:00 AM', '12:00 PM', '3:00 PM', '6:00 PM', '9:00 PM'];
    
    // Get actual meal values from real consumption data
    const breakfastValue = mealBreakdown.breakfast?.[metric] || 0;
    const lunchValue = mealBreakdown.lunch?.[metric] || 0;
    const dinnerValue = mealBreakdown.dinner?.[metric] || 0;
    const snackValue = mealBreakdown.snack?.[metric] || 0;
    
    // Create cumulative data based on actual consumption
    const cumulativeData = [
      0, // Start of day
      breakfastValue, // After breakfast
      breakfastValue, // Mid-morning (same as breakfast)
      breakfastValue + lunchValue, // After lunch
      breakfastValue + lunchValue, // Mid-afternoon (same as lunch total)
      breakfastValue + lunchValue + dinnerValue + snackValue // End of day total
    ];
    
    // If no data, return null
    const totalValue = cumulativeData[cumulativeData.length - 1];
    if (totalValue === 0) return null;
    
    return {
      labels: mealTimes,
      datasets: [{
        label: `${metric.charAt(0).toUpperCase() + metric.slice(1)} Cumulative (Real Data)`,
        data: cumulativeData,
        borderColor: color,
        backgroundColor: `${color}20`,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: color,
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }]
    };
  };

  // Ratio visualization (for fat vs other macros)
  const generateRatioChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    if (!data || data.length === 0) return null;
    
    const latest = data[data.length - 1];
    const fatValue = latest?.fat || 0;
    const proteinValue = latest?.protein || 0;
    const carbsValue = latest?.carbohydrates || 0;
    
    if (fatValue === 0 && proteinValue === 0 && carbsValue === 0) return null;
    
    return {
      labels: ['Fat', 'Protein', 'Carbohydrates'],
      datasets: [{
        label: 'Macronutrient Distribution',
        data: [fatValue, proteinValue, carbsValue],
        backgroundColor: [color, '#4ECDC4', '#45B7D1'],
        borderColor: ['#fff', '#fff', '#fff'],
        borderWidth: 2,
        hoverOffset: 4
      }]
    };
  };



  // Distribution by meal type (for sugar)
  const generateDistributionChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    if (!data || data.length === 0) return null;
    
    const latest = data[data.length - 1];
    const totalValue = (latest as any)[metric] || 0;
    
    if (totalValue === 0) return null;
    
    return {
      labels: ['Breakfast', 'Morning Snack', 'Lunch', 'Afternoon Snack', 'Dinner', 'Evening Snack'],
      datasets: [{
        label: `${metric.charAt(0).toUpperCase() + metric.slice(1)} Distribution`,
        data: [
          totalValue * 0.30, // Breakfast often has more sugar (fruits, cereals)
          totalValue * 0.10,
          totalValue * 0.25,
          totalValue * 0.15,
          totalValue * 0.15,
          totalValue * 0.05
        ],
        backgroundColor: [
          color + 'FF',
          color + 'CC',
          color + '99',
          color + '77',
          color + '44',
          color + '22'
        ].map(c => c.length === 7 ? c + 'FF' : c), // Ensure proper alpha format
        borderWidth: 0
      }]
    };
  };

  // Heatmap-style intensity chart (for sodium)
  const generateHeatmapChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    if (!data || data.length === 0) return null;
    
    const recentData = data.slice(-7); // Last 7 days
    if (recentData.length === 0) return null;
    
    const labels = recentData.map(day => formatDate(day.date));
    const values = recentData.map(day => (day as any)[metric] || 0);
    const maxValue = Math.max(...values);
    
    if (maxValue === 0) return null;
    
    return {
      labels,
      datasets: [{
        label: `${metric.charAt(0).toUpperCase() + metric.slice(1)} Intensity`,
        data: values,
        backgroundColor: values.map(value => {
          const intensity = maxValue > 0 ? value / maxValue : 0;
          const alpha = Math.max(0.2, intensity);
          const alphaHex = Math.round(alpha * 255).toString(16).padStart(2, '0');
          return color.length === 7 ? color + alphaHex : color;
        }),
        borderColor: color,
        borderWidth: 1
      }]
    };
  };

  // Default chart for fallback
  const generateDefaultChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    const chartConfig = chartConfigs.find(config => config.metric === metric);

    if (analyticsChartType === 'comparison') {
      const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      
      // For daily view, use meal-based labels, otherwise use dates
      const labels = selectedTimeRange === 'daily' ? 
        ['Breakfast', 'Lunch', 'Dinner', 'Snack'] : 
        sortedData.map(day => formatDate(day.date));
      
      let values: number[];
      
      if (selectedTimeRange === 'daily') {
        // Use REAL meal data instead of proportions - FIXED
        if (!mealAnalytics?.meal_breakdown) return null;
        
        const mealBreakdown = mealAnalytics.meal_breakdown;
        values = ['breakfast', 'lunch', 'dinner', 'snack'].map(mealType => {
          return mealBreakdown[mealType]?.[metric] || 0;
        });
        
        // If no real consumption data, return null instead of showing dummy data
        const totalConsumed = values.reduce((sum, val) => sum + val, 0);
        if (totalConsumed === 0) return null;
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
        // For pie charts, show real nutritional distribution across meal types - FIXED
        if (!mealAnalytics?.meal_breakdown) return null;
        
        const mealBreakdown = mealAnalytics.meal_breakdown;
        const labels = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];
        const values = labels.map(label => {
          return mealBreakdown[label.toLowerCase()]?.[metric] || 0;
        });
        
        // Check if we have any real data to show
        const totalValue = values.reduce((sum, val) => sum + val, 0);
        if (totalValue === 0) return null;

        return {
          labels,
          datasets: [{
            data: values,
            backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'],
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

      // For daily view, use real meal analytics data instead of estimates - FIXED
      if (!mealAnalytics?.meal_breakdown) {
        // Fallback: if meal analytics not available, try to use today's total data if available
        if (todayData && todayData[metric] > 0) {
          // Distribute the daily total across meals for visualization (approximate)
          const dailyTotal = todayData[metric];
          const approximateValues = [
            dailyTotal * 0.25, // breakfast
            dailyTotal * 0.35, // lunch  
            dailyTotal * 0.35, // dinner
            dailyTotal * 0.05  // snack
          ];
          
          return {
            labels: mealLabels,
            datasets: [{
              label: `${chartConfig?.title || metric} by Meal (Estimated)`,
              data: approximateValues,
              backgroundColor: analyticsChartType === 'line' ? 'rgba(0,0,0,0.05)' : 
                               analyticsChartType === 'area' ? mealColors.map(c => `${c}30`) : mealColors,
              borderColor: analyticsChartType === 'line' ? color : mealColors,
              borderWidth: 2,
              borderDash: [5, 5], // Dashed lines to indicate estimated data
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
        return null;
      }
      
      const mealBreakdown = mealAnalytics.meal_breakdown;
      const values = mealTypes.map(mealType => {
        return mealBreakdown[mealType]?.[metric] || 0;
      });
      
      // Check if we have any real data to show
      const totalConsumed = values.reduce((sum, val) => sum + val, 0);
      if (totalConsumed === 0) {
        // Show a message that no data is available rather than hiding the chart
        return {
          labels: mealLabels,
          datasets: [{
            label: `${chartConfig?.title || metric} by Meal - No Data`,
            data: [0, 0, 0, 0],
            backgroundColor: ['#f0f0f0', '#f0f0f0', '#f0f0f0', '#f0f0f0'],
            borderColor: ['#d0d0d0', '#d0d0d0', '#d0d0d0', '#d0d0d0'],
            borderWidth: 1
          }]
        };
      }

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
    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const currentValue = consumptionAnalytics?.daily_nutrition_history?.[consumptionAnalytics.daily_nutrition_history.length - 1]?.[metric] || 0;
    const dailyGoal = dailyRecommendations[metric] || 100;
    
    // Validate chart config exists
    if (!chartConfig) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
          <Typography variant="body1" color="text.secondary">Chart configuration not found</Typography>
        </Box>
      );
    }

    const data = generateChartData(metric);
    
    if (!data || !data.datasets || data.datasets.length === 0) return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <Typography variant="body1" color="text.secondary">No data available for {chartConfig.title}</Typography>
      </Box>
    );

    const options = getChartOptions(metric);
    
    // Create a unique key to force chart re-rendering when chart type changes
    const chartKey = `${selectedTimeRange}-${analyticsChartType}-${metric}`;

    // Render different chart types based on the nutrient's configured type
    const renderSpecificChart = () => {
      const specificChartType = chartConfig?.type || 'line';
      
      // Handle global chart type selector first (overrides specific types)
      if (analyticsChartType !== 'auto') {
        switch (analyticsChartType) {
          case 'bar':
            return <Bar key={chartKey} data={data} options={options} />;
          case 'line':
            return <Line key={chartKey} data={data} options={options} />;
          case 'area':
            return <Line key={chartKey} data={data} options={{
              ...options,
              elements: { line: { fill: true, tension: 0.4 } },
              plugins: { ...options.plugins, filler: { propagate: true } }
            }} />;
          case 'scatter':
            return <Scatter key={chartKey} data={data} options={{
              ...options,
              elements: { point: { radius: 6, hoverRadius: 8 } },
              plugins: { ...options.plugins, legend: { ...options.plugins?.legend, display: true } }
            }} />;
          case 'comparison':
            return <Line key={chartKey} data={data} options={{
              ...options,
              plugins: { ...options.plugins, legend: { ...options.plugins?.legend, display: true } }
            }} />;
          case 'pie':
            return <Pie key={chartKey} data={data} options={options} />;
          case 'doughnut':
            return <Doughnut key={chartKey} data={data} options={options} />;
          default:
            return <Line key={chartKey} data={data} options={options} />;
        }
      }
      
      // Use specific chart type for each nutrient
      switch (specificChartType) {
        case 'cumulative':
          return <Line key={chartKey} data={data} options={{
            ...options,
            plugins: {
              ...options.plugins,
              title: { ...options.plugins?.title, text: 'Cumulative Intake Throughout Day' }
            }
          }} />;
        case 'ratio':
          return <Pie key={chartKey} data={data} options={{
            ...options,
            plugins: {
              ...options.plugins,
              title: { ...options.plugins?.title, text: 'Macronutrient Distribution' }
            }
          }} />;
        case 'distribution':
          return <Doughnut key={chartKey} data={data} options={{
            ...options,
            plugins: {
              ...options.plugins,
              title: { ...options.plugins?.title, text: 'Distribution Across Meals' }
            }
          }} />;
        case 'heatmap':
          return <Bar key={chartKey} data={data} options={{
            ...options,
            plugins: {
              ...options.plugins,
              title: { ...options.plugins?.title, text: 'Daily Intensity Levels' }
            }
          }} />;
        case 'area':
          return <Line key={chartKey} data={data} options={{
            ...options,
            elements: { line: { fill: true, tension: 0.4 } },
            plugins: { ...options.plugins, filler: { propagate: true } }
          }} />;
        case 'comparison':
          return <Line key={chartKey} data={data} options={{
            ...options,
            plugins: { ...options.plugins, legend: { ...options.plugins?.legend, display: true } }
          }} />;
        default:
          return <Line key={chartKey} data={data} options={options} />;
      }
    };

    return (
      <Box sx={{ height: 400, width: '100%' }}>
        {renderSpecificChart()}
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
      <Container maxWidth="lg" sx={{ mt: { xs: 2, md: 4 }, mb: 4, px: { xs: 2, sm: 3 } }}>
        <Paper elevation={3} sx={{ 
          p: { xs: 3, sm: 4 }, 
          textAlign: 'center', 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: { xs: 2, sm: 3 }
        }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            mb: 2,
            flexDirection: { xs: 'column', sm: 'row' },
            gap: { xs: 1, sm: 0 }
          }}>
            <img 
              src="/dietra_logo.png" 
              alt="Dietra Logo" 
              style={{ 
                height: window.innerWidth < 600 ? '60px' : '80px', 
                width: 'auto', 
                marginRight: window.innerWidth < 600 ? '0' : '20px',
                marginBottom: window.innerWidth < 600 ? '8px' : '0'
              }} 
            />
            <Typography 
              variant="h3" 
              component="h1" 
              sx={{ 
                color: 'white', 
                fontWeight: 'bold',
                fontSize: { xs: '1.8rem', sm: '2.5rem', md: '3rem' },
                textAlign: 'center'
              }}
            >
              AI Nutrition Coach
            </Typography>
          </Box>
          
          {/* Image Carousel */}
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center', px: { xs: 0, sm: 2 } }}>
            <Box sx={{ 
              width: { xs: '100%', sm: '500px', md: '600px' }, 
              height: { xs: '200px', sm: '250px', md: '300px' }, 
              borderRadius: 3, 
              overflow: 'hidden',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
              position: 'relative',
              maxWidth: '100%'
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
                bottom: { xs: 12, sm: 16 }, 
                left: '50%', 
                transform: 'translateX(-50%)',
                display: 'flex',
                gap: 1
              }}>
                {carouselImages.map((_, index) => (
                  <Box
                    key={index}
                    sx={{
                      width: { xs: 10, sm: 12 },
                      height: { xs: 10, sm: 12 },
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
          
          <Typography 
            variant="h6" 
            sx={{ 
              color: 'white', 
              mb: 3, 
              opacity: 0.9, 
              maxWidth: { xs: '100%', sm: '700px', md: '800px' }, 
              mx: 'auto', 
              lineHeight: 1.6,
              fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
              px: { xs: 1, sm: 2 }
            }}
          >
            Welcome to Dietra. Track your nutrition instantly - no meal plan required! Simply snap photos of your meals or log food manually, and our AI automatically analyzes nutritional intake and calculates your diabetes health score. Optional personalized meal plans available. With continuous tracking and an AI-powered Nutrition Coach to answer your dietary questions, Dietra makes achieving health goals effortless and smart.
          </Typography>
          
          <Box sx={{ 
            display: 'flex', 
            gap: { xs: 2, sm: 2 }, 
            justifyContent: 'center', 
            flexWrap: 'wrap',
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: 'center',
            px: { xs: 2, sm: 0 }
          }}>
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
          Your intelligent health companion • Log food anytime, meal plans optional • Last updated: {new Date().toLocaleTimeString()}
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
                  <br/><strong>Note:</strong> You can start logging food and tracking nutrition right away - meal plans are optional!
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
                  <br/><strong>Note:</strong> You can start logging food and tracking nutrition right away - meal plans are optional!
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
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3, overflow: 'auto' }}>
        <Tabs 
          value={tabValue} 
          onChange={(e, newValue) => setTabValue(newValue)} 
          aria-label="dashboard tabs"
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              minWidth: { xs: 'auto', sm: 160 },
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              '@media (max-width: 600px)': {
                '& .MuiSvgIcon-root': {
                  fontSize: '1rem'
                }
              }
            }
          }}
        >
          <Tab 
            icon={<AnalyticsIcon />} 
            label={window.innerWidth < 600 ? "Overview" : "Overview"}
            iconPosition="start"
          />
          <Tab 
            icon={<TimelineIcon />} 
            label={window.innerWidth < 600 ? "Analytics" : "Analytics"}
            iconPosition="start"
          />
          <Tab 
            icon={<CoachIcon />} 
            label={window.innerWidth < 600 ? "AI" : "AI Insights"}
            iconPosition="start"
          />
          <Tab 
            icon={<NotificationIcon />} 
            label={window.innerWidth < 600 ? 
              `Notifs${notifications.length > 0 ? ` (${notifications.length})` : ''}` : 
              `Notifications ${notifications.length > 0 ? `(${notifications.length})` : ''}`
            }
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Overview Tab */}
      <CustomTabPanel value={tabValue} index={0}>
        <Grid container spacing={{ xs: 2, md: 3 }}>
          {/* Today's Summary Cards */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
              color: 'white',
              height: '100%',
              minHeight: { xs: '140px', sm: '160px' }
            }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 1, sm: 2 } }}>
                  <CaloriesIcon sx={{ mr: 1, fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                  <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                    Calories Today
                  </Typography>
                </Box>
                <Typography variant="h3" sx={{ 
                  fontWeight: 'bold',
                  fontSize: { xs: '1.8rem', sm: '2.5rem', md: '3rem' }
                }}>
                  {dashboardData?.today_totals?.calories || 0}
                </Typography>
                <Typography variant="body2" sx={{ 
                  opacity: 0.8,
                  fontSize: { xs: '0.75rem', sm: '0.875rem' }
                }}>
                  Goal: {dashboardData?.goals?.calories || 2000}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={Math.min(((dashboardData?.today_totals?.calories || 0) / (dashboardData?.goals?.calories || 2000)) * 100, 100)}
                  sx={{ 
                    mt: 1, 
                    bgcolor: alpha('#fff', 0.3), 
                    '& .MuiLinearProgress-bar': { bgcolor: 'white' },
                    height: { xs: 6, sm: 8 }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #4ECDC4, #44A08D)',
              color: 'white',
              height: '100%',
              minHeight: { xs: '140px', sm: '160px' }
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

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #A8EDEA, #FED6E3)',
              color: '#333',
              height: '100%',
              minHeight: { xs: '140px', sm: '160px' }
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

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              color: 'white',
              height: '100%',
              minHeight: { xs: '140px', sm: '160px' }
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
                      fetchMealAnalytics(newTimeRange); // ALSO FETCH MEAL ANALYTICS - FIXED
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

          {/* Smart Daily Meal Plan v2.0 */}
          <Grid item xs={12}>
            <SmartDailyMealPlan dashboardData={dashboardData} />
          </Grid>

          {/* Original Meal Plan (Hidden) */}
          <Grid item xs={12} sx={{ display: 'none' }}>
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
                  if (!planData || !planData.meals) {
                    return null;
                  }
                  return (
                    <>
                      {planData.health_conditions?.length > 0 && (
                        <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                          Customized for: {planData.health_conditions.join(', ')}
                        </Typography>
                      )}
                      
                      <Grid container spacing={2}>
                        {Object.entries(planData.meals || {}).map(([mealType, mealDesc]: [string, any]) => {
                          // Get consumption status from backend
                          const consumptionStatus = planData.consumption_status?.[mealType];
                          const isConsumed = consumptionStatus?.consumed || false;
                          
                          // Use structured data from consumptionStatus for consistent display
                          const getDisplayContent = (): string => {
                            if (isConsumed && consumptionStatus) {
                              // Use structured consumption data - show actual food names
                              if (consumptionStatus.total_items === 1) {
                                return `You ate: ${consumptionStatus.actual[0] || 'Consumed meal'}`;
                              } else if (consumptionStatus.total_items > 1) {
                                // For multiple items, show the actual food names joined
                                return `You ate: ${consumptionStatus.actual.join(', ') || 'Multiple items consumed'}`;
                              }
                            }
                            
                            // For planned meals, clean up the description
                            const desc = typeof mealDesc === 'string' ? mealDesc : mealDesc?.description || '';
                            if (!desc) return 'No meal planned';
                            
                            // Remove "Day X:" prefix for planned meals
                            let cleaned = desc.replace(/^Day\s+\d+:\s*/, '');
                            
                            // Validate and sanitize meal names to prevent corrupted data
                            const isSuspiciousMeal = (text: string): boolean => {
                              // Check for patterns that indicate corrupted or nonsensical meal data
                              const suspiciousPatterns = [
                                /^\d+\/\d+\s+\w+\s+fruit/i, // "1/2 Lindt fruit" pattern
                                /^[0-9]+\/[0-9]+/,         // Starts with fractions
                                /lindt/i,                   // Brand names that don't make sense as meals
                                /^[0-9]+\s+(g|ml|oz|cups?|tbsp|tsp)\s*$/i, // Just quantities
                                /^[\d\s\/\-\.]+$/,         // Only numbers and punctuation
                                /^[a-z]{1,2}$/i,           // Single letters or very short nonsense
                              ];
                              return suspiciousPatterns.some(pattern => pattern.test(text.trim()));
                            };
                            
                            // If the meal name is suspicious/corrupted, provide a fallback
                            if (isSuspiciousMeal(cleaned)) {
                              const mealTypeMap: { [key: string]: string } = {
                                'breakfast': 'Healthy breakfast option',
                                'lunch': 'Balanced lunch meal',
                                'dinner': 'Nutritious dinner',
                                'snack': 'Healthy snack'
                              };
                              return mealTypeMap[mealType] || 'Meal option';
                            }
                            
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
                              /\s*\brecommended\b[\s:]*/gi, // Remove single "Recommended:" text
                              /\s*\blight\b[\s:]*\blight\b[\s:]*\blight\b[\s:]*/gi, // Remove repeated "light" text
                              /\s*\blight\b[\s:]*\blight\b[\s:]*/gi, // Remove repeated "light" text
                              /\s*\blight\b[\s:]*/gi, // Remove single "light" text
                              /\s*\blightlightlight\b[\s:]*/gi, // Remove "lightlightlight" pattern
                              /\s*\blightlight\b[\s:]*/gi, // Remove "lightlight" pattern
                              /\s*\blight\b.*$/i, // Remove "light" and everything after it
                              /\s*lightlightlight.*$/i, // Remove "lightlightlight" and everything after it
                              /\s*lightlight.*$/i, // Remove "lightlight" and everything after it
                              /\s*light.*$/i, // Remove "light" and everything after it
                            ];
                            
                            patterns.forEach(pattern => {
                              cleaned = cleaned.replace(pattern, '');
                            });
                            
                            // Additional cleanup for repetitive text patterns
                            // Remove any word that repeats more than 3 times consecutively
                            const words = cleaned.split(/\s+/);
                            const cleanedWords = [];
                            let lastWord = '';
                            let repeatCount = 0;
                            
                            for (const word of words) {
                              if (word.toLowerCase() === lastWord.toLowerCase()) {
                                repeatCount++;
                                if (repeatCount <= 2) { // Keep up to 2 repetitions
                                  cleanedWords.push(word);
                                }
                                // Skip additional repetitions
                              } else {
                                lastWord = word;
                                repeatCount = 1;
                                cleanedWords.push(word);
                              }
                            }
                            
                            cleaned = cleanedWords.join(' ');
                            
                            // Additional aggressive cleanup for repetitive patterns
                            // Remove any text that contains repetitive "light" patterns
                            if (cleaned.toLowerCase().includes('lightlightlight') || 
                                cleaned.toLowerCase().includes('lightlight') ||
                                cleaned.toLowerCase().includes('light light light') ||
                                cleaned.toLowerCase().includes('light light')) {
                              // Extract only the meaningful part before the repetitive text
                              const meaningfulPart = cleaned.split(/\s*light\s*/i)[0];
                              cleaned = meaningfulPart.trim();
                            }
                            
                            // Clean up any remaining artifacts
                            cleaned = cleaned.trim();
                            
                            // If the cleaned name is too short or empty, try to extract from original
                            if (cleaned.length < 3) {
                              // Try to extract a reasonable recipe name
                              const words = desc.replace(/^Day\s+\d+:\s*/, '').split(/\s+/);
                              const meaningfulWords = words.filter((word: string) => 
                                word.length > 2 && 
                                !word.match(/^\d+$/) && 
                                !word.match(/^(with|and|or|the|a|an|in|on|at|to|from|for|of|by|light|recommended)$/i)
                              );
                              cleaned = meaningfulWords.slice(0, 4).join(' ');
                            }
                            
                            // Final fallback for corrupted or empty descriptions
                            if (cleaned.length < 3 || 
                                cleaned.toLowerCase().includes('lightlightlight') ||
                                cleaned.toLowerCase().includes('lightlight') ||
                                cleaned.toLowerCase().includes('light light light') ||
                                cleaned.toLowerCase().includes('light light') ||
                                cleaned.toLowerCase().includes('light')) {
                              // Provide sensible defaults based on meal type
                              const mealDefaults: { [key: string]: string } = {
                                'breakfast': 'Healthy breakfast option',
                                'lunch': 'Balanced lunch option',
                                'dinner': 'Nutritious dinner option',
                                'snack': 'Healthy snack option'
                              };
                              return mealDefaults[mealType] || 'Recipe';
                            }
                            
                            return cleaned || 'Recipe';
                          };
                          
                          const displayContent = getDisplayContent();
                          
                          // Determine card styling based on consumption status
                          const cardStyle = isConsumed ? {
                            bgcolor: 'rgba(76, 175, 80, 0.2)', // Green background for consumed
                            border: '2px solid rgba(76, 175, 80, 0.5)',
                            backdropFilter: 'blur(10px)'
                          } : {
                            bgcolor: 'rgba(255,255,255,0.1)', 
                            backdropFilter: 'blur(10px)'
                          };
                          
                          return (
                            <Grid item xs={12} sm={6} md={3} key={mealType}>
                              <Card sx={cardStyle}>
                                <CardContent sx={{ p: 2 }}>
                                  <Typography variant="subtitle2" sx={{ 
                                    fontWeight: 'bold', 
                                    textTransform: 'capitalize',
                                    color: 'white',
                                    mb: 1,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1
                                  }}>
                                    {mealType}
                                    {isConsumed && (
                                      <CheckCircleIcon sx={{ 
                                        fontSize: 16, 
                                        color: '#4CAF50' 
                                      }} />
                                    )}
                                    {/* Show item count for multiple items */}
                                    {isConsumed && consumptionStatus?.total_items > 1 && (
                                      <Chip 
                                        label={`${consumptionStatus.total_items} items`}
                                        size="small"
                                        sx={{ 
                                          height: '18px',
                                          fontSize: '0.65rem',
                                          bgcolor: 'rgba(255,255,255,0.2)',
                                          color: 'white'
                                        }}
                                      />
                                    )}
                                  </Typography>
                                  <Typography variant="body2" sx={{ 
                                    color: 'rgba(255,255,255,0.9)',
                                    fontSize: isConsumed ? '0.85rem' : '0.875rem',
                                    lineHeight: 1.3,
                                    wordBreak: 'break-word' // Ensure long food names wrap properly
                                  }}>
                                    {displayContent}
                                  </Typography>
                                  {/* Show total calories for consumed items */}
                                  {isConsumed && consumptionStatus?.total_calories > 0 && (
                                    <Typography variant="caption" sx={{ 
                                      color: 'rgba(255, 255, 255, 0.8)',
                                      fontSize: '0.7rem',
                                      mt: 0.5,
                                      display: 'block'
                                    }}>
                                      {consumptionStatus.total_calories} calories
                                    </Typography>
                                  )}
                                  {isConsumed && consumptionStatus?.matched === false && (
                                    <Typography variant="caption" sx={{ 
                                      color: 'rgba(255, 235, 59, 0.9)',
                                      fontSize: '0.7rem',
                                      mt: 0.5,
                                      display: 'block'
                                    }}>
                                      ⚠️ Deviated from plan
                                    </Typography>
                                  )}
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
                          Start tracking immediately! No meal plan needed - just log your food and get instant nutrition insights
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
          <Box sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'column', md: 'row' },
            gap: 2,
            alignItems: { xs: 'stretch', md: 'flex-start' },
            mb: 2 
          }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                Time Range
              </Typography>
              <ToggleButtonGroup
                value={selectedTimeRange}
                exclusive
                onChange={(e, newTimeRange) => {
                  if (newTimeRange) {
                    setSelectedTimeRange(newTimeRange);
                    fetchConsumptionAnalytics(newTimeRange);
                    fetchMealAnalytics(newTimeRange); // Fix: Also fetch meal analytics for Advanced Nutritional Analysis
                  }
                }}
                aria-label="time range selection"
                size="small"
                color="primary"
                sx={{ 
                  flexWrap: { xs: 'wrap', sm: 'nowrap' },
                  '& .MuiToggleButton-root': {
                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                    px: { xs: 1, sm: 2 }
                  }
                }}
              >
                <ToggleButton value="daily">Daily</ToggleButton>
                <ToggleButton value="weekly">Weekly</ToggleButton>
                <ToggleButton value="bi-weekly">Bi-Weekly</ToggleButton>
                <ToggleButton value="monthly">Monthly</ToggleButton>
              </ToggleButtonGroup>
            </Box>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                Chart Type
              </Typography>
              <ToggleButtonGroup
                value={analyticsChartType}
                exclusive
                onChange={(e, newChartType) => newChartType && setAnalyticsChartType(newChartType)}
                aria-label="chart type selection"
                size="small"
                color="secondary"
                sx={{ 
                  flexWrap: { xs: 'wrap', sm: 'wrap', md: 'nowrap' },
                  '& .MuiToggleButton-root': {
                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                    px: { xs: 1, sm: 1.5 },
                    minWidth: { xs: 'auto', sm: 'auto' }
                  }
                }}
              >
                <ToggleButton value="auto">
                  <AIIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Auto</Box>
                </ToggleButton>
                <ToggleButton value="line">
                  <ShowChartIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Line</Box>
                </ToggleButton>
                <ToggleButton value="bar">
                  <BarChartIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Bar</Box>
                </ToggleButton>
                <ToggleButton value="area">
                  <AreaChartIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Area</Box>
                </ToggleButton>
                <ToggleButton value="scatter">
                  <ScatterPlotIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Scatter</Box>
                </ToggleButton>
                <ToggleButton value="comparison">
                  <CompareIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Target</Box>
                </ToggleButton>
                <ToggleButton value="pie">
                  <PieChartIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Pie</Box>
                </ToggleButton>
                <ToggleButton value="doughnut">
                  <DonutLargeIcon sx={{ mr: { xs: 0, sm: 0.5 }, fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Doughnut</Box>
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>
          </Box>
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
          {/* AI Health Coach - Made Much Bigger */}
          <Grid item xs={12}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              minHeight: 600
            }}>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', color: 'white', mb: 3 }}>
                  <CoachIcon sx={{ mr: 2, fontSize: 36 }} />
                  💬 AI Health Coach
                </Typography>
                <Typography variant="h6" sx={{ mb: 4, color: 'rgba(255,255,255,0.95)', lineHeight: 1.6 }}>
                  Get instant personalized advice, meal suggestions, and health insights from your AI coach. Ask anything about your diabetes management, nutrition, meal planning, or health goals!
                </Typography>
                
                {/* Quick suggestion buttons */}
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', mb: 4 }}>
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
                        setAICoachQuery(suggestion);
                        if (!aiCoachLoading) {
                          handleAICoachQuery();
                        }
                      }}
                      clickable
                      sx={{ 
                        bgcolor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        border: '1px solid rgba(255,255,255,0.3)',
                        py: 1.5, 
                        px: 2, 
                        fontSize: '0.95rem',
                        '&:hover': { 
                          bgcolor: 'rgba(255,255,255,0.3)',
                          transform: 'translateY(-2px)',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                        },
                        transition: 'all 0.2s ease'
                      }}
                    />
                  ))}
                </Box>
                
                <TextField
                  fullWidth
                  multiline
                  rows={5}
                  placeholder="Ask me about your nutrition, meal suggestions, health goals, or any diabetes-related questions..."
                  value={aiCoachQuery}
                  onChange={(e) => setAICoachQuery(e.target.value)}
                  sx={{ 
                    mb: 3,
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.15)',
                      color: 'white',
                      fontSize: '1.1rem',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.4)', borderWidth: 2 },
                      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.6)' },
                      '&.Mui-focused fieldset': { borderColor: 'white', borderWidth: 2 }
                    },
                    '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.8)', fontSize: '1.05rem' }
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
                  startIcon={aiCoachLoading ? <CircularProgress size={24} /> : <CoachIcon sx={{ fontSize: 24 }} />}
                  size="large"
                  sx={{ 
                    bgcolor: 'rgba(255,255,255,0.25)', 
                    color: 'white',
                    py: 2,
                    px: 4,
                    fontSize: '1.2rem',
                    fontWeight: 'bold',
                    borderRadius: 3,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                    display: 'block',
                    margin: '0 auto',
                    maxWidth: 300,
                    '&:hover': { 
                      bgcolor: 'rgba(255,255,255,0.35)',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 6px 16px rgba(0,0,0,0.3)'
                    },
                    '&:disabled': { bgcolor: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.6)' },
                    transition: 'all 0.2s ease'
                  }}
                >
                  {aiCoachLoading ? 'AI is thinking...' : 'Ask AI Coach'}
                </Button>
                {aiCoachResponse && (
                  <Paper sx={{ 
                    p: 3, 
                    mt: 3, 
                    bgcolor: 'rgba(255,255,255,0.15)', 
                    backdropFilter: 'blur(10px)',
                    borderRadius: 3,
                    border: '1px solid rgba(255,255,255,0.2)'
                  }}>
                    <Typography variant="h6" sx={{ color: 'white', mb: 2, display: 'flex', alignItems: 'center' }}>
                      <CoachIcon sx={{ mr: 1 }} />
                      AI Coach Response:
                    </Typography>
                    <Typography variant="body1" sx={{ 
                      whiteSpace: 'pre-wrap', 
                      color: 'white', 
                      fontSize: '1.05rem',
                      lineHeight: 1.6,
                      mb: 2
                    }}>
                      {aiCoachResponse}
                    </Typography>
                    <Button 
                      size="medium" 
                      onClick={() => setAICoachResponse('')}
                      sx={{ 
                        mt: 1, 
                        color: 'white', 
                        borderColor: 'rgba(255,255,255,0.4)',
                        px: 3,
                        '&:hover': { 
                          borderColor: 'white', 
                          bgcolor: 'rgba(255,255,255,0.15)',
                          transform: 'translateY(-1px)'
                        },
                        transition: 'all 0.2s ease'
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
          <Alert severity="success" variant="outlined" sx={{ mt: 2, alignItems: 'flex-start' }}>
            <AlertTitle>No meal plan required</AlertTitle>
            <Typography variant="body2" color="text.primary">
              Our AI will analyze nutrition and diabetes suitability automatically. Food logging works independently and updates your daily nutrition score.
              {!quickLogMealType && ' Meal type will be auto-detected based on the current time.'}
            </Typography>
          </Alert>
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



      {/* Pending Consumption Dialog */}
      <PendingConsumptionDialog
        open={showPendingDialog}
        onClose={() => setShowPendingDialog(false)}
        pendingId={pendingId}
        analysisData={pendingAnalysis}
        onAccept={handlePendingAccept}
        onDelete={handlePendingDelete}
      />
    </Container>
  );
};

export default HomePage; 