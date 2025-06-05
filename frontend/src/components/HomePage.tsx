import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  IconButton,
  Fade,
  Slide,
  Zoom,
  useTheme,
  keyframes,
} from '@mui/material';
import {
  Restaurant as RestaurantIcon,
  Chat as ChatIcon,
  Timeline as TimelineIcon,
  History as HistoryIcon,
  AutoAwesome as SparkleIcon,
  Favorite as HeartIcon,
  LocalDining as DiningIcon,
  Psychology as BrainIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';

// Floating animation
const float = keyframes`
  0% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-10px) rotate(2deg); }
  100% { transform: translateY(0px) rotate(0deg); }
`;

// Pulse animation
const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

// Gradient shift animation
const gradientShift = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

const HomePage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setLoaded(true);
  }, []);

  const features = [
    {
      icon: <RestaurantIcon sx={{ fontSize: 40, color: '#4CAF50' }} />,
      title: "Personalized Meal Planning",
      description: "AI-powered meal plans tailored to your diabetes management needs and taste preferences",
      delay: 200,
    },
    {
      icon: <BrainIcon sx={{ fontSize: 40, color: '#2196F3' }} />,
      title: "Smart Recipe Suggestions",
      description: "Access diabetes-friendly recipes with detailed nutritional information and cooking instructions",
      delay: 400,
    },
    {
      icon: <DiningIcon sx={{ fontSize: 40, color: '#FF9800' }} />,
      title: "Consumption Tracking",
      description: "Upload food images for instant AI analysis and track your daily nutrition intake",
      delay: 600,
    },
    {
      icon: <ChatIcon sx={{ fontSize: 40, color: '#9C27B0' }} />,
      title: "AI-Powered Assistant",
      description: "Get instant answers to nutrition questions and personalized dietary advice 24/7",
      delay: 800,
    },
  ];

  const stats = [
    { icon: <BrainIcon />, number: "AI-Powered", label: "Smart Planning" },
    { icon: <RestaurantIcon />, number: "Diabetes-Friendly", label: "Meal Plans" },
    { icon: <HeartIcon />, number: "Health-Focused", label: "Approach" },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(-45deg, ${theme.palette.primary.main}15, ${theme.palette.secondary.main}15, ${theme.palette.primary.main}10, ${theme.palette.secondary.main}10)`,
        backgroundSize: '400% 400%',
        animation: `${gradientShift} 15s ease infinite`,
        py: 2,
      }}
    >
      <Container maxWidth="lg">
        {/* Hero Section */}
        <Slide direction="down" in={loaded} timeout={1000}>
          <Box textAlign="center" sx={{ mb: 6 }}>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                mb: 2,
                animation: `${float} 6s ease-in-out infinite`,
              }}
            >
              <SparkleIcon 
                sx={{ 
                  fontSize: 60, 
                  color: theme.palette.primary.main,
                  mr: 2,
                  animation: `${pulse} 2s ease-in-out infinite`,
                }} 
              />
              <Typography 
                variant="h2" 
                component="h1" 
                sx={{
                  fontWeight: 800,
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  textShadow: '0 4px 8px rgba(0,0,0,0.1)',
                }}
              >
                Diabetes Diet Manager
              </Typography>
            </Box>
            
            <Fade in={loaded} timeout={1500}>
              <Typography 
                variant="h5" 
                sx={{
                  color: 'text.secondary',
                  fontWeight: 300,
                  mb: 4,
                  maxWidth: 600,
                  mx: 'auto',
                }}
              >
                Transform your health journey with AI-powered nutrition guidance designed specifically for diabetes management
              </Typography>
            </Fade>

            {/* Action Buttons */}
            <Zoom in={loaded} timeout={1000}>
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mb: 4 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate('/meal-plan')}
                  sx={{
                    px: 4,
                    py: 2,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    borderRadius: 3,
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                    boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 12px 25px rgba(0,0,0,0.2)',
                    },
                  }}
                >
                  🍽️ Create Meal Plan
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/chat')}
                  sx={{
                    px: 4,
                    py: 2,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    borderRadius: 3,
                    borderWidth: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      borderWidth: 2,
                      backgroundColor: theme.palette.primary.main,
                      color: 'white',
                    },
                  }}
                >
                  💬 Chat with AI
                </Button>
              </Box>
            </Zoom>
          </Box>
        </Slide>

        {/* Stats Section */}
        <Fade in={loaded} timeout={2000}>
          <Grid container spacing={3} sx={{ mb: 6 }}>
            {stats.map((stat, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card
                  sx={{
                    textAlign: 'center',
                    py: 3,
                    background: 'rgba(255,255,255,0.9)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: 3,
                    transition: 'all 0.3s ease',
                    animation: `${float} ${4 + index}s ease-in-out infinite`,
                    '&:hover': {
                      transform: 'translateY(-5px)',
                      boxShadow: '0 15px 30px rgba(0,0,0,0.15)',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ color: theme.palette.primary.main, mb: 1 }}>
                      {stat.icon}
                    </Box>
                    <Typography variant="h4" fontWeight="bold" color="primary">
                      {stat.number}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stat.label}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Fade>

        {/* Features Section */}
        <Typography 
          variant="h3" 
          textAlign="center" 
          sx={{ 
            mb: 5, 
            fontWeight: 700,
            color: theme.palette.primary.main,
          }}
        >
          ✨ Powerful Features
        </Typography>

        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Slide 
                direction={index % 2 === 0 ? 'right' : 'left'} 
                in={loaded} 
                timeout={1000 + feature.delay}
              >
                <Card
                  sx={{
                    height: '100%',
                    background: 'rgba(255,255,255,0.95)',
                    backdropFilter: 'blur(15px)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    borderRadius: 4,
                    transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                    cursor: 'pointer',
                    '&:hover': {
                      transform: 'translateY(-8px) scale(1.02)',
                      boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
                      '& .feature-icon': {
                        transform: 'rotate(10deg) scale(1.1)',
                      },
                    },
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Box
                      className="feature-icon"
                      sx={{
                        transition: 'transform 0.3s ease',
                        mb: 2,
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Typography 
                      variant="h6" 
                      fontWeight="bold" 
                      gutterBottom
                      color="primary"
                    >
                      {feature.title}
                    </Typography>
                    <Typography 
                      variant="body1" 
                      color="text.secondary"
                      lineHeight={1.6}
                    >
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Slide>
            </Grid>
          ))}
        </Grid>

        {/* Quick Access Section */}
        <Fade in={loaded} timeout={3000}>
          <Box 
            sx={{ 
              mt: 6, 
              textAlign: 'center',
              p: 4,
              background: `linear-gradient(45deg, ${theme.palette.primary.main}10, ${theme.palette.secondary.main}10)`,
              borderRadius: 4,
              border: `2px solid ${theme.palette.primary.main}20`,
            }}
          >
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              🚀 Quick Access
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Jump straight into the features you need most
            </Typography>
            
            <Grid container spacing={2} justifyContent="center">
              {[
                { icon: <HistoryIcon />, label: 'Meal History', path: '/meal-plan/history' },
                { icon: <TimelineIcon />, label: 'Consumption', path: '/consumption-history' },
                { icon: <ChatIcon />, label: 'AI Chat', path: '/chat' },
                { icon: <RestaurantIcon />, label: 'New Plan', path: '/meal-plan' },
              ].map((item, index) => (
                <Grid item key={index}>
                  <IconButton
                    onClick={() => navigate(item.path)}
                    sx={{
                      flexDirection: 'column',
                      p: 2,
                      borderRadius: 3,
                      backgroundColor: 'white',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-3px)',
                        backgroundColor: theme.palette.primary.main,
                        color: 'white',
                        boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
                      },
                    }}
                  >
                    {item.icon}
                    <Typography variant="caption" sx={{ mt: 1 }}>
                      {item.label}
                    </Typography>
                  </IconButton>
                </Grid>
              ))}
            </Grid>
          </Box>
        </Fade>
      </Container>
    </Box>
  );
};

export default HomePage; 