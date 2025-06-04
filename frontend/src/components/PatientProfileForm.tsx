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
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { PatientProfile } from '../types/PatientProfile';
import axios from 'axios';

interface SectionProps {
    title: string;
    children: React.ReactNode;
    expanded: boolean;
    onToggle: () => void;
}

const Section: React.FC<SectionProps> = ({ title, children, expanded, onToggle }) => (
    <Card sx={{ mb: 2 }}>
        <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                    {title}
                </Typography>
                <IconButton onClick={onToggle}>
                    {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
            </Box>
            <Collapse in={expanded}>
                {children}
            </Collapse>
        </CardContent>
    </Card>
);

const PatientProfileForm: React.FC = () => {
    const [profile, setProfile] = useState<PatientProfile>({});
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
        // Fetch existing profile data
        const fetchProfile = async () => {
            try {
                const response = await axios.get('/api/profile/get');
                if (response.data.profile) {
                    setProfile(response.data.profile);
                }
            } catch (error) {
                console.error('Error fetching profile:', error);
            }
        };
        fetchProfile();
    }, []);

    const handleSectionToggle = (section: string) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await axios.post('/api/profile/save', profile);
            // Handle successful save (e.g., show success message, redirect)
        } catch (error) {
            console.error('Error saving profile:', error);
            // Handle error (e.g., show error message)
        }
    };

    const handleChange = (field: string, value: any) => {
        setProfile(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleNestedChange = (section: string, field: string, value: any) => {
        setProfile(prev => {
            const sectionValue = prev[section as keyof PatientProfile];
            const safeSection = (sectionValue && typeof sectionValue === 'object') ? sectionValue : {};
            return {
                ...prev,
                [section]: {
                    ...safeSection,
                    [field]: value
                }
            };
        });
    };

    return (
        <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
            <Typography variant="h4" gutterBottom>
                Patient Profile
            </Typography>

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
                            type="number"
                            label="Height (cm)"
                            value={profile.vitalSigns?.heightCm || ''}
                            onChange={(e) => handleNestedChange('vitalSigns', 'heightCm', parseFloat(e.target.value))}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            type="number"
                            label="Weight (kg)"
                            value={profile.vitalSigns?.weightKg || ''}
                            onChange={(e) => handleNestedChange('vitalSigns', 'weightKg', parseFloat(e.target.value))}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Dietary Information Section */}
            <Section
                title="Dietary Information"
                expanded={expandedSections.dietary}
                onToggle={() => handleSectionToggle('dietary')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl fullWidth>
                            <FormLabel>Diet Type</FormLabel>
                            <Select
                                value={profile.dietaryInfo?.dietType || ''}
                                onChange={(e) => handleNestedChange('dietaryInfo', 'dietType', e.target.value)}
                            >
                                <MenuItem value="Omnivore">Omnivore</MenuItem>
                                <MenuItem value="Vegetarian">Vegetarian</MenuItem>
                                <MenuItem value="Vegan">Vegan</MenuItem>
                                <MenuItem value="Keto">Keto</MenuItem>
                                <MenuItem value="Other">Other</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            {/* Physical Activity Section */}
            <Section
                title="Physical Activity"
                expanded={expandedSections.activity}
                onToggle={() => handleSectionToggle('activity')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl component="fieldset">
                            <FormLabel>Work Activity Level</FormLabel>
                            <RadioGroup
                                value={profile.physicalActivity?.workActivityLevel || ''}
                                onChange={(e) => handleNestedChange('physicalActivity', 'workActivityLevel', e.target.value)}
                            >
                                <FormControlLabel value="Sedentary" control={<Radio />} label="Sedentary" />
                                <FormControlLabel value="Moderate" control={<Radio />} label="Moderate" />
                                <FormControlLabel value="Physical Labor" control={<Radio />} label="Physical Labor" />
                            </RadioGroup>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            {/* Lifestyle Section */}
            <Section
                title="Lifestyle & Preferences"
                expanded={expandedSections.lifestyle}
                onToggle={() => handleSectionToggle('lifestyle')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl fullWidth>
                            <FormLabel>Meal Preparation Method</FormLabel>
                            <Select
                                value={profile.lifestyle?.mealPrepMethod || ''}
                                onChange={(e) => handleNestedChange('lifestyle', 'mealPrepMethod', e.target.value)}
                            >
                                <MenuItem value="Own">Own</MenuItem>
                                <MenuItem value="Assisted">Assisted</MenuItem>
                                <MenuItem value="Caregiver">Caregiver</MenuItem>
                                <MenuItem value="Delivery">Delivery</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            {/* Goals Section */}
            <Section
                title="Goals & Readiness"
                expanded={expandedSections.goals}
                onToggle={() => handleSectionToggle('goals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl component="fieldset">
                            <FormLabel>Readiness to Change</FormLabel>
                            <RadioGroup
                                value={profile.readiness || ''}
                                onChange={(e) => handleChange('readiness', e.target.value)}
                            >
                                <FormControlLabel value="Not ready" control={<Radio />} label="Not ready" />
                                <FormControlLabel value="Thinking about it" control={<Radio />} label="Thinking about it" />
                                <FormControlLabel value="Getting started" control={<Radio />} label="Getting started" />
                                <FormControlLabel value="Already making changes" control={<Radio />} label="Already making changes" />
                            </RadioGroup>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    size="large"
                >
                    Save Profile
                </Button>
            </Box>
        </Box>
    );
};

export default PatientProfileForm; 