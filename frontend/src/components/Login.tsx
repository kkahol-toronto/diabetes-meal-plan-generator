import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Link,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('username', formData.username);
      formDataToSend.append('password', formData.password);

      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formDataToSend,
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Login successful, storing token...');
        localStorage.setItem('token', data.access_token);
        console.log('Token stored:', data.access_token.substring(0, 50) + '...');
        
        // Check if the token contains admin status
        try {
          const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
          console.log('Token payload:', tokenPayload);
          if (tokenPayload.is_admin) {
            localStorage.setItem('isAdmin', 'true');
            console.log('Admin status set');
          }
        } catch (error) {
          console.error('Error parsing token:', error);
        }
        
        console.log('Navigating to home page...');
        navigate('/');
        // Remove the reload to avoid clearing state
        // window.location.reload();
      } else {
        const errorData = await response.json();
        // Handle FastAPI validation errors
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `${err.loc[1]}: ${err.msg}`).join(', ');
          setError(errorMessages);
        } else {
          setError(errorData.detail || 'Invalid credentials');
        }
      }
    } catch (err) {
      setError('An error occurred during login');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Login
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            margin="normal"
            required
          />
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/register')}
            >
              Don't have an account? Register
            </Link>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
            >
              Login
            </Button>
          </Box>
        </form>
      </Paper>
    </Container>
  );
};

export default Login; 