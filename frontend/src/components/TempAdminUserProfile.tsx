import React from 'react';
import { useParams } from 'react-router-dom';
import { Container, Paper, Typography, Alert } from '@mui/material';

const TempAdminUserProfile: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          🔧 Temp Admin User Profile
        </Typography>
        
        <Alert severity="success" sx={{ mb: 2 }}>
          ✅ Route is working! User ID: {userId}
        </Alert>
        
        <Typography variant="body1">
          If you can see this page, the routing is working correctly. 
          The issue was likely with admin authentication or component errors.
        </Typography>
        
        <Alert severity="info" sx={{ mt: 2 }}>
          Next step: Go back to using the real AdminUserProfile component 
          and check your admin login status.
        </Alert>
      </Paper>
    </Container>
  );
};

export default TempAdminUserProfile; 