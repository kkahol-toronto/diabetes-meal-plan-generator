import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import config from '../config/environment';
import {
  Paper,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Box,
  Chip,
  alpha,
} from '@mui/material';
import {
  Home as HomeIcon,
  Restaurant as RestaurantIcon,
  Chat as ChatIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  AdminPanelSettings as AdminIcon,
  Book as BookIcon,
  MoreHoriz as MoreIcon,
} from '@mui/icons-material';
interface NavigationItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  color: string;
  category?: string;
}

const BottomNavigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const [value, setValue] = useState<string>('/');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [userInfo, setUserInfo] = useState<any>(null);

  // Fetch user info to determine if admin
  useEffect(() => {
    const fetchUserInfo = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(`${config.API_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          setUserInfo(data);
        }
      } catch (error) {
        console.error('Failed to fetch user info:', error);
      }
    };

    fetchUserInfo();
  }, []);

  // Update selected tab based on current route
  useEffect(() => {
    const currentPath = location.pathname;
    setValue(currentPath);
  }, [location.pathname]);

  // Primary navigation items (always visible)
  const primaryItems: NavigationItem[] = [
    { 
      text: 'Home', 
      icon: <HomeIcon />, 
      path: '/',
      color: '#8B5CF6',
      category: 'main'
    },
    { 
      text: 'Meal Plan', 
      icon: <RestaurantIcon />, 
      path: '/meal-plan',
      color: '#A855F7',
      category: 'main'
    },
    { 
      text: 'Chat', 
      icon: <ChatIcon />, 
      path: '/chat',
      color: '#9333EA',
      category: 'main'
    },
    { 
      text: 'More', 
      icon: <MoreIcon />, 
      path: '/more',
      color: '#7C3AED',
      category: 'more'
    },
  ];

  // Secondary items (shown in "More" menu)
  const secondaryItems: NavigationItem[] = [
    { 
      text: 'Consumption History', 
      icon: <HistoryIcon />, 
      path: '/consumption-history',
      color: '#C084FC',
      category: 'history'
    },
    { 
      text: 'Meal Plan History', 
      icon: <BookIcon />, 
      path: '/meal_plans',
      color: '#DDD6FE',
      category: 'history'
    },
    { 
      text: 'Settings', 
      icon: <SettingsIcon />, 
      path: '/settings',
      color: '#A855F7',
      category: 'system'
    },
  ];

  // Add admin panel if user is admin
  if (userInfo?.is_admin) {
    secondaryItems.push({
      text: 'Admin Panel',
      icon: <AdminIcon />,
      path: '/admin',
      color: '#8B5CF6',
      category: 'system'
    });
  }

  const handleNavigation = (path: string) => {
    if (path === '/more') {
      // Don't navigate, just open menu
      return;
    }
    setValue(path);
    navigate(path);
  };

  const handleMoreClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleSecondaryNavigation = (path: string) => {
    handleMenuClose();
    setValue(path);
    navigate(path);
  };


  const isSecondaryActive = secondaryItems.some(item => item.path === value);

  return (
    <>
      {/* Floating Bottom Navigation */}
      <Box 
        sx={{ 
          position: 'fixed', 
          bottom: 20, 
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          width: 'auto',
          maxWidth: '90%',
          '@media (max-width: 600px)': {
            bottom: 16,
            maxWidth: '95%',
          },
        }}
      >
        <Paper 
          sx={{ 
            background: 'transparent',
            backdropFilter: 'none',
            borderRadius: '0',
            border: 'none',
            boxShadow: 'none',
            padding: 0,
          }} 
          elevation={0}
        >
        <Box 
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 3,
            '@media (max-width: 600px)': {
              gap: 2,
            },
          }}
        >
          {primaryItems.map((item) => {
            const isActive = value === item.path || (item.path === '/more' && isSecondaryActive);
            
            return (
              <Box
                key={item.path}
                onClick={item.path === '/more' ? handleMoreClick : () => handleNavigation(item.path)}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: 70,
                  padding: '16px 12px',
                  borderRadius: '24px',
                  cursor: 'pointer',
                  position: 'relative',
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  background: isActive 
                    ? 'rgba(255, 255, 255, 0.95)' 
                    : 'rgba(255, 255, 255, 0.85)',
                  backdropFilter: 'blur(20px)',
                  border: isActive 
                    ? `2px solid ${item.color}` 
                    : '1px solid rgba(255, 255, 255, 0.3)',
                  boxShadow: isActive 
                    ? `0 8px 32px ${alpha(item.color, 0.4)}, 0 0 0 1px ${alpha(item.color, 0.2)}` 
                    : '0 4px 16px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(255, 255, 255, 0.8) inset',
                  '@media (max-width: 600px)': {
                    minWidth: 60,
                    padding: '14px 10px',
                    borderRadius: '20px',
                  },
                  '&:hover': {
                    transform: 'translateY(-4px) scale(1.08)',
                    background: isActive 
                      ? 'rgba(255, 255, 255, 1)' 
                      : 'rgba(255, 255, 255, 0.95)',
                    boxShadow: isActive 
                      ? `0 12px 40px ${alpha(item.color, 0.5)}, 0 0 0 2px ${alpha(item.color, 0.3)}` 
                      : `0 8px 25px rgba(0, 0, 0, 0.2), 0 4px 12px rgba(255, 255, 255, 0.9) inset`,
                    border: isActive 
                      ? `2px solid ${item.color}` 
                      : `1px solid ${alpha(item.color, 0.4)}`,
                  },
                }}
              >
                <Box
                  sx={{
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 1,
                  }}
                >
                  {React.cloneElement(item.icon, {
                    sx: {
                      fontSize: 26,
                      color: isActive ? item.color : 'rgba(100, 100, 100, 0.8)',
                      transition: 'all 0.3s ease',
                      filter: isActive ? `drop-shadow(0 2px 4px ${alpha(item.color, 0.3)})` : 'drop-shadow(0 1px 2px rgba(0,0,0,0.1))',
                      '@media (max-width: 600px)': {
                        fontSize: 24,
                      },
                    },
                  })}
                  {/* Badge for More button when secondary is active */}
                  {item.path === '/more' && isSecondaryActive && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -4,
                        right: -4,
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        background: `linear-gradient(45deg, ${item.color}, ${alpha(item.color, 0.8)})`,
                        boxShadow: `0 2px 8px ${alpha(item.color, 0.4)}`,
                        border: '2px solid rgba(255, 255, 255, 0.8)',
                      }}
                    />
                  )}
                </Box>
                <Box
                  component="span"
                  sx={{
                    fontSize: '0.75rem',
                    fontWeight: isActive ? 700 : 500,
                    color: isActive ? item.color : 'rgba(80, 80, 80, 0.9)',
                    textAlign: 'center',
                    lineHeight: 1.2,
                    letterSpacing: '0.02em',
                    textShadow: isActive ? `0 1px 2px ${alpha(item.color, 0.1)}` : '0 1px 2px rgba(255,255,255,0.8)',
                    '@media (max-width: 600px)': {
                      fontSize: '0.7rem',
                    },
                  }}
                >
                  {item.text}
                </Box>
                {/* Active indicator */}
                {isActive && (
                  <Box
                    sx={{
                      position: 'absolute',
                      bottom: 4,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: 20,
                      height: 3,
                      borderRadius: '2px',
                      background: `linear-gradient(90deg, ${item.color}, ${alpha(item.color, 0.8)})`,
                      boxShadow: `0 2px 8px ${alpha(item.color, 0.4)}`,
                    }}
                  />
                )}
              </Box>
            );
          })}
        </Box>
        </Paper>
      </Box>

      {/* More Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        sx={{
          '& .MuiPaper-root': {
            borderRadius: '24px',
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(25px)',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15), 0 4px 16px rgba(255, 255, 255, 0.8) inset',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            minWidth: 240,
            marginBottom: 2,
            overflow: 'visible',
          },
        }}
      >
        {/* Category Headers and Items */}
        <Box sx={{ p: 1 }}>
          <Chip 
            label="History" 
            size="small" 
            sx={{ 
              mb: 1, 
              backgroundColor: alpha('#C084FC', 0.1),
              color: '#C084FC',
              fontWeight: 600,
              fontSize: '0.7rem'
            }} 
          />
          {secondaryItems.filter(item => item.category === 'history').map((item) => (
            <MenuItem
              key={item.path}
              onClick={() => handleSecondaryNavigation(item.path)}
              selected={value === item.path}
              sx={{
                borderRadius: '16px',
                mb: 0.5,
                mx: 1,
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                background: 'rgba(248, 250, 252, 0.8)',
                border: '1px solid rgba(200, 200, 200, 0.3)',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.9)',
                  border: `1px solid ${alpha(item.color, 0.5)}`,
                  transform: 'translateY(-2px) scale(1.02)',
                  boxShadow: `0 6px 20px ${alpha(item.color, 0.2)}`,
                },
                '&.Mui-selected': {
                  background: `linear-gradient(135deg, ${item.color} 0%, ${alpha(item.color, 0.8)} 100%)`,
                  border: `1px solid ${item.color}`,
                  transform: 'translateY(-3px) scale(1.05)',
                  boxShadow: `0 8px 25px ${alpha(item.color, 0.4)}`,
                  color: 'white',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {React.cloneElement(item.icon, {
                  sx: { 
                    color: value === item.path ? 'white' : 'rgba(100, 100, 100, 0.8)',
                    fontSize: 20 
                  },
                })}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                sx={{
                  '& .MuiListItemText-primary': {
                    fontSize: '0.875rem',
                    fontWeight: value === item.path ? 600 : 400,
                    color: value === item.path ? 'white' : 'rgba(80, 80, 80, 0.9)',
                  },
                }}
              />
            </MenuItem>
          ))}
          
          <Chip 
            label="System" 
            size="small" 
            sx={{ 
              mt: 1,
              mb: 1, 
              backgroundColor: alpha('#A855F7', 0.1),
              color: '#A855F7',
              fontWeight: 600,
              fontSize: '0.7rem'
            }} 
          />
          {secondaryItems.filter(item => item.category === 'system').map((item) => (
            <MenuItem
              key={item.path}
              onClick={() => handleSecondaryNavigation(item.path)}
              selected={value === item.path}
              sx={{
                borderRadius: '16px',
                mb: 0.5,
                mx: 1,
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                background: 'rgba(248, 250, 252, 0.8)',
                border: '1px solid rgba(200, 200, 200, 0.3)',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.9)',
                  border: `1px solid ${alpha(item.color, 0.5)}`,
                  transform: 'translateY(-2px) scale(1.02)',
                  boxShadow: `0 6px 20px ${alpha(item.color, 0.2)}`,
                },
                '&.Mui-selected': {
                  background: `linear-gradient(135deg, ${item.color} 0%, ${alpha(item.color, 0.8)} 100%)`,
                  border: `1px solid ${item.color}`,
                  transform: 'translateY(-3px) scale(1.05)',
                  boxShadow: `0 8px 25px ${alpha(item.color, 0.4)}`,
                  color: 'white',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {React.cloneElement(item.icon, {
                  sx: { 
                    color: value === item.path ? 'white' : 'rgba(100, 100, 100, 0.8)',
                    fontSize: 20 
                  },
                })}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                sx={{
                  '& .MuiListItemText-primary': {
                    fontSize: '0.875rem',
                    fontWeight: value === item.path ? 600 : 400,
                    color: value === item.path ? 'white' : 'rgba(80, 80, 80, 0.9)',
                  },
                }}
              />
            </MenuItem>
          ))}
        </Box>
      </Menu>
    </>
  );
};

export default BottomNavigation;
