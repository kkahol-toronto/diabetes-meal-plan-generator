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
  LinearProgress,
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import config from '../../config/environment';

interface NutrientData {
  avg_calories: number;
  avg_protein: number;
  avg_carbs: number;
  avg_fat: number;
  total_logs: number;
}

const NutrientAdequacy: React.FC = () => {
  const [data, setData] = useState<NutrientData | null>(null);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNutrientData();
  }, []);

  const fetchNutrientData = async () => {
    try {
      setLoading(true);
      
      // Fetch comprehensive analytics
      const [analyticsResponse, trendsResponse] = await Promise.all([
        fetch(`${config.API_URL}/admin/analytics/comprehensive`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }),
        fetch(`${config.API_URL}/admin/analytics/nutrient-trends?days=14`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        })
      ]);

      if (!analyticsResponse.ok || !trendsResponse.ok) {
        throw new Error('Failed to fetch nutrient data');
      }

      const analyticsData = await analyticsResponse.json();
      const trendsData = await trendsResponse.json();

      setData(analyticsData.nutrient_adequacy);
      setTrendData(trendsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load nutrient data');
      console.error('Error fetching nutrient data:', err);
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
        Error loading nutrient adequacy data: {error}
        <Typography variant="body2" sx={{ mt: 1 }}>
          Using real patient data from production database
        </Typography>
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        No nutrient data available yet. Data will appear as patients log their meals.
      </Alert>
    );
  }

  // Calculate adequacy percentages (based on average daily requirements)
  const dailyTargets = {
    calories: 2000,
    protein: 50,  // grams
    carbs: 250,   // grams  
    fat: 65       // grams
  };

  const adequacyData = [
    {
      name: 'Calories',
      value: data.avg_calories,
      target: dailyTargets.calories,
      percentage: Math.min((data.avg_calories / dailyTargets.calories) * 100, 150),
      color: '#667eea'
    },
    {
      name: 'Protein',
      value: data.avg_protein,
      target: dailyTargets.protein,
      percentage: Math.min((data.avg_protein / dailyTargets.protein) * 100, 150),
      color: '#764ba2'
    },
    {
      name: 'Carbs',
      value: data.avg_carbs,
      target: dailyTargets.carbs,
      percentage: Math.min((data.avg_carbs / dailyTargets.carbs) * 100, 150),
      color: '#f093fb'
    },
    {
      name: 'Fat',
      value: data.avg_fat,
      target: dailyTargets.fat,
      percentage: Math.min((data.avg_fat / dailyTargets.fat) * 100, 150),
      color: '#f5576c'
    }
  ];

  const macroDistribution = [
    { name: 'Protein', value: data.avg_protein * 4, color: '#667eea' },
    { name: 'Carbs', value: data.avg_carbs * 4, color: '#764ba2' },
    { name: 'Fat', value: data.avg_fat * 9, color: '#f093fb' }
  ];

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
        Nutrient Adequacy Analysis
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
        Real-time nutrient analysis from {data.total_logs} consumption logs across all active patients
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={8}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Average Daily Nutrient Intake
            </Typography>
            
            <Grid container spacing={2}>
              {adequacyData.map((nutrient) => (
                <Grid item xs={12} sm={6} key={nutrient.name}>
                  <Card elevation={1}>
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary">
                        {nutrient.name}
                      </Typography>
                      <Typography variant="h6" sx={{ color: nutrient.color, fontWeight: 'bold' }}>
                        {nutrient.value.toFixed(1)}{nutrient.name === 'Calories' ? ' cal' : 'g'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Target: {nutrient.target}{nutrient.name === 'Calories' ? ' cal' : 'g'}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(nutrient.percentage, 100)}
                        sx={{
                          mt: 1,
                          height: 8,
                          borderRadius: 4,
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: nutrient.color,
                            borderRadius: 4,
                          },
                        }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {nutrient.percentage.toFixed(0)}% of target
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Macro Distribution */}
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Macronutrient Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={macroDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {macroDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`${value.toFixed(0)} cal`, 'Calories']} />
              </PieChart>
            </ResponsiveContainer>
            <Box sx={{ mt: 2 }}>
              {macroDistribution.map((entry, index) => (
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
                    {entry.name}: {entry.value.toFixed(0)} cal
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Nutrient Trends */}
        {trendData.length > 0 && (
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                14-Day Nutrient Trends
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={trendData.slice(-14)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    interval="preserveStartEnd"
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)}${name.includes('calories') ? ' cal' : 'g'}`,
                      name.replace('avg_', '').replace('_', ' ').toUpperCase()
                    ]}
                  />
                  <Bar dataKey="avg_calories" fill="#667eea" name="avg_calories" />
                  <Bar dataKey="avg_protein" fill="#764ba2" name="avg_protein" />
                  <Bar dataKey="avg_carbs" fill="#f093fb" name="avg_carbs" />
                  <Bar dataKey="avg_fat" fill="#f5576c" name="avg_fat" />
                </BarChart>
              </ResponsiveContainer>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Daily averages across all patient consumption logs
              </Typography>
            </Paper>
          </Grid>
        )}

        {/* Data Source Info */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ backgroundColor: 'rgba(102, 126, 234, 0.1)' }}>
            <Typography variant="body2">
              <strong>Real Data Source:</strong> This analysis is based on {data.total_logs} actual consumption records 
              logged by patients in the production database. All calculations use real patient meal data, 
              not simulated or demo values.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default NutrientAdequacy; 