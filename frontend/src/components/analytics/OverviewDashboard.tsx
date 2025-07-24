import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Alert, Box, 
  CircularProgress, LinearProgress, Chip, Avatar,
  List, ListItem, ListItemIcon, ListItemText
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Person as PersonIcon,
  PersonAdd as PersonAddIcon,
  LocalFireDepartment as LocalFireDepartmentIcon,
  Grain as GrainIcon,
  MedicalServices as MedicalIcon,
  CalendarToday as CalendarTodayIcon,
  Storage as DataIcon
} from '@mui/icons-material';
import config from '../../config/environment';

interface AnalyticsViewProps {
  viewMode: 'individual' | 'cohort';
  selectedPatient?: string;
  groupingCriteria?: string;
}

const OverviewDashboard: React.FC<AnalyticsViewProps> = ({ 
  viewMode, 
  selectedPatient, 
  groupingCriteria 
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetchOverviewData();
  }, [viewMode, selectedPatient, groupingCriteria]);

  const fetchOverviewData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        view_mode: viewMode,
        group_by: groupingCriteria || 'diabetes_type'
      });

      if (viewMode === 'individual' && selectedPatient) {
        params.append('patient_id', selectedPatient);
      }

      const response = await fetch(`${config.API_URL}/admin/analytics/overview?${params}`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch overview data');
      }
      
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch overview data:', error);
      setLoading(false);
    }
  };

  const getViewModeDescription = () => {
    if (viewMode === 'individual') {
      return selectedPatient 
        ? `Individual analysis for patient ${selectedPatient}`
        : 'Please select a patient to view individual analytics';
    }
    return `Cohort analysis grouped by ${groupingCriteria?.replace('_', ' ')}`;
  };

  const getIconForStat = (iconName: string) => {
    const iconMap: { [key: string]: React.ReactElement } = {
      'people': <PeopleIcon />,
      'person_add': <PersonAddIcon />,
      'trending_up': <TrendingUpIcon />,
      'check_circle': <CheckCircleIcon />,
      'assignment': <AssignmentIcon />,
      'local_fire_department': <LocalFireDepartmentIcon />,
      'grain': <GrainIcon />,
      'person': <PersonIcon />,
      'medical': <MedicalIcon />,
      'calendar': <CalendarTodayIcon />,
      'data': <DataIcon />
    };
    return iconMap[iconName] || <AnalyticsIcon />;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="error">
        Failed to load overview data.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        📊 Overview Dashboard
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        {getViewModeDescription()}
      </Alert>

      {/* Key Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {data.stats?.map((stat: any, index: number) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ 
              background: `linear-gradient(135deg, ${stat.color}22, ${stat.color}11)`,
              border: `1px solid ${stat.color}33`
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: stat.color, mr: 2 }}>
                    {getIconForStat(stat.icon)}
                  </Avatar>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: stat.color }}>
                      {stat.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stat.label}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Current Alerts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📈 Analytics Summary
              </Typography>
              <Typography variant="body1" paragraph>
                This overview provides a high-level view of patient health metrics, engagement patterns, 
                and compliance trends. Use the tabs above to drill down into specific analytical areas.
              </Typography>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Available Analytics Categories:
                </Typography>
                <Grid container spacing={1}>
                  {[
                    'Nutrient Adequacy Analysis',
                    'Engagement & Usage Metrics', 
                    'Outlier & Risk Detection',
                    'Behavioral Pattern Clustering',
                    'Compliance Monitoring'
                  ].map((category, index) => (
                    <Grid item key={index}>
                      <Chip label={category} variant="outlined" size="small" />
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🚨 Recent Alerts
              </Typography>
              <List dense>
                {data.alerts?.map((alert: any, index: number) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemIcon>
                      {alert.severity === 'warning' && <WarningIcon color="warning" />}
                      {alert.severity === 'success' && <CheckCircleIcon color="success" />}
                      {alert.severity === 'info' && <AnalyticsIcon color="info" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary={alert.message}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {loading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress />
        </Box>
      )}
    </Box>
  );
};

export default OverviewDashboard; 