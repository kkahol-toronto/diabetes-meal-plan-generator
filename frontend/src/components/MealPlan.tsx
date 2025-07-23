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
  selectedDays?: number;
}

const MealPlan = ({ mealPlan, selectedDays = 7 }: MealPlanProps) => {
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setLoaded(true);
  }, []);

  // Generate day labels with real dates starting from today
  const generateDayLabels = (numDays: number) => {
    const labels = [];
    const today = new Date();
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    for (let i = 0; i < numDays; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      const dayName = dayNames[date.getDay()];
      const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      
      labels.push({
        dayNumber: `Day ${i + 1}`,
        dayName: dayName,
        date: monthDay,
        fullLabel: i === 0 ? `Day 1 - Today (${dayName})` : `Day ${i + 1} - ${dayName}`,
        shortLabel: i === 0 ? `Day 1\nToday (${dayName})` : `Day ${i + 1}\n${dayName}`,
        headerLabel: i === 0 ? `📅 Day 1\n${dayName} (Today)\n${monthDay}` : `📅 Day ${i + 1}\n${dayName}\n${monthDay}`
      });
    }
    return labels;
  };
  
  const days = generateDayLabels(selectedDays);
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
          🍽️ Your {selectedDays}-Day Meal Plan
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

      {/* Meal Plan Table */}
      <Slide direction="up" in={loaded} timeout={1200}>
        <Card 
          sx={{ 
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
          <Box sx={{ overflow: 'auto' }}>
            <table 
              className="mobile-scroll-table"
              style={{ 
                width: '100%', 
                borderCollapse: 'collapse',
                minWidth: `${Math.max(700, selectedDays * 150)}px`
              }}
            >
              {/* Header Row */}
              <thead>
                <tr>
                  <th style={{
                    padding: '20px 16px',
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                    color: 'white',
                    fontWeight: 'bold',
                    fontSize: '16px',
                    textAlign: 'center',
                    border: '1px solid rgba(0,0,0,0.1)',
                    position: 'sticky',
                    left: 0,
                    zIndex: 10,
                    minWidth: '140px'
                  }}>
                    🍽️ Meals
                  </th>
                                     {days.map((dayLabel) => (
                     <th key={dayLabel.dayNumber} style={{
                       padding: '20px 16px',
                       background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                       color: 'white',
                       fontWeight: 'bold',
                       fontSize: '16px',
                       textAlign: 'center',
                       border: '1px solid rgba(0,0,0,0.1)',
                       minWidth: '250px',
                       whiteSpace: 'pre-line'
                     }}>
                       {dayLabel.headerLabel}
                     </th>
                   ))}
                </tr>
              </thead>
              
              {/* Body Rows */}
              <tbody>
                {mealTypes.map((mealTypeDetail, mealIndex) => (
                  <Fade in={loaded} timeout={1500 + mealIndex * 200} key={mealTypeDetail.name}>
                    <tr style={{
                      transition: 'all 0.3s ease',
                    }}>
                      <td style={{
                        padding: '16px',
                        background: `linear-gradient(135deg, ${mealTypeDetail.color}20, ${mealTypeDetail.color}10)`,
                        fontWeight: 'bold',
                        fontSize: '16px',
                        border: '1px solid rgba(0,0,0,0.1)',
                        position: 'sticky',
                        left: 0,
                        zIndex: 5,
                        color: mealTypeDetail.color,
                        textAlign: 'center'
                      }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                          <Box sx={{ fontSize: 20 }}>{mealTypeDetail.icon}</Box>
                          <span>{mealTypeDetail.label}</span>
                        </Box>
                      </td>
                                             {days.map((dayLabel, dayIndex) => (
                         <td key={dayLabel.dayNumber} style={{
                           padding: '16px',
                           border: '1px solid rgba(0,0,0,0.1)',
                           backgroundColor: mealIndex % 2 === 0 ? '#ffffff' : '#fafafa',
                           verticalAlign: 'top'
                         }}>
                           <Box
                             sx={{
                               p: 2,
                               borderRadius: 2,
                               background: `linear-gradient(135deg, ${mealTypeDetail.color}08, ${mealTypeDetail.color}05)`,
                               border: `1px solid ${mealTypeDetail.color}20`,
                               transition: 'all 0.3s ease',
                               cursor: 'pointer',
                               '&:hover': {
                                 transform: 'translateY(-2px)',
                                 boxShadow: `0 4px 12px ${mealTypeDetail.color}30`,
                                 background: `linear-gradient(135deg, ${mealTypeDetail.color}15, ${mealTypeDetail.color}08)`,
                               },
                             }}
                           >
                             <Typography 
                               variant="body1" 
                               sx={{
                                 color: 'text.primary',
                                 lineHeight: 1.5,
                                 fontWeight: 500,
                                 fontSize: '14px'
                               }}
                             >
                               {mealPlan[mealTypeDetail.name][dayIndex] || (
                                 <span style={{ 
                                   color: theme.palette.text.secondary, 
                                   fontStyle: 'italic' 
                                 }}>
                                   Not specified
                                 </span>
                               )}
                             </Typography>
                           </Box>
                         </td>
                       ))}
                    </tr>
                  </Fade>
                ))}
              </tbody>
            </table>
          </Box>
        </Card>
      </Slide>
    </Box>
  );
};

export default MealPlan; 