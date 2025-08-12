import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent
} from '@mui/material';
import {
  ArrowBack,
  Download,
  CalendarToday,
  Person,
  LocalHospital,
  Assessment,
  Psychology
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
  LineElement
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import ReactMarkdown from 'react-markdown';
import config from '../config/environment';
import { parseLocalYMD } from '../utils/timezone';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

// TypeScript Interfaces
interface PatientInfo {
  user_id: string;
  user_name: string;
  registration_code: string;
  medical_condition: string;
  is_diabetic: boolean;
}

interface AnalysisPeriod {
  days: number;
  start_date: string;
  end_date: string;
  total_records: number;
  days_with_data: number;
}

interface NutritionalAverages {
  daily_avg_calories: number;
  daily_avg_protein: number;
  daily_avg_carbs: number;
  daily_avg_fat: number;
  daily_avg_fiber: number;
  daily_avg_sodium: number;
  daily_avg_sugar: number;
}

interface BarGraphData {
  categories: string[];
  current_values: number[];
  target_values: number[];
  target_ranges: number[][];
}

interface ComplianceAnalysis {
  total_days: number;
  days_within_calorie_target: number;
  days_above_target: number;
  days_below_target: number;
  days_within_nutrient_targets: number;
  days_with_nutrient_issues: number;
  calorie_target_compliance_rate?: number;
  overall_compliance_rate?: number;
  compliance_timeline: Array<{
    date: string;
    calorie_status: string;
    nutrient_issues: string[];
    calories: number;
    within_targets: boolean;
  }>;
  target_ranges: {
    calorie_min: number;
    calorie_max: number;
    fiber_min: number;
    protein_min_percentage: number;
    sodium_max: number;
    sugar_max_percentage: number;
  };
  personal_progress?: {
    score: number;
    avg_daily_calories: number;
    improvement_trend: number;
    recent_average: number;
    early_average: number;
    is_improving: boolean;
    encouragement_message: string;
  };
}

interface DailyData {
  date: string;
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fat: number;
  total_fiber: number;
  total_sodium: number;
  total_sugar: number;
  meal_count: number;
  meals?: Array<{
    timestamp: string;
    food_name: string;
    quantity: number;
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
    fiber: number;
    sodium: number;
    sugar: number;
  }>;
}

interface HistoricalData {
  daily_data: DailyData[];
  weekly_data: any[];
  monthly_data: any[];
}

interface PatientDetailsData {
  patient_info: PatientInfo;
  analysis_period: AnalysisPeriod;
  historical_data: HistoricalData;
  nutritional_averages: NutritionalAverages;
  bar_graph_data: BarGraphData;
  compliance_analysis: ComplianceAnalysis;
  insights: string[];
  recommendations: string[];
  download_ready: boolean;
  generated_at: string;
}

// LLM Advice Interfaces
interface LLMPatientInfo {
  patient_id: string;
  patient_name: string;
  medical_condition: string;
  is_diabetic: boolean;
}

interface LLMAnalysisSummary {
  analysis_period_days: number;
  total_food_records: number;
  avg_daily_calories: number;
  avg_daily_protein: number;
  avg_daily_carbs: number;
  avg_daily_fat: number;
  avg_daily_fiber: number;
  avg_daily_sodium: number;
  concerning_patterns: {
    high_calorie_days: number;
    low_calorie_days: number;
    high_sodium_days: number;
    low_fiber_days: number;
  };
}

interface LLMAdviceData {
  patient_info: LLMPatientInfo;
  analysis_summary: LLMAnalysisSummary;
  llm_advice: string;
  data_availability: string;
  generated_at: string;
  error?: string;
}

const PatientDetails: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  
  const [patientData, setPatientData] = useState<PatientDetailsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const analysisPeriod = 90; // Fixed analysis period
  const [downloadMenuAnchor, setDownloadMenuAnchor] = useState<null | HTMLElement>(null);
  
  // Time period selector for charts
  const [chartTimePeriod, setChartTimePeriod] = useState<string>('weekly');
  const timePeriodOptions = [
    { value: 'today', label: 'Today', days: 1 },
    { value: 'yesterday', label: 'Yesterday', days: 1 },
    { value: 'weekly', label: 'Weekly', days: 7 },
    { value: 'biweekly', label: 'Bi-Weekly', days: 14 },
    { value: 'monthly', label: 'Monthly', days: 30 },
    { value: 'sixmonths', label: 'Six Months', days: 180 },
    { value: 'yearly', label: 'Yearly', days: 365 }
  ];
  
  // LLM Advice state
  const [llmAdviceData, setLlmAdviceData] = useState<LLMAdviceData | null>(null);
  const [llmAdviceLoading, setLlmAdviceLoading] = useState(false);
  const [llmAdviceError, setLlmAdviceError] = useState<string | null>(null);

  // Format AI recommendations with proper markdown rendering
  const formatAIRecommendations = (content: string) => {
    return (
      <ReactMarkdown
        components={{
          p: ({ children }) => <Typography variant="body2" sx={{ mb: 1.5, lineHeight: 1.7 }}>{children}</Typography>,
          strong: ({ children }) => <Typography component="span" sx={{ fontWeight: 'bold', color: 'primary.main' }}>{children}</Typography>,
          em: ({ children }) => <Typography component="span" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>{children}</Typography>,
          ul: ({ children }) => <Box component="ul" sx={{ pl: 2, mb: 1.5, '& li': { mb: 0.5 } }}>{children}</Box>,
          ol: ({ children }) => <Box component="ol" sx={{ pl: 2, mb: 1.5, '& li': { mb: 0.5 } }}>{children}</Box>,
          li: ({ children }) => <Typography component="li" variant="body2" sx={{ lineHeight: 1.6 }}>{children}</Typography>,
          h1: ({ children }) => <Typography variant="h5" sx={{ mt: 2, mb: 1, fontWeight: 'bold', color: 'primary.main' }}>{children}</Typography>,
          h2: ({ children }) => <Typography variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 'bold', color: 'primary.main' }}>{children}</Typography>,
          h3: ({ children }) => <Typography variant="subtitle1" sx={{ mt: 1.5, mb: 1, fontWeight: 'bold', color: 'primary.main' }}>{children}</Typography>,
          h4: ({ children }) => <Typography variant="subtitle2" sx={{ mt: 1.5, mb: 0.5, fontWeight: 'bold', color: 'text.primary' }}>{children}</Typography>,
          blockquote: ({ children }) => (
            <Box 
              sx={{ 
                borderLeft: 3, 
                borderColor: 'primary.main', 
                pl: 2, 
                ml: 1, 
                my: 1.5,
                bgcolor: 'grey.50',
                py: 1,
                borderRadius: '0 4px 4px 0'
              }}
            >
              {children}
            </Box>
          ),
          code: ({ children }) => (
            <Typography 
              component="code" 
              sx={{ 
                bgcolor: 'grey.100', 
                px: 0.5, 
                py: 0.25, 
                borderRadius: 0.5, 
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                color: 'primary.dark'
              }}
            >
              {children}
            </Typography>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  // Handle time period change
  const handleTimePeriodChange = (event: SelectChangeEvent<string>) => {
    setChartTimePeriod(event.target.value);
  };

  // Helper function to get filtered data based on time period
  const getFilteredData = (): DailyData[] => {
    if (!patientData?.historical_data?.daily_data) return [];
    
    const today = new Date();
    const selectedOption = timePeriodOptions.find(option => option.value === chartTimePeriod);
    const daysToShow = selectedOption?.days || 7;
    
    let startDate: Date;
    
    if (chartTimePeriod === 'today') {
      startDate = new Date(today);
      startDate.setHours(0, 0, 0, 0);
    } else if (chartTimePeriod === 'yesterday') {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 1);
      startDate.setHours(0, 0, 0, 0);
    } else {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - daysToShow + 1);
      startDate.setHours(0, 0, 0, 0);
    }
    
    return patientData.historical_data.daily_data.filter((day: DailyData) => {
      const dayDate = parseLocalYMD(day.date);
      return dayDate >= startDate && dayDate <= today;
    });
  };

  const fetchPatientDetails = useCallback(async () => {
    if (!patientId) return;

    try {
      setLoading(true);
      setError(null);
      
      const decodedPatientId = decodeURIComponent(patientId);
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/patient/${encodeURIComponent(decodedPatientId)}/details?days=${analysisPeriod}&include_download_data=true`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('No consumption data found for this patient');
        }
        throw new Error('Failed to fetch patient details');
      }

      const result: PatientDetailsData = await response.json();
      setPatientData(result);
    } catch (err) {
      console.error('Error fetching patient details:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [patientId, analysisPeriod]);

  const fetchLLMAdvice = useCallback(async () => {
    if (!patientId) return;

    try {
      setLlmAdviceLoading(true);
      setLlmAdviceError(null);
      
      const decodedPatientId = decodeURIComponent(patientId);
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/patient/${encodeURIComponent(decodedPatientId)}/advice?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('No consumption data available for AI analysis');
        }
        throw new Error('Failed to fetch AI medical advice');
      }

      const result: LLMAdviceData = await response.json();
      setLlmAdviceData(result);
    } catch (err) {
      console.error('Error fetching LLM advice:', err);
      setLlmAdviceError(err instanceof Error ? err.message : 'Failed to load AI advice');
    } finally {
      setLlmAdviceLoading(false);
    }
  }, [patientId, analysisPeriod]);

  useEffect(() => {
    fetchPatientDetails();
    fetchLLMAdvice();
  }, [fetchPatientDetails, fetchLLMAdvice]);

  const generateNutritionalBarChart = () => {
    if (!patientData?.bar_graph_data) return { datasets: [] };

    const filteredData = getFilteredData();
    const { categories, target_values } = patientData.bar_graph_data;

    // Calculate averages for the selected time period
    const current_values = filteredData.length > 0 ? [
      filteredData.reduce((sum: number, day: DailyData) => sum + day.total_calories, 0) / filteredData.length,
      filteredData.reduce((sum: number, day: DailyData) => sum + day.total_protein, 0) / filteredData.length,
      filteredData.reduce((sum: number, day: DailyData) => sum + day.total_carbs, 0) / filteredData.length,
      filteredData.reduce((sum: number, day: DailyData) => sum + day.total_fat, 0) / filteredData.length
    ] : [0, 0, 0, 0];

    return {
      labels: categories,
      datasets: [
        {
          label: `Current Average (${timePeriodOptions.find(opt => opt.value === chartTimePeriod)?.label})`,
          data: current_values,
          backgroundColor: 'rgba(54, 162, 235, 0.8)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2,
        },
        {
          label: 'Target Value',
          data: target_values,
          backgroundColor: 'rgba(75, 192, 192, 0.8)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 2,
        }
      ]
    };
  };

  const generateComplianceChart = () => {
    if (!patientData?.compliance_analysis?.compliance_timeline) return { datasets: [] };

    const filteredData = getFilteredData();
    
    // Filter compliance data for the selected time period
    const filteredCompliance = patientData.compliance_analysis.compliance_timeline.filter((day: any) => {
      return filteredData.some((filteredDay: DailyData) => filteredDay.date === day.date);
    });

    // Sort by date for proper line chart display
    const sortedCompliance = filteredCompliance.sort((a, b) => parseLocalYMD(a.date).getTime() - parseLocalYMD(b.date).getTime());
    
    // Prepare data for line chart
    const labels = sortedCompliance.map(day => {
      const date = parseLocalYMD(day.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    const calorieData = sortedCompliance.map(day => day.calories);
    
    // Get target ranges
    const targetRanges = patientData.compliance_analysis.target_ranges;
    const upperTarget = Array(sortedCompliance.length).fill(targetRanges.calorie_max);
    const lowerTarget = Array(sortedCompliance.length).fill(targetRanges.calorie_min);
    
    return {
      labels,
      datasets: [
        {
          label: 'Daily Calorie Intake',
          data: calorieData,
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderWidth: 3,
          fill: false,
          tension: 0.2,
          pointBackgroundColor: sortedCompliance.map(day => {
            switch(day.calorie_status) {
              case 'within_target': return 'rgba(75, 192, 192, 1)';
              case 'above_target': return 'rgba(255, 99, 132, 1)';
              case 'below_target': return 'rgba(255, 206, 86, 1)';
              default: return 'rgba(54, 162, 235, 1)';
            }
          }),
          pointBorderColor: 'rgba(255, 255, 255, 1)',
          pointBorderWidth: 2,
          pointRadius: 6,
        },
        {
          label: 'Upper Target',
          data: upperTarget,
          borderColor: 'rgba(255, 99, 132, 0.8)',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0,
        },
        {
          label: 'Lower Target',
          data: lowerTarget,
          borderColor: 'rgba(255, 206, 86, 0.8)',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0,
        }
      ]
    };
  };

  const handleDownloadCSV = async () => {
    console.log('🔥 Download CSV clicked!');
    console.log('Patient data available:', !!patientData);
    console.log('Download ready:', patientData?.download_ready);
    
    // Remove the download_ready check - we'll fetch fresh data anyway
    if (!patientData) {
      console.error('No patient data available');
      return;
    }

    try {
      console.log('📡 Fetching fresh data for download...');
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/patient/${encodeURIComponent(patientId!)}/details?days=${analysisPeriod}&include_download_data=true`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('📡 Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📦 Downloaded data keys:', Object.keys(data));
        console.log('📦 Historical data available:', !!data.historical_data);
        console.log('📦 Daily data available:', !!data.historical_data?.daily_data);
        console.log('📦 Daily data count:', data.historical_data?.daily_data?.length || 0);
        
        // Convert to CSV format
        const csvData = [];
        csvData.push(['Date', 'Food Name', 'Quantity', 'Calories', 'Protein (g)', 'Carbohydrates (g)', 'Fat (g)', 'Fiber (g)', 'Sodium (mg)', 'Sugar (g)']);

        let totalMeals = 0;
        if (data.historical_data?.daily_data) {
          data.historical_data.daily_data.forEach((day: any) => {
            if (day.meals && day.meals.length > 0) {
              day.meals.forEach((meal: any) => {
                csvData.push([
                  day.date,
                  meal.food_name || 'Unknown',
                  meal.quantity || 0,
                  meal.calories || 0,
                  meal.protein || 0,
                  meal.carbohydrates || 0,
                  meal.fat || 0,
                  meal.fiber || 0,
                  meal.sodium || 0,
                  meal.sugar || 0
                ]);
                totalMeals++;
              });
            }
          });
        }
        
        console.log('📊 Total meals processed:', totalMeals);
        console.log('📊 CSV rows:', csvData.length);

        if (csvData.length <= 1) {
          alert('No meal data available to download. Please ensure you have logged meals in the selected time period.');
          setDownloadMenuAnchor(null);
          return;
        }

        const csvContent = csvData.map(row => row.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `${patientData.patient_info.user_name.replace(/\s+/g, '_')}_nutrition_history.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('✅ CSV download completed!');
      } else {
        console.error('❌ API response not OK:', response.status, response.statusText);
        alert('Failed to fetch data for download. Please try again.');
      }
    } catch (error) {
      console.error('❌ Error downloading CSV:', error);
      alert('Error occurred while downloading. Please try again.');
    }
    setDownloadMenuAnchor(null);
  };

  const handleDownloadExcel = () => {
    // For now, we'll download as CSV since implementing Excel requires additional libraries
    handleDownloadCSV();
  };

  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Nutritional Breakdown - Current vs Target',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  const doughnutChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: true,
        text: 'Calorie Target Compliance',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
    },
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={2} sx={{ p: 4 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
          <Box display="flex" gap={2}>
            <Button variant="contained" onClick={() => navigate('/admin/pias-corner')}>
              Back to Patient List
            </Button>
            <Button variant="outlined" onClick={fetchPatientDetails}>
              Retry
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  if (!patientData) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="warning">No patient data available</Alert>
      </Container>
    );
  }

  const { patient_info, analysis_period, nutritional_averages, compliance_analysis, insights, recommendations } = patientData;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center">
            <IconButton onClick={() => navigate('/admin/pias-corner?tab=5')} sx={{ mr: 2 }}>
              <ArrowBack />
            </IconButton>
            <Person sx={{ mr: 1, color: 'primary.main', fontSize: 32 }} />
            <Box>
              <Typography variant="h4" fontWeight="bold">
                {patient_info.user_name}
              </Typography>
              <Box display="flex" alignItems="center" gap={1} mt={1}>
                {patient_info.is_diabetic && (
                  <Chip label="Diabetic" color="secondary" size="small" />
                )}
                <Chip label={patient_info.medical_condition} color="info" size="small" />
                {patient_info.registration_code && (
                  <Chip label={patient_info.registration_code} variant="outlined" size="small" />
                )}
              </Box>
            </Box>
          </Box>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={(e) => setDownloadMenuAnchor(e.currentTarget)}
            >
              Download History
            </Button>
            <Menu
              anchorEl={downloadMenuAnchor}
              open={Boolean(downloadMenuAnchor)}
              onClose={() => setDownloadMenuAnchor(null)}
            >
              <MenuItem onClick={handleDownloadCSV}>Download as CSV</MenuItem>
              <MenuItem onClick={handleDownloadExcel}>Download as Excel</MenuItem>
            </Menu>
          </Box>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="center">
              <CalendarToday sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">Analysis Period</Typography>
                <Typography variant="h6">{analysis_period.days} Days</Typography>
                <Typography variant="caption" color="text.secondary">
                  {analysis_period.start_date} to {analysis_period.end_date}
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="center">
              <Assessment sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">Data Coverage</Typography>
                <Typography variant="h6">{analysis_period.days_with_data} Days</Typography>
                <Typography variant="caption" color="text.secondary">
                  {analysis_period.total_records} food records
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="center">
              <LocalHospital sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">Compliance Rate</Typography>
                <Typography variant="h6">
                  {compliance_analysis.calorie_target_compliance_rate?.toFixed(1) ?? '0.0'}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Calorie target adherence
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
        
        {/* Personal Progress Section - for severely under-eating patients */}
        {compliance_analysis.personal_progress && (
          <>
            <Divider sx={{ my: 2 }} />
            <Alert 
              severity={compliance_analysis.personal_progress.score >= 50 ? "success" : "warning"}
              sx={{ mb: 2 }}
            >
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                🌟 Personal Progress Tracking
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="body2" color="text.secondary">Progress Score</Typography>
                  <Typography variant="h6" color={compliance_analysis.personal_progress.score >= 50 ? "success.main" : "warning.main"}>
                    {compliance_analysis.personal_progress.score}%
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="body2" color="text.secondary">Average Intake</Typography>
                  <Typography variant="h6">
                    {compliance_analysis.personal_progress.avg_daily_calories} cal/day
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="body2" color="text.secondary">Recent Trend</Typography>
                  <Typography 
                    variant="h6" 
                    color={compliance_analysis.personal_progress.is_improving ? "success.main" : "text.primary"}
                  >
                    {compliance_analysis.personal_progress.is_improving ? "📈" : "📊"} 
                    {compliance_analysis.personal_progress.improvement_trend > 0 ? "+" : ""}
                    {compliance_analysis.personal_progress.improvement_trend} cal
                  </Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">Recent vs Early</Typography>
                  <Typography variant="body2">
                    {compliance_analysis.personal_progress.recent_average} vs {compliance_analysis.personal_progress.early_average} cal
                  </Typography>
                </Grid>
              </Grid>
              <Typography variant="body1" sx={{ mt: 2, fontStyle: 'italic' }}>
                {compliance_analysis.personal_progress.encouragement_message}
              </Typography>
            </Alert>
          </>
        )}
      </Paper>

      {/* Charts Section */}
      <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            📊 Nutritional Analysis & Compliance
          </Typography>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Time Period</InputLabel>
            <Select
              value={chartTimePeriod}
              label="Time Period"
              onChange={handleTimePeriodChange}
            >
              {timePeriodOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        
        <Grid container spacing={3}>
          {/* Combined Bar Graph */}
          <Grid item xs={12} lg={8}>
            <Card elevation={2}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                  Nutritional Breakdown - Current vs Target
                </Typography>
                <Box height={400}>
                  <Bar data={generateNutritionalBarChart()} options={barChartOptions} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Compliance Chart */}
          <Grid item xs={12} lg={4}>
            <Card elevation={2}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                  Calorie Intake Trend
                </Typography>
                <Box height={400}>
                  <Line 
                    data={generateComplianceChart()} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                          title: {
                            display: true,
                            text: 'Calories'
                          }
                        },
                        x: {
                          title: {
                            display: true,
                            text: 'Date'
                          }
                        }
                      },
                      plugins: {
                        legend: {
                          display: true,
                          position: 'top' as const
                        },
                        tooltip: {
                          mode: 'index' as const,
                          intersect: false
                        }
                      },
                      interaction: {
                        mode: 'nearest' as const,
                        axis: 'x' as const,
                        intersect: false
                      }
                    }} 
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Nutritional Averages */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="bold">
            📊 Daily Nutritional Averages ({timePeriodOptions.find(opt => opt.value === chartTimePeriod)?.label})
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="primary.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="primary.dark">
                  {(() => {
                    const filteredData = getFilteredData();
                    const avgCalories = filteredData.length > 0 
                      ? filteredData.reduce((sum: number, day: DailyData) => sum + day.total_calories, 0) / filteredData.length 
                      : 0;
                    return Math.round(avgCalories);
                  })()}
                </Typography>
                <Typography variant="caption" color="primary.dark">Calories</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="secondary.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="secondary.dark">
                  {(() => {
                    const filteredData = getFilteredData();
                    const avgProtein = filteredData.length > 0 
                      ? filteredData.reduce((sum: number, day: DailyData) => sum + day.total_protein, 0) / filteredData.length 
                      : 0;
                    return avgProtein.toFixed(1);
                  })()}g
                </Typography>
                <Typography variant="caption" color="secondary.dark">Protein</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="warning.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="warning.dark">
                  {(() => {
                    const filteredData = getFilteredData();
                    const avgCarbs = filteredData.length > 0 
                      ? filteredData.reduce((sum: number, day: DailyData) => sum + day.total_carbs, 0) / filteredData.length 
                      : 0;
                    return avgCarbs.toFixed(1);
                  })()}g
                </Typography>
                <Typography variant="caption" color="warning.dark">Carbohydrates</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="success.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="success.dark">
                  {(() => {
                    const filteredData = getFilteredData();
                    const avgFat = filteredData.length > 0 
                      ? filteredData.reduce((sum: number, day: DailyData) => sum + day.total_fat, 0) / filteredData.length 
                      : 0;
                    return avgFat.toFixed(1);
                  })()}g
                </Typography>
                <Typography variant="caption" color="success.dark">Fat</Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* AI Medical Advice Panel */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <Psychology sx={{ mr: 1, color: 'primary.main', fontSize: 28 }} />
            <Typography variant="h6" fontWeight="bold">
              🤖 AI Medical Advice
            </Typography>
            {llmAdviceLoading && (
              <CircularProgress size={20} sx={{ ml: 2 }} />
            )}
          </Box>
          
          {llmAdviceLoading ? (
            <Box display="flex" alignItems="center" justifyContent="center" minHeight="200px">
              <Box textAlign="center">
                <CircularProgress size={40} sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Generating AI-powered medical recommendations...
                </Typography>
              </Box>
            </Box>
          ) : llmAdviceError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="bold">Failed to load AI advice</Typography>
              <Typography variant="body2">{llmAdviceError}</Typography>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={fetchLLMAdvice} 
                sx={{ mt: 1 }}
              >
                Retry
              </Button>
            </Alert>
          ) : llmAdviceData ? (
            <Box>
              {/* Data Summary */}
              <Box mb={3} p={2} bgcolor="grey.50" borderRadius={1}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">Analysis Period</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {llmAdviceData.analysis_summary.analysis_period_days} days
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">Food Records</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {llmAdviceData.analysis_summary.total_food_records} entries
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">Avg Daily Calories</Typography>
                    <Typography variant="body2" fontWeight="bold" color={
                      llmAdviceData.analysis_summary.avg_daily_calories < 1200 ? 'error.main' :
                      llmAdviceData.analysis_summary.avg_daily_calories > 2500 ? 'warning.main' : 'success.main'
                    }>
                      {llmAdviceData.analysis_summary.avg_daily_calories.toFixed(0)} kcal
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">Data Quality</Typography>
                    <Chip 
                      label={llmAdviceData.data_availability === 'sufficient' ? 'Sufficient' : 'Limited'} 
                      color={llmAdviceData.data_availability === 'sufficient' ? 'success' : 'warning'}
                      size="small"
                    />
                  </Grid>
                </Grid>
              </Box>

              {/* Concerning Patterns */}
              {llmAdviceData.analysis_summary.concerning_patterns && (
                <Box mb={3}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                    ⚠️ Concerning Patterns Identified
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center" p={1} bgcolor="error.light" borderRadius={1}>
                        <Typography variant="h6" fontWeight="bold" color="error.dark">
                          {llmAdviceData.analysis_summary.concerning_patterns.high_calorie_days}
                        </Typography>
                        <Typography variant="caption" color="error.dark">High Calorie Days</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center" p={1} bgcolor="warning.light" borderRadius={1}>
                        <Typography variant="h6" fontWeight="bold" color="warning.dark">
                          {llmAdviceData.analysis_summary.concerning_patterns.low_calorie_days}
                        </Typography>
                        <Typography variant="caption" color="warning.dark">Low Calorie Days</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center" p={1} bgcolor="info.light" borderRadius={1}>
                        <Typography variant="h6" fontWeight="bold" color="info.dark">
                          {llmAdviceData.analysis_summary.concerning_patterns.high_sodium_days}
                        </Typography>
                        <Typography variant="caption" color="info.dark">High Sodium Days</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center" p={1} bgcolor="secondary.light" borderRadius={1}>
                        <Typography variant="h6" fontWeight="bold" color="secondary.dark">
                          {llmAdviceData.analysis_summary.concerning_patterns.low_fiber_days}
                        </Typography>
                        <Typography variant="caption" color="secondary.dark">Low Fiber Days</Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              )}

              {/* AI Medical Advice Content */}
              <Box>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  🩺 Medical Assessment & Recommendations
                </Typography>
                <Paper 
                  elevation={1} 
                  sx={{ 
                    p: 3, 
                    bgcolor: 'background.paper',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2
                  }}
                >
                  {formatAIRecommendations(llmAdviceData.llm_advice)}
                </Paper>
                
                <Box mt={2} display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption" color="text.secondary">
                    Generated: {new Date(llmAdviceData.generated_at).toLocaleString()}
                  </Typography>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    onClick={fetchLLMAdvice}
                    startIcon={<Psychology />}
                  >
                    Refresh Analysis
                  </Button>
                </Box>
              </Box>
            </Box>
          ) : (
            <Alert severity="info">
              <Typography variant="body2">
                AI medical advice will appear here once patient data is analyzed.
              </Typography>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Insights and Recommendations */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                💡 Medical Insights
              </Typography>
              {insights.length > 0 ? (
                insights.map((insight, index) => (
                  <Alert key={index} severity="info" sx={{ mb: 1 }}>
                    {insight}
                  </Alert>
                ))
              ) : (
                <Typography color="text.secondary">No specific insights identified</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                📝 Recommendations
              </Typography>
              {recommendations.length > 0 ? (
                recommendations.map((recommendation, index) => (
                  <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                    {recommendation}
                  </Alert>
                ))
              ) : (
                <Typography color="text.secondary">No specific recommendations at this time</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default PatientDetails;