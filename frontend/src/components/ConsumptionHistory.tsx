import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Tabs,
  Tab,
  Box,
  LinearProgress,
  CircularProgress,
  Alert,
  Grid,
  Paper,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Tooltip,
  IconButton,
  Stack,
  Container
} from '@mui/material';
import { 
  filterRecordsByDateRange,
  filterTodayRecords,
  groupRecordsByLocalDate,
  calculateDailyTotalsFromRecords,
  getUserTimezone,
  debugTimezone,
  convertUTCToLocalDate,
  getUserLocalDate
} from '../utils/timezone';
import { formatUTCToLocal } from '../utils/dateUtils';
import {
  Refresh as RefreshIcon,
  CalendarToday as CalendarIcon,
  TrendingUp as TrendingUpIcon,
  Apple as AppleIcon,
  ExpandMore as ExpandMoreIcon,
  BarChart as BarChartIcon,
  ShowChart as LineChartIcon,
  PieChart as PieChartIcon,
  Timeline as TimelineIcon,
  LocalFireDepartment as CaloriesIcon,
  FitnessCenter as ProteinIcon,
  Grain as CarbsIcon,
  Opacity as FatIcon,
  Nature as FiberIcon,
  Cake as SugarIcon,
  WaterDrop as SodiumIcon,
  Restaurant as MealIcon,
  Schedule as TimeIcon,
  Analytics as AnalyticsIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
} from 'chart.js';
import config from '../config/environment';
import { Bar, Pie, Line, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
);

// Enhanced types for comprehensive nutrition tracking
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
  type: 'bar' | 'line' | 'pie' | 'doughnut' | 'cumulative' | 'ratio' | 'distribution' | 'heatmap';
  metric: keyof NutritionalInfo;
  title: string;
  color: string;
  icon: React.ReactNode;
}

interface TimeRange {
  value: string;
  label: string;
  days: number;
}

interface MedicalRating {
    diabetes_suitability: string;
    glycemic_impact: string;
    recommended_frequency: string;
    portion_recommendation: string;
}

interface ConsumptionRecord {
  id: string;
  user_id: string;
  timestamp: string;
  food_name: string;
  estimated_portion: string;
  nutritional_info: NutritionalInfo;
  medical_rating: MedicalRating;
  image_analysis: string;
  meal_type: string;
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

interface DailyInsights {
  date: string;
  goals: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
  };
  today_totals: NutritionalInfo;
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

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`consumption-tabpanel-${index}`}
      aria-labelledby={`consumption-tab-${index}`}
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

const ConsumptionHistory: React.FC = () => {
  const [consumptionHistory, setConsumptionHistory] = useState<ConsumptionRecord[]>([]);
  const [analytics, setAnalytics] = useState<ConsumptionAnalytics | null>(null);
  const [dailyInsights, setDailyInsights] = useState<DailyInsights | null>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  
  // Enhanced state for advanced analytics
  const [selectedTimeRange, setSelectedTimeRange] = useState('7');
  const [selectedChartType, setSelectedChartType] = useState<'auto' | 'bar' | 'line' | 'pie' | 'doughnut'>('auto');
  const [selectedMetric, setSelectedMetric] = useState<keyof NutritionalInfo>('calories');
  const [comparisonMode, setComparisonMode] = useState(false);
  const [comparisonTimeRange, setComparisonTimeRange] = useState('14'); // For comparison mode
  const [comparisonAnalytics, setComparisonAnalytics] = useState<ConsumptionAnalytics | null>(null);
  const [expandedSections, setExpandedSections] = useState<string[]>(['overview']);
  const [fixingMealTypes, setFixingMealTypes] = useState(false);
  const [mealAnalytics, setMealAnalytics] = useState<any>(null);

  // Time range options
  const timeRanges: TimeRange[] = [
    { value: '1', label: 'Today', days: 1 },
    { value: '7', label: 'This Week', days: 7 },
    { value: '14', label: 'Last 2 Weeks', days: 14 },
    { value: '30', label: 'This Month', days: 30 },
    { value: '90', label: 'Last 3 Months', days: 90 },
    { value: '365', label: 'This Year', days: 365 }
  ];

  // Enhanced chart configurations with diverse visualization types
  const chartConfigs: ChartConfig[] = [
    { type: 'line', metric: 'calories', title: 'Calories Daily Trend', color: '#FF6B6B', icon: <CaloriesIcon /> },
    { type: 'bar', metric: 'protein', title: 'Protein vs Goal', color: '#4ECDC4', icon: <ProteinIcon /> },
    { type: 'cumulative', metric: 'carbohydrates', title: 'Carbs Throughout Day', color: '#45B7D1', icon: <CarbsIcon /> },
    { type: 'ratio', metric: 'fat', title: 'Fat vs Other Macros', color: '#FFA07A', icon: <FatIcon /> },
    { type: 'line', metric: 'fiber', title: 'Fiber Intake Pattern', color: '#98D8C8', icon: <FiberIcon /> },
    { type: 'distribution', metric: 'sugar', title: 'Sugar by Meal Type', color: '#F7DC6F', icon: <SugarIcon /> },
    { type: 'heatmap', metric: 'sodium', title: 'Sodium Intensity', color: '#BB8FCE', icon: <SodiumIcon /> }
  ];

  useEffect(() => {
    loadConsumptionData();
  }, [selectedTimeRange]);

  useEffect(() => {
    if (comparisonMode) {
      loadComparisonData();
    }
  }, [comparisonMode, comparisonTimeRange]);

  // Helper function to generate analytics from filtered records
  const generateAnalyticsFromRecords = (records: any[], days: number) => {
    if (!records || records.length === 0) {
      const today = new Date().toISOString().split('T')[0];
      return {
        total_meals: 0,
        daily_averages: {
          calories: 0,
          protein: 0,
          carbohydrates: 0,
          fat: 0,
          fiber: 0,
          sugar: 0,
          sodium: 0
        },
        daily_nutrition_history: [],
        meal_distribution: {
          breakfast: 0,
          lunch: 0,
          dinner: 0,
          snack: 0
        },
        weekly_trends: {
          calories: [],
          protein: [],
          carbohydrates: [],
          fat: []
        },
        adherence_stats: {
          diabetes_suitable_percentage: 0,
          calorie_goal_adherence: 0,
          protein_goal_adherence: 0,
          carb_goal_adherence: 0
        },
        top_foods: [],
        date_range: {
          start_date: today,
          end_date: today
        }
      };
    }

    // Group records by local date
    const groupedByDate = groupRecordsByLocalDate(records);
    
    // Calculate daily nutrition history
    const dailyNutritionHistory = Object.keys(groupedByDate)
      .sort()
      .map(date => {
        const dayRecords = groupedByDate[date];
        const totals = {
          calories: 0,
          protein: 0,
          carbohydrates: 0,
          fat: 0,
          fiber: 0,
          sugar: 0,
          sodium: 0
        };

        dayRecords.forEach(record => {
          const nutrition = record.nutritional_info || {};
          totals.calories += nutrition.calories || 0;
          totals.protein += nutrition.protein || 0;
          totals.carbohydrates += nutrition.carbohydrates || 0;
          totals.fat += nutrition.fat || 0;
          totals.fiber += nutrition.fiber || 0;
          totals.sugar += nutrition.sugar || 0;
          totals.sodium += nutrition.sodium || 0;
        });

        return {
          date,
          ...totals,
          meals_count: dayRecords.length
        };
      });

    // Calculate overall totals
    const totalCalories = dailyNutritionHistory.reduce((sum, day) => sum + day.calories, 0);
    const totalProtein = dailyNutritionHistory.reduce((sum, day) => sum + day.protein, 0);
    const totalCarbs = dailyNutritionHistory.reduce((sum, day) => sum + day.carbohydrates, 0);
    const totalFat = dailyNutritionHistory.reduce((sum, day) => sum + day.fat, 0);
    const totalFiber = dailyNutritionHistory.reduce((sum, day) => sum + day.fiber, 0);
    const totalSugar = dailyNutritionHistory.reduce((sum, day) => sum + day.sugar, 0);
    const totalSodium = dailyNutritionHistory.reduce((sum, day) => sum + day.sodium, 0);

    // Calculate daily averages
    const actualDays = Math.max(1, dailyNutritionHistory.length);
    const dailyAverages = {
      calories: totalCalories / actualDays,
      protein: totalProtein / actualDays,
      carbohydrates: totalCarbs / actualDays,
      fat: totalFat / actualDays,
      fiber: totalFiber / actualDays,
      sugar: totalSugar / actualDays,
      sodium: totalSodium / actualDays
    };

    // Calculate meal distribution with expected structure
    const mealDistribution = {
      breakfast: 0,
      lunch: 0,
      dinner: 0,
      snack: 0
    };
    
    records.forEach(record => {
      const mealType = record.meal_type || 'snack';
      if (mealType in mealDistribution) {
        mealDistribution[mealType as keyof typeof mealDistribution]++;
      } else {
        mealDistribution.snack++; // Default to snack for unknown meal types
      }
    });

    // Calculate weekly trends (last 7 days of data)
    const last7Days = dailyNutritionHistory.slice(-7);
    const weeklyTrends = {
      calories: last7Days.map(day => day.calories),
      protein: last7Days.map(day => day.protein),
      carbohydrates: last7Days.map(day => day.carbohydrates),
      fat: last7Days.map(day => day.fat)
    };

    // Calculate adherence stats (simplified)
    const diabetesSuitableCount = records.filter(record => {
      const medical = record.medical_rating || {};
      return medical.diabetes_suitability === 'suitable';
    }).length;

    const adherenceStats = {
      diabetes_suitable_percentage: records.length > 0 ? (diabetesSuitableCount / records.length) * 100 : 0,
      calorie_goal_adherence: Math.min(100, (dailyAverages.calories / 2000) * 100),
      protein_goal_adherence: Math.min(100, (dailyAverages.protein / 100) * 100),
      carb_goal_adherence: Math.min(100, (dailyAverages.carbohydrates / 250) * 100)
    };

    // Calculate top foods with calories
    const foodData: Record<string, { frequency: number; total_calories: number }> = {};
    records.forEach(record => {
      const foodName = record.food_name || 'Unknown Food';
      const calories = record.nutritional_info?.calories || 0;
      
      if (!foodData[foodName]) {
        foodData[foodName] = { frequency: 0, total_calories: 0 };
      }
      
      foodData[foodName].frequency++;
      foodData[foodName].total_calories += calories;
    });

    const topFoods = Object.entries(foodData)
      .sort(([,a], [,b]) => b.frequency - a.frequency)
      .slice(0, 10)
      .map(([food, data]) => ({ 
        food, 
        frequency: data.frequency, 
        total_calories: data.total_calories 
      }));

    // Calculate date range
    const sortedDates = dailyNutritionHistory.map(d => d.date).sort();
    const startDate = sortedDates[0] || new Date().toISOString();
    const endDate = sortedDates[sortedDates.length - 1] || new Date().toISOString();

    return {
      total_meals: records.length,
      daily_averages: dailyAverages,
      daily_nutrition_history: dailyNutritionHistory,
      meal_distribution: mealDistribution,
      weekly_trends: weeklyTrends,
      adherence_stats: adherenceStats,
      top_foods: topFoods,
      date_range: {
        start_date: startDate,
        end_date: endDate
      }
    };
  };

  const loadConsumptionData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Debug timezone information
      debugTimezone();

      const selectedDays = parseInt(selectedTimeRange);
      
      // Fetch more data to ensure we have enough records across timezones
      // For "Today", we'll fetch last 3 days to handle timezone differences
      const fetchLimit = selectedDays === 1 ? 50 : selectedDays * 10;

      // Get the auth token
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load raw data (we'll filter client-side for timezone accuracy)
      const [historyResponse, insightsResponse, mealAnalyticsResponse, profileResponse] = await Promise.all([
        fetch(`${config.API_URL}/consumption/history?limit=${fetchLimit}`, { headers }),
        fetch(`${config.API_URL}/coach/daily-insights`, { headers }),
        fetch(`${config.API_URL}/consumption/meal-analytics?days=${selectedDays}`, { headers }),
        fetch(`${config.API_URL}/user/profile`, { headers })
      ]);

      if (!historyResponse.ok) {
        throw new Error(`Failed to load consumption history: ${historyResponse.statusText}`);
      }
      if (!insightsResponse.ok) {
        throw new Error(`Failed to load daily insights: ${insightsResponse.statusText}`);
      }
      if (!mealAnalyticsResponse.ok) {
        console.warn(`Failed to load meal analytics: ${mealAnalyticsResponse.statusText}`);
      }

      const allHistoryData = await historyResponse.json();
      const insightsData = await insightsResponse.json();
      
      // Process meal analytics data if available
      let mealAnalyticsData = null;
      if (mealAnalyticsResponse.ok) {
        mealAnalyticsData = await mealAnalyticsResponse.json();
        console.log('Loaded meal analytics data:', mealAnalyticsData);
        setMealAnalytics(mealAnalyticsData);
      }

      // Load user profile for timezone information
      let profileData = null;
      if (profileResponse.ok) {
        const profileResult = await profileResponse.json();
        profileData = profileResult.profile || {};
        setUserProfile(profileData);
        console.log('Loaded user profile:', profileData);
      }

      // Get user's profile timezone for consistent filtering
      const userTimezone = profileData?.timezone || 'America/Toronto'; // Default to Toronto if not set
      
      console.log('Loaded raw consumption data:', { 
        totalRecords: allHistoryData.length, 
        selectedDays, 
        userTimezone,
        browserTimezone: getUserTimezone().timezone
      });

      // Client-side timezone-aware filtering with debugging
      let filteredHistory: any[] = [];
      
      console.log('=== FILTERING DEBUG ===');
      console.log('Using user profile timezone:', userTimezone);
      console.log('All records timestamps:', allHistoryData.map((r: any) => ({
        id: r.id, 
        food: r.food_name, 
        timestamp: r.timestamp,
        local_date: r.timestamp ? convertUTCToLocalDate(r.timestamp, userTimezone) : 'no timestamp'
      })));
      
      if (selectedDays === 1) {
        // For "Today", use strict filtering - only include records from today
        const today = getUserLocalDate(userTimezone);
        
        console.log('Today (user timezone):', today);
        
        filteredHistory = allHistoryData.filter((record: any) => {
          if (!record.timestamp) return false;
          
          const recordLocalDate = convertUTCToLocalDate(record.timestamp, userTimezone);
          const isToday = recordLocalDate === today;
          
          console.log(`Record ${record.food_name}: ${record.timestamp} -> ${recordLocalDate} (Today: ${isToday})`);
          
          // For "Today" filter, only include today's records (no yesterday records)
          // This matches the homepage logic for consistency
          return isToday;
        });
        
        console.log('Filtered for today (user timezone):', filteredHistory.length, 'records');
      } else {
        // For other ranges, use the original filtering logic
        filteredHistory = filterRecordsByDateRange(allHistoryData, selectedDays, userTimezone);
        console.log(`Filtered for last ${selectedDays} days (user timezone):`, filteredHistory.length, 'records');
      }
      
      console.log('Final filtered records:', filteredHistory.map((r: any) => ({
        id: r.id,
        food: r.food_name,
        timestamp: r.timestamp
      })));
      
      // Fallback mechanism: If we have no filtered records but we have raw data, 
      // and the user is looking at "Today", show the most recent records as fallback
      if (filteredHistory.length === 0 && allHistoryData.length > 0 && selectedDays === 1) {
        console.log('⚠️  No records found with timezone filtering, using fallback...');
        // Show the most recent 10 records as fallback
        const sortedRecords = allHistoryData.sort((a: any, b: any) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        filteredHistory = sortedRecords.slice(0, 10);
        console.log('Fallback: Using most recent', filteredHistory.length, 'records');
      }
      
      console.log('=== END FILTERING DEBUG ===');

      // Generate analytics from filtered data
      let analytics = generateAnalyticsFromRecords(filteredHistory, selectedDays);

      // For "Today" view, use the backend daily insights data to ensure consistency with homepage
      if (selectedDays === 1 && insightsData && insightsData.today_totals) {
        console.log('Using backend daily insights for Today view to ensure consistency with homepage');
        console.log('Backend today_totals:', insightsData.today_totals);
        console.log('Frontend filtered records:', filteredHistory.length);
        
        // DEBUG: If backend shows calories but frontend shows no records, there's an issue
        if (insightsData.today_totals.calories > 0 && filteredHistory.length === 0) {
          console.error('❌ INCONSISTENCY: Backend shows calories but frontend shows no records!');
          console.error('Backend calories:', insightsData.today_totals.calories);
          console.error('Frontend filtered records:', filteredHistory.length);
        } else if (insightsData.today_totals.calories === 0 && filteredHistory.length > 0) {
          console.error('❌ INCONSISTENCY: Backend shows no calories but frontend shows records!');
          console.error('Backend calories:', insightsData.today_totals.calories);
          console.error('Frontend filtered records:', filteredHistory.length);
        } else {
          console.log('✅ Backend and frontend data are consistent');
        }
        
        analytics = {
          ...analytics,
          daily_averages: {
            calories: insightsData.today_totals.calories || 0,
            protein: insightsData.today_totals.protein || 0,
            carbohydrates: insightsData.today_totals.carbohydrates || 0,
            fat: insightsData.today_totals.fat || 0,
            fiber: insightsData.today_totals.fiber || 0,
            sugar: insightsData.today_totals.sugar || 0,
            sodium: insightsData.today_totals.sodium || 0
          }
        };
      }

      setConsumptionHistory(filteredHistory);
      setAnalytics(analytics);
      setDailyInsights(insightsData);

    } catch (err) {
      console.error('Error loading consumption data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load consumption data');
    } finally {
      setLoading(false);
    }
  };

  const loadComparisonData = async () => {
    try {
      const selectedDays = parseInt(comparisonTimeRange);
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load comparison analytics data
      const analyticsResponse = await fetch(`${config.API_URL}/consumption/analytics?days=${selectedDays}`, { headers });
      
      if (!analyticsResponse.ok) {
        throw new Error(`Failed to load comparison analytics: ${analyticsResponse.statusText}`);
      }

      const analyticsData = await analyticsResponse.json();
      setComparisonAnalytics(analyticsData);

    } catch (err) {
      console.error('Error loading comparison data:', err);
      // Don't show error for comparison data, just log it
    }
  };

  const handleFixMealTypes = async () => {
    try {
      setFixingMealTypes(true);
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const response = await fetch(`${config.API_URL}/consumption/fix-meal-types`, {
        method: 'POST',
        headers
      });

      if (!response.ok) {
        throw new Error(`Failed to fix meal types: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Show success message
      if (result.success) {
        alert(`Successfully fixed meal types for ${result.updated_records} out of ${result.total_records} records!`);
        
        // Reload the data to reflect the changes
        loadConsumptionData();
      } else {
        throw new Error(result.error || 'Failed to fix meal types');
      }

    } catch (err) {
      console.error('Error fixing meal types:', err);
      setError(err instanceof Error ? err.message : 'Failed to fix meal types');
    } finally {
      setFixingMealTypes(false);
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
  const generateChartData = (metric: keyof NutritionalInfo) => {
    if (!analytics?.daily_nutrition_history) return null;

    const data = analytics.daily_nutrition_history;
    const chartConfigForType = chartConfigs.find(config => config.metric === metric);
    const colorForType = chartConfigForType?.color || '#45B7D1';
    const chartType = chartConfigForType?.type || 'line';

    // Generate diverse chart types based on nutrient configuration when in "auto" mode
    if (selectedChartType === 'auto') {
      let chartData = null;
      
      switch (chartType) {
        case 'cumulative':
          chartData = generateCumulativeChartData(metric, data, colorForType);
          break;
        case 'ratio':
          chartData = generateRatioChartData(metric, data, colorForType);
          break;
        case 'distribution':
          chartData = generateDistributionChartData(metric, data, colorForType);
          break;
        case 'heatmap':
          chartData = generateHeatmapChartData(metric, data, colorForType);
          break;
      }
      
      // If special chart type worked, return it
      if (chartData && chartData.datasets && chartData.datasets.length > 0) {
        return chartData;
      }
    }

    /* ---------------------------------- PIE / DOUGHNUT ---------------------------------- */
    if (selectedChartType === 'pie' || selectedChartType === 'doughnut') {
      const selectedDays = parseInt(selectedTimeRange, 10);
      
      // For "Today" view, use real meal analytics data - FIXED
      if (selectedDays === 1 && mealAnalytics?.meal_breakdown) {
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
      
      // For multi-day views, use meal distribution (meal counts)
      const mealDistribution = analytics.meal_distribution || {};
      const labels = Object.keys(mealDistribution);
      const values = Object.values(mealDistribution);

      if (labels.length === 0) return null;

      return {
        labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
        datasets: [{
          data: values,
          backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'],
          borderWidth: 2,
          borderColor: '#fff',
          hoverOffset: 4
        }]
      };
    }

    /* ---------------------------------- BAR / LINE ---------------------------------- */
    const selectedDays = parseInt(selectedTimeRange, 10);
    
    // FIXED: For "Today" view, use meal analytics for more accurate data
    if (selectedDays === 1 && mealAnalytics?.meal_breakdown) {
      const mealBreakdown = mealAnalytics.meal_breakdown;
      const mealLabels = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];
      const mealValues = mealLabels.map(mealType => {
        return mealBreakdown[mealType.toLowerCase()]?.[metric] || 0;
      });
      
      // Check if we have any data to show
      const totalValue = mealValues.reduce((sum, val) => sum + val, 0);
      if (totalValue === 0) return null;
      
      return {
        labels: mealLabels,
        datasets: [{
          label: `${metric.charAt(0).toUpperCase() + metric.slice(1)} by Meal (Today)`,
          data: mealValues,
          backgroundColor: selectedChartType === 'line' ? 'rgba(0,0,0,0.05)' : colorForType,
          borderColor: colorForType,
          borderWidth: 2,
          fill: selectedChartType === 'line',
          tension: 0.4,
          pointBackgroundColor: colorForType,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      };
    }
    
    // For multi-day views, use the original daily history approach
    const today = new Date();
    const dateList: string[] = [];
    const valueList: number[] = [];

    // Helper map for quick lookup
    const currentMap: Record<string, any> = {};
    analytics!.daily_nutrition_history.forEach(day => {
      currentMap[day.date.split('T')[0]] = day;
    });

    for (let i = selectedDays - 1; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const iso = d.toISOString().split('T')[0];
      dateList.push(formatDate(iso));
      valueList.push((currentMap[iso]?.[metric] as number) || 0);
    }

    const chartConfigLater = chartConfigs.find(c => c.metric === metric);
    const colorLater = chartConfigLater?.color || '#45B7D1';

    const datasets: any[] = [
      {
        label: `Current (${timeRanges.find(r => r.value === selectedTimeRange)?.label})`,
        data: valueList,
        backgroundColor: selectedChartType === 'line' ? 'rgba(0,0,0,0.05)' : colorLater,
        borderColor: colorLater,
        borderWidth: 2,
        fill: selectedChartType === 'line',
        tension: 0.4,
        pointBackgroundColor: colorLater,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }
    ];

    /* ------------- Comparison dataset (aligned with same dateList) ------------- */
    if (comparisonMode && comparisonAnalytics?.daily_nutrition_history) {
      const comparisonMap: Record<string, any> = {};
      comparisonAnalytics.daily_nutrition_history.forEach(day => {
        comparisonMap[day.date.split('T')[0]] = day;
      });

      const comparisonValues = dateList.map((_l, idx) => {
        const d = new Date(today);
        d.setDate(today.getDate() - (selectedDays - 1 - idx));
        const iso = d.toISOString().split('T')[0];
        return (comparisonMap[iso]?.[metric] as number) || 0;
      });

      const comparisonColor = 'rgba(0,0,0,0.4)';

      datasets.push({
        label: `Comparison (${timeRanges.find(r => r.value === comparisonTimeRange)?.label})`,
        data: comparisonValues,
        backgroundColor: selectedChartType === 'line' ? 'rgba(0,0,0,0.03)' : comparisonColor,
        borderColor: comparisonColor,
        borderWidth: 2,
        fill: selectedChartType === 'line',
        tension: 0.4,
        pointBackgroundColor: comparisonColor,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        ...(selectedChartType === 'line' && { borderDash: [5, 5] })
      });
    }

    return {
      labels: dateList,
      datasets
    };
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

  // Ratio visualization (for fat vs other macros) - FIXED TO USE REAL DATA
  const generateRatioChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    // For "Today" view, use meal analytics for more accurate data
    const selectedDays = parseInt(selectedTimeRange, 10);
    if (selectedDays === 1 && mealAnalytics?.daily_totals) {
      const dailyTotals = mealAnalytics.daily_totals;
      const fatValue = dailyTotals.fat || 0;
      const proteinValue = dailyTotals.protein || 0;
      const carbsValue = dailyTotals.carbohydrates || 0;
      
      if (fatValue === 0 && proteinValue === 0 && carbsValue === 0) return null;
      
      return {
        labels: ['Fat', 'Protein', 'Carbohydrates'],
        datasets: [{
          label: 'Macronutrient Distribution (Today - Real Data)',
          data: [fatValue, proteinValue, carbsValue],
          backgroundColor: [color, '#4ECDC4', '#45B7D1'],
          borderColor: ['#fff', '#fff', '#fff'],
          borderWidth: 2,
          hoverOffset: 4
        }]
      };
    }
    
    // For multi-day views, use daily nutrition history
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



  // Distribution by meal type (for sugar) - FIXED TO USE REAL MEAL DATA
  const generateDistributionChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    if (!mealAnalytics?.meal_breakdown) return null;
    
    const mealBreakdown = mealAnalytics.meal_breakdown;
    
    // Get actual meal values from real consumption data
    const breakfastValue = mealBreakdown.breakfast?.[metric] || 0;
    const lunchValue = mealBreakdown.lunch?.[metric] || 0;
    const dinnerValue = mealBreakdown.dinner?.[metric] || 0;
    const snackValue = mealBreakdown.snack?.[metric] || 0;
    
    // Calculate total and check if we have any data
    const totalValue = breakfastValue + lunchValue + dinnerValue + snackValue;
    if (totalValue === 0) return null;
    
    return {
      labels: ['Breakfast', 'Lunch', 'Dinner', 'Snack'],
      datasets: [{
        label: `${metric.charAt(0).toUpperCase() + metric.slice(1)} Distribution (Real Data)`,
        data: [
          breakfastValue,
          lunchValue,
          dinnerValue,
          snackValue
        ],
        backgroundColor: [
          color + 'FF',
          color + 'CC',
          color + '99',
          color + '77'
        ].map(c => c.length === 7 ? c + 'FF' : c),
        borderWidth: 0
      }]
    };
  };

  // Heatmap-style intensity chart (for sodium)
  const generateHeatmapChartData = (metric: keyof NutritionalInfo, data: any[], color: string) => {
    if (!data || data.length === 0) return null;
    
    const recentData = data.slice(-7);
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

  const getChartOptions = (metric: keyof NutritionalInfo) => {
    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const selectedTimeRangeLabel = timeRanges.find(r => r.value === selectedTimeRange)?.label || 'Selected Period';
    
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
          text: `${chartConfig?.title || metric} - ${selectedTimeRangeLabel}${comparisonMode ? ' (Comparison Mode)' : ''}`,
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
              const rawVal = context.parsed.y ?? context.parsed ?? 0;
              const numericVal = typeof rawVal === 'number' && isFinite(rawVal) ? rawVal : Number(rawVal) || 0;
              const unit = metric === 'calories' ? 'kcal' : 
                          metric === 'sodium' ? 'mg' : 'g';
              return `${label}: ${numericVal.toFixed(1)} ${unit}`;
            }
          }
        }
      }
    };

    // Add scales only for bar and line charts
    if (selectedChartType !== 'pie' && selectedChartType !== 'doughnut') {
      const unit = metric === 'calories' ? 'kcal' : 
                   metric === 'sodium' ? 'mg' : 'g';
      
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
    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const currentValue = (analytics?.daily_nutrition_history?.[analytics.daily_nutrition_history.length - 1] as any)?.[metric] || 0;
    const dailyGoal = dailyRecommendations[metric] || 100;
    
    if (!data) return <Typography>No data available</Typography>;

    const options = getChartOptions(metric);
    const chartKey = `${selectedTimeRange}-${selectedChartType}-${metric}`;
    const specificChartType = chartConfig?.type || 'line';

    // Render specific chart type for each nutrient when in auto mode
    if (selectedChartType === 'auto') {
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
        default:
          return <Line key={chartKey} data={data} options={options} />;
      }
    }
    
    // Fallback to original chart type selector logic for manual selection
    switch (selectedChartType) {
      case 'bar':
        return <Bar key={chartKey} data={data} options={options} />;
      case 'line':
        return <Line key={chartKey} data={data} options={options} />;
      case 'pie':
        return <Pie key={chartKey} data={data} options={options} />;
      case 'doughnut':
        return <Doughnut key={chartKey} data={data} options={options} />;
      default:
        return <Line key={chartKey} data={data} options={options} />;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const selectedDays = parseInt(selectedTimeRange);
      
      // Use timezone-aware formatting based on time range
      if (selectedDays === 1) {
        // For "Today" view, show relative dates with time
        return formatUTCToLocal(dateString, {
          includeDate: true,
          includeTime: true,
          relative: true,
          format: 'short'
        });
      } else if (selectedDays <= 7) {
        // For weekly view, show day and date
        return formatUTCToLocal(dateString, {
          includeDate: true,
          includeTime: false,
          relative: false,
          format: 'short'
        });
      } else if (selectedDays <= 30) {
        // For monthly view, show month and day
        return formatUTCToLocal(dateString, {
          includeDate: true,
          includeTime: false,
          relative: false,
          format: 'short'
        });
      } else {
        // For longer periods, show full date
        return formatUTCToLocal(dateString, {
          includeDate: true,
          includeTime: false,
          relative: false,
          format: 'numeric'
        });
      }
    } catch {
      return 'Invalid Date';
    }
  };

  // Separate function for formatting consumption record timestamps (always show time)
  const formatConsumptionTimestamp = (dateString: string) => {
    try {
      return formatUTCToLocal(dateString, {
        includeDate: true,
        includeTime: true,
        relative: true,
        format: 'short'
      });
    } catch {
      return 'Invalid Date';
    }
  };

  const getDiabetesSuitabilityColor = (suitability: string) => {
    switch (suitability?.toLowerCase()) {
      case 'high':
      case 'good':
      case 'excellent':
        return 'success';
      case 'medium':
      case 'moderate':
        return 'warning';
      case 'low':
      case 'poor':
        return 'error';
      default:
        return 'default';
    }
  };

  const getMealTypeIcon = (mealType: string) => {
    switch (mealType?.toLowerCase()) {
      case 'breakfast':
        return '🌅';
      case 'lunch':
        return '🌞';
      case 'dinner':
        return '🌙';
      case 'snack':
        return '🍎';
      default:
        return '🍽️';
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="400px">
        <CircularProgress size={60} sx={{ mb: 2 }} />
        <Typography color="textSecondary">Loading consumption data...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box maxWidth="600px" mx="auto" p={3}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Error Loading Data</Typography>
          <Typography>{error}</Typography>
          </Alert>
        <Button variant="contained" onClick={loadConsumptionData} startIcon={<RefreshIcon />}>
          Try Again
        </Button>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      {/* Enhanced Header with Controls */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
          <Box>
            <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
              🍎 Nutrition Analytics Dashboard
          </Typography>
            <Typography variant="h6" sx={{ opacity: 0.9 }}>
              Advanced insights into your dietary patterns and nutritional progress
                </Typography>
          </Box>
          <Stack direction="row" spacing={2} alignItems="center">
                  <Button
              variant="contained"
              onClick={loadConsumptionData}
              startIcon={<RefreshIcon />}
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' } }}
            >
              Refresh Data
                  </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Advanced Controls Panel */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Time Period</InputLabel>
              <Select
                value={selectedTimeRange}
                label="Time Period"
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                startAdornment={<TimeIcon sx={{ mr: 1, color: 'action.active' }} />}
              >
                {timeRanges.map((range) => (
                  <MenuItem key={range.value} value={range.value}>
                    {range.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Chart Type</InputLabel>
              <Select
                value={selectedChartType}
                label="Chart Type"
                onChange={(e) => setSelectedChartType(e.target.value as any)}
              >
                <MenuItem value="auto"><AnalyticsIcon sx={{ mr: 1 }} />Auto (Smart Charts)</MenuItem>
                <MenuItem value="bar"><BarChartIcon sx={{ mr: 1 }} />Bar Chart</MenuItem>
                <MenuItem value="line"><LineChartIcon sx={{ mr: 1 }} />Line Chart</MenuItem>
                <MenuItem value="pie"><PieChartIcon sx={{ mr: 1 }} />Pie Chart</MenuItem>
                <MenuItem value="doughnut"><AnalyticsIcon sx={{ mr: 1 }} />Doughnut</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3} sx={{ display: 'none' }}>
            <FormControl fullWidth>
              <InputLabel>Metric</InputLabel>
              <Select
                value={selectedMetric}
                label="Metric"
                onChange={(e) => setSelectedMetric(e.target.value as keyof NutritionalInfo)}
              >
                {chartConfigs.map((config) => (
                  <MenuItem key={config.metric} value={config.metric}>
                    <Box display="flex" alignItems="center" gap={1}>
                      {config.icon}
                      {config.title}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <ToggleButtonGroup
              value={comparisonMode}
              exclusive
              onChange={(e, value) => setComparisonMode(value)}
              aria-label="comparison mode"
              fullWidth
            >
              <ToggleButton value={false} aria-label="single view">
                <AssessmentIcon sx={{ mr: 1 }} />
                Single View
              </ToggleButton>
              <ToggleButton value={true} aria-label="comparison view">
                <TimelineIcon sx={{ mr: 1 }} />
                Compare
              </ToggleButton>
            </ToggleButtonGroup>
          </Grid>

          {/* Comparison Time Range - only show when comparison mode is enabled */}
          {comparisonMode && (
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Compare With</InputLabel>
                <Select
                  value={comparisonTimeRange}
                  label="Compare With"
                  onChange={(e) => setComparisonTimeRange(e.target.value)}
                  startAdornment={<TimeIcon sx={{ mr: 1, color: 'action.active' }} />}
                >
                  {timeRanges.map((range) => (
                    <MenuItem key={range.value} value={range.value}>
                      {range.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Enhanced Tabs with Advanced Analytics */}
      <Paper elevation={2} sx={{ width: '100%' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          aria-label="consumption tabs"
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            '& .MuiTab-root': { 
              fontWeight: 'bold',
              fontSize: { xs: '0.75rem', sm: '0.875rem', md: '1rem' },
              minWidth: { xs: 80, sm: 120, md: 160 },
              px: { xs: 1, sm: 2 }
            }
          }}
        >
          <Tab 
            label="DAILY INSIGHTS" 
            icon={<TrendingUpIcon />}
            iconPosition="start"
          />
          <Tab 
            label="MEAL HISTORY" 
            icon={<MealIcon />}
            iconPosition="start"
          />
          <Tab 
            label="ADVANCED ANALYTICS" 
            icon={<AnalyticsIcon />}
            iconPosition="start"
          />
          <Tab 
            label="DETAILED REPORTS" 
            icon={<AssessmentIcon />}
            iconPosition="start"
          />
        </Tabs>

        {/* Daily Insights Tab */}
        <TabPanel value={activeTab} index={0}>
          {dailyInsights && (
            <Box>
              {/* Today's Progress */}
              <Card sx={{ mb: 3 }}>
                          <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CalendarIcon />
                    Today's Progress
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Calories: {Math.round(dailyInsights.today_totals.calories)}/{dailyInsights.goals.calories}
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(100, dailyInsights.adherence.calories)}
                          sx={{ mt: 1 }}
                        />
                            </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Protein: {Math.round(dailyInsights.today_totals.protein)}g/{dailyInsights.goals.protein}g
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                          value={Math.min(100, dailyInsights.adherence.protein)}
                          sx={{ mt: 1 }}
                        />
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Carbs: {Math.round(dailyInsights.today_totals.carbohydrates)}g/{dailyInsights.goals.carbohydrates}g
                            </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(100, dailyInsights.adherence.carbohydrates)}
                          sx={{ mt: 1 }}
                        />
                      </Box>
                      </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Fat: {Math.round(dailyInsights.today_totals.fat)}g/{dailyInsights.goals.fat}g
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(100, dailyInsights.adherence.fat)}
                          sx={{ mt: 1 }}
                        />
          </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Recommendations */}
              {dailyInsights.recommendations.length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Recommendations
                    </Typography>
          <Box>
                      {dailyInsights.recommendations.map((rec, index) => (
                        <Alert
                          key={index}
                          severity={rec.priority === 'high' ? 'error' : rec.priority === 'medium' ? 'warning' : 'success'}
                          sx={{ mb: 1 }}
                        >
                          {rec.message}
                        </Alert>
                      ))}
        </Box>
                  </CardContent>
                </Card>
              )}
          </Box>
          )}
        </TabPanel>

        {/* Meal History Tab */}
        <TabPanel value={activeTab} index={1}>
          {consumptionHistory.length === 0 ? (
              <Card>
                <CardContent>
                <Box textAlign="center" py={4}>
                  <AppleIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No meals logged yet
                  </Typography>
                  <Typography color="textSecondary">
                    Start logging your meals to see your consumption history here.
                  </Typography>
                </Box>
                </CardContent>
              </Card>
          ) : (
            <Box>
              {consumptionHistory.map((record) => (
                <Card key={record.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Typography variant="h6" component="span">
                        {getMealTypeIcon(record.meal_type)} {record.food_name}
                      </Typography>
                      <Chip label={record.meal_type} variant="outlined" size="small" />
                    </Box>
                    
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      {record.estimated_portion} • {formatConsumptionTimestamp(record.timestamp)}
                    </Typography>

                    <Grid container spacing={{ xs: 1, sm: 2 }} sx={{ mb: 2 }}>
                      <Grid item xs={6} sm={3}>
                        <Paper sx={{ 
                          p: { xs: 1, sm: 1 }, 
                          textAlign: 'center', 
                          bgcolor: 'primary.light', 
                          color: 'primary.contrastText',
                          minHeight: { xs: 60, sm: 'auto' }
                        }}>
                          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                            {Math.round(record.nutritional_info.calories)}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                            Calories
                          </Typography>
                        </Paper>
            </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper sx={{ 
                          p: { xs: 1, sm: 1 }, 
                          textAlign: 'center', 
                          bgcolor: 'success.light', 
                          color: 'success.contrastText',
                          minHeight: { xs: 60, sm: 'auto' }
                        }}>
                          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                            {Math.round(record.nutritional_info.protein)}g
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                            Protein
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper sx={{ 
                          p: { xs: 1, sm: 1 }, 
                          textAlign: 'center', 
                          bgcolor: 'warning.light', 
                          color: 'warning.contrastText',
                          minHeight: { xs: 60, sm: 'auto' }
                        }}>
                          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                            {Math.round(record.nutritional_info.carbohydrates)}g
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                            Carbs
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper sx={{ 
                          p: { xs: 1, sm: 1 }, 
                          textAlign: 'center', 
                          bgcolor: 'secondary.light', 
                          color: 'secondary.contrastText',
                          minHeight: { xs: 60, sm: 'auto' }
                        }}>
                          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                            {Math.round(record.nutritional_info.fat)}g
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                            Fat
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>

                    <Box display="flex" gap={1}>
                      {record.medical_rating?.diabetes_suitability && (
                        <Chip
                          label={`${record.medical_rating.diabetes_suitability} diabetes suitability`}
                          color={getDiabetesSuitabilityColor(record.medical_rating.diabetes_suitability) as any}
                          size="small"
                        />
                      )}
                      {record.medical_rating?.glycemic_impact && (
                        <Chip
                          label={`${record.medical_rating.glycemic_impact} glycemic impact`}
                          variant="outlined"
                          size="small"
                        />
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </TabPanel>

        {/* Advanced Analytics Tab */}
        <TabPanel value={activeTab} index={2}>
          {analytics && (
            <Box>
              {/* Multi-metric Charts */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  📈 Nutrition Metrics Charts
                </Typography>
                <Grid container spacing={3}>
                  {chartConfigs.map((config) => (
                    <Grid item xs={12} md={6} key={config.metric}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {config.icon} {config.title}
                          </Typography>
                          <Box sx={{ height: 300 }}>
                            {renderChart(config.metric)}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>

              {/* Multi-Metric Comparison Grid */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                {chartConfigs.slice(0, 4).map((config) => (
                  <Grid item xs={12} sm={6} md={3} key={config.metric}>
                    <Card 
                      sx={{ 
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        '&:hover': { 
                          transform: 'translateY(-4px)',
                          boxShadow: 4
                        },
                        border: selectedMetric === config.metric ? 2 : 0,
                        borderColor: 'primary.main'
                      }}
                      onClick={() => setSelectedMetric(config.metric)}
                    >
                      <CardContent sx={{ textAlign: 'center', p: 2 }}>
                        <Box sx={{ color: config.color, mb: 1 }}>
                          {config.icon}
                        </Box>
                                                <Typography variant="h4" sx={{ color: config.color, fontWeight: 'bold' }}>
                          {selectedTimeRange === '1' && dailyInsights?.today_totals ? 
                            Math.round((dailyInsights.today_totals[config.metric] || 0) as number) :
                            (analytics!.daily_averages[config.metric] 
                              ? Math.round(analytics!.daily_averages[config.metric] as number)
                              : 0)}
                        </Typography>
                  <Typography variant="body2" color="textSecondary">
                          {config.title}
                        </Typography>
                                                <Typography variant="caption" color="textSecondary">
                          {selectedTimeRange === '1' ? 'Daily Total' : 'Daily Average'}
                        </Typography>
                </CardContent>
              </Card>
            </Grid>
                ))}
              </Grid>

              {/* Expandable Sections */}
              <Accordion 
                expanded={expandedSections.includes('overview')}
                onChange={() => {
                  setExpandedSections(prev => 
                    prev.includes('overview') 
                      ? prev.filter(s => s !== 'overview')
                      : [...prev, 'overview']
                  );
                }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">📊 Overview Statistics</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={comparisonMode ? 6 : 3}>
                      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                        <Typography variant="h3" fontWeight="bold">
                          {analytics!.total_meals}
                  </Typography>
                        <Typography variant="h6">Total Meals</Typography>
                        <Typography variant="body2" sx={{ opacity: 0.8 }}>
                          {timeRanges.find(r => r.value === selectedTimeRange)?.label}
                  </Typography>
                        {comparisonMode && comparisonAnalytics && (
                          <Typography variant="h4" sx={{ mt: 1, opacity: 0.8 }}>
                            vs {comparisonAnalytics!.total_meals}
                          </Typography>
                        )}
                      </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={comparisonMode ? 6 : 3}>
                      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                        <Typography variant="h3" fontWeight="bold">
                          {Math.round(analytics!.adherence_stats.diabetes_suitable_percentage)}%
                  </Typography>
                        <Typography variant="h6">Diabetes Suitable</Typography>
                        <Typography variant="body2" sx={{ opacity: 0.8 }}>
                          Meal Quality Score
                    </Typography>
                        {comparisonMode && comparisonAnalytics && (
                          <Typography variant="h4" sx={{ mt: 1, opacity: 0.8 }}>
                            vs {Math.round(comparisonAnalytics!.adherence_stats.diabetes_suitable_percentage)}%
                          </Typography>
                        )}
                      </Paper>
                    </Grid>
                    {!comparisonMode && (
                      <>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                            <Typography variant="h3" fontWeight="bold">
                              {selectedTimeRange === '1' && dailyInsights?.today_totals ? 
                                Math.round(dailyInsights.today_totals.calories) : 
                                Math.round(analytics!.daily_averages.calories)}
                            </Typography>
                            <Typography variant="h6">{selectedTimeRange === '1' ? 'Total Calories' : 'Avg Calories'}</Typography>
                            <Typography variant="body2" sx={{ opacity: 0.8 }}>
                              Per Day
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
                            <Typography variant="h3" fontWeight="bold">
                              {selectedTimeRange === '1' && dailyInsights?.today_totals ? 
                                Math.round(dailyInsights.today_totals.protein) : 
                                Math.round(analytics!.daily_averages.protein)}g
                            </Typography>
                            <Typography variant="h6">{selectedTimeRange === '1' ? 'Total Protein' : 'Avg Protein'}</Typography>
                            <Typography variant="body2" sx={{ opacity: 0.8 }}>
                              Per Day
                            </Typography>
                          </Paper>
                        </Grid>
                      </>
                    )}
                  </Grid>

                  {/* Comparison Details - only show when comparison mode is enabled */}
                  {comparisonMode && comparisonAnalytics && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        📊 Detailed Comparison
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'grey.100' }}>
                            <Typography variant="h6" fontWeight="bold">
                              {Math.round(analytics!.daily_averages.calories)} vs {Math.round(comparisonAnalytics!.daily_averages.calories)}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Avg Calories/Day
                            </Typography>
                            <Typography variant="body2" color={analytics!.daily_averages.calories > comparisonAnalytics!.daily_averages.calories ? 'error' : 'success'}>
                              {analytics!.daily_averages.calories > comparisonAnalytics!.daily_averages.calories ? '↑' : '↓'} 
                              {Math.abs(Math.round(analytics!.daily_averages.calories - comparisonAnalytics!.daily_averages.calories))} cal
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'grey.100' }}>
                            <Typography variant="h6" fontWeight="bold">
                              {Math.round(analytics!.daily_averages.protein)}g vs {Math.round(comparisonAnalytics!.daily_averages.protein)}g
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Avg Protein/Day
                            </Typography>
                            <Typography variant="body2" color={analytics!.daily_averages.protein > comparisonAnalytics!.daily_averages.protein ? 'success' : 'error'}>
                              {analytics!.daily_averages.protein > comparisonAnalytics!.daily_averages.protein ? '↑' : '↓'} 
                              {Math.abs(Math.round(analytics!.daily_averages.protein - comparisonAnalytics!.daily_averages.protein))}g
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'grey.100' }}>
                            <Typography variant="h6" fontWeight="bold">
                              {Math.round(analytics!.daily_averages.carbohydrates)}g vs {Math.round(comparisonAnalytics!.daily_averages.carbohydrates)}g
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Avg Carbs/Day
                            </Typography>
                            <Typography variant="body2" color={analytics!.daily_averages.carbohydrates > comparisonAnalytics!.daily_averages.carbohydrates ? 'error' : 'success'}>
                              {analytics!.daily_averages.carbohydrates > comparisonAnalytics!.daily_averages.carbohydrates ? '↑' : '↓'} 
                              {Math.abs(Math.round(analytics!.daily_averages.carbohydrates - comparisonAnalytics!.daily_averages.carbohydrates))}g
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'grey.100' }}>
                            <Typography variant="h6" fontWeight="bold">
                              {Math.round(analytics!.daily_averages.fat)}g vs {Math.round(comparisonAnalytics!.daily_averages.fat)}g
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Avg Fat/Day
                            </Typography>
                            <Typography variant="body2" color={analytics!.daily_averages.fat > comparisonAnalytics!.daily_averages.fat ? 'error' : 'success'}>
                              {analytics!.daily_averages.fat > comparisonAnalytics!.daily_averages.fat ? '↑' : '↓'} 
                              {Math.abs(Math.round(analytics!.daily_averages.fat - comparisonAnalytics!.daily_averages.fat))}g
                            </Typography>
                          </Paper>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>

              <Accordion 
                expanded={expandedSections.includes('distribution')}
                onChange={() => {
                  setExpandedSections(prev => 
                    prev.includes('distribution') 
                      ? prev.filter(s => s !== 'distribution')
                      : [...prev, 'distribution']
                  );
                }}
                sx={{ mt: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">🍽️ Meal Distribution Analysis</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ mb: 3 }}>
                    <Button 
                      variant="outlined" 
                      color="primary" 
                      onClick={handleFixMealTypes}
                      disabled={fixingMealTypes}
                      startIcon={fixingMealTypes ? <CircularProgress size={20} /> : <RefreshIcon />}
                      sx={{ mr: 2 }}
                    >
                      {fixingMealTypes ? 'Fixing...' : 'Fix Meal Categories'}
                    </Button>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      If your meals are incorrectly categorized (e.g., all showing as snacks), click this button to fix them based on the time they were logged.
                    </Typography>
                  </Box>
                  <Grid container spacing={3}>
                    {Object.entries(analytics.meal_distribution).map(([meal, count]) => (
                      <Grid item xs={6} sm={3} key={meal}>
            <Paper 
              sx={{ 
                            p: 3, 
                            textAlign: 'center', 
                            bgcolor: 'grey.100',
                transition: 'all 0.3s ease',
                '&:hover': {
                              bgcolor: 'grey.200',
                              transform: 'scale(1.05)'
                            }
                          }}
                        >
                          <Typography variant="h2" sx={{ mb: 1 }}>
                            {getMealTypeIcon(meal)}
              </Typography>
                          <Typography variant="h4" fontWeight="bold" color="primary">
                            {count}
                          </Typography>
                          <Typography variant="h6" sx={{ textTransform: 'capitalize', fontWeight: 'medium' }}>
                            {meal}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            {Math.round((count / analytics!.total_meals) * 100)}% of total
                          </Typography>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </AccordionDetails>
              </Accordion>

              <Accordion 
                expanded={expandedSections.includes('foods')}
                onChange={() => {
                  setExpandedSections(prev => 
                    prev.includes('foods') 
                      ? prev.filter(s => s !== 'foods')
                      : [...prev, 'foods']
                  );
                }}
                sx={{ mt: 2 }}
              >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">🥗 Top Foods Analysis</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {analytics.top_foods.length > 0 ? (
                    <List>
                      {analytics.top_foods.slice(0, 10).map((food, index) => (
                        <ListItem 
                          key={index}
                          sx={{ 
                            bgcolor: index % 2 === 0 ? 'grey.50' : 'transparent',
                            borderRadius: 1,
                            mb: 1
                          }}
                        >
                          <ListItemIcon>
                            <Avatar sx={{ bgcolor: 'primary.main' }}>
                              {index + 1}
                            </Avatar>
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Typography variant="h6" fontWeight="medium">
                                {food.food}
                        </Typography>
                            }
                            secondary={
                              <Box>
                                <Typography variant="body2" color="textSecondary">
                                  Consumed {food.frequency} times • {Math.round(food.total_calories)} total calories
                                </Typography>
                                <Typography variant="body2" color="primary">
                                  Average: {Math.round(food.total_calories / food.frequency)} cal per serving
                                </Typography>
                              </Box>
                            }
                          />
                          <Box textAlign="right">
                        <Chip
                              label={`${food.frequency}x`} 
                              color="primary" 
                          size="small"
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="caption" display="block" color="textSecondary">
                              {Math.round((food.frequency / analytics!.total_meals) * 100)}% frequency
                          </Typography>
                        </Box>
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography color="textSecondary" textAlign="center" py={4}>
                      No food data available for the selected time period.
                    </Typography>
                  )}
                </AccordionDetails>
              </Accordion>
                            </Box>
                          )}
        </TabPanel>

        {/* Detailed Reports Tab */}
        <TabPanel value={activeTab} index={3}>
          <Box>
            <Typography variant="h5" gutterBottom>
              📋 Comprehensive Nutrition Report
                          </Typography>
            <Typography variant="body1" color="textSecondary" paragraph>
              Detailed breakdown of your nutritional intake for {timeRanges.find(r => r.value === selectedTimeRange)?.label.toLowerCase()}
                          </Typography>

            {analytics && (
              <Grid container spacing={3}>
                {/* Macronutrients Breakdown */}
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        🥩 Macronutrients Breakdown
                          </Typography>
                      <Box sx={{ height: 300 }}>
                        {renderChart('calories')}
                          </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Micronutrients */}
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        🌿 Micronutrients Overview
                            </Typography>
                      <Stack spacing={2}>
                                                <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>Fiber</Typography>
                          <Typography fontWeight="bold">
                            {selectedTimeRange === '1' && dailyInsights?.today_totals ? 
                              Math.round(dailyInsights.today_totals.fiber || 0) : 
                              Math.round(analytics!.daily_averages.fiber || 0)}g{selectedTimeRange === '1' ? '' : '/day'}
                          </Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>Sugar</Typography>
                          <Typography fontWeight="bold">
                            {selectedTimeRange === '1' && dailyInsights?.today_totals ? 
                              Math.round(dailyInsights.today_totals.sugar || 0) : 
                              Math.round(analytics!.daily_averages.sugar || 0)}g{selectedTimeRange === '1' ? '' : '/day'}
                          </Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>Sodium</Typography>
                          <Typography fontWeight="bold">
                            {selectedTimeRange === '1' && dailyInsights?.today_totals ? 
                              Math.round(dailyInsights.today_totals.sodium || 0) : 
                              Math.round(analytics!.daily_averages.sodium || 0)}mg{selectedTimeRange === '1' ? '' : '/day'}
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Trends Analysis */}
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        📈 Protein Trend (vs Goal)
                      </Typography>
                      <Box sx={{ height: 400 }}>
                        {renderChart('protein')}
                      </Box>
                    </CardContent>
                  </Card>
                        </Grid>
                      </Grid>
            )}
            </Box>
        </TabPanel>
      </Paper>
      </Container>
  );
};

export default ConsumptionHistory; 