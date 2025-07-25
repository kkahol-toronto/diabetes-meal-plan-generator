import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Avatar, List, ListItem, ListItemText,
  ListItemAvatar, Chip, CircularProgress
} from '@mui/material';
import {
  AccessTime as TimeIcon,
  PhoneAndroid as PhoneIcon,
  Restaurant as RestaurantIcon,
  Chat as ChatIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import config from '../../config/environment';

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

const EngagementMetrics: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEngagementData();
  }, [viewMode, selectedPatient, groupingCriteria]);

  const fetchEngagementData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        view_mode: viewMode,
        group_by: groupingCriteria || 'diabetes_type'
      });

      if (viewMode === 'individual' && selectedPatient) {
        params.append('patient_id', selectedPatient);
      }

      const response = await fetch(`${config.API_URL}/admin/analytics/engagement-metrics?${params}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch engagement data');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch engagement data:', error);
      setLoading(false);
    }
  };

  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Engagement metrics for patient ${selectedPatient}`
        : 'Please select a patient to view individual engagement data';
    }
    return `Cohort engagement metrics grouped by ${groupingCriteria?.replace('_', ' ')}`;
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
        Failed to load engagement metrics.
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
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        📱 Engagement Metrics
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      <Grid container spacing={3}>
        {/* Key Engagement Metrics */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Key Engagement Indicators
              </Typography>
              {viewMode === 'individual' && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Analysis period: {data.period_days} days
                </Typography>
              )}
              <Grid container spacing={2} sx={{ mt: 1 }}>
                {data.engagement_metrics?.map((item: any, index: number) => (
                  <Grid item xs={12} sm={6} md={3} key={index}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="h4" fontWeight="bold" color="primary">
                            {item.value}
                          </Typography>
                          {item.trend === 'up' ? (
                            <TrendingUpIcon color="success" />
                          ) : item.trend === 'down' ? (
                            <TrendingDownIcon color="error" />
                          ) : null}
                        </Box>
                        
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          {item.metric}
                        </Typography>
                        
                        <Chip 
                          label={item.change} 
                          size="small" 
                          color={item.trend === 'up' ? 'success' : item.trend === 'down' ? 'error' : 'default'}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                )) || []}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Activity Breakdown */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🎯 Activity Breakdown
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Platform usage patterns across different features and times of day.
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                {(viewMode === 'individual' ? data.activity_breakdown : data.activity_summary)?.map((activity: any, index: number) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">{activity.name}</Typography>
                      <Typography variant="body2" fontWeight="bold">{activity.percentage.toFixed(1)}%</Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.min(activity.percentage, 100)} 
                      sx={{ 
                        height: 8, 
                        borderRadius: 4,
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: activity.color
                        }
                      }}
                    />
                  </Box>
                )) || []}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Cohort Group Details */}
        {viewMode === 'cohort' && data.groups && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📊 Group Summary
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Engagement metrics by patient group
                </Typography>
                
                <List>
                  {Object.entries(data.groups).map(([groupName, groupData]: [string, any]) => (
                    <ListItem key={groupName}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          {groupName.charAt(0).toUpperCase()}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={groupName}
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              {groupData.registered_patients} registered of {groupData.total_patients} total
                            </Typography>
                            <Typography variant="caption" display="block">
                              {groupData.avg_daily_active_rate.toFixed(1)}% daily active rate
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Engagement Summary */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💡 Engagement Summary
              </Typography>
              
              {viewMode === 'cohort' ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h3" color="primary.main" fontWeight="bold">
                        {data.total_patients}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Patients
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h3" color="success.main" fontWeight="bold">
                        {Object.values(data.groups).reduce((sum: number, group: any) => sum + group.registered_patients, 0)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Registered Users
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h3" color="warning.main" fontWeight="bold">
                        {(Object.values(data.groups).reduce((sum: number, group: any) => sum + group.avg_daily_active_rate, 0) / Math.max(Object.keys(data.groups).length, 1)).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Daily Activity
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h3" color="info.main" fontWeight="bold">
                        {(Object.values(data.groups).reduce((sum: number, group: any) => sum + group.avg_meal_logging_rate, 0) / Math.max(Object.keys(data.groups).length, 1)).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Meal Logging
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Alert severity="info">
                  Individual patient engagement analysis for {data.patient_name}. 
                  Based on {data.period_days} days of activity data.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EngagementMetrics; 