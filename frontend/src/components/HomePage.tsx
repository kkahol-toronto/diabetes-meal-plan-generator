import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
} from '@mui/material';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center" color="primary">
          Welcome to Diabetes Diet Manager
        </Typography>
        
        <Typography variant="h6" gutterBottom align="center" color="text.secondary" sx={{ mb: 4 }}>
          Your Personal Guide to Healthy Living with Diabetes
        </Typography>

        <Box sx={{ mb: 4 }}>
          <Typography variant="body1" paragraph>
            Managing diabetes through proper nutrition is crucial for maintaining good health. Our app is designed to help you make informed food choices and maintain a balanced diet that works for you.
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 3, color: 'primary.main' }}>
            Key Features:
          </Typography>

          <Box component="ul" sx={{ pl: 2 }}>
            <Typography component="li" variant="body1" paragraph>
              <strong>Personalized Meal Planning:</strong> Get customized meal plans based on your dietary preferences, health goals, and diabetes management needs.
            </Typography>
            <Typography component="li" variant="body1" paragraph>
              <strong>Smart Recipe Suggestions:</strong> Access a variety of diabetes-friendly recipes that are both nutritious and delicious.
            </Typography>
            <Typography component="li" variant="body1" paragraph>
              <strong>Automated Shopping Lists:</strong> Generate organized shopping lists based on your meal plan, making grocery shopping easier and more efficient.
            </Typography>
            <Typography component="li" variant="body1" paragraph>
              <strong>AI-Powered Chat Assistant:</strong> Get instant answers to your nutrition questions and personalized advice for managing your diabetes through diet.
            </Typography>
          </Box>

          <Typography variant="body1" paragraph sx={{ mt: 3 }}>
            Start your journey to better health by creating your personalized meal plan or chatting with our AI assistant about your dietary needs.
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={() => navigate('/meal-plan')}
            sx={{ minWidth: 200 }}
          >
            Create Meal Plan
          </Button>
          <Button
            variant="outlined"
            color="primary"
            size="large"
            onClick={() => navigate('/chat')}
            sx={{ minWidth: 200 }}
          >
            Chat with Assistant
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default HomePage; 