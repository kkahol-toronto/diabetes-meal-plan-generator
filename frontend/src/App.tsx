import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Box } from '@mui/material';
import { AppProvider } from './contexts/AppContext';
import HomePage from './components/HomePage';
import MealPlanRequest from './components/MealPlanRequest';
import Login from './components/Login';
import Register from './components/Register';
import Chat from './components/Chat';
import AdminLogin from './components/AdminLogin';
import AdminPanel from './components/AdminPanel';
import AdminPatientProfile from './components/AdminPatientProfile';
import Navigation from './components/Navigation';
import ThankYou from './components/ThankYou';
import AllRecipesPage from './pages/AllRecipesPage';
import AllShoppingListsPage from './pages/AllShoppingListsPage';
import MealPlanHistory from './components/MealPlanHistory';
import MealPlanDetails from './components/MealPlanDetails';
import Settings from './components/Settings';

import ConsumptionHistory from './components/ConsumptionHistory';
import NotificationSystem from './components/NotificationSystem';
import ComplianceFooter from './components/ComplianceFooter';

// Create a theme instance with purple gradient theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#667eea', // Purple primary color
      light: '#9bb5ff',
      dark: '#3f51b5',
    },
    secondary: {
      main: '#764ba2', // Purple secondary color
      light: '#a478d4',
      dark: '#4a2c73',
    },
    background: {
      default: '#f8f9ff', // Light purple-tinted background
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#667eea',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      background: 'linear-gradient(45deg, #667eea, #764ba2)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        contained: {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
          '&:hover': {
            background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
            boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 20px rgba(102, 126, 234, 0.1)',
          borderRadius: 12,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        elevation1: {
          boxShadow: '0 2px 10px rgba(102, 126, 234, 0.1)',
        },
        elevation2: {
          boxShadow: '0 4px 15px rgba(102, 126, 234, 0.15)',
        },
        elevation3: {
          boxShadow: '0 6px 20px rgba(102, 126, 234, 0.2)',
        },
      },
    },
  },
});

// Protected Route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" />;
  }
  return <>{children}</>;
};

// Admin Route component
const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  const isAdmin = localStorage.getItem('isAdmin') === 'true';
  if (!token || !isAdmin) {
    return <Navigate to="/admin/login" />;
  }
  return <>{children}</>;
};

function App() {
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');
  
  return (
    <AppProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            minHeight: '100vh',
          }}
        >
          <Navigation />
          {token && userId && <NotificationSystem userId={userId} />}
          <Box component="main" sx={{ flex: 1 }}>
            <Routes>
          {/* Moved Consumption History Route Up & Restored ProtectedRoute */}
          <Route
            path="/consumption-history"
            element={
              <ProtectedRoute>
                <ConsumptionHistory />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/thank-you" element={<ThankYou />} />

          {/* Admin Protected Routes */}
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPanel />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/patient/:registrationCode"
            element={
              <AdminRoute>
                <AdminPatientProfile />
              </AdminRoute>
            }
          />
          
          {/* Other User Protected Routes */}
          <Route
            path="/meal-plan"
            element={
              <ProtectedRoute>
                <MealPlanRequest />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <Chat />
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-recipes"
            element={
              <ProtectedRoute>
                <AllRecipesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-shopping-lists"
            element={
              <ProtectedRoute>
                <AllShoppingListsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/meal_plans"
            element={
              <ProtectedRoute>
                <MealPlanHistory />
              </ProtectedRoute>
            }
          />
          <Route
            path="/meal-plan/:id"
            element={
              <ProtectedRoute>
                <MealPlanDetails />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />

          
          <Route path="*" element={<div>404 - Page Not Found or Route Not Matched</div>} />
        </Routes>
          </Box>
          <ComplianceFooter />
        </Box>
      </ThemeProvider>
    </AppProvider>
  );
}

export default App; 