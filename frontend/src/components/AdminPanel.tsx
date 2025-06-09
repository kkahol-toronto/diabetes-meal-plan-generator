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
  IconButton,
  Tooltip,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { useNavigate, Link } from 'react-router-dom';

interface Patient {
  id: string;
  name: string;
  phone: string;
  condition: string;
  registration_code: string;
  created_at: string;
  email?: string; // Optional email field that will be populated
}

const AdminPanel = () => {
  console.log('AdminPanel component rendered');
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState<{open: boolean, patient: Patient | null}>({
    open: false,
    patient: null
  });
  const [newPatient, setNewPatient] = useState({
    name: '',
    phone: '',
    condition: '',
  });

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await fetch('http://localhost:8000/admin/patients', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPatients(data);
      } else {
        navigate('/admin/login');
      }
    } catch (err) {
      setError('Failed to fetch patients');
    }
  };

  const checkForDuplicates = (phone: string, email?: string) => {
    const duplicatePhone = patients.find(p => p.phone === phone);
    const duplicateEmail = email ? patients.find(p => p.email === email && p.email !== 'Not registered') : null;
    
    if (duplicatePhone) {
      return `A patient with phone number ${phone} already exists: ${duplicatePhone.name}`;
    }
    
    if (duplicateEmail) {
      return `A patient with email ${email} already exists: ${duplicateEmail.name}`;
    }
    
    return null;
  };

  const handleCreatePatient = async () => {
    try {
      // Check for duplicates before sending to backend
      const duplicateError = checkForDuplicates(newPatient.phone);
      if (duplicateError) {
        setError(duplicateError);
        return;
      }

      const response = await fetch('http://localhost:8000/admin/create-patient', {
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

  const handleDeletePatient = async (patient: Patient) => {
    try {
      const response = await fetch(`http://localhost:8000/admin/patients/${patient.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(data.message);
        setDeleteDialog({ open: false, patient: null });
        fetchPatients();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete patient');
      }
    } catch (err) {
      setError('Failed to delete patient');
    }
  };

  const handleResendCode = async (patientId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/admin/resend-code/${patientId}`, {
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

  const handleRowClick = (patient: Patient, event: React.MouseEvent) => {
    // Don't navigate if clicking on action buttons
    if ((event.target as HTMLElement).closest('button') || (event.target as HTMLElement).closest('a')) {
      return;
    }
    
    const isRegistered = patient.email && patient.email !== 'Not registered' && patient.email !== 'Error fetching email';
    if (isRegistered) {
      navigate(`/admin/users/${patient.id}`);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1">
            Admin Panel
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => setOpenDialog(true)}
          >
            Create New Patient
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>💡 Tips:</strong>
          </Typography>
          <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
            <li>Click on a registered patient's row to view and edit their profile</li>
            <li>Only patients who have registered with their email can have profiles viewed</li>
            <li>Phone numbers and email addresses must be unique - duplicates are not allowed</li>
            <li>Use the delete button (🗑️) to permanently remove patients and all their data</li>
          </ul>
        </Alert>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Condition</TableCell>
                <TableCell>Registration Code</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {patients.map((patient) => {
                const isRegistered = patient.email && patient.email !== 'Not registered' && patient.email !== 'Error fetching email';
                
                return (
                  <TableRow 
                    key={patient.id}
                    onClick={(event) => handleRowClick(patient, event)}
                    sx={{ 
                      cursor: isRegistered ? 'pointer' : 'default',
                      opacity: isRegistered ? 1 : 0.6,
                      '&:hover': isRegistered ? {
                        backgroundColor: 'rgba(0, 0, 0, 0.04)',
                      } : {}
                    }}
                  >
                    <TableCell>{patient.name}</TableCell>
                    <TableCell>{patient.phone}</TableCell>
                    <TableCell>
                      <span style={{ 
                        color: isRegistered ? 'inherit' : '#666',
                        fontStyle: isRegistered ? 'normal' : 'italic'
                      }}>
                        {patient.email || 'Not registered'}
                      </span>
                    </TableCell>
                    <TableCell>{patient.condition}</TableCell>
                    <TableCell>{patient.registration_code}</TableCell>
                    <TableCell>
                      {new Date(patient.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        {isRegistered ? (
                          <Link to={`/admin/users/${patient.id}`} style={{ textDecoration: 'none' }}>
                            <Button size="small" variant="outlined">
                              Edit
                            </Button>
                          </Link>
                        ) : (
                          <span style={{ color: '#666', fontStyle: 'italic', fontSize: '0.875rem' }}>
                            Not registered
                          </span>
                        )}
                        <Tooltip title="Delete Patient">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeleteDialog({ open: true, patient });
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Create Patient Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
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
              helperText="Phone numbers must be unique"
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

        {/* Delete Confirmation Dialog */}
        <Dialog 
          open={deleteDialog.open} 
          onClose={() => setDeleteDialog({ open: false, patient: null })}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Confirm Delete</DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete patient <strong>{deleteDialog.patient?.name}</strong>?
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              This will permanently delete:
            </Typography>
            <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
              <li>Patient record</li>
              <li>Associated profile data</li>
              <li>User account (if registered)</li>
            </ul>
            <Typography variant="body2" color="error" sx={{ mt: 2 }}>
              <strong>This action cannot be undone.</strong>
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialog({ open: false, patient: null })}>
              Cancel
            </Button>
            <Button 
              onClick={() => deleteDialog.patient && handleDeletePatient(deleteDialog.patient)} 
              variant="contained" 
              color="error"
            >
              Delete
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