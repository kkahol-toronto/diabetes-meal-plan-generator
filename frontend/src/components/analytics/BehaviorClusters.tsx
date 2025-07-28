import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Chip, Avatar, List, ListItem, ListItemText,
  ListItemAvatar, CircularProgress, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Button, FormControl,
  InputLabel, Select, MenuItem, Dialog, DialogTitle, DialogContent,
  DialogActions, ListItemIcon
} from '@mui/material';
import {
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Group as GroupIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Timeline as TimelineIcon,
  Restaurant as RestaurantIcon,
  Assessment as AssessmentIcon,
  Insights as InsightsIcon
} from '@mui/icons-material';
import { Radar, Doughnut, Bar, Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
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
  RadialLinearScale,
  Title,
  ChartTooltip,
  Legend
);

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

// Individual Patient Behavior Analysis Component
const IndividualBehaviorAnalysis: React.FC<{selectedPatient: string}> = ({ selectedPatient }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (selectedPatient) {
      fetchBehaviorProfile();
    }
  }, [selectedPatient]);

  const fetchBehaviorProfile = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${config.API_URL}/admin/analytics/patient/${selectedPatient}/behavior-profile`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch behavior profile');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch behavior profile:', error);
      setLoading(false);
    }
  };

  const createBehaviorRadarChart = () => {
    if (!data || !data.behavioral_features) return null;
    
    const features = data.behavioral_features;
    
    return {
      labels: [
        'Meal Regularity',
        'Protein Preference', 
        'Weekend Consistency',
        'Diabetes Compliance',
        'Engagement Score',
        'Logging Consistency'
      ],
      datasets: [{
        label: 'Behavior Profile',
        data: [
          features.eating_patterns?.meal_regularity || 0,
          features.nutritional_preferences?.protein_preference || 0,
          features.temporal_behaviors?.weekend_consistency || 0,
          features.compliance_patterns?.diabetes_compliance || 0,
          features.engagement_behaviors?.engagement_score || 0,
          features.engagement_behaviors?.logging_consistency || 0
        ],
        backgroundColor: 'rgba(102, 126, 234, 0.2)',
        borderColor: '#667eea',
        borderWidth: 2,
        pointBackgroundColor: '#667eea',
      }]
    };
  };

  const createNutritionalPreferencesChart = () => {
    if (!data?.behavioral_features?.nutritional_preferences) return null;
    
    const prefs = data.behavioral_features.nutritional_preferences;
    
    return {
      labels: ['Protein', 'Carbohydrates', 'Fat'],
      datasets: [{
        data: [
          prefs.protein_preference || 0,
          prefs.carb_preference || 0,
          prefs.fat_preference || 0
        ],
        backgroundColor: ['#4ECDC4', '#45B7D1', '#FFA07A'],
        borderWidth: 2,
        borderColor: '#fff'
      }]
    };
  };

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'positive': return 'success';
      case 'concern': return 'error';
      case 'watch': return 'warning';
      default: return 'info';
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'positive': return '✅';
      case 'concern': return '⚠️';
      case 'watch': return '👀';
      default: return 'ℹ️';
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
        Failed to load behavior profile.
      </Alert>
    );
  }

  if (data.error) {
    return (
      <Alert severity="info">
        {data.error}
      </Alert>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Overall Behavior Scores */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Behavior Profile - {data.patient_name}
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="primary">
                  {data.overall_scores?.engagement?.toFixed(0) || 0}
                </Typography>
                <Typography variant="body2">Engagement Score</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="success.main">
                  {data.overall_scores?.compliance?.toFixed(0) || 0}
                </Typography>
                <Typography variant="body2">Compliance Score</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="info.main">
                  {data.overall_scores?.consistency?.toFixed(0) || 0}
                </Typography>
                <Typography variant="body2">Consistency Score</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="warning.main">
                  {data.analysis_period_days}
                </Typography>
                <Typography variant="body2">Days Analyzed</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Behavior Radar Chart */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Comprehensive Behavior Profile</Typography>
            <Box sx={{ height: 400 }}>
              {createBehaviorRadarChart() ? (
                <Radar data={createBehaviorRadarChart()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    r: {
                      beginAtZero: true,
                      max: 100,
                      grid: { color: 'rgba(0,0,0,0.1)' }
                    }
                  }
                }} />
              ) : (
                <Typography variant="body2" color="text.secondary">No radar chart data available</Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Nutritional Preferences */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Macro Preferences</Typography>
            <Box sx={{ height: 400 }}>
              {createNutritionalPreferencesChart() ? (
                <Doughnut data={createNutritionalPreferencesChart()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    }
                  }
                }} />
              ) : (
                <Typography variant="body2" color="text.secondary">No nutritional data available</Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Behavioral Insights */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Behavioral Insights</Typography>
            {data.insights && data.insights.length > 0 ? (
              data.insights.map((insight: any, index: number) => (
                <Alert 
                  key={index}
                  severity={getInsightColor(insight.type)}
                  sx={{ mb: 1 }}
                  icon={<span>{getInsightIcon(insight.type)}</span>}
                >
                  {insight.message}
                </Alert>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No specific behavioral patterns identified
              </Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Detailed Metrics Grid */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Complete Behavior Metrics</Typography>
            <Grid container spacing={2}>
              {/* Engagement Behaviors */}
              <Grid item xs={12} md={6} lg={3}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Engagement Behaviors
                </Typography>
                {data.behavioral_features?.engagement_behaviors && Object.entries(data.behavioral_features.engagement_behaviors).map(([key, value]: [string, any]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {key.replace(/_/g, ' ')}
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={typeof value === 'number' ? Math.min(value, 100) : 0}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                    <Typography variant="caption">
                      {typeof value === 'number' ? value.toFixed(1) : value}
                    </Typography>
                  </Box>
                ))}
              </Grid>

              {/* Compliance Patterns */}
              <Grid item xs={12} md={6} lg={3}>
                <Typography variant="subtitle2" color="success.main" gutterBottom>
                  Compliance Patterns
                </Typography>
                {data.behavioral_features?.compliance_patterns && Object.entries(data.behavioral_features.compliance_patterns).map(([key, value]: [string, any]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {key.replace(/_/g, ' ')}
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={typeof value === 'number' ? value : 0}
                      sx={{ height: 6, borderRadius: 3 }}
                      color="success"
                    />
                    <Typography variant="caption">
                      {typeof value === 'number' ? value.toFixed(1) : value}%
                    </Typography>
                  </Box>
                ))}
              </Grid>

              {/* Nutritional Preferences Details */}
              <Grid item xs={12} md={6} lg={3}>
                <Typography variant="subtitle2" color="info.main" gutterBottom>
                  Nutritional Details
                </Typography>
                {data.behavioral_features?.nutritional_preferences && Object.entries(data.behavioral_features.nutritional_preferences).map(([key, value]: [string, any]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {key.replace(/_/g, ' ')}
                    </Typography>
                    <Typography variant="body1">
                      {typeof value === 'number' ? value.toFixed(1) : value}
                      {key.includes('preference') ? '%' : key.includes('intake') ? 'g' : ''}
                    </Typography>
                  </Box>
                ))}
              </Grid>

              {/* Eating Patterns Details */}
              <Grid item xs={12} md={6} lg={3}>
                <Typography variant="subtitle2" color="warning.main" gutterBottom>
                  Eating Patterns
                </Typography>
                {data.behavioral_features?.eating_patterns && Object.entries(data.behavioral_features.eating_patterns).map(([key, value]: [string, any]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {key.replace(/_/g, ' ')}
                    </Typography>
                    <Typography variant="body1">
                      {typeof value === 'number' ? value.toFixed(1) : value}
                      {key.includes('per_day') ? ' meals' : key.includes('window') ? ' hours' : ''}
                    </Typography>
                  </Box>
                ))}
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

// Cohort Behavior Clustering Component
const CohortBehaviorClusters: React.FC<{groupingCriteria: string}> = ({ groupingCriteria }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
  const [nClusters, setNClusters] = useState(6);

  useEffect(() => {
    fetchClusterAnalysis();
  }, [nClusters]);

  const fetchClusterAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${config.API_URL}/admin/analytics/cohort/behavior-clusters?n_clusters=${nClusters}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch cluster analysis');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch cluster analysis:', error);
      setLoading(false);
    }
  };

  const createClusterScatterPlot = () => {
    if (!data?.pca_visualization_data) return null;
    
    const patients = data.pca_visualization_data.patients;
    const clusters: Record<number, any> = {};
    
    // Group patients by cluster
    patients.forEach((patient: any) => {
      const clusterId = patient.cluster;
      if (!clusters[clusterId]) {
        clusters[clusterId] = {
          label: data.clusters[clusterId]?.cluster_name || `Cluster ${clusterId}`,
          data: [],
          backgroundColor: getClusterColor(clusterId),
          borderColor: getClusterColor(clusterId, 0.8),
          pointRadius: 5,
          pointHoverRadius: 7,
        };
      }
      clusters[clusterId].data.push({
        x: patient.pca_x,
        y: patient.pca_y
      });
    });
    
    return {
      datasets: Object.values(clusters)
    } as any;
  };

  const getClusterColor = (clusterId: number, alpha: number = 0.6) => {
    const colors = [
      `rgba(102, 126, 234, ${alpha})`,
      `rgba(244, 67, 54, ${alpha})`,
      `rgba(76, 175, 80, ${alpha})`,
      `rgba(255, 152, 0, ${alpha})`,
      `rgba(156, 39, 176, ${alpha})`,
      `rgba(0, 188, 212, ${alpha})`,
      `rgba(255, 193, 7, ${alpha})`,
      `rgba(121, 85, 72, ${alpha})`
    ];
    return colors[clusterId % colors.length];
  };

  const createClusterSizeChart = () => {
    if (!data?.clusters) return null;
    
    const clusterData = Object.entries(data.clusters).map(([id, cluster]: [string, any]) => ({
      id: parseInt(id),
      name: cluster.cluster_name,
      size: cluster.patient_count,
      engagement: cluster.avg_engagement,
      compliance: cluster.avg_compliance
    }));
    
    return {
      labels: clusterData.map(c => c.name),
      datasets: [
        {
          label: 'Patient Count',
          data: clusterData.map(c => c.size),
          backgroundColor: clusterData.map((c, i) => getClusterColor(i)),
          borderWidth: 1
        }
      ]
    };
  };

  const createClusterComparisonChart = () => {
    if (!data?.clusters) return null;
    
    const clusterIds = Object.keys(data.clusters);
    const engagementData = clusterIds.map(id => data.clusters[id].avg_engagement);
    const complianceData = clusterIds.map(id => data.clusters[id].avg_compliance);
    
    return {
      labels: clusterIds.map(id => data.clusters[id].cluster_name),
      datasets: [
        {
          label: 'Avg Engagement Score',
          data: engagementData,
          backgroundColor: 'rgba(102, 126, 234, 0.6)',
          borderColor: '#667eea',
          borderWidth: 2
        },
        {
          label: 'Avg Compliance Score',
          data: complianceData,
          backgroundColor: 'rgba(76, 175, 80, 0.6)',
          borderColor: '#4caf50',
          borderWidth: 2
        }
      ]
    };
  };

  // Helper function to generate intervention recommendations
  const generateClusterRecommendations = (cluster: any) => {
    const recommendations = [];
    
    if (cluster.avg_engagement < 40) {
      recommendations.push({
        priority: 'error',
        intervention: 'Engagement Boost',
        description: 'Implement gamification and personalized reminders to increase logging frequency'
      });
    }
    
    if (cluster.avg_compliance < 50) {
      recommendations.push({
        priority: 'warning',
        intervention: 'Compliance Training',
        description: 'Provide diabetes-specific nutrition education and meal planning support'
      });
    }
    
    if (cluster.description && cluster.description.includes('night eating')) {
      recommendations.push({
        priority: 'info',
        intervention: 'Circadian Rhythm',
        description: 'Implement meal timing strategies and evening activity alternatives'
      });
    }
    
    if (cluster.description && cluster.description.includes('weekend')) {
      recommendations.push({
        priority: 'warning',
        intervention: 'Weekend Support',
        description: 'Develop weekend-specific meal plans and check-in protocols'
      });
    }
    
    if (cluster.avg_engagement > 70 && cluster.avg_compliance > 70) {
      recommendations.push({
        priority: 'success',
        intervention: 'Peer Mentoring',
        description: 'Leverage this high-performing group as mentors for other clusters'
      });
    }
    
    return recommendations;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (data?.error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Clustering Analysis Error</Typography>
        <Typography variant="body2">{data.error}</Typography>
        {data.minimum_required && (
          <Typography variant="body2">
            Minimum {data.minimum_required} patients required for clustering analysis.
          </Typography>
        )}
        {data.patients_with_data !== undefined && (
          <Typography variant="body2">
            Currently {data.patients_with_data} patients have sufficient data for analysis.
          </Typography>
        )}
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="error">
        Failed to load cluster analysis.
      </Alert>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Clustering Overview */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Behavior Clustering Analysis
            </Typography>
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="primary">
                  {data.total_patients_analyzed}
                </Typography>
                <Typography variant="body2">Patients Analyzed</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h3" color="info.main">
                  {data.n_clusters}
                </Typography>
                <Typography variant="body2">Behavioral Clusters</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel>Number of Clusters</InputLabel>
                  <Select 
                    value={nClusters} 
                    onChange={(e) => setNClusters(Number(e.target.value))}
                  >
                    {[2, 3, 4, 5, 6, 7, 8].map(n => (
                      <MenuItem key={n} value={n}>{n} Clusters</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button 
                  variant="outlined" 
                  onClick={fetchClusterAnalysis}
                  sx={{ ml: 2, height: 56 }}
                >
                  Reanalyze
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Cluster Visualization */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Behavior Cluster Visualization (PCA)
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Explained variance: {data.pca_visualization_data?.explained_variance_ratio?.[0]?.toFixed(1)}% (PC1) + {data.pca_visualization_data?.explained_variance_ratio?.[1]?.toFixed(1)}% (PC2)
            </Typography>
            <Box sx={{ height: 500 }}>
              {createClusterScatterPlot() ? (
                <Scatter 
                  data={createClusterScatterPlot()!} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { position: 'bottom' },
                      tooltip: {
                        callbacks: {
                          label: function(context: any) {
                            return context.dataset.label || 'Patient';
                          }
                        }
                      }
                    },
                    scales: {
                      x: { title: { display: true, text: 'Principal Component 1' } },
                      y: { title: { display: true, text: 'Principal Component 2' } }
                    }
                  }}
                />
              ) : (
                <Typography variant="body2" color="text.secondary">No cluster visualization data available</Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Cluster Size Distribution */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Cluster Sizes</Typography>
            <Box sx={{ height: 500 }}>
              {createClusterSizeChart() ? (
                <Doughnut data={createClusterSizeChart()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    }
                  }
                }} />
              ) : (
                <Typography variant="body2" color="text.secondary">No cluster size data available</Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Cluster Comparison */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Cluster Performance Comparison</Typography>
            <Box sx={{ height: 400 }}>
              {createClusterComparisonChart() ? (
                <Bar data={createClusterComparisonChart()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: { y: { beginAtZero: true, max: 100 } }
                }} />
              ) : (
                <Typography variant="body2" color="text.secondary">No cluster comparison data available</Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Detailed Cluster Analysis */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Cluster Characteristics</Typography>
            <Grid container spacing={2}>
              {Object.entries(data.clusters || {}).map(([clusterId, cluster]: [string, any]) => (
                <Grid item xs={12} md={6} lg={4} key={clusterId}>
                  <Card 
                    variant="outlined"
                    sx={{ 
                      cursor: 'pointer',
                      border: selectedCluster === parseInt(clusterId) ? 2 : 1,
                      borderColor: selectedCluster === parseInt(clusterId) ? 'primary.main' : 'divider',
                      '&:hover': { 
                        boxShadow: 2,
                        borderColor: 'primary.main'
                      }
                    }}
                    onClick={() => setSelectedCluster(parseInt(clusterId))}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                        <Box 
                          sx={{ 
                            width: 20, 
                            height: 20, 
                            borderRadius: '50%', 
                            backgroundColor: getClusterColor(parseInt(clusterId))
                          }} 
                        />
                        <Typography variant="h6" color="primary">
                          {cluster.cluster_name}
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" gutterBottom>
                        <strong>Patients:</strong> {cluster.patient_count}
                      </Typography>
                      
                      <Typography variant="body2" gutterBottom>
                        <strong>Avg Engagement:</strong> {cluster.avg_engagement.toFixed(1)}%
                      </Typography>
                      
                      <Typography variant="body2" gutterBottom>
                        <strong>Avg Compliance:</strong> {cluster.avg_compliance.toFixed(1)}%
                      </Typography>
                      
                      <Typography variant="body2" sx={{ fontStyle: 'italic', mt: 1 }}>
                        {cluster.description}
                      </Typography>
                      
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Top Characteristics:
                        </Typography>
                        {cluster.top_characteristics?.slice(0, 3).map(([feature, value]: [string, number], index: number) => (
                          <Chip 
                            key={index}
                            label={`${feature.replace(/.*_/, '')}: ${value.toFixed(1)}`}
                            size="small"
                            sx={{ mr: 0.5, mb: 0.5 }}
                            color={index === 0 ? 'primary' : 'default'}
                          />
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Cluster Intervention Recommendations */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Intervention Recommendations by Cluster
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(data.clusters || {}).map(([clusterId, cluster]: [string, any]) => {
                const recommendations = generateClusterRecommendations(cluster);
                return (
                  <Grid item xs={12} md={6} lg={4} key={clusterId}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" color="primary" gutterBottom>
                          {cluster.cluster_name}
                        </Typography>
                        
                        {recommendations.map((rec: any, index: number) => (
                          <Alert 
                            key={index}
                            severity={rec.priority}
                            sx={{ mb: 1, fontSize: '0.875rem' }}
                          >
                            <Typography variant="body2">
                              <strong>{rec.intervention}:</strong> {rec.description}
                            </Typography>
                          </Alert>
                        ))}
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

// Main BehaviorClusters Component
const BehaviorClusters: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Advanced behavior analysis for patient ${selectedPatient}`
        : 'Please select a patient to view individual behavior analysis';
    }
    return `Behavior clustering analysis grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Behavior Clustering & Analysis
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {viewMode === 'individual' ? (
        selectedPatient ? (
          <IndividualBehaviorAnalysis selectedPatient={selectedPatient} />
        ) : (
          <Alert severity="warning">
            Please select a patient from the dropdown above to view individual behavior analysis.
          </Alert>
        )
      ) : (
        <CohortBehaviorClusters groupingCriteria={groupingCriteria || 'diabetes_type'} />
      )}
    </Box>
  );
};

export default BehaviorClusters; 