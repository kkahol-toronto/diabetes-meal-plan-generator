import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import HomeIcon from '@mui/icons-material/Home';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import BookIcon from '@mui/icons-material/Book';
import ChatIcon from '@mui/icons-material/Chat';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import { Psychology } from '@mui/icons-material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import HistoryIcon from '@mui/icons-material/History';
import SettingsIcon from '@mui/icons-material/Settings';
import { isTokenExpired } from '../utils/auth';
import { useApp } from '../contexts/AppContext';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [userInfo, setUserInfo] = useState<{ username: string; is_admin: boolean; name?: string } | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { showNotification } = useApp();

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setUserInfo(null);
          return;
        }

        // Validate token format and get user info from token
        try {
          if (isTokenExpired(token)) {
            throw new Error('Token expired');
          }
          
          const tokenParts = token.split('.');
          if (tokenParts.length !== 3) {
            throw new Error('Invalid token format');
          }
          
          // Set user info from token
          const payload = JSON.parse(atob(tokenParts[1]));
          setUserInfo({
            username: payload.sub,
            is_admin: payload.is_admin || false,
            name: payload.name
          });
          
          // If admin status changed, update localStorage
          if (payload.is_admin) {
            localStorage.setItem('isAdmin', 'true');
          } else {
            localStorage.removeItem('isAdmin');
          }
          
          return; // Skip the API call since we have the info from token
        } catch (e) {
          // Clear invalid token
          localStorage.removeItem('token');
          localStorage.removeItem('isAdmin');
          setUserInfo(null);
          return;
        }
      } catch (error) {
        console.error('Failed to fetch user info:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('isAdmin');
        setUserInfo(null);
      }
    };

    fetchUserInfo();
  }, []);

  const menuItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/' },
    { text: 'Meal Plan', icon: <RestaurantIcon />, path: '/meal-plan' },
    { text: 'Chat', icon: <ChatIcon />, path: '/chat' },
    { text: 'Consumption History', icon: <HistoryIcon />, path: '/consumption-history' },
    { text: 'Meal Plan History', icon: <BookIcon />, path: '/meal_plans' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  // Add admin panel link if user is admin
  if (userInfo?.is_admin) {
    menuItems.push({ text: 'Admin Panel', icon: <AdminPanelSettingsIcon />, path: '/admin' });

  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    setUserInfo(null);
    showNotification('You have been logged out successfully', 'info');
    navigate('/login');
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleDrawer = (open: boolean) => (event: React.KeyboardEvent | React.MouseEvent) => {
    if (
      event.type === 'keydown' &&
      ((event as React.KeyboardEvent).key === 'Tab' || (event as React.KeyboardEvent).key === 'Shift')
    ) {
      return;
    }
    setDrawerOpen(open);
  };

  const NavigationList = () => (
    <List sx={{ py: 0 }}>
      {menuItems.map((item) => (
        <ListItem
          button
          key={item.text}
          onClick={() => {
            console.log(`Navigating to: ${item.path}`);
            navigate(item.path);
            setDrawerOpen(false);
          }}
          selected={location.pathname === item.path}
          sx={{
            color: 'white',
            py: 1.5,
            px: 2,
            borderRadius: 0,
            '&:hover': { 
              backgroundColor: 'rgba(255,255,255,0.1)',
              '& .MuiListItemText-primary': {
                fontWeight: 'bold'
              }
            },
            '&.Mui-selected': { 
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRight: '4px solid white',
              '& .MuiListItemText-primary': {
                fontWeight: 'bold'
              }
            }
          }}
        >
          <ListItemIcon sx={{ 
            color: 'white', 
            minWidth: 40,
            '& .MuiSvgIcon-root': {
              fontSize: '1.2rem'
            }
          }}>
            {item.icon}
          </ListItemIcon>
          <ListItemText 
            primary={item.text}
            primaryTypographyProps={{
              fontSize: '0.95rem',
              fontWeight: location.pathname === item.path ? 'bold' : 'normal'
            }}
          />
        </ListItem>
      ))}
      
      {/* Divider before auth actions */}
      <Box sx={{ borderTop: '1px solid rgba(255,255,255,0.2)', mt: 1, pt: 1 }}>
        {userInfo ? (
          <ListItem 
            button 
            onClick={() => {
              handleLogout();
              setDrawerOpen(false);
            }}
            sx={{
              color: 'white',
              py: 1.5,
              px: 2,
              '&:hover': { 
                backgroundColor: 'rgba(255,255,255,0.1)',
                '& .MuiListItemText-primary': {
                  fontWeight: 'bold'
                }
              }
            }}
          >
            <ListItemIcon sx={{ color: 'white', minWidth: 40 }}>
              <AccountCircleIcon />
            </ListItemIcon>
            <ListItemText 
              primary="Logout" 
              primaryTypographyProps={{
                fontSize: '0.95rem'
              }}
            />
          </ListItem>
        ) : (
          <ListItem 
            button 
            onClick={() => {
              navigate('/login');
              setDrawerOpen(false);
            }}
            sx={{
              color: 'white',
              py: 1.5,
              px: 2,
              '&:hover': { 
                backgroundColor: 'rgba(255,255,255,0.1)',
                '& .MuiListItemText-primary': {
                  fontWeight: 'bold'
                }
              }
            }}
          >
            <ListItemIcon sx={{ color: 'white', minWidth: 40 }}>
              <AccountCircleIcon />
            </ListItemIcon>
            <ListItemText 
              primary="Login" 
              primaryTypographyProps={{
                fontSize: '0.95rem'
              }}
            />
          </ListItem>
        )}
      </Box>
    </List>
  );

  return (
    <AppBar 
      position="static" 
      sx={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        boxShadow: '0 4px 20px rgba(102, 126, 234, 0.3)'
      }}
    >
      <Toolbar>
        {isMobile && (
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={toggleDrawer(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <img 
            src="/dietra_logo.png" 
            alt="Dietra Logo" 
            style={{ 
              height: isMobile ? '40px' : '48px', 
              width: 'auto', 
              marginRight: isMobile ? '8px' : '16px' 
            }} 
          />
          <Typography 
            variant={isMobile ? "h6" : "h6"} 
            component="div"
            sx={{
              fontSize: isMobile ? '1.1rem' : '1.25rem',
              fontWeight: 'bold'
            }}
          >
            Dietra
          </Typography>
        </Box>
        {!isMobile && (
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            {menuItems.map((item) => (
              <Button
                key={item.text}
                color="inherit"
                startIcon={item.icon}
                onClick={() => navigate(item.path)}
                sx={{
                  backgroundColor: location.pathname === item.path ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
                  '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.1)' },
                  borderRadius: 2,
                  px: 1.5,
                  py: 1,
                  fontSize: '0.85rem',
                  minWidth: 'unset',
                  transition: 'all 0.3s ease'
                }}
              >
                {item.text}
              </Button>
            ))}
            {userInfo ? (
              <>
                <Typography variant="body2" sx={{ mr: 1, display: { xs: 'none', md: 'block' } }}>
                  {userInfo.name || userInfo.username}
                </Typography>
                <Button 
                  color="inherit" 
                  size="small"
                  onClick={handleLogout}
                  sx={{ fontSize: '0.85rem' }}
                >
                  Logout
                </Button>
              </>
            ) : (
              <Button 
                color="inherit" 
                size="small"
                onClick={() => navigate('/login')}
                sx={{ fontSize: '0.85rem' }}
              >
                Login
              </Button>
            )}
          </Box>
        )}
      </Toolbar>
      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        <Box
          sx={{ 
            width: 280,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            height: '100%',
            color: 'white',
            display: 'flex',
            flexDirection: 'column'
          }}
          role="presentation"
        >
          {/* Drawer Header */}
          <Box sx={{ 
            p: 2, 
            borderBottom: '1px solid rgba(255,255,255,0.2)',
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}>
            <img 
              src="/dietra_logo.png" 
              alt="Dietra Logo" 
              style={{ 
                height: '32px', 
                width: 'auto'
              }} 
            />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Dietra
            </Typography>
          </Box>
          
          {/* User Info Section */}
          {userInfo && (
            <Box sx={{ 
              p: 2, 
              borderBottom: '1px solid rgba(255,255,255,0.2)',
              bgcolor: 'rgba(255,255,255,0.1)'
            }}>
              <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                {userInfo.name || userInfo.username}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                {userInfo.is_admin ? 'Administrator' : 'User'}
              </Typography>
            </Box>
          )}
          
          {/* Navigation Items */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            <NavigationList />
          </Box>
        </Box>
      </Drawer>
    </AppBar>
  );
};

export default Navigation; 