import React from 'react';
import { Box, Typography, LinearProgress, Paper } from '@mui/material';

interface MicronutrientData {
  nutrient: string;
  consumed: number;
  recommended: number;
  unit: string;
}

interface MicronutrientBarsProps {
  analytics: {
    micronutrients: {
      [key: string]: {
        consumed: number;
        recommended: number;
      };
    };
  };
}

type NutrientInfo = {
  value: number;
  unit: string;
};

type RecommendedValues = {
  [key: string]: NutrientInfo;
};

// Recommended Daily Values (RDV) in mg unless specified
const RECOMMENDED_VALUES: RecommendedValues = {
  fiber: { value: 25000, unit: 'mg' },
  sugar: { value: 25000, unit: 'mg' },
  sodium: { value: 2300, unit: 'mg' },
  potassium: { value: 3500, unit: 'mg' },
  calcium: { value: 1000, unit: 'mg' },
  iron: { value: 18, unit: 'mg' },
  vitaminA: { value: 900, unit: 'mcg' },
  vitaminC: { value: 90, unit: 'mg' },
  vitaminD: { value: 20, unit: 'mcg' },
  vitaminE: { value: 15, unit: 'mg' },
  vitaminK: { value: 120, unit: 'mcg' },
  thiamin: { value: 1.2, unit: 'mg' },
  riboflavin: { value: 1.3, unit: 'mg' },
  niacin: { value: 16, unit: 'mg' },
  vitaminB6: { value: 1.7, unit: 'mg' },
  folate: { value: 400, unit: 'mcg' },
  vitaminB12: { value: 2.4, unit: 'mcg' },
  biotin: { value: 30, unit: 'mcg' },
  pantothenicAcid: { value: 5, unit: 'mg' },
  choline: { value: 550, unit: 'mg' },
  magnesium: { value: 420, unit: 'mg' },
  zinc: { value: 11, unit: 'mg' },
  selenium: { value: 55, unit: 'mcg' },
  copper: { value: 900, unit: 'mcg' },
  manganese: { value: 2.3, unit: 'mg' },
  chromium: { value: 35, unit: 'mcg' },
  molybdenum: { value: 45, unit: 'mcg' },
  chloride: { value: 2300, unit: 'mg' },
  phosphorus: { value: 700, unit: 'mg' }
};

const formatNutrientName = (name: string): string => {
  return name
    .replace(/([A-Z])/g, ' $1') // Add space before capital letters
    .replace(/^./, str => str.toUpperCase()) // Capitalize first letter
    .replace(/B(\d+)/, 'B-$1'); // Add hyphen for B vitamins
};

const MicronutrientBars: React.FC<MicronutrientBarsProps> = ({ analytics }) => {
  const micronutrientData = Object.entries(analytics.micronutrients).map(([nutrient, data]) => ({
    nutrient: formatNutrientName(nutrient),
    consumed: data.consumed,
    recommended: data.recommended,
    unit: RECOMMENDED_VALUES[nutrient as keyof typeof RECOMMENDED_VALUES]?.unit || 'mg'
  }));

  return (
    <Paper 
      elevation={0}
      sx={{ 
        p: 4,
        borderRadius: 4,
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.3)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
        mt: 4,
      }}
    >
      <Typography variant="h6" gutterBottom>
        Micronutrients Progress
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {micronutrientData.map((item, index) => {
          const progress = (item.consumed / item.recommended) * 100;
          const color = progress >= 100 ? 'success' : progress >= 70 ? 'info' : 'warning';
          
          return (
            <Box key={index} sx={{ width: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1" color="textPrimary">
                  {item.nutrient}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {Math.round(item.consumed)} / {item.recommended} {item.unit}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={Math.min(progress, 100)} 
                color={color}
                sx={{ 
                  height: 10, 
                  borderRadius: 5,
                  backgroundColor: 'rgba(0,0,0,0.05)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 5,
                  }
                }}
              />
            </Box>
          );
        })}
      </Box>
    </Paper>
  );
};

export default MicronutrientBars; 