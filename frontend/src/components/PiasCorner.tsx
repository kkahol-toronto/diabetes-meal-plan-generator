import React, { useState, useEffect } from 'react';
import {
  Container, Tabs, Tab, Box, Typography, ToggleButtonGroup, 
  ToggleButton, FormControl, InputLabel, Select, MenuItem,
  Card, CardContent, Grid, Alert, CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import config from '../config/environment';

// Import analytics components
import OverviewDashboard from './analytics/OverviewDashboard';
import NutrientAdequacy from './analytics/NutrientAdequacy';
import EngagementMetrics from './analytics/EngagementMetrics';
import OutlierDetection from './analytics/OutlierDetection';
import BehaviorClusters from './analytics/BehaviorClusters';
import ComplianceAnalysis from './analytics/ComplianceAnalysis';

interface Patient {
  id: string;
  name: string;
  condition: string;
  registration_code: string;
  created_at: string;
}

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

const PiasCorner: React.FC = () => {
  const navigate = useNavigate();
  
  // State Management
  const [viewMode, setViewMode] = useState<'individual' | 'cohort'>('cohort');
  const [tabValue, setTabValue] = useState(0);
  const [selectedPatient, setSelectedPatient] = useState<string>('');
  const [groupingCriteria, setGroupingCriteria] = useState('diabetes_type');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab Panel Component
  const TabPanel = ({ children, value, index }: any) => (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  // Load patients on mount
  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await fetch(`${config.API_URL}/admin/analytics/patients-list`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          navigate('/admin/login');
          return;
        }
        throw new Error('Failed to fetch patients');
      }
      
      const data = await response.json();
      setPatients(data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load patients');
      setLoading(false);
    }
  };

  const handleViewModeChange = (
    event: React.MouseEvent<HTMLElement>,
    newMode: 'individual' | 'cohort' | null,
  ) => {
    if (newMode !== null) {
      setViewMode(newMode);
      // Reset selections when switching modes
      if (newMode === 'individual') {
        setSelectedPatient('');
      } else {
        setGroupingCriteria('diabetes_type');
      }
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress size={60} />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Typography 
        variant="h3" 
        gutterBottom 
        sx={{ 
          fontWeight: 'bold',
          background: 'linear-gradient(45deg, #667eea, #764ba2)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textAlign: 'center',
          mb: 4
        }}
      >
        🎯 Pia's Corner - Advanced Analytics Dashboard
      </Typography>
      
      {/* View Mode Toggle */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Analysis Mode</Typography>
          <ToggleButtonGroup 
            value={viewMode} 
            exclusive 
            onChange={handleViewModeChange}
            sx={{ mb: 2 }}
          >
            <ToggleButton value="individual">
              👤 Individual Patient Analysis
            </ToggleButton>
            <ToggleButton value="cohort">
              👥 Cumulative Cohort Analysis
            </ToggleButton>
          </ToggleButtonGroup>

          {/* Controls Based on View Mode */}
          <Grid container spacing={2}>
            {viewMode === 'individual' ? (
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Select Patient</InputLabel>
                  <Select 
                    value={selectedPatient} 
                    onChange={(e) => setSelectedPatient(e.target.value)}
                    label="Select Patient"
                  >
                    {patients.map(patient => (
                      <MenuItem key={patient.id} value={patient.id}>
                        {patient.name} - {patient.condition} ({patient.registration_code})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            ) : (
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Group Patients By</InputLabel>
                  <Select 
                    value={groupingCriteria} 
                    onChange={(e) => setGroupingCriteria(e.target.value)}
                    label="Group Patients By"
                  >
                    <MenuItem value="diabetes_type">Diabetes Type</MenuItem>
                    <MenuItem value="age_group">Age Group</MenuItem>
                    <MenuItem value="compliance_level">Compliance Level</MenuItem>
                    <MenuItem value="platform_usage">Platform Usage Duration</MenuItem>
                    <MenuItem value="gender">Gender</MenuItem>
                    <MenuItem value="bmi_category">BMI Category</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Analytics Tabs */}
      <Card>
        <Tabs 
          value={tabValue} 
          onChange={(e, newValue) => setTabValue(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="📊 Overview Dashboard" />
          <Tab label="🥗 Nutrient Adequacy" />
          <Tab label="📱 Engagement Metrics" />
          <Tab label="⚠️ Outlier Detection" />
          <Tab label="🔍 Behavior Clusters" />
          <Tab label="✅ Compliance Analysis" />
        </Tabs>

        {/* Tab Content */}
        <TabPanel value={tabValue} index={0}>
          <OverviewDashboard 
            viewMode={viewMode} 
            selectedPatient={selectedPatient} 
            groupingCriteria={groupingCriteria} 
          />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <NutrientAdequacy 
            viewMode={viewMode} 
            selectedPatient={selectedPatient} 
            groupingCriteria={groupingCriteria} 
          />
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <EngagementMetrics 
            viewMode={viewMode} 
            selectedPatient={selectedPatient} 
            groupingCriteria={groupingCriteria} 
          />
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          <OutlierDetection 
            viewMode={viewMode} 
            selectedPatient={selectedPatient} 
            groupingCriteria={groupingCriteria} 
          />
        </TabPanel>
        <TabPanel value={tabValue} index={4}>
          <BehaviorClusters 
            viewMode={viewMode} 
            selectedPatient={selectedPatient} 
            groupingCriteria={groupingCriteria} 
          />
        </TabPanel>
        <TabPanel value={tabValue} index={5}>
          <ComplianceAnalysis 
            viewMode={viewMode} 
            selectedPatient={selectedPatient} 
            groupingCriteria={groupingCriteria} 
          />
        </TabPanel>
      </Card>
    </Container>
  );
};

export default PiasCorner; 