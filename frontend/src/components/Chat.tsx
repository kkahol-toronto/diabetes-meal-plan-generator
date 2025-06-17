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
  ListItemIcon,
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
import DiningIcon from '@mui/icons-material/LocalDining';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { v4 as uuidv4 } from 'uuid';

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
    type?: 'food_analysis' | 'meal_suggestion' | 'general' | 'quick_action';
    data?: any;
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

// Update interface for API response
interface ApiResponse extends Response {
  response?: string;
  message?: string;
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
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [isMobile, setIsMobile] = useState(false);
  const [recordFoodDialog, setRecordFoodDialog] = useState(false);
  const [recordFoodResult, setRecordFoodResult] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [showImageSourceDialog, setShowImageSourceDialog] = useState(false);

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
      await fetchSessions();
      await fetchUserStats();
      if (!currentSession) {
        handleNewChat();
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

      const response = await fetch('/coach/daily-insights', {
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
      messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
    } else {
      scrollToBottom('smooth');
    }

    prevMessagesLengthRef.current = messages.length;
  }, [messages]);

  const handleManualScroll = () => {
    clearTimeout(scrollTimeoutRef.current!); 
    userScrolledRef.current = true;
    scrollTimeoutRef.current = setTimeout(() => {
      userScrolledRef.current = false;
    }, 1000); // Reset after 1 second of inactivity
  };

  useEffect(() => {
    const chatContainer = chatContainerRef.current;
    if (chatContainer) {
      chatContainer.addEventListener('scroll', handleManualScroll);
      return () => {
        chatContainer.removeEventListener('scroll', handleManualScroll);
      };
    }
  }, []);

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      const response = await fetch('/chat/sessions', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
        if (data.length > 0) {
          setCurrentSession(data[0].session_id);
        }
      } else {
        console.error('Failed to fetch sessions:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const fetchChatHistory = async () => {
    if (!currentSession) return;
    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/chat/history/${currentSession}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages);
      } else {
        console.error('Failed to fetch chat history:', response.statusText);
        setMessages([]);
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if ((!input.trim() && !selectedImage) || isLoading) return;

    // Try to detect meal type from the message
    let mealType = null;
    const mealTypeMatch = input.toLowerCase().match(/\b(breakfast|lunch|dinner|snack)s?\b/);
    if (mealTypeMatch) {
      mealType = mealTypeMatch[1];
    }

    const userMessage: Message = {
      id: uuidv4(),
      message: input,
      is_user: true,
      timestamp: new Date().toISOString(),
      session_id: currentSession,
      imageUrl: imagePreviewUrl || undefined,
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput(''); // Clear input after sending
    setSelectedImage(null);
    setImagePreviewUrl(null);
    setShowQuickActions(false);

    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const headers: HeadersInit = {
        'Authorization': `Bearer ${token}`,
      };

      let response: ApiResponse;
      if (selectedImage) {
        // Handle image + message
        const formData = new FormData();
        formData.append('message', input);
        formData.append('session_id', currentSession);
        formData.append('image', selectedImage);
        if (mealType) {
          formData.append('meal_type', mealType);
        }

        response = await fetch('/consumption/analyze-and-record', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });
      } else {
        // Handle text only message
        response = await fetch('/chat/message', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ message: input, session_id: currentSession }),
        });
      }

      if (response.ok) {
        const data = await response.json();
        // Append AI response to messages
        setMessages((prevMessages) => [...prevMessages, {
          id: uuidv4(),
          message: data.response || data.message || data.analysis?.analysis_notes || 'Analysis complete',
          is_user: false,
          timestamp: new Date().toISOString(),
          session_id: currentSession,
          metadata: {
            type: selectedImage ? 'food_analysis' : 'general',
            data: data.analysis || data.metadata
          }
        }]);
      } else {
        setMessages((prevMessages) => [...prevMessages, {
          id: uuidv4(),
          message: `Error: ${response.statusText || 'Failed to send message'}`,
          is_user: false,
          timestamp: new Date().toISOString(),
          session_id: currentSession,
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prevMessages) => [...prevMessages, {
        id: uuidv4(),
        message: 'Error: Failed to send message',
        is_user: false,
        timestamp: new Date().toISOString(),
        session_id: currentSession,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionChange = (event: SelectChangeEvent<string>) => {
    setCurrentSession(event.target.value);
    setShowQuickActions(false);
  };

  const handleClearHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      if (!currentSession) return; // Cannot clear history if no session is selected

      const response = await fetch(`/chat/history/${currentSession}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setMessages([]);
        setShowQuickActions(true);
        // Optionally, remove the session from the list or mark as empty
        setSessions(prev => prev.filter(s => s.session_id !== currentSession));
        // After clearing, create a new session or navigate away if no sessions remain
        if (sessions.length > 1) {
          setCurrentSession(sessions[0].session_id === currentSession ? sessions[1].session_id : sessions[0].session_id);
        } else {
          handleNewChat(); // Create a new chat if no other sessions exist
        }
      } else {
        console.error('Failed to clear history:', response.statusText);
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

    setSelectedImage(file);
    
    // Create preview URL
    const previewUrl = URL.createObjectURL(file);
    setImagePreviewUrl(previewUrl);
  };

  const handleRecordFoodButtonClick = () => {
    setShowImageSourceDialog(true);
  };

  const handleCloseRecordDialog = () => {
    setRecordFoodDialog(false);
    setRecordFoodResult(null);
  };

  const handleCloseImageSourceDialog = () => {
    setShowImageSourceDialog(false);
  };

  const handleGalleryClick = () => {
    fileInputRef.current?.click();
    setShowImageSourceDialog(false);
  };

  const handleCameraClick = () => {
    cameraInputRef.current?.click();
    setShowImageSourceDialog(false);
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
              {sessions.map((session) => (
                <MenuItem key={session.session_id} value={session.session_id}>
                  {new Date(session.timestamp).toLocaleDateString()} - {session.messages?.length || 0} messages
                </MenuItem>
              ))}
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
            <Tooltip title="Log Food (attach image)">
              <IconButton onClick={handleRecordFoodButtonClick} color="primary">
                <Badge badgeContent="AI" color="secondary">
                  <CameraAltIcon />
                </Badge>
              </IconButton>
            </Tooltip>
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
                      bgcolor: message.is_user ? theme.palette.primary.main : theme.palette.secondary.main,
                      color: 'white',
                    }}
                  >
                    {message.is_user ? <PersonIcon /> : <SmartToyIcon />}
                  </Avatar>
                  <Card
                    sx={{
                      bgcolor: message.is_user ? theme.palette.primary.light : theme.palette.grey[100],
                      color: message.is_user ? theme.palette.primary.contrastText : 'inherit',
                      borderRadius: message.is_user ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
                      wordBreak: 'break-word',
                      position: 'relative', // For timestamp positioning
                    }}
                  >
                    <CardContent>
                      {message.imageUrl && (
                        <Box sx={{ mb: 1 }}>
                          <img
                            src={message.imageUrl}
                            alt="Attached"
                            style={{ maxWidth: '100%', borderRadius: '8px' }}
                          />
                        </Box>
                      )}
                      {formatMessage(message.message)}
                    </CardContent>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        position: 'absolute', 
                        bottom: 4, 
                        [message.is_user ? 'left' : 'right']: 12, // Adjust position based on user or AI
                        color: message.is_user ? 'rgba(255,255,255,0.7)' : 'text.secondary',
                        fontSize: '0.6rem',
                      }}
                    >
                      {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                  </Card>
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

        {/* Input Area */}
        <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', gap: 1 }}>
          {selectedImage && (
            <Box sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              p: 1,
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              flexShrink: 0
            }}>
              <CameraAltIcon color="primary" />
              <Typography variant="body2">Image attached</Typography>
              <IconButton size="small" onClick={() => { setSelectedImage(null); setImagePreviewUrl(null); }}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          )}
          {imagePreviewUrl && (
            <Box sx={{ flexShrink: 0 }}>
              <img src={imagePreviewUrl} alt="Image Preview" style={{ maxWidth: '50px', maxHeight: '50px', borderRadius: '4px' }} />
            </Box>
          )}
          <TextField
            fullWidth
            variant="outlined"
            placeholder={selectedImage ? "Add a message with your image..." : "Ask your AI health coach..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            sx={{
              bgcolor: 'background.paper',
              borderRadius: 1,
              '& .MuiOutlinedInput-root': {
                fieldset: {
                  borderColor: 'divider',
                },
                '&:hover fieldset': {
                  borderColor: 'primary.main',
                },
                '&.Mui-focused fieldset': {
                  borderColor: 'primary.main',
                },
              },
            }}
            multiline
            maxRows={4}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            endIcon={<SendIcon />}
            sx={{ height: '56px', flexShrink: 0 }}
            disabled={(!input.trim() && !selectedImage) || isLoading}
          >
            Send
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept="image/*"
            onChange={handleImageUpload}
          />
          <input
            type="file"
            ref={cameraInputRef}
            style={{ display: 'none' }}
            accept="image/*"
            capture="environment"
            onChange={handleImageUpload}
          />
        </Box>
      </Paper>

      {/* Image Source Dialog */}
      <Dialog open={showImageSourceDialog} onClose={handleCloseImageSourceDialog}>
        <DialogTitle>Select Image Source</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<RestaurantIcon />}
              onClick={handleGalleryClick}
              fullWidth
            >
              Choose from Gallery
            </Button>
            <Button
              variant="outlined"
              startIcon={<CameraAltIcon />}
              onClick={handleCameraClick}
              fullWidth
            >
              Take Photo with Camera
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseImageSourceDialog}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Record Food Dialog */}
      <Dialog open={recordFoodDialog} onClose={handleCloseRecordDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Log Meal with AI</DialogTitle>
        <DialogContent dividers>
          {recordFoodResult && (
            <Box>
              <Typography variant="h6" gutterBottom>AI Analysis Complete!</Typography>
              {recordFoodResult.success ? (
                <Box>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    Meal logged successfully! Here's the analysis:
                  </Alert>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Food Items:</Typography>
                  <List dense>
                    {recordFoodResult.data.food_items.map((item: any, index: number) => (
                      <ListItem key={index}>
                        <ListItemIcon><DiningIcon /></ListItemIcon>
                        <ListItemText 
                          primary={item.name} 
                          secondary={`Calories: ${item.nutritional_info.calories}, Protein: ${item.nutritional_info.protein}, Carbs: ${item.nutritional_info.carbohydrates}, Fat: ${item.nutritional_info.fat}`} 
                        />
                      </ListItem>
                    ))}
                  </List>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 2 }}>Total Nutrients:</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon><LocalFireDepartmentIcon /></ListItemIcon>
                      <ListItemText primary={`Total Calories: ${recordFoodResult.data.total_nutrients.calories}`} />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><FitnessCenterIcon /></ListItemIcon>
                      <ListItemText primary={`Total Protein: ${recordFoodResult.data.total_nutrients.protein}`} />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><GrainIcon /></ListItemIcon>
                      <ListItemText primary={`Total Carbohydrates: ${recordFoodResult.data.total_nutrients.carbohydrates}`} />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><FavoriteIcon /></ListItemIcon>
                      <ListItemText primary={`Total Fat: ${recordFoodResult.data.total_nutrients.fat}`} />
                    </ListItem>
                  </List>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 2 }}>Analysis:</Typography>
                  <Typography variant="body2">{recordFoodResult.data.image_analysis}</Typography>
                </Box>
              ) : (
                <Alert severity="error">
                  Failed to log meal: {recordFoodResult.error || 'Unknown error'}
                </Alert>
              )}
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