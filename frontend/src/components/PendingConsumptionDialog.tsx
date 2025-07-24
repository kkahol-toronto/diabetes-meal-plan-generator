import React, { useState, useRef, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  Box,
  TextField,
  IconButton,
  Avatar,
  Divider,
  Alert,
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  CheckCircle as AcceptIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Close as CloseIcon,
  Restaurant as FoodIcon,
  LocalFireDepartment as CaloriesIcon,
  FitnessCenter as ProteinIcon,
  Grain as CarbsIcon,
  Opacity as FatIcon
} from '@mui/icons-material';
import config from '../config/environment';
import { useApp } from '../contexts/AppContext';
import { useNavigate } from 'react-router-dom';

interface NutritionalInfo {
  calories: number;
  carbohydrates: number;
  protein: number;
  fat: number;
  fiber?: number;
  sugar?: number;
  sodium?: number;
}

interface MedicalRating {
  diabetes_suitability: string;
  glycemic_impact: string;
  recommended_frequency: string;
  portion_recommendation: string;
}

interface AnalysisData {
  food_name: string;
  estimated_portion: string;
  nutritional_info: NutritionalInfo;
  medical_rating: MedicalRating;
  analysis_notes: string;
}

interface PendingRecord {
  id: string;
  user_email: string;
  user_id: string;
  created_at: string;
  expires_at: string;
  food_name: string;
  estimated_portion: string;
  nutritional_info: NutritionalInfo;
  medical_rating: MedicalRating;
  analysis_notes: string;
  image_url?: string;
  meal_type?: string;
}

interface EditMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface PendingConsumptionDialogProps {
  open: boolean;
  onClose: () => void;
  pendingId: string | null;
  analysisData: AnalysisData | null;
  imageUrl?: string;
  onAccept: () => void;
  onDelete: () => void;
}

const PendingConsumptionDialog: React.FC<PendingConsumptionDialogProps> = ({
  open,
  onClose,
  pendingId,
  analysisData,
  imageUrl,
  onAccept,
  onDelete
}) => {
  const { showNotification, triggerFoodLogged } = useApp();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'review' | 'edit'>('review');
  const [loading, setLoading] = useState(false);
  const [editMessages, setEditMessages] = useState<EditMessage[]>([]);
  const [editInput, setEditInput] = useState('');
  const [updatedData, setUpdatedData] = useState<AnalysisData | null>(analysisData);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (open && analysisData) {
      setMode('review');
      setUpdatedData(analysisData);
      setEditMessages([]);
      setEditInput('');
    }
  }, [open, analysisData]);

  // Auto-scroll to bottom of edit messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [editMessages]);

  const handleAccept = async () => {
    if (!pendingId) return;

    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch(`${config.API_URL}/consumption/pending/${pendingId}/accept`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      if (response.ok) {
        const result = await response.json();
        showNotification(`Successfully logged: ${result.food_name}`, 'success');
        triggerFoodLogged(); // Refresh homepage data
        onAccept();
        onClose();
      } else {
        throw new Error('Failed to accept food log');
      }
    } catch (error) {
      console.error('Error accepting food log:', error);
      showNotification('Failed to accept food log', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!pendingId) return;

    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch(`${config.API_URL}/consumption/pending/${pendingId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      if (response.ok) {
        showNotification('Food log discarded', 'info');
        onDelete();
        onClose();
      } else {
        throw new Error('Failed to delete food log');
      }
    } catch (error) {
      console.error('Error deleting food log:', error);
      showNotification('Failed to delete food log', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStartEdit = () => {
    setMode('edit');
    // Add initial message explaining edit functionality
    const initialMessage: EditMessage = {
      id: '1',
      content: `Hi! I'm here to help you edit your food log. I can see you have "${updatedData?.food_name}" (${updatedData?.estimated_portion}) with ${Math.round(updatedData?.nutritional_info.calories || 0)} calories. 

Just tell me what you'd like to change in natural language! For example:
• "Change this to grilled chicken breast"
• "Make it 2 cups instead" 
• "Set calories to 300"
• "French Fries, 1 Cup"

What would you like to update?`,
      isUser: false,
      timestamp: new Date()
    };
    setEditMessages([initialMessage]);
  };

  const handleSendEditMessage = async () => {
    if (!editInput.trim() || !pendingId || !updatedData) return;

    const userMessage: EditMessage = {
      id: Date.now().toString(),
      content: editInput,
      isUser: true,
      timestamp: new Date()
    };

    setEditMessages(prev => [...prev, userMessage]);
    const userInput = editInput;
    setEditInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/consumption/pending/${pendingId}/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          message: userInput 
        })
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to process message');
      }

      const data = await response.json();
      
      // Update local state if there were changes
      if (data.has_updates && data.updated_record) {
        const updatedRecord = data.updated_record;
        setUpdatedData({
          food_name: updatedRecord.food_name,
          estimated_portion: updatedRecord.estimated_portion,
          nutritional_info: updatedRecord.nutritional_info,
          medical_rating: updatedRecord.medical_rating,
          analysis_notes: updatedRecord.analysis_notes
        });
      }

      const assistantMessage: EditMessage = {
        id: (Date.now() + 1).toString(),
        content: data.response || "I've processed your request.",
        isUser: false,
        timestamp: new Date()
      };

      setEditMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Error processing edit:', error);
      const errorMessage: EditMessage = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setEditMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToReview = () => {
    setMode('review');
  };

  if (!analysisData || !updatedData) return null;

  const currentData = mode === 'edit' ? updatedData : analysisData;

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{ sx: { minHeight: '60vh' } }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box display="flex" alignItems="center">
          <FoodIcon sx={{ mr: 1 }} />
          {mode === 'review' ? 'Review Food Log' : 'Edit Food Details'}
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        {mode === 'review' ? (
          // Review Mode
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              Please review the food analysis below. You can Accept to save it, Edit to make changes, or Delete to discard it.
            </Alert>

            {imageUrl && (
              <Box sx={{ mb: 2, textAlign: 'center' }}>
                <img 
                  src={`data:image/jpeg;base64,${imageUrl}`} 
                  alt="Food" 
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '200px', 
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                  }} 
                />
              </Box>
            )}

            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <FoodIcon sx={{ mr: 1 }} />
                  {currentData.food_name}
                </Typography>
                <Typography variant="body1" color="textSecondary" gutterBottom>
                  Portion: {currentData.estimated_portion}
                </Typography>

                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                      <CaloriesIcon sx={{ fontSize: 24, mb: 1 }} />
                      <Typography variant="h6">{Math.round(currentData.nutritional_info.calories)}</Typography>
                      <Typography variant="caption">Calories</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                      <ProteinIcon sx={{ fontSize: 24, mb: 1 }} />
                      <Typography variant="h6">{Math.round(currentData.nutritional_info.protein)}g</Typography>
                      <Typography variant="caption">Protein</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                      <CarbsIcon sx={{ fontSize: 24, mb: 1 }} />
                      <Typography variant="h6">{Math.round(currentData.nutritional_info.carbohydrates)}g</Typography>
                      <Typography variant="caption">Carbs</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
                      <FatIcon sx={{ fontSize: 24, mb: 1 }} />
                      <Typography variant="h6">{Math.round(currentData.nutritional_info.fat)}g</Typography>
                      <Typography variant="caption">Fat</Typography>
                    </Paper>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Diabetes Suitability: 
                    <Chip 
                      label={currentData.medical_rating.diabetes_suitability}
                      color={
                        currentData.medical_rating.diabetes_suitability === 'high' ? 'success' :
                        currentData.medical_rating.diabetes_suitability === 'medium' ? 'warning' : 'error'
                      }
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {currentData.analysis_notes}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Box>
        ) : (
          // Edit Mode
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              💬 Chat with your AI nutrition assistant to edit any food details. I understand natural language!
            </Alert>

            {/* Current food summary */}
            <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
              <Typography variant="subtitle2" gutterBottom>Current Food:</Typography>
              <Typography variant="body1">
                <strong>{currentData.food_name}</strong> - {currentData.estimated_portion} ({Math.round(currentData.nutritional_info.calories)} calories)
              </Typography>
            </Paper>

            {/* Chat messages */}
            <Box sx={{ height: '300px', overflowY: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 1, mb: 2 }}>
              {editMessages.map((message) => (
                <Box key={message.id} sx={{ mb: 1, display: 'flex', justifyContent: message.isUser ? 'flex-end' : 'flex-start' }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', maxWidth: '85%' }}>
                    {!message.isUser && (
                      <Avatar sx={{ width: 28, height: 28, mr: 1, bgcolor: 'primary.main', fontSize: '12px' }}>
                        🤖
                      </Avatar>
                    )}
                    <Paper
                      sx={{
                        p: 1.5,
                        borderRadius: message.isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                        bgcolor: message.isUser ? 'primary.main' : 'grey.50',
                        color: message.isUser ? 'primary.contrastText' : 'text.primary',
                        border: message.isUser ? 'none' : '1px solid',
                        borderColor: message.isUser ? 'transparent' : 'grey.200'
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{message.content}</Typography>
                    </Paper>
                    {message.isUser && (
                      <Avatar sx={{ width: 28, height: 28, ml: 1, bgcolor: 'secondary.main', fontSize: '12px' }}>
                        👤
                      </Avatar>
                    )}
                  </Box>
                </Box>
              ))}
              <div ref={messagesEndRef} />
            </Box>

            {/* Edit input */}
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                placeholder="e.g., 'Change to salmon' or 'Make it 2 servings' or '400 calories'"
                value={editInput}
                onChange={(e) => setEditInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendEditMessage()}
                disabled={loading}
              />
              <IconButton 
                onClick={handleSendEditMessage} 
                disabled={!editInput.trim() || loading}
                color="primary"
              >
                {loading ? <CircularProgress size={24} /> : <SendIcon />}
              </IconButton>
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        {mode === 'review' ? (
          <>
            <Button onClick={handleDelete} color="error" startIcon={<DeleteIcon />} disabled={loading}>
              Delete
            </Button>
            <Button onClick={handleStartEdit} startIcon={<EditIcon />} disabled={loading}>
              Edit
            </Button>
            <Button 
              onClick={handleAccept} 
              variant="contained" 
              startIcon={<AcceptIcon />} 
              disabled={loading}
            >
              {loading ? <CircularProgress size={20} /> : 'Accept'}
            </Button>
          </>
        ) : (
          <>
            <Button onClick={handleBackToReview}>
              Back to Review
            </Button>
            <Button 
              onClick={handleAccept} 
              variant="contained" 
              startIcon={<AcceptIcon />} 
              disabled={loading}
            >
              {loading ? <CircularProgress size={20} /> : 'Accept Changes'}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default PendingConsumptionDialog; 