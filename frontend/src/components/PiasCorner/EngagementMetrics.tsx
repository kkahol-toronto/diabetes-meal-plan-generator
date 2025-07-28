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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { TrendingUp, Message, Restaurant, Person } from '@mui/icons-material';
import config from '../../config/environment';

interface EngagementUser {
  user_id: string;
  name: string;
  registration_code: string;
  engagement_score: number;
  consumption_logs: number;
  chat_messages: number;
  meal_plans: number;
  last_activity: string;
  medical_conditions: string[];
  profile_completeness: number;
}

const EngagementMetrics: React.FC = () => {
  const [data, setData] = useState<EngagementUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEngagementData();
  }, []);

  const fetchEngagementData = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`${config.API_URL}/admin/analytics/patient-engagement`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch engagement data');
      }

      const engagementData = await response.json();
      setData(engagementData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load engagement data');
      console.error('Error fetching engagement data:', err);
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
        Error loading engagement metrics: {error}
        <Typography variant="body2" sx={{ mt: 1 }}>
          Using real patient engagement data from production database
        </Typography>
      </Alert>
    );
  }

  if (!data.length) {
    return (
      <Alert severity="info">
        No engagement data available yet. Data will appear as patients interact with the system.
      </Alert>
    );
  }

  // Calculate engagement statistics
  const totalUsers = data.length;
  const avgEngagementScore = data.reduce((sum, user) => sum + user.engagement_score, 0) / totalUsers;
  const totalConsumptionLogs = data.reduce((sum, user) => sum + user.consumption_logs, 0);
  const totalChatMessages = data.reduce((sum, user) => sum + user.chat_messages, 0);
  const totalMealPlans = data.reduce((sum, user) => sum + user.meal_plans, 0);

  // Engagement levels
  const highEngagement = data.filter(user => user.engagement_score > 30).length;
  const mediumEngagement = data.filter(user => user.engagement_score >= 10 && user.engagement_score <= 30).length;
  const lowEngagement = data.filter(user => user.engagement_score < 10).length;

  // Top performers
  const topPerformers = data.slice(0, 10);

  // Engagement distribution data for chart
  const engagementDistribution = [
    { range: 'Low (0-9)', count: lowEngagement, color: '#f5576c' },
    { range: 'Medium (10-30)', count: mediumEngagement, color: '#f093fb' },
    { range: 'High (31+)', count: highEngagement, color: '#667eea' }
  ];

  const getEngagementLevel = (score: number) => {
    if (score > 30) return { level: 'High', color: 'success' };
    if (score >= 10) return { level: 'Medium', color: 'warning' };
    return { level: 'Low', color: 'error' };
  };

  const getLastActivityStatus = (lastActivity: string | null) => {
    if (!lastActivity) return { status: 'Never', color: 'error' };
    
    const activityDate = new Date(lastActivity);
    const now = new Date();
    const daysDiff = Math.floor((now.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysDiff === 0) return { status: 'Today', color: 'success' };
    if (daysDiff <= 7) return { status: `${daysDiff}d ago`, color: 'success' };
    if (daysDiff <= 30) return { status: `${daysDiff}d ago`, color: 'warning' };
    return { status: `${daysDiff}d ago`, color: 'error' };
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
        Patient Engagement Metrics
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
        Real-time analysis of {totalUsers} registered patients and their platform interactions
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Statistics */}
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: 'primary.main', mr: 2 }}>
                  <Person />
                </Avatar>
                <Typography variant="h6">Total Users</Typography>
              </Box>
              <Typography variant="h4" color="primary.main">
                {totalUsers}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Registered patients
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: 'secondary.main', mr: 2 }}>
                  <Restaurant />
                </Avatar>
                <Typography variant="h6">Total Logs</Typography>
              </Box>
              <Typography variant="h4" color="secondary.main">
                {totalConsumptionLogs}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Consumption records
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: 'info.main', mr: 2 }}>
                  <Message />
                </Avatar>
                <Typography variant="h6">Chat Messages</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {totalChatMessages}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AI coach interactions
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: 'success.main', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Typography variant="h6">Avg Engagement</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {avgEngagementScore.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Engagement score
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Engagement Distribution */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Engagement Level Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={engagementDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip formatter={(value: number) => [`${value} users`, 'Count']} />
                <Bar dataKey="count" fill="#667eea" />
              </BarChart>
            </ResponsiveContainer>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Engagement Score = (Consumption Logs × 3) + (Chat Messages × 2) + (Meal Plans × 5)
            </Typography>
          </Paper>
        </Grid>

        {/* Activity Breakdown */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Activity Breakdown
            </Typography>
            <Box sx={{ height: 250, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  High Engagement ({highEngagement} users)
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <Box sx={{ 
                    height: 20, 
                    backgroundColor: '#667eea', 
                    width: `${(highEngagement / totalUsers) * 100}%`,
                    borderRadius: 1,
                    mr: 2
                  }} />
                  <Typography variant="body2">
                    {((highEngagement / totalUsers) * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Medium Engagement ({mediumEngagement} users)
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <Box sx={{ 
                    height: 20, 
                    backgroundColor: '#f093fb', 
                    width: `${(mediumEngagement / totalUsers) * 100}%`,
                    borderRadius: 1,
                    mr: 2
                  }} />
                  <Typography variant="body2">
                    {((mediumEngagement / totalUsers) * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  Low Engagement ({lowEngagement} users)
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <Box sx={{ 
                    height: 20, 
                    backgroundColor: '#f5576c', 
                    width: `${(lowEngagement / totalUsers) * 100}%`,
                    borderRadius: 1,
                    mr: 2
                  }} />
                  <Typography variant="body2">
                    {((lowEngagement / totalUsers) * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Top Performers Table */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top 10 Most Engaged Patients
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Patient</TableCell>
                    <TableCell>Engagement Score</TableCell>
                    <TableCell>Consumption Logs</TableCell>
                    <TableCell>Chat Messages</TableCell>
                    <TableCell>Meal Plans</TableCell>
                    <TableCell>Last Activity</TableCell>
                    <TableCell>Profile Complete</TableCell>
                    <TableCell>Conditions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topPerformers.map((user, index) => {
                    const engagement = getEngagementLevel(user.engagement_score);
                    const lastActivity = getLastActivityStatus(user.last_activity);
                    
                    return (
                      <TableRow key={user.user_id}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              {user.name || 'Unknown'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {user.registration_code || user.user_id}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            <Typography variant="body2" sx={{ mr: 1 }}>
                              {user.engagement_score}
                            </Typography>
                            <Chip 
                              label={engagement.level} 
                              size="small" 
                              color={engagement.color as any}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>{user.consumption_logs}</TableCell>
                        <TableCell>{user.chat_messages}</TableCell>
                        <TableCell>{user.meal_plans}</TableCell>
                        <TableCell>
                          <Chip 
                            label={lastActivity.status} 
                            size="small" 
                            color={lastActivity.color as any}
                          />
                        </TableCell>
                        <TableCell>{user.profile_completeness.toFixed(0)}%</TableCell>
                        <TableCell>
                          <Box>
                            {user.medical_conditions.slice(0, 2).map((condition, idx) => (
                              <Chip 
                                key={idx} 
                                label={condition} 
                                size="small" 
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                            {user.medical_conditions.length > 2 && (
                              <Typography variant="caption" color="text.secondary">
                                +{user.medical_conditions.length - 2} more
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Data Source Info */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ backgroundColor: 'rgba(102, 126, 234, 0.1)' }}>
            <Typography variant="body2">
              <strong>Real Data Source:</strong> This engagement analysis is based on actual patient interactions 
              including {totalConsumptionLogs} consumption logs, {totalChatMessages} chat messages, and {totalMealPlans} meal plans 
              from {totalUsers} registered patients in the production database.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EngagementMetrics; 