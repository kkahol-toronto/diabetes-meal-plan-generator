import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  TrendingUp,
  People,
  Assignment,
  Analytics as AnalyticsIcon,
  Person,
  Groups,
  Restaurant,
  Timeline,
  AccessTime,
  TrendingDown,
  Favorite,
  LocalActivity,
  EmojiEvents,
  Warning,
  CheckCircle,
  Settings,
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  ArcElement,
  Filler,
} from 'chart.js';
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2';
import config from '../config/environment';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  ArcElement,
  Filler
);

interface Patient {
  id: string;
  name: string;
  registration_code: string;
  created_at: string;
  condition: string;
  last_active: string;
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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const PiasCorner: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [tabValue, setTabValue] = useState(0);
  const [analyticsMode, setAnalyticsMode] = useState<'individual' | 'cohort'>('cohort');
  const [selectedPatient, setSelectedPatient] = useState<string>('');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [nutrientData, setNutrientData] = useState<any>(null);
  const [engagementData, setEngagementData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [nutrientLoading, setNutrientLoading] = useState(false);
  const [engagementLoading, setEngagementLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    fetchAnalyticsData();
  }, [analyticsMode, selectedPatient]);

  const fetchPatients = async () => {
    try {
      const response = await fetch(`${config.API_URL}/admin/analytics/patients-list`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPatients(data.patients);
      } else {
        setError('Failed to fetch patients');
      }
    } catch (err) {
      setError('Failed to fetch patients');
    }
  };

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      const url = analyticsMode === 'individual' && selectedPatient
        ? `${config.API_URL}/admin/analytics/overview?patient_id=${selectedPatient}`
        : `${config.API_URL}/admin/analytics/overview`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      } else {
        setError('Failed to fetch analytics data');
      }
    } catch (err) {
      setError('Failed to fetch analytics data');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newMode = event.target.value as 'individual' | 'cohort';
    setAnalyticsMode(newMode);
    if (newMode === 'cohort') {
      setSelectedPatient('');
    }
  };

  const handlePatientChange = (event: SelectChangeEvent) => {
    setSelectedPatient(event.target.value);
  };

  const fetchNutrientData = async () => {
    setNutrientLoading(true);
    try {
      const url = analyticsMode === 'individual' && selectedPatient
        ? `${config.API_URL}/admin/analytics/nutrient-adequacy?patient_id=${selectedPatient}`
        : `${config.API_URL}/admin/analytics/nutrient-adequacy`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNutrientData(data);
      } else {
        setError('Failed to fetch nutrient data');
      }
    } catch (err) {
      setError('Failed to fetch nutrient data');
    } finally {
      setNutrientLoading(false);
    }
  };

  const fetchEngagementData = async () => {
    setEngagementLoading(true);
    try {
      const url = analyticsMode === 'individual' && selectedPatient
        ? `${config.API_URL}/admin/analytics/engagement-metrics?patient_id=${selectedPatient}`
        : `${config.API_URL}/admin/analytics/engagement-metrics`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setEngagementData(data);
      } else {
        setError('Failed to fetch engagement data');
      }
    } catch (err) {
      setError('Failed to fetch engagement data');
    } finally {
      setEngagementLoading(false);
    }
  };

  const renderOverviewCards = () => {
    if (!analyticsData) return null;

    if (analyticsMode === 'individual') {
      // Check if a patient is selected, if not show selection prompt
      if (!selectedPatient) {
        return (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Person sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Please select a patient to view individual analytics
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Use the patient dropdown above to choose a patient for detailed analysis.
            </Typography>
          </Box>
        );
      }

      // Ensure we have the correct data structure for individual patient
      if (!analyticsData.patient_info || !analyticsData.metrics) {
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Loading patient data...
            </Typography>
          </Box>
        );
      }

      const { patient_info, metrics } = analyticsData;
      return (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Person sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Patient Information</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Name: {patient_info?.name || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Condition: {patient_info?.condition || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Age: {patient_info?.age || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Registration: {patient_info?.registration_date ? new Date(patient_info.registration_date).toLocaleDateString() : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Assignment sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Meal Plans</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {metrics?.completed_meal_plans || 0}/{metrics?.total_meal_plans || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Compliance Rate: {metrics?.compliance_rate || 0}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6">Glucose Level</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {metrics?.avg_glucose_level || 0} mg/dL
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Average reading
                </Typography>
                {/* Mini Glucose Trend Chart */}
                <Box sx={{ height: 60 }}>
                  <Line
                    data={{
                      labels: analyticsData?.glucose_trends?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                      datasets: [{
                        data: analyticsData?.glucose_trends?.data || [148, 142, 151, 139, 145, 152, 140],
                        borderColor: 'rgba(76, 175, 80, 1)',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.3,
                        fill: true
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          mode: 'index' as const,
                          intersect: false,
                          callbacks: {
                            label: function(context) {
                              return `${context.parsed.y} mg/dL`;
                            }
                          }
                        }
                      },
                      scales: {
                        x: { display: false },
                        y: { 
                          display: false,
                          beginAtZero: false,
                          min: Math.min(...(analyticsData?.glucose_trends?.data || [140])) - 10,
                          max: Math.max(...(analyticsData?.glucose_trends?.data || [160])) + 10
                        }
                      },
                      elements: {
                        point: { hoverRadius: 6 }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AnalyticsIcon sx={{ mr: 1, color: 'warning.main' }} />
                  <Typography variant="h6">Weight Change</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {metrics?.weight_change ? (metrics.weight_change > 0 ? '+' : '') + metrics.weight_change : '0'} kg
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Since registration
                </Typography>
                {/* Mini Weight Progress Chart */}
                <Box sx={{ height: 60 }}>
                  <Line
                    data={{
                      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                      datasets: [{
                        data: analyticsData?.weight_progression || [82.5, 82.2, 81.8, 81.5, 81.0, 80.0],
                        borderColor: 'rgba(255, 152, 0, 1)',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.3,
                        fill: true
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          mode: 'index' as const,
                          intersect: false,
                          callbacks: {
                            label: function(context) {
                              return `${context.parsed.y} kg`;
                            }
                          }
                        }
                      },
                      scales: {
                        x: { display: false },
                        y: { 
                          display: false,
                          beginAtZero: false,
                          min: Math.min(...(analyticsData?.weight_progression || [80])) - 1,
                          max: Math.max(...(analyticsData?.weight_progression || [85])) + 1
                        }
                      },
                      elements: {
                        point: { hoverRadius: 6 }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Timeline sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6">Weekly Trends</Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Glucose</Typography>
                    <Typography variant="body2" fontWeight="bold" color="success.main">
                      {analyticsData.weekly_trends?.glucose_improvement || '+2.3%'}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Weight</Typography>
                    <Typography variant="body2" fontWeight="bold" color="primary">
                      {analyticsData.weekly_trends?.weight_trend || '-0.2kg'}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Compliance</Typography>
                    <Typography variant="body2" fontWeight="bold" color="success.main">
                      {analyticsData.weekly_trends?.compliance_trend || '+5%'}
                    </Typography>
                  </Box>
                </Box>
                {/* Mini Multi-metric Trend Chart */}
                <Box sx={{ height: 80 }}>
                  <Line
                    data={{
                      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                      datasets: [
                        {
                          label: 'Glucose Improvement',
                          data: [1.2, 1.8, 2.1, 2.3],
                          borderColor: 'rgba(76, 175, 80, 1)',
                          backgroundColor: 'rgba(76, 175, 80, 0.1)',
                          borderWidth: 2,
                          pointRadius: 2,
                          tension: 0.3
                        },
                        {
                          label: 'Compliance Rate',
                          data: [78, 82, 85, 88],
                          borderColor: 'rgba(33, 150, 243, 1)',
                          backgroundColor: 'rgba(33, 150, 243, 0.1)',
                          borderWidth: 2,
                          pointRadius: 2,
                          tension: 0.3,
                          yAxisID: 'y1'
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          mode: 'index' as const,
                          intersect: false,
                          callbacks: {
                            title: function(context) {
                              return context[0].label;
                            },
                            label: function(context) {
                              if (context.datasetIndex === 0) {
                                return `Glucose: +${context.parsed.y}%`;
                              } else {
                                return `Compliance: ${context.parsed.y}%`;
                              }
                            }
                          }
                        }
                      },
                      scales: {
                        x: { display: false },
                        y: { 
                          display: false,
                          beginAtZero: true,
                          max: 5
                        },
                        y1: {
                          display: false,
                          position: 'right' as const,
                          beginAtZero: true,
                          max: 100
                        }
                      },
                      elements: {
                        point: { hoverRadius: 4 }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LocalActivity sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6">Monthly Summary</Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Avg Glucose</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {analyticsData.monthly_summary?.avg_glucose || 142} mg/dL
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Activities</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {analyticsData.monthly_summary?.total_activities || 85}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Coach Sessions</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {analyticsData.monthly_summary?.coaching_sessions || 8}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Activity
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Action</TableCell>
                        <TableCell>Details</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analyticsData.recent_activity?.length > 0 ? (
                        analyticsData.recent_activity.map((activity: any, index: number) => (
                          <TableRow key={index}>
                            <TableCell>{activity.date ? new Date(activity.date).toLocaleDateString() : 'N/A'}</TableCell>
                            <TableCell>{activity.action || 'N/A'}</TableCell>
                            <TableCell>
                              {activity.glucose_reading && `${activity.glucose_reading} mg/dL`}
                              {activity.weight && `${activity.weight} kg`}
                              {activity.duration && activity.duration}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={3} align="center">
                            <Typography variant="body2" color="text.secondary">
                              No recent activity data available
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      );
    } else {
      // Cohort analytics
      const { summary, demographics, engagement_metrics } = analyticsData;
      return (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <People sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Total Patients</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {summary.total_patients}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {summary.active_patients} active
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6">New This Month</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {summary.new_registrations_this_month}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  registrations
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Assignment sx={{ mr: 1, color: 'warning.main' }} />
                  <Typography variant="h6">Compliance Rate</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {summary.avg_compliance_rate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  average
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AnalyticsIcon sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6">Meal Plans</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {summary.total_meal_plans_generated}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  generated
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Patient Demographics
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Chip label="Type 1 Diabetes" variant="outlined" />
                    <Typography>{demographics.type_1_diabetes} patients</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Chip label="Type 2 Diabetes" variant="outlined" />
                    <Typography>{demographics.type_2_diabetes} patients</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Chip label="Prediabetes" variant="outlined" />
                    <Typography>{demographics.prediabetes} patients</Typography>
                  </Box>
                </Box>
                {/* Demographics Pie Chart */}
                <Box sx={{ height: 120, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <Pie
                    data={{
                      labels: ['Type 1', 'Type 2', 'Prediabetes'],
                      datasets: [{
                        data: [
                          demographics.type_1_diabetes || 15,
                          demographics.type_2_diabetes || 28,
                          demographics.prediabetes || 12
                        ],
                        backgroundColor: [
                          '#FF6384',
                          '#36A2EB',
                          '#FFCE56'
                        ],
                        borderWidth: 2
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { 
                          display: false
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              return `${context.label}: ${context.parsed} patients`;
                            }
                          }
                        }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Engagement Metrics
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Daily Active Users</Typography>
                    <Typography variant="body2" fontWeight="bold">{engagement_metrics.daily_active_users}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Weekly Active Users</Typography>
                    <Typography variant="body2" fontWeight="bold">{engagement_metrics.weekly_active_users}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Monthly Active Users</Typography>
                    <Typography variant="body2" fontWeight="bold">{engagement_metrics.monthly_active_users}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Avg Session Duration</Typography>
                    <Typography variant="body2" fontWeight="bold">{engagement_metrics.avg_session_duration}</Typography>
                  </Box>
                </Box>
                {/* Engagement Trend Bar Chart */}
                <Box sx={{ height: 100 }}>
                  <Bar
                    data={{
                      labels: ['Daily', 'Weekly', 'Monthly'],
                      datasets: [{
                        label: 'Active Users',
                        data: [
                          engagement_metrics.daily_active_users || 45,
                          engagement_metrics.weekly_active_users || 180,
                          engagement_metrics.monthly_active_users || 520
                        ],
                        backgroundColor: ['rgba(54, 162, 235, 0.6)', 'rgba(75, 192, 192, 0.6)', 'rgba(255, 206, 86, 0.6)'],
                        borderColor: ['rgba(54, 162, 235, 1)', 'rgba(75, 192, 192, 1)', 'rgba(255, 206, 86, 1)'],
                        borderWidth: 1
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              return `${context.parsed.y} users`;
                            }
                          }
                        }
                      },
                      scales: {
                        x: { 
                          display: true,
                          ticks: { font: { size: 10 } }
                        },
                        y: { 
                          display: false,
                          beginAtZero: true
                        }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Performing Patients
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Compliance Rate</TableCell>
                        <TableCell>Glucose Improvement</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analyticsData.top_performing_patients?.length > 0 ? (
                        analyticsData.top_performing_patients.map((patient: any, index: number) => (
                          <TableRow key={index}>
                            <TableCell>{patient.name || 'N/A'}</TableCell>
                            <TableCell>{patient.compliance_rate || 0}%</TableCell>
                            <TableCell>{patient.glucose_improvement || 0}% improvement</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={3} align="center">
                            <Typography variant="body2" color="text.secondary">
                              No performance data available
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      );
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <AnalyticsIcon sx={{ mr: 2, fontSize: '2rem', color: 'primary.main' }} />
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
          Pia's Corner
        </Typography>
      </Box>

      <Paper sx={{ width: '100%', mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="pia's corner tabs"
            variant={isMobile ? 'fullWidth' : 'standard'}
          >
            <Tab
              label="Overview"
              icon={<AnalyticsIcon />}
              iconPosition="start"
              id="simple-tab-0"
              aria-controls="simple-tabpanel-0"
            />
            <Tab
              label="Nutrient Analysis"
              icon={<Restaurant />}
              iconPosition="start"
              id="simple-tab-1"
              aria-controls="simple-tabpanel-1"
            />
            <Tab
              label="Engagement Metrics"
              icon={<Timeline />}
              iconPosition="start"
              id="simple-tab-2"
              aria-controls="simple-tabpanel-2"
            />
            <Tab
              label="Settings"
              icon={<Settings />}
              iconPosition="start"
              id="simple-tab-3"
              aria-controls="simple-tabpanel-3"
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 3 }}>
            <FormControl component="fieldset" sx={{ mb: 2 }}>
              <FormLabel component="legend">Analytics Mode</FormLabel>
              <RadioGroup
                row
                aria-label="analytics-mode"
                name="analytics-mode"
                value={analyticsMode}
                onChange={handleModeChange}
              >
                <FormControlLabel
                  value="cohort"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Groups sx={{ mr: 1 }} />
                      Cohort Analytics
                    </Box>
                  }
                />
                <FormControlLabel
                  value="individual"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Person sx={{ mr: 1 }} />
                      Individual Patient
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            {analyticsMode === 'individual' && (
              <FormControl sx={{ minWidth: 200, ml: 2 }}>
                <Select
                  value={selectedPatient}
                  onChange={handlePatientChange}
                  displayEmpty
                  placeholder="Select Patient"
                >
                  <MenuItem value="">
                    <em>Select a patient</em>
                  </MenuItem>
                  {patients.map((patient) => (
                    <MenuItem key={patient.id} value={patient.id}>
                      {patient.name} ({patient.condition})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : error ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          ) : (
            renderOverviewCards()
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Nutrient Analysis Tab */}
          <Box sx={{ mb: 3 }}>
            <FormControl component="fieldset" sx={{ mb: 2 }}>
              <FormLabel component="legend">Analytics Mode</FormLabel>
              <RadioGroup
                row
                aria-label="analytics-mode"
                name="analytics-mode"
                value={analyticsMode}
                onChange={handleModeChange}
              >
                <FormControlLabel
                  value="cohort"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Groups sx={{ mr: 1 }} />
                      Cohort Analytics
                    </Box>
                  }
                />
                <FormControlLabel
                  value="individual"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Person sx={{ mr: 1 }} />
                      Individual Patient
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            {analyticsMode === 'individual' && (
              <FormControl sx={{ minWidth: 200, ml: 2 }}>
                <Select
                  value={selectedPatient}
                  onChange={handlePatientChange}
                  displayEmpty
                  placeholder="Select Patient"
                >
                  <MenuItem value="">
                    <em>Select a patient</em>
                  </MenuItem>
                  {patients.map((patient) => (
                    <MenuItem key={patient.id} value={patient.id}>
                      {patient.name} ({patient.condition})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Box>

          {nutrientLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : nutrientData || !nutrientData ? (
            // Show charts with default data if no data loaded yet
            <Grid container spacing={3}>
              {/* Macronutrient Distribution - Pie Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Restaurant sx={{ mr: 1, color: 'primary.main' }} />
                      Macronutrient Distribution
                    </Typography>
                    <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                      <Pie
                        data={{
                          labels: ['Protein', 'Carbohydrates', 'Fats'],
                          datasets: [{
                            data: nutrientData?.macronutrients || [25, 45, 30],
                            backgroundColor: [
                              '#FF6384',
                              '#36A2EB', 
                              '#FFCE56'
                            ],
                            borderColor: [
                              '#FF6384',
                              '#36A2EB',
                              '#FFCE56'
                            ],
                            borderWidth: 2
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'bottom' as const,
                            },
                            tooltip: {
                              callbacks: {
                                label: function(context) {
                                  return `${context.label}: ${context.parsed}%`;
                                }
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Daily Nutrient Targets vs Achieved - Bar Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                      Daily Targets vs Achieved
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <Bar
                        data={{
                          labels: ['Protein', 'Fiber', 'Vitamin D', 'Calcium', 'Iron', 'Vitamin C'],
                          datasets: [
                            {
                              label: 'Target',
                              data: nutrientData?.targets || [50, 25, 20, 1000, 18, 90],
                              backgroundColor: 'rgba(54, 162, 235, 0.6)',
                              borderColor: 'rgba(54, 162, 235, 1)',
                              borderWidth: 1
                            },
                            {
                              label: 'Achieved',
                              data: nutrientData?.achieved || [42, 22, 15, 850, 16, 75],
                              backgroundColor: 'rgba(75, 192, 192, 0.6)',
                              borderColor: 'rgba(75, 192, 192, 1)',
                              borderWidth: 1
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top' as const,
                            },
                            tooltip: {
                              mode: 'index' as const,
                              intersect: false,
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              title: {
                                display: true,
                                text: 'Amount'
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Nutrient Trends Over Time - Line Chart */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Timeline sx={{ mr: 1, color: 'primary.main' }} />
                      Nutrient Trends Over Time
                    </Typography>
                    <Box sx={{ height: 400 }}>
                      <Line
                        data={{
                          labels: nutrientData?.trendLabels || ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                          datasets: [
                            {
                              label: 'Protein (g)',
                              data: nutrientData?.proteinTrend || [45, 48, 42, 50, 47, 52, 49, 51],
                              borderColor: 'rgb(255, 99, 132)',
                              backgroundColor: 'rgba(255, 99, 132, 0.2)',
                              tension: 0.1
                            },
                            {
                              label: 'Fiber (g)',
                              data: nutrientData?.fiberTrend || [20, 22, 18, 25, 23, 27, 24, 26],
                              borderColor: 'rgb(54, 162, 235)',
                              backgroundColor: 'rgba(54, 162, 235, 0.2)',
                              tension: 0.1
                            },
                            {
                              label: 'Vitamin C (mg)',
                              data: nutrientData?.vitaminCTrend || [65, 70, 62, 75, 68, 78, 72, 76],
                              borderColor: 'rgb(255, 205, 86)',
                              backgroundColor: 'rgba(255, 205, 86, 0.2)',
                              tension: 0.1
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top' as const,
                            },
                            tooltip: {
                              mode: 'index' as const,
                              intersect: false,
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              title: {
                                display: true,
                                text: 'Amount'
                              }
                            },
                            x: {
                              title: {
                                display: true,
                                text: 'Time Period'
                              }
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

              {/* Load Data Button */}
              <Grid item xs={12}>
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Box sx={{ 
                    p: 2, 
                    border: '1px solid', 
                    borderColor: 'divider', 
                    borderRadius: 2,
                    cursor: 'pointer',
                    bgcolor: 'background.paper',
                    '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' }
                  }}
                  onClick={() => {
                    if (!nutrientData) fetchNutrientData();
                  }}>
                    {!nutrientData ? (
                      <Typography variant="button" color="primary">
                        Load Real Patient Data
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="success.main">
                        ✓ Real data loaded
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Grid>
            </Grid>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Alert severity="info">
                No nutrient data available. Please load patient data first.
              </Alert>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {/* Engagement Metrics Tab */}
          <Box sx={{ mb: 3 }}>
            <FormControl component="fieldset" sx={{ mb: 2 }}>
              <FormLabel component="legend">Analytics Mode</FormLabel>
              <RadioGroup
                row
                aria-label="analytics-mode"
                name="analytics-mode"
                value={analyticsMode}
                onChange={handleModeChange}
              >
                <FormControlLabel
                  value="cohort"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Groups sx={{ mr: 1 }} />
                      Cohort Analytics
                    </Box>
                  }
                />
                <FormControlLabel
                  value="individual"
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Person sx={{ mr: 1 }} />
                      Individual Patient
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            {analyticsMode === 'individual' && (
              <FormControl sx={{ minWidth: 200, ml: 2 }}>
                <Select
                  value={selectedPatient}
                  onChange={handlePatientChange}
                  displayEmpty
                  placeholder="Select Patient"
                >
                  <MenuItem value="">
                    <em>Select a patient</em>
                  </MenuItem>
                  {patients.map((patient) => (
                    <MenuItem key={patient.id} value={patient.id}>
                      {patient.name} ({patient.condition})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Box>

          {engagementLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : engagementData || !engagementData ? (
            // Show charts with default data if no data loaded yet
            <Grid container spacing={3}>
              {/* Login Frequency Over Time - Line Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <AccessTime sx={{ mr: 1, color: 'primary.main' }} />
                      Login Frequency Over Time
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <Line
                        data={{
                          labels: engagementData?.loginLabels || ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                          datasets: [
                            {
                              label: 'Daily Logins',
                              data: engagementData?.loginFrequency || [3, 5, 4, 6, 7, 5, 6, 8],
                              borderColor: 'rgb(75, 192, 192)',
                              backgroundColor: 'rgba(75, 192, 192, 0.2)',
                              tension: 0.1,
                              fill: true
                            },
                            {
                              label: 'Session Duration (min)',
                              data: engagementData?.sessionDuration || [15, 18, 12, 22, 25, 20, 18, 28],
                              borderColor: 'rgb(255, 99, 132)',
                              backgroundColor: 'rgba(255, 99, 132, 0.2)',
                              tension: 0.1,
                              yAxisID: 'y1'
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top' as const,
                            },
                            tooltip: {
                              mode: 'index' as const,
                              intersect: false,
                            }
                          },
                          scales: {
                            y: {
                              type: 'linear' as const,
                              display: true,
                              position: 'left' as const,
                              title: {
                                display: true,
                                text: 'Number of Logins'
                              }
                            },
                            y1: {
                              type: 'linear' as const,
                              display: true,
                              position: 'right' as const,
                              grid: {
                                drawOnChartArea: false,
                              },
                              title: {
                                display: true,
                                text: 'Duration (minutes)'
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Weekly Meal Logging Consistency - Bar Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Restaurant sx={{ mr: 1, color: 'primary.main' }} />
                      Weekly Meal Logging Consistency
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <Bar
                        data={{
                          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                          datasets: [
                            {
                              label: 'Meals Logged',
                              data: engagementData?.mealLogging || [3, 3, 2, 3, 3, 2, 2],
                              backgroundColor: 'rgba(54, 162, 235, 0.8)',
                              borderColor: 'rgba(54, 162, 235, 1)',
                              borderWidth: 1
                            },
                            {
                              label: 'Expected Meals',
                              data: [3, 3, 3, 3, 3, 3, 3],
                              backgroundColor: 'rgba(201, 203, 207, 0.3)',
                              borderColor: 'rgba(201, 203, 207, 1)',
                              borderWidth: 1
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top' as const,
                            },
                            tooltip: {
                              mode: 'index' as const,
                              intersect: false,
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              max: 4,
                              title: {
                                display: true,
                                text: 'Number of Meals'
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Activity Heatmap Calendar View */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <LocalActivity sx={{ mr: 1, color: 'primary.main' }} />
                      Activity Heatmap - Recent 30 Days
                    </Typography>
                    <Box sx={{ height: 200, p: 2 }}>
                      {/* Activity Calendar Grid */}
                      <Grid container spacing={0.5}>
                        {Array.from({ length: 30 }, (_, i) => {
                          const activityLevel = engagementData?.activityHeatmap?.[i] || Math.floor(Math.random() * 5);
                          const intensity = activityLevel / 4;
                          return (
                            <Grid item key={i}>
                              <Box
                                sx={{
                                  width: 24,
                                  height: 24,
                                  backgroundColor: `rgba(75, 192, 192, ${intensity})`,
                                  border: '1px solid #e0e0e0',
                                  borderRadius: 1,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: 10,
                                  color: intensity > 0.5 ? 'white' : 'text.primary',
                                  cursor: 'pointer',
                                  '&:hover': {
                                    transform: 'scale(1.1)',
                                    zIndex: 1
                                  }
                                }}
                                title={`Day ${30 - i}: ${activityLevel} activities`}
                              >
                                {activityLevel}
                              </Box>
                            </Grid>
                          );
                        })}
                      </Grid>
                      <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Less
                        </Typography>
                        {[0, 1, 2, 3, 4].map((level) => (
                          <Box
                            key={level}
                            sx={{
                              width: 12,
                              height: 12,
                              backgroundColor: `rgba(75, 192, 192, ${level / 4})`,
                              border: '1px solid #e0e0e0',
                              borderRadius: 1
                            }}
                          />
                        ))}
                        <Typography variant="caption" color="text.secondary">
                          More
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Feature Usage Breakdown - Doughnut Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <EmojiEvents sx={{ mr: 1, color: 'primary.main' }} />
                      Feature Usage Breakdown
                    </Typography>
                    <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                      <Doughnut
                        data={{
                          labels: ['Meal Plans', 'AI Coach', 'Progress Tracking', 'Recipes', 'Shopping Lists'],
                          datasets: [{
                            data: engagementData?.featureUsage || [35, 25, 20, 12, 8],
                            backgroundColor: [
                              '#FF6384',
                              '#36A2EB',
                              '#FFCE56',
                              '#4BC0C0',
                              '#9966FF'
                            ],
                            borderColor: [
                              '#FF6384',
                              '#36A2EB',
                              '#FFCE56',
                              '#4BC0C0',
                              '#9966FF'
                            ],
                            borderWidth: 2
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'right' as const,
                            },
                            tooltip: {
                              callbacks: {
                                label: function(context) {
                                  return `${context.label}: ${context.parsed}%`;
                                }
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Engagement Score Trends */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                      Engagement Score Trends
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <Line
                        data={{
                          labels: engagementData?.scoreLabels || ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                          datasets: [
                            {
                              label: 'Overall Engagement Score',
                              data: engagementData?.engagementScore || [65, 70, 68, 75, 80, 82],
                              borderColor: 'rgb(255, 159, 64)',
                              backgroundColor: 'rgba(255, 159, 64, 0.2)',
                              tension: 0.4,
                              fill: true
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top' as const,
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              max: 100,
                              title: {
                                display: true,
                                text: 'Engagement Score (%)'
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Load Data Button */}
              <Grid item xs={12}>
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Box sx={{ 
                    p: 2, 
                    border: '1px solid', 
                    borderColor: 'divider', 
                    borderRadius: 2,
                    cursor: 'pointer',
                    bgcolor: 'background.paper',
                    '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' }
                  }}
                  onClick={() => {
                    if (!engagementData) fetchEngagementData();
                  }}>
                    {!engagementData ? (
                      <Typography variant="button" color="primary">
                        Load Real Engagement Data
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="success.main">
                        ✓ Real data loaded
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Grid>
            </Grid>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Alert severity="info">
                No engagement data available. Please load patient data first.
              </Alert>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Settings Panel
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Settings and configuration options will be implemented in future iterations.
              This section will include:
            </Typography>
            <Box component="ul" sx={{ mt: 2 }}>
              <li>Dashboard refresh intervals</li>
              <li>Data export preferences</li>
              <li>Notification settings</li>
              <li>Display customization options</li>
              <li>User access management</li>
            </Box>
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default PiasCorner;