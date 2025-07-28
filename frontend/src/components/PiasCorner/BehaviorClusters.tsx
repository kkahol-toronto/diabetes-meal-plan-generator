import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
} from '@mui/material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { People, TrendingUp, TrendingFlat, TrendingDown, Star, Warning, CheckCircle } from '@mui/icons-material';
import config from '../../config/environment';

interface BehaviorCluster {
  high_engagement: any[];
  medium_engagement: any[];
  low_engagement: any[];
}

interface ComprehensiveAnalytics {
  behavior_clusters: BehaviorCluster;
  summary: any;
}

const BehaviorClusters: React.FC = () => {
  const [data, setData] = useState<ComprehensiveAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBehaviorData();
  }, []);

  const fetchBehaviorData = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`${config.API_URL}/admin/analytics/comprehensive`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch behavior cluster data');
      }

      const analyticsData = await response.json();
      setData(analyticsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load behavior cluster data');
      console.error('Error fetching behavior cluster data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading behavior clusters: {error}
        <Typography variant="body2" sx={{ mt: 1 }}>
          Using real patient behavior data from production database
        </Typography>
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        No behavior cluster data available yet. Data will appear as patients interact with the system.
      </Alert>
    );
  }

  const clusters = data.behavior_clusters;
  const highEngagement = clusters.high_engagement || [];
  const mediumEngagement = clusters.medium_engagement || [];
  const lowEngagement = clusters.low_engagement || [];

  const totalUsers = highEngagement.length + mediumEngagement.length + lowEngagement.length;

  // Create pie chart data
  const pieData = [
    { 
      name: 'High Engagement', 
      value: highEngagement.length, 
      color: '#4caf50',
      description: '10+ consumption logs'
    },
    { 
      name: 'Medium Engagement', 
      value: mediumEngagement.length, 
      color: '#ff9800',
      description: '5-10 consumption logs'
    },
    { 
      name: 'Low Engagement', 
      value: lowEngagement.length, 
      color: '#f44336',
      description: 'Less than 5 logs'
    }
  ];

  // Analyze behavior patterns for each cluster
  const analyzeBehaviorPatterns = (cluster: any[], clusterName: string) => {
    if (!cluster.length) return { patterns: [], avgProfile: null };

    const totalLogs = cluster.reduce((sum, user) => sum + user.consumption_count, 0);
    const avgLogs = totalLogs / cluster.length;
    
    // Analyze medical conditions
    const conditionsMap: { [key: string]: number } = {};
    cluster.forEach(user => {
      const conditions = user.profile?.medicalConditions || [];
      conditions.forEach((condition: string) => {
        conditionsMap[condition] = (conditionsMap[condition] || 0) + 1;
      });
    });

    const topConditions = Object.entries(conditionsMap)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([condition, count]) => ({ condition, count }));

    // Activity recency analysis
    const recentActivity = cluster.filter(user => {
      if (!user.last_activity) return false;
      const lastActivity = new Date(user.last_activity);
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return lastActivity > weekAgo;
    }).length;

    const patterns = [
      `Average ${avgLogs.toFixed(1)} consumption logs per user`,
      `${((recentActivity / cluster.length) * 100).toFixed(0)}% active in past week`,
      `Top condition: ${topConditions[0]?.condition || 'None'} (${topConditions[0]?.count || 0} users)`
    ];

    return { 
      patterns, 
      avgProfile: {
        avgLogs,
        recentActivityRate: (recentActivity / cluster.length) * 100,
        topConditions
      }
    };
  };

  const highEngagementAnalysis = analyzeBehaviorPatterns(highEngagement, 'High');
  const mediumEngagementAnalysis = analyzeBehaviorPatterns(mediumEngagement, 'Medium');
  const lowEngagementAnalysis = analyzeBehaviorPatterns(lowEngagement, 'Low');

  // Create comparison chart data
  const comparisonData = [
    {
      cluster: 'High',
      users: highEngagement.length,
      avgLogs: highEngagementAnalysis.avgProfile?.avgLogs || 0,
      recentActivity: highEngagementAnalysis.avgProfile?.recentActivityRate || 0
    },
    {
      cluster: 'Medium',
      users: mediumEngagement.length,
      avgLogs: mediumEngagementAnalysis.avgProfile?.avgLogs || 0,
      recentActivity: mediumEngagementAnalysis.avgProfile?.recentActivityRate || 0
    },
    {
      cluster: 'Low',
      users: lowEngagement.length,
      avgLogs: lowEngagementAnalysis.avgProfile?.avgLogs || 0,
      recentActivity: lowEngagementAnalysis.avgProfile?.recentActivityRate || 0
    }
  ];

  const getClusterIcon = (clusterName: string) => {
    switch (clusterName) {
      case 'High': return <Star sx={{ color: '#4caf50' }} />;
      case 'Medium': return <CheckCircle sx={{ color: '#ff9800' }} />;
      case 'Low': return <Warning sx={{ color: '#f44336' }} />;
      default: return <People />;
    }
  };

  const getClusterInsights = (clusterName: string, analysis: any) => {
    switch (clusterName) {
      case 'High':
        return {
          title: 'Champions',
          description: 'Highly engaged patients with consistent logging',
          action: 'Continue current engagement strategies',
          insights: [
            'Most likely to follow meal plans',
            'Regular platform usage',
            'Good candidates for peer mentoring'
          ]
        };
      case 'Medium':
        return {
          title: 'Steady Users',
          description: 'Moderately engaged with room for improvement',
          action: 'Provide gentle encouragement and reminders',
          insights: [
            'Potential for higher engagement',
            'May benefit from gamification',
            'Need periodic check-ins'
          ]
        };
      case 'Low':
        return {
          title: 'At-Risk Group',
          description: 'Low engagement, may need intervention',
          action: 'Proactive outreach and support needed',
          insights: [
            'Risk of dropping out',
            'May have barriers to engagement',
            'Need personalized intervention'
          ]
        };
      default:
        return {
          title: 'Unknown',
          description: '',
          action: '',
          insights: []
        };
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
        Patient Behavior Clusters
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
        Analyzing engagement patterns across {totalUsers} patients to identify behavioral groups
      </Typography>

      <Grid container spacing={3}>
        {/* Overview Cards */}
        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: '#4caf50', mr: 2 }}>
                  <Star />
                </Avatar>
                <Typography variant="h6">High Engagement</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {highEngagement.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Champions ({((highEngagement.length / totalUsers) * 100).toFixed(1)}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: '#ff9800', mr: 2 }}>
                  <CheckCircle />
                </Avatar>
                <Typography variant="h6">Medium Engagement</Typography>
              </Box>
              <Typography variant="h4" color="warning.main">
                {mediumEngagement.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Steady Users ({((mediumEngagement.length / totalUsers) * 100).toFixed(1)}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: '#f44336', mr: 2 }}>
                  <Warning />
                </Avatar>
                <Typography variant="h6">Low Engagement</Typography>
              </Box>
              <Typography variant="h4" color="error.main">
                {lowEngagement.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                At-Risk ({((lowEngagement.length / totalUsers) * 100).toFixed(1)}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Cluster Distribution Pie Chart */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Engagement Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`${value} users`, 'Count']} />
              </PieChart>
            </ResponsiveContainer>
            <Box sx={{ mt: 2 }}>
              {pieData.map((entry, index) => (
                <Box key={index} display="flex" alignItems="center" sx={{ mb: 1 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      backgroundColor: entry.color,
                      borderRadius: '50%',
                      mr: 1,
                    }}
                  />
                  <Typography variant="body2">
                    {entry.name}: {entry.description}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Cluster Comparison */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Cluster Activity Comparison
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="cluster" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Bar yAxisId="left" dataKey="avgLogs" fill="#667eea" name="Avg Logs" />
                <Bar yAxisId="right" dataKey="recentActivity" fill="#764ba2" name="Recent Activity %" />
              </BarChart>
            </ResponsiveContainer>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Blue: Average consumption logs | Purple: Recent activity percentage
            </Typography>
          </Paper>
        </Grid>

        {/* Detailed Cluster Analysis */}
        {[
          { name: 'High', data: highEngagement, analysis: highEngagementAnalysis, color: '#4caf50' },
          { name: 'Medium', data: mediumEngagement, analysis: mediumEngagementAnalysis, color: '#ff9800' },
          { name: 'Low', data: lowEngagement, analysis: lowEngagementAnalysis, color: '#f44336' }
        ].map((cluster) => {
          const insights = getClusterInsights(cluster.name, cluster.analysis);
          
          return (
            <Grid item xs={12} md={4} key={cluster.name}>
              <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
                <Box display="flex" alignItems="center" mb={2}>
                  {getClusterIcon(cluster.name)}
                  <Typography variant="h6" sx={{ ml: 1, color: cluster.color }}>
                    {insights.title}
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {insights.description}
                </Typography>

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom>
                  Key Statistics:
                </Typography>
                <List dense>
                  {cluster.analysis.patterns.map((pattern: string, index: number) => (
                    <ListItem key={index} sx={{ py: 0.5 }}>
                      <ListItemText 
                        primary={pattern}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom>
                  Behavioral Insights:
                </Typography>
                <List dense>
                  {insights.insights.map((insight: string, index: number) => (
                    <ListItem key={index} sx={{ py: 0.5 }}>
                      <ListItemText 
                        primary={insight}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>

                <Box sx={{ mt: 2, p: 1, backgroundColor: 'rgba(0,0,0,0.05)', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="primary">
                    Recommended Action:
                  </Typography>
                  <Typography variant="body2">
                    {insights.action}
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          );
        })}

        {/* Medical Conditions Analysis */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Medical Conditions by Engagement Cluster
            </Typography>
            <Grid container spacing={2}>
              {[
                { name: 'High Engagement', data: highEngagement, analysis: highEngagementAnalysis, color: '#4caf50' },
                { name: 'Medium Engagement', data: mediumEngagement, analysis: mediumEngagementAnalysis, color: '#ff9800' },
                { name: 'Low Engagement', data: lowEngagement, analysis: lowEngagementAnalysis, color: '#f44336' }
              ].map((cluster) => (
                <Grid item xs={12} md={4} key={cluster.name}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom sx={{ color: cluster.color }}>
                        {cluster.name} ({cluster.data.length} users)
                      </Typography>
                                             {cluster.analysis.avgProfile?.topConditions?.length && cluster.analysis.avgProfile.topConditions.length > 0 ? (
                         <List dense>
                           {cluster.analysis.avgProfile.topConditions.map((condition: any, index: number) => (
                            <ListItem key={index} sx={{ py: 0.5 }}>
                              <ListItemText 
                                primary={
                                  <Box display="flex" justifyContent="space-between" alignItems="center">
                                    <Typography variant="body2">
                                      {condition.condition}
                                    </Typography>
                                    <Chip 
                                      label={condition.count} 
                                      size="small" 
                                      sx={{ backgroundColor: cluster.color, color: 'white' }}
                                    />
                                  </Box>
                                }
                              />
                            </ListItem>
                          ))}
                        </List>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No medical conditions data available
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Data Source Info */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ backgroundColor: 'rgba(102, 126, 234, 0.1)' }}>
            <Typography variant="body2">
              <strong>Real Data Source:</strong> Behavior clustering is based on actual patient engagement data 
              from the production database. Clusters are determined by consumption log frequency: 
                             High (10+ logs), Medium (5-10 logs), Low (&lt;5 logs). 
              Analysis includes {totalUsers} active patients with their real interaction patterns.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BehaviorClusters; 