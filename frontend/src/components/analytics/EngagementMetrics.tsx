import React from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Avatar, List, ListItem, ListItemText,
  ListItemAvatar, Chip
} from '@mui/material';
import {
  AccessTime as TimeIcon,
  PhoneAndroid as PhoneIcon,
  Restaurant as RestaurantIcon,
  Chat as ChatIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';

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
  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Engagement metrics for patient ${selectedPatient}`
        : 'Please select a patient to view individual engagement data';
    }
    return `Cohort engagement metrics grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  const mockEngagementData = [
    { metric: 'Daily Active Users', value: '67%', trend: 'up', change: '+5%' },
    { metric: 'Avg. Session Duration', value: '12.5 min', trend: 'up', change: '+2.3 min' },
    { metric: 'Meal Logging Rate', value: '78%', trend: 'stable', change: '±0%' },
    { metric: 'Chat Interactions', value: '145/week', trend: 'up', change: '+12%' },
  ];

  const mockUserActivity = [
    { name: 'Morning Logins', percentage: 85, color: '#ff9800' },
    { name: 'Meal Photo Uploads', percentage: 65, color: '#4caf50' },
    { name: 'Chat Usage', percentage: 45, color: '#2196f3' },
    { name: 'Recipe Views', percentage: 72, color: '#9c27b0' },
  ];

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
              <Grid container spacing={2} sx={{ mt: 1 }}>
                {mockEngagementData.map((item, index) => (
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
                        <Typography variant="body2" color="text.secondary">
                          {item.metric}
                        </Typography>
                        <Chip 
                          label={item.change} 
                          size="small" 
                          color={item.trend === 'up' ? 'success' : item.trend === 'down' ? 'error' : 'default'}
                          sx={{ mt: 1 }}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
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
                {mockUserActivity.map((activity, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">{activity.name}</Typography>
                      <Typography variant="body2" fontWeight="bold">{activity.percentage}%</Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={activity.percentage} 
                      sx={{ 
                        height: 8, 
                        borderRadius: 4,
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: activity.color
                        }
                      }}
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Feature Usage */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🔧 Feature Usage Ranking
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Most and least used platform features.
              </Typography>
              
              <List dense>
                {[
                  { name: 'Meal Plan Generation', usage: '95%', icon: <RestaurantIcon /> },
                  { name: 'Food Logging', usage: '78%', icon: <PhoneIcon /> },
                  { name: 'AI Chat Assistant', usage: '65%', icon: <ChatIcon /> },
                  { name: 'Progress Tracking', usage: '52%', icon: <TrendingUpIcon /> },
                  { name: 'Social Features', usage: '23%', icon: <TimeIcon /> },
                ].map((feature, index) => (
                  <ListItem key={index}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        {feature.icon}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText 
                      primary={feature.name}
                      secondary={`${feature.usage} of users`}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Engagement Insights */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💡 Engagement Insights & Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Alert severity="success">
                    <strong>High Engagement:</strong> Morning users show 85% higher compliance rates
                  </Alert>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Alert severity="warning">
                    <strong>Opportunity:</strong> Only 23% use social features - potential for community building
                  </Alert>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Alert severity="info">
                    <strong>Trending:</strong> Chat interactions up 12% this week - users seeking more guidance
                  </Alert>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EngagementMetrics; 