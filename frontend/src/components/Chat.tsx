import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../contexts/AppContext';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Card,
  CardContent,
  Fade,
  Slide,
  Zoom,
  useTheme,
  keyframes,
  Chip,
  Avatar,
  Grid,
  ButtonGroup,
  Fab,
  Badge,
  alpha,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AddCommentIcon from '@mui/icons-material/AddComment';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import CloseIcon from '@mui/icons-material/Close';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import AssignmentIcon from '@mui/icons-material/Assignment';
import HistoryIcon from '@mui/icons-material/History';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import FavoriteIcon from '@mui/icons-material/Favorite';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import GrainIcon from '@mui/icons-material/Grain';
import SearchIcon from '@mui/icons-material/Search';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import KitchenIcon from '@mui/icons-material/Kitchen';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { v4 as uuidv4 } from 'uuid';
import config from '../config/environment';
import PendingConsumptionDialog from './PendingConsumptionDialog';

// Enhanced Mobile Animations
const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-3px); }
  100% { transform: translateY(0px); }
`;

const slideInUp = keyframes`
  0% { 
    opacity: 0;
    transform: translateY(30px);
  }
  100% { 
    opacity: 1;
    transform: translateY(0);
  }
`;

const fadeInScale = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.95);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

const shimmer = keyframes`
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
`;

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const gradientShift = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

const bounceIn = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.3);
  }
  50% { 
    opacity: 1;
    transform: scale(1.05);
  }
  70% { 
    transform: scale(0.9);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

// Removed duplicate keyframes (already defined above)

const typewriter = keyframes`
  from { width: 0; }
  to { width: 100%; }
`;

interface Message {
  id: string;
  message: string;
  is_user: boolean;
  timestamp: string;
  session_id: string;
  imageUrl?: string;
  metadata?: {
    type?: 'food_analysis' | 'meal_suggestion' | 'general' | 'quick_action' | 'food_logging' | 'fridge_analysis';
    data?: any;
    image_type?: 'food' | 'fridge';
    analysis_mode?: 'logging' | 'analysis' | 'question' | 'fridge';
  };
}

interface Session {
  session_id: string;
  timestamp: string;
  messages: Message[];
}

interface QuickAction {
  label: string;
  icon: React.ReactNode;
  action: () => void;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'info';
}

// New interface for image analysis options
interface ImageAnalysisOption {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  action: (file: File) => void;
}

// Helper function for action button colors
const getActionColor = (color: string) => {
  const colorMap = {
    primary: {
      gradient: '#667eea 0%, #764ba2 100%',
      hoverGradient: '#5a67d8 0%, #6b46c1 100%',
      shadow: 'rgba(102, 126, 234, 0.3)'
    },
    secondary: {
      gradient: '#f093fb 0%, #f5576c 100%',
      hoverGradient: '#ec4899 0%, #ef4444 100%',
      shadow: 'rgba(240, 147, 251, 0.3)'
    },
    success: {
      gradient: '#4facfe 0%, #00f2fe 100%',
      hoverGradient: '#06b6d4 0%, #0891b2 100%',
      shadow: 'rgba(79, 172, 254, 0.3)'
    },
    warning: {
      gradient: '#ffecd2 0%, #fcb69f 100%',
      hoverGradient: '#f59e0b 0%, #f97316 100%',
      shadow: 'rgba(255, 236, 210, 0.3)'
    },
    error: {
      gradient: '#ff9a9e 0%, #fecfef 100%',
      hoverGradient: '#f87171 0%, #fb7185 100%',
      shadow: 'rgba(255, 154, 158, 0.3)'
    },
    info: {
      gradient: '#a8edea 0%, #fed6e3 100%',
      hoverGradient: '#06b6d4 0%, #ec4899 100%',
      shadow: 'rgba(168, 237, 234, 0.3)'
    }
  };
  return colorMap[color as keyof typeof colorMap] || colorMap.primary;
};

const Chat = () => {
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);
  const { triggerFoodLogged } = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<string>('');
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const chatContainerRef = useRef<null | HTMLDivElement>(null);
  const prevMessagesLengthRef = useRef<number>(messages.length);
  const userScrolledRef = useRef<boolean>(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [isMobile, setIsMobile] = useState(false);
  const [recordFoodDialog, setRecordFoodDialog] = useState(false);
  const [recordFoodResult, setRecordFoodResult] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [showQuickActions, setShowQuickActions] = useState(true);

  // New state for enhanced image analysis
  const [imageOptionsDialog, setImageOptionsDialog] = useState(false);
  const [selectedAnalysisMode, setSelectedAnalysisMode] = useState<'logging' | 'analysis' | 'question' | 'fridge' | null>(null);
  const [pendingImageFile, setPendingImageFile] = useState<File | null>(null);

  // Meal type selection for food logging
  const [selectedMealType, setSelectedMealType] = useState<string>('');
  const [showMealTypeSelector, setShowMealTypeSelector] = useState(false);

  // Pending consumption dialog state (same as HomePage)
  const [showPendingDialog, setShowPendingDialog] = useState(false);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [pendingAnalysis, setPendingAnalysis] = useState<any>(null);
  const [pendingImageUrl, setPendingImageUrl] = useState<string | null>(null);

  // Auto-detect meal type based on current time
  const autoDetectMealType = () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 11) return 'breakfast';
    if (hour >= 11 && hour < 16) return 'lunch';
    if (hour >= 16 && hour < 22) return 'dinner';
    return 'snack';
  };

  // Check if the input text suggests food logging
  const checkForFoodLogging = (text: string) => {
    const logKeywords = ['log', 'record', 'ate', 'eaten', 'had', 'consumed', 'just ate', 'just had'];
    const foodKeywords = ['food', 'meal', 'breakfast', 'lunch', 'dinner', 'snack'];
    
    const textLower = text.toLowerCase();
    const hasLogKeyword = logKeywords.some(keyword => textLower.includes(keyword));
    const hasFoodKeyword = foodKeywords.some(keyword => textLower.includes(keyword));
    
    return hasLogKeyword && hasFoodKeyword;
  };

  const quickActions: QuickAction[] = [
    {
      label: 'Meal Suggestion',
      icon: <LightbulbIcon />,
      action: () => setInput("What should I eat for "),
      color: 'secondary'
    },
    {
      label: 'Create Plan',
      icon: <AssignmentIcon />,
      action: () => setInput("What should I eat for dinner?"),
      color: 'success'
    },
    {
      label: 'My Progress',
      icon: <TrendingUpIcon />,
      action: () => setInput("How am I doing with my diabetes management?"),
      color: 'info'
    },
    {
      label: 'Health Tips',
      icon: <FavoriteIcon />,
      action: () => setInput("Give me some diabetes management tips"),
      color: 'warning'
    }
  ];

  // Enhanced image analysis options
  const imageAnalysisOptions: ImageAnalysisOption[] = [
    {
      id: 'food_logging',
      title: 'Log Food',
      description: 'Analyze and automatically log this food to your consumption history',
      icon: <CameraAltIcon sx={{ fontSize: 40 }} />,
      color: '#667eea',
      action: (file: File) => handleImageAnalysisSelection('logging', file)
    },
    {
      id: 'food_analysis',
      title: 'Analyze Food',
      description: 'Get detailed nutritional analysis without logging to history',
      icon: <SearchIcon sx={{ fontSize: 40 }} />,
      color: '#11998e',
      action: (file: File) => handleImageAnalysisSelection('analysis', file)
    },
    {
      id: 'food_question',
      title: 'Ask About Food',
      description: 'Upload food image and ask specific questions about it',
      icon: <QuestionAnswerIcon sx={{ fontSize: 40 }} />,
      color: '#f093fb',
      action: (file: File) => handleImageAnalysisSelection('question', file)
    },
    {
      id: 'fridge_analysis',
      title: 'Fridge Analysis',
      description: 'Analyze your fridge contents and get cooking suggestions',
      icon: <KitchenIcon sx={{ fontSize: 40 }} />,
      color: '#ff9a9e',
      action: (file: File) => handleImageAnalysisSelection('fridge', file)
    }
  ];

  const handleNewChat = () => {
    const newSessionId = uuidv4();
    console.log("Creating new chat session:", newSessionId);
    
    const newSession = {
      session_id: newSessionId,
      timestamp: new Date().toISOString(),
      messages: []
    };
    
    setSessions(prev => [...prev, newSession]);
    setCurrentSession(newSessionId);
    setMessages([]);
    setShowQuickActions(true);
  };

  useEffect(() => {
    const loadSessionsAndInitialize = async () => {
      try {
        await fetchSessions();
        await fetchUserStats();
      } catch (error) {
        console.error('Error initializing chat:', error);
      }
    };
    loadSessionsAndInitialize();
  }, []);

  useEffect(() => {
    if (currentSession) {
      fetchChatHistory();
    }
  }, [currentSession]);

  const fetchUserStats = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${config.API_URL}/coach/daily-insights`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUserStats(data);
      }
    } catch (error) {
      console.error('Error fetching user stats:', error);
    }
  };

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    if (chatContainerRef.current && !userScrolledRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      if (scrollHeight - scrollTop - clientHeight < 150) {
        messagesEndRef.current?.scrollIntoView({ behavior });
      }
    }
  };

  useEffect(() => {
    if (userScrolledRef.current) {
      return;
    }

    const chatContainer = chatContainerRef.current;
    if (!chatContainer) return;

    const newMessagesAdded = messages.length > prevMessagesLengthRef.current;

    if (newMessagesAdded) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else if (!isLoading && messages.length > 0) {
      scrollToBottom('smooth');
    }

    prevMessagesLengthRef.current = messages.length;
  }, [messages, isLoading]);

  const handleManualScroll = () => {
    userScrolledRef.current = true;
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    scrollTimeoutRef.current = setTimeout(() => {
      userScrolledRef.current = false;
    }, 1000);
  };

  useEffect(() => {
    const container = chatContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleManualScroll);
      return () => {
        container.removeEventListener('scroll', handleManualScroll);
        // Clear timeout on cleanup
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
        }
      };
    }
  }, []);

  // Cleanup image preview URLs on component unmount
  useEffect(() => {
    return () => {
      if (imagePreviewUrl) {
        URL.revokeObjectURL(imagePreviewUrl);
      }
    };
  }, [imagePreviewUrl]);

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.log("No token found, redirecting to login");
        navigate('/login');
        return;
      }

      const response = await fetch(`${config.API_URL}/chat/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
        
        // Only set current session if none exists and sessions are available
        if (!currentSession && data.sessions && data.sessions.length > 0) {
          setCurrentSession(data.sessions[0].session_id);
        } else if (!currentSession && (!data.sessions || data.sessions.length === 0)) {
          // If no sessions exist, create a new one
          handleNewChat();
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
      // If there's an error and no current session, create a new one
      if (!currentSession) {
        handleNewChat();
      }
    }
  };

  const fetchChatHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token || !currentSession) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      
      const response = await fetch(`${config.API_URL}/chat/history?session_id=${currentSession}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Only update messages if the session hasn't changed while loading
        if (currentSession === data.session_id || !data.session_id) {
          setMessages(data.messages || []);
          setShowQuickActions(!data.messages || data.messages.length === 0);
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        console.error('Failed to fetch chat history:', response.status);
        setMessages([]);
        setShowQuickActions(true);
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
      setMessages([]);
      setShowQuickActions(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() && !selectedImage) return;

    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    // Capture meal type before clearing state
    const currentMealType = selectedMealType || autoDetectMealType();
    const currentAnalysisMode = selectedAnalysisMode;
    const currentShowMealTypeSelector = showMealTypeSelector;

    const messageId = uuidv4();
    const userMessage: Message = {
      id: messageId,
      message: input,
      is_user: true,
      timestamp: new Date().toISOString(),
      session_id: currentSession,
      imageUrl: imagePreviewUrl || undefined,
      metadata: selectedImage ? {
        type: 'food_analysis',
        image_type: selectedAnalysisMode === 'fridge' ? 'fridge' : 'food',
        analysis_mode: selectedAnalysisMode || 'analysis'
      } : undefined
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    
    // Clean up image-related state and URLs
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
    setSelectedImage(null);
    setImagePreviewUrl(null);
    setSelectedAnalysisMode(null);
    setSelectedMealType('');
    setShowMealTypeSelector(false);
    setIsLoading(true);
    setShowQuickActions(false);

    try {
      let response;
      
      if (selectedImage) {
        // Handle image + message with enhanced analysis mode
        const formData = new FormData();
        formData.append('message', input);
        formData.append('image', selectedImage);
        formData.append('session_id', currentSession);
        formData.append('analysis_mode', currentAnalysisMode || 'analysis');
        
        // Add meal type if in logging mode
        if (currentAnalysisMode === 'logging') {
          formData.append('meal_type', currentMealType);
        }

        response = await fetch(`${config.API_URL}/chat/message-with-image`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });
      } else {
        // Handle text-only message
        const messageBody: any = {
          message: input,
          session_id: currentSession,
        };
        
        // Add meal type if food logging is detected
        if (currentShowMealTypeSelector && checkForFoodLogging(input)) {
          messageBody.meal_type = currentMealType;
        }
        
        response = await fetch(`${config.API_URL}/chat/message`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(messageBody),
        });
      }

      if (response.ok) {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let aiResponse = '';
        let aiMessageId = uuidv4();
        let pendingData: any = null;

        // Add placeholder AI message
        const aiMessage: Message = {
          id: aiMessageId,
          message: '',
          is_user: false,
          timestamp: new Date().toISOString(),
          session_id: currentSession,
          metadata: selectedImage ? {
            type: selectedAnalysisMode === 'fridge' ? 'fridge_analysis' : 'food_analysis',
            image_type: selectedAnalysisMode === 'fridge' ? 'fridge' : 'food',
            analysis_mode: selectedAnalysisMode || 'analysis'
          } : undefined
        };
        setMessages(prev => [...prev, aiMessage]);

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);

            // Try to parse chunk as SSE lines first
            const lines = chunk.split('\n');
            let parsedContent = false;

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.content) {
                    aiResponse += data.content;
                    parsedContent = true;
                  }
                  // Check for pending consumption data
                  if (data.pending_id && data.analysis) {
                    pendingData = data;
                  }
                } catch (e) {
                  // Not JSON, treat remainder as plain text
                  aiResponse += line.slice(6);
                  parsedContent = true;
                }
              }
            }

            // If nothing parsed via SSE, treat whole chunk as plain text
            if (!parsedContent) {
              aiResponse += chunk;
            }

            // Update message with current aggregated response
            setMessages(prev =>
              prev.map(msg =>
                msg.id === aiMessageId
                  ? { ...msg, message: aiResponse }
                  : msg
              )
            );
          }
          
          // Show pending consumption dialog if this was a food logging operation
          if (currentAnalysisMode === 'logging' && pendingData) {
            setPendingId(pendingData.pending_id);
            setPendingAnalysis(pendingData.analysis);
            setPendingImageUrl(pendingData.image_url || null);
            setShowPendingDialog(true);
          } else if (currentAnalysisMode === 'logging' || (currentShowMealTypeSelector && checkForFoodLogging(userMessage.message))) {
            // Trigger homepage refresh for other food logging operations
            triggerFoodLogged();
          }
        } else {
          // Handle non-streamed response (fallback)
          const responseData = await response.json();
          if (responseData.pending_id && responseData.analysis && currentAnalysisMode === 'logging') {
            setPendingId(responseData.pending_id);
            setPendingAnalysis(responseData.analysis);
            setPendingImageUrl(responseData.image_url || null);
            setShowPendingDialog(true);
          }
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: uuidv4(),
        message: 'Sorry, I encountered an error. Please try again.',
        is_user: false,
        timestamp: new Date().toISOString(),
        session_id: currentSession,
      };
      setMessages(prev => [...prev, errorMessage]);
      setShowQuickActions(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionChange = (event: SelectChangeEvent<string>) => {
    const newSessionId = event.target.value;
    if (newSessionId !== currentSession) {
      // Clear messages immediately to prevent showing old messages
      setMessages([]);
      setIsLoading(true);
      setCurrentSession(newSessionId);
    }
  };

  const handleClearHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${config.API_URL}/chat/history?session_id=${currentSession}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setMessages([]);
        setShowQuickActions(true);
      }
    } catch (error) {
      console.error('Error clearing history:', error);
    }
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Image size must be less than 10MB');
      return;
    }

    // Store the file and show options dialog
    setPendingImageFile(file);
    setImageOptionsDialog(true);
  };

  const handleImageAnalysisSelection = (mode: 'logging' | 'analysis' | 'question' | 'fridge', file: File) => {
    setSelectedAnalysisMode(mode);
    setSelectedImage(file);
    
    // Clean up previous preview URL to prevent memory leaks
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
    
    // Create preview URL
    const previewUrl = URL.createObjectURL(file);
    setImagePreviewUrl(previewUrl);
    
    // Close dialogs
    setImageOptionsDialog(false);
    setPendingImageFile(null);
    
    // Set appropriate input based on mode
    switch (mode) {
      case 'logging':
        setInput('Please analyze this food and log it to my consumption history.');
        setShowMealTypeSelector(true);
        setSelectedMealType(''); // Reset meal type
        break;
      case 'analysis':
        setInput('Please provide a detailed nutritional analysis of this food.');
        setShowMealTypeSelector(false);
        break;
      case 'question':
        setInput('I have a question about this food: ');
        setShowMealTypeSelector(false);
        break;
      case 'fridge':
        setInput('Please analyze my fridge contents and suggest what I can cook.');
        setShowMealTypeSelector(false);
        break;
    }
  };

  const handleRecordFoodButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleCloseRecordDialog = () => {
    setRecordFoodDialog(false);
    setRecordFoodResult(null);
  };

  const handleQuickAction = (action: QuickAction) => {
    action.action();
    // Focus on input after setting text
    setTimeout(() => {
      const inputElement = document.querySelector('input[placeholder*="Ask your AI health coach"]') as HTMLInputElement;
      if (inputElement) {
        inputElement.focus();
        inputElement.setSelectionRange(inputElement.value.length, inputElement.value.length);
      }
    }, 100);
  };

  // Pending consumption dialog handlers (same as HomePage)
  const handlePendingAccept = () => {
    // Close dialog and refresh data
    setShowPendingDialog(false);
    setPendingId(null);
    setPendingAnalysis(null);
    setPendingImageUrl(null);
    // Refresh user stats
    fetchUserStats();
  };

  const handlePendingDelete = () => {
    // Close dialog and clean up
    setShowPendingDialog(false);
    setPendingId(null);
    setPendingAnalysis(null);
    setPendingImageUrl(null);
  };

  const formatMessage = (message: string) => {
    // Enhanced message formatting with better styling
    return (
      <ReactMarkdown
        components={{
          p: ({ children }) => <Typography variant="body1" sx={{ mb: 1 }}>{children}</Typography>,
          strong: ({ children }) => <Typography component="span" sx={{ fontWeight: 'bold', color: 'primary.main' }}>{children}</Typography>,
          em: ({ children }) => <Typography component="span" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>{children}</Typography>,
          ul: ({ children }) => <Box component="ul" sx={{ pl: 2, mb: 1 }}>{children}</Box>,
          li: ({ children }) => <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>{children}</Typography>,
          h3: ({ children }) => <Typography variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>{children}</Typography>,
          code: ({ children }) => (
            <Typography 
              component="code" 
              sx={{ 
                bgcolor: 'grey.100', 
                px: 0.5, 
                py: 0.25, 
                borderRadius: 0.5, 
                fontFamily: 'monospace',
                fontSize: '0.875rem'
              }}
            >
              {children}
            </Typography>
          ),
        }}
      >
        {message}
      </ReactMarkdown>
    );
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: { xs: 0.5, sm: 2 },
      px: { xs: 0.5, sm: 2 },
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
        animation: `${gradientShift} 8s ease infinite`,
        backgroundSize: '400% 400%',
        zIndex: 0,
      }
    }}>
      <Container maxWidth="sm" sx={{ 
        height: '100vh', 
        display: 'flex', 
        flexDirection: 'column',
        position: 'relative',
        zIndex: 1,
        px: { xs: 0, sm: 3 }
      }}>
      {/* Header */}
      <Fade in={true} timeout={1000}>
        <Paper elevation={0} sx={{ 
          p: { xs: 2, sm: 3 }, 
          mb: { xs: 1, sm: 2 },
          background: 'rgba(255, 255, 255, 0.25)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: { xs: '16px', sm: '24px' },
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          animation: `${fadeInScale} 0.8s ease-out`,
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
            borderRadius: { xs: '16px', sm: '24px' },
            animation: `${shimmer} 3s ease-in-out infinite`,
            backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
            backgroundSize: '200px 100%',
            backgroundRepeat: 'no-repeat',
          }
        }}>
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            {/* Main header row */}
            <Box sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: { xs: 2, sm: 0 }
            }}>
              {/* Left side - Title */}
              <Slide direction="right" in={true} timeout={800}>
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: { xs: 1.5, sm: 2 }
                }}>
                  <Box sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '50%',
                    p: { xs: 0.75, sm: 1 },
                    boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                    animation: `${pulse} 2s ease-in-out infinite`,
                  }}>
                    <Avatar sx={{ 
                      bgcolor: 'rgba(255, 255, 255, 0.9)', 
                      color: '#667eea',
                      width: { xs: 32, sm: 40 },
                      height: { xs: 32, sm: 40 }
                    }}>
                      <SmartToyIcon sx={{ fontSize: { xs: 18, sm: 24 } }} />
                    </Avatar>
                  </Box>
                  <Box>
                    <Typography variant="h6" sx={{ 
                      fontSize: { xs: '1.1rem', sm: '1.5rem' },
                      fontWeight: 'bold',
                      color: 'white',
                      textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                      animation: `${bounceIn} 1s ease-out 0.3s both`,
                      lineHeight: 1.2
                    }}>
                      🤖 AI Health Coach
                    </Typography>
                    <Typography variant="body2" sx={{ 
                      fontSize: { xs: '0.8rem', sm: '0.875rem' },
                      color: 'rgba(255, 255, 255, 0.9)',
                      textShadow: '0 1px 3px rgba(0,0,0,0.2)',
                      animation: `${slideInUp} 0.8s ease-out 0.5s both`,
                      display: { xs: 'none', sm: 'block' }
                    }}>
                      Your intelligent diabetes management companion
                    </Typography>
                  </Box>
                </Box>
              </Slide>
              
              {/* Right side - Buttons */}
              <Slide direction="left" in={true} timeout={1000}>
                <Zoom in={true} timeout={1000} style={{ transitionDelay: '0.6s' }}>
                  <Box sx={{ 
                    display: 'flex',
                    gap: { xs: 0.5, sm: 1 },
                    background: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.25)',
                    borderRadius: { xs: '12px', sm: '16px' }, 
                    p: { xs: 0.5, sm: 0.75 },
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                  }}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleNewChat}
                      sx={{
                        background: 'rgba(255, 255, 255, 0.9)',
                        color: '#333',
                        fontWeight: 'bold',
                        fontSize: { xs: '0.65rem', sm: '0.75rem' },
                        px: { xs: 1.5, sm: 2 },
                        py: { xs: 0.6, sm: 0.8 },
                        minWidth: { xs: '70px', sm: '80px' },
                        height: { xs: '28px', sm: '32px' },
                        border: 'none',
                        borderRadius: { xs: '8px', sm: '10px' },
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        textTransform: 'none',
                        letterSpacing: '0.5px',
                        '&:hover': {
                          background: 'white',
                          transform: 'translateY(-1px)',
                          boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
                        },
                        '&:active': {
                          transform: 'translateY(0px)',
                        },
                        transition: 'all 0.2s ease',
                      }}
                    >
                      NEW CHAT
                    </Button>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleClearHistory}
                      sx={{
                        background: 'rgba(255, 255, 255, 0.9)',
                        color: '#333',
                        fontWeight: 'bold',
                        fontSize: { xs: '0.65rem', sm: '0.75rem' },
                        px: { xs: 1.5, sm: 2 },
                        py: { xs: 0.6, sm: 0.8 },
                        minWidth: { xs: '60px', sm: '70px' },
                        height: { xs: '28px', sm: '32px' },
                        border: 'none',
                        borderRadius: { xs: '8px', sm: '10px' },
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        textTransform: 'none',
                        letterSpacing: '0.5px',
                        '&:hover': {
                          background: 'white',
                          transform: 'translateY(-1px)',
                          boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
                        },
                        '&:active': {
                          transform: 'translateY(0px)',
                        },
                        transition: 'all 0.2s ease',
                      }}
                    >
                      CLEAR
                    </Button>
                  </Box>
                </Zoom>
              </Slide>
            </Box>

            {/* Stats chips row */}
            {userStats && (
              <Slide direction="up" in={true} timeout={1000} style={{ transitionDelay: '0.8s' }}>
                <Box sx={{ 
                  display: 'flex',
                  gap: 1.5, 
                  justifyContent: 'center',
                  alignItems: 'center',
                  mt: { xs: 0, sm: 2 }
                }}>
                  <Zoom in={true} timeout={800} style={{ transitionDelay: '1.0s' }}>
                    <Chip 
                      icon={<LocalFireDepartmentIcon sx={{ fontSize: { xs: 14, sm: 16 } }} />} 
                      label={`${userStats.today_totals?.calories || 0} cal`}
                      size="small"
                      sx={{ 
                        background: 'linear-gradient(135deg, rgba(255,87,34,0.85) 0%, rgba(255,152,0,0.85) 100%)',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: { xs: '0.7rem', sm: '0.75rem' },
                        height: { xs: 26, sm: 28 },
                        '& .MuiChip-label': {
                          px: { xs: 1.5, sm: 2 }
                        },
                        boxShadow: '0 4px 12px rgba(255,87,34,0.3)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: '0 6px 16px rgba(255,87,34,0.4)',
                        },
                        transition: 'all 0.3s ease',
                      }}
                    />
                  </Zoom>
                  <Zoom in={true} timeout={800} style={{ transitionDelay: '1.2s' }}>
                    <Chip 
                      icon={<FavoriteIcon sx={{ fontSize: { xs: 14, sm: 16 } }} />} 
                      label={`${Math.round(userStats.diabetes_adherence || 0)}% score`}
                      size="small"
                      sx={{ 
                        background: 'linear-gradient(135deg, rgba(233,30,99,0.85) 0%, rgba(156,39,176,0.85) 100%)',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: { xs: '0.7rem', sm: '0.75rem' },
                        height: { xs: 26, sm: 28 },
                        '& .MuiChip-label': {
                          px: { xs: 1.5, sm: 2 }
                        },
                        boxShadow: '0 4px 12px rgba(233,30,99,0.3)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: '0 6px 16px rgba(233,30,99,0.4)',
                        },
                        transition: 'all 0.3s ease',
                      }}
                    />
                  </Zoom>
                </Box>
              </Slide>
            )}
          </Box>
        </Paper>
      </Fade>



      {/* Quick Actions */}
      {showQuickActions && messages.length === 0 && (
        <Fade in={showQuickActions} timeout={1200}>
          <Paper elevation={0} sx={{ 
            p: { xs: 1.5, sm: 3 },
            mb: { xs: 1, sm: 2 },
            borderRadius: { xs: '16px', sm: '24px' },
            background: 'rgba(255, 255, 255, 0.25)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            animation: `${slideInUp} 0.8s ease-out 0.3s both`,
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
              borderRadius: { xs: '16px', sm: '24px' },
              animation: `${shimmer} 3s ease-in-out infinite`,
              backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
              backgroundSize: '200px 100%',
              backgroundRepeat: 'no-repeat',
            }
          }}>
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              <Typography variant="h6" gutterBottom sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1,
                color: 'white',
                fontWeight: 700,
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                animation: `${bounceIn} 1s ease-out 0.5s both`
              }}>
                <Box sx={{
                  background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
                  borderRadius: '50%',
                  p: 1,
                  boxShadow: '0 4px 12px rgba(255, 215, 0, 0.4)',
                  animation: `${pulse} 2s ease-in-out infinite`,
                }}>
                  <LightbulbIcon sx={{ color: 'white' }} />
                </Box>
                Quick Actions
              </Typography>
              <Typography variant="body2" sx={{ 
                mb: 2,
                color: 'rgba(255, 255, 255, 0.9)',
                textShadow: '0 1px 3px rgba(0,0,0,0.2)',
                animation: `${slideInUp} 0.8s ease-out 0.7s both`
              }}>
                Get started with these common requests:
              </Typography>
            </Box>
            <Grid container spacing={{ xs: 1.5, sm: 2 }} sx={{ position: 'relative', zIndex: 1 }}>
              {quickActions.map((action, index) => (
                <Grid item xs={6} sm={6} md={4} key={index}>
                  <Zoom in={true} timeout={600} style={{ transitionDelay: `${0.9 + index * 0.1}s` }}>
                    <Button
                      variant="contained"
                      fullWidth
                      startIcon={action.icon}
                      onClick={() => handleQuickAction(action)}
                      sx={{ 
                        py: { xs: 1.5, sm: 2 },
                        px: { xs: 1, sm: 2 },
                        borderRadius: { xs: '12px', sm: '16px' },
                        background: `linear-gradient(135deg, ${getActionColor(action.color).gradient})`,
                        color: 'white',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        boxShadow: `0 4px 12px ${getActionColor(action.color).shadow}`,
                        fontWeight: 600,
                        fontSize: { xs: '0.8rem', sm: '0.875rem' },
                        textTransform: 'none',
                        justifyContent: 'flex-start',
                        '& .MuiButton-startIcon': {
                          marginRight: { xs: 0.5, sm: 1 },
                          '& > *:nth-of-type(1)': {
                            fontSize: { xs: 16, sm: 20 }
                          }
                        },
                        '&:hover': {
                          transform: 'translateY(-3px) scale(1.02)',
                          boxShadow: `0 8px 20px ${getActionColor(action.color).shadow}`,
                          background: `linear-gradient(135deg, ${getActionColor(action.color).hoverGradient})`,
                        },
                        '&:active': {
                          transform: 'translateY(-1px) scale(0.98)',
                        },
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      }}
                    >
                      {action.label}
                    </Button>
                  </Zoom>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Fade>
      )}

      {/* Messages */}
      <Fade in={true} timeout={1500}>
        <Paper 
          elevation={0} 
          sx={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            overflow: 'hidden',
            mb: { xs: 1, sm: 2 },
            borderRadius: { xs: '16px', sm: '24px' },
            background: 'rgba(255, 255, 255, 0.25)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            animation: `${fadeInScale} 1s ease-out 1s both`,
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
              borderRadius: { xs: '16px', sm: '24px' },
              animation: `${shimmer} 4s ease-in-out infinite`,
              backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)',
              backgroundSize: '200px 100%',
              backgroundRepeat: 'no-repeat',
            }
          }}
        >
        <Box
          ref={chatContainerRef}
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: { xs: 1.5, sm: 3 },
            display: 'flex',
            flexDirection: 'column',
            gap: { xs: 1.5, sm: 2 },
            position: 'relative',
            zIndex: 1,
          }}
        >
          {messages.length === 0 && !showQuickActions && (
            <Fade in={true} timeout={2000}>
              <Box sx={{ 
                textAlign: 'center', 
                py: 6,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2
              }}>
                <Box sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '50%',
                  p: 3,
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)',
                  animation: `${pulse} 2s ease-in-out infinite`,
                }}>
                  <SmartToyIcon sx={{ fontSize: 40, color: 'white' }} />
                </Box>
                <Typography variant="h6" sx={{
                  color: 'white',
                  fontWeight: 600,
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  animation: `${bounceIn} 1s ease-out 2.2s both`
                }}>
                  Start a conversation with your AI health coach
                </Typography>
                <Typography variant="body2" sx={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  textShadow: '0 1px 3px rgba(0,0,0,0.2)',
                  animation: `${slideInUp} 0.8s ease-out 2.4s both`
                }}>
                  Ask about nutrition, meal planning, or diabetes management
                </Typography>
              </Box>
            </Fade>
          )}

          {messages.map((message, index) => (
            <Slide key={message.id} direction="up" in={true} timeout={300 + index * 100}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: message.is_user ? 'flex-end' : 'flex-start',
                  mb: 1,
                }}
              >
                <Box
                  sx={{
                    maxWidth: { xs: '85%', sm: '70%' },
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: { xs: 0.75, sm: 1 },
                    flexDirection: message.is_user ? 'row-reverse' : 'row',
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: message.is_user ? 'primary.main' : 'secondary.main',
                      width: { xs: 28, sm: 32 },
                      height: { xs: 28, sm: 32 },
                    }}
                  >
                    {message.is_user ? <PersonIcon sx={{ fontSize: { xs: 16, sm: 20 } }} /> : <SmartToyIcon sx={{ fontSize: { xs: 16, sm: 20 } }} />}
                  </Avatar>
                  
                  <Paper
                    elevation={1}
                    sx={{
                      p: { xs: 1.5, sm: 2 },
                      bgcolor: message.is_user ? 'primary.main' : 'grey.100',
                      color: message.is_user ? 'white' : 'text.primary',
                      borderRadius: { xs: 1.5, sm: 2 },
                      position: 'relative',
                      animation: message.metadata?.type === 'food_analysis' || message.metadata?.type === 'fridge_analysis' ? `${pulse} 2s ease-in-out` : 'none',
                      border: message.metadata?.type === 'food_analysis' || message.metadata?.type === 'fridge_analysis' ? '2px solid' : 'none',
                      borderColor: message.metadata?.type === 'food_analysis' || message.metadata?.type === 'fridge_analysis' ? 'success.main' : 'transparent',
                    }}
                  >
                    {message.imageUrl && (
                      <Box sx={{ mb: 1 }}>
                        <img
                          src={message.imageUrl}
                          alt="Uploaded"
                          style={{
                            maxWidth: '100%',
                            maxHeight: '200px',
                            borderRadius: '8px',
                          }}
                        />
                      </Box>
                    )}
                    
                    {message.metadata?.type === 'food_analysis' && (
                      <Chip
                        label={`Food ${message.metadata.analysis_mode === 'logging' ? 'Logged' : 'Analysis'}`}
                        color="success"
                        size="small"
                        sx={{ mb: 1 }}
                      />
                    )}

                    {message.metadata?.type === 'fridge_analysis' && (
                      <Chip
                        label="Fridge Analysis"
                        color="info"
                        size="small"
                        sx={{ mb: 1 }}
                      />
                    )}
                    
                    <Box sx={{ '& > *:last-child': { mb: 0 } }}>
                      {formatMessage(message.message)}
                    </Box>
                    
                    <Typography
                      variant="caption"
                      sx={{
                        display: 'block',
                        mt: 1,
                        opacity: 0.7,
                        fontSize: '0.75rem',
                      }}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </Typography>
                  </Paper>
                </Box>
              </Box>
            </Slide>
          ))}

          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                  <SmartToyIcon />
                </Avatar>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    bgcolor: 'grey.100',
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="text.secondary">
                    AI is thinking...
                  </Typography>
                </Paper>
              </Box>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>
      </Paper>
      </Fade>

      {/* Input Area */}
      <Fade in={true} timeout={1800}>
        <Paper elevation={0} sx={{ 
          p: { xs: 1.5, sm: 3 },
          borderRadius: { xs: '16px', sm: '24px' },
          background: 'rgba(255, 255, 255, 0.25)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          animation: `${slideInUp} 0.8s ease-out 1.2s both`,
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(45deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04))',
            borderRadius: { xs: '16px', sm: '24px' },
            animation: `${shimmer} 4s ease-in-out infinite`,
            backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
            backgroundSize: '200px 100%',
            backgroundRepeat: 'no-repeat',
          }
        }}>
        {selectedImage && (
          <Box sx={{ mb: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {selectedAnalysisMode === 'fridge' ? <KitchenIcon color="primary" /> : <CameraAltIcon color="primary" />}
              <Typography variant="body2">
                {selectedAnalysisMode === 'fridge' ? 'Fridge image attached' : 'Food image attached'} 
                {selectedAnalysisMode && ` (${selectedAnalysisMode} mode)`}
              </Typography>
              <IconButton size="small" onClick={() => { 
                setSelectedImage(null); 
                setImagePreviewUrl(null); 
                setSelectedAnalysisMode(null);
              }}>
                <CloseIcon />
              </IconButton>
            </Box>
            {imagePreviewUrl && (
              <img
                src={imagePreviewUrl}
                alt="Preview"
                style={{ maxWidth: '100px', maxHeight: '100px', borderRadius: '4px' }}
              />
            )}
          </Box>
        )}

        {/* Meal Type Selector for Food Logging */}
        {showMealTypeSelector && (
          <Box sx={{ mb: 2, p: 2, bgcolor: 'primary.50', borderRadius: 2, border: '1px solid', borderColor: 'primary.200' }}>
            <Typography variant="subtitle2" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
              Select Meal Type:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                size="small"
                variant={selectedMealType === '' ? 'contained' : 'outlined'}
                onClick={() => setSelectedMealType('')}
                sx={{ minWidth: 'auto' }}
              >
                🤖 Auto ({autoDetectMealType()})
              </Button>
              <Button
                size="small"
                variant={selectedMealType === 'breakfast' ? 'contained' : 'outlined'}
                onClick={() => setSelectedMealType('breakfast')}
                sx={{ minWidth: 'auto' }}
              >
                🌅 Breakfast
              </Button>
              <Button
                size="small"
                variant={selectedMealType === 'lunch' ? 'contained' : 'outlined'}
                onClick={() => setSelectedMealType('lunch')}
                sx={{ minWidth: 'auto' }}
              >
                🥗 Lunch
              </Button>
              <Button
                size="small"
                variant={selectedMealType === 'dinner' ? 'contained' : 'outlined'}
                onClick={() => setSelectedMealType('dinner')}
                sx={{ minWidth: 'auto' }}
              >
                🍽️ Dinner
              </Button>
              <Button
                size="small"
                variant={selectedMealType === 'snack' ? 'contained' : 'outlined'}
                onClick={() => setSelectedMealType('snack')}
                sx={{ minWidth: 'auto' }}
              >
                🍿 Snacks
              </Button>
            </Box>
          </Box>
        )}

        <Box sx={{ 
          display: 'flex', 
          gap: { xs: 1, sm: 2 }, 
          alignItems: 'flex-end', 
          position: 'relative', 
          zIndex: 1 
        }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => {
              const value = e.target.value;
              setInput(value);
              
              // Show meal type selector if text suggests food logging
              if (checkForFoodLogging(value) && !selectedImage) {
                setShowMealTypeSelector(true);
              } else if (!selectedImage && selectedAnalysisMode !== 'logging') {
                setShowMealTypeSelector(false);
              }
            }}
            placeholder="Ask your AI health coach anything, upload food photos, or just type what you ate to log it instantly - no meal plan needed!"
            variant="outlined"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: { xs: '16px', sm: '20px' },
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
                fontSize: { xs: '0.9rem', sm: '1rem' },
                '&:hover': {
                  boxShadow: '0 6px 16px rgba(0, 0, 0, 0.1)',
                  transform: 'translateY(-1px)',
                },
                '&.Mui-focused': {
                  boxShadow: '0 8px 20px rgba(102, 126, 234, 0.2)',
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.3s ease',
              },
              '& .MuiOutlinedInput-input': {
                color: '#333',
                fontWeight: 500,
                fontSize: { xs: '0.9rem', sm: '1rem' },
                padding: { xs: '12px 14px', sm: '16.5px 14px' },
              },
              '& .MuiInputBase-input::placeholder': {
                color: 'rgba(0, 0, 0, 0.6)',
                fontWeight: 400,
                fontSize: { xs: '0.85rem', sm: '1rem' },
              }
            }}
          />
          <Zoom in={true} timeout={600} style={{ transitionDelay: '1.4s' }}>
            <Tooltip title="Enhanced Image Analysis">
              <IconButton onClick={handleRecordFoodButtonClick}
                sx={{
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  color: 'white',
                  width: { xs: 44, sm: 52 },
                  height: { xs: 44, sm: 52 },
                  borderRadius: '50%',
                  boxShadow: '0 4px 12px rgba(240, 147, 251, 0.4)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  '&:hover': { 
                    background: 'linear-gradient(135deg, #ec4899 0%, #ef4444 100%)',
                    transform: 'translateY(-2px) scale(1.05)',
                    boxShadow: '0 8px 20px rgba(240, 147, 251, 0.6)',
                  },
                  '&:active': {
                    transform: 'translateY(0px) scale(0.95)',
                  },
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <PhotoCameraIcon sx={{ fontSize: { xs: 20, sm: 24 } }} />
              </IconButton>
            </Tooltip>
          </Zoom>
          <Zoom in={true} timeout={600} style={{ transitionDelay: '1.6s' }}>
            <Tooltip title="Send Message">
              <span>
                <IconButton
                  onClick={handleSendMessage}
                  disabled={(!input.trim() && !selectedImage) || isLoading}
                  sx={{
                    background: (!input.trim() && !selectedImage) || isLoading 
                      ? 'rgba(0, 0, 0, 0.12)'
                      : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    width: { xs: 44, sm: 52 },
                    height: { xs: 44, sm: 52 },
                    borderRadius: '50%',
                    boxShadow: (!input.trim() && !selectedImage) || isLoading 
                      ? 'none'
                      : '0 4px 12px rgba(102, 126, 234, 0.4)',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    '&:hover': !isLoading && (input.trim() || selectedImage) ? { 
                      background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                      transform: 'translateY(-2px) scale(1.05)',
                      boxShadow: '0 8px 20px rgba(102, 126, 234, 0.6)',
                    } : {},
                    '&:active': !isLoading && (input.trim() || selectedImage) ? {
                      transform: 'translateY(0px) scale(0.95)',
                    } : {},
                    '&:disabled': { 
                      background: 'rgba(0, 0, 0, 0.12)',
                      color: 'rgba(0, 0, 0, 0.26)',
                      transform: 'none',
                      boxShadow: 'none',
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}
                >
                  {isLoading ? (
                    <CircularProgress size={20} sx={{ color: 'white' }} />
                  ) : (
                    <SendIcon sx={{ fontSize: { xs: 20, sm: 24 } }} />
                  )}
                </IconButton>
              </span>
            </Tooltip>
          </Zoom>
        </Box>
      </Paper>
      </Fade>

      {/* Hidden file inputs */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        accept="image/*"
        onChange={handleImageUpload}
      />

      {/* Enhanced Image Analysis Options Dialog */}
      <Dialog 
        open={imageOptionsDialog} 
        onClose={() => {
          setImageOptionsDialog(false);
          setPendingImageFile(null);
        }} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: { borderRadius: 3 }
        }}
      >
        <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
                        <PhotoCameraIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
          <Typography variant="h5" component="div" sx={{ fontWeight: 'bold' }}>
            Choose Analysis Type
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            How would you like to analyze your image?
          </Typography>
        </DialogTitle>
        
        <DialogContent sx={{ p: 3 }}>
          <Grid container spacing={3}>
            {imageAnalysisOptions.map((option) => (
              <Grid item xs={12} sm={6} key={option.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    transition: 'all 0.3s ease-in-out',
                    border: '2px solid transparent',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      borderColor: option.color,
                      boxShadow: `0 8px 25px ${alpha(option.color, 0.3)}`,
                    }
                  }}
                  onClick={() => pendingImageFile && option.action(pendingImageFile)}
                >
                  <CardContent sx={{ p: 3, textAlign: 'center' }}>
                    <Box sx={{ color: option.color, mb: 2 }}>
                      {option.icon}
                    </Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                      {option.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5 }}>
                      {option.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        
        <DialogActions sx={{ p: 3, pt: 0 }}>
          <Button 
            onClick={() => {
              setImageOptionsDialog(false);
              setPendingImageFile(null);
            }}
                          startIcon={<CloseIcon />}
          >
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

      {/* Food Analysis Result Dialog */}
      <Dialog open={recordFoodDialog} onClose={handleCloseRecordDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RestaurantIcon color="success" />
          Food Analysis Complete
        </DialogTitle>
        <DialogContent>
          {recordFoodResult && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {recordFoodResult.food_name}
              </Typography>
              
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center', py: 1 }}>
                      <LocalFireDepartmentIcon color="error" />
                      <Typography variant="h6">{recordFoodResult.nutritional_info?.calories || 'N/A'}</Typography>
                      <Typography variant="caption">Calories</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center', py: 1 }}>
                      <FitnessCenterIcon color="success" />
                      <Typography variant="h6">{recordFoodResult.nutritional_info?.protein || 'N/A'}g</Typography>
                      <Typography variant="caption">Protein</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center', py: 1 }}>
                      <GrainIcon color="warning" />
                      <Typography variant="h6">{recordFoodResult.nutritional_info?.carbohydrates || 'N/A'}g</Typography>
                      <Typography variant="caption">Carbs</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center', py: 1 }}>
                      <Typography variant="h6">{recordFoodResult.nutritional_info?.fat || 'N/A'}g</Typography>
                      <Typography variant="caption">Fat</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Alert 
                severity={
                  recordFoodResult.medical_rating?.diabetes_suitability?.toLowerCase() === 'high' ? 'success' :
                  recordFoodResult.medical_rating?.diabetes_suitability?.toLowerCase() === 'medium' ? 'warning' : 'error'
                }
                sx={{ mb: 2 }}
              >
                <Typography variant="subtitle2">
                  Diabetes Suitability: {recordFoodResult.medical_rating?.diabetes_suitability || 'Unknown'}
                </Typography>
                {recordFoodResult.medical_rating?.diabetes_notes && (
                  <Typography variant="body2">
                    {recordFoodResult.medical_rating.diabetes_notes}
                  </Typography>
                )}
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseRecordDialog}>Close</Button>
          <Button variant="contained" onClick={() => navigate('/consumption-history')}>
            View History
          </Button>
        </DialogActions>
      </Dialog>

      {/* Pending Consumption Dialog */}
      <PendingConsumptionDialog
        open={showPendingDialog}
        onClose={() => setShowPendingDialog(false)}
        pendingId={pendingId}
        analysisData={pendingAnalysis}
        imageUrl={pendingImageUrl || undefined}
        onAccept={handlePendingAccept}
        onDelete={handlePendingDelete}
      />
      </Container>
    </Box>
  );
};

export default Chat; 