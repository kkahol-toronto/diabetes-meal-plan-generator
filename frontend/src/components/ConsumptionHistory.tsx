import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Avatar,
  Fade,
  Slide,
  Zoom,
  useTheme,
  keyframes,
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import { useNavigate } from 'react-router-dom';

// Animations
const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
  100% { transform: translateY(0px); }
`;

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const shimmer = keyframes`
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
`;

const gradientShift = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

interface ConsumptionRecord {
  id: string;
  timestamp: string;
  food_name: string;
  estimated_portion: string;
  nutritional_info: {
    calories: number;
    carbohydrates: number;
    protein: number;
    fat: number;
    fiber: number;
    sugar: number;
    sodium: number;
  };
  medical_rating: {
    diabetes_suitability: string;
    glycemic_impact: string;
    recommended_frequency: string;
    portion_recommendation: string;
  };
  image_analysis: string;
  image_url: string;
}

interface Analytics {
  period_days: number;
  total_records: number;
  total_calories: number;
  average_daily_calories: number;
  total_macronutrients: {
    carbohydrates: number;
    protein: number;
    fat: number;
  };
  diabetes_suitable_percentage: number;
  consumption_records: ConsumptionRecord[];
}

const ConsumptionHistory = () => {
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);
  const [consumptionHistory, setConsumptionHistory] = useState<ConsumptionRecord[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analyticsPeriod, setAnalyticsPeriod] = useState(7);
  const navigate = useNavigate();

  useEffect(() => {
    setLoaded(true);
  }, []);

  useEffect(() => {
    fetchConsumptionHistory();
    fetchAnalytics(analyticsPeriod);

    // Add event listener for consumption record updates
    const handleConsumptionRecorded = () => {
      fetchConsumptionHistory();
      fetchAnalytics(analyticsPeriod);
    };

    window.addEventListener('consumptionRecorded', handleConsumptionRecorded);

    // Cleanup
    return () => {
      window.removeEventListener('consumptionRecorded', handleConsumptionRecorded);
    };
  }, [analyticsPeriod]);

  const fetchConsumptionHistory = async () => {
    try {
      setIsLoading(true);
      console.log('Fetching consumption history...');
      const token = localStorage.getItem('token');
      console.log('Using token:', token ? 'Token exists' : 'No token found');
      
      const response = await fetch('http://localhost:8000/consumption/history?limit=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const data = await response.json();
        console.log('Received consumption history:', data);
        console.log('Number of records:', data.length);
        if (data.length > 0) {
          console.log('First record:', data[0]);
          console.log('First record keys:', Object.keys(data[0]));
        } else {
          console.log('No records found in the response');
        }
        setConsumptionHistory(data);
      } else {
        console.error('Failed to fetch consumption history:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error response:', errorText);
        setError('Failed to fetch consumption history');
      }
    } catch (error) {
      console.error('Error fetching consumption history:', error);
      setError('Error fetching consumption history');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAnalytics = async (days: number) => {
    try {
      setAnalyticsLoading(true);
      const response = await fetch(`http://localhost:8000/consumption/analytics?days=${days}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        console.error('Failed to fetch analytics');
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleAnalyticsPeriodChange = (event: any) => {
    const days = event.target.value;
    setAnalyticsPeriod(days);
    fetchAnalytics(days);
  };

  const getSuitabilityColor = (suitability: string) => {
    switch (suitability?.toLowerCase()) {
      case 'high':
      case 'good':
      case 'suitable':
        return 'success';
      case 'medium':
      case 'moderate':
        return 'warning';
      case 'low':
      case 'poor':
      case 'avoid':
        return 'error';
      default:
        return 'default';
    }
  };

  const getGlycemicImpactIcon = (impact: string) => {
    switch (impact?.toLowerCase()) {
      case 'low':
        return <TrendingDownIcon color="success" />;
      case 'high':
        return <TrendingUpIcon color="error" />;
      default:
        return <TrendingUpIcon color="warning" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      // Handle the case where backend sends UTC timestamp without 'Z' suffix
      let processedTimestamp = timestamp;
      
      // If the string doesn't end with 'Z' or timezone info, assume it's UTC
      if (!timestamp.includes('Z') && !timestamp.includes('+') && !timestamp.includes('-', 10)) {
        processedTimestamp = timestamp + 'Z';
      }
      
      const date = new Date(processedTimestamp);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }

      // Return formatted timestamp in user's local timezone
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
      });
    } catch (e) {
      return 'Invalid Date';
    }
  };

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: `linear-gradient(-45deg, ${theme.palette.primary.main}08, ${theme.palette.secondary.main}08, ${theme.palette.primary.main}05, ${theme.palette.secondary.main}05)`,
          backgroundSize: '400% 400%',
          animation: `${gradientShift} 15s ease infinite`,
          py: 4,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress 
              size={60}
              sx={{
                animation: `${pulse} 2s ease-in-out infinite`,
              }}
            />
          </Box>
        </Container>
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: `linear-gradient(-45deg, ${theme.palette.primary.main}08, ${theme.palette.secondary.main}08, ${theme.palette.primary.main}05, ${theme.palette.secondary.main}05)`,
          backgroundSize: '400% 400%',
          animation: `${gradientShift} 15s ease infinite`,
          py: 4,
        }}
      >
        <Container maxWidth="lg">
          <Alert 
            severity="error"
            sx={{
              borderRadius: 3,
              animation: `${pulse} 1s ease`,
            }}
          >
            {error}
          </Alert>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(-45deg, ${theme.palette.primary.main}08, ${theme.palette.secondary.main}08, ${theme.palette.primary.main}05, ${theme.palette.secondary.main}05)`,
        backgroundSize: '400% 400%',
        animation: `${gradientShift} 15s ease infinite`,
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Fade in={loaded} timeout={1000}>
          <Typography 
            variant="h3" 
            component="h1" 
            gutterBottom
            align="center"
            sx={{
              fontWeight: 800,
              mb: 4,
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              textShadow: '0 4px 8px rgba(0,0,0,0.1)',
            }}
          >
            📊 Consumption History
          </Typography>
        </Fade>

        {/* Analytics Overview */}
        <Slide direction="down" in={loaded} timeout={1200}>
          <Box>
            <Paper 
              elevation={0}
              sx={{ 
                p: 4, 
                mb: 4,
                borderRadius: 4,
                background: 'rgba(255,255,255,0.95)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255,255,255,0.3)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: '-200px',
                  width: '200px',
                  height: '100%',
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                  animation: `${shimmer} 3s infinite`,
                },
              }}
            >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h2">
            Analytics Overview
          </Typography>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Period</InputLabel>
            <Select
              value={analyticsPeriod}
              label="Period"
              onChange={handleAnalyticsPeriodChange}
            >
              <MenuItem value={1}>1 Day</MenuItem>
              <MenuItem value={7}>7 Days</MenuItem>
              <MenuItem value={14}>14 Days</MenuItem>
              <MenuItem value={30}>30 Days</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {analyticsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        ) : analytics ? (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Records
                  </Typography>
                  <Typography variant="h4">
                    {analytics.total_records}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Calories
                  </Typography>
                  <Typography variant="h4">
                    <LocalFireDepartmentIcon color="warning" sx={{ mr: 1 }} />
                    {Math.round(analytics.total_calories)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Avg: {Math.round(analytics.average_daily_calories)}/day
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Diabetes Suitable
                  </Typography>
                  <Typography variant="h4" color={analytics.diabetes_suitable_percentage >= 70 ? 'success.main' : 'warning.main'}>
                    {Math.round(analytics.diabetes_suitable_percentage)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Macronutrients
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography variant="h6" color="textPrimary">
                      Carbs: {Math.round(analytics.total_macronutrients.carbohydrates)}g
                    </Typography>
                    <Typography variant="h6" color="textPrimary">
                      Protein: {Math.round(analytics.total_macronutrients.protein)}g
                    </Typography>
                    <Typography variant="h6" color="textPrimary">
                      Fat: {Math.round(analytics.total_macronutrients.fat)}g
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
            ) : null}
            </Paper>

            {/* Consumption History Timeline */}
            <Paper 
              elevation={0}
              sx={{ 
                p: 4,
                borderRadius: 4,
                background: 'rgba(255,255,255,0.95)',
                backdropFilter: 'blur(15px)',
                border: '1px solid rgba(255,255,255,0.3)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
                },
              }}
            >
              <Typography 
                variant="h5" 
                component="h2" 
                gutterBottom
                sx={{
                  fontWeight: 700,
                  color: theme.palette.primary.main,
                  mb: 3,
                }}
              >
                📋 Recent Consumption
              </Typography>

              {consumptionHistory.length === 0 ? (
                <Alert 
                  severity="info"
                  sx={{
                    borderRadius: 3,
                    animation: `${pulse} 1s ease`,
                  }}
                >
                  No consumption records found. Start recording your meals using the "Record Food" feature in the chat!
                </Alert>
              ) : (
                <Timeline>
            {consumptionHistory.map((record, index) => (
              <TimelineItem key={record.id}>
                <TimelineOppositeContent sx={{ m: 'auto 0' }} color="text.secondary">
                  {formatTimestamp(record.timestamp)}
                </TimelineOppositeContent>
                <TimelineSeparator>
                  <TimelineDot color="primary">
                    <RestaurantIcon />
                  </TimelineDot>
                  {index < consumptionHistory.length - 1 && <TimelineConnector />}
                </TimelineSeparator>
                <TimelineContent sx={{ py: '12px', px: 2 }}>
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                        <Typography variant="h6" component="span">
                          {record.food_name}
                        </Typography>
                        <Chip
                          label={record.medical_rating?.diabetes_suitability || 'Unknown'}
                          color={getSuitabilityColor(record.medical_rating?.diabetes_suitability) as any}
                          size="small"
                        />
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getGlycemicImpactIcon(record.medical_rating?.glycemic_impact)}
                          <Typography variant="body2" color="textSecondary">
                            {record.nutritional_info?.calories || 0} cal
                          </Typography>
                        </Box>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={4}>
                          {record.image_url && (
                            <Box sx={{ mb: 2 }}>
                              <img
                                src={`data:image/jpeg;base64,${record.image_url}`}
                                alt={record.food_name}
                                style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '8px' }}
                              />
                            </Box>
                          )}
                          <Typography variant="body2" color="textSecondary">
                            Portion: {record.estimated_portion}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <Typography variant="subtitle2" gutterBottom>
                            Nutritional Information:
                          </Typography>
                          <TableContainer>
                            <Table size="small">
                              <TableBody>
                                <TableRow>
                                  <TableCell>Calories</TableCell>
                                  <TableCell>{record.nutritional_info?.calories || 'N/A'}</TableCell>
                                </TableRow>
                                <TableRow>
                                  <TableCell>Carbohydrates</TableCell>
                                  <TableCell>{record.nutritional_info?.carbohydrates || 'N/A'}g</TableCell>
                                </TableRow>
                                <TableRow>
                                  <TableCell>Protein</TableCell>
                                  <TableCell>{record.nutritional_info?.protein || 'N/A'}g</TableCell>
                                </TableRow>
                                <TableRow>
                                  <TableCell>Fat</TableCell>
                                  <TableCell>{record.nutritional_info?.fat || 'N/A'}g</TableCell>
                                </TableRow>
                                <TableRow>
                                  <TableCell>Fiber</TableCell>
                                  <TableCell>{record.nutritional_info?.fiber || 'N/A'}g</TableCell>
                                </TableRow>
                                <TableRow>
                                  <TableCell>Sugar</TableCell>
                                  <TableCell>{record.nutritional_info?.sugar || 'N/A'}g</TableCell>
                                </TableRow>
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <Typography variant="subtitle2" gutterBottom>
                            Medical Rating:
                          </Typography>
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="body2">
                              <strong>Diabetes Suitability:</strong> {record.medical_rating?.diabetes_suitability || 'N/A'}
                            </Typography>
                          </Box>
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="body2">
                              <strong>Glycemic Impact:</strong> {record.medical_rating?.glycemic_impact || 'N/A'}
                            </Typography>
                          </Box>
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="body2">
                              <strong>Recommended Frequency:</strong> {record.medical_rating?.recommended_frequency || 'N/A'}
                            </Typography>
                          </Box>
                          {record.medical_rating?.portion_recommendation && (
                            <Box sx={{ mb: 1 }}>
                              <Typography variant="body2">
                                <strong>Portion Recommendation:</strong> {record.medical_rating.portion_recommendation}
                              </Typography>
                            </Box>
                          )}
                          
                          {record.image_analysis && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Analysis Notes:
                              </Typography>
                              <Typography variant="body2" sx={{ backgroundColor: 'grey.100', p: 1, borderRadius: 1, fontSize: '0.875rem' }}>
                                {record.image_analysis}
                              </Typography>
                            </Box>
                          )}
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
                      )}
            </Paper>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/chat')}
                sx={{
                  borderRadius: 3,
                  px: 3,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    backgroundColor: theme.palette.primary.main,
                    color: 'white',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
                  },
                }}
              >
                📝 Record New Consumption
              </Button>
            </Box>
          </Box>
        </Slide>
      </Container>
    </Box>
  );
};

export default ConsumptionHistory; 