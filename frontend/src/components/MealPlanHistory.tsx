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
  Tooltip,
  Collapse,
  Fade,
  Slide,
  Zoom,
  useTheme,
  keyframes,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useNavigate } from 'react-router-dom';
import { MealPlanData } from '../types';
import { handleAuthError, getAuthHeaders } from '../utils/auth';

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

const MealPlanHistory = () => {
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);
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
  const [showDetails, setShowDetails] = useState(false);
  const [details, setDetails] = useState('');
  const navigate = useNavigate();

  // Helper functions to manage permanently deleted IDs
  const getDeletedIds = (): string[] => {
    try {
      const stored = localStorage.getItem('deleted_meal_plan_ids');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  };

  const addDeletedIds = (ids: string[]) => {
    try {
      console.log('addDeletedIds called with:', ids);
      const existingDeleted = getDeletedIds();
      console.log('Existing deleted IDs:', existingDeleted);
      const uniqueIds = new Set([...existingDeleted, ...ids]);
      const newDeleted = Array.from(uniqueIds);
      console.log('New deleted IDs array to store:', newDeleted);
      localStorage.setItem('deleted_meal_plan_ids', JSON.stringify(newDeleted));
      console.log('Successfully stored deleted IDs in localStorage');
    } catch (error) {
      console.log('Failed to save deleted IDs to localStorage:', error);
    }
  };

  const clearAllDeletedIds = () => {
    try {
      localStorage.removeItem('deleted_meal_plan_ids');
    } catch (error) {
      console.log('Failed to clear deleted IDs from localStorage:', error);
    }
  };

  const fetchMealPlans = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      if (!headers) {
        navigate('/login');
        return;
      }

      const response = await fetch('http://localhost:8000/meal_plans', {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        if (handleAuthError(response, navigate)) {
          return;
        }
        throw new Error(`HTTP ${response.status}: Failed to fetch meal plans.`);
      }

      const data = await response.json();
      console.log('Fetched meal plans from backend:', data);
      
      // Get permanently deleted IDs
      const deletedIds = getDeletedIds();
      console.log('Permanently deleted IDs from localStorage:', deletedIds);
      
      // Filter out permanently deleted meal plans
      const allPlans = data.meal_plans || [];
      console.log('All plans from backend (before filtering):', allPlans.map((p: MealPlanData) => ({ id: p.id, created_at: p.created_at })));
      
      const visiblePlans = allPlans.filter((plan: MealPlanData) => {
        const planId = plan.id;
        const isDeleted = planId && deletedIds.includes(planId);
        console.log(`Plan ${planId}: deleted=${isDeleted}`);
        return planId && !isDeleted;
      });
      
      console.log('Visible plans after filtering:', visiblePlans.length, 'of', allPlans.length);
      console.log('Visible plan IDs:', visiblePlans.map((p: MealPlanData) => p.id));
      
      setMealPlans(visiblePlans);
      setFilteredPlans(visiblePlans);
    } catch (err) {
      if (!handleAuthError(err, navigate)) {
        console.error('Error fetching meal plans:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch meal plans.');
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
    console.log('handleSelectPlan called with planId:', planId);
    console.log('Current selectedMealPlans:', selectedMealPlans);
    
    setSelectedMealPlans(prevSelected => {
      const isCurrentlySelected = prevSelected.includes(planId);
      const newSelection = isCurrentlySelected
        ? prevSelected.filter(id => id !== planId)
        : [...prevSelected, planId];
      
      console.log('New selection will be:', newSelection);
      return newSelection;
    });
  };

  const handleSelectAll = () => {
    const allCurrentIds = filteredPlans.map(plan => plan.id).filter(Boolean) as string[];
    console.log('handleSelectAll - all current IDs:', allCurrentIds);
    console.log('handleSelectAll - currently selected:', selectedMealPlans);
    
    const allSelected = allCurrentIds.every(id => selectedMealPlans.includes(id));
    
    if (allSelected) {
      // Deselect all visible plans
      setSelectedMealPlans(prev => prev.filter(id => !allCurrentIds.includes(id)));
      console.log('Deselecting all visible plans');
    } else {
      // Select all visible plans
      const newSelections = allCurrentIds.filter(id => !selectedMealPlans.includes(id));
      setSelectedMealPlans(prev => [...prev, ...newSelections]);
      console.log('Selecting all visible plans, new selections:', newSelections);
    }
  };

  const handleDeleteSelected = async () => {
    console.log('handleDeleteSelected called');
    console.log('selectedMealPlans:', selectedMealPlans);
    
    if (selectedMealPlans.length === 0) {
      console.log('No meal plans selected, returning early');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete ${selectedMealPlans.length} selected meal plan(s)?`)) {
      console.log('User cancelled deletion');
      return;
    }

    // Get the selected meal plans from current state
    const selectedPlans = mealPlans.filter(plan => selectedMealPlans.includes(plan.id || ''));
    const selectedIds = selectedPlans.map(plan => plan.id).filter(Boolean) as string[];
    
    console.log('Selected plans to delete:', selectedIds);

    // Add ALL selected IDs to permanently deleted list (just like Clear All does)
    addDeletedIds(selectedIds);

    // IMMEDIATELY remove selected plans from UI (just like Clear All does)
    const remainingPlans = mealPlans.filter(plan => !selectedIds.includes(plan.id || ''));
    setMealPlans(remainingPlans);
    setFilteredPlans(remainingPlans);
    setSelectedMealPlans([]);

    // Show success message
    setSnackbarMessage(`${selectedIds.length} meal plan(s) permanently removed from your history!`);
    setSnackbarSeverity('success');
    setSnackbarOpen(true);

    console.log('Selected plans deleted from frontend. Remaining plans:', remainingPlans.length);

    // Try backend deletion in background (optional - user doesn't care)
    try {
      const headers = getAuthHeaders();
      if (headers) {
        fetch('http://localhost:8000/meal_plans/bulk_delete', {
          method: 'POST',
          headers,
          body: JSON.stringify({ plan_ids: selectedIds }),
        }).catch(() => {
          console.log('Backend deletion failed, but UI already updated');
        });
      }
    } catch (error) {
      console.log('Backend deletion failed, but UI already updated');
    }
  };

  const handleClearAll = async () => {
    if (mealPlans.length === 0) {
      setSnackbarMessage('No meal plans to delete.');
      setSnackbarSeverity('info');
      setSnackbarOpen(true);
      return;
    }

    if (!window.confirm(`Are you sure you want to delete ALL ${mealPlans.length} meal plans? This action cannot be undone.`)) {
      return;
    }

    // Get all current meal plan IDs to permanently delete
    const allCurrentIds = mealPlans.map(plan => plan.id).filter(Boolean) as string[];
    
    // Add all current IDs to permanently deleted list FIRST
    addDeletedIds(allCurrentIds);

    // IMMEDIATELY clear all from UI - user doesn't want to see them anymore
    const totalCount = mealPlans.length;
    setSelectedMealPlans([]);
    setMealPlans([]);
    setFilteredPlans([]);
    setSearchQuery('');

    // Show success message immediately
    setSnackbarMessage(`All ${totalCount} meal plans permanently removed from your history!`);
    setSnackbarSeverity('success');
    setSnackbarOpen(true);

    // Try to delete from backend in the background (optional - user doesn't care if this fails)
    try {
      const headers = getAuthHeaders();
      if (headers) {
        fetch('http://localhost:8000/meal_plans/all', {
          method: 'DELETE',
          headers,
        }).catch(() => {
          // Silent fail - user doesn't care about backend errors
          console.log('Backend clear all failed, but UI already updated');
        });
      }
    } catch (error) {
      // Silent fail - user doesn't care about backend errors
      console.log('Backend clear all failed, but UI already updated');
    }
  };

  const formatDate = (dateString: string) => {
    try {
      // Handle the case where backend sends UTC timestamp without 'Z' suffix
      let processedDateString = dateString;
      
      // If the string doesn't end with 'Z' or timezone info, assume it's UTC
      if (!dateString.includes('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
        processedDateString = dateString + 'Z';
      }
      
      const date = new Date(processedDateString);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }

      const now = new Date();
      // Zero out the time for both dates to compare only the date part (in local timezone)
      const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const diffTime = nowOnly.getTime() - dateOnly.getTime();
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

      // Format time in user's local timezone
      const timeString = date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
      });

      if (diffDays === 0) return `Today, ${timeString}`;
      if (diffDays === 1) return `Yesterday, ${timeString}`;
      // For all earlier dates, show as 'Month Day, Year, HH:MM AM/PM'
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }) + `, ${timeString}`;
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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={handleSelectAll}
                        disabled={loading}
                    >
                        {filteredPlans.every(plan => selectedMealPlans.includes(plan.id || '')) 
                            ? 'Deselect All' 
                            : 'Select All'
                        }
                    </Button>
                    <Typography variant="body2" sx={{ alignSelf: 'center', color: 'text.secondary' }}>
                        {selectedMealPlans.length} of {filteredPlans.length} selected
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                     <Tooltip title="If a plan can't be deleted, it may have already been removed or is corrupted. The list will refresh automatically.">
                       <span>
                     <Button
                        variant="outlined"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={handleDeleteSelected}
                        disabled={selectedMealPlans.length === 0 || loading}
                     >
                        Delete Selected ({selectedMealPlans.length})
                     </Button>
                       </span>
                     </Tooltip>
                     <Button
                        variant="outlined"
                        color="error"
                        onClick={handleClearAll}
                        disabled={loading}
                     >
                        Clear All
                     </Button>
                </Box>
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

      </Paper>

      <Snackbar open={snackbarOpen} autoHideDuration={6000} onClose={handleCloseSnackbar} anchorOrigin={{ vertical: 'top', horizontal: 'center' }}>
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage.split('\n').map((line, idx) => <div key={idx}>{line}</div>)}
          {snackbarMessage.includes('Details available.') && (
            <>
              <Button
                color="inherit"
                size="small"
                endIcon={<ExpandMoreIcon />}
                onClick={() => setShowDetails((prev) => !prev)}
                sx={{ mt: 1 }}
              >
                {showDetails ? 'Hide Details' : 'Show Details'}
              </Button>
              <Collapse in={showDetails}>
                <Box sx={{ mt: 1, bgcolor: '#f9f9f9', p: 1, borderRadius: 1, fontSize: 13, color: '#555' }}>
                  {details}
                </Box>
              </Collapse>
            </>
          )}
        </Alert>
      </Snackbar>
      {loading && (
        <Box position="fixed" top={0} left={0} width="100vw" height="100vh" zIndex={2000} display="flex" alignItems="center" justifyContent="center" bgcolor="rgba(255,255,255,0.6)">
          <CircularProgress size={60} />
        </Box>
      )}
    </Container>
  );
};

export default MealPlanHistory; 