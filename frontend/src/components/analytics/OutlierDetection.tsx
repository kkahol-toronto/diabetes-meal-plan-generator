import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Avatar, IconButton, Tooltip, CircularProgress
} from '@mui/material';
import {
  Warning as WarningIcon,
  ErrorOutline as ErrorIcon,
  Info as InfoIcon,
  Visibility as ViewIcon,
  Flag as FlagIcon,
  TrendingDown as TrendingDownIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as TimeIcon
} from '@mui/icons-material';
import config from '../../config/environment';

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

const OutlierDetection: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOutlierData();
  }, [viewMode, selectedPatient, groupingCriteria]);

  const fetchOutlierData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        view_mode: viewMode,
        group_by: groupingCriteria || 'diabetes_type'
      });

      if (viewMode === 'individual' && selectedPatient) {
        params.append('patient_id', selectedPatient);
      }

      const response = await fetch(`${config.API_URL}/admin/analytics/outlier-detection?${params}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch outlier data');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch outlier data:', error);
      setLoading(false);
    }
  };

  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Outlier detection for patient ${selectedPatient}`
        : 'Please select a patient to view individual outlier analysis';
    }
    return `Cohort outlier detection grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical': return <ErrorIcon color="error" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'info': return <InfoIcon color="info" />;
      default: return <InfoIcon />;
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
        Failed to load outlier detection data.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        ⚠️ Outlier Detection & Risk Alerts
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {/* Individual Patient View */}
      {viewMode === 'individual' && data.registration_status === 'not_registered' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          This patient has not registered yet. No consumption data available for outlier analysis.
        </Alert>
      )}

      {/* Alert Summary Cards */}
      {data.alerts && data.alerts.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {data.alerts.map((alert: any, index: number) => (
            <Grid item xs={12} md={4} key={index}>
              <Card sx={{ 
                bgcolor: alert.type === 'critical' ? 'error.light' : 
                        alert.type === 'warning' ? 'warning.light' : 'info.light',
                color: 'white'
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                      {getAlertIcon(alert.type)}
                    </Avatar>
                    <Box>
                      <Typography variant="h4" fontWeight="bold">
                        {alert.count || alert.patient_count || 1}
                      </Typography>
                      <Typography variant="body2">
                        {alert.message}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Individual Patient Outliers */}
      {viewMode === 'individual' && data.outliers && data.outliers.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🔍 Detected Issues for {data.patient_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Risk Score: {data.risk_score}/100
                </Typography>
                
                <Grid container spacing={2}>
                  {data.outliers.map((outlier: any, index: number) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Alert severity={outlier.severity === 'high' ? 'error' : 'warning'}>
                        <Typography variant="body2" fontWeight="bold">
                          {outlier.anomaly}
                        </Typography>
                        <Typography variant="body2">
                          Value: {outlier.value?.toFixed(1)} | Target: {outlier.threshold}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                          💡 {outlier.recommendation}
                        </Typography>
                      </Alert>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Cohort Outlier Patients Table */}
      {viewMode === 'cohort' && data.outlier_patients && data.outlier_patients.length > 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🔍 Patients Requiring Attention
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {data.outlier_patients.length} patients identified as statistical outliers based on health metrics, 
                  engagement patterns, and compliance indicators.
                </Typography>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Patient</TableCell>
                        <TableCell>Condition</TableCell>
                        <TableCell>Detected Anomaly</TableCell>
                        <TableCell>Risk Score</TableCell>
                        <TableCell>Severity</TableCell>
                        <TableCell>Last Active</TableCell>
                        <TableCell>Group</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.outlier_patients.map((patient: any) => (
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
                          <TableCell>{patient.condition}</TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {patient.anomaly}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body2" fontWeight="bold">
                                {patient.risk_score}
                              </Typography>
                              {patient.risk_score > 80 ? (
                                <TrendingUpIcon color="error" fontSize="small" />
                              ) : (
                                <TrendingDownIcon color="success" fontSize="small" />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={patient.severity.toUpperCase()} 
                              color={getSeverityColor(patient.severity) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <TimeIcon fontSize="small" color="action" />
                              <Typography variant="body2">
                                {patient.last_active}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip label={patient.group} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Tooltip title="View Patient Profile">
                                <IconButton size="small">
                                  <ViewIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Flag for Follow-up">
                                <IconButton size="small">
                                  <FlagIcon />
                                </IconButton>
                              </Tooltip>
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
        </Grid>
      )}

      {/* No Outliers Found */}
      {((viewMode === 'cohort' && (!data.outlier_patients || data.outlier_patients.length === 0)) ||
        (viewMode === 'individual' && data.registration_status === 'registered' && (!data.outliers || data.outliers.length === 0))) && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {viewMode === 'individual' 
            ? `No significant outliers detected for ${data.patient_name}. Patient appears to be following recommended patterns.`
            : 'No significant outliers detected in the patient cohort. All patients appear to be following recommended patterns.'
          }
        </Alert>
      )}

      {/* Additional Information */}
      <Grid container spacing={3}>
        {/* Detection Rules */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🎯 Active Detection Rules
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Automated rules triggering outlier alerts.
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                {[
                  'Blood glucose >300 mg/dL or <70 mg/dL',
                  'No food logging for >48 hours',
                  'Carb intake >2x recommended daily amount',
                  'Weight change >5 lbs in 7 days',
                  'No platform activity for >7 days'
                ].map((rule, index) => (
                  <Alert severity="info" sx={{ mb: 1 }} key={index}>
                    {rule}
                  </Alert>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recommended Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🔧 Recommended Actions
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Suggested interventions for detected outliers.
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                {[
                  'Schedule immediate consultation for high-risk patients',
                  'Send automated reminder notifications',
                  'Adjust meal plan recommendations',
                  'Escalate to primary care physician',
                  'Initiate re-engagement protocol'
                ].map((action, index) => (
                  <Alert severity="warning" sx={{ mb: 1 }} key={index}>
                    {action}
                  </Alert>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OutlierDetection; 