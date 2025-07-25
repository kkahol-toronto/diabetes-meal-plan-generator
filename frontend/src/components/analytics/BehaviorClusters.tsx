import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Chip, Avatar, List, ListItem, ListItemText,
  ListItemAvatar, CircularProgress, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper
} from '@mui/material';
import {
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Group as GroupIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import config from '../../config/environment';

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
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBehaviorData();
  }, [viewMode, selectedPatient, groupingCriteria]);

  const fetchBehaviorData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        view_mode: viewMode,
        group_by: groupingCriteria || 'diabetes_type'
      });

      if (viewMode === 'individual' && selectedPatient) {
        params.append('patient_id', selectedPatient);
      }

      const response = await fetch(`${config.API_URL}/admin/analytics/behavior-clusters?${params}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch behavior data');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch behavior data:', error);
      setLoading(false);
    }
  };

  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Behavioral cluster analysis for patient ${selectedPatient}`
        : 'Please select a patient to view individual behavioral patterns';
    }
    return `Cohort behavioral clustering grouped by ${groupingCriteria?.replace('_', ' ')}`;
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
        Failed to load behavior cluster data.
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
        🔍 Behavior Clusters
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {viewMode === 'individual' ? (
        // Individual Patient Behavior Analysis
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  👤 Primary Behavior Cluster
                </Typography>
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Avatar sx={{ width: 80, height: 80, mx: 'auto', mb: 2, bgcolor: 'primary.main' }}>
                    <PersonIcon fontSize="large" />
                  </Avatar>
                  <Typography variant="h5" color="primary" fontWeight="bold">
                    {data.primary_cluster}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
                    {data.cluster_description}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📊 Behavioral Traits
                </Typography>
                <List>
                  {data.behavioral_traits?.map((trait: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'secondary.main' }}>
                          <TrendingUpIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText primary={trait} />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🎯 Personalized Recommendations
                </Typography>
                <Grid container spacing={2}>
                  {data.recommendations?.map((rec: string, index: number) => (
                    <Grid item xs={12} md={4} key={index}>
                      <Alert severity="info">
                        {rec}
                      </Alert>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : (
        // Cohort Behavior Clustering
        <Grid container spacing={3}>
          {/* Behavior Clusters */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  👥 Identified Behavior Clusters
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Based on {data.total_registered} registered patients out of {data.total_patients} total
                </Typography>
                
                <Grid container spacing={3}>
                  {data.clusters?.map((cluster: any) => (
                    <Grid item xs={12} md={6} lg={3} key={cluster.id}>
                      <Card 
                        variant="outlined" 
                        sx={{ 
                          height: '100%',
                          borderColor: cluster.color,
                          '&:hover': { boxShadow: 3 }
                        }}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Avatar sx={{ bgcolor: cluster.color, mr: 2 }}>
                              <GroupIcon />
                            </Avatar>
                            <Box>
                              <Typography variant="h6" fontWeight="bold">
                                {cluster.name}
                              </Typography>
                              <Chip 
                                label={`${cluster.size} patients`} 
                                size="small" 
                                sx={{ bgcolor: cluster.color, color: 'white' }}
                              />
                            </Box>
                          </Box>
                          
                          <Typography variant="body2" paragraph>
                            {cluster.description}
                          </Typography>
                          
                          <Typography variant="subtitle2" gutterBottom>
                            Key Characteristics:
                          </Typography>
                          <Box sx={{ mb: 2 }}>
                            {cluster.characteristics?.map((char: string, index: number) => (
                              <Chip 
                                key={index}
                                label={char} 
                                size="small" 
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                          </Box>
                          
                          <Alert severity="info" sx={{ mt: 2 }}>
                            <Typography variant="caption">
                              <strong>Outcomes:</strong> {cluster.outcomes}
                            </Typography>
                          </Alert>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Cluster Distribution */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📈 Cluster Distribution
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Patient distribution across behavior clusters
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  {data.clusters?.map((cluster: any) => {
                    const percentage = data.total_registered > 0 ? (cluster.size / data.total_registered) * 100 : 0;
                    return (
                      <Box key={cluster.id} sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">{cluster.name}</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {cluster.size} ({percentage.toFixed(1)}%)
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={percentage} 
                          sx={{ 
                            height: 8, 
                            borderRadius: 4,
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: cluster.color
                            }
                          }}
                        />
                      </Box>
                    );
                  })}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Pattern Insights */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🧠 Pattern Insights
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Key behavioral patterns and their health impact correlations
                </Typography>
                
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Pattern</strong></TableCell>
                        <TableCell><strong>Impact</strong></TableCell>
                        <TableCell><strong>Correlation</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.pattern_insights?.map((insight: any, index: number) => (
                        <TableRow key={index}>
                          <TableCell>{insight.pattern}</TableCell>
                          <TableCell>
                            <Chip 
                              label={insight.impact} 
                              size="small"
                              color={
                                insight.impact === 'High' ? 'error' : 
                                insight.impact === 'Medium' ? 'warning' : 
                                insight.impact === 'Critical' ? 'error' : 'info'
                              }
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {insight.correlation}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Summary Insights */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  💡 Key Insights & Recommendations
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Alert severity="success">
                      <Typography variant="body2">
                        <strong>High Performers:</strong> {data.clusters?.find((c: any) => c.id === 'tech-engaged')?.size || 0} patients show excellent digital engagement
                      </Typography>
                    </Alert>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Alert severity="warning">
                      <Typography variant="body2">
                        <strong>Need Support:</strong> {data.clusters?.find((c: any) => c.id === 'developing-habits')?.size || 0} patients require additional guidance
                      </Typography>
                    </Alert>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Alert severity="info">
                      <Typography variant="body2">
                        <strong>Opportunity:</strong> Morning active patterns show {((data.clusters?.find((c: any) => c.id === 'morning-active')?.size || 0) / Math.max(data.total_registered, 1) * 100).toFixed(0)}% better outcomes
                      </Typography>
                    </Alert>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default BehaviorClusters; 