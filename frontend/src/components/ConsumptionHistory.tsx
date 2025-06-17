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
  const [expandedSections, setExpandedSections] = useState<string[]>(['overview']);

  // Time range options
  const timeRanges: TimeRange[] = [
    { value: '1', label: 'Today', days: 1 },
    { value: '2', label: 'Yesterday vs Today', days: 2 },
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
  }, [selectedTimeRange]);

  const loadConsumptionData = async () => {
    try {
      setLoading(true);
      setError(null);

      const selectedDays = parseInt(selectedTimeRange);
      const historyLimit = selectedDays === 1 ? 20 : selectedDays * 5; // More data for longer periods

      // Get the auth token
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load all data in parallel with dynamic time range (using authenticated endpoints)
      const [historyResponse, analyticsResponse, insightsResponse] = await Promise.all([
        fetch(`http://localhost:8000/consumption/history?limit=${historyLimit}`, { headers }),
        fetch(`http://localhost:8000/consumption/analytics?days=${selectedDays}`, { headers }),
        fetch('http://localhost:8000/coach/daily-insights', { headers })
      ]);

      if (!historyResponse.ok) {
        throw new Error(`Failed to load consumption history: ${historyResponse.statusText}`);
      }
      if (!analyticsResponse.ok) {
        throw new Error(`Failed to load analytics: ${analyticsResponse.statusText}`);
      }
      if (!insightsResponse.ok) {
        throw new Error(`Failed to load daily insights: ${insightsResponse.statusText}`);
      }

      const historyData = await historyResponse.json();
      const analyticsData = await analyticsResponse.json();
      const insightsData = await insightsResponse.json();

      console.log('Loaded consumption data:', { historyData, analyticsData, insightsData });

      setConsumptionHistory(historyData);
      setAnalytics(analyticsData);
      setDailyInsights(insightsData);

    } catch (err) {
      console.error('Error loading consumption data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load consumption data');
    } finally {
      setLoading(false);
    }
  };

  // Helper functions for chart data generation
  const generateChartData = (metric: keyof NutritionalInfo) => {
    if (!analytics?.daily_nutrition_history) return null;

    const data = analytics.daily_nutrition_history.slice(-parseInt(selectedTimeRange));
    const labels = data.map(day => formatDate(day.date));
    const values = data.map(day => (day as any)[metric] || 0);

    const chartConfig = chartConfigs.find(config => config.metric === metric);
    const color = chartConfig?.color || '#45B7D1';

    if (selectedChartType === 'pie' || selectedChartType === 'doughnut') {
      // For pie charts, show distribution across meal types
      const mealDistribution = analytics.meal_distribution;
      return {
        labels: Object.keys(mealDistribution),
        datasets: [{
          data: Object.values(mealDistribution),
          backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      };
    }

    return {
      labels,
      datasets: [{
        label: chartConfig?.title || metric,
        data: values,
        backgroundColor: selectedChartType === 'line' ? 'transparent' : color,
        borderColor: color,
        borderWidth: 2,
        fill: selectedChartType === 'line',
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
          text: `${chartConfig?.title || metric} - ${timeRanges.find(r => r.value === selectedTimeRange)?.label}`,
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
      scales: selectedChartType === 'pie' || selectedChartType === 'doughnut' ? {} : {
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

    switch (selectedChartType) {
      case 'bar':
        return <Bar data={data} options={options} />;
      case 'line':
        return <Line data={data} options={options} />;
      case 'pie':
        return <Pie data={data} options={options} />;
      case 'doughnut':
        return <Doughnut data={data} options={options} />;
      default:
        return <Bar data={data} options={options} />;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
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
                <MenuItem value="bar"><BarChartIcon sx={{ mr: 1 }} />Bar Chart</MenuItem>
                <MenuItem value="line"><LineChartIcon sx={{ mr: 1 }} />Line Chart</MenuItem>
                <MenuItem value="pie"><PieChartIcon sx={{ mr: 1 }} />Pie Chart</MenuItem>
                <MenuItem value="doughnut"><AnalyticsIcon sx={{ mr: 1 }} />Doughnut</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
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
                      {record.estimated_portion} • {formatDate(record.timestamp)}
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
                        <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
                          <Typography variant="h6">{Math.round(record.nutritional_info.fat)}g</Typography>
                          <Typography variant="caption">Fat</Typography>
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
              {/* Interactive Chart Section */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    📈 Interactive Nutrition Charts
                  </Typography>
                  <Box sx={{ height: 400, mt: 2 }}>
                    {renderChart(selectedMetric)}
                  </Box>
                </CardContent>
              </Card>

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
                          {analytics.daily_averages[config.metric] 
                            ? Math.round(analytics.daily_averages[config.metric] as number)
                            : 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                          {config.title}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Daily Average
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
            <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                        <Typography variant="h3" fontWeight="bold">
                          {analytics.total_meals}
                  </Typography>
                        <Typography variant="h6">Total Meals</Typography>
                        <Typography variant="body2" sx={{ opacity: 0.8 }}>
                          {timeRanges.find(r => r.value === selectedTimeRange)?.label}
                  </Typography>
                      </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                        <Typography variant="h3" fontWeight="bold">
                          {Math.round(analytics.adherence_stats.diabetes_suitable_percentage)}%
                  </Typography>
                        <Typography variant="h6">Diabetes Suitable</Typography>
                        <Typography variant="body2" sx={{ opacity: 0.8 }}>
                          Meal Quality Score
                    </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                        <Typography variant="h3" fontWeight="bold">
                          {Math.round(analytics.daily_averages.calories)}
                    </Typography>
                        <Typography variant="h6">Avg Calories</Typography>
                        <Typography variant="body2" sx={{ opacity: 0.8 }}>
                          Per Day
                    </Typography>
                      </Paper>
            </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
                        <Typography variant="h3" fontWeight="bold">
                          {Math.round(analytics.daily_averages.protein)}g
                        </Typography>
                        <Typography variant="h6">Avg Protein</Typography>
                        <Typography variant="body2" sx={{ opacity: 0.8 }}>
                          Per Day
                        </Typography>
            </Paper>
                    </Grid>
                  </Grid>
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
                            {Math.round((count / analytics.total_meals) * 100)}% of total
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
                              {Math.round((food.frequency / analytics.total_meals) * 100)}% frequency
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
                          <Typography fontWeight="bold">{Math.round(analytics.daily_averages.fiber || 0)}g/day</Typography>
                          </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>Sugar</Typography>
                          <Typography fontWeight="bold">{Math.round(analytics.daily_averages.sugar || 0)}g/day</Typography>
                          </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>Sodium</Typography>
                          <Typography fontWeight="bold">{Math.round(analytics.daily_averages.sodium || 0)}mg/day</Typography>
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
      </Container>
  );
};

export default ConsumptionHistory; 