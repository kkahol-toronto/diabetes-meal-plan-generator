import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    Checkbox,
    FormControl,
    FormControlLabel,
    FormGroup,
    FormHelperText,
    FormLabel,
    Grid,
    MenuItem,
    Radio,
    RadioGroup,
    Select,
    Switch,
    TextField,
    Typography,
    Collapse,
    IconButton,
    Alert,
    CircularProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { PatientProfile } from '../types/PatientProfile';
import axios from 'axios';

interface AdminProfileFormProps {
    userId: string;
}

interface SectionProps {
    title: string;
    children: React.ReactNode;
    expanded: boolean;
    onToggle: () => void;
}

const Section: React.FC<SectionProps> = ({ title, children, expanded, onToggle }) => (
    <Card sx={{ mb: 2 }}>
        <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h6">{title}</Typography>
                <IconButton onClick={onToggle}>
                    {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
            </Box>
            <Collapse in={expanded}>
                <Box mt={2}>{children}</Box>
            </Collapse>
        </CardContent>
    </Card>
);

const AdminProfileForm: React.FC<AdminProfileFormProps> = ({ userId }) => {
    const [profile, setProfile] = useState<PatientProfile>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({
        demographics: true,
        medical: true,
        vitals: true,
        dietary: true,
        activity: true,
        lifestyle: true,
        goals: true,
    });

    useEffect(() => {
        fetchProfile();
    }, [userId]);

    const fetchProfile = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.get(`/admin/profile/${userId}`);
            if (response.data.profile) {
                setProfile(response.data.profile);
            }
        } catch (error) {
            console.error('Error fetching profile:', error);
            setError('Failed to load profile. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleSectionToggle = (section: string) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoading(true);
            setError(null);
            setSuccess(null);
            
            console.log('Original profile data:', profile);
            
            // Clean the profile data - remove empty strings and null values for optional fields
            const cleanedProfile = Object.entries(profile).reduce((acc, [key, value]) => {
                // Keep all non-empty values
                if (value !== '' && value !== null && value !== undefined) {
                    // For arrays, keep them even if empty (they might be intentionally empty)
                    if (Array.isArray(value)) {
                        acc[key] = value;
                    }
                    // For objects, only include if they have meaningful content
                    else if (typeof value === 'object' && value !== null) {
                        const cleanedObj = Object.entries(value).reduce((objAcc, [objKey, objValue]) => {
                            if (objValue !== '' && objValue !== null && objValue !== undefined) {
                                objAcc[objKey] = objValue;
                            }
                            return objAcc;
                        }, {} as any);
                        // Include the object even if empty (for proper structure)
                        acc[key] = cleanedObj;
                    } else {
                        acc[key] = value;
                    }
                }
                return acc;
            }, {} as any);
            
            console.log('Cleaned profile data:', cleanedProfile);
            console.log('Required fields check:');
            console.log('- fullName:', cleanedProfile.fullName);
            console.log('- dateOfBirth:', cleanedProfile.dateOfBirth);
            console.log('- sex:', cleanedProfile.sex);
            
            // Only validate required fields for completely new/empty profiles
            // Let the backend handle validation and merging for existing profiles
            const hasAnyData = Object.keys(cleanedProfile).length > 0;
            
            if (!hasAnyData) {
                setError('Please fill in at least one field before saving.');
                return;
            }
            
            console.log('Sending cleaned profile data to backend:', cleanedProfile);
            const response = await axios.post(`/admin/profile/${userId}`, cleanedProfile);
            console.log('Backend response:', response.data);
            setSuccess('Profile saved successfully');
        } catch (error: any) {
            console.error('Error saving profile:', error);
            console.error('Error response:', error.response?.data);
            if (error.response?.data?.detail) {
                setError(`Failed to save profile: ${error.response.data.detail}`);
            } else {
                setError('Failed to save profile. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (field: string, value: any) => {
        setProfile(prev => ({
            ...prev,
            [field]: value
        }));
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box component="form" onSubmit={handleSubmit}>
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}
            {success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                    {success}
                </Alert>
            )}

            {/* Demographics Section */}
            <Section
                title="Demographics"
                expanded={expandedSections.demographics}
                onToggle={() => handleSectionToggle('demographics')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Full Name"
                            value={profile.fullName || ''}
                            onChange={(e) => handleChange('fullName', e.target.value)}
                            helperText={`Last updated by: ${profile.fullNameUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Date of Birth"
                            type="date"
                            value={profile.dateOfBirth || ''}
                            onChange={(e) => handleChange('dateOfBirth', e.target.value)}
                            InputLabelProps={{ shrink: true }}
                            helperText={`Last updated by: ${profile.dateOfBirthUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                            <FormLabel>Sex</FormLabel>
                            <RadioGroup
                                value={profile.sex || ''}
                                onChange={(e) => handleChange('sex', e.target.value)}
                            >
                                <FormControlLabel value="Male" control={<Radio />} label="Male" />
                                <FormControlLabel value="Female" control={<Radio />} label="Female" />
                                <FormControlLabel value="Other" control={<Radio />} label="Other" />
                            </RadioGroup>
                            <FormHelperText>
                                Last updated by: {profile.sexUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            {/* Medical History Section */}
            <Section
                title="Medical History"
                expanded={expandedSections.medical}
                onToggle={() => handleSectionToggle('medical')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl component="fieldset">
                            <FormLabel>Medical Conditions</FormLabel>
                            <FormGroup>
                                {['Type 1 Diabetes', 'Type 2 Diabetes', 'Hypertension', 'Heart Disease'].map((condition) => (
                                    <FormControlLabel
                                        key={condition}
                                        control={
                                            <Checkbox
                                                checked={profile.medicalHistory?.includes(condition) || false}
                                                onChange={(e) => {
                                                    const newHistory = e.target.checked
                                                        ? [...(profile.medicalHistory || []), condition]
                                                        : (profile.medicalHistory || []).filter(c => c !== condition);
                                                    handleChange('medicalHistory', newHistory);
                                                }}
                                            />
                                        }
                                        label={condition}
                                    />
                                ))}
                            </FormGroup>
                            <FormHelperText>
                                Last updated by: {profile.medicalHistoryUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            {/* Vital Signs Section */}
            <Section
                title="Vital Signs"
                expanded={expandedSections.vitals}
                onToggle={() => handleSectionToggle('vitals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Height (cm)"
                            type="number"
                            value={profile.vitalSigns?.heightCm || ''}
                            onChange={(e) => handleChange('vitalSigns', {
                                ...profile.vitalSigns,
                                heightCm: parseFloat(e.target.value)
                            })}
                            helperText={`Last updated by: ${profile.vitalSignsUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Weight (kg)"
                            type="number"
                            value={profile.vitalSigns?.weightKg || ''}
                            onChange={(e) => handleChange('vitalSigns', {
                                ...profile.vitalSigns,
                                weightKg: parseFloat(e.target.value)
                            })}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Lab Values Section */}
            <Section
                title="Lab Values"
                expanded={expandedSections.vitals}
                onToggle={() => handleSectionToggle('vitals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="A1C (%)"
                            type="number"
                            value={profile.labValues?.a1c || ''}
                            onChange={(e) => handleChange('labValues', {
                                ...profile.labValues,
                                a1c: parseFloat(e.target.value)
                            })}
                            helperText={`Last updated by: ${profile.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Fasting Glucose (mg/dL)"
                            type="number"
                            value={profile.labValues?.fastingGlucose || ''}
                            onChange={(e) => handleChange('labValues', {
                                ...profile.labValues,
                                fastingGlucose: parseFloat(e.target.value)
                            })}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Submit Button */}
            <Box mt={3} display="flex" justifyContent="flex-end">
                <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    disabled={loading}
                >
                    {loading ? 'Saving...' : 'Save Profile'}
                </Button>
            </Box>
        </Box>
    );
};

export default AdminProfileForm; 