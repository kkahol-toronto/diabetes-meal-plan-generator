import React from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { Container, Paper, Typography, Box, Alert } from '@mui/material';

const RouteDebugger: React.FC = () => {
  const location = useLocation();
  const params = useParams();
  
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          🐛 Route Debugger
        </Typography>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          This component helps debug routing issues
        </Alert>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">Current Location:</Typography>
          <Typography variant="body1" sx={{ fontFamily: 'monospace', bg: '#f5f5f5', p: 1 }}>
            {location.pathname}
          </Typography>
        </Box>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">URL Parameters:</Typography>
          <Typography variant="body1" sx={{ fontFamily: 'monospace', bg: '#f5f5f5', p: 1 }}>
            {JSON.stringify(params, null, 2)}
          </Typography>
        </Box>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">Search Params:</Typography>
          <Typography variant="body1" sx={{ fontFamily: 'monospace', bg: '#f5f5f5', p: 1 }}>
            {location.search}
          </Typography>
        </Box>
        
        <Alert severity="success">
          ✅ If you can see this, the route is working!
        </Alert>
      </Paper>
    </Container>
  );
};

export default RouteDebugger; 