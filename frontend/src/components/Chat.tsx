import React, { useState, useEffect, useRef } from 'react';
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

// Animations
const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-3px); }
  100% { transform: translateY(0px); }
`;

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
`;

const shimmer = keyframes`
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
`;

const gradientShift = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

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

const Chat = () => {
  const theme = useTheme();
  const [loaded, setLoaded] = useState(false);
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
      action: () => setInput("Create an adaptive meal plan for me"),
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
        formData.append('analysis_mode', selectedAnalysisMode || 'analysis');

        response = await fetch(`${config.API_URL}/chat/message-with-image`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });
      } else {
        // Handle text-only message
        response = await fetch(`${config.API_URL}/chat/message`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: input,
            session_id: currentSession,
          }),
        });
      }

      if (response.ok) {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let aiResponse = '';
        let aiMessageId = uuidv4();

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
        break;
      case 'analysis':
        setInput('Please provide a detailed nutritional analysis of this food.');
        break;
      case 'question':
        setInput('I have a question about this food: ');
        break;
      case 'fridge':
        setInput('Please analyze my fridge contents and suggest what I can cook.');
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
    <Container maxWidth="lg" sx={{ height: '100vh', display: 'flex', flexDirection: 'column', py: 2 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 2, mb: 2, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'white', color: 'primary.main' }}>
              <SmartToyIcon />
            </Avatar>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                🤖 AI Health Coach
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Your intelligent diabetes management companion
              </Typography>
            </Box>
          </Box>
          
          {userStats && (
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip 
                icon={<LocalFireDepartmentIcon />} 
                label={`${userStats.today_totals?.calories || 0} cal`}
                sx={{ bgcolor: alpha('#fff', 0.2), color: 'white' }}
              />
              <Chip 
                icon={<FavoriteIcon />} 
                label={`${Math.round(userStats.diabetes_adherence || 0)}% score`}
                sx={{ bgcolor: alpha('#fff', 0.2), color: 'white' }}
              />
            </Box>
          )}
        </Box>
      </Paper>

      {/* Chat Controls */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Chat Session</InputLabel>
            <Select
              value={currentSession}
              onChange={handleSessionChange}
              label="Chat Session"
            >
              {sessions.map((session) => {
                const messageCount = session.session_id === currentSession ? messages.length : (session.messages?.length || 0);
                return (
                  <MenuItem key={session.session_id} value={session.session_id}>
                    {new Date(session.timestamp).toLocaleDateString()} - {messageCount} messages
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>
          
          <ButtonGroup variant="outlined" size="small">
            <Button startIcon={<AddCommentIcon />} onClick={handleNewChat}>
              New Chat
            </Button>
            <Button startIcon={<CloseIcon />} onClick={handleClearHistory}>
              Clear
            </Button>
          </ButtonGroup>

          <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          </Box>
        </Box>
      </Paper>

      {/* Quick Actions */}
      {showQuickActions && messages.length === 0 && (
        <Fade in={showQuickActions}>
          <Paper elevation={1} sx={{ p: 3, mb: 2, bgcolor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LightbulbIcon color="primary" />
              Quick Actions
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Get started with these common requests:
            </Typography>
            <Grid container spacing={1}>
              {quickActions.map((action, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={action.icon}
                    onClick={() => handleQuickAction(action)}
                    color={action.color}
                    sx={{ 
                      py: 1.5, 
                      justifyContent: 'flex-start',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 2
                      },
                      transition: 'all 0.2s ease-in-out'
                    }}
                  >
                    {action.label}
                  </Button>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Fade>
      )}

      {/* Messages */}
      <Paper 
        elevation={1} 
        sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column', 
          overflow: 'hidden',
          mb: 2
        }}
      >
        <Box
          ref={chatContainerRef}
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {messages.length === 0 && !showQuickActions && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <SmartToyIcon sx={{ fontSize: 60, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Start a conversation with your AI health coach
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Ask about nutrition, meal planning, or diabetes management
              </Typography>
            </Box>
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
                    maxWidth: '70%',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 1,
                    flexDirection: message.is_user ? 'row-reverse' : 'row',
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: message.is_user ? 'primary.main' : 'secondary.main',
                      width: 32,
                      height: 32,
                    }}
                  >
                    {message.is_user ? <PersonIcon /> : <SmartToyIcon />}
                  </Avatar>
                  
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      bgcolor: message.is_user ? 'primary.main' : 'grey.100',
                      color: message.is_user ? 'white' : 'text.primary',
                      borderRadius: 2,
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

      {/* Input Area */}
      <Paper elevation={2} sx={{ p: 2 }}>
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

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your AI health coach anything about diabetes, nutrition, meal planning, or upload images for analysis..."
            variant="outlined"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
              },
            }}
          />
          <Tooltip title="Enhanced Image Analysis">
            <IconButton onClick={handleRecordFoodButtonClick} color="primary"
              sx={{
                bgcolor: 'secondary.main',
                color: 'white',
                '&:hover': { bgcolor: 'secondary.dark' },
                width: 48,
                height: 48,
              }}
            >
              <Badge badgeContent="NEW" color="error">
                <PhotoCameraIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          <Tooltip title="Send Message">
            <span>
              <IconButton
                color="primary"
                onClick={handleSendMessage}
                disabled={(!input.trim() && !selectedImage) || isLoading}
                sx={{
                  bgcolor: 'primary.main',
                  color: 'white',
                  '&:hover': { bgcolor: 'primary.dark' },
                  '&:disabled': { bgcolor: 'grey.300' },
                  width: 48,
                  height: 48,
                }}
              >
                <SendIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Paper>

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
    </Container>
  );
};

export default Chat; 