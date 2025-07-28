import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Tab,
  Tabs,
} from '@mui/material';
import { BarChart, TrendingUp, FindInPage, Groups, Timeline, TableChart, Psychology } from '@mui/icons-material';

// Import individual dashboard components
import NutrientAdequacy from './PiasCorner/NutrientAdequacy';
import EngagementMetrics from './PiasCorner/EngagementMetrics';
import OutlierDetection from './PiasCorner/OutlierDetection';
import BehaviorClusters from './PiasCorner/BehaviorClusters';
import ComplianceGraph from './PiasCorner/ComplianceGraph';
import PatientTable from './PiasCorner/PatientTable';
import AIAdviceDoctor from './PiasCorner/AIAdviceDoctor';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`pias-corner-tabpanel-${index}`}
      aria-labelledby={`pias-corner-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `pias-corner-tab-${index}`,
    'aria-controls': `pias-corner-tabpanel-${index}`,
  };
}

const PiasCorner: React.FC = () => {
  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const tabs = [
    { label: 'Nutrient Adequacy', icon: <BarChart />, component: <NutrientAdequacy /> },
    { label: 'Engagement Metrics', icon: <TrendingUp />, component: <EngagementMetrics /> },
    { label: 'Outlier Detection', icon: <FindInPage />, component: <OutlierDetection /> },
    { label: 'Behavior Clusters', icon: <Groups />, component: <BehaviorClusters /> },
    { label: 'Compliance Graph', icon: <Timeline />, component: <ComplianceGraph /> },
    { label: 'Patient Table', icon: <TableChart />, component: <PatientTable /> },
    { label: 'AI Advice Doctor', icon: <Psychology />, component: <AIAdviceDoctor /> },
  ];

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
          <Psychology sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Typography 
            variant="h3" 
            component="h1"
            sx={{
              background: 'linear-gradient(45deg, #667eea, #764ba2)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 'bold',
            }}
          >
            Pia's Corner
          </Typography>
        </Box>

        <Typography variant="h6" sx={{ mb: 4, color: 'text.secondary' }}>
          Comprehensive Patient Analytics Dashboard - Real-time insights from production data
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={value} 
            onChange={handleChange} 
            aria-label="Pia's Corner dashboard tabs"
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
          >
            {tabs.map((tab, index) => (
              <Tab 
                key={index}
                icon={tab.icon} 
                iconPosition="start"
                label={tab.label} 
                {...a11yProps(index)}
                sx={{ 
                  minHeight: '72px',
                  textTransform: 'none',
                  fontSize: '0.95rem',
                  fontWeight: 500,
                }}
              />
            ))}
          </Tabs>
        </Box>

        {tabs.map((tab, index) => (
          <TabPanel key={index} value={value} index={index}>
            {tab.component}
          </TabPanel>
        ))}
      </Paper>
    </Container>
  );
};

export default PiasCorner; 