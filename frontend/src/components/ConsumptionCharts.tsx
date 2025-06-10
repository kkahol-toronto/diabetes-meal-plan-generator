import React, { useState } from 'react';
import {
  PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
  LineChart, Line, AreaChart, Area,
  ResponsiveContainer
} from 'recharts';
import { Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem, Grid } from '@mui/material';

// Professional color palette
const COLORS = {
  primary: '#2E7D32',      // Deep green for primary data
  secondary: '#1976D2',    // Blue for secondary data
  accent: '#FFA000',       // Amber for accents/target line
  pieColors: ['#2E7D32', '#1976D2', '#FFA000'],  // Consistent colors for pie chart
  background: '#F5F5F5',   // Light grey background
};

// Custom styles
const styles = {
  chartContainer: {
    backgroundColor: COLORS.background,
    borderRadius: 2,
    padding: 2,
  },
  title: {
    fontWeight: 600,
    color: '#263238',
    marginBottom: 2,
  },
  select: {
    '& .MuiOutlinedInput-root': {
      borderRadius: 2,
    },
  },
};

interface ConsumptionChartsProps {
  analytics: {
    total_macronutrients: {
      carbohydrates: number;
      protein: number;
      fat: number;
    };
    consumption_records: Array<{
      timestamp: string;
      nutritional_info: {
        calories: number;
        carbohydrates: number;
        protein: number;
        fat: number;
      };
    }>;
    period_days?: number;
  };
  targetCalories?: number;
}

type ChartType = 'bar' | 'line' | 'area';

// Custom tooltip styles
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <Paper
        elevation={3}
        sx={{
          p: 1.5,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          border: '1px solid rgba(0, 0, 0, 0.05)',
        }}
      >
        <Typography variant="subtitle2" sx={{ mb: 1 }}>{label}</Typography>
        {payload.map((entry: any, index: number) => (
          <Typography
            key={index}
            variant="body2"
            sx={{ color: entry.color, mb: 0.5 }}
          >
            {`${entry.name}: ${entry.value.toLocaleString()} cal`}
          </Typography>
        ))}
      </Paper>
    );
  }
  return null;
};

const ConsumptionCharts: React.FC<ConsumptionChartsProps> = ({ analytics, targetCalories = 2000 }) => {
  const [calorieChartType, setCalorieChartType] = useState<ChartType>('bar');
  
  // Prepare data for macronutrients pie chart
  const macroData = [
    { name: 'Carbohydrates', value: analytics.total_macronutrients.carbohydrates },
    { name: 'Protein', value: analytics.total_macronutrients.protein },
    { name: 'Fat', value: analytics.total_macronutrients.fat }
  ];

  // Function to format date based on period
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    if (!analytics.period_days || analytics.period_days <= 1) {
      // For single day, show time
      return date.toLocaleString('en-US', {
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
      });
    } else {
      // For multiple days, show date
      return date.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
    }
  };

  // Prepare data for calories chart based on period
  const caloriesData = analytics.consumption_records.reduce((acc: any[], record) => {
    const timeKey = formatDate(record.timestamp);
    const existingEntry = acc.find(item => item.time === timeKey);
    
    if (existingEntry) {
      existingEntry.calories += record.nutritional_info.calories;
      existingEntry.cumulative = (acc[acc.indexOf(existingEntry) - 1]?.cumulative || 0) + existingEntry.calories;
    } else {
      // Get cumulative calories up to this point
      const cumulative = (acc[acc.length - 1]?.cumulative || 0) + record.nutritional_info.calories;
      acc.push({
        time: timeKey,
        calories: record.nutritional_info.calories,
        cumulative: cumulative
      });
    }
    
    return acc;
  }, []).sort((a, b) => {
    // Sort by timestamp
    const dateA = new Date(a.time);
    const dateB = new Date(b.time);
    return dateA.getTime() - dateB.getTime();
  });

  // Render calorie chart based on selected type
  const renderCalorieChart = () => {
    const commonProps = {
      data: caloriesData,
      margin: { top: 20, right: 30, left: 20, bottom: 25 }
    };

    const commonAxisProps = {
      style: {
        fontSize: '0.75rem',
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      }
    };

    // Calculate appropriate angle for x-axis labels based on period
    const xAxisAngle = !analytics.period_days || analytics.period_days <= 1 ? -45 : 0;
    const xAxisHeight = !analytics.period_days || analytics.period_days <= 1 ? 60 : 30;

    switch (calorieChartType) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
            <XAxis
              dataKey="time"
              angle={xAxisAngle}
              textAnchor={xAxisAngle === 0 ? "middle" : "end"}
              height={xAxisHeight}
              tick={commonAxisProps}
            />
            <YAxis
              tick={commonAxisProps}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
                fontSize: '0.875rem',
              }}
            />
            <ReferenceLine
              y={targetCalories}
              label={{ value: 'Target', position: 'right', fill: COLORS.accent }}
              stroke={COLORS.accent}
              strokeDasharray="3 3"
            />
            <Line
              type="monotone"
              dataKey="calories"
              stroke={COLORS.primary}
              name="Calories per meal"
              dot={{ r: 4, fill: COLORS.primary }}
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="cumulative"
              stroke={COLORS.secondary}
              name="Cumulative calories"
              dot={{ r: 4, fill: COLORS.secondary }}
              strokeWidth={2}
            />
          </LineChart>
        );
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
            <XAxis
              dataKey="time"
              angle={xAxisAngle}
              textAnchor={xAxisAngle === 0 ? "middle" : "end"}
              height={xAxisHeight}
              tick={commonAxisProps}
            />
            <YAxis
              tick={commonAxisProps}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
                fontSize: '0.875rem',
              }}
            />
            <ReferenceLine
              y={targetCalories}
              label={{ value: 'Target', position: 'right', fill: COLORS.accent }}
              stroke={COLORS.accent}
              strokeDasharray="3 3"
            />
            <Area
              type="monotone"
              dataKey="calories"
              stackId="1"
              stroke={COLORS.primary}
              fill={COLORS.primary}
              fillOpacity={0.6}
              name="Calories per meal"
            />
            <Area
              type="monotone"
              dataKey="cumulative"
              stackId="2"
              stroke={COLORS.secondary}
              fill={COLORS.secondary}
              fillOpacity={0.3}
              name="Cumulative calories"
            />
          </AreaChart>
        );
      default:
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
            <XAxis
              dataKey="time"
              angle={xAxisAngle}
              textAnchor={xAxisAngle === 0 ? "middle" : "end"}
              height={xAxisHeight}
              tick={commonAxisProps}
            />
            <YAxis
              tick={commonAxisProps}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
                fontSize: '0.875rem',
              }}
            />
            <ReferenceLine
              y={targetCalories}
              label={{ value: 'Target', position: 'right', fill: COLORS.accent }}
              stroke={COLORS.accent}
              strokeDasharray="3 3"
            />
            <Bar
              dataKey="calories"
              fill={COLORS.primary}
              name="Calories per meal"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="cumulative"
              fill={COLORS.secondary}
              name="Cumulative calories"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        );
    }
  };

  return (
    <Box sx={{ mt: 4, mb: 4 }}>
      <Paper
        elevation={2}
        sx={{
          p: 4,
          borderRadius: 2,
          background: '#FFFFFF',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        }}
      >
        <Grid container spacing={4}>
          {/* Macronutrient Distribution */}
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={styles.title}>
                Macronutrient Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={macroData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {macroData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS.pieColors[index % COLORS.pieColors.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend
                    wrapperStyle={{
                      paddingTop: '20px',
                      fontSize: '0.875rem',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Grid>

          {/* Daily Calorie Intake */}
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 3 }}>
              <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 3
              }}>
                <Typography variant="h6" sx={styles.title}>
                  {analytics.period_days && analytics.period_days > 1 ? 'Period Calorie Intake' : 'Daily Calorie Intake'}
                </Typography>
                <FormControl size="small" sx={{ minWidth: 150, ...styles.select }}>
                  <InputLabel>Chart Type</InputLabel>
                  <Select
                    value={calorieChartType}
                    label="Chart Type"
                    onChange={(e) => setCalorieChartType(e.target.value as ChartType)}
                  >
                    <MenuItem value="bar">Bar Chart</MenuItem>
                    <MenuItem value="line">Line Chart</MenuItem>
                    <MenuItem value="area">Area Chart</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                {renderCalorieChart()}
              </ResponsiveContainer>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default ConsumptionCharts; 