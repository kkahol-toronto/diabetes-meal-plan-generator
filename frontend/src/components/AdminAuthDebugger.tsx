import React from 'react';
import { Container, Paper, Typography, Box, Alert, Chip } from '@mui/material';

const AdminAuthDebugger: React.FC = () => {
  const token = localStorage.getItem('token');
  const isAdmin = localStorage.getItem('isAdmin');
  const userId = localStorage.getItem('userId');
  
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          🔐 Admin Auth Debugger
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">Token Status:</Typography>
          <Chip 
            label={token ? "✅ Token Present" : "❌ No Token"} 
            color={token ? "success" : "error"}
            sx={{ mr: 1 }}
          />
          {token && (
            <Typography variant="body2" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
              {token.substring(0, 50)}...
            </Typography>
          )}
        </Box>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">Admin Status:</Typography>
          <Chip 
            label={isAdmin === 'true' ? "✅ Admin" : "❌ Not Admin"} 
            color={isAdmin === 'true' ? "success" : "error"}
            sx={{ mr: 1 }}
          />
          <Typography variant="body2">
            localStorage.isAdmin = "{isAdmin}"
          </Typography>
        </Box>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">User ID:</Typography>
          <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
            {userId || 'Not set'}
          </Typography>
        </Box>
        
        <Alert severity={token && isAdmin === 'true' ? "success" : "warning"}>
          {token && isAdmin === 'true' 
            ? "✅ You should have access to admin routes"
            : "⚠️ You need to login as admin first"
          }
        </Alert>
      </Paper>
    </Container>
  );
};

export default AdminAuthDebugger; 