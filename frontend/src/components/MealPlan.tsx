import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Divider,
  Paper,
  ListItemIcon,
  Chip,
  Fade,
  Slide,
  Zoom,
  useTheme,
  keyframes,
} from '@mui/material';
import { Theme } from '@mui/material/styles';
import { MealPlanData } from '../types';

// Import icons for meal types
import BreakfastIcon from '@mui/icons-material/FreeBreakfast';
import LunchIcon from '@mui/icons-material/LunchDining';
import DinnerIcon from '@mui/icons-material/DinnerDining';
import SnackIcon from '@mui/icons-material/Icecream'; // Placeholder, find a better snack icon if needed
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter'; // For calories
import BoltIcon from '@mui/icons-material/Bolt'; // For Protein
import GrainIcon from '@mui/icons-material/Grain'; // For Carbs
import OilIcon from '@mui/icons-material/Opacity'; // For Fats

// Animations
const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
  100% { transform: translateY(0px); }
`;

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const shimmer = keyframes`
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
`;

interface MealPlanProps {
  mealPlan: MealPlanData;
}

const MealPlan = ({ mealPlan }: MealPlanProps) => {
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setLoaded(true);
  }, []);

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const mealTypes: Array<{ 
    name: keyof Pick<MealPlanData, 'breakfast' | 'lunch' | 'dinner' | 'snacks'>; 
    icon: JSX.Element; 
    label: string;
    color: string;
  }> = [
    { name: 'breakfast', icon: <BreakfastIcon />, label: 'Breakfast', color: '#FF6B35' },
    { name: 'lunch', icon: <LunchIcon />, label: 'Lunch', color: '#4ECDC4' },
    { name: 'dinner', icon: <DinnerIcon />, label: 'Dinner', color: '#45B7D1' },
    { name: 'snacks', icon: <SnackIcon />, label: 'Snacks', color: '#96CEB4' },
  ];

  const nutritionData = [
    { 
      icon: <FitnessCenterIcon />, 
      label: 'Calories', 
      value: `${mealPlan.dailyCalories} kcal`, 
      color: '#FF6B6B',
      bgColor: 'rgba(255, 107, 107, 0.1)'
    },
    { 
      icon: <BoltIcon />, 
      label: 'Protein', 
      value: `${mealPlan.macronutrients.protein}g`, 
      color: '#4ECDC4',
      bgColor: 'rgba(78, 205, 196, 0.1)'
    },
    { 
      icon: <GrainIcon />, 
      label: 'Carbs', 
      value: `${mealPlan.macronutrients.carbs}g`, 
      color: '#45B7D1',
      bgColor: 'rgba(69, 183, 209, 0.1)'
    },
    { 
      icon: <OilIcon />, 
      label: 'Fats', 
      value: `${mealPlan.macronutrients.fats}g`, 
      color: '#96CEB4',
      bgColor: 'rgba(150, 206, 180, 0.1)'
    },
  ];

  return (
    <Box 
      sx={{ 
        p: 1,
        background: `linear-gradient(-45deg, ${theme.palette.primary.main}08, ${theme.palette.secondary.main}08, ${theme.palette.primary.main}05, ${theme.palette.secondary.main}05)`,
        minHeight: '100vh',
      }}
    >
      <Fade in={loaded} timeout={1000}>
        <Typography 
          variant="h4" 
          component="h2" 
          gutterBottom 
          align="center" 
          sx={{ 
            fontWeight: 800,
            mb: 4,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            textShadow: '0 4px 8px rgba(0,0,0,0.1)',
          }}
        >
          🍽️ Your Weekly Meal Plan
        </Typography>
      </Fade>

      {/* Nutritional Goals Section */}
      <Slide direction="down" in={loaded} timeout={1200}>
        <Card 
          sx={{ 
            mb: 4, 
            borderRadius: 4, 
            background: 'rgba(255,255,255,0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.3)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
            overflow: 'hidden',
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: '-200px',
              width: '200px',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
              animation: `${shimmer} 3s infinite`,
            },
          }}
        >
          <CardContent 
            sx={{ 
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              color: 'white',
              textAlign: 'center',
              py: 3,
            }}
          >
            <Typography variant="h5" component="div" fontWeight="bold">
              🎯 Daily Nutritional Goals
            </Typography>
          </CardContent>
          <CardContent sx={{ p: 4 }}>
            <Grid container spacing={3}>
              {nutritionData.map((item, index) => (
                <Grid item xs={6} sm={3} key={index}>
                  <Zoom in={loaded} timeout={1000 + index * 200}>
                    <Card
                      sx={{
                        textAlign: 'center',
                        p: 2,
                        borderRadius: 3,
                        background: item.bgColor,
                        border: `2px solid ${item.color}20`,
                        transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                        cursor: 'pointer',
                        animation: `${float} ${3 + index * 0.5}s ease-in-out infinite`,
                        '&:hover': {
                          transform: 'translateY(-8px) scale(1.05)',
                          boxShadow: `0 12px 25px ${item.color}40`,
                          background: item.bgColor.replace('0.1', '0.2'),
                        },
                      }}
                    >
                      <Box sx={{ color: item.color, mb: 1, fontSize: 32 }}>
                        {item.icon}
                      </Box>
                      <Typography variant="h6" fontWeight="bold" color={item.color}>
                        {item.value}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {item.label}
                      </Typography>
                    </Card>
                  </Zoom>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Slide>

      {/* Daily Meal Plans */}
      <Grid container spacing={3}>
        {days.map((day, dayIndex) => (
          <Grid item xs={12} md={6} lg={4} key={day}>
            <Slide 
              direction={dayIndex % 2 === 0 ? 'right' : 'left'} 
              in={loaded} 
              timeout={1000 + dayIndex * 150}
            >
              <Card 
                sx={{ 
                  borderRadius: 4, 
                  height: '100%',
                  background: 'rgba(255,255,255,0.95)',
                  backdropFilter: 'blur(15px)',
                  border: '1px solid rgba(255,255,255,0.3)',
                  transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                  animation: `${float} ${4 + dayIndex * 0.3}s ease-in-out infinite`,
                  '&:hover': {
                    transform: 'translateY(-10px)',
                    boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
                    '& .day-header': {
                      background: `linear-gradient(135deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`,
                    },
                  },
                }}
              >
                <CardContent 
                  className="day-header"
                  sx={{ 
                    background: `linear-gradient(135deg, ${theme.palette.secondary.main}dd, ${theme.palette.secondary.dark}dd)`,
                    color: 'white',
                    textAlign: 'center',
                    py: 2,
                    transition: 'all 0.3s ease',
                  }}
                >
                  <Typography variant="h6" component="div" fontWeight="bold">
                    {day}
                  </Typography>
                </CardContent>
                <CardContent sx={{ p: 3 }}>
                  {mealTypes.map((mealTypeDetail, mealIndex) => (
                    <Fade in={loaded} timeout={1500 + dayIndex * 100 + mealIndex * 50} key={mealTypeDetail.name}>
                      <Paper 
                        elevation={0}
                        sx={{
                          mb: 2, 
                          p: 3, 
                          borderRadius: 3, 
                          background: `linear-gradient(135deg, ${mealTypeDetail.color}15, ${mealTypeDetail.color}08)`,
                          border: `2px solid ${mealTypeDetail.color}30`,
                          transition: 'all 0.3s ease',
                          cursor: 'pointer',
                          '&:hover': {
                            transform: 'translateX(10px)',
                            boxShadow: `0 8px 20px ${mealTypeDetail.color}30`,
                            background: `linear-gradient(135deg, ${mealTypeDetail.color}25, ${mealTypeDetail.color}15)`,
                            '& .meal-icon': {
                              transform: 'rotate(10deg) scale(1.2)',
                              animation: `${pulse} 0.6s ease`,
                            },
                          },
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2}}>
                          <Box 
                            className="meal-icon"
                            sx={{ 
                              minWidth: 'auto', 
                              mr: 2, 
                              color: mealTypeDetail.color,
                              fontSize: 28,
                              transition: 'all 0.3s ease',
                            }}
                          >
                            {mealTypeDetail.icon}
                          </Box>
                          <Typography 
                            variant="subtitle1" 
                            sx={{ 
                              fontWeight: 700, 
                              color: mealTypeDetail.color,
                              textTransform: 'uppercase',
                              letterSpacing: 1,
                            }}
                          >
                            {mealTypeDetail.label}
                          </Typography>
                        </Box>
                        <Typography 
                          variant="body1" 
                          sx={{
                            color: 'text.primary',
                            lineHeight: 1.6,
                            fontWeight: 500,
                            pl: 1,
                          }}
                        >
                          {mealPlan[mealTypeDetail.name][dayIndex] || 'Not specified'}
                        </Typography>
                      </Paper>
                    </Fade>
                  ))}
                </CardContent>
              </Card>
            </Slide>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default MealPlan; 