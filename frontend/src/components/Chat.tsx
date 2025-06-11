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
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AddCommentIcon from '@mui/icons-material/AddComment';
import ImageIcon from '@mui/icons-material/Image';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import CloseIcon from '@mui/icons-material/Close';
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
}

interface Session {
  session_id: string;
  timestamp: string;
  messages: Message[];
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
  const userScrolledRef = useRef<boolean>(false); // Flag to indicate user has scrolled manually
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null); // Timeout for resetting userScrolledRef
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recordFoodInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [isMobile, setIsMobile] = useState(false);
  const [recordFoodDialog, setRecordFoodDialog] = useState(false);
  const [recordFoodResult, setRecordFoodResult] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);

  const handleNewChat = () => {
    const newSessionId = uuidv4();
    console.log("Creating new chat session:", newSessionId);
    
    // Create the new session object
    const newSession = {
      session_id: newSessionId,
      timestamp: new Date().toISOString(),
      messages: []
    };
    
    // Add the new session to the sessions list first
    setSessions(prev => [...prev, newSession]);
    
    // Then set it as the current session
    setCurrentSession(newSessionId);
    setMessages([]);
  };

  useEffect(() => {
    // On initial load, fetch sessions and then decide if we need to start a new one.
    const loadSessionsAndInitialize = async () => {
      await fetchSessions(); // This will populate the sessions dropdown
      // After fetching, if no currentSession is set (e.g. by user selection or previous state),
      // start a new chat. This prevents loading an old chat automatically.
      if (!currentSession) { // Check currentSession *after* fetchSessions tried to set it from existing
        handleNewChat();
      }
    };
    loadSessionsAndInitialize();
  }, []); // Runs once on mount

  useEffect(() => {
    if (currentSession) {
      fetchChatHistory();
    }
  }, [currentSession]);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    if (chatContainerRef.current && !userScrolledRef.current) { // Only scroll if user hasn't manually scrolled
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      if (scrollHeight - scrollTop - clientHeight < 150) { // Increased threshold slightly
        messagesEndRef.current?.scrollIntoView({ behavior });
      }
    }
  };

  // Effect for handling auto-scroll based on message changes
  useEffect(() => {
    if (userScrolledRef.current) {
      // If user has scrolled, don't interfere
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

  // Effect for scrolling when loading completes
  useEffect(() => {
    if (!isLoading && messages.length > 0 && !userScrolledRef.current) {
      scrollToBottom('smooth');
    }
  }, [isLoading, messages.length]);

  // Handle manual scroll by user
  const handleManualScroll = () => {
    userScrolledRef.current = true;
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    scrollTimeoutRef.current = setTimeout(() => {
      userScrolledRef.current = false;
    }, 1000); // Reset flag after 1 second of no scrolling from user
  };

  // Add and remove scroll listener
  useEffect(() => {
    const container = chatContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleManualScroll);
      return () => {
        container.removeEventListener('scroll', handleManualScroll);
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
        }
      };
    }
  }, []); // Empty dependency array, runs once on mount and cleanup on unmount

  useEffect(() => {
    // Check if device is mobile
    setIsMobile(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent));
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await fetch('http://localhost:8000/chat/sessions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data: Session[] = await response.json();
        setSessions(data);
        // We no longer automatically set currentSession to data[0].session_id here.
        // The logic in the initial useEffect will call handleNewChat if currentSession is still empty.
        // If a currentSession *is* already set (e.g. user selected from dropdown), we keep it.
        if (data.length > 0 && currentSession && !data.find(s => s.session_id === currentSession)) {
          // If current session is no longer in the fetched list (e.g. deleted), start a new one.
          console.log("Current session no longer exists, starting a new chat.");
          handleNewChat();
        } else if (data.length === 0 && !currentSession) {
           // This case is now primarily handled by the initial useEffect, but good as a fallback.
           handleNewChat();
        }

      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      // If fetching sessions fails, and no current session, ensure a new chat can be started
      if (!currentSession) {
        handleNewChat();
      }
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await fetch(`http://localhost:8000/chat/history?session_id=${currentSession}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(data.map((msg: any) => ({
          id: msg.id,
          message: msg.message_content,
          is_user: msg.is_user,
          timestamp: msg.timestamp,
          session_id: msg.session_id,
          imageUrl: msg.imageUrl
        })));
      }
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    }
  };

  const handleSendCombinedMessage = async () => {
    if (!input.trim() && !selectedImage) return;

    setIsLoading(true);

    const formData = new FormData();
    formData.append('message', input);
    if (selectedImage) {
      formData.append('image', selectedImage);
    }
    formData.append('session_id', currentSession);

    try {
      const response = await fetch('http://localhost:8000/chat/message-with-image', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      // Optionally handle streaming or just refresh chat history
      await fetchChatHistory();
      setInput('');
      setSelectedImage(null);
    } catch (error) {
      console.error('Error sending combined message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionChange = (event: SelectChangeEvent<string>) => {
    setCurrentSession(event.target.value);
  };

  const handleClearHistory = async () => {
    try {
      const response = await fetch(`http://localhost:8000/chat/history?session_id=${currentSession}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        setMessages([]);
        await fetchSessions();
      }
    } catch (error) {
      console.error('Failed to clear chat history:', error);
    }
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Create a temporary URL for the image
    const imageUrl = URL.createObjectURL(file);
    
    // Add user message with image
    const userMessage = {
      id: uuidv4(),
      message: 'Analyzing this image...',
      is_user: true,
      timestamp: new Date().toISOString(),
      session_id: currentSession,
      imageUrl
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('prompt', 'Analyze the calorie content and nutritional information of this food image.');

      const response = await fetch('http://localhost:8000/chat/analyze-image', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData
      });

      if (response.ok) {
        const reader = response.body?.getReader();
        if (reader) {
          const decoder = new TextDecoder();
          let assistantMessage = '';

          // Add initial empty assistant message
          setMessages(prev => [...prev, {
            id: uuidv4(),
            message: '',
            is_user: false,
            timestamp: new Date().toISOString(),
            session_id: currentSession
          }]);

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            assistantMessage += chunk;
            
            // Update the last message (assistant's message) with the new content
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage && !lastMessage.is_user) {
                lastMessage.message = assistantMessage;
              }
              return newMessages;
            });
          }
        }
      } else {
        console.error('Failed to analyze image');
      }
    } catch (error) {
      console.error('Error analyzing image:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecordFood = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsLoading(true);
      const formData = new FormData();
      formData.append('image', file);
      if (currentSession) {
        formData.append('session_id', currentSession);
      }

      const response = await fetch('http://localhost:8000/consumption/analyze-and-record', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setRecordFoodResult(result);
        setRecordFoodDialog(true);
        
        // Dispatch event to notify ConsumptionHistory component
        window.dispatchEvent(new Event('consumptionRecorded'));
        
        // Also, refresh chat history for the current session if a session_id was sent
        // This will show the newly recorded food item in the chat
        if (currentSession) {
          await fetchChatHistory(); // Re-fetch chat history for the current session
        }

      } else {
        console.error('Failed to analyze and record food', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error response from analyze-and-record:', errorText);
      }
    } catch (error) {
      console.error('Error analyzing and recording food:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleRecordFoodButtonClick = () => {
    if (recordFoodInputRef.current) {
      recordFoodInputRef.current.click();
    }
  };

  const handleCloseRecordDialog = () => {
    setRecordFoodDialog(false);
    setRecordFoodResult(null);
  };

  useEffect(() => {
    setLoaded(true);
  }, []);

  // Show preview when image is selected
  useEffect(() => {
    if (selectedImage) {
      const url = URL.createObjectURL(selectedImage);
      setImagePreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setImagePreviewUrl(null);
    }
  }, [selectedImage]);

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, height: '80vh', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" component="h1">
            Chat with Your Diet Assistant
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel id="session-select-label">Chat Session</InputLabel>
              <Select
                labelId="session-select-label"
                id="session-select"
                value={currentSession}
                label="Chat Session"
                onChange={handleSessionChange}
              >
                {sessions.map((session) => (
                  <MenuItem key={session.session_id} value={session.session_id}>
                    {new Date(session.timestamp).toLocaleString()} (ID: {session.session_id.substring(0, 8)})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              onClick={handleNewChat}
              startIcon={<AddCommentIcon />}
            >
              New Chat
            </Button>
            <Button
              variant="outlined"
              color="error"
              onClick={handleClearHistory}
              disabled={!currentSession || messages.length === 0}
            >
              Clear History
            </Button>
          </Box>
        </Box>

        <Box 
          ref={chatContainerRef}
          sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}
        >
          <List>
            {messages.map((msg, index) => (
              <React.Fragment key={index}>
                <ListItem
                  sx={{
                    justifyContent: msg.is_user ? 'flex-end' : 'flex-start',
                  }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      maxWidth: '70%',
                      backgroundColor: msg.is_user ? 'primary.light' : 'grey.100',
                      color: msg.is_user ? 'white' : 'text.primary',
                    }}
                  >
                    <Typography variant="subtitle2" color="textSecondary">
                      {msg.is_user ? 'You' : 'Assistant'}:
                    </Typography>
                    {msg.imageUrl && (
                      <Box sx={{ mb: 2 }}>
                        <img 
                          src={msg.imageUrl} 
                          alt="Uploaded food" 
                          style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '8px' }} 
                        />
                      </Box>
                    )}
                    <ReactMarkdown>{msg.message}</ReactMarkdown>
                  </Paper>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
            <div ref={messagesEndRef} />
          </List>
        </Box>

        <Box component="form" onSubmit={(e) => { e.preventDefault(); handleSendCombinedMessage(); }} sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {/* Image preview thumbnail */}
          {imagePreviewUrl && (
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, maxWidth: 200 }}>
              <img
                src={imagePreviewUrl}
                alt="Preview"
                style={{ maxWidth: 100, maxHeight: 100, borderRadius: 8, marginRight: 8, border: '1px solid #ccc' }}
              />
              <IconButton size="small" onClick={() => setSelectedImage(null)} aria-label="Remove image preview">
                <CloseIcon />
              </IconButton>
            </Box>
          )}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <input
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              id="chat-image-upload"
              onChange={e => setSelectedImage(e.target.files?.[0] || null)}
            />
            <label htmlFor="chat-image-upload">
              <Tooltip title="Attach image">
                <IconButton component="span" color={selectedImage ? "success" : "primary"}>
                  <ImageIcon />
                </IconButton>
              </Tooltip>
            </label>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendCombinedMessage()}
              disabled={isLoading}
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={isLoading || (!input.trim() && !selectedImage)}
              endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            >
              Send
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Record Food Result Dialog */}
      <Dialog open={recordFoodDialog} onClose={handleCloseRecordDialog} maxWidth="md" fullWidth>
        <DialogTitle>Food Analysis Result</DialogTitle>
        <DialogContent>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : recordFoodResult?.error ? (
            <Alert severity="error">{recordFoodResult.error}</Alert>
          ) : recordFoodResult?.analysis ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                {recordFoodResult.analysis.food_name}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Estimated Portion: {recordFoodResult.analysis.estimated_portion}
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Nutritional Information:
                </Typography>
                <Box sx={{ pl: 2 }}>
                  <Typography>• Calories: {recordFoodResult.analysis.nutritional_info?.calories || 'N/A'}</Typography>
                  <Typography>• Carbohydrates: {recordFoodResult.analysis.nutritional_info?.carbohydrates || 'N/A'}g</Typography>
                  <Typography>• Protein: {recordFoodResult.analysis.nutritional_info?.protein || 'N/A'}g</Typography>
                  <Typography>• Fat: {recordFoodResult.analysis.nutritional_info?.fat || 'N/A'}g</Typography>
                  <Typography>• Fiber: {recordFoodResult.analysis.nutritional_info?.fiber || 'N/A'}g</Typography>
                  <Typography>• Sugar: {recordFoodResult.analysis.nutritional_info?.sugar || 'N/A'}g</Typography>
                </Box>
              </Box>

              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Diabetes Suitability Rating:
                </Typography>
                <Box sx={{ pl: 2 }}>
                  <Typography>• Overall Suitability: <strong>{recordFoodResult.analysis.medical_rating?.diabetes_suitability || 'N/A'}</strong></Typography>
                  <Typography>• Glycemic Impact: {recordFoodResult.analysis.medical_rating?.glycemic_impact || 'N/A'}</Typography>
                  <Typography>• Recommended Frequency: {recordFoodResult.analysis.medical_rating?.recommended_frequency || 'N/A'}</Typography>
                </Box>
              </Box>

              {recordFoodResult.analysis.analysis_notes && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Analysis Notes:
                  </Typography>
                  <Typography variant="body2" sx={{ backgroundColor: 'grey.100', p: 2, borderRadius: 1 }}>
                    {recordFoodResult.analysis.analysis_notes}
                  </Typography>
                </Box>
              )}

              <Alert severity="success" sx={{ mt: 2 }}>
                Food consumption has been recorded to your history!
              </Alert>
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseRecordDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Chat; 