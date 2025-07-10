import React from 'react';
import { Box, Typography, Container, Divider } from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';

const ComplianceFooter: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        mt: 'auto',
        py: 2,
        backgroundColor: '#f5f5f5',
        borderTop: '1px solid #e0e0e0',
        position: 'relative',
        bottom: 0,
        width: '100%',
        zIndex: 1000,
      }}
    >
      <Container maxWidth="lg">
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            flexWrap: 'wrap',
            textAlign: 'center',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <SecurityIcon 
              sx={{ 
                fontSize: '1.1rem', 
                color: '#1976d2',
              }} 
            />
            <VerifiedUserIcon 
              sx={{ 
                fontSize: '1.1rem', 
                color: '#2e7d32',
              }} 
            />
          </Box>
          
          <Typography
            variant="body2"
            sx={{
              color: '#666',
              fontSize: '0.85rem',
              fontWeight: 500,
              lineHeight: 1.4,
              maxWidth: '900px',
            }}
          >
            🔒 This tool complies with the Personal Health Information Protection Act (PHIPA) in Canada 
            and the Health Insurance Portability and Accountability Act (HIPAA) in the United States.
          </Typography>
        </Box>
        
        {/* Optional additional compliance info */}
        <Box
          sx={{
            mt: 1,
            pt: 1,
            borderTop: '1px solid #eee',
            textAlign: 'center',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: '#888',
              fontSize: '0.75rem',
              display: 'block',
            }}
          >
            All personal health information is encrypted and securely stored in compliance with applicable privacy laws.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default ComplianceFooter; 