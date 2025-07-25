// This is a React component file written in TypeScript (.tsx extension)
// React is a JavaScript library for building user interfaces with reusable components
// TypeScript adds type checking to JavaScript to catch errors early

// ===== IMPORT STATEMENTS =====
// These lines bring in external code/libraries that this file needs to use

// React is the core library - useState and useEffect are "hooks" (special functions)
// that let components store data and perform actions when things change
import React, { useState, useEffect } from 'react';

// Material-UI (MUI) is a component library that provides pre-built UI elements
// like buttons, cards, charts, etc. with consistent styling
import {
  Grid, Card, CardContent, Typography, Alert, Box,
  LinearProgress, Chip, CircularProgress, FormControl,
  InputLabel, Select, MenuItem, Button, Tooltip
} from '@mui/material';

// Chart.js components for creating different types of charts
// Radar = spider/star chart, Bar = column chart, Doughnut = pie chart, Line = line graph
import {
  Radar, Bar, Doughnut, Line
} from 'react-chartjs-2';

// Chart.js core components that need to be registered before using charts
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

// Import configuration settings (like API URLs) from another file
import config from '../../config/environment';

// ===== CHART.JS SETUP =====
// Register Chart.js components so they can be used in the application
// This is required before creating any charts
ChartJS.register(
  CategoryScale,      // For labeling chart axes
  LinearScale,        // For numeric scales  
  PointElement,       // For drawing points on charts
  LineElement,        // For drawing lines
  BarElement,         // For drawing bars
  RadialLinearScale,  // For radar/spider charts
  ArcElement,         // For pie/doughnut charts
  Title,              // For chart titles
  ChartTooltip,       // For hover tooltips
  Legend              // For chart legends
);

// ===== TYPE DEFINITIONS =====
// TypeScript interface - defines the shape/structure of data
// This tells TypeScript what properties this component expects to receive
interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';  // Must be one of these two values
  selectedPatient?: string;           // Optional (?) property - might not exist
  groupingCriteria?: string;          // Optional property
}

// ===== CONSTANTS =====
// Complete list of nutrients including micronutrients
// 'const' means this value cannot be changed after it's created
const NUTRIENTS_LIST = [
  // Macronutrients and energy - the main nutrients our body needs in large amounts
  'calories', 'protein', 'carbohydrates', 'fiber', 'total_fat', 'saturated_fat',
  // Vitamins - nutrients needed in small amounts for body functions
  'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
  'thiamin_b1', 'riboflavin_b2', 'niacin_b3', 'vitamin_b6', 'vitamin_b12', 'folate',
  // Minerals - inorganic substances needed for body functions
  'calcium', 'iron', 'magnesium', 'phosphorus', 'potassium', 'sodium', 'zinc'
];

// ===== UTILITY FUNCTION =====
// Function that takes a nutrient name and formats it nicely for display
// Arrow function syntax: const functionName = (parameters) => { code }
const formatNutrientName = (nutrient: string): string => {
  return nutrient
    .replace(/_/g, ' ')                     // Replace all underscores with spaces
    .replace(/\b\w/g, l => l.toUpperCase()) // Capitalize first letter of each word
    .replace(/B(\d+)/g, 'B$1');             // Keep B vitamin numbering (B1, B2, etc.)
};

// ===== INDIVIDUAL PATIENT ANALYSIS COMPONENT =====
// React component for analyzing one patient's nutrient data
// React.FC means "React Functional Component" with TypeScript
// The {selectedPatient: string} part defines what data this component receives
const IndividualNutrientAnalysis: React.FC<{selectedPatient: string}> = ({ selectedPatient }) => {
  
  // ===== STATE VARIABLES =====
  // useState is a React hook that creates a variable that can change over time
  // When these change, the component automatically re-renders (updates the display)
  
  // Stores the nutrient data fetched from the server
  // <any> means any type of data (not recommended in production but used here for simplicity)
  const [data, setData] = useState<any>(null);
  
  // Boolean (true/false) to track if we're currently loading data
  const [loading, setLoading] = useState(true);
  
  // String to track which nutrient is currently selected in the dropdown
  const [selectedNutrient, setSelectedNutrient] = useState<string>('all');

  // ===== EFFECT HOOK =====
  // useEffect runs code when the component first loads or when dependencies change
  // The array [selectedPatient] means this runs when selectedPatient changes
  useEffect(() => {
    // Only fetch data if a patient is actually selected
    if (selectedPatient) {
      fetchIndividualData(); // Call the function to get data
    }
  }, [selectedPatient]); // Dependency array - when this changes, run the effect

  // ===== ASYNC FUNCTION TO FETCH DATA =====
  // Async function that gets nutrient data from the server
  // 'async' means this function can wait for server responses
  const fetchIndividualData = async () => {
    try { // Try to execute this code, catch errors if they happen
      setLoading(true); // Show loading indicator
      
      // Fetch data from the server using the patient ID
      // Template literal `${}` inserts variables into strings
      const response = await fetch(`${config.API_URL}/admin/analytics/patient/${selectedPatient}/nutrient-adequacy`, {
        headers: { 
          // Authorization header with login token from browser storage
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json' // Tell server we're sending JSON
        }
      });
      
      // Check if the server response was successful
      if (!response.ok) {
        throw new Error('Failed to fetch data'); // Create an error if request failed
      }
      
      // Convert server response from JSON text to JavaScript object
      const result = await response.json();
      setData(result);    // Store the data in our state variable
      setLoading(false);  // Hide loading indicator
    } catch (error) { // If anything went wrong, handle the error
      console.error('Failed to fetch individual nutrient data:', error);
      setLoading(false); // Hide loading indicator even if there was an error
    }
  };

  // ===== HELPER FUNCTION =====
  // Function that returns an array of nutrient names that we have data for
  const getAvailableNutrients = (): string[] => {
    // If no data or no compliance percentages, return empty array
    if (!data || !data.compliance_percentages) return [];
    // Object.keys() gets all the property names from an object
    return Object.keys(data.compliance_percentages);
  };

  // ===== CHART CREATION FUNCTION =====
  // Function that creates data structure for radar (spider) charts
  const createRadarChart = () => {
    // Early return if no data available
    if (!data || !data.compliance_percentages) return null;
    
    const availableNutrients = getAvailableNutrients();
    let nutrients, values; // Variables to hold chart data
    
    // If showing all nutrients
    if (selectedNutrient === 'all') {
      nutrients = availableNutrients;
      // .map() creates a new array by transforming each element
      values = availableNutrients.map(n => data.compliance_percentages[n]);
    } else if (availableNutrients.includes(selectedNutrient)) {
      // If showing one specific nutrient
      nutrients = [selectedNutrient];
      values = [data.compliance_percentages[selectedNutrient]];
    } else {
      return null; // Selected nutrient not available
    }
    
    // Return chart.js data structure
    return {
      labels: nutrients.map(n => formatNutrientName(n)), // Chart labels
      datasets: [{
        label: 'RDA Compliance %',           // Legend label
        data: values,                        // The actual data points
        backgroundColor: 'rgba(102, 126, 234, 0.2)', // Fill color (semi-transparent)
        borderColor: '#667eea',              // Line color
        borderWidth: 2,                      // Line thickness
        pointBackgroundColor: '#667eea',     // Point color
        pointRadius: 4,                      // Point size
      }]
    };
  };

  // ===== ANOTHER CHART CREATION FUNCTION =====
  // Function that creates data structure for bar charts
  const createBarChart = () => {
    // Similar logic to radar chart but for bar chart format
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
        // Generate different colors for each bar using HSL color space
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

  // ===== COLOR HELPER FUNCTION =====
  // Function that returns appropriate color based on nutrient status
  const getStatusColor = (status: string) => {
    // Switch statement - like multiple if/else conditions
    switch (status) {
      case 'adequate': return '#4caf50';     // Green for good
      case 'below_target': return '#ff9800'; // Orange for warning
      case 'deficient': return '#f44336';    // Red for deficient
      case 'within_limit': return '#4caf50'; // Green for within limits
      case 'elevated': return '#ff9800';     // Orange for elevated
      case 'excessive': return '#f44336';    // Red for excessive
      default: return '#9e9e9e';             // Gray for unknown
    }
  };

  // ===== CONDITIONAL RENDERING =====
  // These if statements determine what to show based on the current state

  // If still loading data, show a spinning loading indicator
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // If no data was received, show an error message
  if (!data) {
    return (
      <Alert severity="error">
        Failed to load nutrient adequacy data for this patient.
      </Alert>
    );
  }

  // If patient hasn't registered yet, show limited information
  if (data.registration_status === 'not_registered') {
    return (
      <Alert severity="info">
        This patient has not registered yet. Only RDA targets are available.
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2">RDA Targets for {data.patient_name}:</Typography>
          <Grid container spacing={1} sx={{ mt: 1 }}>
            {/* Object.entries() converts object to array of [key, value] pairs */}
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

  // ===== PREPARATION FOR MAIN RENDER =====
  const availableNutrients = getAvailableNutrients();
  // Conditional operator: condition ? valueIfTrue : valueIfFalse
  // Choose chart type based on selection and number of nutrients
  const chartData = selectedNutrient === 'all' || availableNutrients.length <= 5 ? createRadarChart() : createBarChart();

  // ===== MAIN COMPONENT RENDER =====
  // JSX (JavaScript XML) - looks like HTML but is actually JavaScript
  // Components must return exactly one parent element
  return (
    <Grid container spacing={3}>
      {/* Grid system for responsive layout - like CSS flexbox */}
      
      {/* Nutrient Filter Dropdown */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Filter by Nutrient</Typography>
            <FormControl fullWidth>
              <InputLabel>Select Nutrient</InputLabel>
              <Select
                value={selectedNutrient}
                // Event handler - runs when user changes selection
                onChange={(e) => setSelectedNutrient(e.target.value)}
                label="Select Nutrient"
              >
                <MenuItem value="all">All Nutrients</MenuItem>
                {/* Map over available nutrients to create menu items */}
                {availableNutrients.map(nutrient => (
                  <MenuItem key={nutrient} value={nutrient}>
                    {formatNutrientName(nutrient)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {/* Conditional rendering with && operator - only show if condition is true */}
            {selectedNutrient !== 'all' && availableNutrients.includes(selectedNutrient) && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="primary" fontWeight="bold">
                  {formatNutrientName(selectedNutrient)} Compliance
                </Typography>
                <Typography variant="h4" color="primary">
                  {/* .toFixed(1) rounds number to 1 decimal place */}
                  {data.compliance_percentages[selectedNutrient].toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={data.compliance_percentages[selectedNutrient]} 
                  sx={{ 
                    height: 8,
                    borderRadius: 4,
                    mt: 1,
                    // Dynamic CSS based on compliance percentage
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
                  // Ternary operator for color based on score
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
              {/* .filter() creates new array with items that match condition */}
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
              {/* Template literal with conditional text */}
              {selectedNutrient === 'all' ? 'All Nutrients Compliance' : `${formatNutrientName(selectedNutrient)} Compliance`}
            </Typography>
            {/* Only render chart if we have data */}
            {chartData ? (
              <Box sx={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                {/* Conditional rendering of different chart types */}
                {selectedNutrient === 'all' && availableNutrients.length <= 5 ? (
                  <Radar 
                    data={chartData} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: { 
                        r: {  // 'r' is for radial scale in radar charts
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
                        y: {  // Y-axis configuration
                          beginAtZero: true, 
                          max: 100,
                          ticks: {
                            stepSize: 10,
                            // Callback function to format tick labels
                            callback: function(value) {
                              return value + '%';
                            }
                          }
                        },
                        x: { // X-axis configuration
                          ticks: {
                            maxRotation: 45 // Rotate labels if needed
                          }
                        }
                      },
                      plugins: {
                        legend: {
                          display: false
                        },
                        tooltip: {
                          callbacks: {
                            // Custom tooltip text
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
      {/* && operator: only render if condition is true */}
      {data.deficiencies && data.deficiencies.length > 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>⚠️ Identified Issues</Typography>
              <Grid container spacing={2}>
                {/* Map over deficiencies array to create list items */}
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
                      {/* Only show recommendation if it exists */}
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

// ===== COHORT ANALYSIS COMPONENT =====
// Component for analyzing groups of patients together
const CohortNutrientAnalysis: React.FC<{groupingCriteria: string}> = ({ groupingCriteria }) => {
  // State variables for this component
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  // Array state for tracking multiple selected nutrients
  const [selectedNutrients, setSelectedNutrients] = useState<string[]>(['calories', 'protein', 'carbohydrates', 'fiber']);

  // Effect that runs when grouping criteria changes
  useEffect(() => {
    fetchCohortData();
  }, [groupingCriteria]);

  // Function to fetch data for multiple patients grouped together
  const fetchCohortData = async () => {
    try {
      setLoading(true);
      // API call with query parameter for grouping
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

  // Function to get all available nutrients across all patient groups
  const getAvailableNutrients = (): string[] => {
    if (!data || !data.groups) return [];
    
    // Set data structure automatically removes duplicates
    const allNutrients = new Set<string>();
    // Object.values() gets all the values from an object (ignoring the keys)
    Object.values(data.groups).forEach((group: any) => {
      if (group.rda_compliance_stats) {
        Object.keys(group.rda_compliance_stats).forEach(nutrient => {
          allNutrients.add(nutrient);
        });
      }
    });
    
    // Convert Set back to Array
    return Array.from(allNutrients);
  };

  // Function to create chart data for compliance comparison
  const createComplianceChart = () => {
    if (!data) return null;
    
    const groups = Object.keys(data.groups);
    const availableNutrients = getAvailableNutrients();
    // Filter selected nutrients to only include ones we have data for
    const nutrientsToShow = selectedNutrients.filter(n => availableNutrients.includes(n));
    
    // Create dataset for each nutrient
    const datasets = nutrientsToShow.map((nutrient, index) => ({
      label: formatNutrientName(nutrient),
      data: groups.map(group => {
        const stats = data.groups[group].rda_compliance_stats[nutrient];
        const value = stats ? stats.percentage_meeting_target : 0;
        return value;
      }),
      // HSL color generation for unlimited colors
      backgroundColor: `hsla(${(index * 137.5) % 360}, 70%, 60%, 0.8)`,
      borderWidth: 1,
      borderColor: `hsla(${(index * 137.5) % 360}, 70%, 50%, 1)`,
    }));

    return {
      labels: groups,
      datasets
    };
  };

  // Function to create deficiency summary chart
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
          // Add up patients affected across groups
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

  // Loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
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
                multiple // Allow selecting multiple items
                value={selectedNutrients}
                onChange={(e) => setSelectedNutrients(e.target.value as string[])}
                label="Choose Nutrients for Chart"
                // Custom rendering of selected values as chips
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
              {/* Quick filter buttons */}
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
                // Filter available nutrients to only include vitamins
                onClick={() => setSelectedNutrients(availableNutrients.filter(n => 
                  ['vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'vitamin_b6', 'vitamin_b12', 'folate'].includes(n)
                ))}
              >
                Vitamins Only
              </Button>
              <Button 
                size="small" 
                variant="outlined"
                // Filter available nutrients to only include minerals
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
              {/* .reduce() combines array values into single value */}
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
              {/* Show subtitle if filtering */}
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
              {/* Object.entries() converts object to [key, value] pairs for iteration */}
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
                      {/* .slice(0, 3) gets first 3 items from array */}
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

// ===== MAIN COMPONENT =====
// The main component that decides whether to show individual or cohort analysis
const NutrientAdequacy: React.FC<AnalyticsViewProps> = ({ 
  viewMode,        // Either 'individual' or 'cohort'
  selectedPatient, // Patient ID for individual analysis
  groupingCriteria // How to group patients for cohort analysis
}) => {
  
  // Function that returns description text based on current mode
  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Nutrient adequacy analysis for patient ${selectedPatient}`
        : 'Please select a patient to view individual nutrient analysis';
    }
    // For cohort mode
    return `Cohort nutrient adequacy grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  // Main render function - returns JSX
  return (
    <Box>
      {/* Main title with emoji */}
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        🥗 Nutrient Adequacy Analysis
      </Typography>
      
      {/* Information alert showing current mode */}
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {/* Conditional rendering based on view mode */}
      {viewMode === 'individual' ? (
        // Individual patient analysis
        selectedPatient ? (
          <IndividualNutrientAnalysis selectedPatient={selectedPatient} />
        ) : (
          <Alert severity="warning">
            Please select a patient from the dropdown above to view individual nutrient analysis.
          </Alert>
        )
      ) : (
        // Cohort analysis
        <CohortNutrientAnalysis groupingCriteria={groupingCriteria || 'diabetes_type'} />
      )}
    </Box>
  );
};

// ===== EXPORT =====
// Make this component available for import in other files
// 'default' means this is the main thing exported from this file
export default NutrientAdequacy; 