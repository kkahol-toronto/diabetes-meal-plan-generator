import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
} from '@mui/material';
import { Psychology, Analytics } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import config from '../config/environment';

interface Patient {
  id: string;
  name: string;
  phone: string;
  condition: string;
  registration_code: string;
  created_at: string;
}

const AdminPanel: React.FC = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [newPatient, setNewPatient] = useState({
    name: '',
    phone: '',
    condition: '',
  });
  const [adminTimezone, setAdminTimezone] = useState<string>('UTC');

  // Function to format phone number
  const formatPhoneNumber = (phone: string) => {
    // Remove all non-digit characters
    const cleaned = phone.replace(/\D/g, '');
    
    // Check if it's a 10-digit number
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    
    // If not 10 digits, return original
    return phone;
  };

  useEffect(() => {
    // Detect admin's timezone on component mount
    const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    setAdminTimezone(detectedTimezone);
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await fetch(`${config.API_URL}/admin/patients`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Sort patients by created_at in descending order (newest first)
        const sortedPatients = data.sort((a: Patient, b: Patient) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setPatients(sortedPatients);
      } else {
        navigate('/admin/login');
      }
    } catch (err) {
      setError('Failed to fetch patients');
    }
  };

  const handleCreatePatient = async () => {
    try {
      const response = await fetch(`${config.API_URL}/admin/create-patient`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(newPatient),
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(`${data.message} (Registration Code: ${data.registration_code})`);
        setOpenDialog(false);
        setNewPatient({ name: '', phone: '', condition: '' });
        fetchPatients();
      } else {
        const errorData = await response.json();
        // Handle FastAPI validation errors
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `${err.loc[1]}: ${err.msg}`).join(', ');
          setError(errorMessages);
        } else {
          setError(errorData.detail || 'Failed to create patient');
        }
      }
    } catch (err) {
      setError('Failed to create patient');
    }
  };

  const handleResendCode = async (patientId: string) => {
    try {
      const response = await fetch(`${config.API_URL}/admin/resend-code/${patientId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(data.message);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to resend code');
      }
    } catch (err) {
      setError('Failed to resend code');
    }
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setNewPatient(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      console.log(`[DEBUG] Original timestamp: ${timestamp}`);
      console.log(`[DEBUG] Admin timezone: ${adminTimezone}`);
      
      // Ensure the timestamp is treated as UTC by adding Z if it doesn't have it
      let utcTimestamp = timestamp;
      if (!timestamp.endsWith('Z') && !timestamp.includes('+')) {
        utcTimestamp = timestamp + 'Z';
      }
      
      const date = new Date(utcTimestamp);
      console.log(`[DEBUG] Parsed date: ${date.toISOString()}`);
      
      const formatted = date.toLocaleString('en-US', { 
        timeZone: adminTimezone,
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
        hour12: true
      });
      
      console.log(`[DEBUG] Formatted result: ${formatted}`);
      return formatted;
    } catch (error) {
      console.error(`[DEBUG] Error formatting timestamp: ${error}`);
      return timestamp; // Fallback to original timestamp if parsing fails
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1">
            Admin Panel
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<Analytics />}
              onClick={() => navigate('/admin/pias-corner')}
            >
              Pia's Corner
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={() => setOpenDialog(true)}
            >
              Create New Patient
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>Condition</TableCell>
                <TableCell>Registration Code</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {patients.map((patient) => (
                <TableRow key={patient.id}>
                  <TableCell>{patient.name}</TableCell>
                  <TableCell>{formatPhoneNumber(patient.phone)}</TableCell>
                  <TableCell>{patient.condition}</TableCell>
                  <TableCell>{patient.registration_code}</TableCell>
                  <TableCell>{formatTimestamp(patient.created_at)}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Button
                        variant="outlined"
                        color="primary"
                        size="small"
                        onClick={() => handleResendCode(patient.id)}
                      >
                        Resend Code
                      </Button>
                      <Button
                        variant="contained"
                        color="secondary"
                        size="small"
                        onClick={() => navigate(`/admin/patient/${patient.registration_code}`)}
                      >
                        View Profile
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
          <DialogTitle>Create New Patient</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Name"
              name="name"
              value={newPatient.name}
              onChange={handleChange}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Phone Number"
              name="phone"
              value={newPatient.phone}
              onChange={handleChange}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Condition"
              name="condition"
              value={newPatient.condition}
              onChange={handleChange}
              margin="normal"
              required
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
            <Button onClick={handleCreatePatient} variant="contained" color="primary">
              Create
            </Button>
          </DialogActions>
        </Dialog>

        <Snackbar
          open={!!success}
          autoHideDuration={6000}
          onClose={() => setSuccess(null)}
        >
          <Alert severity="success" onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        </Snackbar>
      </Paper>
    </Container>
  );
};

export default AdminPanel; 