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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Divider,
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
  Button,
  TableSortLabel,
  Badge,
  IconButton,
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
  ReportProblem,
  Close,
  Save,
  Visibility,
  CalendarToday,
  NoteAdd,
  Email as EmailIcon,
  Check as CheckIcon,
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
import { Bar, Line, Pie, Doughnut, Scatter } from 'react-chartjs-2';
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
  const [clinicalAlertsData, setClinicalAlertsData] = useState<any>(null);
  const [behaviorClusteringData, setBehaviorClusteringData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [nutrientLoading, setNutrientLoading] = useState(false);
  const [engagementLoading, setEngagementLoading] = useState(false);
  const [clinicalAlertsLoading, setClinicalAlertsLoading] = useState(false);
  const [behaviorClusteringLoading, setBehaviorClusteringLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alertSortBy, setAlertSortBy] = useState<'severity' | 'date' | 'patient_name' | 'alert_type'>('severity');
  const [alertSortOrder, setAlertSortOrder] = useState<'asc' | 'desc'>('desc');
  const [alertFilter, setAlertFilter] = useState<'All' | 'Calories' | 'Nutrients' | 'Under-eating'>('All');
  const [patientModalOpen, setPatientModalOpen] = useState(false);
  const [selectedCluster, setSelectedCluster] = useState<any>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<any>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewAction, setReviewAction] = useState<'resolved' | 'monitoring' | 'escalated' | 'dismissed'>('resolved');
  const [reviewLoading, setReviewLoading] = useState(false);

  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    fetchAnalyticsData();
  }, [analyticsMode, selectedPatient]);

  useEffect(() => {
    // Reset nutrient data when switching modes or patients to avoid stale data
    setNutrientData(null);
    
    // Auto-fetch nutrient data when switching to individual mode with a selected patient
    // or when changing patients in individual mode, and we're on the nutrient analysis tab
    if (analyticsMode === 'individual' && selectedPatient && tabValue === 1 && !nutrientData) {
      setTimeout(() => {
        fetchNutrientData();
      }, 200);
    }
  }, [analyticsMode, selectedPatient, tabValue]);

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
    
    // If switching to nutrient analysis tab and we have a selected patient but no data, auto-load
    if (newValue === 1 && analyticsMode === 'individual' && selectedPatient && !nutrientData) {
      setTimeout(() => {
        fetchNutrientData();
      }, 100);
    }
    
    // Auto-load clinical alerts data when switching to that tab
    if (newValue === 3 && !clinicalAlertsData) {
      setTimeout(() => {
        fetchClinicalAlertsData();
      }, 100);
    }
    
    // Auto-load behavior clustering data when switching to that tab
    if (newValue === 4 && !behaviorClusteringData) {
      setTimeout(() => {
        fetchBehaviorClusteringData();
      }, 100);
    }
  };

  const handleModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newMode = event.target.value as 'individual' | 'cohort';
    setAnalyticsMode(newMode);
    // Reset all cached data when switching modes
    setNutrientData(null);
    setEngagementData(null);
    if (newMode === 'cohort') {
      setSelectedPatient('');
    }
  };

  const handlePatientChange = (event: SelectChangeEvent) => {
    setSelectedPatient(event.target.value);
    // Reset cached data when switching patients
    setNutrientData(null);
    setEngagementData(null);
    // The useEffect hook will handle auto-fetching the data
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

  const fetchClinicalAlertsData = async () => {
    setClinicalAlertsLoading(true);
    try {
      const response = await fetch(`${config.API_URL}/admin/analytics/clinical-alerts`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setClinicalAlertsData(data);
      } else {
        setError('Failed to fetch clinical alerts data');
      }
    } catch (err) {
      setError('Failed to fetch clinical alerts data');
    } finally {
      setClinicalAlertsLoading(false);
    }
  };

  const fetchBehaviorClusteringData = async () => {
    setBehaviorClusteringLoading(true);
    try {
      const response = await fetch(`${config.API_URL}/admin/analytics/behavior-clustering`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBehaviorClusteringData(data);
      } else {
        setError('Failed to fetch behavior clustering data');
      }
    } catch (err) {
      setError('Failed to fetch behavior clustering data');
    } finally {
      setBehaviorClusteringLoading(false);
    }
  };

  const handleViewPatients = (archetype: any) => {
    // Find patients in this cluster from the correlation data
    const clusterPatients = behaviorClusteringData.behavior_outcome_correlation
      .filter((patient: any) => patient.cluster === archetype.cluster_id);
    
    setSelectedCluster({
      ...archetype,
      patients: clusterPatients
    });
    setPatientModalOpen(true);
  };

  const handleReviewAlert = (alert: any) => {
    setSelectedAlert(alert);
    setReviewNotes('');
    setReviewAction('resolved');
    setReviewDialogOpen(true);
  };

  const handleCloseReviewDialog = () => {
    setReviewDialogOpen(false);
    setSelectedAlert(null);
    setReviewNotes('');
    setReviewAction('resolved');
  };

  const handleSubmitReview = async () => {
    if (!selectedAlert) return;
    
    setReviewLoading(true);
    try {
      const reviewData = {
        alert_id: selectedAlert.id,
        action: reviewAction,
        notes: reviewNotes,
        reviewed_by: 'current_admin', // In production, get from auth context
        reviewed_at: new Date().toISOString()
      };

      const response = await fetch(`${config.API_URL}/admin/analytics/review-alert`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reviewData)
      });

      if (response.ok) {
        // Update the local alert data to reflect the review
        if (clinicalAlertsData && clinicalAlertsData.active_alerts) {
          const updatedAlerts = clinicalAlertsData.active_alerts.map((alert: any) => 
            alert.id === selectedAlert.id 
              ? { ...alert, reviewed: true, review_status: reviewAction, review_notes: reviewNotes, reviewed_at: new Date().toISOString() }
              : alert
          );
          
          setClinicalAlertsData({
            ...clinicalAlertsData,
            active_alerts: updatedAlerts
          });
        }
        
        setError(null);
        handleCloseReviewDialog();
      } else {
        setError('Failed to submit alert review');
      }
    } catch (err) {
      setError('Failed to submit alert review');
    } finally {
      setReviewLoading(false);
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

          {/* Patient Compliance Distribution Chart */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Patient Compliance Distribution</Typography>
                </Box>
                <Box sx={{ height: 400, position: 'relative' }}>
                  {analyticsData.patient_compliance_distribution?.length > 0 ? (
                    <Bar
                      data={{
                        labels: analyticsData.patient_compliance_distribution.map((patient: any) => patient.name),
                        datasets: [{
                          label: 'Compliance Rate (%)',
                          data: analyticsData.patient_compliance_distribution.map((patient: any) => patient.compliance_rate),
                          backgroundColor: analyticsData.patient_compliance_distribution.map((patient: any) => {
                            const rate = patient.compliance_rate;
                            if (rate >= 75) return 'rgba(76, 175, 80, 0.8)'; // Green for high compliance
                            if (rate >= 50) return 'rgba(255, 193, 7, 0.8)'; // Yellow for medium compliance
                            return 'rgba(244, 67, 54, 0.8)'; // Red for low compliance
                          }),
                          borderColor: analyticsData.patient_compliance_distribution.map((patient: any) => {
                            const rate = patient.compliance_rate;
                            if (rate >= 75) return 'rgba(76, 175, 80, 1)';
                            if (rate >= 50) return 'rgba(255, 193, 7, 1)';
                            return 'rgba(244, 67, 54, 1)';
                          }),
                          borderWidth: 2,
                          hoverBackgroundColor: analyticsData.patient_compliance_distribution.map((patient: any) => {
                            const rate = patient.compliance_rate;
                            if (rate >= 75) return 'rgba(76, 175, 80, 0.9)';
                            if (rate >= 50) return 'rgba(255, 193, 7, 0.9)';
                            return 'rgba(244, 67, 54, 0.9)';
                          }),
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        onClick: (event, elements) => {
                          if (elements.length > 0) {
                            const clickedIndex = elements[0].index;
                            const clickedPatient = analyticsData.patient_compliance_distribution[clickedIndex];
                            if (clickedPatient?.patient_id) {
                              setAnalyticsMode('individual');
                              setSelectedPatient(clickedPatient.patient_id);
                            }
                          }
                        },
                        plugins: {
                          legend: {
                            display: false
                          },
                          tooltip: {
                            callbacks: {
                              title: function(context) {
                                const patientIndex = context[0].dataIndex;
                                const patient = analyticsData.patient_compliance_distribution[patientIndex];
                                return patient.name;
                              },
                              label: function(context) {
                                const patientIndex = context.dataIndex;
                                const patient = analyticsData.patient_compliance_distribution[patientIndex];
                                return [
                                  `Compliance Rate: ${patient.compliance_rate}%`,
                                  `Completed Plans: ${patient.completed_plans}/${patient.total_plans}`,
                                  'Click to view individual analytics'
                                ];
                              }
                            }
                          }
                        },
                        scales: {
                          x: {
                            display: true,
                            title: {
                              display: true,
                              text: 'Patients'
                            },
                            ticks: {
                              maxRotation: 45,
                              minRotation: 45
                            }
                          },
                          y: {
                            display: true,
                            beginAtZero: true,
                            max: 100,
                            title: {
                              display: true,
                              text: 'Compliance Rate (%)'
                            },
                            ticks: {
                              callback: function(value) {
                                return value + '%';
                              }
                            }
                          }
                        }
                      }}
                    />
                  ) : (
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      height: '100%',
                      color: 'text.secondary'
                    }}>
                      <TrendingDown sx={{ fontSize: 48, mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        No Compliance Data Available
                      </Typography>
                      <Typography variant="body2">
                        Patient compliance data will appear here once patients start using meal plans.
                      </Typography>
                    </Box>
                  )}
                </Box>
                
                {/* Legend */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom sx={{ textAlign: 'center' }}>
                    Compliance Thresholds: Green ≥75% (High) • Yellow 50-75% (Medium) • Red &lt;50% (Low)
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mt: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ 
                        width: 16, 
                        height: 16, 
                        backgroundColor: 'rgba(244, 67, 54, 0.8)', 
                        mr: 1, 
                        borderRadius: 1 
                      }} />
                      <Typography variant="body2">Low (&lt;50%)</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ 
                        width: 16, 
                        height: 16, 
                        backgroundColor: 'rgba(255, 193, 7, 0.8)', 
                        mr: 1, 
                        borderRadius: 1 
                      }} />
                      <Typography variant="body2">Medium (50-75%)</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ 
                        width: 16, 
                        height: 16, 
                        backgroundColor: 'rgba(76, 175, 80, 0.8)', 
                        mr: 1, 
                        borderRadius: 1 
                      }} />
                      <Typography variant="body2">High (&gt;75%)</Typography>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 1 }}>
                    Click on any bar to view individual patient analytics
                  </Typography>
                </Box>
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
              label="Clinical Alerts"
              icon={<ReportProblem />}
              iconPosition="start"
              id="simple-tab-3"
              aria-controls="simple-tabpanel-3"
            />
            <Tab
              label="Behavior Analysis"
              icon={<Groups />}
              iconPosition="start"
              id="simple-tab-4"
              aria-controls="simple-tabpanel-4"
            />
            <Tab
              label="Settings"
              icon={<Settings />}
              iconPosition="start"
              id="simple-tab-5"
              aria-controls="simple-tabpanel-5"
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
              {/* RDA Achievement Bar Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Restaurant sx={{ mr: 1, color: 'primary.main' }} />
                      {nutrientData?.mode === 'individual' ? 'Individual RDA Achievement' : 'RDA Achievement Rate'}
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <Bar
                        data={{
                          labels: ['Protein', 'Fiber', 'Vitamin D', 'Calcium', 'Iron', 'Vitamin C', 'Folate', 'Magnesium'],
                          datasets: [{
                            label: '% Patients Meeting RDA',
                            data: nutrientData?.rda_achievement ? [
                              nutrientData.rda_achievement.protein,
                              nutrientData.rda_achievement.fiber,
                              nutrientData.rda_achievement.vitamin_d,
                              nutrientData.rda_achievement.calcium,
                              nutrientData.rda_achievement.iron,
                              nutrientData.rda_achievement.vitamin_c,
                              nutrientData.rda_achievement.folate,
                              nutrientData.rda_achievement.magnesium
                            ] : analyticsMode === 'individual' 
                              ? [92, 72, 60, 85, 89, 87, 80, 76]  // Individual patient default
                              : [85, 45, 32, 67, 71, 89, 58, 63], // Cohort default
                            backgroundColor: function(context: any) {
                              const value = context.parsed.y;
                              if (value >= 80) return 'rgba(76, 175, 80, 0.8)'; // Green
                              if (value >= 60) return 'rgba(255, 193, 7, 0.8)'; // Yellow  
                              return 'rgba(244, 67, 54, 0.8)'; // Red
                            },
                            borderColor: function(context: any) {
                              const value = context.parsed.y;
                              if (value >= 80) return 'rgba(76, 175, 80, 1)';
                              if (value >= 60) return 'rgba(255, 193, 7, 1)';
                              return 'rgba(244, 67, 54, 1)';
                            },
                            borderWidth: 1
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
                                label: function(context: any) {
                                  if (nutrientData?.mode === 'individual') {
                                    return `${context.parsed.y}% of target achieved`;
                                  }
                                  return `${context.parsed.y}% of patients meet RDA`;
                                }
                              }
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              max: 100,
                              title: {
                                display: true,
                                text: nutrientData?.mode === 'individual' ? '% of Target Achieved' : '% of Patients Meeting RDA'
                              }
                            },
                            x: {
                              ticks: {
                                maxRotation: 45
                              }
                            }
                          }
                        }}
                        plugins={[{
                          id: 'rdaReferenceLine',
                          beforeDraw: (chart: any) => {
                            const ctx = chart.ctx;
                            const yAxis = chart.scales.y;
                            const xAxis = chart.scales.x;
                            const targetY = yAxis.getPixelForValue(80);
                            
                            ctx.save();
                            ctx.strokeStyle = 'rgba(244, 67, 54, 0.8)';
                            ctx.lineWidth = 2;
                            ctx.setLineDash([5, 5]);
                            ctx.beginPath();
                            ctx.moveTo(xAxis.left, targetY);
                            ctx.lineTo(xAxis.right, targetY);
                            ctx.stroke();
                            ctx.restore();
                          }
                        }]}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Top Deficiencies Pie Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Warning sx={{ mr: 1, color: 'primary.main' }} />
                      {nutrientData?.mode === 'individual' ? 'Individual Nutrient Deficiencies' : 'Most Common Deficiencies'}
                    </Typography>
                    <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                      <Pie
                        data={{
                          labels: nutrientData?.top_deficiencies?.map((d: any) => d.name) || (analyticsMode === 'individual' 
                            ? ['Low Vitamin D', 'Low Magnesium', 'Low Calcium', 'Low Folate']
                            : ['Low Fiber', 'Insufficient Vitamin D', 'Excess Sodium', 'Low Iron', 'Other']),
                          datasets: [{
                            data: nutrientData?.top_deficiencies?.map((d: any) => d.deficit_percentage || d.percentage) || (analyticsMode === 'individual' 
                              ? [40, 28, 25, 20]  // Individual patient deficiency percentages
                              : [35, 25, 20, 12, 8]), // Cohort deficiency percentages
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
                              position: 'bottom' as const,
                            },
                            tooltip: {
                              callbacks: {
                                label: function(context: any) {
                                  const deficiency = nutrientData?.top_deficiencies?.[context.dataIndex];
                                  if (deficiency) {
                                    if (nutrientData?.mode === 'individual') {
                                      return [
                                        `${context.label}: ${context.parsed}% below target`,
                                        `Current: ${deficiency.current_intake}`,
                                        `Target: ${deficiency.target_intake}`,
                                        `Deficit: ${deficiency.deficit}`
                                      ];
                                    } else {
                                      return `${context.label}: ${context.parsed}% (${deficiency.patients_affected} patients)`;
                                    }
                                  }
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

              {/* Nutrient Trends Over Time - Line Chart */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Timeline sx={{ mr: 1, color: 'primary.main' }} />
                      {nutrientData?.mode === 'individual' ? 'Individual Nutrient Trends (8 Weeks)' : 'Cohort Average Nutrient Trends (8 Weeks)'}
                    </Typography>
                    <Box sx={{ height: 400 }}>
                      <Line
                        data={{
                          labels: nutrientData?.trendLabels || ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                          datasets: [
                            {
                              label: 'Protein (g)',
                              data: nutrientData?.proteinTrend || (analyticsMode === 'individual' 
                                ? [80, 85, 82, 88, 92, 89, 95, 93]  // Individual improving trend
                                : [78, 79, 81, 83, 84, 86, 87, 89]), // Cohort gradual improvement
                              borderColor: 'rgb(255, 99, 132)',
                              backgroundColor: 'rgba(255, 99, 132, 0.2)',
                              tension: 0.1
                            },
                            {
                              label: 'Fiber (g)',
                              data: nutrientData?.fiberTrend || (analyticsMode === 'individual' 
                                ? [18, 19, 17, 21, 23, 25, 24, 26]  // Individual variable progress
                                : [20, 20.5, 21, 22, 22.5, 23, 23.5, 24]), // Cohort steady improvement
                              borderColor: 'rgb(54, 162, 235)',
                              backgroundColor: 'rgba(54, 162, 235, 0.2)',
                              tension: 0.1
                            },
                            {
                              label: 'Vitamin C (mg)',
                              data: nutrientData?.vitaminCTrend || (analyticsMode === 'individual' 
                                ? [70, 75, 68, 78, 82, 79, 85, 88]  // Individual strong improvement
                                : [68, 69, 71, 72, 74, 75, 76, 77]), // Cohort moderate improvement
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
                                text: nutrientData?.mode === 'individual' ? 'Individual Intake Amount' : 'Average Intake Amount'
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

              {/* Daily Compliance Heatmap */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <AccessTime sx={{ mr: 1, color: 'primary.main' }} />
                      {nutrientData?.mode === 'individual' ? 'Individual Daily Compliance (4 Weeks)' : 'Average Daily Compliance Heatmap (4 Weeks)'}
                    </Typography>
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'center',
                      p: 2
                    }}>
                      {/* Day labels */}
                      <Box sx={{ 
                        display: 'flex', 
                        mb: 1,
                        '& > div:first-of-type': { width: '80px' } // Space for week labels
                      }}>
                        <Box sx={{ width: '80px' }}></Box>
                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                          <Box 
                            key={day}
                            sx={{ 
                              width: '50px', 
                              textAlign: 'center', 
                              fontSize: '0.875rem',
                              fontWeight: 'medium',
                              color: 'text.secondary'
                            }}
                          >
                            {day}
                          </Box>
                        ))}
                      </Box>
                      
                      {/* Heatmap grid */}
                      {(nutrientData?.daily_compliance_heatmap || (analyticsMode === 'individual' ? [
                        [0.9, 0.85, 0.95, 0.88, 0.82, 0.75, 0.8],   // Individual patient higher compliance
                        [0.92, 0.87, 0.93, 0.85, 0.79, 0.78, 0.82],
                        [0.88, 0.91, 0.96, 0.90, 0.84, 0.73, 0.79],
                        [0.94, 0.89, 0.98, 0.92, 0.86, 0.71, 0.77]
                      ] : [
                        [0.8, 0.75, 0.9, 0.85, 0.78, 0.65, 0.7],     // Cohort average compliance
                        [0.82, 0.77, 0.88, 0.83, 0.76, 0.68, 0.72],
                        [0.85, 0.79, 0.91, 0.87, 0.74, 0.63, 0.69],
                        [0.87, 0.81, 0.93, 0.89, 0.72, 0.61, 0.67]
                      ])).map((week: number[], weekIndex: number) => (
                        <Box key={weekIndex} sx={{ display: 'flex', mb: 0.5 }}>
                          <Box sx={{ 
                            width: '80px', 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            fontSize: '0.875rem',
                            fontWeight: 'medium',
                            color: 'text.secondary'
                          }}>
                            Week {weekIndex + 1}
                          </Box>
                          {week.map((compliance: number, dayIndex: number) => {
                            const intensity = Math.max(0, Math.min(1, compliance));
                            const greenValue = Math.floor(255 * intensity);
                            const alpha = 0.3 + (intensity * 0.7);
                            
                            return (
                              <Box
                                key={`${weekIndex}-${dayIndex}`}
                                sx={{
                                  width: '50px',
                                  height: '40px',
                                  bgcolor: `rgba(76, 175, 80, ${alpha})`,
                                  border: '1px solid',
                                  borderColor: 'divider',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: '0.75rem',
                                  fontWeight: 'medium',
                                  color: intensity > 0.5 ? 'white' : 'text.primary',
                                  cursor: 'pointer',
                                  transition: 'all 0.2s ease',
                                  '&:hover': {
                                    transform: 'scale(1.05)',
                                    borderColor: 'primary.main',
                                    borderWidth: '2px'
                                  }
                                }}
                                title={`Week ${weekIndex + 1}, ${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dayIndex]}: ${Math.round(compliance * 100)}% ${nutrientData?.mode === 'individual' ? 'individual compliance' : 'average compliance'}`}
                              >
                                {Math.round(compliance * 100)}%
                              </Box>
                            );
                          })}
                        </Box>
                      ))}
                      
                      {/* Legend */}
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        mt: 2, 
                        gap: 1,
                        fontSize: '0.875rem'
                      }}>
                        <Typography variant="body2" color="text.secondary">
                          Compliance Level:
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Box sx={{ 
                            width: '16px', 
                            height: '16px', 
                            bgcolor: 'rgba(76, 175, 80, 0.3)',
                            border: '1px solid',
                            borderColor: 'divider'
                          }} />
                          <Typography variant="body2" color="text.secondary">Low</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Box sx={{ 
                            width: '16px', 
                            height: '16px', 
                            bgcolor: 'rgba(76, 175, 80, 0.7)',
                            border: '1px solid',
                            borderColor: 'divider'
                          }} />
                          <Typography variant="body2" color="text.secondary">Medium</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Box sx={{ 
                            width: '16px', 
                            height: '16px', 
                            bgcolor: 'rgba(76, 175, 80, 1)',
                            border: '1px solid',
                            borderColor: 'divider'
                          }} />
                          <Typography variant="body2" color="text.secondary">High</Typography>
                        </Box>
                      </Box>
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
                    if (!nutrientData && (analyticsMode !== 'individual' || selectedPatient)) {
                      fetchNutrientData();
                    }
                  }}>
                    {!nutrientData ? (
                      <Typography variant="button" color="primary">
                        {analyticsMode === 'individual' && selectedPatient 
                          ? `Load ${patients.find(p => p.id === selectedPatient)?.name || 'Patient'} Data`
                          : analyticsMode === 'individual' 
                            ? 'Select Patient First'
                            : 'Load Cohort Data'
                        }
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="success.main">
                        ✓ {nutrientData?.mode === 'individual' ? 'Individual' : 'Cohort'} data loaded
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
            // Enhanced Engagement Metrics with Funnel Analysis and Missed Log Tracking
            <Grid container spacing={3}>
              {/* Engagement Funnel Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Timeline sx={{ mr: 1, color: 'primary.main' }} />
                      Engagement Funnel Analysis
                    </Typography>
                    <Box sx={{ height: 350, p: 2, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      {/* Custom Funnel Chart */}
                      {engagementData?.funnel_analysis?.stages?.map((stage: any, index: number) => {
                        const isBottleneck = engagementData?.funnel_analysis?.bottlenecks?.includes(stage.name);
                        const width = Math.max(20, stage.percentage); // Minimum width for visibility
                        return (
                          <Box key={index} sx={{ mb: 1, cursor: 'pointer', '&:hover': { opacity: 0.8 } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                              <Typography variant="body2" sx={{ minWidth: 120, fontSize: '0.875rem' }}>
                                {stage.name}
                              </Typography>
                              <Box 
                                sx={{ 
                                  width: `${width}%`,
                                  height: 32,
                                  background: isBottleneck 
                                    ? 'linear-gradient(45deg, #f44336, #ff7961)'
                                    : index === 0 
                                      ? 'linear-gradient(45deg, #4caf50, #81c784)'
                                      : 'linear-gradient(45deg, #2196f3, #64b5f6)',
                                  borderRadius: 1,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: 'white',
                                  fontWeight: 'bold',
                                  fontSize: '0.75rem',
                                  position: 'relative',
                                  ml: 1
                                }}
                              >
                                {stage.count} ({stage.percentage}%)
                                {stage.conversion_rate && (
                                  <Typography 
                                    variant="caption" 
                                    sx={{ 
                                      position: 'absolute', 
                                      right: -30, 
                                      top: -15, 
                                      bgcolor: isBottleneck ? 'error.main' : 'success.main',
                                      color: 'white',
                                      px: 0.5,
                                      borderRadius: 0.5,
                                      fontSize: '0.625rem'
                                    }}
                                  >
                                    {stage.conversion_rate}%
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                          </Box>
                        );
                      }) || (
                        // Default funnel data
                        [
                          { name: 'Registration', count: 120, percentage: 100, conversion_rate: null },
                          { name: 'First Login', count: 98, percentage: 82, conversion_rate: 82 },
                          { name: 'Daily Logging', count: 75, percentage: 63, conversion_rate: 77 },
                          { name: 'Trend Reporting', count: 52, percentage: 43, conversion_rate: 69 },
                          { name: 'Long-term Engagement', count: 38, percentage: 32, conversion_rate: 73 }
                        ].map((stage, index) => {
                          const isBottleneck = ['First Login', 'Daily Logging'].includes(stage.name);
                          const width = Math.max(20, stage.percentage);
                          return (
                            <Box key={index} sx={{ mb: 1, cursor: 'pointer', '&:hover': { opacity: 0.8 } }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                                <Typography variant="body2" sx={{ minWidth: 120, fontSize: '0.875rem' }}>
                                  {stage.name}
                                </Typography>
                                <Box 
                                  sx={{ 
                                    width: `${width}%`,
                                    height: 32,
                                    background: isBottleneck 
                                      ? 'linear-gradient(45deg, #f44336, #ff7961)'
                                      : index === 0 
                                        ? 'linear-gradient(45deg, #4caf50, #81c784)'
                                        : 'linear-gradient(45deg, #2196f3, #64b5f6)',
                                    borderRadius: 1,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                    fontWeight: 'bold',
                                    fontSize: '0.75rem',
                                    position: 'relative',
                                    ml: 1
                                  }}
                                >
                                  {stage.count} ({stage.percentage}%)
                                  {stage.conversion_rate && (
                                    <Typography 
                                      variant="caption" 
                                      sx={{ 
                                        position: 'absolute', 
                                        right: -30, 
                                        top: -15, 
                                        bgcolor: isBottleneck ? 'error.main' : 'success.main',
                                        color: 'white',
                                        px: 0.5,
                                        borderRadius: 0.5,
                                        fontSize: '0.625rem'
                                      }}
                                    >
                                      {stage.conversion_rate}%
                                    </Typography>
                                  )}
                                </Box>
                              </Box>
                            </Box>
                          );
                        })
                      )}
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
                        Click stages to view patient details • Red indicates bottlenecks
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Missed Logs Calendar Heatmap */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <CalendarToday sx={{ mr: 1, color: 'primary.main' }} />
                      Missed Logs Calendar (Last 30 Days)
                    </Typography>
                    <Box sx={{ height: 350, p: 1 }}>
                      {/* Calendar Header */}
                      <Box sx={{ display: 'flex', gap: 0.5, mb: 1 }}>
                        {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, i) => (
                          <Typography key={i} variant="caption" sx={{ width: 30, textAlign: 'center', fontWeight: 'bold' }}>
                            {day}
                          </Typography>
                        ))}
                      </Box>
                      
                      {/* Calendar Grid */}
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxWidth: 220 }}>
                        {(engagementData?.missed_logs_analysis?.calendar_heatmap || Array.from({ length: 30 }, (_, i) => {
                          const totalPatients = 45;
                          const missedCount = Math.floor(Math.random() * 15) + 2;
                          return {
                            date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                            missed_count: missedCount,
                            total_patients: totalPatients,
                            percentage: Math.round((missedCount / totalPatients) * 100 * 10) / 10
                          };
                        })).map((day: any, index: number) => {
                          const intensity = day.percentage / 40; // Normalize to 0-1 range (40% max for color)
                          const isWeekend = new Date(day.date).getDay() % 6 === 0;
                          return (
                            <Box
                              key={index}
                              sx={{
                                width: 28,
                                height: 28,
                                backgroundColor: intensity > 0.7 
                                  ? '#d32f2f' 
                                  : intensity > 0.4 
                                    ? '#ff9800' 
                                    : intensity > 0.2 
                                      ? '#ffeb3b' 
                                      : '#4caf50',
                                border: '1px solid #e0e0e0',
                                borderRadius: 1,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '0.625rem',
                                color: intensity > 0.4 ? 'white' : 'black',
                                cursor: 'pointer',
                                '&:hover': {
                                  transform: 'scale(1.1)',
                                  zIndex: 1,
                                  boxShadow: 2
                                }
                              }}
                              title={`${day.date}: ${day.missed_count}/${day.total_patients} patients missed logs (${day.percentage}%)`}
                            >
                              {day.missed_count}
                            </Box>
                          );
                        })}
                      </Box>
                      
                      {/* Legend */}
                      <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Less
                        </Typography>
                        {[0, 0.2, 0.4, 0.6, 0.8].map((level, i) => (
                          <Box
                            key={i}
                            sx={{
                              width: 12,
                              height: 12,
                              backgroundColor: level > 0.6 
                                ? '#d32f2f' 
                                : level > 0.3 
                                  ? '#ff9800' 
                                  : level > 0.1 
                                    ? '#ffeb3b' 
                                    : '#4caf50',
                              border: '1px solid #e0e0e0',
                              borderRadius: 1
                            }}
                          />
                        ))}
                        <Typography variant="caption" color="text.secondary">
                          More
                        </Typography>
                      </Box>

                      {/* Weekly Pattern Summary */}
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 1 }}>
                          Weekly Pattern:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {Object.entries(engagementData?.missed_logs_analysis?.weekly_patterns || {
                            monday: 15, tuesday: 12, wednesday: 18, thursday: 14,
                            friday: 22, saturday: 28, sunday: 31
                          }).map(([day, count]) => (
                            <Typography key={day} variant="caption" sx={{ 
                              bgcolor: (count as number) > 25 ? 'error.light' : 'success.light',
                              color: (count as number) > 25 ? 'error.dark' : 'success.dark',
                              px: 0.5,
                              borderRadius: 0.5,
                              fontSize: '0.6rem'
                            }}>
                              {`${day.slice(0, 3)}: ${count}`}
                            </Typography>
                          ))}
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Irregular Reporting Alerts Table */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Warning sx={{ mr: 1, color: 'primary.main' }} />
                      Irregular Reporting Alerts
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Patient</TableCell>
                            <TableCell align="right">Days Since Last Log</TableCell>
                            <TableCell align="right">Avg Gap (Days)</TableCell>
                            <TableCell align="right">Consistency Score</TableCell>
                            <TableCell align="center">Risk Level</TableCell>
                            <TableCell align="center">Actions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {(engagementData?.irregular_reporting || [
                            { patient_id: "p001", patient_name: "John Smith", days_since_last_log: 8, avg_gap_days: 3.2, consistency_score: 45, risk_level: "high", last_login: "2024-01-07" },
                            { patient_id: "p002", patient_name: "Sarah Johnson", days_since_last_log: 4, avg_gap_days: 2.1, consistency_score: 72, risk_level: "medium", last_login: "2024-01-11" },
                            { patient_id: "p003", patient_name: "Michael Brown", days_since_last_log: 15, avg_gap_days: 5.8, consistency_score: 28, risk_level: "critical", last_login: "2023-12-31" },
                            { patient_id: "p004", patient_name: "Emma Davis", days_since_last_log: 6, avg_gap_days: 2.8, consistency_score: 68, risk_level: "medium", last_login: "2024-01-09" },
                            { patient_id: "p005", patient_name: "David Wilson", days_since_last_log: 12, avg_gap_days: 4.5, consistency_score: 35, risk_level: "critical", last_login: "2024-01-03" }
                          ]).map((patient: any) => (
                            <TableRow key={patient.patient_id} hover>
                              <TableCell>
                                <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                  {patient.patient_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  ID: {patient.patient_id}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Typography variant="body2" sx={{ 
                                  color: patient.days_since_last_log > 10 ? 'error.main' : patient.days_since_last_log > 5 ? 'warning.main' : 'text.primary',
                                  fontWeight: patient.days_since_last_log > 7 ? 'bold' : 'normal'
                                }}>
                                  {patient.days_since_last_log}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">{patient.avg_gap_days}</TableCell>
                              <TableCell align="right">
                                <Typography variant="body2" sx={{ 
                                  color: patient.consistency_score < 40 ? 'error.main' : patient.consistency_score < 70 ? 'warning.main' : 'success.main'
                                }}>
                                  {patient.consistency_score}%
                                </Typography>
                              </TableCell>
                              <TableCell align="center">
                                <Chip 
                                  label={patient.risk_level.toUpperCase()}
                                  size="small"
                                  color={patient.risk_level === 'critical' ? 'error' : patient.risk_level === 'high' ? 'warning' : 'default'}
                                  variant={patient.risk_level === 'critical' ? 'filled' : 'outlined'}
                                />
                              </TableCell>
                              <TableCell align="center">
                                <Box sx={{ display: 'flex', gap: 0.5 }}>
                                  <IconButton size="small" color="primary" title="Send Reminder">
                                    <EmailIcon sx={{ fontSize: 16 }} />
                                  </IconButton>
                                  <IconButton size="small" color="info" title="View Profile">
                                    <Person sx={{ fontSize: 16 }} />
                                  </IconButton>
                                  <IconButton size="small" color="success" title="Mark Contacted">
                                    <CheckIcon sx={{ fontSize: 16 }} />
                                  </IconButton>
                                </Box>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Enhanced Engagement Time-Series */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                        <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                        Enhanced Engagement Trends
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button size="small" variant="outlined">Weekly</Button>
                        <Button size="small" variant="contained">Monthly</Button>
                      </Box>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      <Line
                        data={{
                          labels: engagementData?.engagement_timeseries?.labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                          datasets: [
                            {
                              label: 'Daily Actives ↗️',
                              data: engagementData?.engagement_timeseries?.daily_actives?.data || [35, 38, 33, 41, 39, 42],
                              borderColor: '#4caf50',
                              backgroundColor: 'rgba(76, 175, 80, 0.1)',
                              tension: 0.3,
                              yAxisID: 'y'
                            },
                            {
                              label: 'Session Duration (min) ↗️',
                              data: engagementData?.engagement_timeseries?.session_duration?.data || [15.2, 16.1, 14.8, 17.3, 18.1, 18.9],
                              borderColor: '#2196f3',
                              backgroundColor: 'rgba(33, 150, 243, 0.1)',
                              tension: 0.3,
                              yAxisID: 'y1'
                            },
                            {
                              label: 'Logging Consistency (%) ↗️',
                              data: engagementData?.engagement_timeseries?.logging_consistency?.data || [68, 72, 65, 75, 78, 81],
                              borderColor: '#ff9800',
                              backgroundColor: 'rgba(255, 152, 0, 0.1)',
                              tension: 0.3,
                              yAxisID: 'y2'
                            },
                            {
                              label: 'Feature Usage (%) →',
                              data: engagementData?.engagement_timeseries?.feature_usage?.data || [85, 87, 83, 89, 91, 93],
                              borderColor: '#9c27b0',
                              backgroundColor: 'rgba(156, 39, 176, 0.1)',
                              tension: 0.3,
                              yAxisID: 'y2'
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
                                text: 'Daily Active Users'
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
                                text: 'Session Duration (min)'
                              }
                            },
                            y2: {
                              type: 'linear' as const,
                              display: false,
                              min: 0,
                              max: 100
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Compact Activity Heatmap */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <LocalActivity sx={{ mr: 1, color: 'primary.main' }} />
                      Activity Heatmap - Recent 30 Days
                    </Typography>
                    <Box sx={{ height: 120, p: 1 }}>
                      <Grid container spacing={0.5}>
                        {Array.from({ length: 30 }, (_, i) => {
                          const activityLevel = engagementData?.activityHeatmap?.[i] || Math.floor(Math.random() * 5);
                          const intensity = activityLevel / 4;
                          return (
                            <Grid item key={i}>
                              <Box
                                sx={{
                                  width: 20,
                                  height: 20,
                                  backgroundColor: `rgba(75, 192, 192, ${intensity})`,
                                  border: '1px solid #e0e0e0',
                                  borderRadius: 1,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: 8,
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
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Feature Usage Breakdown - Compact */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <EmojiEvents sx={{ mr: 1, color: 'primary.main' }} />
                      Feature Usage Breakdown
                    </Typography>
                    <Box sx={{ height: 200, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
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
          {/* Clinical Alerts Tab */}
          {clinicalAlertsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : clinicalAlertsData ? (
            <Grid container spacing={3}>
              {/* Summary Cards */}
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ 
                  bgcolor: 'error.light', 
                  color: 'error.contrastText',
                  position: 'relative',
                  overflow: 'visible'
                }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Warning sx={{ mr: 1, fontSize: '2rem' }} />
                      <Typography variant="h6">Total Active Alerts</Typography>
                    </Box>
                    <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {clinicalAlertsData?.summary?.total_active_alerts || 0}
                    </Typography>
                    <Typography variant="body2">
                      requiring attention
                    </Typography>
                    {/* Pulse animation for critical alerts */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        width: 12,
                        height: 12,
                        bgcolor: 'error.main',
                        borderRadius: '50%',
                        animation: 'pulse 2s infinite',
                        '@keyframes pulse': {
                          '0%': { opacity: 1, transform: 'scale(1)' },
                          '50%': { opacity: 0.5, transform: 'scale(1.2)' },
                          '100%': { opacity: 1, transform: 'scale(1)' }
                        }
                      }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingDown sx={{ mr: 1, fontSize: '2rem' }} />
                      <Typography variant="h6">Extreme Intake</Typography>
                    </Box>
                    <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {clinicalAlertsData?.summary?.extreme_intake_patients || 0}
                    </Typography>
                    <Typography variant="body2">
                      patients affected
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ bgcolor: 'info.light', color: 'info.contrastText' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, fontSize: '2rem' }} />
                      <Typography variant="h6">Nutrient Spikes</Typography>
                    </Box>
                    <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {clinicalAlertsData?.summary?.nutrient_spike_alerts || 0}
                    </Typography>
                    <Typography variant="body2">
                      spike events
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CheckCircle sx={{ mr: 1, fontSize: '2rem' }} />
                      <Typography variant="h6">Resolved This Week</Typography>
                    </Box>
                    <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {clinicalAlertsData?.summary?.resolved_this_week || 0}
                    </Typography>
                    <Typography variant="body2">
                      interventions successful
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Calorie Outliers Box Plot */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingDown sx={{ mr: 1, color: 'warning.main' }} />
                      Calorie Distribution & Outliers
                    </Typography>
                    <Box sx={{ height: 350, position: 'relative' }}>
                      {/* Custom Box Plot Implementation */}
                      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <Box sx={{ flex: 1, position: 'relative', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 2 }}>
                          {/* Y-axis labels */}
                          <Box sx={{ position: 'absolute', left: -10, top: 10, fontSize: '0.75rem' }}>3500</Box>
                          <Box sx={{ position: 'absolute', left: -10, top: '25%', fontSize: '0.75rem' }}>2800</Box>
                          <Box sx={{ position: 'absolute', left: -10, top: '50%', fontSize: '0.75rem' }}>2100</Box>
                          <Box sx={{ position: 'absolute', left: -10, top: '75%', fontSize: '0.75rem' }}>1400</Box>
                          <Box sx={{ position: 'absolute', left: -10, bottom: 10, fontSize: '0.75rem' }}>700</Box>
                          
                          {/* Box plot visualization */}
                          <Box sx={{ position: 'relative', width: '80%', left: '10%', height: '100%' }}>
                            {/* Quartile box */}
                            <Box 
                              sx={{ 
                                position: 'absolute',
                                left: '25%',
                                width: '50%',
                                top: '35%',
                                height: '30%',
                                border: '2px solid',
                                borderColor: 'primary.main',
                                bgcolor: 'primary.light',
                                opacity: 0.3
                              }}
                            />
                            {/* Median line */}
                            <Box 
                              sx={{ 
                                position: 'absolute',
                                left: '25%',
                                width: '50%',
                                top: '47%',
                                height: '2px',
                                bgcolor: 'primary.main'
                              }}
                            />
                            {/* Whiskers */}
                            <Box sx={{ position: 'absolute', left: '49%', top: '20%', width: '2px', height: '15%', bgcolor: 'text.secondary' }} />
                            <Box sx={{ position: 'absolute', left: '49%', bottom: '20%', width: '2px', height: '15%', bgcolor: 'text.secondary' }} />
                            
                            {/* Outlier points */}
                            {(clinicalAlertsData?.calorie_outliers?.outliers || []).map((outlier: any, index: number) => {
                              const isHigh = outlier.value > 2800;
                              const yPosition = isHigh ? `${Math.max(5, 20 - (outlier.value - 2800) / 100)}%` : `${Math.min(95, 80 + (1400 - outlier.value) / 100)}%`;
                              return (
                                <Box
                                  key={index}
                                  sx={{
                                    position: 'absolute',
                                    left: `${40 + (index * 8)}%`,
                                    top: yPosition,
                                    width: 12,
                                    height: 12,
                                    borderRadius: '50%',
                                    bgcolor: outlier.severity === 'critical' ? 'error.main' : 'warning.main',
                                    cursor: 'pointer',
                                    '&:hover': { transform: 'scale(1.2)' }
                                  }}
                                  title={`${outlier.patient_name}: ${outlier.value} cal`}
                                />
                              );
                            })}
                          </Box>
                        </Box>
                        
                        <Box sx={{ mt: 1, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary">Patient Calorie Distribution</Typography>
                        </Box>
                        
                        {/* Legend */}
                        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'error.main', mr: 0.5 }} />
                            <Typography variant="caption">Critical (&gt;3000 cal)</Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'warning.main', mr: 0.5 }} />
                            <Typography variant="caption">Warning (&lt;800 cal)</Typography>
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Nutrient Spike Detection Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'info.main' }} />
                      Nutrient Spike Detection
                    </Typography>
                    <Box sx={{ height: 350 }}>
                      <Scatter
                        data={{
                          datasets: (clinicalAlertsData?.nutrient_spikes || []).map((spike: any, index: number) => ({
                            label: `${spike.patient_name} - ${spike.nutrient}`,
                            data: [{
                              x: new Date(spike.date).getTime(),
                              y: spike.rda_percent
                            }],
                            backgroundColor: spike.severity === 'critical' ? 'rgba(244, 67, 54, 0.8)' : 'rgba(255, 152, 0, 0.8)',
                            borderColor: spike.severity === 'critical' ? 'rgba(244, 67, 54, 1)' : 'rgba(255, 152, 0, 1)',
                            pointRadius: 8,
                            pointHoverRadius: 10
                          }))
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
                                title: function(context: any) {
                                  const spikes = clinicalAlertsData?.nutrient_spikes || [];
                                  const spike = spikes[context[0]?.datasetIndex];
                                  return spike ? `${spike.patient_name} - ${spike.nutrient.toUpperCase()}` : '';
                                },
                                label: function(context: any) {
                                  const spikes = clinicalAlertsData?.nutrient_spikes || [];
                                  const spike = spikes[context.datasetIndex];
                                  return spike ? [
                                    `Value: ${spike.value}mg`,
                                    `RDA %: ${spike.rda_percent}%`,
                                    `Date: ${spike.date}`,
                                    `Severity: ${spike.severity}`
                                  ] : [];
                                }
                              }
                            }
                          },
                          scales: {
                            x: {
                              type: 'linear' as const,
                              title: {
                                display: true,
                                text: 'Date'
                              },
                              ticks: {
                                callback: function(value: any) {
                                  const date = new Date(value);
                                  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                                }
                              }
                            },
                            y: {
                              beginAtZero: true,
                              title: {
                                display: true,
                                text: 'Nutrient Level (% of RDA)'
                              }
                            }
                          },
                          onClick: (event, elements) => {
                            if (elements.length > 0) {
                              const clickedIndex = elements[0].datasetIndex;
                              const spikes = clinicalAlertsData?.nutrient_spikes || [];
                              const clickedSpike = spikes[clickedIndex];
                              if (clickedSpike) {
                                // Could switch to individual patient view here
                                console.log('Clicked spike:', clickedSpike);
                              }
                            }
                          }
                        }}
                      />
                    </Box>
                    {/* Reference line legend */}
                    <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: 20, height: 2, bgcolor: 'error.main', mr: 1 }} />
                        <Typography variant="caption">300% RDA Alert Threshold (hover points for details)</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Active Alerts Table */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                        <Warning sx={{ mr: 1, color: 'warning.main' }} />
                        Active Clinical Alerts
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                        <Select
                          size="small"
                          value={alertFilter}
                          onChange={(e) => setAlertFilter(e.target.value as any)}
                          sx={{ minWidth: 120 }}
                        >
                          <MenuItem value="All">All Alerts</MenuItem>
                          <MenuItem value="Calories">Calories</MenuItem>
                          <MenuItem value="Nutrients">Nutrients</MenuItem>
                          <MenuItem value="Under-eating">Under-eating</MenuItem>
                        </Select>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => fetchClinicalAlertsData()}
                          startIcon={<CheckCircle />}
                        >
                          Refresh
                        </Button>
                      </Box>
                    </Box>
                    
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>
                              <TableSortLabel
                                active={alertSortBy === 'patient_name'}
                                direction={alertSortBy === 'patient_name' ? alertSortOrder : 'asc'}
                                onClick={() => {
                                  if (alertSortBy === 'patient_name') {
                                    setAlertSortOrder(alertSortOrder === 'asc' ? 'desc' : 'asc');
                                  } else {
                                    setAlertSortBy('patient_name');
                                    setAlertSortOrder('asc');
                                  }
                                }}
                              >
                                Patient Name
                              </TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel
                                active={alertSortBy === 'alert_type'}
                                direction={alertSortBy === 'alert_type' ? alertSortOrder : 'asc'}
                                onClick={() => {
                                  if (alertSortBy === 'alert_type') {
                                    setAlertSortOrder(alertSortOrder === 'asc' ? 'desc' : 'asc');
                                  } else {
                                    setAlertSortBy('alert_type');
                                    setAlertSortOrder('asc');
                                  }
                                }}
                              >
                                Alert Type
                              </TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel
                                active={alertSortBy === 'severity'}
                                direction={alertSortBy === 'severity' ? alertSortOrder : 'asc'}
                                onClick={() => {
                                  if (alertSortBy === 'severity') {
                                    setAlertSortOrder(alertSortOrder === 'asc' ? 'desc' : 'asc');
                                  } else {
                                    setAlertSortBy('severity');
                                    setAlertSortOrder('desc'); // Default to desc for severity
                                  }
                                }}
                              >
                                Severity
                              </TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel
                                active={alertSortBy === 'date'}
                                direction={alertSortBy === 'date' ? alertSortOrder : 'asc'}
                                onClick={() => {
                                  if (alertSortBy === 'date') {
                                    setAlertSortOrder(alertSortOrder === 'asc' ? 'desc' : 'asc');
                                  } else {
                                    setAlertSortBy('date');
                                    setAlertSortOrder('desc');
                                  }
                                }}
                              >
                                Date
                              </TableSortLabel>
                            </TableCell>
                            <TableCell>Value</TableCell>
                            <TableCell>Action</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {(clinicalAlertsData?.active_alerts || [])
                            .filter((alert: any) => {
                              if (alertFilter === 'All') return true;
                              if (alertFilter === 'Calories') return alert.alert_type.includes('Calories');
                              if (alertFilter === 'Nutrients') return alert.alert_type.includes('Spike') || alert.alert_type.includes('Excess');
                              if (alertFilter === 'Under-eating') return alert.alert_type.includes('Under-eating');
                              return true;
                            })
                            .sort((a: any, b: any) => {
                              const order = alertSortOrder === 'asc' ? 1 : -1;
                              if (alertSortBy === 'severity') {
                                const severityOrder = { critical: 3, warning: 2, info: 1 };
                                return ((severityOrder as any)[a.severity] - (severityOrder as any)[b.severity]) * order;
                              }
                              if (alertSortBy === 'date') {
                                return (new Date(a.date).getTime() - new Date(b.date).getTime()) * order;
                              }
                              return (a[alertSortBy] > b[alertSortBy] ? 1 : -1) * order;
                            })
                            .map((alert: any, index: number) => (
                              <TableRow 
                                key={alert.id} 
                                hover
                                sx={{ 
                                  cursor: 'pointer',
                                  '&:hover': { bgcolor: 'action.hover' }
                                }}
                                onClick={() => {
                                  // Could switch to individual patient view
                                  console.log('Clicked alert:', alert);
                                }}
                              >
                                <TableCell>{alert.patient_name}</TableCell>
                                <TableCell>
                                  <Chip
                                    label={alert.alert_type}
                                    size="small"
                                    color={
                                      alert.alert_type.includes('Calories') ? 'warning' :
                                      alert.alert_type.includes('Spike') || alert.alert_type.includes('Excess') ? 'info' :
                                      'error'
                                    }
                                  />
                                </TableCell>
                                <TableCell>
                                  <Chip
                                    label={alert.severity.toUpperCase()}
                                    size="small"
                                    color={alert.severity === 'critical' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'}
                                    sx={{
                                      animation: alert.severity === 'critical' ? 'pulse 2s infinite' : 'none',
                                      '@keyframes pulse': {
                                        '0%': { opacity: 1 },
                                        '50%': { opacity: 0.7 },
                                        '100%': { opacity: 1 }
                                      }
                                    }}
                                  />
                                </TableCell>
                                <TableCell>{new Date(alert.date).toLocaleDateString()}</TableCell>
                                <TableCell sx={{ fontFamily: 'monospace' }}>{alert.value}</TableCell>
                                <TableCell>
                                  <Button
                                    size="small"
                                    variant={alert.reviewed ? "contained" : "outlined"}
                                    color={alert.reviewed ? "success" : "primary"}
                                    startIcon={alert.reviewed ? <CheckCircle /> : <Visibility />}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleReviewAlert(alert);
                                    }}
                                  >
                                    {alert.reviewed ? 'Reviewed' : 'Review'}
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    
                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Showing {(clinicalAlertsData?.active_alerts || []).filter((alert: any) => {
                          if (alertFilter === 'All') return true;
                          if (alertFilter === 'Calories') return alert.alert_type.includes('Calories');
                          if (alertFilter === 'Nutrients') return alert.alert_type.includes('Spike') || alert.alert_type.includes('Excess');
                          if (alertFilter === 'Under-eating') return alert.alert_type.includes('Under-eating');
                          return true;
                        }).length} of {(clinicalAlertsData?.active_alerts || []).length} alerts
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Auto-refresh: 5 minutes • Last updated: {new Date().toLocaleTimeString()}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Clinical Alerts Dashboard
                </Typography>
                <Typography variant="body1" gutterBottom>
                  Monitor patient outliers and intervention needs in real-time.
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Analyzing real consumption data from all patients...
                </Typography>
                <Button
                  variant="contained"
                  onClick={fetchClinicalAlertsData}
                  startIcon={<ReportProblem />}
                  sx={{ mt: 1 }}
                >
                  Load Real Clinical Alerts
                </Button>
              </Alert>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          {/* Behavior Analysis Tab */}
          {behaviorClusteringLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : behaviorClusteringData ? (
            <Grid container spacing={3}>
              {/* Behavioral Archetype Dashboard Cards - Top Row */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Groups sx={{ mr: 1, color: 'primary.main' }} />
                  Behavioral Archetypes
                </Typography>
                <Grid container spacing={2}>
                  {behaviorClusteringData.behavioral_archetypes.map((archetype: any) => (
                    <Grid item xs={12} md={4} key={archetype.cluster_id}>
                      <Card sx={{ 
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        '&:hover': { 
                          transform: 'translateY(-4px)', 
                          boxShadow: 4,
                          borderColor: archetype.color
                        },
                        border: '2px solid transparent'
                      }}>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Box sx={{ 
                              backgroundColor: archetype.color + '20',
                              borderRadius: 2,
                              p: 1,
                              mr: 2
                            }}>
                              <Restaurant sx={{ color: archetype.color, fontSize: '2rem' }} />
                            </Box>
                            <Box>
                              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                {archetype.name}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {archetype.patient_count} patients
                              </Typography>
                            </Box>
                          </Box>
                          
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {archetype.description}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                            <Chip 
                              label={`${archetype.avg_outcomes.glucose_improvement}% glucose ↗`}
                              size="small" 
                              color="success" 
                              variant="outlined"
                            />
                            <Chip 
                              label={`${archetype.avg_outcomes.weight_change}kg weight`}
                              size="small" 
                              color={archetype.avg_outcomes.weight_change < 0 ? "success" : "warning"}
                              variant="outlined"
                            />
                            <Chip 
                              label={`${archetype.avg_outcomes.compliance_rate}% compliance`}
                              size="small" 
                              color="info" 
                              variant="outlined"
                            />
                          </Box>
                          
                          <Button 
                            variant="outlined" 
                            size="small" 
                            onClick={() => handleViewPatients(archetype)}
                            sx={{ 
                              borderColor: archetype.color,
                              color: archetype.color,
                              '&:hover': { 
                                backgroundColor: archetype.color + '10',
                                borderColor: archetype.color
                              }
                            }}
                          >
                            View Patients
                          </Button>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Grid>

              {/* Behavior-Outcome Correlation Scatter Plot and Donut Chart - Middle Row */}
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
                      Behavior-Outcome Correlation
                    </Typography>
                    <Box sx={{ height: 400 }}>
                      <Scatter
                        data={{
                          datasets: behaviorClusteringData.behavioral_archetypes.map((archetype: any) => ({
                            label: archetype.name,
                            data: behaviorClusteringData.behavior_outcome_correlation
                              .filter((patient: any) => patient.cluster === archetype.cluster_id)
                              .map((patient: any) => ({
                                x: patient.behavior_score,
                                y: patient.glucose_improvement
                              })),
                            backgroundColor: archetype.color + '80',
                            borderColor: archetype.color,
                            pointRadius: 6,
                            pointHoverRadius: 8
                          }))
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top' as const,
                            },
                            tooltip: {
                              callbacks: {
                                title: function(context: any) {
                                  const pointIndex = context[0].dataIndex;
                                  const datasetIndex = context[0].datasetIndex;
                                  const archetype = behaviorClusteringData.behavioral_archetypes[datasetIndex];
                                  const patients = behaviorClusteringData.behavior_outcome_correlation
                                    .filter((p: any) => p.cluster === archetype.cluster_id);
                                  return patients[pointIndex]?.patient_name || 'Patient';
                                },
                                label: function(context: any) {
                                  const pointIndex = context.dataIndex;
                                  const datasetIndex = context.datasetIndex;
                                  const archetype = behaviorClusteringData.behavioral_archetypes[datasetIndex];
                                  const patients = behaviorClusteringData.behavior_outcome_correlation
                                    .filter((p: any) => p.cluster === archetype.cluster_id);
                                  const patient = patients[pointIndex];
                                  return [
                                    `Behavior Score: ${context.parsed.x}`,
                                    `Glucose Improvement: ${context.parsed.y}%`,
                                    `Weight Change: ${patient?.weight_change}kg`,
                                    `Compliance: ${patient?.compliance_rate}%`
                                  ];
                                }
                              }
                            }
                          },
                          scales: {
                            x: {
                              title: {
                                display: true,
                                text: 'Behavior Score (Consistency, Logging Frequency, Meal Timing)'
                              },
                              min: 0,
                              max: 100
                            },
                            y: {
                              title: {
                                display: true,
                                text: 'Glucose Improvement (%)'
                              },
                              min: 0
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <People sx={{ mr: 1, color: 'primary.main' }} />
                      Patient Distribution
                    </Typography>
                    <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
                      <Doughnut
                        data={{
                          labels: behaviorClusteringData.cluster_distribution.map((cluster: any) => cluster.cluster),
                          datasets: [{
                            data: behaviorClusteringData.cluster_distribution.map((cluster: any) => cluster.count),
                            backgroundColor: behaviorClusteringData.behavioral_archetypes.map((archetype: any) => archetype.color + '80'),
                            borderColor: behaviorClusteringData.behavioral_archetypes.map((archetype: any) => archetype.color),
                            borderWidth: 2,
                            hoverBackgroundColor: behaviorClusteringData.behavioral_archetypes.map((archetype: any) => archetype.color + 'CC'),
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'bottom' as const,
                              labels: {
                                usePointStyle: true,
                                pointStyle: 'circle',
                                font: {
                                  size: 11
                                }
                              }
                            },
                            tooltip: {
                              callbacks: {
                                label: function(context: any) {
                                  const cluster = behaviorClusteringData.cluster_distribution[context.dataIndex];
                                  return `${cluster.cluster}: ${cluster.count} patients (${cluster.percentage}%)`;
                                }
                              }
                            }
                          },
                          cutout: '60%'
                        }}
                      />
                      <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center'
                      }}>
                        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                          {behaviorClusteringData.cluster_distribution.reduce((sum: number, cluster: any) => sum + cluster.count, 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Patients
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Behavioral Trends Timeline and Outcome Comparison - Bottom Row */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <Timeline sx={{ mr: 1, color: 'primary.main' }} />
                      Behavioral Trends Over Time
                    </Typography>
                    <Box sx={{ height: 350 }}>
                      <Line
                        data={{
                          labels: behaviorClusteringData.cluster_trends.labels,
                          datasets: behaviorClusteringData.cluster_trends.datasets.map((dataset: any) => ({
                            label: dataset.cluster,
                            data: dataset.data,
                            borderColor: dataset.color,
                            backgroundColor: dataset.color + '20',
                            borderWidth: 3,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            tension: 0.3
                          }))
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
                            x: {
                              title: {
                                display: true,
                                text: 'Time Period'
                              }
                            },
                            y: {
                              title: {
                                display: true,
                                text: 'Number of Patients in Cluster'
                              },
                              beginAtZero: true
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

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                      Outcome Comparison by Cluster
                    </Typography>
                    <Box sx={{ height: 350 }}>
                      <Bar
                        data={{
                          labels: behaviorClusteringData.outcome_comparison.clusters,
                          datasets: [
                            {
                              label: 'Glucose Improvement (%)',
                              data: behaviorClusteringData.outcome_comparison.glucose_improvement,
                              backgroundColor: 'rgba(76, 175, 80, 0.6)',
                              borderColor: 'rgba(76, 175, 80, 1)',
                              borderWidth: 1
                            },
                            {
                              label: 'Weight Change (kg)',
                              data: behaviorClusteringData.outcome_comparison.weight_change.map((val: number) => Math.abs(val)),
                              backgroundColor: 'rgba(33, 150, 243, 0.6)',
                              borderColor: 'rgba(33, 150, 243, 1)',
                              borderWidth: 1
                            },
                            {
                              label: 'Compliance Rate (%)',
                              data: behaviorClusteringData.outcome_comparison.compliance_rate,
                              backgroundColor: 'rgba(255, 152, 0, 0.6)',
                              borderColor: 'rgba(255, 152, 0, 1)',
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
                              callbacks: {
                                label: function(context: any) {
                                  const datasetLabel = context.dataset.label;
                                  let value = context.parsed.y;
                                  
                                  if (datasetLabel === 'Weight Change (kg)') {
                                    const originalValue = behaviorClusteringData.outcome_comparison.weight_change[context.dataIndex];
                                    return `${datasetLabel}: ${originalValue}kg`;
                                  }
                                  
                                  return `${datasetLabel}: ${value}${datasetLabel.includes('%') ? '' : datasetLabel.includes('kg') ? 'kg' : ''}`;
                                }
                              }
                            }
                          },
                          scales: {
                            x: {
                              title: {
                                display: true,
                                text: 'Behavioral Clusters'
                              }
                            },
                            y: {
                              title: {
                                display: true,
                                text: 'Outcome Metrics'
                              },
                              beginAtZero: true
                            }
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Advanced Analytics Section */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <EmojiEvents sx={{ mr: 1, color: 'primary.main' }} />
                  Success Stories & Risk Indicators
                </Typography>
                
                <Grid container spacing={2}>
                  {/* Success Stories */}
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2, color: 'success.main' }}>
                          Recent Success Stories
                        </Typography>
                        {behaviorClusteringData.success_stories.map((story: any, index: number) => (
                          <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'success.light', borderRadius: 1, color: 'success.contrastText' }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                              {story.patient_name}
                            </Typography>
                            <Typography variant="caption">
                              {story.from_cluster} → {story.to_cluster}
                            </Typography>
                            <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              <Chip label={story.improvement_metrics.glucose_improvement} size="small" color="success" />
                              <Chip label={story.improvement_metrics.weight_change} size="small" color="success" />
                              <Chip label={story.improvement_metrics.compliance_rate} size="small" color="success" />
                            </Box>
                            <Typography variant="caption" sx={{ display: 'block', mt: 1, fontStyle: 'italic' }}>
                              Intervention: {story.intervention}
                            </Typography>
                          </Box>
                        ))}
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Risk Indicators */}
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2, color: 'warning.main' }}>
                          Risk Indicators & Interventions
                        </Typography>
                        {behaviorClusteringData.risk_indicators.map((risk: any, index: number) => (
                          <Box key={index} sx={{ 
                            mb: 2, 
                            p: 2, 
                            bgcolor: risk.risk_level === 'high' ? 'error.light' : 'warning.light', 
                            borderRadius: 1,
                            color: risk.risk_level === 'high' ? 'error.contrastText' : 'warning.contrastText'
                          }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                {risk.cluster}
                              </Typography>
                              <Chip 
                                label={`${risk.risk_level.toUpperCase()} RISK`} 
                                size="small" 
                                color={risk.risk_level === 'high' ? 'error' : 'warning'}
                                variant="filled"
                              />
                            </Box>
                            <Typography variant="caption" sx={{ display: 'block', mb: 1 }}>
                              {risk.patients_at_risk} patients at risk
                            </Typography>
                            <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                              Recommended: {risk.intervention_needed}
                            </Typography>
                          </Box>
                        ))}
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Grid>

              {/* Predictive Insights */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <CheckCircle sx={{ mr: 1, color: 'primary.main' }} />
                      Predictive Insights
                    </Typography>
                    <Grid container spacing={2}>
                      {behaviorClusteringData.predictive_insights.map((insight: any, index: number) => (
                        <Grid item xs={12} md={4} key={index}>
                          <Box sx={{ 
                            p: 2, 
                            border: '1px solid', 
                            borderColor: 'divider', 
                            borderRadius: 2,
                            height: '100%',
                            bgcolor: 'background.paper'
                          }}>
                            <Typography variant="body2" sx={{ mb: 2 }}>
                              {insight.insight}
                            </Typography>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Typography variant="caption" color="text.secondary">
                                Sample: {insight.sample_size} patients
                              </Typography>
                              <Chip 
                                label={`${Math.round(insight.confidence * 100)}% confidence`}
                                size="small"
                                color={insight.confidence > 0.8 ? 'success' : insight.confidence > 0.7 ? 'warning' : 'default'}
                                variant="outlined"
                              />
                            </Box>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Behavior Analysis Dashboard
                </Typography>
                <Typography variant="body1" gutterBottom>
                  Analyze patient behavioral patterns and link behaviors to health outcomes.
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Loading comprehensive behavioral clustering data...
                </Typography>
                <Button
                  variant="contained"
                  onClick={fetchBehaviorClusteringData}
                  startIcon={<Groups />}
                  sx={{ mt: 1 }}
                >
                  Load Behavior Analysis
                </Button>
              </Alert>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={5}>
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

      {/* Review Alert Dialog */}
      <Dialog 
        open={reviewDialogOpen} 
        onClose={handleCloseReviewDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ReportProblem sx={{ mr: 2, color: selectedAlert?.severity === 'critical' ? 'error.main' : 'warning.main' }} />
            Review Clinical Alert
          </Box>
          <Button onClick={handleCloseReviewDialog} size="small">
            <Close />
          </Button>
        </DialogTitle>
        
        <DialogContent>
          {selectedAlert && (
            <Box sx={{ pt: 1 }}>
              {/* Alert Overview */}
              <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Person sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="h6">{selectedAlert.patient_name}</Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Patient ID: {selectedAlert.patient_id}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <CalendarToday sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="h6">Alert Details</Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Date: {new Date(selectedAlert.date).toLocaleDateString()}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Divider sx={{ my: 2 }} />
                      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                        <Chip
                          label={selectedAlert.alert_type}
                          color={
                            selectedAlert.alert_type.includes('Calories') ? 'warning' :
                            selectedAlert.alert_type.includes('Spike') || selectedAlert.alert_type.includes('Excess') ? 'info' :
                            'error'
                          }
                          size="medium"
                        />
                        <Chip
                          label={`${selectedAlert.severity.toUpperCase()} PRIORITY`}
                          color={selectedAlert.severity === 'critical' ? 'error' : 'warning'}
                          variant="outlined"
                          size="medium"
                        />
                      </Box>
                      
                      <Typography variant="h6" gutterBottom>Value:</Typography>
                      <Typography variant="body1" sx={{ fontFamily: 'monospace', bgcolor: 'grey.100', p: 1, borderRadius: 1, mb: 2 }}>
                        {selectedAlert.value}
                      </Typography>
                      
                      <Typography variant="h6" gutterBottom>Description:</Typography>
                      <Typography variant="body1" paragraph>
                        {selectedAlert.description}
                      </Typography>
                      
                      <Typography variant="h6" gutterBottom>Recommended Action:</Typography>
                      <Typography variant="body1" paragraph sx={{ color: 'warning.main', fontWeight: 'medium' }}>
                        {selectedAlert.action_needed}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Review Form */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <NoteAdd sx={{ mr: 1, color: 'primary.main' }} />
                    Clinical Review
                  </Typography>
                  
                  <FormControl component="fieldset" sx={{ mb: 3, width: '100%' }}>
                    <FormLabel component="legend" sx={{ mb: 2 }}>Review Action</FormLabel>
                    <RadioGroup
                      value={reviewAction}
                      onChange={(e) => setReviewAction(e.target.value as any)}
                    >
                      <FormControlLabel 
                        value="resolved" 
                        control={<Radio />} 
                        label={
                          <Box>
                            <Typography variant="body1" fontWeight="medium">Resolved</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Issue has been addressed and resolved
                            </Typography>
                          </Box>
                        }
                      />
                      <FormControlLabel 
                        value="monitoring" 
                        control={<Radio />} 
                        label={
                          <Box>
                            <Typography variant="body1" fontWeight="medium">Continue Monitoring</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Keep alert active and monitor patient progress
                            </Typography>
                          </Box>
                        }
                      />
                      <FormControlLabel 
                        value="escalated" 
                        control={<Radio />} 
                        label={
                          <Box>
                            <Typography variant="body1" fontWeight="medium">Escalate to Physician</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Requires immediate medical attention
                            </Typography>
                          </Box>
                        }
                      />
                      <FormControlLabel 
                        value="dismissed" 
                        control={<Radio />} 
                        label={
                          <Box>
                            <Typography variant="body1" fontWeight="medium">Dismiss</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Alert is not clinically significant
                            </Typography>
                          </Box>
                        }
                      />
                    </RadioGroup>
                  </FormControl>

                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Clinical Notes"
                    placeholder="Enter your clinical assessment, actions taken, and any follow-up instructions..."
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    sx={{ mb: 2 }}
                  />
                  
                  <Typography variant="body2" color="text.secondary">
                    Review will be logged with timestamp and reviewer information.
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button 
            onClick={handleCloseReviewDialog}
            variant="outlined"
            disabled={reviewLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSubmitReview}
            variant="contained"
            startIcon={reviewLoading ? <CircularProgress size={20} /> : <Save />}
            disabled={reviewLoading || !reviewNotes.trim()}
            color={reviewAction === 'escalated' ? 'error' : 'primary'}
          >
            {reviewLoading ? 'Submitting...' : `Submit ${reviewAction === 'escalated' ? 'Escalation' : 'Review'}`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Patient Modal for Behavioral Clusters */}
      <Dialog 
        open={patientModalOpen} 
        onClose={() => setPatientModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ 
          backgroundColor: selectedCluster?.color + '10',
          borderBottom: `2px solid ${selectedCluster?.color}`,
          display: 'flex',
          alignItems: 'center'
        }}>
          <Box sx={{ 
            backgroundColor: selectedCluster?.color + '20',
            borderRadius: 2,
            p: 1,
            mr: 2
          }}>
            <Restaurant sx={{ color: selectedCluster?.color, fontSize: '1.5rem' }} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              {selectedCluster?.name} Patients
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {selectedCluster?.patients?.length || 0} patients in this behavioral cluster
            </Typography>
          </Box>
        </DialogTitle>
        
        <DialogContent sx={{ p: 0 }}>
          {selectedCluster?.patients && selectedCluster.patients.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'grey.50' }}>
                    <TableCell sx={{ fontWeight: 'bold' }}>Patient Name</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 'bold' }}>Behavior Score</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 'bold' }}>Compliance Rate</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 'bold' }}>Glucose Improvement</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 'bold' }}>Weight Change</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedCluster.patients.map((patient: any, index: number) => (
                    <TableRow 
                      key={patient.patient_id || index}
                      sx={{ 
                        '&:hover': { backgroundColor: selectedCluster.color + '05' },
                        borderLeft: `4px solid ${selectedCluster.color}20`
                      }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            backgroundColor: selectedCluster.color + '20',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            mr: 2
                          }}>
                            <Person sx={{ color: selectedCluster.color, fontSize: '1.2rem' }} />
                          </Box>
                          <Box>
                            <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                              {patient.patient_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              ID: {patient.patient_id}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={`${patient.behavior_score}`}
                          size="small"
                          sx={{ 
                            backgroundColor: selectedCluster.color + '20',
                            color: selectedCluster.color,
                            fontWeight: 'bold'
                          }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={`${patient.compliance_rate}%`}
                          size="small"
                          color={patient.compliance_rate >= 80 ? "success" : patient.compliance_rate >= 60 ? "warning" : "error"}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Typography variant="body2" sx={{ 
                            color: patient.glucose_improvement > 0 ? 'success.main' : 'text.secondary',
                            fontWeight: 'medium'
                          }}>
                            {patient.glucose_improvement > 0 ? '+' : ''}{patient.glucose_improvement}%
                          </Typography>
                          {patient.glucose_improvement > 0 && (
                            <TrendingUp sx={{ fontSize: '1rem', color: 'success.main', ml: 0.5 }} />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" sx={{ 
                          color: patient.weight_change < 0 ? 'success.main' : patient.weight_change > 0 ? 'warning.main' : 'text.secondary',
                          fontWeight: 'medium'
                        }}>
                          {patient.weight_change > 0 ? '+' : ''}{patient.weight_change}kg
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                No patients found in this cluster
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                This behavioral archetype currently has no assigned patients.
              </Typography>
            </Box>
          )}
          
          {/* Cluster Summary */}
          {selectedCluster && (
            <Box sx={{ p: 3, backgroundColor: 'grey.50', borderTop: '1px solid', borderColor: 'grey.200' }}>
              <Typography variant="h6" gutterBottom sx={{ color: selectedCluster.color, fontWeight: 'bold' }}>
                Cluster Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Description:
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {selectedCluster.description}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Key Characteristics:
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    {(selectedCluster.characteristics || []).map((char: string, index: number) => (
                      <Typography key={index} variant="body2" sx={{ 
                        display: 'flex', 
                        alignItems: 'center'
                      }}>
                        • {char}
                      </Typography>
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Average Outcomes:
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Chip 
                      label={`${selectedCluster.avg_outcomes?.glucose_improvement || 0}% Glucose Improvement`}
                      color="success" 
                      variant="outlined"
                      size="small"
                    />
                    <Chip 
                      label={`${selectedCluster.avg_outcomes?.weight_change || 0}kg Weight Change`}
                      color={selectedCluster.avg_outcomes?.weight_change < 0 ? "success" : "warning"}
                      variant="outlined"
                      size="small"
                    />
                    <Chip 
                      label={`${selectedCluster.avg_outcomes?.compliance_rate || 0}% Compliance Rate`}
                      color="info" 
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions sx={{ p: 2 }}>
          <Button 
            onClick={() => setPatientModalOpen(false)}
            variant="outlined"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PiasCorner;