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
  MenuItem
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
import { Bar, Doughnut } from 'react-chartjs-2';
import config from '../config/environment';

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
  compliance_timeline: Array<{
    date: string;
    calorie_status: string;
    nutrient_issues: string[];
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
}

interface PatientDetailsData {
  patient_info: PatientInfo;
  analysis_period: AnalysisPeriod;
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
  
  // LLM Advice state
  const [llmAdviceData, setLlmAdviceData] = useState<LLMAdviceData | null>(null);
  const [llmAdviceLoading, setLlmAdviceLoading] = useState(false);
  const [llmAdviceError, setLlmAdviceError] = useState<string | null>(null);

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

    const { categories, current_values, target_values } = patientData.bar_graph_data;

    return {
      labels: categories,
      datasets: [
        {
          label: 'Current Average',
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
    if (!patientData?.compliance_analysis) return { datasets: [] };

    const { days_within_calorie_target, days_above_target, days_below_target } = patientData.compliance_analysis;

    return {
      labels: ['Within Target', 'Above Target', 'Below Target'],
      datasets: [
        {
          data: [days_within_calorie_target, days_above_target, days_below_target],
          backgroundColor: [
            'rgba(75, 192, 192, 0.8)',
            'rgba(255, 99, 132, 0.8)',
            'rgba(255, 206, 86, 0.8)'
          ],
          borderColor: [
            'rgba(75, 192, 192, 1)',
            'rgba(255, 99, 132, 1)',
            'rgba(255, 206, 86, 1)'
          ],
          borderWidth: 2,
        }
      ]
    };
  };

  const handleDownloadCSV = async () => {
    if (!patientData?.download_ready) return;

    try {
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/patient/${encodeURIComponent(patientId!)}/details?days=${analysisPeriod}&include_download_data=true`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Convert to CSV format
        const csvData = [];
        csvData.push(['Date', 'Food Name', 'Quantity', 'Calories', 'Protein (g)', 'Carbohydrates (g)', 'Fat (g)', 'Fiber (g)', 'Sodium (mg)', 'Sugar (g)']);

        if (data.historical_data?.daily_data) {
          data.historical_data.daily_data.forEach((day: any) => {
            if (day.meals) {
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
              });
            }
          });
        }

        const csvContent = csvData.map(row => row.join(',')).join('\\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `${patientData.patient_info.user_name.replace(/\\s+/g, '_')}_nutrition_history.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      console.error('Error downloading CSV:', error);
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
            <IconButton onClick={() => navigate('/admin/pias-corner')} sx={{ mr: 2 }}>
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
                  {((compliance_analysis.days_within_calorie_target / compliance_analysis.total_days) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Calorie target adherence
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Combined Bar Graph */}
        <Grid item xs={12} lg={8}>
          <Card elevation={2}>
            <CardContent>
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
              <Box height={400}>
                <Doughnut data={generateComplianceChart()} options={doughnutChartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Nutritional Averages */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="bold">
            📊 Daily Nutritional Averages
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="primary.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="primary.dark">
                  {nutritional_averages.daily_avg_calories.toFixed(0)}
                </Typography>
                <Typography variant="caption" color="primary.dark">Calories</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="secondary.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="secondary.dark">
                  {nutritional_averages.daily_avg_protein.toFixed(1)}g
                </Typography>
                <Typography variant="caption" color="secondary.dark">Protein</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="warning.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="warning.dark">
                  {nutritional_averages.daily_avg_carbs.toFixed(1)}g
                </Typography>
                <Typography variant="caption" color="warning.dark">Carbohydrates</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center" p={2} bgcolor="success.light" borderRadius={1}>
                <Typography variant="h5" fontWeight="bold" color="success.dark">
                  {nutritional_averages.daily_avg_fat.toFixed(1)}g
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
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      whiteSpace: 'pre-wrap',
                      lineHeight: 1.7,
                      fontSize: '0.95rem'
                    }}
                  >
                    {llmAdviceData.llm_advice}
                  </Typography>
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