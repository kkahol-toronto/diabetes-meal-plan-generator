import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { Snackbar, Alert, Backdrop, CircularProgress } from '@mui/material';

interface User {
  id: string;
  username: string;
  email?: string;
  name?: string;
  is_admin: boolean;
}

interface Notification {
  id: string;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
  autoHideDuration?: number;
}

interface AppState {
  isLoading: boolean;
  loadingMessage?: string;
  user: User | null;
  notifications: Notification[];
  foodLoggedTrigger: number; // Timestamp to trigger data refresh
}

type AppAction =
  | { type: 'SET_LOADING'; payload: { isLoading: boolean; message?: string } }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'ADD_NOTIFICATION'; payload: Omit<Notification, 'id'> }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_NOTIFICATIONS' }
  | { type: 'TRIGGER_FOOD_LOGGED' };

const initialState: AppState = {
  isLoading: false,
  user: null,
  notifications: [],
  foodLoggedTrigger: 0,
};

const AppContext = createContext<{
  state: AppState;
  setLoading: (isLoading: boolean, message?: string) => void;
  setUser: (user: User | null) => void;
  showNotification: (message: string, severity?: Notification['severity'], autoHideDuration?: number) => void;
  clearNotifications: () => void;
  triggerFoodLogged: () => void;
} | null>(null);

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload.isLoading,
        loadingMessage: action.payload.message,
      };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
      };
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [
          ...state.notifications,
          { ...action.payload, id: Date.now().toString() },
        ],
      };
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
    case 'CLEAR_NOTIFICATIONS':
      return {
        ...state,
        notifications: [],
      };
    case 'TRIGGER_FOOD_LOGGED':
      return {
        ...state,
        foodLoggedTrigger: Date.now(),
      };
    default:
      return state;
  }
};

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const setLoading = (isLoading: boolean, message?: string) => {
    dispatch({ type: 'SET_LOADING', payload: { isLoading, message } });
  };

  const setUser = (user: User | null) => {
    dispatch({ type: 'SET_USER', payload: user });
  };

  const showNotification = (
    message: string,
    severity: Notification['severity'] = 'info',
    autoHideDuration: number = 6000
  ) => {
    dispatch({
      type: 'ADD_NOTIFICATION',
      payload: { message, severity, autoHideDuration },
    });
  };

  const clearNotifications = () => {
    dispatch({ type: 'CLEAR_NOTIFICATIONS' });
  };

  const triggerFoodLogged = () => {
    dispatch({ type: 'TRIGGER_FOOD_LOGGED' });
  };

  const removeNotification = (id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  };

  return (
    <AppContext.Provider
      value={{
        state,
        setLoading,
        setUser,
        showNotification,
        clearNotifications,
        triggerFoodLogged,
      }}
    >
      {children}
      
      {/* Global Loading Backdrop */}
      <Backdrop
        open={state.isLoading}
        sx={{ 
          color: '#fff', 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          flexDirection: 'column',
          gap: 2,
        }}
      >
        <CircularProgress color="inherit" size={60} />
        {state.loadingMessage && (
          <div style={{ textAlign: 'center', fontSize: '1.1rem' }}>
            {state.loadingMessage}
          </div>
        )}
      </Backdrop>

      {/* Global Notifications */}
      {state.notifications.map((notification) => (
        <Snackbar
          key={notification.id}
          open={true}
          autoHideDuration={notification.autoHideDuration}
          onClose={() => removeNotification(notification.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ mt: 8 }}
        >
          <Alert
            onClose={() => removeNotification(notification.id)}
            severity={notification.severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}; 