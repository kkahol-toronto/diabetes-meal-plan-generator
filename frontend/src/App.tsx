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
import AdminUserProfile from './components/AdminUserProfile';
import AdminDashboard from './components/AdminDashboard';
// Debug imports - can remove these later
import RouteDebugger from './components/RouteDebugger';
import AdminAuthDebugger from './components/AdminAuthDebugger';
import TempAdminUserProfile from './components/TempAdminUserProfile';
import SimpleAdminProfile from './components/SimpleAdminProfile';
import Navigation from './components/Navigation';
import ThankYou from './components/ThankYou';
import AllRecipesPage from './pages/AllRecipesPage';
import AllShoppingListsPage from './pages/AllShoppingListsPage';
import MealPlanHistory from './components/MealPlanHistory';

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
    return <Navigate to="/admin/login" replace />;
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
          <Route path="/emergency/:userId" element={<div style={{padding: '20px'}}><h1>🚨 EMERGENCY ROUTE WORKS!</h1><p>UserId: {window.location.pathname.split('/')[2]}</p></div>} />
          
          {/* Admin Protected Routes - Nested */}
          <Route path="/admin" element={<AdminRoute><AdminPanel /></AdminRoute>}>
            <Route index element={<AdminDashboard />} />
            <Route path="users/:userId" element={<AdminUserProfile />} />
          </Route>
          
          <Route path="/debug/:userId" element={<RouteDebugger />} />
          <Route path="/auth-debug" element={<AdminAuthDebugger />} />
          <Route path="/temp-admin/:userId" element={<TempAdminUserProfile />} />
          <Route path="/simple/:userId" element={<SimpleAdminProfile />} />
          
          {/* User Protected Routes */}
          <Route path="/meal-plan" element={<ProtectedRoute><MealPlanRequest /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path="/my-recipes" element={<ProtectedRoute><AllRecipesPage /></ProtectedRoute>} />
          <Route path="/my-shopping-lists" element={<ProtectedRoute><AllShoppingListsPage /></ProtectedRoute>} />
          <Route path="/meal_plans" element={<ProtectedRoute><MealPlanHistory /></ProtectedRoute>} />
          
          {/* Catch-all route */}
          <Route path="*" element={<div>404 - Page Not Found</div>} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App; 