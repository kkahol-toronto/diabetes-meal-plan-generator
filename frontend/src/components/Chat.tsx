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
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  message: string;
  is_user: boolean;
  timestamp: string;
  session_id: string;
}

interface Session {
  session_id: string;
  timestamp: string;
  messages: Message[];
}

const Chat = () => {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<string>('');
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (currentSession) {
      fetchChatHistory();
    }
  }, [currentSession]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const response = await fetch('http://localhost:8000/chat/sessions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSessions(data);
        if (data.length > 0 && !currentSession) {
          setCurrentSession(data[0].session_id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
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
        setMessages(data.map((msg: Message) => ({ role: msg.is_user ? 'user' : 'assistant', content: msg.message })));
      }
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ message: input }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: data.assistant_message.message }
        ]);
      } else {
        console.error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
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
                    {new Date(session.timestamp).toLocaleString()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              color="secondary"
              onClick={handleClearHistory}
              disabled={!currentSession}
            >
              Clear History
            </Button>
          </Box>
        </Box>

        <Box sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
          <List>
            {messages.map((msg, index) => (
              <React.Fragment key={index}>
                <ListItem
                  sx={{
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      maxWidth: '70%',
                      backgroundColor: msg.role === 'user' ? 'primary.light' : 'grey.100',
                      color: msg.role === 'user' ? 'white' : 'text.primary',
                    }}
                  >
                    <Typography variant="subtitle2" color="textSecondary">
                      {msg.role === 'user' ? 'You' : 'Assistant'}:
                    </Typography>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </Paper>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
            <div ref={messagesEndRef} />
          </List>
        </Box>

        <Box component="form" onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            disabled={isLoading}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={isLoading || !input.trim()}
            endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          >
            Send
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default Chat; 