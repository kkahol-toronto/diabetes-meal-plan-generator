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
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { isTokenExpired } from '../utils/auth';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [userInfo, setUserInfo] = useState<{ username: string; is_admin: boolean; name?: string } | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

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
<<<<<<< HEAD
    { text: 'Recipes', icon: <BookIcon />, path: '/my-recipes' },
    { text: 'Shopping List', icon: <ShoppingCartIcon />, path: '/my-shopping-lists' },
=======
>>>>>>> origin/changed_ui_backend_ram
    { text: 'Chat', icon: <ChatIcon />, path: '/chat' },
    { text: 'History', icon: <BookIcon />, path: '/meal-plan/history' },
  ];

  // Add admin panel link if user is admin
  if (userInfo?.is_admin) {
    menuItems.push({ text: 'Admin Panel', icon: <AdminPanelSettingsIcon />, path: '/admin' });
  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    setUserInfo(null);
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
    <List>
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
        <ListItem button onClick={() => navigate('/login')}>
          <ListItemText primary="Login" />
        </ListItem>
      )}
    </List>
  );

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
                onClick={() => navigate(item.path)}
                sx={{
                  backgroundColor: location.pathname === item.path ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
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
              <Button color="inherit" onClick={() => navigate('/login')}>
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
          onClick={toggleDrawer(false)}
          onKeyDown={toggleDrawer(false)}
        >
          <NavigationList />
        </Box>
      </Drawer>
    </AppBar>
  );
};

export default Navigation; 