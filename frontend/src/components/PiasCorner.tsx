import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Divider,
  Button,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TableChartIcon from '@mui/icons-material/TableChart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WarningIcon from '@mui/icons-material/Warning';
import RefreshIcon from '@mui/icons-material/Refresh';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
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
import { Bar, Pie, Line } from 'react-chartjs-2';
import config from '../config/environment';

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

// Types for the API response
interface PatientInfo {
  user_id: string;
  user_name: string;
}

// Engagement metrics interfaces
interface EngagementUser {
  user_id: string;
  user_name: string;
  total_logs: number;
  active_days: number;
  avg_logs_per_day: number;
  weekly_logs_avg: number;
  days_since_last_log: number;
  engagement_level: 'excellent' | 'good' | 'poor' | 'warning' | 'critical' | 'inactive';
  last_log_date: string | null;
}

interface DailyMetric {
  date: string;
  active_users: number;
  total_users: number;
  engagement_rate: number;
  day_of_week: string;
}

interface EngagementSummary {
  excellent: number;
  good: number;
  poor: number;
  warning: number;
  critical: number;
  inactive: number;
}

interface EngagementAlertsData {
  critical_users: PatientInfo[];
  warning_users: PatientInfo[];
  inactive_users: PatientInfo[];
}

interface EngagementMetricsData {
  total_registered_patients: number;
  total_registered_users: number;
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
    total_consumption_records: number;
  };
  daily_metrics: DailyMetric[];
  engagement_summary: EngagementSummary;
  engagement_trend: 'improving' | 'declining' | 'stable';
  user_engagement_details: EngagementUser[];
  alerts: EngagementAlertsData;
  recommendations: {
    immediate_followup: number;
    needs_encouragement: number;
    performing_well: number;
  };
  generated_at: string;
}

interface NutrientAdequacyData {
  cohort_size: number;
  total_registered_patients: number;
  total_registered_users: number;
  inactive_patients_count: number;
  inactive_patients: PatientInfo[];
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
    total_records_analyzed: number;
  };
  rda_compliance: {
    [nutrient: string]: {
      adequate?: { count: number; percentage: number };
      low?: { count: number; percentage: number };
      high?: { count: number; percentage: number };
    };
  };
  deficiency_analysis: {
    top_deficiencies: Array<{
      issue: string;
      affected_patients: number;
      percentage: number;
      severity: 'high' | 'medium' | 'low';
      recommendation: string;
    }>;
    summary: {
      patients_with_fiber_deficiency: number;
      patients_with_excess_sodium: number;
      patients_with_excess_sugar: number;
      patients_with_low_protein: number;
    };
  };
  cohort_averages: {
    daily_averages: {
      [nutrient: string]: number;
    };
    vs_rda: {
      fiber_deficit: number;
      sodium_excess: number;
      protein_status: string;
    };
  };
  recommendations: {
    priority_actions: string[];
    monitoring_focus: string[];
  };
  generated_at: string;
}

const PiasCorner: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<NutrientAdequacyData | null>(null);
  const [engagementData, setEngagementData] = useState<EngagementMetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [engagementLoading, setEngagementLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [engagementError, setEngagementError] = useState<string | null>(null);
  const [analysisPeriod, setAnalysisPeriod] = useState(30);

  const handleBackToAdmin = () => {
    navigate('/admin');
  };

  const fetchNutrientAdequacyData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/nutrient-adequacy?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch nutrient adequacy data');
      }

      const result: NutrientAdequacyData = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error fetching nutrient adequacy data:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [analysisPeriod]);

  const fetchEngagementMetrics = useCallback(async () => {
    try {
      setEngagementLoading(true);
      setEngagementError(null);
      
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/engagement-metrics?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch engagement metrics');
      }

      const result: EngagementMetricsData = await response.json();
      setEngagementData(result);
    } catch (err) {
      console.error('Error fetching engagement metrics:', err);
      setEngagementError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setEngagementLoading(false);
    }
  }, [analysisPeriod]);

  useEffect(() => {
    fetchNutrientAdequacyData();
    fetchEngagementMetrics();
  }, [analysisPeriod, fetchNutrientAdequacyData, fetchEngagementMetrics]);

  // Chart generation functions
  const generatePopulationAveragesChart = () => {
    if (!data) return null;

    const { daily_averages } = data.cohort_averages;
    const nutrients = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber', 'sodium', 'sugar'];
    const labels = nutrients.map(n => n.charAt(0).toUpperCase() + n.slice(1));
    const values = nutrients.map(n => daily_averages[n] || 0);

    return {
      labels,
      datasets: [
        {
          label: 'Cohort Daily Averages',
          data: values,
          backgroundColor: [
            '#FF6384', // Calories - red
            '#36A2EB', // Protein - blue
            '#FFCE56', // Carbs - yellow
            '#4BC0C0', // Fat - teal
            '#9966FF', // Fiber - purple
            '#FF9F40', // Sodium - orange
            '#FF6384'  // Sugar - pink
          ],
          borderColor: [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF',
            '#FF9F40',
            '#FF6384'
          ],
          borderWidth: 2
        }
      ]
    };
  };

  const generateComplianceHeatmapChart = () => {
    if (!data) return null;

    const { rda_compliance } = data;
    const nutrients = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber', 'sodium', 'sugar'];
    
    const adequateData = nutrients.map(nutrient => 
      rda_compliance[nutrient]?.adequate?.percentage || 0
    );
    const lowData = nutrients.map(nutrient => 
      rda_compliance[nutrient]?.low?.percentage || 0
    );
    const highData = nutrients.map(nutrient => 
      rda_compliance[nutrient]?.high?.percentage || 0
    );

    return {
      labels: nutrients.map(n => n.charAt(0).toUpperCase() + n.slice(1)),
      datasets: [
        {
          label: 'Adequate Intake (%)',
          data: adequateData,
          backgroundColor: '#4CAF50',
          borderColor: '#4CAF50',
          borderWidth: 1
        },
        {
          label: 'Low Intake (%)',
          data: lowData,
          backgroundColor: '#FF9800',
          borderColor: '#FF9800',
          borderWidth: 1
        },
        {
          label: 'High Intake (%)',
          data: highData,
          backgroundColor: '#F44336',
          borderColor: '#F44336',
          borderWidth: 1
        }
      ]
    };
  };

  // Chart options
  const getChartOptions = (title: string) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            size: 12
          }
        }
      },
      title: {
        display: true,
        text: title,
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.dataset.label || '';
            const value = context.parsed.y || context.parsed;
            return `${label}: ${typeof value === 'number' ? value.toFixed(1) : value}${title.includes('Compliance') ? '%' : ''}`;
          }
        }
      }
    },
    scales: title.includes('Compliance') ? {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function(value: any) {
            return value + '%';
          }
        }
      }
    } : undefined
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return '#f44336';
      case 'medium': return '#ff9800';
      case 'low': return '#4caf50';
      default: return '#757575';
    }
  };

  // Engagement chart generation functions
  const generateEngagementFunnelChart = () => {
    if (!engagementData) return null;

    const { engagement_summary, total_registered_users } = engagementData;

    // Calculate funnel stages: Onboarding → Daily Log → Trend
    const onboarded = total_registered_users;
    const activeLoggers = engagement_summary.excellent + engagement_summary.good + engagement_summary.poor;
    const trendingPositive = engagement_summary.excellent + engagement_summary.good;

    return {
      labels: ['Registered Patients', 'Active Loggers', 'Positive Trend'],
      datasets: [{
        label: 'Patient Engagement Funnel',
        data: [onboarded, activeLoggers, trendingPositive],
        backgroundColor: [
          '#2196F3', // Blue for registered
          '#4CAF50', // Green for active
          '#FF9800'  // Orange for trending
        ],
        borderColor: [
          '#1976D2',
          '#388E3C', 
          '#F57C00'
        ],
        borderWidth: 2
      }]
    };
  };

  const generateEngagementTimeSeriesChart = () => {
    if (!engagementData) return null;

    const { daily_metrics } = engagementData;
    
    // Prepare time series data
    const labels = daily_metrics.map(metric => {
      const date = new Date(metric.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    const activeUsersData = daily_metrics.map(metric => metric.active_users);
    const engagementRateData = daily_metrics.map(metric => metric.engagement_rate);

    return {
      labels,
      datasets: [
        {
          label: 'Active Users',
          data: activeUsersData,
          borderColor: '#2196F3',
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          fill: true,
          yAxisID: 'y',
          tension: 0.4
        },
        {
          label: 'Engagement Rate (%)',  
          data: engagementRateData,
          borderColor: '#4CAF50',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          fill: true,
          yAxisID: 'y1',
          tension: 0.4
        }
      ]
    };
  };

  const getEngagementTimeSeriesOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: { size: 12 }
        }
      },
      title: {
        display: true,
        text: 'Patient Engagement Over Time',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Active Users'
        },
        beginAtZero: true
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Engagement Rate (%)'
        },
        beginAtZero: true,
        max: 100,
        grid: {
          drawOnChartArea: false,
        },
        ticks: {
          callback: function(value: any) {
            return value + '%';
          }
        }
      }
    }
  });

  const getFunnelChartOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Patient Engagement Funnel',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const value = context.parsed.y || context.parsed;
            const percentage = engagementData ? 
              ((value / engagementData.total_registered_users) * 100).toFixed(1) : '0';
            return `${context.label}: ${value} patients (${percentage}%)`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Patients'
        }
      }
    }
  });



  if (loading || engagementLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Loading Pia's Corner Analytics...
          </Typography>
          <Typography variant="body2" sx={{ mt: 1, opacity: 0.7 }}>
            {loading && 'Loading nutrient data...'}
            {engagementLoading && ' Loading engagement metrics...'}
          </Typography>
        </Paper>
      </Container>
    );
  }

  if (error || engagementError) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Nutrient Data Error: {error}
            </Alert>
          )}
          {engagementError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Engagement Data Error: {engagementError}
            </Alert>
          )}
          <Button
            variant="contained"
            onClick={() => {
              fetchNutrientAdequacyData();
              fetchEngagementMetrics();
            }}
            sx={{ mr: 2 }}
          >
            Retry
          </Button>
        </Paper>
      </Container>
    );
  }

  const populationAveragesData = generatePopulationAveragesChart();
  const complianceHeatmapData = generateComplianceHeatmapChart();
  const engagementFunnelData = generateEngagementFunnelChart();
  const engagementTimeSeriesData = generateEngagementTimeSeriesChart();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={handleBackToAdmin}
              sx={{ minWidth: 'auto' }}
            >
              Back to Admin Panel
            </Button>
            <Typography variant="h4" component="h1">
              Pia's Corner
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Period</InputLabel>
              <Select
                value={analysisPeriod}
                label="Period"
                onChange={(e) => setAnalysisPeriod(Number(e.target.value))}
              >
                <MenuItem value={7}>7 Days</MenuItem>
                <MenuItem value={30}>30 Days</MenuItem>
                <MenuItem value={60}>60 Days</MenuItem>
                <MenuItem value={90}>90 Days</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchNutrientAdequacyData}
            >
              Refresh
            </Button>
          </Box>
        </Box>

        <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
          Patient Food Analysis & Risk Assessment Dashboard
        </Typography>

        {/* Quick Stats Summary */}
        <Stack direction="row" spacing={2} sx={{ mb: 4, flexWrap: 'wrap' }}>
          <Chip 
            icon={<AnalyticsIcon />}
            label={`${data?.cohort_size || 0} Active Patients`}
            color="primary"
            variant="outlined"
          />
          <Chip 
            label={`${data?.total_registered_patients || 0} Total Patients`}
            color="default"
            variant="outlined"
          />
          <Chip 
            icon={<TableChartIcon />}
            label={`${data?.analysis_period.total_records_analyzed || 0} Food Logs`}
            color="secondary"
            variant="outlined"
          />
          <Chip 
            label={`${data?.analysis_period.days || 0} Day Analysis`}
            variant="outlined"
          />
          {(data?.inactive_patients_count ?? 0) > 0 && (
            <Chip 
              icon={<WarningIcon />}
              label={`${data?.inactive_patients_count ?? 0} Inactive Patients`}
              color="warning"
              variant="outlined"
            />
          )}
        </Stack>

        <Divider sx={{ mb: 4 }} />

        {/* Main Content Grid */}
        <Grid container spacing={3}>
          {/* Charts Section */}
          <Grid item xs={12} lg={8}>
            <Grid container spacing={3}>
              {/* Population Averages Chart - Pie Chart */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6">
                        Population Nutrient Averages
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {populationAveragesData ? (
                        <Pie 
                          data={populationAveragesData} 
                          options={getChartOptions('Daily Averages Across Cohort')}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* RDA Compliance Heatmap - Bar Chart */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                      <Typography variant="h6">
                        RDA Compliance Levels
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {complianceHeatmapData ? (
                        <Bar 
                          data={complianceHeatmapData} 
                          options={getChartOptions('Compliance by Nutrient (%)')}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Population Averages - Bar Chart Alternative */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'info.main' }} />
                      <Typography variant="h6">
                        Detailed Nutrient Intake Analysis
                      </Typography>
                    </Box>
                    <Box sx={{ height: 300 }}>
                      {populationAveragesData ? (
                        <Bar 
                          data={populationAveragesData} 
                          options={getChartOptions('Average Daily Intake by Nutrient')}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Sidebar Section */}
          <Grid item xs={12} lg={4}>
            <Grid container spacing={3}>
              {/* Critical Deficiencies Alert */}
              <Grid item xs={12}>
                <Card elevation={2} sx={{ bgcolor: '#fff3e0' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <WarningIcon sx={{ mr: 1, color: 'warning.main' }} />
                      <Typography variant="h6" color="warning.main">
                        Top Deficiencies
                      </Typography>
                    </Box>
                    <List dense>
                      {data?.deficiency_analysis.top_deficiencies.slice(0, 4).map((deficiency, index) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <FiberManualRecordIcon 
                              sx={{ 
                                fontSize: 12, 
                                color: getSeverityColor(deficiency.severity)
                              }} 
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" fontWeight="medium">
                                  {deficiency.issue}
                                </Typography>
                                <Chip 
                                  label={`${deficiency.percentage}%`}
                                  size="small"
                                  sx={{ 
                                    bgcolor: getSeverityColor(deficiency.severity),
                                    color: 'white',
                                    fontSize: '0.75rem'
                                  }}
                                />
                              </Box>
                            }
                            secondary={
                              <Typography variant="caption" color="text.secondary">
                                {deficiency.affected_patients} patients affected
                              </Typography>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              {/* Cohort Statistics */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Cohort Statistics
                    </Typography>
                    <Stack spacing={2}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Registered Patients:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {data?.total_registered_patients}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Active Patients:</Typography>
                        <Typography variant="body2" fontWeight="bold" color="primary.main">
                          {data?.cohort_size}
                        </Typography>
                      </Box>
                      {(data?.inactive_patients_count ?? 0) > 0 && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Inactive Patients:</Typography>
                          <Typography variant="body2" fontWeight="bold" color="warning.main">
                            {data?.inactive_patients_count ?? 0}
                          </Typography>
                        </Box>
                      )}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Analysis Period:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {data?.analysis_period.days} days
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Food Records:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {data?.analysis_period.total_records_analyzed}
                        </Typography>
                      </Box>
                      <Divider />
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          Fiber Status:
                        </Typography>
                        <Typography variant="body2">
                          {(data?.cohort_averages?.vs_rda?.fiber_deficit ?? 0) > 0 
                            ? `${(data?.cohort_averages?.vs_rda?.fiber_deficit ?? 0).toFixed(1)}g deficit per day`
                            : 'Adequate intake'
                          }
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          Sodium Status:
                        </Typography>
                        <Typography variant="body2">
                          {(data?.cohort_averages?.vs_rda?.sodium_excess ?? 0) > 0 
                            ? `${(data?.cohort_averages?.vs_rda?.sodium_excess ?? 0).toFixed(0)}mg excess per day`
                            : 'Within limits'
                          }
                        </Typography>
                      </Box>
                      {data?.inactive_patients && data.inactive_patients.length > 0 && (
                        <>
                          <Divider />
                          <Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              Patients Missing Food Logs:
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {data.inactive_patients.slice(0, 3).map((patient, index) => (
                                <Typography key={index} variant="caption" color="warning.main">
                                  • {patient.user_name}
                                </Typography>
                              ))}
                              {data.inactive_patients.length > 3 && (
                                <Typography variant="caption" color="text.secondary">
                                  ... and {data.inactive_patients.length - 3} more
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Engagement Metrics Section */}
          <Grid item xs={12}>
            <Typography variant="h5" sx={{ mb: 3, mt: 4 }}>
              Patient Engagement Analytics
            </Typography>
            <Grid container spacing={3}>
              {/* Engagement Funnel Chart */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6">
                        Patient Engagement Funnel
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {engagementFunnelData ? (
                        <Bar 
                          data={engagementFunnelData} 
                          options={getFunnelChartOptions()}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No engagement data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Engagement Time Series Chart */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                      <Typography variant="h6">
                        Engagement Trends Over Time
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {engagementTimeSeriesData ? (
                        <Line 
                          data={engagementTimeSeriesData} 
                          options={getEngagementTimeSeriesOptions()}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No engagement data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Engagement Summary Cards */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                      <TableChartIcon sx={{ mr: 1, color: 'info.main' }} />
                      <Typography variant="h6">
                        Engagement Summary
                      </Typography>
                    </Box>
                    {engagementData && (
                      <Grid container spacing={2}>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="success.main" fontWeight="bold">
                              {engagementData.engagement_summary.excellent}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Excellent
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="primary.main" fontWeight="bold">
                              {engagementData.engagement_summary.good}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Good
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="warning.main" fontWeight="bold">
                              {engagementData.engagement_summary.poor}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Poor
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="warning.main" fontWeight="bold">
                              {engagementData.engagement_summary.warning}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Warning
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="error.main" fontWeight="bold">
                              {engagementData.engagement_summary.critical}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Critical
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="text.secondary" fontWeight="bold">
                              {engagementData.engagement_summary.inactive}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Inactive
                            </Typography>
                          </Card>
                        </Grid>
                      </Grid>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Recommendations Section */}
          <Grid item xs={12}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <TableChartIcon sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6">
                    Clinical Recommendations
                  </Typography>
                </Box>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 2 }}>
                      Priority Actions
                    </Typography>
                    <List>
                      {data?.recommendations.priority_actions.map((action, index) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemIcon>
                            <Box 
                              sx={{ 
                                width: 24, 
                                height: 24, 
                                borderRadius: '50%', 
                                bgcolor: 'primary.main', 
                                color: 'white',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '0.75rem',
                                fontWeight: 'bold'
                              }}
                            >
                              {index + 1}
                            </Box>
                          </ListItemIcon>
                          <ListItemText 
                            primary={action}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 2 }}>
                      Monitoring Focus
                    </Typography>
                    <List>
                      {data?.recommendations.monitoring_focus.map((focus, index) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemIcon>
                            <AnalyticsIcon sx={{ color: 'secondary.main' }} />
                          </ListItemIcon>
                          <ListItemText 
                            primary={focus}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default PiasCorner;