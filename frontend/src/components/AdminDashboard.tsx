import React from 'react';
import { Container, Paper, Typography } from '@mui/material';

const AdminDashboard: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome to the Admin Dashboard
        </Typography>
        <Typography variant="body1">
          Use the panel to manage patients and view user profiles.
        </Typography>
      </Paper>
    </Container>
  );
};

export default AdminDashboard; 