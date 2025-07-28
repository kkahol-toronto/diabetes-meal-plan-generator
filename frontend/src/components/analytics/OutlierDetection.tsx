import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Chip, Avatar, List, ListItem, ListItemText,
  ListItemAvatar, CircularProgress, Dialog, DialogTitle, DialogContent,
  DialogActions, Button, ListItemIcon, FormControl, InputLabel,
  Select, MenuItem, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Tooltip
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Person as PersonIcon,
  TrendingUp as TrendingUpIcon,
  Visibility as VisibilityIcon,
  Flag as FlagIcon,
  Notifications as NotificationIcon
} from '@mui/icons-material';
import { Line, Doughnut, Bar, Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import config from '../../config/environment';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

// Individual Patient Outlier Analysis Component
const IndividualOutlierAnalysis: React.FC<{selectedPatient: string}> = ({ selectedPatient }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedOutlier, setSelectedOutlier] = useState<any>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    if (selectedPatient) {
      fetchIndividualOutliers();
    }
  }, [selectedPatient]);

  const fetchIndividualOutliers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${config.API_URL}/admin/analytics/outlier-detection?view_mode=individual&patient_id=${selectedPatient}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch outlier data');
      }
      
      const result = await response.json();
      
      // Transform old endpoint data format to new component format for individual
      if (result.registration_status === 'not_registered') {
        setData(result);
      } else {
        const transformedData = {
          patient_name: result.patient_name,
          registration_status: result.registration_status,
          analysis_period_days: 30,
          outliers: result.outliers?.map((outlier: any, index: number) => ({
            type: outlier.type === 'nutrition' ? 'nutritional_outlier' : outlier.type,
            date: new Date().toISOString().split('T')[0],
            severity: outlier.severity,
            nutrient: outlier.anomaly?.includes('carbohydrate') ? 'Carbohydrates' : 
                     outlier.anomaly?.includes('sodium') ? 'Sodium' : 
                     outlier.anomaly?.includes('fiber') ? 'Fiber' : 'General',
            value: outlier.value,
            expected_range: `< ${outlier.threshold}`,
            food_name: `${outlier.anomaly}`,
            meal_records: []
          })) || [],
          summary: {
            total_outliers: result.outliers?.length || 0,
            high_severity: result.outliers?.filter((o: any) => o.severity === 'high').length || 0,
            extreme_severity: 0,
            moderate_severity: result.outliers?.filter((o: any) => o.severity === 'medium').length || 0,
            outlier_types: result.outliers?.reduce((acc: any, outlier: any) => {
              const type = outlier.type === 'nutrition' ? 'nutritional_outlier' : outlier.type;
              acc[type] = (acc[type] || 0) + 1;
              return acc;
            }, {}) || {},
            recommendations: result.alerts?.map((alert: any) => ({
              priority: alert.type === 'critical' ? 'immediate' : 'standard',
              message: alert.message,
              action: 'Review patient care plan'
            })) || []
          }
        };
        setData(transformedData);
      }
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch individual outlier data:', error);
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'extreme': return 'error';
      case 'high': return 'error';
      case 'moderate': return 'warning';
      default: return 'info';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'extreme': return '🚨';
      case 'high': return '⚠️';
      case 'moderate': return '⚡';
      default: return 'ℹ️';
    }
  };

  const getOutlierTypeLabel = (type: string) => {
    const labels = {
      'nutritional_outlier': 'Nutritional Extreme',
      'binge_eating': 'Binge Eating',
      'under_eating': 'Under-eating',
      'excessive_meal_frequency': 'Too Many Meals',
      'late_night_eating': 'Late Night Eating'
    };
    return labels[type as keyof typeof labels] || type;
  };

  const createOutlierTimelineChart = () => {
    if (!data || !data.outliers) return null;
    
    // Group outliers by date
    const outliersByDate = data.outliers.reduce((acc: any, outlier: any) => {
      const date = outlier.date;
      if (!acc[date]) acc[date] = 0;
      acc[date] += outlier.severity === 'high' || outlier.severity === 'extreme' ? 2 : 1;
      return acc;
    }, {});
    
    // Create date range for last 30 days
    const dates = Array.from({length: 30}, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (29 - i));
      return date.toISOString().split('T')[0];
    });
    
    const outlierCounts = dates.map(date => outliersByDate[date] || 0);
    
    return {
      labels: dates.map(date => new Date(date).toLocaleDateString()),
      datasets: [{
        label: 'Outlier Severity Score',
        data: outlierCounts,
        borderColor: '#f44336',
        backgroundColor: 'rgba(244, 67, 54, 0.1)',
        fill: true,
        tension: 0.4
      }]
    };
  };

  const createOutlierDistributionChart = () => {
    if (!data || !data.summary?.outlier_types) return null;
    
    return {
      labels: Object.keys(data.summary.outlier_types).map(getOutlierTypeLabel),
      datasets: [{
        data: Object.values(data.summary.outlier_types),
        backgroundColor: ['#f44336', '#ff9800', '#ffc107', '#4caf50', '#2196f3'],
        borderWidth: 2,
        borderColor: '#fff'
      }]
    };
  };

  const handleOutlierClick = (outlier: any) => {
    setSelectedOutlier(outlier);
    setDialogOpen(true);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="error">
        Failed to load outlier analysis.
      </Alert>
    );
  }

  if (data.registration_status === 'not_registered') {
    return (
      <Alert severity="info">
        {data.message}
      </Alert>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Summary Overview */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Outlier Analysis - {data.patient_name}
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="error.main">
                  {data.summary?.total_outliers || 0}
                </Typography>
                <Typography variant="body2">Total Outliers</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="error.main">
                  {(data.summary?.high_severity || 0) + (data.summary?.extreme_severity || 0)}
                </Typography>
                <Typography variant="body2">High/Extreme Severity</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="warning.main">
                  {data.summary?.moderate_severity || 0}
                </Typography>
                <Typography variant="body2">Moderate Severity</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="info.main">
                  {data.analysis_period_days}
                </Typography>
                <Typography variant="body2">Days Analyzed</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Outlier Timeline */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Outlier Timeline (30 Days)</Typography>
            <Box sx={{ height: 300 }}>
              {createOutlierTimelineChart() ? (
                <Line data={createOutlierTimelineChart()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: { y: { beginAtZero: true } },
                  plugins: {
                    legend: {
                      display: false
                    }
                  }
                }} />
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Typography variant="body2" color="text.secondary">No outlier timeline data available</Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Outlier Type Distribution */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Outlier Types</Typography>
            <Box sx={{ height: 300 }}>
              {createOutlierDistributionChart() ? (
                <Doughnut data={createOutlierDistributionChart()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    }
                  }
                }} />
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Typography variant="body2" color="text.secondary">No outlier type data available</Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Outliers List */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Recent Outliers</Typography>
            <List>
              {data.outliers?.slice(0, 10).map((outlier: any, index: number) => (
                <ListItem 
                  key={index}
                  sx={{ 
                    border: '1px solid #e0e0e0', 
                    borderRadius: 1, 
                    mb: 1,
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                  onClick={() => handleOutlierClick(outlier)}
                >
                  <ListItemIcon>
                    <Typography variant="h6">{getSeverityIcon(outlier.severity)}</Typography>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip 
                          label={getOutlierTypeLabel(outlier.type)}
                          color={getSeverityColor(outlier.severity)}
                          size="small"
                        />
                        <Typography variant="body1">
                          {outlier.date} - {outlier.nutrient && `${outlier.nutrient}: ${outlier.value}`}
                          {outlier.calories && `${outlier.calories} calories`}
                          {outlier.food_name && ` (${outlier.food_name})`}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      outlier.expected_range ? `Expected: ${outlier.expected_range}` : 
                      outlier.meal_count ? `${outlier.meal_count} meals` : ''
                    }
                  />
                  <IconButton>
                    <VisibilityIcon />
                  </IconButton>
                </ListItem>
              )) || []}
            </List>
          </CardContent>
        </Card>
      </Grid>

      {/* Recommendations */}
      {data.summary?.recommendations && data.summary.recommendations.length > 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Recommendations</Typography>
              {data.summary.recommendations.map((rec: any, index: number) => (
                <Alert 
                  key={index}
                  severity={rec.priority === 'immediate' ? 'error' : 'warning'}
                  sx={{ mb: 1 }}
                >
                  <Typography variant="subtitle2">{rec.message}</Typography>
                  <Typography variant="body2">{rec.action}</Typography>
                </Alert>
              ))}
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Outlier Detail Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Outlier Details - {selectedOutlier && getOutlierTypeLabel(selectedOutlier.type)}
        </DialogTitle>
        <DialogContent>
          {selectedOutlier && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="h6" color={getSeverityColor(selectedOutlier.severity)}>
                  {getSeverityIcon(selectedOutlier.severity)} {selectedOutlier.severity.toUpperCase()} SEVERITY
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">Date</Typography>
                <Typography variant="body1">{selectedOutlier.date}</Typography>
              </Grid>
              
              {selectedOutlier.time && (
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Time</Typography>
                  <Typography variant="body1">{selectedOutlier.time}</Typography>
                </Grid>
              )}
              
              {selectedOutlier.nutrient && (
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Nutrient</Typography>
                  <Typography variant="body1">{selectedOutlier.nutrient}</Typography>
                </Grid>
              )}
              
              {selectedOutlier.value && (
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Value</Typography>
                  <Typography variant="body1">{selectedOutlier.value}</Typography>
                </Grid>
              )}
              
              {selectedOutlier.expected_range && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">Expected Range</Typography>
                  <Typography variant="body1">{selectedOutlier.expected_range}</Typography>
                </Grid>
              )}
              
              {selectedOutlier.food_name && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">Food Item</Typography>
                  <Typography variant="body1">{selectedOutlier.food_name}</Typography>
                </Grid>
              )}
              
              {selectedOutlier.meal_records && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">Related Meals</Typography>
                  {selectedOutlier.meal_records.map((meal: any, idx: number) => (
                    <Chip 
                      key={idx}
                      label={`${meal.food_name} (${meal.nutritional_info?.calories || 0} cal)`}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          <Button variant="contained" color="primary">
            Flag for Follow-up
          </Button>
        </DialogActions>
      </Dialog>


    </Grid>
  );
};

// Cohort Outlier Analysis Component
const CohortOutlierAnalysis: React.FC<{groupingCriteria: string}> = ({ groupingCriteria }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [alertDialogOpen, setAlertDialogOpen] = useState(false);
  const [patientDetailsOpen, setPatientDetailsOpen] = useState(false);
  const [selectedPatientDetails, setSelectedPatientDetails] = useState<any>(null);
  const [patientDetailsLoading, setPatientDetailsLoading] = useState(false);

  useEffect(() => {
    fetchCohortOutliers();
  }, [groupingCriteria]);

  const fetchCohortOutliers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${config.API_URL}/admin/analytics/outlier-detection?view_mode=cohort&group_by=${groupingCriteria}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch cohort outlier data');
      }
      
      const result = await response.json();
      
      // Transform old endpoint data format to new component format
      const transformedData = {
        grouping_criteria: groupingCriteria,
        total_population_outliers: result.outlier_patients?.length || 0,
        groups: {},
        analysis_timestamp: new Date().toISOString()
      };

      // Group outlier patients by their group
      if (result.outlier_patients) {
        const groupedData: any = {};
        
        result.outlier_patients.forEach((patient: any) => {
          const groupName = patient.group || 'Unknown';
          if (!groupedData[groupName]) {
            groupedData[groupName] = {
              patient_count: 0,
              registered_patients: 0,
              patients_with_outliers: 0,
              total_outliers: 0,
              outlier_distribution: {},
              high_risk_patients: []
            };
          }
          
          groupedData[groupName].total_outliers += 1;
          groupedData[groupName].patients_with_outliers += 1;
          
          if (patient.risk_score >= 70) {
            groupedData[groupName].high_risk_patients.push({
              patient_id: patient.id,
              patient_name: patient.name,
              high_severity_outliers: Math.floor(patient.risk_score / 20)
            });
          }
          
          // Add to outlier distribution
          const outlierType = patient.severity === 'high' ? 'nutritional_outlier' : 'binge_eating';
          if (!groupedData[groupName].outlier_distribution[outlierType]) {
            groupedData[groupName].outlier_distribution[outlierType] = 0;
          }
          groupedData[groupName].outlier_distribution[outlierType] += 1;
        });
        
        transformedData.groups = groupedData;
      }

      setData(transformedData);
      setSelectedGroup(Object.keys(transformedData.groups)[0] || '');
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch cohort outlier data:', error);
      setLoading(false);
    }
  };

  const fetchPatientDetails = async (patientId: string) => {
    try {
      setPatientDetailsLoading(true);
      
      // Fetch patient profile
      const profileResponse = await fetch(`${config.API_URL}/admin/patients/${patientId}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!profileResponse.ok) {
        throw new Error('Failed to fetch patient profile');
      }
      
      const patientProfile = await profileResponse.json();
      
      // Check if patient is registered and get their consumption data
      const outlierResponse = await fetch(`${config.API_URL}/admin/analytics/outlier-detection?view_mode=individual&patient_id=${patientId}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      let consumptionData = null;
      let recentHistory = [];
      
      if (outlierResponse.ok) {
        const outlierData = await outlierResponse.json();
        
        if (outlierData.registration_status === 'registered') {
          // Get user email from registration code
          const userQuery = await fetch(`${config.API_URL}/admin/patients/${patientId}/consumption-history?days=2`, {
            headers: { 
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (userQuery.ok) {
            recentHistory = await userQuery.json();
          }
        }
        
        consumptionData = outlierData;
      }
      
      setSelectedPatientDetails({
        profile: patientProfile,
        outliers: consumptionData,
        recentHistory: recentHistory || [],
        lastUpdated: new Date().toISOString()
      });
      
      setPatientDetailsOpen(true);
      setPatientDetailsLoading(false);
    } catch (error) {
      console.error('Failed to fetch patient details:', error);
      setPatientDetailsLoading(false);
    }
  };

  const createPopulationOutlierChart = () => {
    if (!data) return null;
    
    const groups = Object.keys(data.groups);
    const outlierCounts = groups.map(group => data.groups[group].total_outliers);
    const patientCounts = groups.map(group => data.groups[group].patient_count);
    const outlierRates = groups.map((group, index) => 
      patientCounts[index] > 0 ? (outlierCounts[index] / patientCounts[index]) * 100 : 0
    );
    
    return {
      labels: groups,
      datasets: [
        {
          label: 'Total Outliers',
          data: outlierCounts,
          backgroundColor: '#f44336',
          yAxisID: 'y',
          type: 'bar' as const
        },
        {
          label: 'Outlier Rate (%)',
          data: outlierRates,
          backgroundColor: '#ff9800',
          borderColor: '#ff9800',
          type: 'line' as const,
          yAxisID: 'y1'
        }
      ]
    };
  };

  const createOutlierTypeHeatmap = () => {
    if (!data) return null;
    
    const groups = Object.keys(data.groups);
    const outlierTypes = ['nutritional_outlier', 'binge_eating', 'under_eating', 'late_night_eating'];
    
    const heatmapData = outlierTypes.map(type => ({
      type,
      data: groups.map(group => {
        const distribution = data.groups[group].outlier_distribution || {};
        return distribution[type] || 0;
      })
    }));
    
    return { groups, outlierTypes, heatmapData };
  };

  const getHighestRiskPatients = () => {
    if (!data) return [];
    
    const allHighRisk: any[] = [];
    Object.entries(data.groups).forEach(([groupName, groupData]: [string, any]) => {
      (groupData.high_risk_patients || []).forEach((patient: any) => {
        allHighRisk.push({
          ...patient,
          group: groupName
        });
      });
    });
    
    return allHighRisk.sort((a, b) => b.high_severity_outliers - a.high_severity_outliers).slice(0, 10);
  };



  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="error">
        Failed to load cohort outlier analysis.
      </Alert>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Population Overview */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Population Outlier Overview - {groupingCriteria.replace('_', ' ')}
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="error.main">
                  {data.total_population_outliers}
                </Typography>
                <Typography variant="body2">Total Outliers</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="warning.main">
                  {Object.keys(data.groups).length}
                </Typography>
                <Typography variant="body2">Groups Analyzed</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="info.main">
                  {Object.values(data.groups).reduce((sum: number, group: any) => sum + group.patients_with_outliers, 0)}
                </Typography>
                <Typography variant="body2">Patients with Outliers</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="error.main">
                  {getHighestRiskPatients().length}
                </Typography>
                <Typography variant="body2">High Risk Patients</Typography>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 2 }}>
              <Button 
                variant="contained" 
                color="error" 
                onClick={() => setAlertDialogOpen(true)}
                startIcon={<NotificationIcon />}
              >
                Generate Alerts for High Risk Patients
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Outlier Distribution by Groups */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Outlier Distribution by Group</Typography>
            <Box sx={{ height: 400 }}>
              {createPopulationOutlierChart() ? (
                <Chart type="bar" data={createPopulationOutlierChart()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: { type: 'linear', display: true, position: 'left' },
                    y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false } }
                  }
                }} />
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Typography variant="body2" color="text.secondary">No population outlier data available</Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Group Selector for Detailed View */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Detailed Group Analysis</Typography>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Select Group</InputLabel>
              <Select 
                value={selectedGroup} 
                onChange={(e) => setSelectedGroup(e.target.value)}
              >
                {Object.keys(data.groups).map(group => (
                  <MenuItem key={group} value={group}>{group}</MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {selectedGroup && data.groups[selectedGroup] && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Patients: {data.groups[selectedGroup].patient_count}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Registered: {data.groups[selectedGroup].registered_patients}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  With Outliers: {data.groups[selectedGroup].patients_with_outliers}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Outliers: {data.groups[selectedGroup].total_outliers}
                </Typography>
                <Typography variant="body2" color="error.main">
                  High Risk: {data.groups[selectedGroup].high_risk_patients?.length || 0}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Outlier Type Heatmap */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Outlier Type Distribution Heatmap</Typography>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Outlier Type</strong></TableCell>
                    {createOutlierTypeHeatmap()?.groups.map((group: string) => (
                      <TableCell key={group} align="center"><strong>{group}</strong></TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {createOutlierTypeHeatmap()?.heatmapData.map((row: any) => (
                    <TableRow key={row.type}>
                      <TableCell>
                        <strong>{row.type.replace('_', ' ').toUpperCase()}</strong>
                      </TableCell>
                      {row.data.map((count: number, index: number) => {
                        const intensity = Math.min(count / 5, 1); // Normalize to 0-1
                        const bgColor = `rgba(244, 67, 54, ${intensity})`;
                        return (
                          <TableCell 
                            key={index}
                            align="center"
                            sx={{ 
                              backgroundColor: bgColor,
                              color: intensity > 0.5 ? 'white' : 'black',
                              fontWeight: 'bold'
                            }}
                          >
                            {count}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* High Risk Patients List */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Top 10 Highest Risk Patients (Across All Groups)
            </Typography>
            <List>
              {getHighestRiskPatients().map((patient: any, index: number) => (
                <ListItem 
                  key={index}
                  sx={{ 
                    border: '1px solid #ffcdd2', 
                    borderRadius: 1, 
                    mb: 1,
                    bgcolor: index < 3 ? '#ffebee' : 'transparent'
                  }}
                >
                  <ListItemIcon>
                    <Typography variant="h6" color="error.main">
                      {index < 3 ? '🚨' : '⚠️'}
                    </Typography>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" fontWeight="bold">
                          {patient.patient_name}
                        </Typography>
                        <Chip 
                          label={patient.group}
                          size="small"
                          color="info"
                        />
                        <Chip 
                          label={`${patient.high_severity_outliers} high-severity outliers`}
                          size="small"
                          color="error"
                        />
                      </Box>
                    }
                    secondary={`Patient ID: ${patient.patient_id}`}
                  />
                  <Button 
                    variant="outlined" 
                    color="error" 
                    size="small"
                    onClick={() => fetchPatientDetails(patient.patient_id)}
                    disabled={patientDetailsLoading}
                  >
                    {patientDetailsLoading ? 'Loading...' : 'View Details'}
                  </Button>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>

      {/* Alert Generation Dialog */}
      <Dialog 
        open={alertDialogOpen} 
        onClose={() => setAlertDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Generate High Risk Patient Alerts</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            This will generate immediate alerts for all high-risk patients identified in the analysis.
          </Typography>
          
          <Alert severity="warning" sx={{ my: 2 }}>
            {getHighestRiskPatients().length} patients will receive priority alerts for immediate review.
          </Alert>
          
          <Typography variant="h6" gutterBottom>Alert Recipients:</Typography>
          <List dense>
            {getHighestRiskPatients().slice(0, 5).map((patient: any, index: number) => (
              <ListItem key={index}>
                <ListItemText 
                  primary={patient.patient_name}
                  secondary={`${patient.group} - ${patient.high_severity_outliers} severe outliers`}
                />
              </ListItem>
            ))}
            {getHighestRiskPatients().length > 5 && (
              <ListItem>
                <ListItemText primary={`... and ${getHighestRiskPatients().length - 5} more patients`} />
              </ListItem>
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlertDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error">
            Generate Alerts
          </Button>
        </DialogActions>
      </Dialog>

      {/* Patient Details Dialog */}
      <Dialog 
        open={patientDetailsOpen} 
        onClose={() => setPatientDetailsOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h5">
              {selectedPatientDetails?.profile?.name || 'Patient Details'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Last Updated: {selectedPatientDetails?.lastUpdated ? new Date(selectedPatientDetails.lastUpdated).toLocaleString() : 'N/A'}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedPatientDetails && (
            <Grid container spacing={3}>
              {/* Patient Profile Section */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      👤 Patient Profile
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">Patient ID</Typography>
                      <Typography variant="body1" fontWeight="bold">{selectedPatientDetails.profile?.id}</Typography>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">Name</Typography>
                      <Typography variant="body1" fontWeight="bold">{selectedPatientDetails.profile?.name}</Typography>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">Email</Typography>
                      <Typography variant="body1">{selectedPatientDetails.profile?.email || 'Not provided'}</Typography>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">Condition</Typography>
                      <Chip 
                        label={selectedPatientDetails.profile?.condition || 'Unknown'}
                        color={selectedPatientDetails.profile?.condition?.includes('Type 2') ? 'error' : 'warning'}
                        size="small"
                      />
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">Registration Status</Typography>
                      <Chip 
                        label={selectedPatientDetails.outliers?.registration_status === 'registered' ? 'Active' : 'Not Registered'}
                        color={selectedPatientDetails.outliers?.registration_status === 'registered' ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">Registration Date</Typography>
                      <Typography variant="body1">
                        {selectedPatientDetails.profile?.created_at ? 
                          new Date(selectedPatientDetails.profile.created_at).toLocaleDateString() : 'N/A'}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Points of Attention Section */}
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="error">
                      ⚠️ Points of Attention & Risk Factors
                    </Typography>
                    {selectedPatientDetails.outliers?.registration_status === 'registered' ? (
                      <>
                        {selectedPatientDetails.outliers?.outliers?.length > 0 ? (
                          <List>
                            {selectedPatientDetails.outliers.outliers.map((outlier: any, index: number) => (
                              <ListItem 
                                key={index}
                                sx={{ 
                                  border: '1px solid #ffcdd2', 
                                  borderRadius: 1, 
                                  mb: 1,
                                  bgcolor: outlier.severity === 'high' ? '#ffebee' : 'transparent'
                                }}
                              >
                                <ListItemIcon>
                                  <Typography variant="h6">
                                    {outlier.severity === 'high' ? '🚨' : '⚠️'}
                                  </Typography>
                                </ListItemIcon>
                                <ListItemText
                                  primary={
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      <Chip 
                                        label={outlier.severity?.toUpperCase()}
                                        color={outlier.severity === 'high' ? 'error' : 'warning'}
                                        size="small"
                                      />
                                      <Typography variant="body1" fontWeight="bold">
                                        {outlier.nutrient || outlier.food_name}
                                      </Typography>
                                    </Box>
                                  }
                                  secondary={
                                    <Box>
                                      <Typography variant="body2">
                                        Current: {outlier.value} | Expected: {outlier.expected_range}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary">
                                        Date: {outlier.date}
                                      </Typography>
                                    </Box>
                                  }
                                />
                              </ListItem>
                            ))}
                          </List>
                        ) : (
                          <Alert severity="success">
                            No significant outliers detected. Patient appears to be following their care plan well.
                          </Alert>
                        )}

                        {/* Recommendations */}
                        {selectedPatientDetails.outliers?.summary?.recommendations?.length > 0 && (
                          <Box sx={{ mt: 3 }}>
                            <Typography variant="h6" gutterBottom>📋 Recommendations</Typography>
                            {selectedPatientDetails.outliers.summary.recommendations.map((rec: any, index: number) => (
                              <Alert 
                                key={index}
                                severity={rec.priority === 'immediate' ? 'error' : 'warning'}
                                sx={{ mb: 1 }}
                              >
                                <Typography variant="subtitle2">{rec.message}</Typography>
                                <Typography variant="body2">{rec.action}</Typography>
                              </Alert>
                            ))}
                          </Box>
                        )}
                      </>
                    ) : (
                      <Alert severity="info">
                        Patient has not registered yet. No consumption data available for analysis.
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Last 48 Hours Food History */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      🍽️ Last 48 Hours Food Log History
                    </Typography>
                    {selectedPatientDetails.recentHistory?.length > 0 ? (
                      <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                        <Table stickyHeader>
                          <TableHead>
                            <TableRow>
                              <TableCell><strong>Date & Time</strong></TableCell>
                              <TableCell><strong>Food Item</strong></TableCell>
                              <TableCell align="center"><strong>Calories</strong></TableCell>
                              <TableCell align="center"><strong>Carbs (g)</strong></TableCell>
                              <TableCell align="center"><strong>Protein (g)</strong></TableCell>
                              <TableCell align="center"><strong>Fat (g)</strong></TableCell>
                              <TableCell align="center"><strong>Fiber (g)</strong></TableCell>
                              <TableCell align="center"><strong>Sodium (mg)</strong></TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {selectedPatientDetails.recentHistory.map((entry: any, index: number) => {
                              const nutrition = entry.nutritional_info || {};
                              const dateTime = new Date(entry.timestamp || entry.date);
                              const isRecent = (new Date().getTime() - dateTime.getTime()) <= (24 * 60 * 60 * 1000); // Last 24 hours
                              
                              return (
                                <TableRow 
                                  key={index}
                                  sx={{ 
                                    bgcolor: isRecent ? '#e3f2fd' : 'transparent',
                                    '&:hover': { bgcolor: '#f5f5f5' }
                                  }}
                                >
                                  <TableCell>
                                    <Box>
                                      <Typography variant="body2" fontWeight="bold">
                                        {dateTime.toLocaleDateString()}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary">
                                        {dateTime.toLocaleTimeString()}
                                      </Typography>
                                    </Box>
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="body2" fontWeight="bold">
                                      {entry.food_name}
                                    </Typography>
                                    {entry.portion && (
                                      <Typography variant="body2" color="text.secondary">
                                        Portion: {entry.portion}
                                      </Typography>
                                    )}
                                  </TableCell>
                                  <TableCell align="center">
                                    <Chip 
                                      label={nutrition.calories || 0}
                                      size="small"
                                      color={nutrition.calories > 500 ? 'error' : nutrition.calories > 200 ? 'warning' : 'default'}
                                    />
                                  </TableCell>
                                  <TableCell align="center">{nutrition.carbohydrates?.toFixed(1) || 0}</TableCell>
                                  <TableCell align="center">{nutrition.protein?.toFixed(1) || 0}</TableCell>
                                  <TableCell align="center">{nutrition.fat?.toFixed(1) || 0}</TableCell>
                                  <TableCell align="center">{nutrition.fiber?.toFixed(1) || 0}</TableCell>
                                  <TableCell align="center">{nutrition.sodium?.toFixed(0) || 0}</TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    ) : (
                      <Alert severity="info">
                        No food consumption data available for the last 48 hours.
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Health Metrics Summary */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      📊 Health Metrics Summary
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} md={3}>
                        <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                          <Typography variant="h4" color="error.main">
                            {selectedPatientDetails.outliers?.summary?.total_outliers || 0}
                          </Typography>
                          <Typography variant="body2">Total Outliers</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                          <Typography variant="h4" color="error.main">
                            {selectedPatientDetails.outliers?.summary?.high_severity || 0}
                          </Typography>
                          <Typography variant="body2">High Severity</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                          <Typography variant="h4" color="warning.main">
                            {selectedPatientDetails.outliers?.summary?.moderate_severity || 0}
                          </Typography>
                          <Typography variant="body2">Moderate Severity</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                          <Typography variant="h4" color="info.main">
                            {selectedPatientDetails.recentHistory?.length || 0}
                          </Typography>
                          <Typography variant="body2">Recent Logs (48h)</Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPatientDetailsOpen(false)}>Close</Button>
          <Button variant="contained" color="primary">
            Export Report
          </Button>
          <Button variant="contained" color="error">
            Schedule Follow-up
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
};

// Main OutlierDetection Component
const OutlierDetection: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Advanced outlier detection for patient ${selectedPatient}`
        : 'Please select a patient to view individual outlier analysis';
    }
    return `Population outlier analysis grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        ⚠️ Outlier Detection & Risk Analysis
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {viewMode === 'individual' ? (
        selectedPatient ? (
          <IndividualOutlierAnalysis selectedPatient={selectedPatient} />
        ) : (
          <Alert severity="warning">
            Please select a patient from the dropdown above to view individual outlier analysis.
          </Alert>
        )
      ) : (
        <CohortOutlierAnalysis groupingCriteria={groupingCriteria || 'diabetes_type'} />
      )}
    </Box>
  );
};

export default OutlierDetection; 