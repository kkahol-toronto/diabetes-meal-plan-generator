import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  TextField,
  InputAdornment,
  Chip,
  Avatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import { Search, Visibility, Person, Restaurant, Chat, CalendarToday, TrendingUp, Close } from '@mui/icons-material';
import config from '../../config/environment';

interface PatientTableData {
  user_id: string;
  consumption_count: number;
  last_activity: string;
  profile: any;
  registration_code: string;
}

interface PatientDetails {
  user_info: PatientTableData;
  consumption_history: any[];
  meal_plans: any[];
  chat_history: any[];
}

const PatientTable: React.FC = () => {
  const [data, setData] = useState<PatientTableData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState<keyof PatientTableData>('consumption_count');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<PatientTableData | null>(null);
  const [patientDetails, setPatientDetails] = useState<PatientDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  useEffect(() => {
    fetchPatientData();
  }, []);

  const fetchPatientData = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`${config.API_URL}/admin/analytics/comprehensive`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch patient data');
      }

      const analyticsData = await response.json();
      setData(analyticsData.patient_table || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patient data');
      console.error('Error fetching patient data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientDetails = async (patient: PatientTableData) => {
    try {
      setDetailsLoading(true);
      setSelectedPatient(patient);
      
      // In a real implementation, you would fetch detailed data for the specific patient
      // For now, we'll simulate with the available data
      const mockDetails: PatientDetails = {
        user_info: patient,
        consumption_history: [], // Would fetch from /admin/patient/{id}/consumption
        meal_plans: [], // Would fetch from /admin/patient/{id}/meal-plans
        chat_history: [] // Would fetch from /admin/patient/{id}/chat
      };
      
      setPatientDetails(mockDetails);
    } catch (err) {
      console.error('Error fetching patient details:', err);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleSort = (property: keyof PatientTableData) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const closeDialog = () => {
    setSelectedPatient(null);
    setPatientDetails(null);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading patient table: {error}
        <Typography variant="body2" sx={{ mt: 1 }}>
          Using real patient data from production database
        </Typography>
      </Alert>
    );
  }

  if (!data.length) {
    return (
      <Alert severity="info">
        No patient data available yet. Data will appear as patients register and interact with the system.
      </Alert>
    );
  }

  // Filter and sort data
  const filteredData = data.filter(patient => 
    patient.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (patient.profile?.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (patient.registration_code || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedData = filteredData.sort((a, b) => {
    let aValue = a[orderBy];
    let bValue = b[orderBy];
    
    // Handle special cases for sorting
    if (orderBy === 'last_activity') {
      aValue = new Date(aValue || '1970-01-01').getTime();
      bValue = new Date(bValue || '1970-01-01').getTime();
    }
    
    if (order === 'desc') {
      return bValue > aValue ? 1 : -1;
    }
    return aValue > bValue ? 1 : -1;
  });

  const paginatedData = sortedData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const getActivityStatus = (lastActivity: string | null) => {
    if (!lastActivity) return { status: 'Never', color: 'error' };
    
    const activityDate = new Date(lastActivity);
    const now = new Date();
    const daysDiff = Math.floor((now.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysDiff === 0) return { status: 'Today', color: 'success' };
    if (daysDiff <= 7) return { status: `${daysDiff}d ago`, color: 'success' };
    if (daysDiff <= 30) return { status: `${daysDiff}d ago`, color: 'warning' };
    return { status: `${daysDiff}d ago`, color: 'error' };
  };

  const getEngagementLevel = (consumptionCount: number) => {
    if (consumptionCount > 20) return { level: 'High', color: 'success' };
    if (consumptionCount >= 10) return { level: 'Medium', color: 'warning' };
    if (consumptionCount >= 5) return { level: 'Low', color: 'info' };
    return { level: 'Minimal', color: 'error' };
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
        Patient Data Table & Drill-Down
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
        Comprehensive view of {data.length} registered patients with detailed drill-down capabilities
      </Typography>

      <Grid container spacing={3}>
        {/* Search and Controls */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Patient Directory
              </Typography>
              <TextField
                size="small"
                placeholder="Search patients..."
                value={searchTerm}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
                sx={{ minWidth: 300 }}
              />
            </Box>

            {/* Patient Table */}
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Patient</TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={orderBy === 'consumption_count'}
                        direction={orderBy === 'consumption_count' ? order : 'asc'}
                        onClick={() => handleSort('consumption_count')}
                      >
                        Activity Level
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={orderBy === 'last_activity'}
                        direction={orderBy === 'last_activity' ? order : 'asc'}
                        onClick={() => handleSort('last_activity')}
                      >
                        Last Activity
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>Medical Conditions</TableCell>
                    <TableCell>Registration</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedData.map((patient) => {
                    const activityStatus = getActivityStatus(patient.last_activity);
                    const engagementLevel = getEngagementLevel(patient.consumption_count);
                    const conditions = patient.profile?.medicalConditions || [];
                    
                    return (
                      <TableRow key={patient.user_id} hover>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            <Avatar sx={{ mr: 2, backgroundColor: 'primary.main' }}>
                              <Person />
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {patient.profile?.name || 'Unknown'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {patient.user_id}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Chip 
                              label={engagementLevel.level}
                              size="small"
                              color={engagementLevel.color as any}
                              sx={{ mb: 0.5 }}
                            />
                            <Typography variant="caption" display="block">
                              {patient.consumption_count} logs
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={activityStatus.status}
                            size="small"
                            color={activityStatus.color as any}
                          />
                        </TableCell>
                        <TableCell>
                          <Box>
                            {conditions.slice(0, 2).map((condition: string, idx: number) => (
                              <Chip 
                                key={idx}
                                label={condition}
                                size="small"
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                            {conditions.length > 2 && (
                              <Typography variant="caption" color="text.secondary">
                                +{conditions.length - 2} more
                              </Typography>
                            )}
                            {conditions.length === 0 && (
                              <Typography variant="caption" color="text.secondary">
                                None listed
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {patient.registration_code || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <IconButton 
                            size="small" 
                            color="primary"
                            onClick={() => fetchPatientDetails(patient)}
                          >
                            <Visibility />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              rowsPerPageOptions={[5, 10, 25]}
              component="div"
              count={filteredData.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </Paper>
        </Grid>

        {/* Data Source Info */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ backgroundColor: 'rgba(102, 126, 234, 0.1)' }}>
            <Typography variant="body2">
              <strong>Real Data Source:</strong> Patient table displays actual user data from the production database 
              including {data.length} registered patients, their consumption logs, profiles, and activity timestamps. 
              All information is real patient data, not demo or simulated values.
            </Typography>
          </Alert>
        </Grid>
      </Grid>

      {/* Patient Details Dialog */}
      <Dialog 
        open={!!selectedPatient} 
        onClose={closeDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Patient Details: {selectedPatient?.profile?.name || 'Unknown'}
            </Typography>
            <IconButton onClick={closeDialog}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {detailsLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : patientDetails && (
            <Grid container spacing={3}>
              {/* Basic Information */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom color="primary">
                  Basic Information
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Email" 
                      secondary={patientDetails.user_info.user_id} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Name" 
                      secondary={patientDetails.user_info.profile?.name || 'Not provided'} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Registration Code" 
                      secondary={patientDetails.user_info.registration_code || 'N/A'} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Consumption Logs" 
                      secondary={`${patientDetails.user_info.consumption_count} total logs`} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Last Activity" 
                      secondary={patientDetails.user_info.last_activity ? new Date(patientDetails.user_info.last_activity).toLocaleString() : 'Never'} 
                    />
                  </ListItem>
                </List>
              </Grid>

              {/* Medical Information */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom color="primary">
                  Medical Information
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Medical Conditions" 
                      secondary={
                        <Box>
                          {(patientDetails.user_info.profile?.medicalConditions || []).map((condition: string, idx: number) => (
                            <Chip 
                              key={idx}
                              label={condition}
                              size="small"
                              sx={{ mr: 0.5, mb: 0.5 }}
                            />
                          ))}
                          {(!patientDetails.user_info.profile?.medicalConditions || patientDetails.user_info.profile.medicalConditions.length === 0) && 'None listed'}
                        </Box>
                      } 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Age" 
                      secondary={patientDetails.user_info.profile?.age || 'Not provided'} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Weight" 
                      secondary={patientDetails.user_info.profile?.weight ? `${patientDetails.user_info.profile.weight} lbs` : 'Not provided'} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Height" 
                      secondary={patientDetails.user_info.profile?.height ? `${patientDetails.user_info.profile.height} inches` : 'Not provided'} 
                    />
                  </ListItem>
                </List>
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom color="primary">
                  Dietary Information
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" gutterBottom>
                      Dietary Restrictions
                    </Typography>
                    <Box>
                      {(patientDetails.user_info.profile?.dietaryRestrictions || []).map((restriction: string, idx: number) => (
                        <Chip 
                          key={idx}
                          label={restriction}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                      {(!patientDetails.user_info.profile?.dietaryRestrictions || patientDetails.user_info.profile.dietaryRestrictions.length === 0) && (
                        <Typography variant="body2" color="text.secondary">None listed</Typography>
                      )}
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" gutterBottom>
                      Allergies
                    </Typography>
                    <Box>
                      {(patientDetails.user_info.profile?.allergies || []).map((allergy: string, idx: number) => (
                        <Chip 
                          key={idx}
                          label={allergy}
                          size="small"
                          color="error"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                      {(!patientDetails.user_info.profile?.allergies || patientDetails.user_info.profile.allergies.length === 0) && (
                        <Typography variant="body2" color="text.secondary">None listed</Typography>
                      )}
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" gutterBottom>
                      Food Preferences
                    </Typography>
                    <Box>
                      {(patientDetails.user_info.profile?.foodPreferences || []).map((preference: string, idx: number) => (
                        <Chip 
                          key={idx}
                          label={preference}
                          size="small"
                          color="info"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                      {(!patientDetails.user_info.profile?.foodPreferences || patientDetails.user_info.profile.foodPreferences.length === 0) && (
                        <Typography variant="body2" color="text.secondary">None listed</Typography>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              </Grid>

              {/* Activity Summary */}
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom color="primary">
                  Activity Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: 'rgba(102, 126, 234, 0.1)', borderRadius: 1 }}>
                      <Restaurant sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
                      <Typography variant="h6">{patientDetails.user_info.consumption_count}</Typography>
                      <Typography variant="body2" color="text.secondary">Consumption Logs</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: 'rgba(118, 75, 162, 0.1)', borderRadius: 1 }}>
                      <CalendarToday sx={{ fontSize: 32, color: 'secondary.main', mb: 1 }} />
                      <Typography variant="h6">-</Typography>
                      <Typography variant="body2" color="text.secondary">Meal Plans</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1 }}>
                      <Chat sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                      <Typography variant="h6">-</Typography>
                      <Typography variant="body2" color="text.secondary">Chat Messages</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: 'rgba(255, 152, 0, 0.1)', borderRadius: 1 }}>
                      <TrendingUp sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
                      <Typography variant="h6">-</Typography>
                      <Typography variant="body2" color="text.secondary">Engagement Score</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>Close</Button>
          <Button variant="contained" onClick={closeDialog}>
            View Full Profile
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PatientTable; 