import React, { useState, useEffect } from 'react';
import config from '../config/environment';
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
import DownloadIcon from '@mui/icons-material/Download';
import { useNavigate } from 'react-router-dom';
import { MealPlanData } from '../types';
import { handleAuthError, getAuthHeaders } from '../utils/auth';
import { mealPlanApi } from '../utils/api';

// Enhanced Mobile Animations
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

const slideInUp = keyframes`
  0% { 
    opacity: 0;
    transform: translateY(30px);
  }
  100% { 
    opacity: 1;
    transform: translateY(0);
  }
`;

const fadeInScale = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.95);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

const bounceIn = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.3);
  }
  50% { 
    opacity: 1;
    transform: scale(1.05);
  }
  70% { 
    transform: scale(0.9);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

const glow = keyframes`
  0% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
  50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.8), 0 0 30px rgba(102, 126, 234, 0.4); }
  100% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
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
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info'>('success');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [details, setDetails] = useState('');
  const navigate = useNavigate();

  const fetchMealPlans = async (forceRefresh: boolean = false) => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      if (!headers) {
        navigate('/login');
        return;
      }

      // ROBUST CACHE CLEARING: Add cache-busting parameters when force refreshing
      const cacheParams = forceRefresh ? `?_t=${Date.now()}&_refresh=true` : '';
      
      // Clear any browser/axios caches if force refreshing
      if (forceRefresh) {
        console.log('[CACHE] Force refresh requested - clearing all caches');
        
        // Clear localStorage cache if any
        const cacheKeys = Object.keys(localStorage).filter(key => 
          key.includes('meal_plan') || key.includes('mealPlan') || key.includes('history')
        );
        cacheKeys.forEach(key => {
          localStorage.removeItem(key);
          console.log(`[CACHE] Cleared localStorage key: ${key}`);
        });
        
        // Clear sessionStorage cache if any
        const sessionKeys = Object.keys(sessionStorage).filter(key => 
          key.includes('meal_plan') || key.includes('mealPlan') || key.includes('history')
        );
        sessionKeys.forEach(key => {
          sessionStorage.removeItem(key);
          console.log(`[CACHE] Cleared sessionStorage key: ${key}`);
        });
      }

      const data = await mealPlanApi.getHistory() as { meal_plans: MealPlanData[] };
      console.log('Fetched meal plans from backend:', data);
      
      // Use all meal plans directly from backend (no localStorage filtering)
      const allPlans = data.meal_plans || [];
      console.log('All plans from backend:', allPlans.map((p: MealPlanData) => ({ id: p.id, created_at: p.created_at })));
      
      // ADDITIONAL FILTERING: Remove any plans that might have is_deleted flag
      const activePlans = allPlans.filter((plan: any) => !plan.is_deleted);
      console.log(`Filtered out ${allPlans.length - activePlans.length} deleted plans`);
      
      // Sort plans by creation date (newest first)
      const sortedPlans = activePlans.sort((a: MealPlanData, b: MealPlanData) => {
        const dateA = new Date(a.created_at || '');
        const dateB = new Date(b.created_at || '');
        return dateB.getTime() - dateA.getTime();
      });

      setMealPlans(sortedPlans);
      setFilteredPlans(sortedPlans);
      console.log(`Loaded ${sortedPlans.length} meal plans successfully`);
      
    } catch (error) {
      console.error('Error fetching meal plans:', error);
      setError('Failed to load meal plans. Please try again.');
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

    // Set loading state
    setLoading(true);

    try {
      // Perform actual backend deletion FIRST
      console.log('Performing backend deletion...');
      const result = await mealPlanApi.delete(selectedIds);
      console.log('Backend deletion successful:', result);

      // ROBUST DELETION: Force refresh from backend instead of local filtering
      // This ensures deleted items don't reappear from caches
      console.log('ROBUST DELETION: Force refreshing from backend after deletion...');
      await fetchMealPlans(true); // Force refresh with cache clearing
      
      setSelectedMealPlans([]);

      // Show success message
      setSnackbarMessage(`${selectedIds.length} meal plan(s) deleted successfully!`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      console.log('ROBUST DELETION: Force refresh completed after successful deletion');

    } catch (error) {
      console.error('Failed to delete selected meal plans:', error);
      
      // Show error message
      setSnackbarMessage('Failed to delete selected meal plans. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
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

    // Set loading state
    setLoading(true);
    const totalCount = mealPlans.length;

    try {
      // Perform actual backend deletion FIRST
      console.log('Performing backend clear all...');
      const result = await mealPlanApi.deleteAll();
      console.log('Backend clear all successful:', result);

      // ROBUST DELETION: Force refresh from backend instead of local clearing
      // This ensures deleted items don't reappear from caches
      console.log('ROBUST DELETION: Force refreshing from backend after clear all...');
      await fetchMealPlans(true); // Force refresh with cache clearing
      
      setSelectedMealPlans([]);
      setSearchQuery('');

      // Show success message
      setSnackbarMessage(`All ${totalCount} meal plans deleted successfully!`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      console.log('ROBUST DELETION: Force refresh completed after clear all');

    } catch (error) {
      console.error('Failed to clear all meal plans:', error);
      
      // Show error message
      setSnackbarMessage('Failed to delete all meal plans. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
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

  const handleDownloadPDF = async (filename: string) => {
    try {
      const headers = getAuthHeaders();
      if (!headers) {
        navigate('/login');
        return;
      }

      const response = await fetch(`${config.API_URL}/download-saved-pdf/${filename}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        if (handleAuthError(response, navigate)) {
          return;
        }
        throw new Error('Failed to download PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSnackbarMessage('PDF downloaded successfully!');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      setSnackbarMessage('Failed to download PDF. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  const handleGeneratePDF = async (mealPlanId: string) => {
    try {
      const headers = getAuthHeaders();
      if (!headers) {
        navigate('/login');
        return;
      }

      setSnackbarMessage('Generating PDF...');
      setSnackbarSeverity('info');
      setSnackbarOpen(true);

      const response = await fetch(`${config.API_URL}/generate-pdf/${mealPlanId}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        if (handleAuthError(response, navigate)) {
          return;
        }
        throw new Error('Failed to generate PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Extract filename from content-disposition header or create default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'meal_plan.pdf';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSnackbarMessage('PDF downloaded successfully!');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Error generating PDF:', error);
      setSnackbarMessage('Failed to generate PDF. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

   const handleCloseSnackbar = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  if (loading && filteredPlans.length === 0) {
    return (
      <Box sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2
      }}>
        <Fade in={true} timeout={1000}>
          <Paper elevation={0} sx={{
            p: 4,
            borderRadius: '24px',
            background: 'rgba(255, 255, 255, 0.25)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            textAlign: 'center',
            maxWidth: 400,
            animation: `${pulse} 2s ease-in-out infinite`,
          }}>
            <CircularProgress 
              size={80} 
              sx={{ 
                mb: 3,
                color: 'white',
                animation: `${float} 3s ease-in-out infinite`
              }} 
            />
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'white',
                fontWeight: 600,
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                mb: 1
              }}
            >
              📚 Loading Meal Plan History
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.8)',
                textShadow: '0 1px 3px rgba(0,0,0,0.2)'
              }}
            >
              Fetching your saved meal plans...
            </Typography>
          </Paper>
        </Fade>
      </Box>
    );
  }

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: { xs: 1, sm: 2 },
      px: { xs: 1, sm: 2 },
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
        animation: `${gradientShift} 8s ease infinite`,
        backgroundSize: '400% 400%',
        zIndex: 0,
      }
    }}>
      <Container maxWidth="sm" sx={{ 
        position: 'relative',
        zIndex: 1,
        py: 2
      }}>
        <Fade in={true} timeout={1000}>
          <Paper elevation={0} sx={{ 
            p: { xs: 2, sm: 3 },
            mb: 3,
            borderRadius: '24px',
            background: 'rgba(255, 255, 255, 0.25)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            animation: `${fadeInScale} 0.8s ease-out`,
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
              borderRadius: '24px',
              animation: `${shimmer} 3s ease-in-out infinite`,
              backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
              backgroundSize: '200px 100%',
              backgroundRepeat: 'no-repeat',
            }
          }}>
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              <Slide direction="down" in={true} timeout={800}>
                <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ 
                  mb: 4,
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: { xs: '1.75rem', sm: '2.125rem' },
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  animation: `${bounceIn} 1s ease-out 0.3s both`
                }}>
                  📚 Meal Plan History
                </Typography>
              </Slide>
            </Box>
          </Paper>
        </Fade>

        {error && (
          <Fade in={true} timeout={600}>
            <Alert 
              severity="error" 
              sx={{ 
                mb: 3,
                borderRadius: '16px',
                background: 'rgba(244, 67, 54, 0.1)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(244, 67, 54, 0.3)',
                color: 'white',
                '& .MuiAlert-icon': {
                  color: 'white'
                }
              }}
            >
              {error}
            </Alert>
          </Fade>
        )}

        {filteredPlans.length > 0 && (
          <Slide direction="up" in={true} timeout={1200}>
            <Paper elevation={0} sx={{ 
              p: { xs: 2, sm: 3 },
              mb: 3,
              borderRadius: '20px',
              background: 'rgba(255, 255, 255, 0.15)',
              backdropFilter: 'blur(15px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 6px 24px rgba(0, 0, 0, 0.1)',
              animation: `${slideInUp} 0.8s ease-out 0.3s both`,
            }}>
              <Box sx={{ 
                display: 'flex', 
                flexDirection: { xs: 'column', md: 'row' },
                justifyContent: { xs: 'center', md: 'space-between' }, 
                alignItems: { xs: 'stretch', md: 'center' }, 
                gap: 2
              }}>
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: 1, 
                  alignItems: { xs: 'center', sm: 'flex-start' }
                }}>
                    <Zoom in={true} timeout={600} style={{ transitionDelay: '0.5s' }}>
                      <Button
                        variant="contained"
                        size="small"
                        onClick={handleSelectAll}
                        disabled={loading}
                        sx={{ 
                          minWidth: { xs: '140px', sm: 'auto' },
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
                          background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                          color: 'white',
                          borderRadius: '50px',
                          px: 3,
                          py: 1,
                          fontWeight: 600,
                          textTransform: 'none',
                          boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)',
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          '&:hover': {
                            background: 'linear-gradient(135deg, #45a049 0%, #3d8b40 100%)',
                            transform: 'translateY(-2px)',
                            boxShadow: '0 6px 16px rgba(76, 175, 80, 0.4)',
                          },
                          '&:disabled': {
                            background: 'rgba(255, 255, 255, 0.2)',
                            color: 'rgba(255, 255, 255, 0.5)',
                          },
                          transition: 'all 0.3s ease',
                        }}
                      >
                        {filteredPlans.every(plan => selectedMealPlans.includes(plan.id || '')) 
                            ? '✓ Deselect All' 
                            : '☐ Select All'
                        }
                      </Button>
                    </Zoom>
                    <Typography variant="body2" sx={{ 
                      alignSelf: 'center', 
                      color: 'rgba(255, 255, 255, 0.8)',
                      textAlign: { xs: 'center', sm: 'left' },
                      fontSize: { xs: '0.75rem', sm: '0.875rem' },
                      fontWeight: 500,
                      textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                    }}>
                        📊 {selectedMealPlans.length} of {filteredPlans.length} selected
                    </Typography>
                </Box>
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: 2, 
                  alignItems: 'center',
                  justifyContent: { xs: 'center', sm: 'flex-end' }
                }}>
                     <Tooltip title="If a plan can't be deleted, it may have already been removed or is corrupted. The list will refresh automatically.">
                       <span>
                         <Zoom in={true} timeout={600} style={{ transitionDelay: '0.7s' }}>
                           <Button
                             variant="contained"
                             startIcon={<DeleteIcon />}
                             onClick={handleDeleteSelected}
                             disabled={selectedMealPlans.length === 0 || loading}
                             sx={{ 
                               minWidth: { xs: '160px', sm: 'auto' },
                               fontSize: { xs: '0.75rem', sm: '0.875rem' },
                               background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                               color: 'white',
                               borderRadius: '50px',
                               px: 3,
                               py: 1,
                               fontWeight: 600,
                               textTransform: 'none',
                               boxShadow: '0 4px 12px rgba(244, 67, 54, 0.3)',
                               border: '1px solid rgba(255, 255, 255, 0.2)',
                               '&:hover': {
                                 background: 'linear-gradient(135deg, #d32f2f 0%, #c62828 100%)',
                                 transform: 'translateY(-2px)',
                                 boxShadow: '0 6px 16px rgba(244, 67, 54, 0.4)',
                               },
                               '&:disabled': {
                                 background: 'rgba(255, 255, 255, 0.2)',
                                 color: 'rgba(255, 255, 255, 0.5)',
                               },
                               transition: 'all 0.3s ease',
                             }}
                           >
                             🗑️ Delete Selected ({selectedMealPlans.length})
                           </Button>
                         </Zoom>
                       </span>
                     </Tooltip>
                     <Zoom in={true} timeout={600} style={{ transitionDelay: '0.9s' }}>
                       <Button
                         variant="contained"
                         onClick={handleClearAll}
                         disabled={loading}
                         sx={{ 
                           minWidth: { xs: '120px', sm: 'auto' },
                           fontSize: { xs: '0.75rem', sm: '0.875rem' },
                           background: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
                           color: 'white',
                           borderRadius: '50px',
                           px: 3,
                           py: 1,
                           fontWeight: 600,
                           textTransform: 'none',
                           boxShadow: '0 4px 12px rgba(255, 152, 0, 0.3)',
                           border: '1px solid rgba(255, 255, 255, 0.2)',
                           '&:hover': {
                             background: 'linear-gradient(135deg, #f57c00 0%, #ef6c00 100%)',
                             transform: 'translateY(-2px)',
                             boxShadow: '0 6px 16px rgba(255, 152, 0, 0.4)',
                           },
                           '&:disabled': {
                             background: 'rgba(255, 255, 255, 0.2)',
                             color: 'rgba(255, 255, 255, 0.5)',
                           },
                           transition: 'all 0.3s ease',
                         }}
                       >
                         🧹 Clear All
                       </Button>
                     </Zoom>
                </Box>
              </Box>
            </Paper>
          </Slide>
        )}

        <Slide direction="up" in={true} timeout={1400}>
          <Box sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="🔍 Search by ID, date, calories, or macronutrients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              sx={{
                '& .MuiOutlinedInput-root': {
                  background: 'rgba(255, 255, 255, 0.15)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '50px',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  color: 'white',
                  fontSize: '0.9rem',
                  '& fieldset': {
                    border: 'none',
                  },
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.2)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 12px rgba(102, 126, 234, 0.2)',
                  },
                  '&.Mui-focused': {
                    background: 'rgba(255, 255, 255, 0.25)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 6px 16px rgba(102, 126, 234, 0.3)',
                    animation: `${glow} 2s ease-in-out infinite`,
                  },
                  transition: 'all 0.3s ease',
                },
                '& .MuiInputBase-input': {
                  color: 'white',
                  '&::placeholder': {
                    color: 'rgba(255, 255, 255, 0.7)',
                    opacity: 1,
                  },
                },
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: 'rgba(255, 255, 255, 0.7)' }} />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </Slide>

        {filteredPlans.length === 0 ? (
          <Fade in={true} timeout={1000}>
            <Paper elevation={0} sx={{
              p: 6,
              borderRadius: '24px',
              background: 'rgba(255, 255, 255, 0.15)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              textAlign: 'center',
              animation: `${fadeInScale} 0.8s ease-out`,
            }}>
              <Typography variant="h5" gutterBottom sx={{ 
                color: 'white',
                fontWeight: 600,
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                mb: 2
              }}>
                {searchQuery ? '🔍 No matching meal plans found' : '📋 No meal plans found'}
              </Typography>
              <Typography variant="body1" sx={{ 
                color: 'rgba(255, 255, 255, 0.8)',
                textShadow: '0 1px 3px rgba(0,0,0,0.2)',
                mb: 4
              }}>
                {searchQuery ? 'Try adjusting your search terms' : 'Start by creating your first personalized meal plan'}
              </Typography>
              <Zoom in={true} timeout={800} style={{ transitionDelay: '0.5s' }}>
                <Button
                  variant="contained"
                  onClick={() => navigate('/meal-plan')}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    borderRadius: '50px',
                    px: 4,
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600,
                    textTransform: 'none',
                    boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                      transform: 'translateY(-3px) scale(1.05)',
                      boxShadow: '0 8px 25px rgba(102, 126, 234, 0.5)',
                      animation: `${glow} 1.5s ease-in-out infinite`,
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  ✨ Create New Meal Plan
                </Button>
              </Zoom>
            </Paper>
          </Fade>
        ) : (
          <Grid container spacing={3}>
            {filteredPlans.map((plan, index) => (
              <Grid item xs={12} sm={6} key={plan.id}>
                <Zoom 
                  in={true} 
                  timeout={600} 
                  style={{ transitionDelay: `${index * 100}ms` }}
                >
                  <Card 
                    sx={{ 
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: '20px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(20px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                      transition: 'all 0.3s ease',
                      position: 'relative',
                      overflow: 'hidden',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
                        borderRadius: '20px',
                        animation: `${shimmer} 4s ease-in-out infinite`,
                        backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)',
                        backgroundSize: '200px 100%',
                        backgroundRepeat: 'no-repeat',
                      },
                      '&:hover': {
                        transform: 'translateY(-8px) scale(1.02)',
                        boxShadow: '0 12px 40px rgba(102, 126, 234, 0.2)',
                        background: 'rgba(255, 255, 255, 0.15)',
                        animation: `${glow} 2s ease-in-out infinite`,
                      },
                    }}
                  >
                    <CardContent sx={{ position: 'relative', zIndex: 1, p: 3 }}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={selectedMealPlans.includes(plan.id || '')}
                            onChange={() => handleSelectPlan(plan.id || '')}
                            disabled={!plan.id}
                            sx={{
                              color: 'rgba(255, 255, 255, 0.7)',
                              '&.Mui-checked': {
                                color: '#4CAF50',
                              },
                            }}
                          />
                        }
                        label={
                          <Typography variant="h6" gutterBottom sx={{
                            color: 'white',
                            fontWeight: 600,
                            textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                          }}>
                            📋 Meal Plan {formatMealPlanId(plan.id || '')}
                          </Typography>
                        }
                        sx={{ mb: 2, alignItems: 'flex-start' }}
                      />
                   
                      <Typography variant="body2" gutterBottom sx={{
                        color: 'rgba(255, 255, 255, 0.8)',
                        textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                        mb: 2
                      }}>
                        📅 Created {formatDate(plan.created_at || '')}
                      </Typography>
                    
                      <Box mt={2}>
                        <Chip 
                          label={`🔥 ${plan.dailyCalories || 'N/A'} kcal`}
                          sx={{ 
                            mb: 2,
                            background: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
                            color: 'white',
                            fontWeight: 600,
                            border: '1px solid rgba(255, 255, 255, 0.3)',
                            boxShadow: '0 2px 8px rgba(255, 152, 0, 0.3)',
                          }}
                        />
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            display: 'block', 
                            mb: 1, 
                            fontWeight: 600,
                            color: 'rgba(255, 255, 255, 0.9)',
                            textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                            fontSize: '0.8rem'
                          }}
                        >
                          📊 Daily Macro Targets
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          <Chip
                            label={`💪 ${plan.macronutrients?.protein ?? 'N/A'}g`}
                            size="small"
                            sx={{
                              background: 'rgba(76, 175, 80, 0.2)',
                              color: 'rgba(255, 255, 255, 0.9)',
                              border: '1px solid rgba(76, 175, 80, 0.3)',
                              fontWeight: 500,
                            }}
                          />
                          <Chip
                            label={`🌾 ${plan.macronutrients?.carbs ?? 'N/A'}g`}
                            size="small"
                            sx={{
                              background: 'rgba(33, 150, 243, 0.2)',
                              color: 'rgba(255, 255, 255, 0.9)',
                              border: '1px solid rgba(33, 150, 243, 0.3)',
                              fontWeight: 500,
                            }}
                          />
                          <Chip
                            label={`🥑 ${plan.macronutrients?.fats ?? 'N/A'}g`}
                            size="small"
                            sx={{
                              background: 'rgba(156, 39, 176, 0.2)',
                              color: 'rgba(255, 255, 255, 0.9)',
                              border: '1px solid rgba(156, 39, 176, 0.3)',
                              fontWeight: 500,
                            }}
                          />
                        </Stack>
                      </Box>

                    <Box 
                      mt={2} 
                      sx={{
                        display: 'flex', 
                        flexDirection: { xs: 'column', sm: 'row' },
                        justifyContent: { xs: 'center', sm: 'space-between' }, 
                        alignItems: 'center',
                        gap: 1
                      }}
                    >
                        {/* Show PDF button for all meal plans */}
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => {
                            if (plan.consolidated_pdf?.filename) {
                              // Download existing PDF
                              handleDownloadPDF(plan.consolidated_pdf.filename);
                            } else {
                              // Generate PDF on-demand
                              handleGeneratePDF(plan.id || '');
                            }
                          }}
                          disabled={!plan.id}
                          sx={{ 
                            minWidth: { xs: '120px', sm: 'auto' },
                            width: { xs: '100%', sm: 'auto' },
                            maxWidth: { xs: '200px', sm: 'none' },
                            fontSize: { xs: '0.75rem', sm: '0.875rem' },
                            background: 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
                            color: 'white',
                            borderRadius: '50px',
                            px: 2,
                            py: 0.5,
                            fontWeight: 600,
                            textTransform: 'none',
                            boxShadow: '0 3px 10px rgba(33, 150, 243, 0.3)',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            '&:hover': {
                              background: 'linear-gradient(135deg, #1976D2 0%, #1565C0 100%)',
                              transform: 'translateY(-1px)',
                              boxShadow: '0 4px 12px rgba(33, 150, 243, 0.4)',
                            },
                            '&:disabled': {
                              background: 'rgba(255, 255, 255, 0.2)',
                              color: 'rgba(255, 255, 255, 0.5)',
                            },
                            transition: 'all 0.3s ease',
                          }}
                        >
                          📄 Download PDF
                        </Button>
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => navigate(`/meal-plan/${plan.id || ''}`)}
                          disabled={!plan.id}
                          sx={{ 
                            minWidth: { xs: '120px', sm: 'auto' },
                            width: { xs: '100%', sm: 'auto' },
                            maxWidth: { xs: '200px', sm: 'none' },
                            fontSize: { xs: '0.75rem', sm: '0.875rem' },
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            borderRadius: '50px',
                            px: 2,
                            py: 0.5,
                            fontWeight: 600,
                            textTransform: 'none',
                            boxShadow: '0 3px 10px rgba(102, 126, 234, 0.3)',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            '&:hover': {
                              background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                              transform: 'translateY(-1px)',
                              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                            },
                            '&:disabled': {
                              background: 'rgba(255, 255, 255, 0.2)',
                              color: 'rgba(255, 255, 255, 0.5)',
                            },
                            transition: 'all 0.3s ease',
                          }}
                        >
                          👁️ View Details
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Zoom>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
      
      {/* Snackbar and Loading Overlay */}
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
    </Box>
  );
};

export default MealPlanHistory; 