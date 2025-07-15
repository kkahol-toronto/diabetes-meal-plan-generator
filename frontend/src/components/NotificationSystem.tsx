import React, { useState, useEffect } from 'react';
import config from '../config/environment';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Box,
  Typography,
  IconButton,
  Chip,
  Slide,
  Fade,
  useTheme,
} from '@mui/material';
import {
  Close as CloseIcon,
  Psychology as BrainIcon,
  Restaurant as MealIcon,
  TrendingUp as ProgressIcon,
  EmojiEvents as RewardIcon,
  Warning as WarningIcon,
  Schedule as TimeIcon,
  Lightbulb as TipIcon,
} from '@mui/icons-material';

interface Notification {
  id: string;
  type: 'meal_reminder' | 'progress_alert' | 'coaching_tip' | 'reward' | 'warning';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high';
  timestamp: Date;
  autoHide?: boolean;
  duration?: number;
}

interface NotificationSystemProps {
  userId?: string;
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({ userId }) => {
  const theme = useTheme();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [currentNotification, setCurrentNotification] = useState<Notification | null>(null);

  useEffect(() => {
    if (userId) {
      // Only check once on mount / login
      checkForNotifications();
      // No interval – notifications will show only on initial login/refresh
      return () => {};
    }
  }, [userId]);

  useEffect(() => {
    if (notifications.length > 0 && !currentNotification) {
      showNextNotification();
    }
  }, [notifications, currentNotification]);

  const checkForNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Check for meal reminders based on time
      const now = new Date();
      const hour = now.getHours();
      
      // Breakfast reminder (7-9 AM)
      if (hour >= 7 && hour <= 9) {
        addNotification({
          type: 'meal_reminder',
          title: '🌅 Breakfast Time!',
          message: 'Start your day with a diabetes-friendly breakfast. Your AI coach has suggestions ready!',
          priority: 'medium',
          autoHide: true,
          duration: 8000,
        });
      }
      
      // Lunch reminder (12-2 PM)
      if (hour >= 12 && hour <= 14) {
        addNotification({
          type: 'meal_reminder',
          title: '☀️ Lunch Break!',
          message: 'Time for a balanced lunch. Check your meal plan for today\'s recommendations.',
          priority: 'medium',
          autoHide: true,
          duration: 8000,
        });
      }
      
      // Dinner reminder (6-8 PM)
      if (hour >= 18 && hour <= 20) {
        addNotification({
          type: 'meal_reminder',
          title: '🌙 Dinner Time!',
          message: 'End your day with a nutritious dinner. Your AI coach can suggest diabetes-friendly options.',
          priority: 'medium',
          autoHide: true,
          duration: 8000,
        });
      }

      // Fetch AI-generated notifications
      const response = await fetch(`${config.API_URL}/coach/notifications`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        data.notifications?.forEach((notif: any) => {
          addNotification({
            type: notif.type,
            title: notif.title,
            message: notif.message,
            priority: notif.priority,
            autoHide: notif.auto_hide,
            duration: notif.duration,
          });
        });
      }
    } catch (error) {
      console.error('Error checking notifications:', error);
    }
  };

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };

    setNotifications(prev => {
      // Avoid duplicate notifications
      const exists = prev.some(n => 
        n.type === newNotification.type && 
        n.title === newNotification.title &&
        Date.now() - n.timestamp.getTime() < 300000 // 5 minutes
      );
      
      if (exists) return prev;
      
      return [...prev, newNotification].slice(-10); // Keep only last 10 notifications
    });
  };

  const showNextNotification = () => {
    if (notifications.length > 0) {
      const next = notifications[0];
      setCurrentNotification(next);
      setNotifications(prev => prev.slice(1));
    }
  };

  const handleClose = () => {
    setCurrentNotification(null);
    // Show next notification after a short delay
    setTimeout(showNextNotification, 1000);
  };

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'meal_reminder': return <MealIcon />;
      case 'progress_alert': return <ProgressIcon />;
      case 'coaching_tip': return <TipIcon />;
      case 'reward': return <RewardIcon />;
      case 'warning': return <WarningIcon />;
      default: return <BrainIcon />;
    }
  };

  const getNotificationSeverity = (type: Notification['type'], priority: Notification['priority']) => {
    if (type === 'warning') return 'warning';
    if (type === 'reward') return 'success';
    if (priority === 'high') return 'error';
    if (priority === 'medium') return 'warning';
    return 'info';
  };

  const getPriorityColor = (priority: Notification['priority']) => {
    switch (priority) {
      case 'high': return theme.palette.error.main;
      case 'medium': return theme.palette.warning.main;
      case 'low': return theme.palette.success.main;
      default: return theme.palette.info.main;
    }
  };

  if (!currentNotification) return null;

  return (
    <Slide direction="down" in={!!currentNotification} mountOnEnter unmountOnExit>
      <Snackbar
        open={!!currentNotification}
        autoHideDuration={currentNotification.autoHide ? (currentNotification.duration || 6000) : null}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        sx={{ mt: 8 }}
      >
        <Alert
          severity={getNotificationSeverity(currentNotification.type, currentNotification.priority)}
          onClose={handleClose}
          sx={{
            minWidth: 350,
            maxWidth: 500,
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
            '& .MuiAlert-icon': {
              fontSize: 28,
            },
          }}
          icon={getNotificationIcon(currentNotification.type)}
          action={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={currentNotification.priority.toUpperCase()}
                size="small"
                sx={{
                  backgroundColor: `${getPriorityColor(currentNotification.priority)}20`,
                  color: getPriorityColor(currentNotification.priority),
                  fontWeight: 600,
                  fontSize: '0.7rem',
                }}
              />
              <IconButton
                size="small"
                onClick={handleClose}
                sx={{ color: 'inherit' }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          }
        >
          <AlertTitle sx={{ fontWeight: 700, mb: 1 }}>
            {currentNotification.title}
          </AlertTitle>
          <Typography variant="body2" sx={{ lineHeight: 1.5 }}>
            {currentNotification.message}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
            <TimeIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {currentNotification.timestamp.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
              })}
            </Typography>
          </Box>
        </Alert>
      </Snackbar>
    </Slide>
  );
};

export default NotificationSystem; 