import React, { ReactNode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import HomePage from './components/HomePage';
import MealPlanRequest from './components/MealPlanRequest';
import Login from './components/Login';
import Register from './components/Register';
import Chat from './components/Chat';
import AdminLogin from './components/AdminLogin';
import AdminPanel from './components/AdminPanel';
import Navigation from './components/Navigation';
import ThankYou from './components/ThankYou';
import AllRecipesPage from './pages/AllRecipesPage';
import AllShoppingListsPage from './pages/AllShoppingListsPage';
import MealPlanHistory from './components/MealPlanHistory';
import ConsumptionHistory from './components/ConsumptionHistory';
import UserProfileForm from './components/UserProfileForm/index';

// Create a theme instance
const theme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32', // Diabetes-friendly green
    },
    secondary: {
      main: '#81C784', // Lighter green
    },
    background: {
      default: '#F5F5F5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
  },
});

interface ProtectedRouteProps {
  children: ReactNode;
}

// Protected Route component
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" />;
  }
  return <>{children}</>;
};

// Admin Route component
const AdminRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const token = localStorage.getItem('token');
  const isAdmin = localStorage.getItem('isAdmin') === 'true';
  if (!token || !isAdmin) {
    return <Navigate to="/admin/login" />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Navigation />
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

        {/* Admin Protected Route */}
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminPanel />
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
          path="/profile"
          element={
            <ProtectedRoute>
              <UserProfileForm onSubmit={async (profile) => {
                // Handle profile submission
                try {
                  const response = await fetch('http://localhost:8000/user/profile', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    },
                    body: JSON.stringify(profile),
                  });
                  if (!response.ok) {
                    throw new Error('Failed to save profile');
                  }
                } catch (error) {
                  console.error('Error saving profile:', error);
                  throw error;
                }
              }} />
            </ProtectedRoute>
          }
        />
        
        <Route 
          path="*" 
          element={
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              404 - Page Not Found or Route Not Matched
            </div>
          } 
        />
      </Routes>
    </ThemeProvider>
  );
};

export default App; 