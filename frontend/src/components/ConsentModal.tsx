import React, { useState, useRef, useEffect } from 'react';
import {
  Modal,
  Box,
  Typography,
  Button,
  IconButton,
  Divider,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

interface ConsentModalProps {
  open: boolean;
  onClose: () => void;
  onScrolled: () => void;
  hasScrolledToBottom: boolean;
}

const ConsentModal: React.FC<ConsentModalProps> = ({
  open,
  onClose,
  onScrolled,
  hasScrolledToBottom,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const [isScrolledToBottom, setIsScrolledToBottom] = useState(hasScrolledToBottom);

  useEffect(() => {
    setIsScrolledToBottom(hasScrolledToBottom);
  }, [hasScrolledToBottom]);

  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      // Check if user has scrolled to the bottom (with a small margin of error)
      if (scrollTop + clientHeight >= scrollHeight - 20) {
        setIsScrolledToBottom(true);
        onScrolled();
      }
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="consent-modal-title"
      aria-describedby="consent-modal-description"
    >
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          bgcolor: 'white',
          boxShadow: 24,
          p: 0,
          borderRadius: 2,
          width: { xs: '90%', sm: '70%', md: '60%' },
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          maxWidth: '800px',
          overflow: 'hidden',
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          p: 2,
          bgcolor: '#667eea', 
          color: 'white'
        }}>
          <Typography id="consent-modal-title" variant="h6" component="h2" sx={{ fontWeight: 'bold' }}>
            Terms and Conditions
          </Typography>
          <IconButton onClick={onClose} size="small" sx={{ color: 'white' }}>
            <CloseIcon />
          </IconButton>
        </Box>

        <Divider />
        
        <Box
          ref={scrollContainerRef}
          onScroll={handleScroll}
          sx={{ 
            overflowY: 'auto', 
            maxHeight: '70vh', 
            p: 3,
          }}
        >
          <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
            Health Information Terms and Conditions
          </Typography>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            <strong>Last Updated: June 10, 2024</strong>
          </Typography>
          <Typography variant="body2" sx={{ mb: 3 }}>
            This document explains how Diet Meal Planner ("we", "us", "our") collects, uses, and protects your health information when you use our application.
          </Typography>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            1. Information We Collect
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            We collect the following types of health-related information:
          </Typography>
          <ul>
            <li><Typography variant="body2">Medical conditions and diagnoses</Typography></li>
            <li><Typography variant="body2">Dietary restrictions and allergies</Typography></li>
            <li><Typography variant="body2">Height, weight, and other physical measurements</Typography></li>
            <li><Typography variant="body2">Food consumption history</Typography></li>
            <li><Typography variant="body2">Exercise habits and mobility information</Typography></li>
            <li><Typography variant="body2">Medication information</Typography></li>
          </ul>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            2. How We Use Your Information
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            We use your health information to:
          </Typography>
          <ul>
            <li><Typography variant="body2">Generate personalized meal plans tailored to your health needs</Typography></li>
            <li><Typography variant="body2">Provide dietary recommendations that align with your medical conditions</Typography></li>
            <li><Typography variant="body2">Track and analyze your nutrition habits to offer better guidance</Typography></li>
            <li><Typography variant="body2">Improve our AI-powered health coaching features</Typography></li>
            <li><Typography variant="body2">Create shopping lists based on your dietary requirements</Typography></li>
          </ul>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            3. Information Sharing
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            We do not sell your personal information to third parties. We may share anonymized, aggregated data for research purposes to improve diabetes management and nutrition science.
          </Typography>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            4. Data Security
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            We implement robust security measures to protect your health information, including encryption, access controls, and regular security audits. However, no method of transmission over the Internet or electronic storage is 100% secure.
          </Typography>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            5. Your Rights
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            You have the right to:
          </Typography>
          <ul>
            <li><Typography variant="body2">Access the health information we have about you</Typography></li>
            <li><Typography variant="body2">Request corrections to your information</Typography></li>
            <li><Typography variant="body2">Request deletion of your account and associated data</Typography></li>
            <li><Typography variant="body2">Withdraw consent at any time (though this may limit functionality)</Typography></li>
          </ul>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            6. Data Retention
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            We retain your health information for as long as your account is active or as needed to provide you services. If you delete your account, we will delete or anonymize your information within 30 days.
          </Typography>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            7. Changes to This Policy
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            We may update these Terms and Conditions periodically. We will notify you of significant changes by email or through the application.
          </Typography>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            8. Contact Information
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            If you have questions about these Terms and Conditions or your information, please contact us at support@dietmealplanner.com.
          </Typography>

          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, mt: 3 }}>
            Agreement Statement
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            By checking the consent box, you acknowledge that you have read and understood these Terms and Conditions and consent to the collection and use of your health information as described. You understand that this information is necessary to provide you with personalized meal planning services tailored to your health needs.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            You may withdraw your consent at any time by contacting us, but doing so may result in limited functionality of the Diet Meal Planner application.
          </Typography>
        </Box>
        
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'flex-end', 
          p: 2, 
          bgcolor: '#f8f8f8',
          borderTop: '1px solid #e0e0e0'
        }}>
          <Button
            onClick={onClose}
            variant="contained"
            disabled={!isScrolledToBottom}
            sx={{
              bgcolor: isScrolledToBottom ? '#667eea' : 'grey.400',
              color: 'white',
              fontWeight: 'bold',
              '&:hover': {
                bgcolor: isScrolledToBottom ? '#5166d6' : 'grey.500',
              }
            }}
          >
            {isScrolledToBottom ? 'I Understand' : 'Please scroll to the end'}
          </Button>
        </Box>
      </Box>
    </Modal>
  );
};

export default ConsentModal; 