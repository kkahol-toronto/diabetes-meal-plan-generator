import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Grid,
  useTheme,
} from '@mui/material';
import {
  Home as HomeIcon,
  ArrowBack as BackIcon,
  SearchOff as NotFoundIcon,
} from '@mui/icons-material';

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 6, 
          textAlign: 'center',
          borderRadius: 4,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        }}
      >
        <Box sx={{ mb: 4 }}>
          <NotFoundIcon 
            sx={{ 
              fontSize: 120, 
              color: theme.palette.primary.main,
              opacity: 0.7,
              mb: 2,
            }} 
          />
          
          <Typography 
            variant="h1" 
            component="h1" 
            sx={{
              fontSize: '6rem',
              fontWeight: 800,
              color: theme.palette.primary.main,
              textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
              mb: 2,
            }}
          >
            404
          </Typography>
          
          <Typography 
            variant="h4" 
            component="h2" 
            gutterBottom
            sx={{
              fontWeight: 600,
              color: theme.palette.text.primary,
              mb: 2,
            }}
          >
            Page Not Found
          </Typography>
          
          <Typography 
            variant="body1" 
            color="text.secondary"
            sx={{
              fontSize: '1.1rem',
              maxWidth: 500,
              mx: 'auto',
              mb: 4,
            }}
          >
            Oops! The page you're looking for doesn't exist. It might have been moved, 
            deleted, or you entered the wrong URL.
          </Typography>
        </Box>

        <Grid container spacing={2} justifyContent="center">
          <Grid item>
            <Button
              variant="contained"
              size="large"
              startIcon={<HomeIcon />}
              onClick={handleGoHome}
              sx={{
                px: 4,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
                borderRadius: 3,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.2)',
                },
              }}
            >
              Go Home
            </Button>
          </Grid>
          <Grid item>
            <Button
              variant="outlined"
              size="large"
              startIcon={<BackIcon />}
              onClick={handleGoBack}
              sx={{
                px: 4,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
                borderRadius: 3,
                borderWidth: 2,
                '&:hover': {
                  borderWidth: 2,
                  transform: 'translateY(-2px)',
                },
              }}
            >
              Go Back
            </Button>
          </Grid>
        </Grid>

        <Box sx={{ mt: 6 }}>
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ fontSize: '0.9rem' }}
          >
            If you believe this is an error, please contact our support team.
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default NotFound; 