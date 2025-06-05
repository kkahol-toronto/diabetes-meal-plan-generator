import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import HomePage from './components/HomePage';
import MealPlanRequest from './components/MealPlanRequest';
import MealPlanHistory from './components/MealPlanHistory';
import MealPlanDetails from './components/MealPlanDetails';
import Login from './components/Login';
import Register from './components/Register';
import Chat from './components/Chat';
import AdminLogin from './components/AdminLogin';
import AdminPanel from './components/AdminPanel';
import Navigation from './components/Navigation';
import ConsumptionHistory from './components/ConsumptionHistory';
import ErrorBoundary from './components/ErrorBoundary';
import NotFound from './components/NotFound';
import { AppProvider } from './contexts/AppContext';

// Create a theme instance with enhanced accessibility and design
const theme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32', // Diabetes-friendly green
      light: '#4CAF50',
      dark: '#1B5E20',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#81C784', // Lighter green
      light: '#A5D6A7',
      dark: '#558B2F',
      contrastText: '#000000',
    },
    background: {
      default: '#F8F9FA',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
    },
    error: {
      main: '#F44336',
      light: '#EF5350',
      dark: '#C62828',
    },
    warning: {
      main: '#FF9800',
      light: '#FFB74D',
      dark: '#F57C00',
    },
    info: {
      main: '#2196F3',
      light: '#42A5F5',
      dark: '#1976D2',
    },
    success: {
      main: '#4CAF50',
      light: '#66BB6A',
      dark: '#388E3C',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
    },
    h2: {
      fontWeight: 700,
      fontSize: '2rem',
      lineHeight: 1.3,
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
      lineHeight: 1.3,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.4,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.125rem',
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
      fontSize: '0.875rem',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0,0,0,0.08)',
    '0px 4px 8px rgba(0,0,0,0.12)',
    '0px 8px 16px rgba(0,0,0,0.16)',
    '0px 12px 24px rgba(0,0,0,0.20)',
    '0px 16px 32px rgba(0,0,0,0.24)',
    ...Array(19).fill('0px 16px 32px rgba(0,0,0,0.24)'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '12px 24px',
          fontWeight: 600,
          textTransform: 'none',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0px 4px 12px rgba(0,0,0,0.15)',
          },
        },
        contained: {
          boxShadow: '0px 2px 8px rgba(0,0,0,0.15)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          border: '1px solid rgba(0,0,0,0.08)',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0px 8px 24px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
          },
        },
      },
    },
  },
});

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" />;
  }
  return <>{children}</>;
};

// Admin Route component
const AdminRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const isAdmin = localStorage.getItem('isAdmin') === 'true';
  if (!token || !isAdmin) {
    return <Navigate to="/admin/login" />;
  }
  return <>{children}</>;
};

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppProvider>
          <Router>
            <Navigation />
            <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route
            path="/doctor-admin-page"
            element={
              <AdminRoute>
                <AdminPanel />
              </AdminRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPanel />
              </AdminRoute>
            }
          />
          <Route
            path="/meal-plan/history"
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
            path="/consumption-history"
            element={
              <ProtectedRoute>
                <ConsumptionHistory />
              </ProtectedRoute>
            }
          />
          {/* Catch-all route for 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
          </Router>
        </AppProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App; 