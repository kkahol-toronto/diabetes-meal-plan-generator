import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Stack,
  Checkbox,
  FormControlLabel,
  Snackbar,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import DeleteIcon from '@mui/icons-material/Delete';
import { useNavigate } from 'react-router-dom';
import { MealPlanData } from '../types';
import { handleAuthError, getAuthHeaders } from '../utils/auth';

const MealPlanHistory = () => {
  console.log("MealPlanHistory component loaded");
  console.log('MealPlanHistory component mounted');
  const [mealPlans, setMealPlans] = useState<MealPlanData[]>([]);
  const [filteredPlans, setFilteredPlans] = useState<MealPlanData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMealPlans, setSelectedMealPlans] = useState<string[]>([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');
  const navigate = useNavigate();

  const fetchMealPlans = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers) {
        navigate('/login');
        return;
      }

      setLoading(true);
      const response = await fetch('http://localhost:8000/meal_plans', {
        headers,
      });

      if (!response.ok) {
        if (handleAuthError(response, navigate)) {
          return;
        }
        throw new Error('Failed to fetch meal plans');
      }

      const data = await response.json();
      const sortedPlans = (data.meal_plans || []).sort((a: MealPlanData, b: MealPlanData) => {
        const dateA = new Date(a.created_at || 0).getTime();
        const dateB = new Date(b.created_at || 0).getTime();
        return dateB - dateA;
      });
      setMealPlans(sortedPlans);
      setFilteredPlans(sortedPlans);
    } catch (err) {
      if (!handleAuthError(err, navigate)) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log("MealPlanHistory useEffect triggered");
    fetchMealPlans();
  }, [navigate]);

  useEffect(() => {
    const filtered = mealPlans.filter(plan => {
      // Skip corrupted plans
      if (!plan.id || !plan.created_at || !plan.dailyCalories || !plan.macronutrients) {
        return false;
      }

      const searchLower = searchQuery.toLowerCase();
      const dateStr = new Date(plan.created_at).toLocaleDateString();
      const planId = plan.id.toLowerCase();
      const calories = plan.dailyCalories.toString();
      const protein = (plan.macronutrients.protein ?? '').toString();
      const carbs = (plan.macronutrients.carbs ?? '').toString();
      const fats = (plan.macronutrients.fats ?? '').toString();

      return (
        planId.includes(searchLower) ||
        dateStr.includes(searchLower) ||
        calories.includes(searchLower) ||
        protein.includes(searchLower) ||
        carbs.includes(searchLower) ||
        fats.includes(searchLower)
      );
    });
    setFilteredPlans(filtered);
  }, [searchQuery, mealPlans]);

  const handleSelectPlan = (planId: string) => {
    setSelectedMealPlans(prevSelected =>
      prevSelected.includes(planId)
        ? prevSelected.filter(id => id !== planId)
        : [...prevSelected, planId]
    );
  };

  const handleDeleteSelected = async () => {
    if (selectedMealPlans.length === 0) return;

    if (!window.confirm(`Are you sure you want to delete ${selectedMealPlans.length} selected meal plan(s)?`)) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      if (!headers) {
        navigate('/login');
        return;
      }

      // Ensure all IDs have the correct prefix
      const formattedIds = selectedMealPlans.map(id => {
        return id.startsWith('meal_plan_') ? id : `meal_plan_${id}`;
      });

      const response = await fetch('http://localhost:8000/meal_plans/bulk_delete', {
        method: 'POST',
        headers,
        body: JSON.stringify({ plan_ids: formattedIds }),
      });

      if (!response.ok) {
        if (handleAuthError(response, navigate)) {
          return;
        }
        const result = await response.json();
        throw new Error(result.detail || 'Failed to delete selected meal plans.');
      }

      const result = await response.json();
      let message = result.message;
      if (result.failed_deletions?.length > 0) {
        message += `\nFailed to delete: ${result.failed_deletions.join(', ')}`;
      }
      if (result.corrupted_plans?.length > 0) {
        message += `\nCorrupted plans found and deleted: ${result.corrupted_plans.join(', ')}`;
      }

      setSnackbarMessage(message);
      setSnackbarSeverity(result.failed_deletions?.length > 0 ? 'warning' : 'success');
      setSnackbarOpen(true);

      setSelectedMealPlans([]);
      fetchMealPlans();

    } catch (err) {
      if (!handleAuthError(err, navigate)) {
        console.error('Error deleting selected plans:', err);
        setError(err instanceof Error ? err.message : 'An error occurred while deleting plans.');
        setSnackbarMessage(err instanceof Error ? err.message : 'Failed to delete plans.');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to delete ALL your meal plans? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      if (!headers) {
        navigate('/login');
        return;
      }

      const response = await fetch('http://localhost:8000/meal_plans/all', {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        if (handleAuthError(response, navigate)) {
          return;
        }
        const result = await response.json();
        throw new Error(result.detail || 'Failed to clear all meal plans.');
      }

      const result = await response.json();
      setSnackbarMessage(result.message || 'All meal plans deleted.');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      setSelectedMealPlans([]);
      setMealPlans([]);
      setFilteredPlans([]);

    } catch (err) {
      if (!handleAuthError(err, navigate)) {
        console.error('Error clearing all plans:', err);
        setError(err instanceof Error ? err.message : 'An error occurred while clearing plans.');
        setSnackbarMessage(err instanceof Error ? err.message : 'Failed to clear plans.');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays} days ago`;
      
      // Format as "Month Day, Year"
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return 'Invalid Date';
    }
  };

  const formatMealPlanId = (id: string) => {
    if (!id) return 'Unknown';
    // Remove 'meal_plan_' prefix if it exists
    const cleanId = id.replace('meal_plan_', '');
    // Take last 6 characters for display
    return cleanId.slice(-6).toUpperCase();
  };

   const handleCloseSnackbar = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  if (loading && filteredPlans.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ mb: 4 }}>
          Meal Plan History
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {filteredPlans.length > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mb: 2 }}>
                 <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={handleDeleteSelected}
                    disabled={selectedMealPlans.length === 0 || loading}
                 >
                    Delete Selected ({selectedMealPlans.length})
                 </Button>
                 <Button
                    variant="outlined"
                    color="error"
                    onClick={handleClearAll}
                    disabled={loading}
                 >
                    Clear All
                 </Button>
            </Box>
        )}

        <Box sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search by ID, date, calories, or macronutrients..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {filteredPlans.length === 0 ? (
          <Box textAlign="center" py={4}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {searchQuery ? 'No matching meal plans found' : 'No meal plans found'}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate('/meal-plan')}
              sx={{ mt: 2 }}
            >
              Create New Meal Plan
            </Button>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {filteredPlans.map((plan) => (
              <Grid item xs={12} md={6} lg={4} key={plan.id}>
                <Card 
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                >
                  <CardContent>
                     <FormControlLabel
                        control={
                           <Checkbox
                              checked={selectedMealPlans.includes(plan.id || '')}
                              onChange={() => handleSelectPlan(plan.id || '')}
                              disabled={!plan.id}
                           />
                        }
                        label={
                            <Typography variant="h6" gutterBottom>
                               Meal Plan {formatMealPlanId(plan.id || '')}
                            </Typography>
                        }
                        sx={{ mb: 1, alignItems: 'flex-start' }}
                     />
                   
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Created {formatDate(plan.created_at || '')}
                    </Typography>
                    
                    <Box mt={2}>
                      <Chip 
                        label={`${plan.dailyCalories || 'N/A'} kcal`}
                        color="primary"
                        sx={{ mb: 1 }}
                      />
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        <Chip
                          label={`Protein: ${plan.macronutrients?.protein ?? 'N/A'}g`}
                          variant="outlined"
                          size="small"
                        />
                        <Chip
                          label={`Carbs: ${plan.macronutrients?.carbs ?? 'N/A'}g`}
                          variant="outlined"
                          size="small"
                        />
                        <Chip
                          label={`Fats: ${plan.macronutrients?.fats ?? 'N/A'}g`}
                          variant="outlined"
                          size="small"
                        />
                      </Stack>
                    </Box>

                    <Box mt={2} display="flex" justifyContent="flex-end">
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        onClick={() => navigate(`/meal-plan/${plan.id || ''}`)}
                        disabled={!plan.id}
                      >
                        View Details
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/meal-plan')}
          >
            Create New Meal Plan
          </Button>
        </Box>
      </Paper>

      <Snackbar open={snackbarOpen} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default MealPlanHistory; 