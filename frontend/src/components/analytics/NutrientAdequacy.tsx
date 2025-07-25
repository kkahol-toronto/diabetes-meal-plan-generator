import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Chip, CircularProgress, FormControl,
  InputLabel, Select, MenuItem, Button, Tooltip
} from '@mui/material';
import {
  Radar, Bar, Doughnut, Line
} from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  ArcElement,
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
  RadialLinearScale,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

// Individual Patient Analysis Component
const IndividualNutrientAnalysis: React.FC<{selectedPatient: string}> = ({ selectedPatient }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (selectedPatient) {
      fetchIndividualData();
    }
  }, [selectedPatient]);

  const fetchIndividualData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${config.API_URL}/admin/analytics/patient/${selectedPatient}/nutrient-adequacy`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch data');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch individual nutrient data:', error);
      setLoading(false);
    }
  };

  const createRadarChart = () => {
    if (!data || !data.compliance_percentages) return null;
    
    const nutrients = Object.keys(data.compliance_percentages);
    const values = Object.values(data.compliance_percentages) as number[];
    
    return {
      labels: nutrients.map(n => n.charAt(0).toUpperCase() + n.slice(1).replace('_', ' ')),
      datasets: [{
        label: 'RDA Compliance %',
        data: values,
        backgroundColor: 'rgba(102, 126, 234, 0.2)',
        borderColor: '#667eea',
        borderWidth: 2,
        pointBackgroundColor: '#667eea',
        pointRadius: 4,
      }]
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'adequate': return '#4caf50';
      case 'below_target': return '#ff9800';
      case 'deficient': return '#f44336';
      case 'within_limit': return '#4caf50';
      case 'elevated': return '#ff9800';
      case 'excessive': return '#f44336';
      default: return '#9e9e9e';
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
        Failed to load nutrient adequacy data for this patient.
      </Alert>
    );
  }

  if (data.registration_status === 'not_registered') {
    return (
      <Alert severity="info">
        This patient has not registered yet. Only RDA targets are available.
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2">RDA Targets for {data.patient_name}:</Typography>
          <Grid container spacing={1} sx={{ mt: 1 }}>
            {Object.entries(data.rda_targets).map(([nutrient, value]: [string, any]) => (
              <Grid item key={nutrient}>
                <Chip 
                  label={`${nutrient.replace('_', ' ')}: ${value.toFixed(1)}`}
                  size="small"
                  variant="outlined"
                />
              </Grid>
            ))}
          </Grid>
        </Box>
      </Alert>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Overall Compliance Score */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Overall Compliance</Typography>
            <Typography variant="h3" color="primary" sx={{ mb: 1 }}>
              {data.overall_compliance_score.toFixed(1)}%
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={data.overall_compliance_score} 
              sx={{ 
                height: 8,
                borderRadius: 4,
                '& .MuiLinearProgress-bar': {
                  backgroundColor: data.overall_compliance_score >= 80 ? '#4caf50' :
                                 data.overall_compliance_score >= 60 ? '#ff9800' : '#f44336'
                }
              }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Analysis period: {data.period_days} days
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Radar Chart */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Nutrient Compliance Radar</Typography>
            {data.compliance_percentages && Object.keys(data.compliance_percentages).length > 0 ? (
              <Box sx={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Radar 
                  data={createRadarChart()!} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { 
                      r: { 
                        beginAtZero: true, 
                        max: 100,
                        ticks: {
                          stepSize: 20
                        }
                      } 
                    },
                    plugins: {
                      legend: {
                        display: false
                      }
                    }
                  }} 
                />
              </Box>
            ) : (
              <Alert severity="info">No consumption data available for chart visualization</Alert>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Deficiencies & Issues */}
      {data.deficiencies && data.deficiencies.length > 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>⚠️ Identified Issues</Typography>
              <Grid container spacing={2}>
                {data.deficiencies.map((def: any, index: number) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Alert 
                      severity={def.severity === 'severe' ? 'error' : 'warning'} 
                      sx={{ height: '100%' }}
                    >
                      <Typography variant="body2" fontWeight="bold">
                        {def.nutrient.toUpperCase().replace('_', ' ')}
                      </Typography>
                      <Typography variant="body2">
                        Status: {def.status.replace('_', ' ')}
                      </Typography>
                      <Typography variant="body2">
                        Actual: {def.actual.toFixed(1)} | Target: {def.target.toFixed(1)}
                      </Typography>
                      {def.recommendation && (
                        <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                          💡 {def.recommendation}
                        </Typography>
                      )}
                    </Alert>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Personalized Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>🎯 Personalized Recommendations</Typography>
              <Grid container spacing={2}>
                {data.recommendations.map((rec: any, index: number) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Chip 
                            label={rec.priority} 
                            size="small"
                            color={rec.priority === 'high' ? 'error' : 'warning'}
                          />
                          <Chip 
                            label={rec.category} 
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          {rec.nutrient.toUpperCase().replace('_', ' ')}
                        </Typography>
                        <Typography variant="body2" paragraph>
                          {rec.recommendation}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {rec.rationale}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );
};

// Cohort Analysis Component
const CohortNutrientAnalysis: React.FC<{groupingCriteria: string}> = ({ groupingCriteria }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCohortData();
  }, [groupingCriteria]);

  const fetchCohortData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${config.API_URL}/admin/analytics/cohort/nutrient-adequacy?group_by=${groupingCriteria}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch data');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch cohort nutrient data:', error);
      setLoading(false);
    }
  };

  const createComplianceChart = () => {
    if (!data) return null;
    
    const groups = Object.keys(data.groups);
    const nutrients = ['calories', 'protein', 'carbohydrates', 'fiber'];
    

    
    const datasets = nutrients.map((nutrient, index) => ({
      label: nutrient.charAt(0).toUpperCase() + nutrient.slice(1),
      data: groups.map(group => {
        const stats = data.groups[group].rda_compliance_stats[nutrient];
        const value = stats ? stats.percentage_meeting_target : 0;

        return value;
      }),
      backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5af19'][index],
      borderWidth: 1,
      borderColor: ['#667eea', '#764ba2', '#f093fb', '#f5af19'][index],
    }));



    return {
      labels: groups,
      datasets
    };
  };

  const createDeficiencyChart = () => {
    if (!data) return null;
    
    // Aggregate top deficiencies across all groups
    const allDeficiencies: {[key: string]: number} = {};
    Object.values(data.groups).forEach((group: any) => {
      if (group.top_deficiencies && group.top_deficiencies.length > 0) {
        group.top_deficiencies.forEach((def: any) => {
          if (!allDeficiencies[def.nutrient]) {
            allDeficiencies[def.nutrient] = 0;
          }
          allDeficiencies[def.nutrient] += def.patients_affected;
        });
      }
    });



    // If no deficiencies, show a placeholder
    if (Object.keys(allDeficiencies).length === 0) {
      return {
        labels: ['No Data'],
        datasets: [{
          data: [1],
          backgroundColor: ['#e0e0e0'],
        }]
      };
    }

    return {
      labels: Object.keys(allDeficiencies).map(n => n.charAt(0).toUpperCase() + n.slice(1).replace('_', ' ')),
      datasets: [{
        data: Object.values(allDeficiencies),
        backgroundColor: ['#FF6B6B', '#FFA07A', '#FFD700', '#98D8C8', '#87CEEB'],
      }]
    };
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
        Failed to load cohort nutrient adequacy data.
      </Alert>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Population Overview */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Population Overview - Grouped by {groupingCriteria.replace('_', ' ')}
            </Typography>
            <Typography variant="body1">
              Total Patients: {data.total_patients} | Analysis Period: {data.period_days} days
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Groups: {Object.keys(data.groups).length} | 
              Registered Patients: {Object.values(data.groups).reduce((sum: number, group: any) => sum + group.registered_patients, 0)}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* RDA Compliance by Groups */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              % Patients Meeting RDA Targets (≥60%) by Group
            </Typography>
            {Object.keys(data.groups).length > 0 ? (
              <Box sx={{ height: 400 }}>
                <Bar 
                  data={createComplianceChart()!} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: { 
                        beginAtZero: true, 
                        max: 100,
                        ticks: {
                          stepSize: 10,
                          callback: function(value) {
                            return value + '%';
                          }
                        }
                      },
                      x: {
                        ticks: {
                          maxRotation: 45
                        }
                      }
                    },
                    plugins: {
                      legend: {
                        position: 'top'
                      },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                          }
                        }
                      }
                    }
                  }}
                />
              </Box>
            ) : (
              <Alert severity="info">
                No patient groups with consumption data available for analysis.
              </Alert>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Top Deficiencies Across Population */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Top Deficiencies</Typography>
            <Box sx={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Doughnut 
                data={createDeficiencyChart()!} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    },
                    tooltip: {
                      callbacks: {
                        label: function(context) {
                          const label = context.label || '';
                          const value = context.parsed;
                          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                          const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
                          return `${label}: ${value} patients (${percentage}%)`;
                        }
                      }
                    }
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Detailed Group Breakdown */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Detailed Group Analysis</Typography>
            <Grid container spacing={2}>
              {Object.entries(data.groups).map(([groupName, groupData]: [string, any]) => (
                <Grid item xs={12} md={6} lg={4} key={groupName}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">{groupName}</Typography>
                      <Typography variant="body2">Total Patients: {groupData.patient_count}</Typography>
                      <Typography variant="body2">Registered: {groupData.registered_patients}</Typography>
                      <Typography variant="body2">
                        Avg Compliance: {groupData.average_compliance_score ? groupData.average_compliance_score.toFixed(1) : '0'}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        With consumption data: {groupData.registered_patients}
                      </Typography>
                      
                      <Typography variant="subtitle2" sx={{ mt: 2 }}>Top Issues:</Typography>
                      {groupData.top_deficiencies.slice(0, 3).map((def: any, index: number) => (
                        <Chip 
                          key={index}
                          label={`${def.nutrient.replace('_', ' ')}: ${def.patients_affected} affected`}
                          size="small"
                          color="warning"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

// Main Component
const NutrientAdequacy: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Nutrient adequacy analysis for patient ${selectedPatient}`
        : 'Please select a patient to view individual nutrient analysis';
    }
    return `Cohort nutrient adequacy grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        🥗 Nutrient Adequacy Analysis
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {viewMode === 'individual' ? (
        selectedPatient ? (
          <IndividualNutrientAnalysis selectedPatient={selectedPatient} />
        ) : (
          <Alert severity="warning">
            Please select a patient from the dropdown above to view individual nutrient analysis.
          </Alert>
        )
      ) : (
        <CohortNutrientAnalysis groupingCriteria={groupingCriteria || 'diabetes_type'} />
      )}
    </Box>
  );
};

export default NutrientAdequacy; 