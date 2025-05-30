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
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import HomeIcon from '@mui/icons-material/Home';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import ChatIcon from '@mui/icons-material/Chat';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [userInfo, setUserInfo] = useState<{ username: string; is_admin: boolean; name?: string } | null>(null);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setUserInfo(null);
          return;
        }

        try {
          const tokenParts = token.split('.');
          if (tokenParts.length !== 3) {
            throw new Error('Invalid token format');
          }
          const payload = JSON.parse(atob(tokenParts[1]));
          if (payload.exp * 1000 < Date.now()) {
            throw new Error('Token expired');
          }
          
          setUserInfo({
            username: payload.sub,
            is_admin: payload.is_admin || false,
            name: payload.name
          });
          
          if (payload.is_admin) {
            localStorage.setItem('isAdmin', 'true');
          } else {
            localStorage.removeItem('isAdmin');
          }
        } catch (e) {
          localStorage.removeItem('token');
          localStorage.removeItem('isAdmin');
          setUserInfo(null);
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
    { text: 'Meal Plan', icon: <RestaurantIcon />, path: 'meal-plan' },
    { text: 'Recipes', icon: <RestaurantIcon />, path: 'recipes' },
    { text: 'Shopping List', icon: <RestaurantIcon />, path: 'shopping-list' },
    { text: 'Meal History', icon: <RestaurantIcon />, path: 'meals' },
    { text: 'Chat', icon: <ChatIcon />, path: 'chat' },
  ];

  if (userInfo?.is_admin) {
    menuItems.push({ text: 'Admin Panel', icon: <AdminPanelSettingsIcon />, path: 'admin' });
  }

  const handleNavigation = (path: string) => {
    console.log('Navigating to:', path);
    navigate(path);
    setDrawerOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    setUserInfo(null);
    navigate('login');
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

  // Helper function to check if a path is active
  const isActivePath = (path: string) => {
    const currentPath = location.pathname.replace(/^\/+/, '');
    const checkPath = path.replace(/^\/+/, '');
    return currentPath === checkPath;
  };

  return (
    <AppBar position="static">
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
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Diabetes Diet Manager
        </Typography>
        {!isMobile && (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {menuItems.map((item) => (
              <Button
                key={item.text}
                color="inherit"
                startIcon={item.icon}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  backgroundColor: isActivePath(item.path) ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                }}
              >
                {item.text}
              </Button>
            ))}
            {userInfo ? (
              <>
                <Typography variant="body1" sx={{ mr: 2 }}>
                  Welcome, {userInfo.name || userInfo.username}!
                </Typography>
                <Button color="inherit" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            ) : (
              <Button color="inherit" onClick={() => handleNavigation('login')}>
                Login
              </Button>
            )}
          </Box>
        )}
      </Toolbar>
      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        <Box
          sx={{ width: 250 }}
          role="presentation"
        >
          <List>
            {menuItems.map((item) => (
              <ListItem
                button
                key={item.text}
                onClick={() => handleNavigation(item.path)}
                selected={isActivePath(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
            {userInfo ? (
              <ListItem button onClick={handleLogout}>
                <ListItemText primary="Logout" />
              </ListItem>
            ) : (
              <ListItem button onClick={() => handleNavigation('login')}>
                <ListItemText primary="Login" />
              </ListItem>
            )}
          </List>
        </Box>
      </Drawer>
    </AppBar>
  );
};

export default Navigation; 