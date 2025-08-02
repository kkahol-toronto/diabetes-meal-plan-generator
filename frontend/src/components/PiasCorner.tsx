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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip,
  IconButton,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Badge
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TableChartIcon from '@mui/icons-material/TableChart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WarningIcon from '@mui/icons-material/Warning';
import RefreshIcon from '@mui/icons-material/Refresh';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DashboardIcon from '@mui/icons-material/Dashboard';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import TrendingUpOutlinedIcon from '@mui/icons-material/TrendingUpOutlined';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import GroupIcon from '@mui/icons-material/Group';
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

interface AnalysisPeriod {
  days: number;
  total_records_analyzed: number;
  start_date: string;
  end_date: string;
}

interface CohortAverages {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sodium: number;
  sugar: number;
  vs_rda: {
    protein_deficit: number;
    fiber_deficit: number;
    sodium_excess: number;
  };
}

interface DeficiencyAnalysis {
  top_deficiencies: Array<{
    issue: string;
    percentage: number;
    severity: string;
    affected_patients: number;
  }>;
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
  analysis_period: AnalysisPeriod;
  cohort_averages: CohortAverages;
  rda_compliance: {
    protein: number;
    fiber: number;
    calories: number;
  };
  deficiency_analysis: DeficiencyAnalysis;
  recommendations: Recommendations;
  generated_at: string;
}

// Engagement metrics interfaces
interface UserEngagementAnalysis {
  user_id: string;
  user_name: string;
  logs_count: number;
  unique_days: number;
  engagement_score: number;
  engagement_level: string;
  last_log_date: string;
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
  user_engagement_analysis: UserEngagementAnalysis[];
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
  chronic_risk: boolean;
  pattern_info: PatternInfo;
  analysis_period: AnalysisPeriodInfo;
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
  behavior_score: number;
  health_outcomes: {
    weight_management: string;
    diabetes_impact: string;
    sleep_quality: string;
    nutritional_status: string;
    data_reliability: string;
  };
  medical_notes: string;
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

// Compliance analysis interfaces
interface ComplianceTargets {
  calorie_range: { min: number; max: number };
  logging_frequency: { min_logs_per_day: number };
  nutrient_balance: {
    protein_min_percentage: number;
    carbs_max_percentage: number;
    sodium_max_mg: number;
    fiber_min_g: number;
  };
}

interface ComplianceSegments {
  high: any[];
  medium: any[];
  low: any[];
}

interface ComplianceAverages {
  avg_logging_compliance: number;
  avg_calorie_compliance: number;
  avg_nutrient_compliance: number;
  avg_overall_compliance: number;
}

interface ComplianceSummary {
  high_compliance_count: number;
  medium_compliance_count: number;
  low_compliance_count: number;
  high_compliance_percentage: number;
  medium_compliance_percentage: number;
  low_compliance_percentage: number;
}

interface DiabeticAnalysis {
  total_diabetic_patients: number;
  diabetic_high_compliance: number;
  diabetic_medium_compliance: number;
  diabetic_low_compliance: number;
}

interface MedicalInsights {
  medical_alerts: string[];
  priority_actions: string[];
}

interface ComplianceData {
  analysis_period: {
    days: number;
    total_patients_analyzed: number;
  };
  compliance_segments: ComplianceSegments;
  compliance_averages: ComplianceAverages;
  compliance_summary: ComplianceSummary;
  diabetic_analysis: DiabeticAnalysis;
  medical_insights: MedicalInsights;
  compliance_targets: ComplianceTargets;
  generated_at: string;
}

// Patient summary interfaces
interface PatientSummaryProfile {
  user_id: string;
  user_name: string;
  registration_code: string;
  medical_condition: string;
  is_diabetic: boolean;
  analysis_period: {
    total_days: number;
    logged_days: number;
    data_availability: string;
  };
  daily_averages: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
    fiber: number;
    sodium: number;
    sugar: number;
  };
  target_compliance: {
    days_within_calorie_target: number;
    days_above_target: number;
    days_below_target: number;
    days_with_nutrient_issues: number;
    days_without_nutrient_issues: number;
    calorie_compliance_rate: number;
    nutrient_compliance_rate: number;
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
  };
  logging_rate: number;
  overall_compliance_rate: number;
  risk_level: string;
  recommendations: string[];
}

interface PatientSummaryStatistics {
  total_patients: number;
  patients_with_data: number;
  patients_without_data: number;
  avg_calories: number;
  avg_compliance_rate: number;
  avg_logging_rate: number;
  risk_distribution: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    unknown: number;
  };
}

interface PatientSummaryData {
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
  };
  summary_statistics: PatientSummaryStatistics;
  patient_summaries: PatientSummaryProfile[];
  medical_insights: string[];
  compliance_targets: ComplianceTargets;
  generated_at: string;
}

const PiasCorner: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<NutrientAdequacyData | null>(null);
  const [engagementData, setEngagementData] = useState<EngagementMetricsData | null>(null);
  const [outlierData, setOutlierData] = useState<OutlierDetectionData | null>(null);
  const [behaviorData, setBehaviorData] = useState<BehaviorClustersData | null>(null);
  const [complianceData, setComplianceData] = useState<ComplianceData | null>(null);
  const [patientSummaryData, setPatientSummaryData] = useState<PatientSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [engagementLoading, setEngagementLoading] = useState(true);
  const [outlierLoading, setOutlierLoading] = useState(true);
  const [behaviorLoading, setBehaviorLoading] = useState(true);
  const [complianceLoading, setComplianceLoading] = useState(true);
  const [patientSummaryLoading, setPatientSummaryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [engagementError, setEngagementError] = useState<string | null>(null);
  const [outlierError, setOutlierError] = useState<string | null>(null);
  const [behaviorError, setBehaviorError] = useState<string | null>(null);
  const [complianceError, setComplianceError] = useState<string | null>(null);
  const [patientSummaryError, setPatientSummaryError] = useState<string | null>(null);
  const [analysisPeriod, setAnalysisPeriod] = useState(30);
  const [activeTab, setActiveTab] = useState(0);
  
  // Table state
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<keyof PatientSummaryProfile>('user_name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const handleBackToAdmin = () => {
    navigate('/admin');
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const fetchNutrientAdequacyData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${config.API_URL}/admin/pias-corner/nutrient-adequacy?days=${analysisPeriod}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch nutrient adequacy data');
      }

      const result: NutrientAdequacyData = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error fetching nutrient adequacy data:', err);
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

  const fetchComplianceData = useCallback(async () => {
    try {
      setComplianceLoading(true);
      setComplianceError(null);
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
        throw new Error('Failed to fetch compliance data');
      }

      const result: ComplianceData = await response.json();
      setComplianceData(result);
    } catch (err) {
      console.error('Error fetching compliance data:', err);
      setComplianceError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setComplianceLoading(false);
    }
  }, [analysisPeriod]);

  const fetchPatientSummaryData = useCallback(async () => {
    try {
      setPatientSummaryLoading(true);
      setPatientSummaryError(null);
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
        throw new Error('Failed to fetch patient summary data');
      }

      const result: PatientSummaryData = await response.json();
      setPatientSummaryData(result);
    } catch (err) {
      console.error('Error fetching patient summary data:', err);
      setPatientSummaryError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setPatientSummaryLoading(false);
    }
  }, [analysisPeriod]);

  useEffect(() => {
    fetchNutrientAdequacyData();
    fetchEngagementMetrics();
    fetchOutlierDetection();
    fetchBehaviorClusters();
    fetchComplianceData();
    fetchPatientSummaryData();
  }, [analysisPeriod, fetchNutrientAdequacyData, fetchEngagementMetrics, fetchOutlierDetection, fetchBehaviorClusters, fetchComplianceData, fetchPatientSummaryData]);

  // Chart generation functions
  const generatePopulationAveragesChart = () => {
    if (!data) return null;

    return {
      labels: ['Protein', 'Carbs', 'Fat', 'Fiber', 'Sodium', 'Sugar'],
      datasets: [{
        label: 'Daily Average (g/mg)',
        data: [
          data.cohort_averages.protein,
          data.cohort_averages.carbohydrates,
          data.cohort_averages.fat,
          data.cohort_averages.fiber,
          data.cohort_averages.sodium / 1000, // Convert to grams for display
          data.cohort_averages.sugar
        ],
        backgroundColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0',
          '#9966FF',
          '#FF9F40'
        ],
        borderWidth: 1,
      }]
    };
  };

  const generateComplianceHeatmapChart = () => {
    if (!data) return null;

    return {
      labels: ['Protein', 'Fiber', 'Calories'],
      datasets: [{
        label: 'RDA Compliance (%)',
        data: [
          data.rda_compliance.protein,
          data.rda_compliance.fiber,
          data.rda_compliance.calories
        ],
        backgroundColor: [
          data.rda_compliance.protein >= 80 ? '#4CAF50' : data.rda_compliance.protein >= 60 ? '#FF9800' : '#F44336',
          data.rda_compliance.fiber >= 80 ? '#4CAF50' : data.rda_compliance.fiber >= 60 ? '#FF9800' : '#F44336',
          data.rda_compliance.calories >= 80 ? '#4CAF50' : data.rda_compliance.calories >= 60 ? '#FF9800' : '#F44336'
        ],
        borderWidth: 1,
      }]
    };
  };

  const generateEngagementFunnelChart = () => {
    if (!engagementData) return null;

    return {
      labels: ['Excellent', 'Good', 'Fair', 'Poor', 'Critical', 'Inactive'],
      datasets: [{
        label: 'Number of Patients',
        data: [
          engagementData.engagement_summary.excellent,
          engagementData.engagement_summary.good,
          engagementData.engagement_summary.fair,
          engagementData.engagement_summary.poor,
          engagementData.engagement_summary.critical,
          engagementData.engagement_summary.inactive
        ],
        backgroundColor: [
          '#4CAF50',
          '#2196F3',
          '#FF9800',
          '#FF5722',
          '#9C27B0',
          '#607D8B'
        ],
        borderWidth: 1,
      }]
    };
  };

  const generateEngagementTimeSeriesChart = () => {
    if (!engagementData) return null;

    return {
      labels: engagementData.daily_metrics.map(metric => 
        new Date(metric.date).toLocaleDateString()
      ),
      datasets: [{
        label: 'Active Users',
        data: engagementData.daily_metrics.map(metric => metric.active_users),
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        fill: true,
        tension: 0.4,
      }]
    };
  };

  // Behavior clusters chart generation functions
  const generateBehaviorClustersScatterplot = () => {
    if (!behaviorData) return { datasets: [] };

    const { behavior_clusters } = behaviorData;
    const datasets = [];

    if (behavior_clusters.high_protein_low_carb.length > 0) {
      datasets.push({
        label: 'High Protein - Low Carb',
        data: behavior_clusters.high_protein_low_carb.map((patient, index) => ({
          x: index,
          y: patient.behavior_score ?? 0,
          patientName: patient.user_name,
          analysisDays: patient.analysis_days,
          hasDiabetes: patient.has_diabetes,
          calories: patient.behavior_score ?? 0,
          score: patient.behavior_score ?? 0,
          clusterType: 'High Protein - Low Carb'
        })),
        backgroundColor: '#4CAF50',
        borderColor: '#388E3C',
        pointRadius: 6,
      });
    }

    if (behavior_clusters.night_eaters.length > 0) {
      datasets.push({
        label: 'Night Eaters',
        data: behavior_clusters.night_eaters.map((patient, index) => ({
          x: index,
          y: patient.behavior_score ?? 0,
          patientName: patient.user_name,
          analysisDays: patient.analysis_days,
          hasDiabetes: patient.has_diabetes,
          calories: patient.behavior_score ?? 0,
          score: patient.behavior_score ?? 0,
          clusterType: 'Night Eaters'
        })),
        backgroundColor: '#FF5722',
        borderColor: '#D32F2F',
        pointRadius: 6,
      });
    }

    if (behavior_clusters.under_reporters.length > 0) {
      datasets.push({
        label: 'Under-reporters',
        data: behavior_clusters.under_reporters.map((patient, index) => ({
          x: index,
          y: patient.behavior_score ?? 0,
          patientName: patient.user_name,
          analysisDays: patient.analysis_days,
          hasDiabetes: patient.has_diabetes,
          calories: patient.behavior_score ?? 0,
          score: patient.behavior_score ?? 0,
          clusterType: 'Under-reporters'
        })),
        backgroundColor: '#FF9800',
        borderColor: '#F57C00',
        pointRadius: 6,
      });
    }

    return { datasets };
  };

  const getBehaviorClustersOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Patient Behavioral Clusters',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const point = context.raw;
            return [
              `Patient: ${point.patientName}`,
              `Cluster: ${point.clusterType}`,
              `Analysis Days: ${point.analysisDays}`,
              `Score: ${point.score}`,
              `Has Diabetes: ${point.hasDiabetes ? 'Yes' : 'No'}`,
            ];
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Patient Index'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Behavioral Metric (varies by cluster)'
        }
      }
    }
  });

  // Chart options
  const getChartOptions = (title: string) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: true,
        text: title,
      },
    },
  });

  const getFunnelChartOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: true,
        text: 'Patient Engagement Levels',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Patients'
        }
      }
    }
  });

  const getEngagementTimeSeriesOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Daily Active Users Trend',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Active Users'
        }
      }
    }
  });

  // Helper functions
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'severe': return '#f44336';
      case 'moderate': return '#ff9800';
      case 'mild': return '#ffeb3b';
      default: return '#4caf50';
    }
  };

  const handleSort = (column: keyof PatientSummaryProfile) => {
    const isAsc = sortBy === column && sortOrder === 'asc';
    setSortOrder(isAsc ? 'desc' : 'asc');
    setSortBy(column);
  };

  const handleRowClick = (patient: PatientSummaryProfile) => {
    const patientId = encodeURIComponent(patient.user_id);
    navigate(`/admin/pias-corner/patient/${patientId}`);
  };

  const getFilteredAndSortedPatients = () => {
    if (!patientSummaryData?.patient_summaries) return [];

    let filtered = patientSummaryData.patient_summaries.filter(patient =>
      patient.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.medical_condition.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return filtered.sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      return 0;
    });
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getComplianceColor = (rate: number) => {
    if (rate >= 0.8) return 'success.main';
    if (rate >= 0.6) return 'warning.main';
    return 'error.main';
  };

  if (loading || engagementLoading || outlierLoading || behaviorLoading || complianceLoading || patientSummaryLoading) {
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
            {complianceLoading && ' Loading compliance data...'}
            {patientSummaryLoading && ' Loading patient summaries...'}
          </Typography>
        </Paper>
      </Container>
    );
  }

  if (error || engagementError || outlierError || behaviorError || complianceError || patientSummaryError) {
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
          {complianceError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Compliance Analysis Error: {complianceError}
            </Alert>
          )}
          {patientSummaryError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Patient Summary Error: {patientSummaryError}
            </Alert>
          )}
          <Button
            variant="contained"
            onClick={() => {
              fetchNutrientAdequacyData();
              fetchEngagementMetrics();
              fetchOutlierDetection();
              fetchBehaviorClusters();
              fetchComplianceData();
              fetchPatientSummaryData();
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
              onClick={fetchNutrientAdequacyData}
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
              label={
                <Badge 
                  badgeContent={data?.deficiency_analysis?.top_deficiencies?.length ?? 0}
                  color="warning"
                  max={9}
                >
                  Nutrition Analysis
                </Badge>
              }
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
              icon={
                <Badge 
                  badgeContent={patientSummaryData?.patient_summaries?.length ?? 0}
                  color="primary"
                  max={999}
                >
                  <GroupIcon />
                </Badge>
              } 
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
                          options={getChartOptions('Daily Averages Across Cohort')}
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
                          options={getChartOptions('Compliance by Nutrient (%)')}
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
                    <Grid container spacing={2}>
                      {data?.deficiency_analysis.top_deficiencies.slice(0, 4).map((deficiency, index) => (
                        <Grid item xs={12} sm={6} md={3} key={index}>
                          <Box sx={{ textAlign: 'center', p: 2, border: '1px solid', borderColor: 'warning.light', borderRadius: 1 }}>
                            <Typography variant="h6" color="warning.dark" fontWeight="bold">
                              {deficiency.percentage}%
                            </Typography>
                            <Typography variant="body2" fontWeight="medium">
                              {deficiency.issue}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {deficiency.affected_patients} patients
                            </Typography>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
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
                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
                          <Typography variant="h4" fontWeight="bold" color="primary.dark">
                            {data?.total_registered_patients}
                          </Typography>
                          <Typography variant="caption" color="primary.dark">Total Patients</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                          <Typography variant="h4" fontWeight="bold" color="success.dark">
                            {data?.cohort_size}
                          </Typography>
                          <Typography variant="caption" color="success.dark">Active Patients</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'secondary.light', borderRadius: 1 }}>
                          <Typography variant="h4" fontWeight="bold" color="secondary.dark">
                            {data?.analysis_period.total_records_analyzed}
                          </Typography>
                          <Typography variant="caption" color="secondary.dark">Food Records</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: data?.inactive_patients_count ? 'warning.light' : 'info.light', borderRadius: 1 }}>
                          <Typography variant="h4" fontWeight="bold" color={data?.inactive_patients_count ? 'warning.dark' : 'info.dark'}>
                            {data?.inactive_patients_count ?? 0}
                          </Typography>
                          <Typography variant="caption" color={data?.inactive_patients_count ? 'warning.dark' : 'info.dark'}>Inactive Patients</Typography>
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
            <Typography variant="h5" sx={{ mb: 3 }}>
              🥗 Nutrition Analysis
            </Typography>
            <Grid container spacing={3}>
              {/* Detailed Nutrition Charts */}
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
                          options={getChartOptions('Daily Averages Across Cohort')}
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
                          options={getChartOptions('Compliance by Nutrient (%)')}
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

              {/* Detailed Nutritional Analysis */}
              <Grid item xs={12}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AnalyticsIcon sx={{ mr: 1, color: 'info.main' }} />
                      <Typography variant="h6">
                        Detailed Nutrient Intake Analysis
                      </Typography>
                    </Box>
                    <Box sx={{ height: 300 }}>
                      {populationAveragesData ? (
                        <Bar 
                          data={populationAveragesData} 
                          options={getChartOptions('Average Daily Intake by Nutrient')}
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
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="success.main" fontWeight="bold">
                              {engagementData.engagement_summary.excellent}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Excellent
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="info.main" fontWeight="bold">
                              {engagementData.engagement_summary.good}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Good
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="warning.main" fontWeight="bold">
                              {engagementData.engagement_summary.fair}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Fair
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="error.main" fontWeight="bold">
                              {engagementData.engagement_summary.poor}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Poor
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="text.secondary" fontWeight="bold">
                              {engagementData.engagement_summary.critical}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Critical
                            </Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={6} sm={4} md={2}>
                          <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                            <Typography variant="h4" color="action.disabled" fontWeight="bold">
                              {engagementData.engagement_summary.inactive}
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
                    <Grid container spacing={2}>
                      {outlierData?.outliers?.patient_profiles?.slice(0, 6).map((patient, index) => (
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
                                Pattern: {patient.pattern_info?.pattern_type || 'Multiple Issues'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Analysis: {patient.analysis_period?.days_analyzed || 0} days
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
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
                    <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
                        {behaviorData?.cluster_summary.high_protein_low_carb_count ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        High Protein - Low Carb
                      </Typography>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
                        {behaviorData?.cluster_summary.night_eaters_count ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Night Eaters
                      </Typography>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
                        {behaviorData?.cluster_summary.under_reporters_count ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Under-reporters
                      </Typography>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
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
                        data={generateBehaviorClustersScatterplot() || { datasets: [] }}
                        options={getBehaviorClustersOptions()}
                      />
                    </Box>
                    {behaviorData?.cluster_summary.total_clustered_patients === 0 && (
                      <Typography color="text.secondary">
                        No behavioral patterns detected in current analysis period
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 4 && (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
              ✅ Compliance Tracking
            </Typography>
            <Grid container spacing={3}>
              {/* Compliance Distribution */}
              <Grid item xs={12}>
                <Typography variant="h6">
                  Patient Compliance Analysis
                </Typography>
              </Grid>

              {/* Compliance Summary Cards */}
              <Grid item xs={12} md={4}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: 'error.dark' }}>
                      Low Compliance
                    </Typography>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h3" color="error.main" fontWeight="bold">
                        {complianceData?.compliance_segments.low.length ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Patients (&lt;50% compliance)
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: 'success.dark' }}>
                      Medium Compliance
                    </Typography>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h3" color="warning.main" fontWeight="bold">
                        {complianceData?.compliance_segments.medium.length ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Patients (50-80% compliance)
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: 'info.dark' }}>
                      High Compliance
                    </Typography>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h3" color="success.main" fontWeight="bold">
                        {complianceData?.compliance_segments.high.length ?? 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Patients (&gt;80% compliance)
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Diabetic Patient Analysis */}
              {complianceData && complianceData.diabetic_analysis.total_diabetic_patients > 0 && (
                <Grid item xs={12}>
                  <Card elevation={2} sx={{ bgcolor: '#f3e5f5' }}>
                    <CardContent>
                      <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: 'secondary.dark' }}>
                        Diabetic Patient Compliance
                      </Typography>
                      <Grid container spacing={3}>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                            <Typography variant="h5" fontWeight="bold" color="info.dark">
                              {complianceData.diabetic_analysis.total_diabetic_patients}
                            </Typography>
                            <Typography variant="caption" color="info.dark">Total Diabetic</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                            <Typography variant="h5" fontWeight="bold" color="success.dark">
                              {complianceData.diabetic_analysis.diabetic_high_compliance}
                            </Typography>
                            <Typography variant="caption" color="success.dark">High Compliance</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                            <Typography variant="h5" fontWeight="bold" color="warning.dark">
                              {complianceData.diabetic_analysis.diabetic_medium_compliance}
                            </Typography>
                            <Typography variant="caption" color="warning.dark">Medium Compliance</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                            <Typography variant="h5" fontWeight="bold" color="error.dark">
                              {complianceData.diabetic_analysis.diabetic_low_compliance}
                            </Typography>
                            <Typography variant="caption" color="error.dark">Low Compliance</Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </Box>
        )}

        {activeTab === 5 && (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
              👥 Patient Directory
            </Typography>

            {/* Search and Controls */}
            <Card elevation={2} sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Patient Summary Table
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {patientSummaryData?.patient_summaries.length ?? 0} patients
                  </Typography>
                </Box>
                
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Search patients by name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </CardContent>
            </Card>

            {/* Patient Table */}
            {patientSummaryData && (
              <Card elevation={2}>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'grey.50' }}>
                        <TableCell>
                          <TableSortLabel
                            active={sortBy === 'user_name'}
                            direction={sortBy === 'user_name' ? sortOrder : 'asc'}
                            onClick={() => handleSort('user_name')}
                          >
                            Patient Name
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="right">
                          <TableSortLabel
                            active={sortBy === 'risk_level'}
                            direction={sortBy === 'risk_level' ? sortOrder : 'asc'}
                            onClick={() => handleSort('risk_level')}
                          >
                            Risk Level
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="right">
                          <TableSortLabel
                            active={sortBy === 'overall_compliance_rate'}
                            direction={sortBy === 'overall_compliance_rate' ? sortOrder : 'asc'}
                            onClick={() => handleSort('overall_compliance_rate')}
                          >
                            Compliance
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="right">
                          <TableSortLabel
                            active={sortBy === 'logging_rate'}
                            direction={sortBy === 'logging_rate' ? sortOrder : 'asc'}
                            onClick={() => handleSort('logging_rate')}
                          >
                            Logging Rate
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="right">
                          Daily Avg Calories
                        </TableCell>
                        <TableCell align="right">
                          Daily Avg Protein
                        </TableCell>
                        <TableCell align="right">
                          Daily Avg Carbs
                        </TableCell>
                        <TableCell align="right">
                          Daily Avg Fat
                        </TableCell>
                        <TableCell align="center">
                          Actions
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {getFilteredAndSortedPatients().map((patient, index) => (
                        <TableRow 
                          key={patient.user_id}
                          hover
                          sx={{ 
                            cursor: 'pointer',
                            '&:hover': { bgcolor: 'action.hover' }
                          }}
                          onClick={() => handleRowClick(patient)}
                        >
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {patient.user_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {patient.medical_condition} {patient.is_diabetic && '• Diabetic'}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip 
                              label={patient.risk_level}
                              color={getRiskLevelColor(patient.risk_level)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography 
                              variant="body2" 
                              fontWeight="medium"
                              color={getComplianceColor(patient.overall_compliance_rate)}
                            >
                              {(patient.overall_compliance_rate * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {(patient.logging_rate * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {patient.daily_averages.calories.toFixed(0)} kcal
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {patient.daily_averages.protein.toFixed(1)}g
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {patient.daily_averages.carbs.toFixed(1)}g
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {patient.daily_averages.fat.toFixed(1)}g
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Tooltip title="View Patient Details">
                              <IconButton
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRowClick(patient);
                                }}
                              >
                                <VisibilityIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {patientSummaryData && getFilteredAndSortedPatients().length === 0 && (
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <Typography variant="h6" color="text.secondary">
                      No patients found matching your search criteria
                    </Typography>
                  </Box>
                )}
              </Card>
            )}

            {/* Summary Statistics */}
            {patientSummaryData && (
              <Grid container spacing={3} sx={{ mt: 2 }}>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h6" fontWeight="bold" color="info.dark">
                      {patientSummaryData.summary_statistics.patients_with_data}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Patients with Data
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h6" fontWeight="bold" color="warning.dark">
                      {patientSummaryData.summary_statistics.patients_without_data}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Patients without Data
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h6" fontWeight="bold" color="secondary.dark">
                      {patientSummaryData.summary_statistics.avg_calories.toFixed(0)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Avg Calories
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h6" fontWeight="bold" color="success.dark">
                      {(patientSummaryData.summary_statistics.avg_compliance_rate * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Avg Compliance
                    </Typography>
                  </Card>
                </Grid>
              </Grid>
            )}
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default PiasCorner;