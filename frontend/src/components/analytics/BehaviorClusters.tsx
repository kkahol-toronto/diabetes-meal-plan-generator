import React from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  Avatar, AvatarGroup, List, ListItem, ListItemText,
  Chip, LinearProgress, Divider
} from '@mui/material';
import {
  People as PeopleIcon,
  Psychology as PsychologyIcon,
  Schedule as ScheduleIcon,
  Restaurant as RestaurantIcon,
  TrendingUp as TrendingUpIcon,
  Group as GroupIcon
} from '@mui/icons-material';

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

const BehaviorClusters: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Behavioral cluster analysis for patient ${selectedPatient}`
        : 'Please select a patient to view individual behavioral patterns';
    }
    return `Cohort behavioral clustering grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  const mockClusters = [
    {
      id: 'morning-warriors',
      name: 'Morning Warriors',
      description: 'Early risers with consistent morning routines',
      size: 34,
      characteristics: [
        'Log meals before 8 AM',
        'High morning engagement',
        'Consistent exercise patterns',
        'Above-average compliance (87%)'
      ],
      color: '#ff9800',
      outcomes: 'Excellent glucose control'
    },
    {
      id: 'social-eaters',
      name: 'Social Eaters',
      description: 'Meal patterns influenced by social activities',
      size: 28,
      characteristics: [
        'Weekend dining out spikes',
        'Higher carb intake on social occasions',
        'Active in community features',
        'Moderate compliance (65%)'
      ],
      color: '#4caf50',
      outcomes: 'Variable glucose levels'
    },
    {
      id: 'stress-responders',
      name: 'Stress Responders',
      description: 'Food choices correlate with stress indicators',
      size: 19,
      characteristics: [
        'Irregular meal timing',
        'Comfort food preferences',
        'Lower engagement during stressful periods',
        'Needs intervention (45% compliance)'
      ],
      color: '#f44336',
      outcomes: 'Requires close monitoring'
    },
    {
      id: 'tech-savvy',
      name: 'Tech Savvy',
      description: 'High engagement with all digital features',
      size: 42,
      characteristics: [
        'Daily app usage >30 minutes',
        'Frequent photo logging',
        'Active chat usage',
        'High compliance (92%)'
      ],
      color: '#2196f3',
      outcomes: 'Optimal health outcomes'
    }
  ];

  const mockPatternInsights = [
    { pattern: 'Meal Timing Consistency', impact: 'High', correlation: '+23% better glucose control' },
    { pattern: 'Weekend Behavior Variance', impact: 'Medium', correlation: '15% compliance drop on weekends' },
    { pattern: 'Social Influence', impact: 'High', correlation: 'Peer support increases adherence by 31%' },
    { pattern: 'Stress-Food Correlation', impact: 'High', correlation: 'Stress events lead to 40% more carb intake' },
  ];

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        🔍 Behavioral Pattern Clusters
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {/* Cluster Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {mockClusters.map((cluster) => (
          <Grid item xs={12} md={6} key={cluster.id}>
            <Card sx={{ 
              border: `2px solid ${cluster.color}33`,
              '&:hover': { 
                boxShadow: `0 4px 20px ${cluster.color}22`,
                transform: 'translateY(-2px)'
              },
              transition: 'all 0.3s ease'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Avatar sx={{ bgcolor: cluster.color, width: 48, height: 48 }}>
                    <GroupIcon />
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" fontWeight="bold">
                      {cluster.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {cluster.description}
                    </Typography>
                    <Chip 
                      label={`${cluster.size} patients`} 
                      size="small" 
                      sx={{ 
                        mt: 1,
                        bgcolor: cluster.color + '22',
                        color: cluster.color
                      }}
                    />
                  </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom>
                  Key Characteristics:
                </Typography>
                <List dense>
                  {cluster.characteristics.map((char, index) => (
                    <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                      <ListItemText 
                        primary={char}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>

                <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="body2" fontWeight="bold" color={cluster.color}>
                    Outcome: {cluster.outcomes}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Pattern Analysis */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Behavioral Pattern Impact Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Correlation between behavioral patterns and health outcomes.
              </Typography>

              <Box sx={{ mt: 3 }}>
                {mockPatternInsights.map((insight, index) => (
                  <Box key={index} sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {insight.pattern}
                      </Typography>
                      <Chip 
                        label={`${insight.impact} Impact`}
                        size="small"
                        color={insight.impact === 'High' ? 'error' : insight.impact === 'Medium' ? 'warning' : 'success'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {insight.correlation}
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={insight.impact === 'High' ? 85 : insight.impact === 'Medium' ? 60 : 35}
                      color={insight.impact === 'High' ? 'error' : insight.impact === 'Medium' ? 'warning' : 'success'}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🎯 Intervention Strategies
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Targeted approaches for each behavioral cluster.
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Alert severity="success" sx={{ mb: 2 }}>
                  <strong>Morning Warriors:</strong> Leverage their consistency for peer mentoring
                </Alert>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <strong>Tech Savvy:</strong> Beta test new features and gamification
                </Alert>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <strong>Social Eaters:</strong> Provide social dining strategies and group challenges
                </Alert>
                <Alert severity="error" sx={{ mb: 2 }}>
                  <strong>Stress Responders:</strong> Implement stress management tools and flexible plans
                </Alert>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📈 Cluster Migration
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Patients moving between behavioral clusters.
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Positive Migrations:</strong> 12 patients moved to higher-performing clusters
                </Typography>
                <Typography variant="body2">
                  <strong>At-Risk Migrations:</strong> 5 patients moved to stress-responder cluster
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BehaviorClusters; 