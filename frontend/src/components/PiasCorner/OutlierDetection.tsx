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
  Button,
} from '@mui/material';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Warning, TrendingUp, TrendingDown, Person, Restaurant } from '@mui/icons-material';
import config from '../../config/environment';

interface OutlierUser {
  user_id: string;
  avg_calories: number;
  total_logs: number;
  reason: string;
}

interface ComprehensiveAnalytics {
  outlier_detection: OutlierUser[];
  engagement_metrics: any[];
  summary: any;
}

const OutlierDetection: React.FC = () => {
  const [data, setData] = useState<ComprehensiveAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOutlierData();
  }, []);

  const fetchOutlierData = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`${config.API_URL}/admin/analytics/comprehensive`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch outlier data');
      }

      const analyticsData = await response.json();
      setData(analyticsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load outlier data');
      console.error('Error fetching outlier data:', err);
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
        Error loading outlier detection data: {error}
        <Typography variant="body2" sx={{ mt: 1 }}>
          Using real patient data from production database
        </Typography>
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        No outlier data available yet. Data will appear as patients log their meals.
      </Alert>
    );
  }

  const outliers = data.outlier_detection || [];
  const allUsers = data.engagement_metrics || [];

  // Calculate additional outlier metrics
  const highCalorieOutliers = outliers.filter(o => o.reason === 'High calorie intake');
  const lowCalorieOutliers = outliers.filter(o => o.reason === 'Low calorie intake');

  // Create scatter plot data for all users
  const scatterData = allUsers.map(user => ({
    userId: user.user_id,
    name: user.profile?.name || 'Unknown',
    logsCount: user.consumption_count,
    avgCalories: user.consumption_count > 0 ? (allUsers.find(u => u.user_id === user.user_id)?.total_calories || 0) / user.consumption_count : 0,
    isOutlier: outliers.some(o => o.user_id === user.user_id),
    outlierType: outliers.find(o => o.user_id === user.user_id)?.reason || null
  })).filter(user => user.logsCount > 0);

  // Distribution data for chart
  const distributionData = [
    {
      range: 'Very Low (<500 cal)',
      count: outliers.filter(o => o.avg_calories < 500).length,
      color: '#f44336'
    },
    {
      range: 'Low (500-1200 cal)',
      count: scatterData.filter(d => d.avgCalories >= 500 && d.avgCalories < 1200 && !d.isOutlier).length,
      color: '#ff9800'
    },
    {
      range: 'Normal (1200-2500 cal)',
      count: scatterData.filter(d => d.avgCalories >= 1200 && d.avgCalories <= 2500).length,
      color: '#4caf50'
    },
    {
      range: 'High (2500-3000 cal)',
      count: scatterData.filter(d => d.avgCalories > 2500 && d.avgCalories <= 3000 && !d.isOutlier).length,
      color: '#ff9800'
    },
    {
      range: 'Very High (>3000 cal)',
      count: outliers.filter(o => o.avg_calories > 3000).length,
      color: '#f44336'
    }
  ];

  const getOutlierSeverity = (avgCalories: number) => {
    if (avgCalories > 4000 || avgCalories < 300) return { level: 'Critical', color: 'error' };
    if (avgCalories > 3500 || avgCalories < 400) return { level: 'High', color: 'warning' };
    return { level: 'Moderate', color: 'info' };
  };

  const getRecommendation = (outlier: OutlierUser) => {
    if (outlier.reason === 'High calorie intake') {
      if (outlier.avg_calories > 4000) return 'Immediate intervention needed - consult nutritionist';
      if (outlier.avg_calories > 3500) return 'Review meal portions and food choices';
      return 'Monitor closely and provide portion guidance';
    } else {
      if (outlier.avg_calories < 300) return 'Critical - check for eating disorder or medical issue';
      if (outlier.avg_calories < 400) return 'Urgent - increase caloric intake safely';
      return 'Provide nutritional support to increase intake';
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
        Outlier Detection & Analysis
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
        Identifying {outliers.length} patients with unusual consumption patterns from {allUsers.length} active users
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Statistics */}
        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: 'error.main', mr: 2 }}>
                  <Warning />
                </Avatar>
                <Typography variant="h6">Total Outliers</Typography>
              </Box>
              <Typography variant="h4" color="error.main">
                {outliers.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Out of {allUsers.length} active users
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: 'warning.main', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Typography variant="h6">High Intake</Typography>
              </Box>
              <Typography variant="h4" color="warning.main">
                {highCalorieOutliers.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Above 3000 cal/day avg
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ backgroundColor: 'info.main', mr: 2 }}>
                  <TrendingDown />
                </Avatar>
                <Typography variant="h6">Low Intake</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {lowCalorieOutliers.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Below 500 cal/day avg
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Calorie Distribution */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Calorie Intake Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={distributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="range" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                />
                <YAxis />
                <Tooltip formatter={(value: number) => [`${value} users`, 'Count']} />
                <Bar dataKey="count" fill="#667eea" />
              </BarChart>
            </ResponsiveContainer>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Normal range: 1200-2500 calories per day average
            </Typography>
          </Paper>
        </Grid>

        {/* Scatter Plot */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              User Activity vs Average Calories
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="logsCount" 
                  name="Log Count"
                  label={{ value: 'Number of Logs', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  dataKey="avgCalories" 
                  name="Avg Calories"
                  label={{ value: 'Avg Calories/Day', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  formatter={(value: number, name: string) => [
                    name === 'avgCalories' ? `${value.toFixed(0)} cal` : value,
                    name === 'avgCalories' ? 'Avg Calories' : 'Log Count'
                  ]}
                  labelFormatter={(label, payload) => {
                    if (payload && payload[0]) {
                      const data = payload[0].payload;
                      return `${data.name} (${data.userId})`;
                    }
                    return '';
                  }}
                />
                <Scatter 
                  data={scatterData.filter(d => !d.isOutlier)} 
                  fill="#667eea" 
                  name="Normal Users"
                />
                <Scatter 
                  data={scatterData.filter(d => d.isOutlier)} 
                  fill="#f44336" 
                  name="Outliers"
                />
              </ScatterChart>
            </ResponsiveContainer>
            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
              <Box display="flex" alignItems="center">
                <Box sx={{ width: 12, height: 12, backgroundColor: '#667eea', borderRadius: '50%', mr: 1 }} />
                <Typography variant="body2">Normal Users</Typography>
              </Box>
              <Box display="flex" alignItems="center">
                <Box sx={{ width: 12, height: 12, backgroundColor: '#f44336', borderRadius: '50%', mr: 1 }} />
                <Typography variant="body2">Outliers</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Detailed Outlier Table */}
        {outliers.length > 0 && (
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Detailed Outlier Analysis
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Patient ID</TableCell>
                      <TableCell>Issue Type</TableCell>
                      <TableCell>Average Calories</TableCell>
                      <TableCell>Total Logs</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Recommendation</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {outliers.map((outlier, index) => {
                      const severity = getOutlierSeverity(outlier.avg_calories);
                      const recommendation = getRecommendation(outlier);
                      
                      return (
                        <TableRow key={outlier.user_id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {outlier.user_id.split('@')[0]}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {outlier.user_id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={outlier.reason}
                              size="small"
                              color={outlier.reason === 'High calorie intake' ? 'warning' : 'info'}
                              icon={outlier.reason === 'High calorie intake' ? <TrendingUp /> : <TrendingDown />}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold" 
                              color={outlier.avg_calories > 3000 ? 'error.main' : 'info.main'}>
                              {outlier.avg_calories.toFixed(0)} cal/day
                            </Typography>
                          </TableCell>
                          <TableCell>{outlier.total_logs}</TableCell>
                          <TableCell>
                            <Chip 
                              label={severity.level}
                              size="small"
                              color={severity.color as any}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ maxWidth: 200 }}>
                              {recommendation}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Button 
                              size="small" 
                              variant="outlined"
                              onClick={() => {
                                // Could navigate to patient profile or trigger intervention
                                console.log('Action for patient:', outlier.user_id);
                              }}
                            >
                              Review
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        )}

        {/* No Outliers Message */}
        {outliers.length === 0 && (
          <Grid item xs={12}>
            <Alert severity="success" sx={{ backgroundColor: 'rgba(76, 175, 80, 0.1)' }}>
              <Typography variant="body1">
                <strong>Great News!</strong> No outliers detected in current patient data.
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                All patients are maintaining calorie intake within normal ranges (500-3000 calories per day).
                This analysis is based on real consumption data from {allUsers.length} active patients.
              </Typography>
            </Alert>
          </Grid>
        )}

        {/* Data Source Info */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ backgroundColor: 'rgba(102, 126, 234, 0.1)' }}>
            <Typography variant="body2">
              <strong>Real Data Source:</strong> Outlier detection is performed on actual patient consumption data 
                             from the production database. Thresholds: High outliers (&gt;3000 cal/day), Low outliers (&lt;500 cal/day). 
              Analysis includes {allUsers.length} patients with consumption logs.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OutlierDetection; 