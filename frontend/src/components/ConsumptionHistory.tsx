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
  Container,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  FormControlLabel,
  Switch,
  Fab,
  TextField
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
  Assessment as AssessmentIcon,
  // Phase 1: Deletion capabilities icons
  Delete as DeleteIcon,
  DeleteForever as DeleteForeverIcon,
  Restore as RestoreIcon,
  SelectAll as SelectAllIcon,
  Clear as ClearIcon,
  Undo as UndoIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  // Edit functionality icons
  Edit as EditIcon
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
  type: 'bar' | 'line' | 'pie' | 'doughnut';
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
  // Phase 1: Deletion capabilities
  deleted_at?: string;
  deleted_by?: string;
  deletion_reason?: string;
  soft_delete?: boolean;
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  
  // Enhanced state for advanced analytics
  const [selectedTimeRange, setSelectedTimeRange] = useState('7');
  const [selectedChartType, setSelectedChartType] = useState<'bar' | 'line' | 'pie' | 'doughnut'>('bar');
  const [selectedMetric, setSelectedMetric] = useState<keyof NutritionalInfo>('calories');
  const [comparisonMode, setComparisonMode] = useState(false);
  const [comparisonTimeRange, setComparisonTimeRange] = useState('14'); // For comparison mode
  const [comparisonAnalytics, setComparisonAnalytics] = useState<ConsumptionAnalytics | null>(null);
  const [expandedSections, setExpandedSections] = useState<string[]>(['overview']);
  const [fixingMealTypes, setFixingMealTypes] = useState(false);

  // Phase 1: Deletion capabilities state
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [bulkDelete, setBulkDelete] = useState(false);
  const [showDeleted, setShowDeleted] = useState(false);
  const [undoSnackbar, setUndoSnackbar] = useState(false);
  const [lastDeleted, setLastDeleted] = useState<string[]>([]);
  const [deletionLoading, setDeletionLoading] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Edit functionality state
  const [editDialog, setEditDialog] = useState(false);
  const [editingRecord, setEditingRecord] = useState<ConsumptionRecord | null>(null);
  const [editFormData, setEditFormData] = useState({
    food_name: '',
    estimated_portion: '',
    meal_type: ''
  });
  const [editLoading, setEditLoading] = useState(false);

  // Time range options
  const timeRanges: TimeRange[] = [
    { value: '1', label: 'Today', days: 1 },
    { value: '7', label: 'This Week', days: 7 },
    { value: '14', label: 'Last 2 Weeks', days: 14 },
    { value: '30', label: 'This Month', days: 30 },
    { value: '90', label: 'Last 3 Months', days: 90 },
    { value: '365', label: 'This Year', days: 365 }
  ];

  // Chart configurations for different metrics
  const chartConfigs: ChartConfig[] = [
    { type: 'bar', metric: 'calories', title: 'Calories', color: '#FF6B6B', icon: <CaloriesIcon /> },
    { type: 'bar', metric: 'protein', title: 'Protein (g)', color: '#4ECDC4', icon: <ProteinIcon /> },
    { type: 'bar', metric: 'carbohydrates', title: 'Carbohydrates (g)', color: '#45B7D1', icon: <CarbsIcon /> },
    { type: 'bar', metric: 'fat', title: 'Fat (g)', color: '#FFA07A', icon: <FatIcon /> },
    { type: 'bar', metric: 'fiber', title: 'Fiber (g)', color: '#98D8C8', icon: <FiberIcon /> },
    { type: 'bar', metric: 'sugar', title: 'Sugar (g)', color: '#F7DC6F', icon: <SugarIcon /> },
    { type: 'bar', metric: 'sodium', title: 'Sodium (mg)', color: '#BB8FCE', icon: <SodiumIcon /> }
  ];

  useEffect(() => {
    loadConsumptionData();
  }, [selectedTimeRange, showDeleted]);

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

      // Use the new endpoint that supports showing deleted records
      const endpoint = showDeleted 
        ? `/consumption/history-with-deleted?include_deleted=true&limit=${fetchLimit}`
        : `/consumption/history?limit=${fetchLimit}`;

      const [historyResponse, insightsResponse] = await Promise.all([
        fetch(`${config.API_URL}${endpoint}`, { headers }),
        fetch(`${config.API_URL}/coach/daily-insights`, { headers })
      ]);

      if (!historyResponse.ok) {
        throw new Error(`Failed to load consumption history: ${historyResponse.statusText}`);
      }
      if (!insightsResponse.ok) {
        throw new Error(`Failed to load daily insights: ${insightsResponse.statusText}`);
      }

      const historyData = await historyResponse.json();
      const insightsData = await insightsResponse.json();

      // Extract consumption history from response
      const allHistoryData = showDeleted 
        ? historyData.consumption_history 
        : historyData;

      console.log('Loaded raw consumption data:', { 
        totalRecords: allHistoryData.length, 
        selectedDays, 
        timezone: getUserTimezone(),
        showDeleted
      });

      // Client-side timezone-aware filtering with debugging
      let filteredHistory: any[] = [];
      
      console.log('=== FILTERING DEBUG ===');
      console.log('All records timestamps:', allHistoryData.map((r: any) => ({
        id: r.id, 
        food: r.food_name, 
        timestamp: r.timestamp,
        local_date: r.timestamp ? convertUTCToLocalDate(r.timestamp) : 'no timestamp'
      })));
      
      if (selectedDays === 1) {
        // For "Today", use strict filtering - only include records from today
        const today = getUserLocalDate();
        
        console.log('Today (local):', today);
        
        filteredHistory = allHistoryData.filter((record: any) => {
          if (!record.timestamp) return false;
          
          const recordLocalDate = convertUTCToLocalDate(record.timestamp);
          const isToday = recordLocalDate === today;
          
          console.log(`Record ${record.food_name}: ${record.timestamp} -> ${recordLocalDate} (Today: ${isToday})`);
          
          // For "Today" filter, only include today's records (no yesterday records)
          // This matches the homepage logic for consistency
          return isToday;
        });
        
        console.log('Filtered for today (lenient):', filteredHistory.length, 'records');
      } else {
        // For other ranges, use the original filtering logic
        filteredHistory = filterRecordsByDateRange(allHistoryData, selectedDays);
        console.log(`Filtered for last ${selectedDays} days:`, filteredHistory.length, 'records');
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

  // Phase 1: Deletion capability functions
  const handleSingleDelete = async (itemId: string) => {
    try {
      setDeletionLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${config.API_URL}/consumption/${itemId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete item');
      }

      setLastDeleted([itemId]);
      setSnackbarMessage('Item deleted successfully');
      setUndoSnackbar(true);
      
      // Refresh consumption history
      await loadConsumptionData();
    } catch (error) {
      console.error('Delete failed:', error);
      setError('Failed to delete item');
    } finally {
      setDeletionLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    try {
      setDeletionLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${config.API_URL}/consumption/bulk`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ consumption_ids: selectedItems })
      });

      if (!response.ok) {
        throw new Error('Failed to delete items');
      }

      const result = await response.json();
      
      setLastDeleted(selectedItems);
      setSnackbarMessage(`${result.deleted_count} items deleted successfully`);
      setUndoSnackbar(true);
      setSelectedItems([]);
      setDeleteDialog(false);
      
      if (result.failed_deletions.length > 0) {
        console.warn('Some deletions failed:', result.failed_deletions);
      }
      
      await loadConsumptionData();
    } catch (error) {
      console.error('Bulk delete failed:', error);
      setError('Failed to delete items');
    } finally {
      setDeletionLoading(false);
    }
  };

  const handleRestore = async (itemId: string) => {
    try {
      setDeletionLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${config.API_URL}/consumption/${itemId}/restore`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to restore item');
      }

      setSnackbarMessage('Item restored successfully');
      setUndoSnackbar(true);
      await loadConsumptionData();
    } catch (error) {
      console.error('Restore failed:', error);
      setError('Failed to restore item');
    } finally {
      setDeletionLoading(false);
    }
  };

  const handleUndo = async () => {
    try {
      const token = localStorage.getItem('token');
      
      for (const itemId of lastDeleted) {
        await fetch(`${config.API_URL}/consumption/${itemId}/restore`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      setUndoSnackbar(false);
      setSnackbarMessage('Items restored successfully');
      await loadConsumptionData();
    } catch (error) {
      console.error('Undo failed:', error);
      setError('Failed to undo deletion');
    }
  };

  const handleSelectAll = () => {
    if (selectedItems.length === consumptionHistory.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(consumptionHistory.map(item => item.id));
    }
  };

  const handleItemSelect = (itemId: string) => {
    if (selectedItems.includes(itemId)) {
      setSelectedItems(selectedItems.filter(id => id !== itemId));
    } else {
      setSelectedItems([...selectedItems, itemId]);
    }
  };

  // Edit functionality functions
  const handleEdit = (record: ConsumptionRecord) => {
    setEditingRecord(record);
    setEditFormData({
      food_name: record.food_name,
      estimated_portion: record.estimated_portion,
      meal_type: record.meal_type
    });
    setEditDialog(true);
  };

  const handleSaveEdit = async () => {
    if (!editingRecord) return;
    
    try {
      setEditLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${config.API_URL}/consumption/${editingRecord.id}/edit`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editFormData)
      });

      if (!response.ok) {
        throw new Error('Failed to update item');
      }

      setSnackbarMessage('Item updated successfully');
      setUndoSnackbar(true);
      setEditDialog(false);
      setEditingRecord(null);
      
      // Refresh consumption history
      await loadConsumptionData();
    } catch (error) {
      console.error('Edit failed:', error);
      setError('Failed to update item');
    } finally {
      setEditLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditDialog(false);
    setEditingRecord(null);
    setEditFormData({
      food_name: '',
      estimated_portion: '',
      meal_type: ''
    });
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

  // Helper functions for chart data generation
  const generateChartData = (metric: keyof NutritionalInfo) => {
    if (!analytics?.daily_nutrition_history) return null;

    /* ---------------------------------- PIE / DOUGHNUT ---------------------------------- */
    if (selectedChartType === 'pie' || selectedChartType === 'doughnut') {
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

    const chartConfig = chartConfigs.find(c => c.metric === metric);
    const color = chartConfig?.color || '#45B7D1';

    const datasets: any[] = [
      {
        label: `Current (${timeRanges.find(r => r.value === selectedTimeRange)?.label})`,
        data: valueList,
        backgroundColor: selectedChartType === 'line' ? 'rgba(0,0,0,0.05)' : color,
        borderColor: color,
        borderWidth: 2,
        fill: selectedChartType === 'line',
        tension: 0.4,
        pointBackgroundColor: color,
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
    if (!data) return <Typography>No data available</Typography>;

    const options = getChartOptions(metric);
    
    // Create a unique key to force chart re-rendering when time range or chart type changes
    const chartKey = `${selectedTimeRange}-${selectedChartType}-${metric}`;

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
        return <Bar key={chartKey} data={data} options={options} />;
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
                  {/* Phase 1: Show/Hide Deleted Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={showDeleted}
                  onChange={(e) => setShowDeleted(e.target.checked)}
                  sx={{ 
                    '& .MuiSwitch-switchBase.Mui-checked': { 
                      color: 'rgba(255,255,255,0.8)' 
                    }
                  }}
                />
              }
              label="Show Deleted"
              sx={{ color: 'rgba(255,255,255,0.9)' }}
            />
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

      {/* Phase 1: Bulk Actions Bar */}
      {selectedItems.length > 0 && (
        <Paper elevation={2} sx={{ p: 2, mb: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} selected
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                onClick={handleSelectAll}
                startIcon={selectedItems.length === consumptionHistory.length ? <ClearIcon /> : <SelectAllIcon />}
                sx={{ 
                  borderColor: 'primary.contrastText', 
                  color: 'primary.contrastText',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
                }}
              >
                {selectedItems.length === consumptionHistory.length ? 'Clear All' : 'Select All'}
              </Button>
              <Button
                variant="contained"
                color="error"
                onClick={() => setDeleteDialog(true)}
                startIcon={<DeleteIcon />}
                disabled={deletionLoading}
              >
                Delete Selected
              </Button>
            </Stack>
          </Box>
        </Paper>
      )}

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
          variant="fullWidth"
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            '& .MuiTab-root': { 
              fontWeight: 'bold',
              fontSize: '1rem'
            }
          }}
        >
          <Tab 
            label="📊 Daily Insights" 
            icon={<TrendingUpIcon />}
            iconPosition="start"
          />
          <Tab 
            label="🍽️ Meal History" 
            icon={<MealIcon />}
            iconPosition="start"
          />
          <Tab 
            label="📈 Advanced Analytics" 
            icon={<AnalyticsIcon />}
            iconPosition="start"
          />
          <Tab 
            label="📋 Detailed Reports" 
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

        {/* Enhanced Meal History Tab with Deletion Capabilities */}
        {activeTab === 1 && (
          <TabPanel value={activeTab} index={1}>
            {consumptionHistory.length === 0 ? (
              <Card>
                <CardContent>
                  <Box textAlign="center" py={4}>
                    <AppleIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      {showDeleted ? 'No records found' : 'No meals logged yet'}
                    </Typography>
                    <Typography color="textSecondary">
                      {showDeleted 
                        ? 'No consumption records found for the selected time period.' 
                        : 'Start logging your meals to see your consumption history here.'
                      }
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            ) : (
              <Box>
                {consumptionHistory.map((record) => (
                  <Card 
                    key={record.id} 
                    sx={{ 
                      mb: 2,
                      opacity: record.soft_delete ? 0.6 : 1,
                      border: record.soft_delete ? '1px dashed' : 'none',
                      borderColor: 'error.main'
                    }}
                  >
                    <CardContent>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        {/* Phase 1: Selection Checkbox */}
                        <Checkbox
                          checked={selectedItems.includes(record.id)}
                          onChange={() => handleItemSelect(record.id)}
                          disabled={record.soft_delete}
                        />
                        
                        <Typography variant="h6" component="span" sx={{ flexGrow: 1 }}>
                          {getMealTypeIcon(record.meal_type)} {record.food_name}
                          {record.soft_delete && (
                            <Chip 
                              label="DELETED" 
                              color="error" 
                              size="small" 
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Typography>
                        
                        <Chip label={record.meal_type} variant="outlined" size="small" />
                        
                        {/* Phase 1: Action Buttons */}
                        <Box display="flex" gap={1}>
                          {record.soft_delete ? (
                            <Tooltip title="Restore">
                              <IconButton 
                                onClick={() => handleRestore(record.id)}
                                color="success"
                                disabled={deletionLoading}
                              >
                                <RestoreIcon />
                              </IconButton>
                            </Tooltip>
                          ) : (
                            <>
                              <Tooltip title="Edit">
                                <IconButton 
                                  onClick={() => handleEdit(record)}
                                  color="primary"
                                  disabled={editLoading}
                                >
                                  <EditIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete">
                                <IconButton 
                                  onClick={() => handleSingleDelete(record.id)}
                                  color="error"
                                  disabled={deletionLoading}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </>
                          )}
                        </Box>
                      </Box>
                      
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        {record.estimated_portion} • {formatConsumptionTimestamp(record.timestamp)}
                        {record.deleted_at && (
                          <span style={{ color: 'red', marginLeft: 8 }}>
                            • Deleted: {formatConsumptionTimestamp(record.deleted_at)}
                          </span>
                        )}
                      </Typography>

                      <Grid container spacing={2} sx={{ mb: 2 }}>
                        <Grid item xs={6} sm={3}>
                          <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                            <Typography variant="h6">{Math.round(record.nutritional_info.calories)}</Typography>
                            <Typography variant="caption">Calories</Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                            <Typography variant="h6">{Math.round(record.nutritional_info.protein)}g</Typography>
                            <Typography variant="caption">Protein</Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                            <Typography variant="h6">{Math.round(record.nutritional_info.carbohydrates)}g</Typography>
                            <Typography variant="caption">Carbs</Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'info.light', color: 'info.contrastText' }}>
                            <Typography variant="h6">{Math.round(record.nutritional_info.fat)}g</Typography>
                            <Typography variant="caption">Fat</Typography>
                          </Paper>
                        </Grid>
                      </Grid>

                      {record.medical_rating && (
                        <Chip
                          label={`Diabetes Suitability: ${record.medical_rating.diabetes_suitability || 'N/A'}`}
                          color={getDiabetesSuitabilityColor(record.medical_rating.diabetes_suitability)}
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      )}
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </TabPanel>
        )}

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
                        📈 Trends Analysis
                              </Typography>
                      <Box sx={{ height: 400 }}>
                        {renderChart(selectedMetric)}
                            </Box>
                    </CardContent>
                  </Card>
                        </Grid>
                      </Grid>
            )}
            </Box>
        </TabPanel>
      </Paper>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onClose={handleCancelEdit} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Food Log</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Food Name"
              value={editFormData.food_name}
              onChange={(e) => setEditFormData({ ...editFormData, food_name: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Portion"
              value={editFormData.estimated_portion}
              onChange={(e) => setEditFormData({ ...editFormData, estimated_portion: e.target.value })}
              margin="normal"
              required
              placeholder="e.g., 1 cup, 200g, medium portion"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Meal Type</InputLabel>
              <Select
                value={editFormData.meal_type}
                onChange={(e) => setEditFormData({ ...editFormData, meal_type: e.target.value })}
                label="Meal Type"
                required
              >
                <MenuItem value="breakfast">Breakfast</MenuItem>
                <MenuItem value="lunch">Lunch</MenuItem>
                <MenuItem value="dinner">Dinner</MenuItem>
                <MenuItem value="snack">Snack</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelEdit}>Cancel</Button>
          <Button 
            onClick={handleSaveEdit} 
            variant="contained"
            disabled={editLoading || !editFormData.food_name.trim()}
          >
            {editLoading ? <CircularProgress size={20} /> : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Phase 1: Delete Confirmation Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Delete Selected Items</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''}?
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            This action can be undone within the current session.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleBulkDelete} 
            color="error" 
            variant="contained"
            disabled={deletionLoading}
          >
            {deletionLoading ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Phase 1: Undo Snackbar */}
      <Snackbar 
        open={undoSnackbar} 
        autoHideDuration={10000}
        onClose={() => setUndoSnackbar(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          severity="info" 
          action={
            lastDeleted.length > 0 ? (
              <Button color="inherit" onClick={handleUndo} startIcon={<UndoIcon />}>
                UNDO
              </Button>
            ) : null
          }
          onClose={() => setUndoSnackbar(false)}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ConsumptionHistory; 