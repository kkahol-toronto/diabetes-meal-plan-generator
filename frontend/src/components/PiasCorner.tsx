import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  ButtonBase,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,

  IconButton,

  Tabs,
  Tab,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  TextField
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TableChartIcon from '@mui/icons-material/TableChart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WarningIcon from '@mui/icons-material/Warning';
import RefreshIcon from '@mui/icons-material/Refresh';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';

import DashboardIcon from '@mui/icons-material/Dashboard';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import TrendingUpOutlinedIcon from '@mui/icons-material/TrendingUpOutlined';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import GroupIcon from '@mui/icons-material/Group';
import PersonIcon from '@mui/icons-material/Person';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
} from 'chart.js';
import { Bar, Pie, Line, Scatter } from 'react-chartjs-2';
import config from '../config/environment';
import { formatLocalYMD, parseLocalYMD } from '../utils/timezone';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
);

// Types for the API response
interface PatientInfo {
  user_id: string;
  user_name: string;
}

interface DetailedPatientInfo {
  user_id: string;
  user_name: string;
  registration_code: string;
  phone: string;
  condition: string;
  is_active: boolean;
}

interface AnalysisPeriod {
  days: number;
  total_records_analyzed: number;
  start_date: string;
  end_date: string;
}

interface CohortAverages {
  daily_averages: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;

    sodium: number;
    sugar: number;
  };
  vs_rda: {
    protein_deficit: number;

    sodium_excess: number;
  };
}

interface DeficiencyAnalysis {
  top_deficiencies: Array<{
    issue: string;
    percentage: number;
    severity: string;
    affected_patients: number;
    recommendation?: string;
  }>;
  summary: {

    patients_with_excess_sodium: number;
    patients_with_excess_sugar: number;
    patients_with_low_protein: number;
  };
}

interface Recommendations {
  priority_actions: string[];
  monitoring_focus: string[];
}

interface NutrientAdequacyData {
  cohort_size: number;
  total_registered_patients: number;
  total_registered_users: number;
  inactive_patients_count: number;
  inactive_patients: PatientInfo[];
  active_patients: PatientInfo[];
  all_registered_patients: DetailedPatientInfo[];
  analysis_period: AnalysisPeriod;
  cohort_averages: CohortAverages;
  rda_compliance: {
    [key: string]: {
      adequate?: {
        count: number;
        percentage: number;
      };
      low?: {
        count: number;
        percentage: number;
      };
      high?: {
        count: number;
        percentage: number;
      };
    };
  };
  deficiency_analysis: DeficiencyAnalysis;
  recommendations: Recommendations;
  generated_at: string;
}

// Engagement metrics interfaces
interface UserEngagementAnalysis {
  user_id: string;
  user_name: string;
  total_logs: number;
  active_days: number;
  avg_logs_per_day: number;
  weekly_logs_avg: number;
  engagement_level: string;
  last_log_date: string | null;
  days_since_last_log: number;
}

interface DailyMetric {
  date: string;
  active_users: number;
  total_logs: number;
  avg_logs_per_user: number;
}

interface EngagementSummary {
  excellent: number;
  good: number;
  fair: number;
  poor: number;
  critical: number;
  inactive: number;
}

interface EngagementTrend {
  period: string;
  direction: string;
  percentage_change: number;
}

interface EngagementMetricsData {
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
  };
  daily_metrics: DailyMetric[];
  user_engagement_details: UserEngagementAnalysis[];
  engagement_summary: EngagementSummary;
  engagement_trend: EngagementTrend;
}

// Outlier detection interfaces
interface PatternInfo {
  pattern_type: string;
  severity: string;
  duration_days: number;
  recommendations: string[];
}

interface AnalysisPeriodInfo {
  days_analyzed: number;
  total_records: number;
  avg_daily_calories: number;
}

interface MedicalClassification {
  critical_patients: number;
  urgent_patients: number;
  concern_patients: number;
  normal_patients: number;
  chronic_malnutrition_cases: number;
}

interface PatientProfile {
  user_id: string;
  user_name: string;
  medical_priority: number;
  chronic_risk?: boolean;
  total_days_analyzed: number;
  outlier_days: number;
  chronic_malnutrition_risk: boolean;
  binge_eating_pattern: boolean;
  pattern_type: string;
  // Legacy fields for backwards compatibility
  pattern_info?: PatternInfo;
  analysis_period?: AnalysisPeriodInfo;
}

interface OutlierDetectionData {
  analysis_period: {
    days: number;
    total_patients_analyzed: number;
    total_food_records: number;
  };
  medical_classification: MedicalClassification;
  outliers: {
    extreme_calorie_outliers: any[];
    nutrient_spike_outliers: any[];
    patient_profiles: PatientProfile[];
  };
  summary: {
    total_outlier_days: number;
    most_common_outlier: string;
    patients_affected: number;
  };
  recommendations: {
    immediate_attention: string[];
    monitoring_required: string[];
  };
  generated_at: string;
}

// Behavior clusters interfaces
interface BehaviorPatient {
  user_id: string;
  user_name: string;
  analysis_days: number;
  has_diabetes: boolean;
  behavior_score?: number;
  avg_daily_calories: number;
  avg_protein_percentage?: number;
  avg_carb_percentage?: number;
  high_protein_low_carb_score?: number;
  night_eating_days?: number;
  night_eating_frequency?: number;
  night_eating_severity?: string;
  under_reporting_severity?: string;
  avg_calorie_deficit?: number;
  health_outcomes: {
    weight_management: string;
    diabetes_impact: string;
    sleep_quality?: string;
    nutritional_status?: string;
    data_reliability?: string;
  };
  medical_notes?: string;
}

interface ClusterSummary {
  high_protein_low_carb_count: number;
  night_eaters_count: number;
  under_reporters_count: number;
  multiple_behaviors: number;
  total_clustered_patients: number;
}

interface BehaviorClusters {
  high_protein_low_carb: BehaviorPatient[];
  night_eaters: BehaviorPatient[];
  under_reporters: BehaviorPatient[];
}

interface BehaviorClustersData {
  analysis_period: {
    days: number;
    total_patients_analyzed: number;
  };
  cluster_summary: ClusterSummary;
  behavior_clusters: BehaviorClusters;
  health_outcomes: any;
  medical_insights: {
    priority_interventions: string[];
    positive_patterns: string[];
    monitoring_recommendations: string[];
  };
  generated_at: string;
}

// Compliance patient profile interface
interface CompliancePatientProfile {
  user_id: string;
  user_name: string;
  medical_condition: string;
  is_diabetic: boolean;
  analysis_days: number;
  logged_days: number;
  logging_compliance_rate: number;
  calorie_compliance_rate: number;
  nutrient_compliance_rate: number;
  overall_compliance_rate: number;
  compliance_category: 'high' | 'medium' | 'low';
  compliance_issues: string[];
  strengths: string[];
  recommendations: string[];
}

// Compliance Tracking interfaces - rebuilt from scratch to match backend API exactly
interface ComplianceTrackingData {
  total_registered_patients: number;
  total_registered_users: number;
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
    total_patients_analyzed: number;
  };
  compliance_summary: {
    high_compliance_count: number;
    medium_compliance_count: number;
    low_compliance_count: number;
    high_compliance_percentage: number;
    medium_compliance_percentage: number;
    low_compliance_percentage: number;
  };
  compliance_averages: {
    avg_logging_compliance: number;
    avg_calorie_compliance: number;
    avg_nutrient_compliance: number;
    avg_overall_compliance: number;
  };
  compliance_categories: {
    high_compliance: CompliancePatientProfile[];
    medium_compliance: CompliancePatientProfile[];
    low_compliance: CompliancePatientProfile[];
  };
  diabetic_analysis: {
    total_diabetic_patients: number;
    diabetic_high_compliance: number;
    diabetic_medium_compliance: number;
    diabetic_low_compliance: number;
  };
  compliance_targets: any; // Can define later if needed
  medical_insights: {
    medical_alerts: string[];
    priority_actions: string[];
  };
  generated_at: string;
}

// Patient Directory interfaces - rebuilt from scratch to match backend API exactly
interface PatientSummary {
  user_id: string;
  user_name: string;
  registration_code: string;
  medical_condition: string;
  is_diabetic: boolean;
  analysis_period: {
    total_days: number;
    logged_days: number;
    missing_days: number;
  };
  daily_averages: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;

    sodium: number;
    sugar: number;
  };
  target_compliance: {
    days_within_calorie_target: number;
    days_missed_calorie_target: number;
    calorie_target_compliance_rate: number;
    days_within_nutrient_targets: number;
    days_missed_nutrient_targets: number;
    nutrient_target_compliance_rate: number;
    overall_compliance_rate: number;
  };
  logging_metrics: {
    daily_average_log_count: number;
    most_active_day: string;
    least_active_day: string;
    logging_consistency: string;
  };
  health_indicators: {
    status: string;
    risk_level: string;
    recommendations: string[];
  };
}

// Enhanced Analytics interfaces
interface EnhancedAnalyticsData {
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
    total_records: number;
    active_days: number;
  };
  nutrient_trends: Array<{
    date: string;
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;

    sugar: number;
    sodium: number;
  }>;
  meal_timing_patterns: {
    breakfast: number;
    lunch: number;
    dinner: number;
    snack: number;
  };
  micronutrient_analysis: {
    [key: string]: {
      average: number;
      count: number;
      total: number;
    };
  };
  food_group_distribution: {
    [key: string]: number;
  };
  generated_at: string;
}

// Individual Patient Nutrition interfaces
interface IndividualPatientNutrition {
  patient_email: string;
  patient_name: string;
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
    total_records: number;
    active_days: number;
  };
  daily_averages: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;

    sugar: number;
    sodium: number;
  };
  nutrient_trends: Array<{
    date: string;
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;

    sugar: number;
    sodium: number;
  }>;
  meal_patterns: {
    [key: string]: number;
  };
  food_frequency: {
    [key: string]: {
      count: number;
      total_calories: number;
    };
  };
  rda_compliance: {

    sodium: number;
    sugar: number;
    protein: number;
  };
  medical_insights: string[];
  generated_at: string;
}

// Patient option for dropdown
interface PatientOption {
  email: string;
  name: string;
  registration_code: string;
}

// Individual Patient Engagement interfaces
interface PatientEngagementData {
  patient_email: string;
  patient_name: string;
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
    total_records: number;
  };
  daily_logging_timeline: Array<{
    date: string;
    total_logs: number;
    logs: Array<{
      time: string;
      hour: number;
      food_name: string;
      meal_type: string;
      timestamp: string;
    }>;
    first_log_time: string | null;
    last_log_time: string | null;
  }>;
  meal_timing_patterns: {
    [key: string]: {
      average_time: string;
      frequency: number;
      consistency: number;
    };
  };
  engagement_metrics: {
    total_logs: number;
    active_days: number;
    logging_streak: number;
    consistency_score: number;
    avg_logs_per_day: number;
  };
  eating_behavior_insights: string[];
  medical_risk_flags: string[];
  generated_at: string;
}

interface PatientDirectoryData {
  total_patients: number;
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
    total_records_analyzed: number;
  };
  summary_statistics: {
    patients_with_data: number;
    patients_without_data: number;
    avg_daily_calories: number;
    avg_compliance_rate: number;
    avg_logging_rate: number;
    risk_distribution: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
  patient_summaries: PatientSummary[];
  medical_insights: string[];
  compliance_targets: any; // We can define this later if needed
  generated_at: string;
}

const PiasCorner: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [data, setData] = useState<NutrientAdequacyData | null>(null);
  const [engagementData, setEngagementData] = useState<EngagementMetricsData | null>(null);
  const [outlierData, setOutlierData] = useState<OutlierDetectionData | null>(null);
  const [behaviorData, setBehaviorData] = useState<BehaviorClustersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [engagementLoading, setEngagementLoading] = useState(true);
  const [outlierLoading, setOutlierLoading] = useState(true);
  const [behaviorLoading, setBehaviorLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [engagementError, setEngagementError] = useState<string | null>(null);
  const [outlierError, setOutlierError] = useState<string | null>(null);
  const [behaviorError, setBehaviorError] = useState<string | null>(null);
  const [analysisPeriod, setAnalysisPeriod] = useState(30);
  const [activeTab, setActiveTab] = useState(0);
  
  // Set active tab based on URL parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const tabParam = urlParams.get('tab');
    if (tabParam && !isNaN(parseInt(tabParam))) {
      setActiveTab(parseInt(tabParam));
    }
  }, [location.search]);
  
  // Enhanced analytics state
  const [enhancedAnalyticsData, setEnhancedAnalyticsData] = useState<EnhancedAnalyticsData | null>(null);
  const [enhancedAnalyticsLoading, setEnhancedAnalyticsLoading] = useState(true);
  const [enhancedAnalyticsError, setEnhancedAnalyticsError] = useState<string | null>(null);
  
  // Patient-specific analysis state
  const [selectedPatient, setSelectedPatient] = useState<PatientOption | null>(null);
  const [patientNutritionData, setPatientNutritionData] = useState<IndividualPatientNutrition | null>(null);
  const [patientNutritionLoading, setPatientNutritionLoading] = useState(false);
  const [patientNutritionError, setPatientNutritionError] = useState<string | null>(null);

  // Patient engagement states
  const [selectedEngagementPatient, setSelectedEngagementPatient] = useState<PatientOption | null>(null);
  const [patientEngagementData, setPatientEngagementData] = useState<PatientEngagementData | null>(null);
  const [patientEngagementLoading, setPatientEngagementLoading] = useState(false);
  const [patientEngagementError, setPatientEngagementError] = useState<string | null>(null);
  const [availablePatients, setAvailablePatients] = useState<PatientOption[]>([]);
  
  // Patient list modal state
  const [patientListModal, setPatientListModal] = useState<{
    open: boolean;
    title: string;
    patients: PatientInfo[] | UserEngagementAnalysis[];
    detailedPatients: DetailedPatientInfo[];
    type: 'total' | 'active' | 'inactive' | 'records' | 'excellent_engagement' | 'good_engagement' | 'fair_engagement' | 'poor_engagement' | 'critical_engagement' | 'inactive_engagement';
  }>({
    open: false,
    title: '',
    patients: [],
    detailedPatients: [],
    type: 'total'
  });

  // Behavioral clustering modal state
  const [behaviorModal, setBehaviorModal] = useState<{
    open: boolean;
    title: string;
    patients: BehaviorPatient[];
    type: 'high_protein_low_carb' | 'night_eaters' | 'under_reporters' | 'multiple_behaviors';
  }>({
    open: false,
    title: '',
    patients: [],
    type: 'high_protein_low_carb'
  });

  // Compliance patient modal state
  const [complianceModal, setComplianceModal] = useState<{
    open: boolean;
    title: string;
    patients: CompliancePatientProfile[];
    type: 'high' | 'medium' | 'low';
  }>({
    open: false,
    title: '',
    patients: [],
    type: 'high'
  });
  
  // Patient Directory state - rebuilt from scratch
  const [patientDirectoryData, setPatientDirectoryData] = useState<PatientDirectoryData | null>(null);
  const [patientDirectoryLoading, setPatientDirectoryLoading] = useState(true);
  const [patientDirectoryError, setPatientDirectoryError] = useState<string | null>(null);

  // Compliance Tracking state - rebuilt from scratch
  const [complianceTrackingData, setComplianceTrackingData] = useState<ComplianceTrackingData | null>(null);
  const [complianceTrackingLoading, setComplianceTrackingLoading] = useState(true);
  const [complianceTrackingError, setComplianceTrackingError] = useState<string | null>(null);

  const handleBackToAdmin = () => {
    navigate('/admin');
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleOpenPatientList = (
    type: 'total' | 'active' | 'inactive' | 'records' | 'excellent_engagement' | 'good_engagement' | 'fair_engagement' | 'poor_engagement' | 'critical_engagement' | 'inactive_engagement',
    title: string,
    patients: PatientInfo[] | UserEngagementAnalysis[],
    detailedPatients?: DetailedPatientInfo[]
  ) => {
    setPatientListModal({
      open: true,
      title,
      patients,
      detailedPatients: detailedPatients || [],
      type
    });
  };

  const handleClosePatientList = () => {
    setPatientListModal({
      open: false,
      title: '',
      patients: [],
      detailedPatients: [],
      type: 'total'
    });
  };

  // Behavioral clustering modal handlers
  const handleOpenBehaviorModal = (
    type: 'high_protein_low_carb' | 'night_eaters' | 'under_reporters' | 'multiple_behaviors',
    title: string,
    patients: BehaviorPatient[]
  ) => {
    setBehaviorModal({
      open: true,
      title,
      patients,
      type
    });
  };

  const handleCloseBehaviorModal = () => {
    setBehaviorModal({
      open: false,
      title: '',
      patients: [],
      type: 'high_protein_low_carb'
    });
  };

  // Compliance modal handlers
  const handleOpenComplianceModal = (
    type: 'high' | 'medium' | 'low',
    title: string,
    patients: CompliancePatientProfile[]
  ) => {
    setComplianceModal({
      open: true,
      title,
      patients,
      type
    });
  };

  const handleCloseComplianceModal = () => {
    setComplianceModal({
      open: false,
      title: '',
      patients: [],
      type: 'high'
    });
  };

  const fetchNutrientAdequacyData = useCallback(async () => {

    try {
      setLoading(true);
      setError(null);
      const url = `${config.API_URL}/admin/pias-corner/nutrient-adequacy?days=${analysisPeriod}`;

      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });



      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`Failed to fetch nutrient adequacy data: ${response.status} ${errorText}`);
      }

      const result: NutrientAdequacyData = await response.json();

      setData(result);
    } catch (err) {
      console.error('=== ERROR FETCHING NUTRIENT ADEQUACY ===');
      console.error('Error details:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [analysisPeriod]);

  const fetchEngagementMetrics = useCallback(async () => {
    try {
      setEngagementLoading(true);
      setEngagementError(null);
      const response = await fetch(`${config.API_URL}/admin/pias-corner/engagement-metrics?days=${analysisPeriod}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch engagement metrics data');
      }

      const result: EngagementMetricsData = await response.json();
      setEngagementData(result);
    } catch (err) {
      console.error('Error fetching engagement metrics data:', err);
      setEngagementError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setEngagementLoading(false);
    }
  }, [analysisPeriod]);

  const fetchOutlierDetection = useCallback(async () => {
    try {
      setOutlierLoading(true);
      setOutlierError(null);
      const response = await fetch(`${config.API_URL}/admin/pias-corner/outliers?days=${analysisPeriod}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch outlier detection data');
      }

      const result: OutlierDetectionData = await response.json();
      setOutlierData(result);
    } catch (err) {
      console.error('Error fetching outlier detection data:', err);
      setOutlierError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setOutlierLoading(false);
    }
  }, [analysisPeriod]);

  const fetchBehaviorClusters = useCallback(async () => {
    try {
      setBehaviorLoading(true);
      setBehaviorError(null);
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/behavior-clusters?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch behavior clusters data');
      }

      const result: BehaviorClustersData = await response.json();
      setBehaviorData(result);
    } catch (err) {
      console.error('Error fetching behavior clusters data:', err);
      setBehaviorError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setBehaviorLoading(false);
    }
  }, [analysisPeriod]);

  // Compliance Tracking fetch function - rebuilt from scratch
  const fetchComplianceTracking = useCallback(async () => {
    try {
      setComplianceTrackingLoading(true);
      setComplianceTrackingError(null);
      
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/compliance?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch compliance tracking data');
      }

      const result: ComplianceTrackingData = await response.json();
      setComplianceTrackingData(result);
    } catch (err) {
      console.error('❌ Error fetching compliance tracking:', err);
      setComplianceTrackingError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setComplianceTrackingLoading(false);
    }
  }, [analysisPeriod]);

  // Patient Directory fetch function - rebuilt from scratch
  const fetchPatientDirectory = useCallback(async () => {
    try {
      setPatientDirectoryLoading(true);
      setPatientDirectoryError(null);
      
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/patients-summary?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch patient directory data');
      }

      const result: PatientDirectoryData = await response.json();
      setPatientDirectoryData(result);
    } catch (err) {
      console.error('❌ Error fetching patient directory:', err);
      setPatientDirectoryError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setPatientDirectoryLoading(false);
    }
  }, [analysisPeriod]);
  
  // Enhanced Analytics fetch function
  const fetchEnhancedAnalytics = useCallback(async () => {
    try {
      setEnhancedAnalyticsLoading(true);
      setEnhancedAnalyticsError(null);
      
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/enhanced-analytics?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch enhanced analytics data');
      }

      const result: EnhancedAnalyticsData = await response.json();
      setEnhancedAnalyticsData(result);
    } catch (err) {
      console.error('❌ Error fetching enhanced analytics:', err);
      setEnhancedAnalyticsError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setEnhancedAnalyticsLoading(false);
    }
  }, [analysisPeriod]);
  
  // Fetch available patients for dropdown
  const fetchAvailablePatients = useCallback(async () => {
    try {
      const response = await fetch(`${config.API_URL}/admin/patients`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch patients');
      }

      const patients = await response.json();
      
      // Get user emails for each patient by registration code
      const patientOptions: PatientOption[] = [];
      
      for (const patient of patients) {
        // Try to find user email using the patient data we already have
        // We'll use the all_registered_patients from the main data which has email mappings
        if (data?.all_registered_patients) {
          const matchingUser = data.all_registered_patients.find(
            p => p.registration_code === patient.registration_code
          );
          if (matchingUser) {
            patientOptions.push({
              email: matchingUser.user_id,
              name: patient.name || matchingUser.user_name,
              registration_code: patient.registration_code
            });
          }
        }
      }
      
      setAvailablePatients(patientOptions);
    } catch (err) {
      console.error('❌ Error fetching available patients:', err);
    }
  }, [data?.all_registered_patients]);
  
  // Individual Patient Nutrition fetch function
  const fetchPatientNutrition = useCallback(async (patientEmail: string) => {
    if (!patientEmail) return;
    
    try {
      setPatientNutritionLoading(true);
      setPatientNutritionError(null);
      
      // URL encode the email
      const encodedEmail = encodeURIComponent(patientEmail);
      
      const response = await fetch(
        `${config.API_URL}/admin/pias-corner/patient-nutrition/${encodedEmail}?days=${analysisPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch patient nutrition data');
      }

      const result: IndividualPatientNutrition = await response.json();
      setPatientNutritionData(result);
    } catch (err) {
      console.error('❌ Error fetching patient nutrition:', err);
      setPatientNutritionError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setPatientNutritionLoading(false);
    }
  }, [analysisPeriod]);

  // Fetch individual patient engagement data
  const fetchPatientEngagementData = useCallback(async (patientEmail: string) => {
    setPatientEngagementLoading(true);
    setPatientEngagementError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`${config.API_URL}/admin/pias-corner/patient-engagement/${encodeURIComponent(patientEmail)}?days=${analysisPeriod}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch patient engagement data');
      }

      const result: PatientEngagementData = await response.json();
      setPatientEngagementData(result);
    } catch (err) {
      console.error('❌ Error fetching patient engagement:', err);
      setPatientEngagementError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setPatientEngagementLoading(false);
    }
  }, [analysisPeriod]);

  useEffect(() => {
    fetchNutrientAdequacyData();
    
    fetchEngagementMetrics();
    fetchOutlierDetection();
    fetchBehaviorClusters();
    fetchComplianceTracking();
    fetchPatientDirectory();
    fetchEnhancedAnalytics();
    

  }, [analysisPeriod, fetchNutrientAdequacyData, fetchEngagementMetrics, fetchOutlierDetection, fetchBehaviorClusters, fetchComplianceTracking, fetchPatientDirectory, fetchEnhancedAnalytics]);
  
  // Fetch available patients when data is loaded
  useEffect(() => {
    if (data?.all_registered_patients) {
      fetchAvailablePatients();
    }
  }, [data?.all_registered_patients, fetchAvailablePatients]);
  
  // Fetch individual patient data when patient is selected
  useEffect(() => {
    if (selectedPatient) {
      fetchPatientNutrition(selectedPatient.email);
    } else {
      setPatientNutritionData(null);
    }
  }, [selectedPatient, fetchPatientNutrition]);

  // Chart generation functions
  const generatePopulationAveragesChart = () => {
    // Use patient-specific data if patient is selected, otherwise use population data
    let dailyAverages;
    
    if (selectedPatient && patientNutritionData) {
      dailyAverages = patientNutritionData.daily_averages;
    } else if (data?.cohort_averages?.daily_averages) {
      dailyAverages = data.cohort_averages.daily_averages;
    } else {
      return null;
    }
    
    return {
      labels: ['Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sodium (g)', 'Sugar (g)'],
      datasets: [{
        label: 'Daily Average',
        data: [
          dailyAverages.protein || 0,
          dailyAverages.carbohydrates || 0,
          dailyAverages.fat || 0,
          (dailyAverages.sodium || 0) / 1000, // Convert mg to grams for display
          dailyAverages.sugar || 0
        ],
        backgroundColor: [
          '#FF6384', // Red for Protein
          '#36A2EB', // Blue for Carbs
          '#FFCE56', // Yellow for Fat
          '#9966FF', // Purple for Sodium
          '#FF9F40'  // Orange for Sugar
        ],
        borderColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#9966FF',
          '#FF9F40'
        ],
        borderWidth: 2,
      }]
    };
  };

  const generateComplianceHeatmapChart = () => {
    const RDA = {
      calories: { min: 1800, max: 2200 },
      protein: { min: 50, max: 100 },
      carbohydrates: { min: 130, max: 300 },
      fat: { min: 44, max: 78 },

      sodium: { max: 2300 },
      sugar: { max: 50 },
    } as const;

    const desiredOrder = ['calories','protein','carbohydrates','fat','sodium','sugar'];

    const pctFromRange = (avg: number, min?: number, max?: number) => {
      const safeAvg = Number.isFinite(avg) ? avg : 0;
      const safeMin = Number.isFinite(min as number) ? (min as number) : undefined;
      const safeMax = Number.isFinite(max as number) ? (max as number) : undefined;
      if (safeMin != null && safeMax != null) {
        if (safeAvg >= safeMin && safeAvg <= safeMax) return 100;
        if (safeAvg < safeMin) return Math.max(0, Math.min(100, (safeAvg / safeMin) * 100));
        return Math.max(0, Math.min(100, (safeMax / safeAvg) * 100));
      }
      if (safeMax != null) {
        return Math.max(0, Math.min(100, (safeMax / Math.max(safeAvg, 1e-9)) * 100));
      }
      if (safeMin != null) {
        return Math.max(0, Math.min(100, (safeAvg / safeMin) * 100));
      }
      return 0;
    };

    const compliance = (selectedPatient ? (patientNutritionData as any)?.rda_compliance : (data as any)?.rda_compliance) as Record<string, any> | undefined;
    const cohortAverages = data?.cohort_averages?.daily_averages;
    const deficiencies = data?.deficiency_analysis?.top_deficiencies ?? [];


    const excessSodiumPct = Number(
      deficiencies.find((d: any) => typeof d?.issue === 'string' && d.issue.toLowerCase().includes('excess sodium'))?.percentage ?? NaN
    );
    const excessSugarPct = Number(
      deficiencies.find((d: any) => typeof d?.issue === 'string' && d.issue.toLowerCase().includes('excess sugar'))?.percentage ?? NaN
    );
    const lowProteinPct = Number(
      deficiencies.find((d: any) => typeof d?.issue === 'string' && d.issue.toLowerCase().includes('low protein'))?.percentage ?? NaN
    );

    const values = desiredOrder.map((nutrient) => {


      const adequatePct = compliance && typeof compliance === 'object' ? compliance[nutrient]?.adequate?.percentage : undefined;
      if (Number.isFinite(adequatePct as number)) {

        return (adequatePct as number);
      }


      if (nutrient === 'sodium' && Number.isFinite(excessSodiumPct)) return Math.max(0, 100 - (excessSodiumPct as number));
      if (nutrient === 'sugar' && Number.isFinite(excessSugarPct)) return Math.max(0, 100 - (excessSugarPct as number));
      if (nutrient === 'protein' && Number.isFinite(lowProteinPct)) return Math.max(0, 100 - (lowProteinPct as number));

      const avg = cohortAverages?.[nutrient as keyof typeof cohortAverages] ?? 0;
      const r = (RDA as any)[nutrient] ?? {};
      const fallback = pctFromRange(avg, r.min, r.max);

      return fallback;
    });

    const labelFormat = (n: string) => n === 'carbohydrates' ? 'Carbs' : n.charAt(0).toUpperCase() + n.slice(1);
    const colors = values.map(v => v >= 80 ? '#4CAF50' : v >= 60 ? '#FF9800' : v >= 40 ? '#FF5722' : '#F44336');

    return {
      labels: desiredOrder.map(labelFormat),
      datasets: [{
        label: 'RDA Compliance (%)',
        data: values,
        backgroundColor: colors,
        borderColor: colors,
        borderWidth: 2,
        maxBarThickness: 60,
      }]
    };
  };

  const generateEngagementFunnelChart = () => {
    if (!engagementData) return null;

    const colors = [
      '#4CAF50', // Green - Excellent
      '#2196F3', // Blue - Good
      '#FF9800', // Orange - Fair
      '#FF5722', // Red - Poor
      '#9C27B0', // Purple - Critical
      '#607D8B'  // Blue-Gray - Inactive
    ];

    const borderColors = [
      '#388E3C', // Darker Green - Excellent
      '#1976D2', // Darker Blue - Good
      '#F57C00', // Darker Orange - Fair
      '#D32F2F', // Darker Red - Poor
      '#7B1FA2', // Darker Purple - Critical
      '#455A64'  // Darker Blue-Gray - Inactive
    ];

    return {
      labels: ['Excellent', 'Good', 'Fair', 'Poor', 'Critical', 'Inactive'],
      datasets: [{
        label: 'Number of Patients',
        data: [
          engagementData.engagement_summary.excellent || 0,
          engagementData.engagement_summary.good || 0,
          engagementData.engagement_summary.fair || 0,
          engagementData.engagement_summary.poor || 0,
          engagementData.engagement_summary.critical || 0,
          engagementData.engagement_summary.inactive || 0
        ],
        backgroundColor: colors,
        borderColor: borderColors,
        borderWidth: 2,
        maxBarThickness: 50,
      }]
    };
  };

  const generateEngagementTimeSeriesChart = () => {
    if (!engagementData || !engagementData.daily_metrics?.length) return null;

    // Sort metrics by date to ensure proper chronological order
    const sortedMetrics = [...engagementData.daily_metrics].sort((a, b) => 
      parseLocalYMD(a.date).getTime() - parseLocalYMD(b.date).getTime()
    );

    // Generate complete date range to fill any gaps
    const startDate = parseLocalYMD(sortedMetrics[0].date);
    const endDate = parseLocalYMD(sortedMetrics[sortedMetrics.length - 1].date);
    
    const completeData = [];
    const metricsMap = new Map(sortedMetrics.map(m => [m.date, m]));
    
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      const dateKey = d.toISOString().split('T')[0];
      const metric = metricsMap.get(dateKey);
      
      completeData.push({
        date: dateKey,
        active_users: metric?.active_users || 0,
        label: d.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric' 
        })
      });
    }

    return {
      labels: completeData.map(item => item.label),
      datasets: [{
        label: 'Active Users',
        data: completeData.map(item => item.active_users),
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#2196F3',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      }]
    };
  };

  // Behavior clusters chart generation functions
  const generateBehaviorClustersScatterplot = (): any => {
    if (!behaviorData) return { datasets: [] };

    const { behavior_clusters } = behaviorData;
    const datasets: any[] = [];

    if (behavior_clusters.high_protein_low_carb.length > 0) {
      datasets.push({
        label: 'High Protein - Low Carb',
        data: behavior_clusters.high_protein_low_carb.map((patient, index) => ({
          x: index,
          y: patient.avg_daily_calories ?? 0,
          patientName: patient.user_name,
          analysisDays: patient.analysis_days,
          hasDiabetes: patient.has_diabetes,
          calories: patient.avg_daily_calories ?? 0,
          proteinPercentage: patient.avg_protein_percentage ?? 0,
          carbPercentage: patient.avg_carb_percentage ?? 0,
          score: patient.high_protein_low_carb_score ?? 0,
          clusterType: 'High Protein - Low Carb'
        })),
        backgroundColor: '#4CAF50',
        borderColor: '#388E3C',
        pointRadius: 8,
        pointHoverRadius: 10,
      });
    }

    if (behavior_clusters.night_eaters.length > 0) {
      datasets.push({
        label: 'Night Eaters',
        data: behavior_clusters.night_eaters.map((patient, index) => ({
          x: index + (behavior_clusters.high_protein_low_carb.length || 0),
          y: patient.avg_daily_calories ?? 0,
          patientName: patient.user_name,
          analysisDays: patient.analysis_days,
          hasDiabetes: patient.has_diabetes,
          calories: patient.avg_daily_calories ?? 0,
          nightEatingDays: patient.night_eating_days ?? 0,
          nightEatingFrequency: patient.night_eating_frequency ?? 0,
          severity: patient.night_eating_severity ?? 'unknown',
          clusterType: 'Night Eaters'
        })),
        backgroundColor: '#FF5722',
        borderColor: '#D32F2F',
        pointRadius: 8,
        pointHoverRadius: 10,
      });
    }

    if (behavior_clusters.under_reporters.length > 0) {
      datasets.push({
        label: 'Under-reporters',
        data: behavior_clusters.under_reporters.map((patient, index) => ({
          x: index + (behavior_clusters.high_protein_low_carb.length || 0) + (behavior_clusters.night_eaters.length || 0),
          y: patient.avg_daily_calories ?? 0,
          patientName: patient.user_name,
          analysisDays: patient.analysis_days,
          hasDiabetes: patient.has_diabetes,
          calories: patient.avg_daily_calories ?? 0,
          severity: patient.under_reporting_severity ?? 'unknown',
          calorieDeficit: patient.avg_calorie_deficit ?? 0,
          clusterType: 'Under-reporters'
        })),
        backgroundColor: '#FF9800',
        borderColor: '#F57C00',
        pointRadius: 8,
        pointHoverRadius: 10,
      });
    }

    return { datasets };
  };

  const getBehaviorClustersOptions = (): any => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Patient Behavioral Clusters',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const point = context.raw;
            const baseInfo = [
              `Patient: ${point.patientName}`,
              `Cluster: ${point.clusterType}`,
              `Avg Daily Calories: ${Math.round(point.calories)}`,
              `Analysis Days: ${point.analysisDays}`,
              `Has Diabetes: ${point.hasDiabetes ? 'Yes' : 'No'}`,
            ];

            // Add cluster-specific information
            if (point.clusterType === 'High Protein - Low Carb') {
              baseInfo.push(`Protein %: ${Math.round(point.proteinPercentage)}%`);
              baseInfo.push(`Carb %: ${Math.round(point.carbPercentage)}%`);
              baseInfo.push(`Pattern Score: ${Math.round(point.score)}%`);
            } else if (point.clusterType === 'Night Eaters') {
              baseInfo.push(`Night Eating Days: ${point.nightEatingDays}`);
              baseInfo.push(`Night Eating %: ${Math.round(point.nightEatingFrequency)}%`);
              baseInfo.push(`Severity: ${point.severity}`);
            } else if (point.clusterType === 'Under-reporters') {
              baseInfo.push(`Severity: ${point.severity}`);
              baseInfo.push(`Calorie Deficit: ${Math.round(Math.abs(point.calorieDeficit))}`);
            }

            return baseInfo;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Patient Index',
          font: {
            size: 12,
            weight: 'bold' as const
          }
        },
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Average Daily Calories',
          font: {
            size: 12,
            weight: 'bold' as const
          }
        },
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.1)'
        },
        beginAtZero: true
      }
    }
  });
  
  // Enhanced Analytics Chart Generation Functions
  const generateNutrientTrendsChart = () => {
    const dataSource = selectedPatient ? patientNutritionData : enhancedAnalyticsData;
    if (!dataSource?.nutrient_trends?.length) return null;

    const trends = dataSource.nutrient_trends;
    const labels = trends.map(trend => {
      const date = parseLocalYMD(trend.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    return {
      labels,
      datasets: [
        {
          label: 'Calories',
          data: trends.map(trend => trend.calories),
          borderColor: '#FF6384',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          fill: false,
          tension: 0.4,
          yAxisID: 'y'
        },
        {
          label: 'Protein (g)',
          data: trends.map(trend => trend.protein),
          borderColor: '#36A2EB',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          fill: false,
          tension: 0.4,
          yAxisID: 'y1'
        },
        {
          label: 'Carbs (g)',
          data: trends.map(trend => trend.carbohydrates),
          borderColor: '#FFCE56',
          backgroundColor: 'rgba(255, 206, 86, 0.1)',
          fill: false,
          tension: 0.4,
          yAxisID: 'y1'
        },
        {
          label: 'Fat (g)',
          data: trends.map(trend => trend.fat),
          borderColor: '#4BC0C0',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          fill: false,
          tension: 0.4,
          yAxisID: 'y1'
        }
      ]
    };
  };
  
  const generateMealPatternsChart = () => {
    const dataSource = selectedPatient ? patientNutritionData?.meal_patterns : enhancedAnalyticsData?.meal_timing_patterns;
    if (!dataSource) return null;

    const mealTypes = Object.keys(dataSource);
    const mealCounts = Object.values(dataSource);

    return {
      labels: mealTypes.map(type => type.charAt(0).toUpperCase() + type.slice(1)),
      datasets: [{
        label: 'Number of Meals',
        data: mealCounts,
        backgroundColor: [
          '#FF6384', // Breakfast
          '#36A2EB', // Lunch
          '#FFCE56', // Dinner
          '#4BC0C0'  // Snack
        ],
        borderColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0'
        ],
        borderWidth: 2
      }]
    };
  };
  
  const generateFoodGroupsChart = () => {
    if (selectedPatient) {
      // For individual patients, show top foods instead of food groups
      if (!patientNutritionData?.food_frequency) return null;
      
      const topFoods = Object.entries(patientNutritionData.food_frequency)
        .sort(([, a], [, b]) => b.count - a.count)
        .slice(0, 8);
      
      return {
        labels: topFoods.map(([food]) => food.length > 20 ? food.substring(0, 20) + '...' : food),
        datasets: [{
          label: 'Consumption Count',
          data: topFoods.map(([, data]) => data.count),
          backgroundColor: [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
          ],
          borderWidth: 1
        }]
      };
    } else {
      // For overall analytics, show food groups
      if (!enhancedAnalyticsData?.food_group_distribution) return null;
      
      const foodGroups = enhancedAnalyticsData.food_group_distribution;
      const labels = Object.keys(foodGroups);
      const data = Object.values(foodGroups);
      
      return {
        labels,
        datasets: [{
          label: 'Food Group Distribution',
          data,
          backgroundColor: [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
          ],
          borderWidth: 1
        }]
      };
    }
  };
  


  // Chart options
  const getChartOptions = (title: string, isBarChart: boolean = false) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        display: !isBarChart, // Hide legend for bar charts since colors are meaningful
      },
      title: {
        display: true,
        text: title,
        font: {
          size: 14,
          weight: 'bold' as const
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.parsed?.y ?? context.parsed;
            
            if (isBarChart && title.includes('Compliance')) {
              return `${label}: ${value.toFixed(1)}%`;
            } else if (label.includes('Sodium')) {
              return `${label}: ${value.toFixed(2)}g`;
            } else {
              return `${label}: ${value.toFixed(1)}g`;
            }
          }
        }
      }
    },
    scales: isBarChart ? {
      y: {
        beginAtZero: true,
        max: title.includes('Compliance') ? 100 : undefined,
        title: {
          display: true,
          text: title.includes('Compliance') ? 'Compliance Percentage (%)' : 'Amount (g)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Nutrients'
        }
      }
    } : undefined
  });

  const getFunnelChartOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        display: false, // Hide legend since colors are self-explanatory with labels
      },
      title: {
        display: true,
        text: 'Patient Engagement Levels',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.parsed.y || 0;
            return `${label}: ${value} patient${value !== 1 ? 's' : ''}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Engagement Level'
        }
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Patients'
        },
        ticks: {
          stepSize: 1,
          precision: 0
        }
      }
    },
    elements: {
      bar: {
        borderRadius: 4
      }
    }
  });

  const getEngagementTimeSeriesOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        display: false, // Hide legend for single dataset
      },
      title: {
        display: true,
        text: 'Daily Active Users Trend',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: function(context: any) {
            const value = context.parsed.y || 0;
            return `Active Users: ${value}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        },
        grid: {
          display: false
        },
        ticks: {
          maxTicksLimit: 31, // Show up to 31 days (month view)
          maxRotation: 45, // Rotate labels for better readability
          minRotation: 0,
          autoSkip: false, // Don't skip any labels - show every day
          stepSize: 1 // Show every single day
        }
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Active Users'
        },
        ticks: {
          stepSize: 1,
          precision: 0
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  });
  
  // Enhanced chart options
  const getNutrientTrendsOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: selectedPatient ? `Nutrient Trends - ${selectedPatient.name}` : 'Population Nutrient Trends',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Calories'
        }
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Nutrients (g)'
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    }
  });

  // Helper functions
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return '#f44336';    // Red for high severity
      case 'medium': return '#ff9800';  // Orange for medium severity  
      case 'low': return '#ffeb3b';     // Yellow for low severity
      default: return '#4caf50';        // Green for normal/good
    }
  };

  // Patient Directory functions removed - will be rebuilt from scratch

  if (loading || engagementLoading || outlierLoading || behaviorLoading || complianceTrackingLoading || patientDirectoryLoading || enhancedAnalyticsLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <CircularProgress size={60} sx={{ mb: 2 }} />
          <Typography variant="h6">Loading Pia's Corner Dashboard...</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {loading && ' Loading nutrient analysis...'}
            {engagementLoading && ' Loading engagement metrics...'}
            {outlierLoading && ' Loading outlier detection...'}
            {behaviorLoading && ' Loading behavior analysis...'}
            {complianceTrackingLoading && ' Loading compliance tracking...'}
            {patientDirectoryLoading && ' Loading patient directory...'}
            {enhancedAnalyticsLoading && ' Loading enhanced analytics...'}
          </Typography>
        </Paper>
      </Container>
    );
  }

  if (error || engagementError || outlierError || behaviorError || complianceTrackingError || patientDirectoryError || enhancedAnalyticsError) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Nutrient Data Error: {error}
            </Alert>
          )}
          {engagementError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Engagement Data Error: {engagementError}
            </Alert>
          )}
          {outlierError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Outlier Detection Error: {outlierError}
            </Alert>
          )}
          {behaviorError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Behavior Clusters Error: {behaviorError}
            </Alert>
          )}
          {complianceTrackingError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Compliance Tracking Error: {complianceTrackingError}
            </Alert>
          )}
          {patientDirectoryError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Patient Directory Error: {patientDirectoryError}
            </Alert>
          )}
          {enhancedAnalyticsError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Enhanced Analytics Error: {enhancedAnalyticsError}
            </Alert>
          )}
          {patientNutritionError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Patient Nutrition Error: {patientNutritionError}
            </Alert>
          )}

          <Button
            variant="contained"
            onClick={() => {
              fetchNutrientAdequacyData();
              fetchEngagementMetrics();
              fetchOutlierDetection();
              fetchBehaviorClusters();
              fetchComplianceTracking();
              fetchPatientDirectory();
              fetchEnhancedAnalytics();
            }}
            sx={{ mr: 2 }}
          >
            Retry
          </Button>

        </Paper>
      </Container>
    );
  }

  const populationAveragesData = generatePopulationAveragesChart();
  const complianceHeatmapData = generateComplianceHeatmapChart();
  const engagementFunnelData = generateEngagementFunnelChart();
  const engagementTimeSeriesData = generateEngagementTimeSeriesChart();
  
  // Enhanced analytics chart data
  const nutrientTrendsData = generateNutrientTrendsChart();
  const mealPatternsData = generateMealPatternsChart();
  const foodGroupsData = generateFoodGroupsChart();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={handleBackToAdmin}
              sx={{ minWidth: 'auto' }}
            >
              Back to Admin Panel
            </Button>
            <Typography variant="h4" component="h1">
              Pia's Corner
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Period</InputLabel>
              <Select
                value={analysisPeriod}
                label="Period"
                onChange={(e) => setAnalysisPeriod(Number(e.target.value))}
              >
                <MenuItem value={7}>7 Days</MenuItem>
                <MenuItem value={30}>30 Days</MenuItem>
                <MenuItem value={60}>60 Days</MenuItem>
                <MenuItem value={90}>90 Days</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => {
                fetchNutrientAdequacyData();
                fetchEnhancedAnalytics();
                if (selectedPatient) {
                  fetchPatientNutrition(selectedPatient.email);
                }
              }}
            >
              Refresh
            </Button>
          </Box>
        </Box>

        <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
          Patient Food Analysis & Risk Assessment Dashboard
        </Typography>

        {/* Quick Stats Summary */}
        <Stack direction="row" spacing={2} sx={{ mb: 4, flexWrap: 'wrap' }}>
          <Chip 
            icon={<AnalyticsIcon />}
            label={`${data?.cohort_size || 0} Active Patients`}
            color="primary"
            variant="outlined"
          />
          <Chip 
            label={`${data?.total_registered_patients || 0} Total Patients`}
            color="default"
            variant="outlined"
          />
          <Chip 
            icon={<TableChartIcon />}
            label={`${data?.analysis_period.total_records_analyzed || 0} Food Logs`}
            color="secondary"
            variant="outlined"
          />
          <Chip 
            label={`${data?.analysis_period.days || 0} Day Analysis`}
            variant="outlined"
          />
          {(data?.inactive_patients_count ?? 0) > 0 && (
            <Chip 
              icon={<WarningIcon />}
              label={`${data?.inactive_patients_count ?? 0} Inactive Patients`}
              color="warning"
              variant="outlined"
            />
          )}
        </Stack>

        {/* Navigation Tabs */}
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ 
              borderBottom: 1, 
              borderColor: 'divider',
              '& .MuiTab-root': {
                minHeight: 72,
                textTransform: 'none',
                fontSize: '0.95rem',
                fontWeight: 500
              }
            }}
          >
            <Tab 
              icon={<DashboardIcon />} 
              label="Overview" 
              iconPosition="start"
            />
            <Tab 
              icon={<RestaurantIcon />} 
              label="Nutrition Analysis"
              iconPosition="start"
            />
            <Tab 
              icon={<TrendingUpOutlinedIcon />} 
              label="Patient Engagement" 
              iconPosition="start"
            />
            <Tab 
              icon={
                <Badge 
                  badgeContent={
                    (outlierData?.outliers?.extreme_calorie_outliers?.length ?? 0) + 
                    (outlierData?.outliers?.nutrient_spike_outliers?.length ?? 0)
                  }
                  color="error"
                  max={99}
                >
                  <ReportProblemIcon />
                </Badge>
              } 
              label="Risk Assessment" 
              iconPosition="start"
            />
            <Tab 
              icon={<AssignmentTurnedInIcon />} 
              label="Compliance Tracking" 
              iconPosition="start"
            />
            <Tab 
              icon={<GroupIcon />} 
              label="Patient Directory" 
              iconPosition="start"
            />
          </Tabs>
        </Paper>

        {/* Tab Content */}
        {activeTab === 0 && (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
              🏥 Dashboard Overview
            </Typography>
            <Grid container spacing={3}>
              {/* Key Summary Charts */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6">
                        Population Nutrient Averages
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {populationAveragesData ? (
                        <Pie 
                          data={populationAveragesData} 
                          options={getChartOptions('Daily Nutrient Averages Across Patient Cohort')}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                      <Typography variant="h6">
                        RDA Compliance Levels
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {complianceHeatmapData ? (
                        <Bar 
                          data={complianceHeatmapData} 
                          options={getChartOptions('RDA Compliance by Nutrient (%)', true)}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Critical Deficiencies Alert */}
              <Grid item xs={12}>
                <Card elevation={2} sx={{ bgcolor: '#fff3e0' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <WarningIcon sx={{ mr: 1, color: 'warning.main' }} />
                      <Typography variant="h6" color="warning.main">
                        Top Nutritional Deficiencies
                      </Typography>
                    </Box>
                    {data?.deficiency_analysis?.top_deficiencies ? (
                      <Grid container spacing={2}>
                        {data.deficiency_analysis.top_deficiencies
                          .filter((deficiency: any) => !deficiency.issue?.toLowerCase().includes('fiber'))
                          .slice(0, 4).map((deficiency, index) => (
                          <Grid item xs={12} sm={6} md={3} key={index}>
                            <Box sx={{ 
                              textAlign: 'center', 
                              p: 2, 
                              border: '1px solid', 
                              borderColor: deficiency.severity === 'high' ? 'error.light' : 'warning.light', 
                              borderRadius: 1,
                              bgcolor: deficiency.severity === 'high' ? 'error.light' : 'warning.light',
                              opacity: 0.9
                            }}>
                              <Typography variant="h6" color={deficiency.severity === 'high' ? 'error.dark' : 'warning.dark'} fontWeight="bold">
                                {deficiency.percentage}%
                              </Typography>
                              <Typography variant="body2" fontWeight="medium" sx={{ mb: 1 }}>
                                {deficiency.issue}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {deficiency.affected_patients} patients
                              </Typography>
                              {deficiency.recommendation && (
                                <Typography variant="caption" sx={{ display: 'block', mt: 1, fontStyle: 'italic' }}>
                                  {deficiency.recommendation}
                                </Typography>
                              )}
                            </Box>
                          </Grid>
                        ))}
                      </Grid>
                    ) : (
                      <Typography color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
                        No deficiency data available
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Cohort Statistics */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Cohort Statistics
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={6} sm={3}>
                        <Box 
                          sx={{ 
                            textAlign: 'center', 
                            p: 2, 
                            bgcolor: 'primary.light', 
                            borderRadius: 1,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              bgcolor: 'primary.main',
                              transform: 'translateY(-2px)',
                              boxShadow: 3
                            }
                          }}
                          onClick={() => {
                            const allRegisteredPatients = data?.all_registered_patients || [];
                            handleOpenPatientList('total', 'All Registered Patients', [], allRegisteredPatients);
                          }}
                        >
                          <Typography variant="h4" fontWeight="bold" color="primary.dark">
                            {data?.total_registered_patients}
                          </Typography>
                          <Typography variant="caption" color="primary.dark">Total Patients</Typography>
                          <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8 }}>
                            Click to view list
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box 
                          sx={{ 
                            textAlign: 'center', 
                            p: 2, 
                            bgcolor: 'success.light', 
                            borderRadius: 1,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              bgcolor: 'success.main',
                              transform: 'translateY(-2px)',
                              boxShadow: 3
                            }
                          }}
                          onClick={() => {
                            const activePatients = data?.active_patients || [];
                            handleOpenPatientList('active', 'Active Patients (With Recent Food Logs)', activePatients);
                          }}
                        >
                          <Typography variant="h4" fontWeight="bold" color="success.dark">
                            {data?.cohort_size}
                          </Typography>
                          <Typography variant="caption" color="success.dark">Active Patients</Typography>
                          <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8 }}>
                            Click to view list
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box 
                          sx={{ 
                            textAlign: 'center', 
                            p: 2, 
                            bgcolor: 'secondary.light', 
                            borderRadius: 1,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              bgcolor: 'secondary.main',
                              transform: 'translateY(-2px)',
                              boxShadow: 3
                            }
                          }}
                          onClick={() => {
                            handleOpenPatientList('records', 'Food Records Information', []);
                          }}
                        >
                          <Typography variant="h4" fontWeight="bold" color="secondary.dark">
                            {data?.analysis_period.total_records_analyzed}
                          </Typography>
                          <Typography variant="caption" color="secondary.dark">Food Records</Typography>
                          <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8 }}>
                            Click for details
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box 
                          sx={{ 
                            textAlign: 'center', 
                            p: 2, 
                            bgcolor: data?.inactive_patients_count ? 'warning.light' : 'info.light', 
                            borderRadius: 1,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              bgcolor: data?.inactive_patients_count ? 'warning.main' : 'info.main',
                              transform: 'translateY(-2px)',
                              boxShadow: 3
                            }
                          }}
                          onClick={() => {
                            const inactivePatients = data?.inactive_patients || [];
                            handleOpenPatientList('inactive', 'Inactive Patients (No Recent Food Logs)', inactivePatients);
                          }}
                        >
                          <Typography variant="h4" fontWeight="bold" color={data?.inactive_patients_count ? 'warning.dark' : 'info.dark'}>
                            {data?.inactive_patients_count ?? 0}
                          </Typography>
                          <Typography variant="caption" color={data?.inactive_patients_count ? 'warning.dark' : 'info.dark'}>Inactive Patients</Typography>
                          <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8 }}>
                            Click to view list
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 1 && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">
                🥗 Nutrition Analysis
              </Typography>
              
              {/* Patient Selection Dropdown */}
              <Box sx={{ minWidth: 300 }}>
                <Autocomplete
                  value={selectedPatient}
                  onChange={(event, newValue) => {
                    setSelectedPatient(newValue);
                  }}
                  options={availablePatients}
                  getOptionLabel={(option) => `${option.name} (${option.email})`}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Select Patient (Optional)"
                      placeholder="All Patients (Default)"
                      size="small"
                      helperText={selectedPatient ? 'Showing individual patient data' : 'Showing aggregated data for all patients'}
                    />
                  )}
                  renderOption={(props, option) => (
                    <Box component="li" {...props}>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {option.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {option.email} • {option.registration_code}
                        </Typography>
                      </Box>
                    </Box>
                  )}
                  clearOnEscape
                  loading={patientNutritionLoading}
                />
              </Box>
            </Box>
            
            {/* Patient-specific loading indicator */}
            {patientNutritionLoading && (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2, mb: 2 }}>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Loading patient nutrition data...
                </Typography>
              </Box>
            )}
            
            {/* Patient-specific error */}
            {patientNutritionError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {patientNutritionError}
              </Alert>
            )}
            
            <Grid container spacing={3}>
              {/* Nutrient Trends Over Time - NEW ENHANCED CHART */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                      <Typography variant="h6">
                        {selectedPatient ? `${selectedPatient.name} - Daily Nutrient Trends` : 'Population Daily Nutrient Trends'}
                      </Typography>
                    </Box>
                    <Box sx={{ height: 400 }}>
                      {nutrientTrendsData ? (
                        <Line 
                          data={nutrientTrendsData} 
                          options={getNutrientTrendsOptions()}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No nutrient trend data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Detailed Nutrition Charts */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6">
                        {selectedPatient ? `${selectedPatient.name} - Nutrient Averages` : 'Population Nutrient Averages'}
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {populationAveragesData ? (
                        <Pie 
                          data={populationAveragesData} 
                          options={getChartOptions(
                            selectedPatient 
                              ? `Daily Nutrient Averages - ${selectedPatient.name}` 
                              : 'Daily Nutrient Averages Across Patient Cohort'
                          )}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                      <Typography variant="h6">
                        {selectedPatient ? `${selectedPatient.name} - RDA Compliance` : 'RDA Compliance Levels'}
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {complianceHeatmapData ? (
                        <Bar 
                          data={complianceHeatmapData} 
                          options={getChartOptions('RDA Compliance by Nutrient (%)', true)}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Meal Patterns Chart - NEW ENHANCED CHART */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <RestaurantIcon sx={{ mr: 1, color: 'warning.main' }} />
                      <Typography variant="h6">
                        {selectedPatient ? `${selectedPatient.name} - Meal Patterns` : 'Population Meal Timing Patterns'}
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {mealPatternsData ? (
                        <Bar 
                          data={mealPatternsData} 
                          options={getChartOptions(
                            selectedPatient 
                              ? `Meal Distribution - ${selectedPatient.name}` 
                              : 'Meal Timing Distribution', 
                            true
                          )}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No meal pattern data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Food Groups/Top Foods Chart - NEW ENHANCED CHART */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <GroupIcon sx={{ mr: 1, color: 'info.main' }} />
                      <Typography variant="h6">
                        {selectedPatient ? `${selectedPatient.name} - Top Foods` : 'Food Group Distribution'}
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {foodGroupsData ? (
                        <Pie 
                          data={foodGroupsData} 
                          options={getChartOptions(
                            selectedPatient 
                              ? `Most Consumed Foods - ${selectedPatient.name}` 
                              : 'Food Group Distribution'
                          )}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No food group data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              

              
              {/* Patient-Specific Medical Insights */}
              {selectedPatient && patientNutritionData?.medical_insights && (
                <Grid item xs={12}>
                  <Card elevation={2} sx={{ bgcolor: '#f3e5f5' }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <WarningIcon sx={{ mr: 1, color: 'secondary.main' }} />
                        <Typography variant="h6" color="secondary.main">
                          Medical Insights for {selectedPatient.name}
                        </Typography>
                      </Box>
                      <List dense>
                        {patientNutritionData.medical_insights.map((insight, index) => (
                          <ListItem key={index} sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 32 }}>
                              <FiberManualRecordIcon 
                                sx={{ fontSize: 12, color: 'secondary.main' }} 
                              />
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Typography variant="body2">
                                  {insight}
                                </Typography>
                              }
                            />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Detailed Nutritional Analysis */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'info.main' }} />
                      <Typography variant="h6">
                        {selectedPatient ? `${selectedPatient.name} - Detailed Nutrient Analysis` : 'Detailed Nutrient Intake Analysis'}
                      </Typography>
                    </Box>
                    <Box sx={{ height: 300 }}>
                      {populationAveragesData ? (
                        <Bar 
                          data={populationAveragesData} 
                          options={getChartOptions('Average Daily Intake by Nutrient', true)}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Deficiency Details */}
              <Grid item xs={12}>
                <Card elevation={2} sx={{ bgcolor: '#fff3e0' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <WarningIcon sx={{ mr: 1, color: 'warning.main' }} />
                      <Typography variant="h6" color="warning.main">
                        Detailed Deficiency Analysis
                      </Typography>
                    </Box>
                    <List dense>
                      {data?.deficiency_analysis.top_deficiencies.map((deficiency, index) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <FiberManualRecordIcon 
                              sx={{ 
                                fontSize: 12, 
                                color: getSeverityColor(deficiency.severity)
                              }} 
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" fontWeight="medium">
                                  {deficiency.issue}
                                </Typography>
                                <Chip 
                                  label={`${deficiency.percentage}%`}
                                  size="small"
                                  sx={{ 
                                    bgcolor: getSeverityColor(deficiency.severity),
                                    color: 'white',
                                    fontSize: '0.75rem'
                                  }}
                                />
                              </Box>
                            }
                            secondary={
                              <Typography variant="caption" color="text.secondary">
                                {deficiency.affected_patients} patients affected
                              </Typography>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 2 && (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
              📊 Patient Engagement
            </Typography>

            {/* Individual Patient Analysis Section */}
            <Card elevation={2} sx={{ mb: 3, bgcolor: '#f8f9fa' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">
                    Individual Patient Engagement Analysis
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ minWidth: 120 }}>
                    Select Patient:
                  </Typography>
                  <Autocomplete
                    value={selectedEngagementPatient}
                    onChange={(event: React.SyntheticEvent, newValue: PatientOption | null) => {
                      setSelectedEngagementPatient(newValue);
                      if (newValue) {
                        fetchPatientEngagementData(newValue.email);
                      } else {
                        setPatientEngagementData(null);
                      }
                    }}
                    options={patientDirectoryData?.patient_summaries?.map(p => ({
                      name: p.user_name,
                      email: p.user_id,
                      registration_code: p.registration_code
                    })) || []}
                    getOptionLabel={(option) => option.name}
                    isOptionEqualToValue={(option, value) => option.email === value.email}
                    sx={{ flexGrow: 1, maxWidth: 400 }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Search Patient"
                        variant="outlined"
                        size="small"
                        InputProps={{
                          ...params.InputProps,
                          endAdornment: (
                            <>
                              {patientEngagementLoading ? <CircularProgress color="inherit" size={20} /> : null}
                              {params.InputProps.endAdornment}
                            </>
                          ),
                        }}
                      />
                    )}
                    renderOption={(props, option) => (
                      <Box component="li" {...props}>
                        <Box>
                          <Typography variant="body1" fontWeight="medium">
                            {option.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {option.email} • {option.registration_code}
                          </Typography>
                        </Box>
                      </Box>
                    )}
                    clearOnEscape
                    loading={patientEngagementLoading}
                  />
                </Box>

                {/* Individual Patient Engagement Analysis */}
                {selectedEngagementPatient && patientEngagementData && (
                  <Grid container spacing={3}>
                    {/* Engagement Metrics Cards */}
                    <Grid item xs={12}>
                      <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                        📈 {patientEngagementData.patient_name} - Engagement Metrics
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6} sm={3}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="primary.main" fontWeight="bold">
                              {patientEngagementData.engagement_metrics.total_logs}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Total Food Logs
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="success.main" fontWeight="bold">
                              {patientEngagementData.engagement_metrics.active_days}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Active Days
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="warning.main" fontWeight="bold">
                              {patientEngagementData.engagement_metrics.logging_streak}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Day Streak
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="info.main" fontWeight="bold">
                              {patientEngagementData.engagement_metrics.consistency_score}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Consistency Score
                            </Typography>
                          </Card>
                        </Grid>
                      </Grid>
                    </Grid>

                    {/* Daily Logging Timeline */}
                    <Grid item xs={12} md={8}>
                      <Card elevation={1}>
                        <CardContent>
                          <Typography variant="h6" sx={{ mb: 2 }}>
                            🕒 Daily Food Logging Timeline
                          </Typography>
                          <Box sx={{ height: 300, overflowY: 'auto' }}>
                            {patientEngagementData.daily_logging_timeline.map((day, index) => (
                              <Box key={day.date} sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid #e0e0e0' }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                  <Typography variant="subtitle2" fontWeight="bold">
                                    {formatLocalYMD(day.date, 'en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                                  </Typography>
                                  <Chip size="small" label={`${day.total_logs} logs`} color="primary" />
                                </Box>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                  {day.logs.map((log, logIndex) => (
                                    <Chip
                                      key={logIndex}
                                      size="small"
                                      variant="outlined"
                                      label={`${log.time} - ${log.food_name}`}
                                      color={
                                        log.meal_type === 'breakfast' ? 'success' :
                                        log.meal_type === 'lunch' ? 'primary' :
                                        log.meal_type === 'dinner' ? 'warning' : 'default'
                                      }
                                    />
                                  ))}
                                </Box>
                              </Box>
                            ))}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Meal Timing Patterns */}
                    <Grid item xs={12} md={4}>
                      <Card elevation={1}>
                        <CardContent>
                          <Typography variant="h6" sx={{ mb: 2 }}>
                            ⏰ Meal Timing Patterns
                          </Typography>
                          <Box sx={{ height: 300, overflowY: 'auto' }}>
                            {Object.entries(patientEngagementData.meal_timing_patterns).map(([mealType, pattern]) => (
                              <Box key={mealType} sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid #e0e0e0' }}>
                                <Typography variant="subtitle2" fontWeight="bold" sx={{ textTransform: 'capitalize', mb: 1 }}>
                                  {mealType}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  Average Time: <strong>{pattern.average_time}</strong>
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  Frequency: <strong>{pattern.frequency} times</strong>
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                  <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                                    Consistency:
                                  </Typography>
                                  <Box sx={{ 
                                    width: 60, 
                                    height: 8, 
                                    bgcolor: 'grey.300', 
                                    borderRadius: 1,
                                    position: 'relative'
                                  }}>
                                    <Box sx={{
                                      width: `${pattern.consistency}%`,
                                      height: '100%',
                                      bgcolor: pattern.consistency > 70 ? 'success.main' : pattern.consistency > 40 ? 'warning.main' : 'error.main',
                                      borderRadius: 1
                                    }} />
                                  </Box>
                                  <Typography variant="caption" sx={{ ml: 1 }}>
                                    {Math.round(pattern.consistency)}%
                                  </Typography>
                                </Box>
                              </Box>
                            ))}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Behavior Insights & Risk Flags */}
                    <Grid item xs={12}>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Card elevation={1}>
                            <CardContent>
                              <Typography variant="h6" sx={{ mb: 2, color: 'info.main' }}>
                                💡 Behavioral Insights
                              </Typography>
                              <List dense>
                                {patientEngagementData.eating_behavior_insights.map((insight, index) => (
                                  <ListItem key={index}>
                                    <ListItemText
                                      primary={insight}
                                      primaryTypographyProps={{ variant: 'body2' }}
                                    />
                                  </ListItem>
                                ))}
                                {patientEngagementData.eating_behavior_insights.length === 0 && (
                                  <ListItem>
                                    <ListItemText
                                      primary="No specific behavioral patterns detected"
                                      primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                                    />
                                  </ListItem>
                                )}
                              </List>
                            </CardContent>
                          </Card>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Card elevation={1}>
                            <CardContent>
                              <Typography variant="h6" sx={{ mb: 2, color: 'error.main' }}>
                                ⚠️ Medical Risk Flags
                              </Typography>
                              <List dense>
                                {patientEngagementData.medical_risk_flags.map((flag, index) => (
                                  <ListItem key={index}>
                                    <ListItemText
                                      primary={flag}
                                      primaryTypographyProps={{ variant: 'body2', color: 'error.main' }}
                                    />
                                  </ListItem>
                                ))}
                                {patientEngagementData.medical_risk_flags.length === 0 && (
                                  <ListItem>
                                    <ListItemText
                                      primary="✅ No medical risk flags detected"
                                      primaryTypographyProps={{ variant: 'body2', color: 'success.main' }}
                                    />
                                  </ListItem>
                                )}
                              </List>
                            </CardContent>
                          </Card>
                        </Grid>
                      </Grid>
                    </Grid>
                  </Grid>
                )}

                {selectedEngagementPatient && patientEngagementLoading && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                    <CircularProgress />
                  </Box>
                )}

                {selectedEngagementPatient && patientEngagementError && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {patientEngagementError}
                  </Alert>
                )}

                {!selectedEngagementPatient && (
                  <Box sx={{ textAlign: 'center', p: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      👆 Select a patient above to view their detailed engagement analysis, food logging timeline, meal patterns, and medical insights.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Population-Wide Engagement Overview */}
            <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary' }}>
              📊 Population-Wide Engagement Overview
            </Typography>
            <Grid container spacing={3}>
              {/* Engagement Funnel Chart */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6">
                        Patient Engagement Funnel
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {engagementFunnelData ? (
                        <Bar 
                          data={engagementFunnelData} 
                          options={getFunnelChartOptions()}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No engagement data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Engagement Time Series Chart */}
              <Grid item xs={12} md={6}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                      <Typography variant="h6">
                        Engagement Trends Over Time
                      </Typography>
                    </Box>
                    <Box sx={{ height: 350 }}>
                      {engagementTimeSeriesData ? (
                        <Line 
                          data={engagementTimeSeriesData} 
                          options={getEngagementTimeSeriesOptions()}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                          <Typography>No engagement data available</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Engagement Summary Cards */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                      <TableChartIcon sx={{ mr: 1, color: 'info.main' }} />
                      <Typography variant="h6">
                        Engagement Summary
                      </Typography>
                    </Box>
                    {engagementData && (
                      <Grid container spacing={2}>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card 
                            variant="outlined" 
                            sx={{ 
                              textAlign: 'center', 
                              p: 2,
                              cursor: 'pointer',
                              transition: 'all 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: 2
                              }
                            }}
                            onClick={() => handleOpenPatientList('excellent_engagement', 'Excellent Engagement Patients', engagementData?.user_engagement_details?.filter((u: UserEngagementAnalysis) => u.engagement_level === 'excellent') || [])}
                          >
                            <Typography variant="h4" color="success.main" fontWeight="bold">
                              {engagementData.engagement_summary.excellent ?? 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Excellent
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card 
                            variant="outlined" 
                            sx={{ 
                              textAlign: 'center', 
                              p: 2,
                              cursor: 'pointer',
                              transition: 'all 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: 2
                              }
                            }}
                            onClick={() => handleOpenPatientList('good_engagement', 'Good Engagement Patients', engagementData?.user_engagement_details?.filter((u: UserEngagementAnalysis) => u.engagement_level === 'good') || [])}
                          >
                            <Typography variant="h4" color="info.main" fontWeight="bold">
                              {engagementData.engagement_summary.good ?? 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Good
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card 
                            variant="outlined" 
                            sx={{ 
                              textAlign: 'center', 
                              p: 2,
                              cursor: 'pointer',
                              transition: 'all 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: 2
                              }
                            }}
                            onClick={() => handleOpenPatientList('fair_engagement', 'Fair Engagement Patients', engagementData?.user_engagement_details?.filter((u: UserEngagementAnalysis) => u.engagement_level === 'fair') || [])}
                          >
                            <Typography variant="h4" color="warning.main" fontWeight="bold">
                              {engagementData.engagement_summary.fair ?? 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Fair
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card 
                            variant="outlined" 
                            sx={{ 
                              textAlign: 'center', 
                              p: 2,
                              cursor: 'pointer',
                              transition: 'all 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: 2
                              }
                            }}
                            onClick={() => handleOpenPatientList('poor_engagement', 'Poor Engagement Patients', engagementData?.user_engagement_details?.filter((u: UserEngagementAnalysis) => u.engagement_level === 'poor') || [])}
                          >
                            <Typography variant="h4" color="error.main" fontWeight="bold">
                              {engagementData.engagement_summary.poor ?? 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Poor
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card 
                            variant="outlined" 
                            sx={{ 
                              textAlign: 'center', 
                              p: 2,
                              cursor: 'pointer',
                              transition: 'all 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: 2
                              }
                            }}
                            onClick={() => handleOpenPatientList('critical_engagement', 'Critical Engagement Patients', engagementData?.user_engagement_details?.filter((u: UserEngagementAnalysis) => u.engagement_level === 'critical') || [])}
                          >
                            <Typography variant="h4" color="error.dark" fontWeight="bold">
                              {engagementData.engagement_summary.critical ?? 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Critical
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card 
                            variant="outlined" 
                            sx={{ 
                              textAlign: 'center', 
                              p: 2,
                              cursor: 'pointer',
                              transition: 'all 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: 2
                              }
                            }}
                            onClick={() => handleOpenPatientList('inactive_engagement', 'Inactive Engagement Patients', engagementData?.user_engagement_details?.filter((u: UserEngagementAnalysis) => u.engagement_level === 'inactive') || [])}
                          >
                            <Typography variant="h4" color="action.disabled" fontWeight="bold">
                              {engagementData.engagement_summary.inactive ?? 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Inactive
                            </Typography>
                          </Card>
                        </Grid>
                      </Grid>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 3 && (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
              🚨 Risk Assessment
            </Typography>
            <Grid container spacing={3}>
              {/* Patient Alert Dashboard */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                      <ReportProblemIcon sx={{ mr: 1, color: 'error.main' }} />
                      <Typography variant="h6" fontWeight="bold" color="error.main">
                        High Priority Patient Alerts
                      </Typography>
                    </Box>
                    {outlierLoading && (
                      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
                        <CircularProgress />
                        <Typography sx={{ ml: 2 }}>
                          Analyzing patient risk patterns...
                        </Typography>
                      </Box>
                    )}
                    
                    {outlierError && (
                      <Alert severity="error" sx={{ mb: 2 }}>
                        Error loading risk assessment: {outlierError}
                      </Alert>
                    )}
                    
                    {!outlierLoading && !outlierError && (
                      <>
                        {outlierData?.outliers?.patient_profiles && outlierData.outliers.patient_profiles.length > 0 ? (
                          <Grid container spacing={2}>
                            {outlierData.outliers.patient_profiles.slice(0, 6).map((patient, index) => (
                              <Grid item xs={12} md={6} lg={4} key={index}>
                                <Card 
                                  variant="outlined" 
                                  sx={{ 
                                    bgcolor: patient.chronic_risk ? '#ffebee' : '#fff3e0',
                                    border: `2px solid ${patient.chronic_risk ? '#f44336' : '#ff9800'}`
                                  }}
                                >
                                  <CardContent sx={{ pb: 1 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                      <Typography variant="h6" fontWeight="bold" color={patient.chronic_risk ? 'inherit' : 'error.main'}>
                                        {patient.user_name}
                                      </Typography>
                                      <Chip 
                                        label={`Priority ${patient.medical_priority}`}
                                        color={patient.medical_priority >= 3 ? 'error' : 'warning'}
                                        size="small"
                                      />
                                    </Box>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                      Pattern: {patient.pattern_type || 'Multiple Issues'}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      Analysis: {patient.total_days_analyzed || 0} days
                                    </Typography>
                                  </CardContent>
                                </Card>
                              </Grid>
                            ))}
                          </Grid>
                        ) : (
                          <Alert severity="success" sx={{ mt: 2 }}>
                            <Typography>
                              <strong>No high-risk patients detected</strong> in the current {analysisPeriod}-day analysis period.
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              All patients appear to have healthy eating patterns without concerning outliers or medical risk factors.
                            </Typography>
                          </Alert>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Behavior Clusters */}
              <Grid item xs={12}>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Patient Behavioral Clustering Analysis
                </Typography>
                
                {/* Behavior Cluster Summary Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6} md={3}>
                    <Card 
                      variant="outlined" 
                      sx={{ 
                        textAlign: 'center', 
                        p: 2,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3,
                          borderColor: 'success.main'
                        }
                      }}
                      onClick={() => handleOpenBehaviorModal(
                        'high_protein_low_carb',
                        'High Protein - Low Carb Patients',
                        behaviorData?.behavior_clusters.high_protein_low_carb || []
                      )}
                    >
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1, color: 'success.main' }}>
                        {behaviorData?.cluster_summary.high_protein_low_carb_count ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        High Protein - Low Carb
                      </Typography>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card 
                      variant="outlined" 
                      sx={{ 
                        textAlign: 'center', 
                        p: 2,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3,
                          borderColor: 'error.main'
                        }
                      }}
                      onClick={() => handleOpenBehaviorModal(
                        'night_eaters',
                        'Night Eaters',
                        behaviorData?.behavior_clusters.night_eaters || []
                      )}
                    >
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1, color: 'error.main' }}>
                        {behaviorData?.cluster_summary.night_eaters_count ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Night Eaters
                      </Typography>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card 
                      variant="outlined" 
                      sx={{ 
                        textAlign: 'center', 
                        p: 2,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3,
                          borderColor: 'warning.main'
                        }
                      }}
                      onClick={() => handleOpenBehaviorModal(
                        'under_reporters',
                        'Under-reporters',
                        behaviorData?.behavior_clusters.under_reporters || []
                      )}
                    >
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1, color: 'warning.main' }}>
                        {behaviorData?.cluster_summary.under_reporters_count ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Under-reporters
                      </Typography>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card 
                      variant="outlined" 
                      sx={{ 
                        textAlign: 'center', 
                        p: 2,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3,
                          borderColor: 'info.main'
                        }
                      }}
                      onClick={() => {
                        // For multiple behaviors, we need to create a combined list
                        const allPatients = [...(behaviorData?.behavior_clusters.high_protein_low_carb || []), ...(behaviorData?.behavior_clusters.night_eaters || []), ...(behaviorData?.behavior_clusters.under_reporters || [])];
                        const multiplePatients = allPatients.filter((patient, index, arr) => 
                          arr.findIndex(p => p.user_id === patient.user_id) !== index
                        );
                        handleOpenBehaviorModal(
                          'multiple_behaviors',
                          'Patients with Multiple Behaviors',
                          multiplePatients
                        );
                      }}
                    >
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1, color: 'info.main' }}>
                        {behaviorData?.cluster_summary.multiple_behaviors ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Multiple Behaviors
                      </Typography>
                    </Card>
                  </Grid>
                </Grid>

                {/* Behavior Clusters Scatterplot */}
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                      Behavioral Pattern Visualization
                    </Typography>
                    <Box sx={{ height: 400 }}>
                      <Scatter 
                        data={generateBehaviorClustersScatterplot() || { datasets: [] } as any}
                        options={getBehaviorClustersOptions() as any}
                      />
                    </Box>
                    {behaviorLoading && (
                      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                        <CircularProgress />
                        <Typography sx={{ ml: 2 }}>
                          Analyzing patient behavioral patterns...
                        </Typography>
                      </Box>
                    )}
                    {behaviorError && (
                      <Alert severity="error" sx={{ mb: 2 }}>
                        Error loading behavioral analysis: {behaviorError}
                      </Alert>
                    )}
                    {!behaviorLoading && !behaviorError && behaviorData?.cluster_summary.total_clustered_patients === 0 && (
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <Typography>
                          <strong>No behavioral patterns detected</strong> in the current {analysisPeriod}-day analysis period.
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          This could mean: (1) Patients have healthy, consistent eating patterns, (2) Not enough data for pattern detection, or (3) Try extending the analysis period.
                        </Typography>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 4 && (
          <Box>
            <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold' }}>
              Compliance Tracking
            </Typography>

            {/* Summary Statistics */}
            {complianceTrackingData && (
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="primary.main">
                        {complianceTrackingData?.total_registered_patients ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Patients
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="info.main">
                        {complianceTrackingData?.analysis_period?.total_patients_analyzed ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Analyzed
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="success.main">
                        {(complianceTrackingData?.compliance_averages?.avg_overall_compliance ?? 0).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average Compliance
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="warning.main">
                        {complianceTrackingData?.analysis_period?.days ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Days Analyzed
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}

            {/* Compliance Level Cards */}
            {complianceTrackingData && (
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={4}>
                  <ButtonBase 
                    onClick={() => {
                      const patients = complianceTrackingData?.compliance_categories?.low_compliance ?? [];
                      handleOpenComplianceModal('low', 'Low Compliance Patients', patients);
                    }}
                    disabled={(complianceTrackingData?.compliance_categories?.low_compliance?.length ?? 0) === 0}
                    sx={{ 
                      width: '100%', 
                      height: '100%',
                      borderRadius: 1,
                      '&:hover': {
                        '& .compliance-card': {
                          transform: 'translateY(-2px)',
                          boxShadow: 4
                        }
                      },
                      '&:disabled': {
                        cursor: 'not-allowed',
                        opacity: 0.6
                      }
                    }}
                  >
                    <Card 
                      elevation={2} 
                      className="compliance-card" 
                      sx={{ 
                        height: '100%', 
                        width: '100%',
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: 'error.dark' }}>
                          Low Compliance
                        </Typography>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h3" color="error.main" fontWeight="bold">
                            {complianceTrackingData?.compliance_summary?.low_compliance_count ?? 0}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Patients (Below 50% compliance)
                          </Typography>
                          <Typography variant="body1" fontWeight="medium" color="error.main">
                            {(complianceTrackingData?.compliance_summary?.low_compliance_percentage ?? 0).toFixed(1)}%
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </ButtonBase>
                </Grid>

                <Grid item xs={12} md={4}>
                  <ButtonBase 
                    onClick={() => {
                      const patients = complianceTrackingData?.compliance_categories?.medium_compliance ?? [];
                      handleOpenComplianceModal('medium', 'Medium Compliance Patients', patients);
                    }}
                    disabled={(complianceTrackingData?.compliance_categories?.medium_compliance?.length ?? 0) === 0}
                    sx={{ 
                      width: '100%', 
                      height: '100%',
                      borderRadius: 1,
                      '&:hover': {
                        '& .compliance-card': {
                          transform: 'translateY(-2px)',
                          boxShadow: 4
                        }
                      },
                      '&:disabled': {
                        cursor: 'not-allowed',
                        opacity: 0.6
                      }
                    }}
                  >
                    <Card 
                      elevation={2} 
                      className="compliance-card" 
                      sx={{ 
                        height: '100%', 
                        width: '100%',
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: 'warning.dark' }}>
                          Medium Compliance
                        </Typography>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h3" color="warning.main" fontWeight="bold">
                            {complianceTrackingData?.compliance_summary?.medium_compliance_count ?? 0}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Patients (50-80% compliance)
                          </Typography>
                          <Typography variant="body1" fontWeight="medium" color="warning.main">
                            {(complianceTrackingData?.compliance_summary?.medium_compliance_percentage ?? 0).toFixed(1)}%
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </ButtonBase>
                </Grid>

                <Grid item xs={12} md={4}>
                  <ButtonBase 
                    onClick={() => {
                      const patients = complianceTrackingData?.compliance_categories?.high_compliance ?? [];
                      handleOpenComplianceModal('high', 'High Compliance Patients', patients);
                    }}
                    disabled={(complianceTrackingData?.compliance_categories?.high_compliance?.length ?? 0) === 0}
                    sx={{ 
                      width: '100%', 
                      height: '100%',
                      borderRadius: 1,
                      '&:hover': {
                        '& .compliance-card': {
                          transform: 'translateY(-2px)',
                          boxShadow: 4
                        }
                      },
                      '&:disabled': {
                        cursor: 'not-allowed',
                        opacity: 0.6
                      }
                    }}
                  >
                    <Card 
                      elevation={2} 
                      className="compliance-card" 
                      sx={{ 
                        height: '100%', 
                        width: '100%',
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: 'success.dark' }}>
                          High Compliance
                        </Typography>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h3" color="success.main" fontWeight="bold">
                            {complianceTrackingData?.compliance_summary?.high_compliance_count ?? 0}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Patients (Above 80% compliance)
                          </Typography>
                          <Typography variant="body1" fontWeight="medium" color="success.main">
                            {(complianceTrackingData?.compliance_summary?.high_compliance_percentage ?? 0).toFixed(1)}%
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </ButtonBase>
                </Grid>
              </Grid>
            )}

            {/* No Data State */}
            {complianceTrackingData && (complianceTrackingData?.total_registered_patients ?? 0) === 0 && (
              <Card elevation={2}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <AssignmentTurnedInIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No Compliance Data Available
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    No patients have sufficient data for compliance analysis.
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Box>
        )}

        {activeTab === 5 && (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
              👥 Patient Directory
            </Typography>

            {/* Summary Statistics */}
            {patientDirectoryData && (
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="primary.main">
                        {patientDirectoryData.total_patients}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Patients
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="success.main">
                        {patientDirectoryData.summary_statistics.patients_with_data}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        With Data
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="warning.main">
                        {patientDirectoryData.summary_statistics.patients_without_data}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Without Data
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" color="info.main">
                        {patientDirectoryData.analysis_period.total_records_analyzed}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Records Analyzed
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}

            {/* Simple Patient List */}
            {patientDirectoryData?.patient_summaries && (
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Patient List ({patientDirectoryData.patient_summaries.length} patients)
                  </Typography>
                  
                  <Grid container spacing={2}>
                    {patientDirectoryData.patient_summaries.map((patient) => (
                      <Grid item xs={12} sm={6} md={4} key={patient.user_id}>
                        <Card 
                          variant="outlined" 
                          sx={{ 
                            cursor: 'pointer',
                            '&:hover': { boxShadow: 2, borderColor: 'primary.main' }
                          }}
                          onClick={() => {
                            const patientId = encodeURIComponent(patient.user_id);
                            navigate(`/admin/pias-corner/patient/${patientId}`);
                          }}
                        >
                          <CardContent sx={{ p: 2 }}>
                            <Typography variant="subtitle1" fontWeight="bold" noWrap>
                              {patient.user_name}
                            </Typography>
                            
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              {patient.medical_condition}
                              {patient.is_diabetic && ' • Diabetic'}
                            </Typography>
                            
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Chip 
                                label={patient.health_indicators.risk_level}
                                color={
                                  patient.health_indicators.risk_level === 'Critical' ? 'error' :
                                  patient.health_indicators.risk_level === 'High' ? 'warning' :
                                  patient.health_indicators.risk_level === 'Medium' ? 'info' :
                                  patient.health_indicators.risk_level === 'Low' ? 'success' : 'default'
                                }
                                size="small"
                              />
                              
                              <Typography variant="caption" color="text.secondary">
                                {patient.analysis_period.logged_days}/{patient.analysis_period.total_days} days
                              </Typography>
                            </Box>
                            
                            <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption">
                                🔥 {patient.daily_averages.calories.toFixed(0)} cal
                              </Typography>
                              <Typography variant="caption">
                                📊 {(patient.target_compliance.overall_compliance_rate * 100).toFixed(0)}%
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            )}

            {/* No Data State */}
            {patientDirectoryData && patientDirectoryData.patient_summaries.length === 0 && (
              <Card elevation={2}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <GroupIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No Patient Data Available
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    No patients have logged food data in the current analysis period.
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Box>
        )}
      </Paper>

      {/* Patient List Modal */}
      <Dialog
        open={patientListModal.open}
        onClose={handleClosePatientList}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">{patientListModal.title}</Typography>
          <IconButton onClick={handleClosePatientList} size="small">
            <ArrowBackIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {patientListModal.type === 'inactive' && patientListModal.patients.length > 0 ? (
            <List>
              {patientListModal.patients.map((patient, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={patient.user_name}
                    secondary={`Email: ${patient.user_id}`}
                  />
                  <Chip 
                    label="Inactive" 
                    color="warning" 
                    size="small" 
                    sx={{ ml: 1 }}
                  />
                </ListItem>
              ))}
            </List>
          ) : patientListModal.type === 'records' ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h6" gutterBottom>
                Food Records Analysis
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                Total Records: {data?.analysis_period.total_records_analyzed || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analysis Period: {data?.analysis_period.start_date} to {data?.analysis_period.end_date}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Records from {data?.cohort_size || 0} active patients over {data?.analysis_period.days || 0} days
              </Typography>
            </Box>
          ) : patientListModal.type === 'total' && patientListModal.detailedPatients.length > 0 ? (
            <List>
              {patientListModal.detailedPatients.map((patient, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" fontWeight="medium">
                          {patient.user_name}
                        </Typography>
                        <Chip 
                          label={patient.is_active ? "Active" : "Inactive"} 
                          color={patient.is_active ? "success" : "warning"} 
                          size="small" 
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" display="block">
                          Email: {patient.user_id}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Registration: {patient.registration_code}
                        </Typography>
                        {patient.phone !== "N/A" && (
                          <Typography variant="caption" display="block">
                            Phone: {patient.phone}
                          </Typography>
                        )}
                        {patient.condition !== "N/A" && (
                          <Typography variant="caption" display="block">
                            Condition: {patient.condition}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : patientListModal.type === 'total' ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="body1" color="text.secondary">
                Total Registered Patients: {data?.total_registered_patients || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                This includes all patients registered in the system, both active and inactive.
              </Typography>
              <Alert severity="warning" sx={{ mt: 2 }}>
                No patient data found in the admin panel.
              </Alert>
            </Box>
          ) : patientListModal.type === 'active' && patientListModal.patients.length > 0 ? (
            <List>
              {patientListModal.patients.map((patient, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={patient.user_name}
                    secondary={`Email: ${patient.user_id}`}
                  />
                  <Chip 
                    label="Active" 
                    color="success" 
                    size="small" 
                    sx={{ ml: 1 }}
                  />
                </ListItem>
              ))}
            </List>
          ) : patientListModal.type === 'active' ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="body1" color="text.secondary">
                Active Patients: {data?.cohort_size || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                These are patients who have logged food consumption data in the last {data?.analysis_period.days || 0} days.
              </Typography>
              <Alert severity="warning" sx={{ mt: 2 }}>
                No active patients found in the current analysis period.
              </Alert>
            </Box>
          ) : patientListModal.type.includes('_engagement') && patientListModal.patients.length > 0 ? (
            <List>
              {(patientListModal.patients as UserEngagementAnalysis[]).map((patient, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" fontWeight="medium">
                          {patient.user_name}
                        </Typography>
                        <Chip 
                          label={patient.engagement_level?.charAt(0).toUpperCase() + patient.engagement_level?.slice(1) || 'Unknown'} 
                          color={
                            patient.engagement_level === 'excellent' ? 'success' :
                            patient.engagement_level === 'good' ? 'info' :
                            patient.engagement_level === 'fair' ? 'warning' :
                            patient.engagement_level === 'poor' ? 'error' :
                            patient.engagement_level === 'critical' ? 'error' :
                            'default'
                          }
                          size="small" 
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" display="block">
                          Email: {patient.user_id}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Total Logs: {patient.total_logs || 0}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Avg Logs/Day: {patient.avg_logs_per_day || 0}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Days Since Last Log: {patient.days_since_last_log || 0}
                        </Typography>
                        {patient.last_log_date && (
                          <Typography variant="caption" display="block">
                            Last Log: {patient.last_log_date}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : patientListModal.type.includes('_engagement') ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="body1" color="text.secondary">
                {patientListModal.type.replace('_engagement', '').charAt(0).toUpperCase() + patientListModal.type.replace('_engagement', '').slice(1)} Engagement: 0 patients
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                No patients found with this engagement level in the current analysis period.
              </Typography>
              <Alert severity="info" sx={{ mt: 2 }}>
                This engagement level classification is based on food logging frequency and consistency.
              </Alert>
            </Box>
          ) : (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
              No patient data available
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePatientList} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Behavioral Clustering Modal */}
      <Dialog
        open={behaviorModal.open}
        onClose={handleCloseBehaviorModal}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">{behaviorModal.title}</Typography>
          <IconButton onClick={handleCloseBehaviorModal} size="small">
            <ArrowBackIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {behaviorModal.patients.length > 0 ? (
            <List>
              {behaviorModal.patients.map((patient, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" fontWeight="medium">
                          {patient.user_name}
                        </Typography>
                        {patient.has_diabetes && (
                          <Chip 
                            label="Diabetes" 
                            color="warning" 
                            size="small" 
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Email: {patient.user_id}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Analysis Days: {patient.analysis_days} | Avg Daily Calories: {Math.round(patient.avg_daily_calories)}
                        </Typography>
                        {behaviorModal.type === 'high_protein_low_carb' && (
                          <Typography variant="body2" color="success.main">
                            Protein: {Math.round(patient.avg_protein_percentage || 0)}% | Carbs: {Math.round(patient.avg_carb_percentage || 0)}% | Score: {Math.round(patient.high_protein_low_carb_score || 0)}%
                          </Typography>
                        )}
                        {behaviorModal.type === 'night_eaters' && (
                          <Typography variant="body2" color="error.main">
                            Night Eating Days: {patient.night_eating_days} | Frequency: {Math.round(patient.night_eating_frequency || 0)}% | Severity: {patient.night_eating_severity}
                          </Typography>
                        )}
                        {behaviorModal.type === 'under_reporters' && (
                          <Typography variant="body2" color="warning.main">
                            Severity: {patient.under_reporting_severity} | Calorie Deficit: {Math.round(Math.abs(patient.avg_calorie_deficit || 0))} cal/day
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body1" sx={{ textAlign: 'center', py: 3 }}>
              No patients found in this behavioral category
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseBehaviorModal} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Compliance Patient Modal */}
      <Dialog
        open={complianceModal.open}
        onClose={handleCloseComplianceModal}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">{complianceModal.title}</Typography>
          <IconButton onClick={handleCloseComplianceModal} size="small">
            <ArrowBackIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {complianceModal.patients.length > 0 ? (
            <List>
              {complianceModal.patients.map((patient, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="h6" fontWeight="bold">
                          {patient.user_name}
                        </Typography>
                        {patient.is_diabetic && (
                          <Chip 
                            label="Diabetic" 
                            color="error" 
                            size="small" 
                            variant="outlined"
                          />
                        )}
                        <Chip 
                          label={`${patient.overall_compliance_rate.toFixed(1)}% Overall`}
                          color={
                            patient.compliance_category === 'high' ? 'success' :
                            patient.compliance_category === 'medium' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Grid container spacing={2}>
                          {/* Patient Info */}
                          <Grid item xs={12} md={6}>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              <strong>Email:</strong> {patient.user_id}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              <strong>Medical Condition:</strong> {patient.medical_condition}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                              <strong>Analysis Period:</strong> {patient.logged_days}/{patient.analysis_days} days logged
                            </Typography>
                          </Grid>
                          
                          {/* Compliance Metrics */}
                          <Grid item xs={12} md={6}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              <Typography variant="body2">
                                <strong>Logging:</strong> {patient.logging_compliance_rate.toFixed(1)}%
                              </Typography>
                              <Typography variant="body2">
                                <strong>Calorie Targets:</strong> {patient.calorie_compliance_rate.toFixed(1)}%
                              </Typography>
                              <Typography variant="body2">
                                <strong>Nutrient Balance:</strong> {patient.nutrient_compliance_rate.toFixed(1)}%
                              </Typography>
                            </Box>
                          </Grid>
                          
                          {/* Issues & Strengths */}
                          <Grid item xs={12} md={6}>
                            {patient.compliance_issues.length > 0 && (
                              <Box sx={{ mb: 1 }}>
                                <Typography variant="body2" color="error.main" fontWeight="medium">
                                  Issues:
                                </Typography>
                                {patient.compliance_issues.map((issue, i) => (
                                  <Typography key={i} variant="body2" color="error.main" sx={{ fontSize: '0.75rem', ml: 1 }}>
                                    • {issue}
                                  </Typography>
                                ))}
                              </Box>
                            )}
                            {patient.strengths.length > 0 && (
                              <Box>
                                <Typography variant="body2" color="success.main" fontWeight="medium">
                                  Strengths:
                                </Typography>
                                {patient.strengths.map((strength, i) => (
                                  <Typography key={i} variant="body2" color="success.main" sx={{ fontSize: '0.75rem', ml: 1 }}>
                                    • {strength}
                                  </Typography>
                                ))}
                              </Box>
                            )}
                          </Grid>
                          
                          {/* Recommendations */}
                          <Grid item xs={12} md={6}>
                            <Box>
                              <Typography variant="body2" color="primary.main" fontWeight="medium">
                                Medical Recommendations:
                              </Typography>
                              {patient.recommendations.map((rec, i) => (
                                <Typography key={i} variant="body2" color="primary.main" sx={{ fontSize: '0.75rem', ml: 1 }}>
                                  • {rec}
                                </Typography>
                              ))}
                            </Box>
                          </Grid>
                        </Grid>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body1" sx={{ textAlign: 'center', py: 3 }}>
              No patients found in this compliance category
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseComplianceModal} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PiasCorner;