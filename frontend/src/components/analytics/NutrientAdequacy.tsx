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

// Complete list of nutrients including micronutrients
const NUTRIENTS_LIST = [
  // Macronutrients and energy
  'calories', 'protein', 'carbohydrates', 'fiber', 'total_fat', 'saturated_fat',
  // Vitamins
  'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
  'thiamin_b1', 'riboflavin_b2', 'niacin_b3', 'vitamin_b6', 'vitamin_b12', 'folate',
  // Minerals
  'calcium', 'iron', 'magnesium', 'phosphorus', 'potassium', 'sodium', 'zinc'
];

const formatNutrientName = (nutrient: string): string => {
  return nutrient
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .replace(/B(\d+)/g, 'B$1'); // Keep B vitamin numbering
};

// Individual Patient Analysis Component
const IndividualNutrientAnalysis: React.FC<{selectedPatient: string}> = ({ selectedPatient }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNutrient, setSelectedNutrient] = useState<string>('all');

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

  const getAvailableNutrients = (): string[] => {
    if (!data || !data.compliance_percentages) return [];
    return Object.keys(data.compliance_percentages);
  };

  const createRadarChart = () => {
    if (!data || !data.compliance_percentages) return null;
    
    const availableNutrients = getAvailableNutrients();
    let nutrients, values;
    
    if (selectedNutrient === 'all') {
      nutrients = availableNutrients;
      values = availableNutrients.map(n => data.compliance_percentages[n]);
    } else if (availableNutrients.includes(selectedNutrient)) {
      nutrients = [selectedNutrient];
      values = [data.compliance_percentages[selectedNutrient]];
    } else {
      return null; // Selected nutrient not available
    }
    
    return {
      labels: nutrients.map(n => formatNutrientName(n)),
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

  const createBarChart = () => {
    if (!data || !data.compliance_percentages) return null;
    
    const availableNutrients = getAvailableNutrients();
    let nutrients, values;
    
    if (selectedNutrient === 'all') {
      nutrients = availableNutrients;
      values = availableNutrients.map(n => data.compliance_percentages[n]);
    } else if (availableNutrients.includes(selectedNutrient)) {
      nutrients = [selectedNutrient];
      values = [data.compliance_percentages[selectedNutrient]];
    } else {
      return null;
    }
    
    return {
      labels: nutrients.map(n => formatNutrientName(n)),
      datasets: [{
        label: 'RDA Compliance %',
        data: values,
        backgroundColor: nutrients.map((_, index) => 
          `hsla(${(index * 137.5) % 360}, 70%, 60%, 0.8)`
        ),
        borderColor: nutrients.map((_, index) => 
          `hsla(${(index * 137.5) % 360}, 70%, 50%, 1)`
        ),
        borderWidth: 1,
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
                  label={`${formatNutrientName(nutrient)}: ${value.toFixed(1)}`}
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

  const availableNutrients = getAvailableNutrients();
  const chartData = selectedNutrient === 'all' || availableNutrients.length <= 5 ? createRadarChart() : createBarChart();

  return (
    <Grid container spacing={3}>
      {/* Nutrient Filter Dropdown */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Filter by Nutrient</Typography>
            <FormControl fullWidth>
              <InputLabel>Select Nutrient</InputLabel>
              <Select
                value={selectedNutrient}
                onChange={(e) => setSelectedNutrient(e.target.value)}
                label="Select Nutrient"
              >
                <MenuItem value="all">All Nutrients</MenuItem>
                {availableNutrients.map(nutrient => (
                  <MenuItem key={nutrient} value={nutrient}>
                    {formatNutrientName(nutrient)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {selectedNutrient !== 'all' && availableNutrients.includes(selectedNutrient) && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="primary" fontWeight="bold">
                  {formatNutrientName(selectedNutrient)} Compliance
                </Typography>
                <Typography variant="h4" color="primary">
                  {data.compliance_percentages[selectedNutrient].toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={data.compliance_percentages[selectedNutrient]} 
                  sx={{ 
                    height: 8,
                    borderRadius: 4,
                    mt: 1,
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: data.compliance_percentages[selectedNutrient] >= 80 ? '#4caf50' :
                                     data.compliance_percentages[selectedNutrient] >= 60 ? '#ff9800' : '#f44336'
                    }
                  }}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

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

      {/* Nutrient Stats */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Quick Stats</Typography>
            <Typography variant="body2">
              Total Nutrients Tracked: {availableNutrients.length}
            </Typography>
            <Typography variant="body2">
              Above 80%: {availableNutrients.filter(n => data.compliance_percentages[n] >= 80).length}
            </Typography>
            <Typography variant="body2">
              60-80%: {availableNutrients.filter(n => data.compliance_percentages[n] >= 60 && data.compliance_percentages[n] < 80).length}
            </Typography>
            <Typography variant="body2">
              Below 60%: {availableNutrients.filter(n => data.compliance_percentages[n] < 60).length}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Chart Visualization */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {selectedNutrient === 'all' ? 'All Nutrients Compliance' : `${formatNutrientName(selectedNutrient)} Compliance`}
            </Typography>
            {chartData ? (
              <Box sx={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                {selectedNutrient === 'all' && availableNutrients.length <= 5 ? (
                  <Radar 
                    data={chartData} 
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
                ) : (
                  <Bar 
                    data={chartData} 
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
                          display: false
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              return `Compliance: ${context.parsed.y.toFixed(1)}%`;
                            }
                          }
                        }
                      }
                    }} 
                  />
                )}
              </Box>
            ) : (
              <Alert severity="info">
                {selectedNutrient === 'all' 
                  ? 'No consumption data available for chart visualization'
                  : `No data available for ${formatNutrientName(selectedNutrient)}`
                }
              </Alert>
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
                        {formatNutrientName(def.nutrient).toUpperCase()}
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
                          {formatNutrientName(rec.nutrient).toUpperCase()}
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
  const [selectedNutrients, setSelectedNutrients] = useState<string[]>(['calories', 'protein', 'carbohydrates', 'fiber']);

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

  const getAvailableNutrients = (): string[] => {
    if (!data || !data.groups) return [];
    
    const allNutrients = new Set<string>();
    Object.values(data.groups).forEach((group: any) => {
      if (group.rda_compliance_stats) {
        Object.keys(group.rda_compliance_stats).forEach(nutrient => {
          allNutrients.add(nutrient);
        });
      }
    });
    
    return Array.from(allNutrients);
  };

  const createComplianceChart = () => {
    if (!data) return null;
    
    const groups = Object.keys(data.groups);
    const availableNutrients = getAvailableNutrients();
    const nutrientsToShow = selectedNutrients.filter(n => availableNutrients.includes(n));
    
    const datasets = nutrientsToShow.map((nutrient, index) => ({
      label: formatNutrientName(nutrient),
      data: groups.map(group => {
        const stats = data.groups[group].rda_compliance_stats[nutrient];
        const value = stats ? stats.percentage_meeting_target : 0;
        return value;
      }),
      backgroundColor: `hsla(${(index * 137.5) % 360}, 70%, 60%, 0.8)`,
      borderWidth: 1,
      borderColor: `hsla(${(index * 137.5) % 360}, 70%, 50%, 1)`,
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

    const nutrients = Object.keys(allDeficiencies);
    return {
      labels: nutrients.map(n => formatNutrientName(n)),
      datasets: [{
        data: Object.values(allDeficiencies),
        backgroundColor: nutrients.map((_, index) => 
          `hsla(${(index * 137.5) % 360}, 70%, 60%, 0.8)`
        ),
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

  const availableNutrients = getAvailableNutrients();

  return (
    <Grid container spacing={3}>
      {/* Nutrient Selection Controls */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Select Nutrients to Display</Typography>
            <FormControl fullWidth>
              <InputLabel>Choose Nutrients for Chart</InputLabel>
              <Select
                multiple
                value={selectedNutrients}
                onChange={(e) => setSelectedNutrients(e.target.value as string[])}
                label="Choose Nutrients for Chart"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={formatNutrientName(value)} size="small" />
                    ))}
                  </Box>
                )}
              >
                {availableNutrients.map((nutrient) => (
                  <MenuItem key={nutrient} value={nutrient}>
                    {formatNutrientName(nutrient)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button 
                size="small" 
                variant="outlined"
                onClick={() => setSelectedNutrients(['calories', 'protein', 'carbohydrates', 'fiber'])}
              >
                Macros Only
              </Button>
              <Button 
                size="small" 
                variant="outlined"
                onClick={() => setSelectedNutrients(availableNutrients.filter(n => 
                  ['vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'vitamin_b6', 'vitamin_b12', 'folate'].includes(n)
                ))}
              >
                Vitamins Only
              </Button>
              <Button 
                size="small" 
                variant="outlined"
                onClick={() => setSelectedNutrients(availableNutrients.filter(n => 
                  ['calcium', 'iron', 'magnesium', 'phosphorus', 'potassium', 'sodium', 'zinc'].includes(n)
                ))}
              >
                Minerals Only
              </Button>
              <Button 
                size="small" 
                variant="outlined"
                onClick={() => setSelectedNutrients(availableNutrients)}
              >
                All Available
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>

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
            <Typography variant="body2" color="text.secondary">
              Available Nutrients: {availableNutrients.length} | Selected for Chart: {selectedNutrients.length}
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
              {selectedNutrients.length < availableNutrients.length && 
                ` - Showing ${selectedNutrients.length} Selected Nutrients`
              }
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
                          label={`${formatNutrientName(def.nutrient)}: ${def.patients_affected} affected`}
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