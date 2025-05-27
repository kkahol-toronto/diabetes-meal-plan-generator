import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
} from '@mui/material';

const ThankYou: React.FC = () => {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h3" component="h1" gutterBottom>
            Thank You!
          </Typography>
          <Typography variant="h5" color="text.secondary" sx={{ mt: 2 }}>
            Happy Shopping! Enjoy your healthy meals! 🛍️ 🥗
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default ThankYou; 