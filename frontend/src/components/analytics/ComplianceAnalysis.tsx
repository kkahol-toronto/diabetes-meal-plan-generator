import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Avatar, IconButton, CircularProgress
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Star as StarIcon,
  Flag as FlagIcon
} from '@mui/icons-material';
import config from '../../config/environment';

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

const ComplianceAnalysis: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComplianceData();
  }, [viewMode, selectedPatient, groupingCriteria]);

  const fetchComplianceData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        view_mode: viewMode,
        group_by: groupingCriteria || 'diabetes_type'
      });

      if (viewMode === 'individual' && selectedPatient) {
        params.append('patient_id', selectedPatient);
      }

      const response = await fetch(`${config.API_URL}/admin/analytics/compliance-analysis?${params}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch compliance data');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch compliance data:', error);
      setLoading(false);
    }
  };

  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Compliance analysis for patient ${selectedPatient}`
        : 'Please select a patient to view individual compliance data';
    }
    return `Cohort compliance analysis grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  const getComplianceColor = (value: number) => {
    if (value >= 85) return '#4caf50';
    if (value >= 70) return '#ff9800';
    return '#f44336';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'success';
      case 'good': return 'info';
      case 'needs-improvement': return 'warning';
      default: return 'default';
    }
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
        Failed to load compliance data.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        ✅ Compliance Analysis & Monitoring
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {/* Individual Patient View - Not Registered */}
      {viewMode === 'individual' && data.registration_status === 'not_registered' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          This patient has not registered yet. No compliance data available for analysis.
        </Alert>
      )}

      {/* Compliance Metrics Overview */}
      {data.compliance_metrics && data.compliance_metrics.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {data.compliance_metrics.map((metric: any, index: number) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h4" fontWeight="bold" color={getComplianceColor(metric.value)}>
                      {metric.value}%
                    </Typography>
                    {metric.trend === 'up' ? (
                      <TrendingUpIcon color="success" />
                    ) : metric.trend === 'down' ? (
                      <TrendingDownIcon color="error" />
                    ) : null}
                  </Box>
                  
                  <Typography variant="body2" fontWeight="bold" gutterBottom>
                    {metric.metric}
                  </Typography>
                  
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Target: {metric.target}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={(metric.value / metric.target) * 100} 
                      sx={{ 
                        mt: 1,
                        height: 6, 
                        borderRadius: 3,
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: getComplianceColor(metric.value)
                        }
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Individual Patient Details */}
      {viewMode === 'individual' && data.patient_details && Object.keys(data.patient_details).length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📋 Patient Compliance Details - {data.patient_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Detailed breakdown of compliance metrics for this patient.
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Overall Score</Typography>
                    <Typography variant="h4" color={getComplianceColor(data.patient_details.overall)}>
                      {data.patient_details.overall}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Current Streak</Typography>
                    <Typography variant="h4" color="primary">
                      {data.patient_details.streak} days
                    </Typography>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Total Logs</Typography>
                    <Typography variant="h4" color="secondary">
                      {data.patient_details.total_logs}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Status</Typography>
                    <Chip 
                      label={data.patient_details.status.toUpperCase()} 
                      color={getStatusColor(data.patient_details.status) as any}
                      sx={{ mt: 1 }}
                    />
                  </Grid>
                </Grid>

                {data.recommendations && data.recommendations.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="h6" gutterBottom>💡 Recommendations</Typography>
                    {data.recommendations.map((rec: string, index: number) => (
                      <Alert severity="info" sx={{ mb: 1 }} key={index}>
                        {rec}
                      </Alert>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Cohort Patient Compliance Table */}
      {viewMode === 'cohort' && data.patient_compliance && data.patient_compliance.length > 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📋 Individual Patient Compliance
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Detailed compliance tracking across key health management areas for {data.patient_compliance.length} registered patients.
                </Typography>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Patient</TableCell>
                        <TableCell>Overall</TableCell>
                        <TableCell>Meal Plan</TableCell>
                        <TableCell>Nutrition</TableCell>
                        <TableCell>Logging</TableCell>
                        <TableCell>Streak</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Group</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.patient_compliance.map((patient: any) => (
                        <TableRow key={patient.id}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Avatar sx={{ width: 32, height: 32 }}>
                                {patient.name.charAt(0)}
                              </Avatar>
                              <Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {patient.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {patient.id}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold" color={getComplianceColor(patient.overall)}>
                              {patient.overall}%
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color={getComplianceColor(patient.meal_plan)}>
                              {patient.meal_plan}%
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color={getComplianceColor(patient.nutrition)}>
                              {patient.nutrition}%
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color={getComplianceColor(patient.logging)}>
                              {patient.logging}%
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <ScheduleIcon fontSize="small" color="action" />
                              <Typography variant="body2" fontWeight="bold">
                                {patient.streak} days
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={patient.status.toUpperCase()} 
                              color={getStatusColor(patient.status) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip label={patient.group} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <IconButton size="small">
                                <CheckCircleIcon />
                              </IconButton>
                              <IconButton size="small">
                                <FlagIcon />
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

          {/* Compliance Champions */}
          <Grid item xs={12} lg={4}>
            <Card sx={{ height: 'fit-content' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🏆 Compliance Champions
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Top performers this month.
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  {data.top_performers && data.top_performers.length > 0 ? 
                    data.top_performers.map((champion: any, index: number) => (
                      <Box key={champion.id} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                        <Avatar sx={{ bgcolor: 'success.main', color: 'white', width: 32, height: 32 }}>
                          {index + 1}
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" fontWeight="bold" color="success.contrastText">
                            {champion.name}
                          </Typography>
                          <Typography variant="caption" color="success.contrastText">
                            {champion.overall}% compliance • {champion.streak} day streak
                          </Typography>
                        </Box>
                        <StarIcon sx={{ color: 'success.contrastText' }} />
                      </Box>
                    )) :
                    <Typography variant="body2" color="text.secondary">
                      No top performers to display yet.
                    </Typography>
                  }
                </Box>
              </CardContent>
            </Card>

            {/* Needs Attention */}
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  ⚠️ Needs Attention
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Patients requiring intervention.
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  {data.needs_attention && data.needs_attention.length > 0 ? 
                    data.needs_attention.map((patient: any) => (
                      <Alert 
                        key={patient.id}
                        severity="warning" 
                        sx={{ mb: 1 }}
                        action={
                          <IconButton size="small" color="inherit">
                            <FlagIcon />
                          </IconButton>
                        }
                      >
                        <Typography variant="body2">
                          <strong>{patient.name}</strong> - {patient.overall}% compliance
                        </Typography>
                      </Alert>
                    )) :
                    <Typography variant="body2" color="text.secondary">
                      No patients requiring immediate attention.
                    </Typography>
                  }
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* No Data Message */}
      {((viewMode === 'cohort' && (!data.patient_compliance || data.patient_compliance.length === 0)) ||
        (viewMode === 'individual' && data.registration_status === 'registered' && (!data.patient_details || Object.keys(data.patient_details).length === 0))) && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {viewMode === 'individual' 
            ? `No compliance data available for ${data.patient_name}. Patient may need to start logging activities.`
            : 'No registered patients with compliance data found for analysis.'
          }
        </Alert>
      )}
    </Box>
  );
};

export default ComplianceAnalysis; 