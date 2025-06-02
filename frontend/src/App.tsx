import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
<<<<<<< HEAD
import AllRecipesPage from './pages/AllRecipesPage';
import AllShoppingListsPage from './pages/AllShoppingListsPage';
=======
import MealPlanHistory from './components/MealPlanHistory';
>>>>>>> origin/changed_ui_backend_ram

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
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navigation />
        <Routes>
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
          
          {/* User Protected Routes */}
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
<<<<<<< HEAD
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
=======
            path="/meal_plans"
            element={
              <ProtectedRoute>
                <MealPlanHistory />
              </ProtectedRoute>
            }
          />

          {/* Catch-all route for debugging - Renders a simple message if no other route matches */}
          <Route path="*" element={<div>404 - Page Not Found or Route Not Matched</div>} />
>>>>>>> origin/changed_ui_backend_ram
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App; 