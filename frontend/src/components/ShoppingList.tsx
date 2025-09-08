import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Button,
  Box,
  CircularProgress,
  Checkbox,
  Divider,
  ListItemIcon,
  Chip,
  Grid,
  Alert,
  Card,
  CardContent,
  keyframes,
  Fade,
  Slide,
  Zoom,
} from '@mui/material';
import { Theme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import PrintIcon from '@mui/icons-material/Print';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import RefreshIcon from '@mui/icons-material/Refresh';
import CategoryIcon from '@mui/icons-material/Category';
import { ShoppingItem } from '../types';
import config from '../config/environment';

// Enhanced mobile animations
const slideInUp = keyframes`
  0% { 
    opacity: 0;
    transform: translateY(30px);
  }
  100% { 
    opacity: 1;
    transform: translateY(0);
  }
`;

const fadeInScale = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.95);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

const bounceIn = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.3);
  }
  50% { 
    opacity: 1;
    transform: scale(1.05);
  }
  70% { 
    transform: scale(0.9);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

interface ShoppingListProps {
  shoppingList: ShoppingItem[];
}

const ShoppingList: React.FC<ShoppingListProps> = ({ shoppingList: initialShoppingList }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<Array<ShoppingItem & { checked: boolean }>>(
    initialShoppingList.map(item => ({ ...item, checked: false }))
  );

  useEffect(() => {
    const fetchAndSetShoppingList = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }
        const response = await fetch(`${config.API_URL}/user/shopping-list`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch shopping list'}));
          throw new Error(errorData.detail || 'Failed to fetch shopping list');
        }
        const data = await response.json();
        setItems((data.items || []).map((item: ShoppingItem) => ({
          ...item,
          checked: false
        })));
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (initialShoppingList && initialShoppingList.length > 0) {
        setItems(initialShoppingList.map(item => ({ ...item, checked: false })));
        setLoading(false);
    } else {
        fetchAndSetShoppingList();
    }
  }, [initialShoppingList, navigate]);

  const handleToggle = (itemName: string, itemCategory: string) => {
    setItems(prevItems => 
      prevItems.map(item => 
        item.name === itemName && item.category === itemCategory 
          ? { ...item, checked: !item.checked } 
          : item
      )
    );
  };

  const handleCopyList = () => {
    const textToCopy = categories.map(category => {
      const categoryItems = items
        .filter(item => item.category === category)
        .map(item => `${item.checked ? '[x]' : '[ ]'} ${item.name} - ${item.amount}`)
      .join('\n');
      return `${category}:\n${categoryItems}`;
    }).join('\n\n');
    navigator.clipboard.writeText(textToCopy).then(() => {
      console.log('Shopping list copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy shopping list: ', err);
    });
  };

  const handlePrintList = () => {
    window.print();
  };

  const categories = Array.from(new Set(items.map(item => item.category))).sort();

  if (loading) {
    return (
      <Fade in={true} timeout={800}>
        <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" sx={{ p: 4, minHeight: '300px' }}>
          <CircularProgress sx={{ mb: 2, color: 'white' }} size={60} />
          <Typography sx={{ color: 'white', fontWeight: 600, textShadow: '0 1px 3px rgba(0,0,0,0.3)' }}>
            Loading shopping list...
          </Typography>
        </Box>
      </Fade>
    );
  }

  if (error) {
    return (
      <Fade in={true} timeout={800}>
        <Card sx={{ 
          p: { xs: 2, sm: 3 }, 
          borderRadius: '20px', 
          m: 2,
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
        }}>
          <Alert 
            severity="error" 
            sx={{ 
              mb: 2,
              borderRadius: '12px',
              background: 'rgba(244, 67, 54, 0.1)',
              border: '1px solid rgba(244, 67, 54, 0.2)',
            }}
          >
            {error}
          </Alert>
          <Button
            variant="contained"
            onClick={() => navigate(-1)}
            startIcon={<NavigateBeforeIcon />}
            sx={{ 
              borderRadius: '50px', 
              px: 3,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                transform: 'translateY(-2px)',
              }
            }}
          >
            Go Back
          </Button>
        </Card>
      </Fade>
    );
  }

  if (!items.length) {
    return (
      <Fade in={true} timeout={800}>
        <Card sx={{ 
          p: { xs: 2, sm: 3 }, 
          textAlign: 'center', 
          borderRadius: '20px', 
          m: 2,
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)',
        }}>
          <Typography variant="h6" sx={{ color: '#667eea', fontWeight: 600, mb: 1 }}>
            Your Shopping List is Empty
          </Typography>
          <Typography variant="body1" sx={{ color: 'rgba(102, 126, 234, 0.7)' }}>
            It seems no items were added to the shopping list.
          </Typography>
        </Card>
      </Fade>
    );
  }

  return (
    <Box sx={{ p: { xs: 1, sm: 2 } }}>
      <Fade in={true} timeout={1000}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography 
            variant="h5" 
            component="h2" 
            sx={{ 
              fontWeight: 700, 
              color: 'white',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              mb: 1,
              fontSize: { xs: '1.25rem', sm: '1.5rem' }
            }}
          >
            🛒 Your Shopping List
          </Typography>
          <Typography 
            variant="body2" 
            sx={{ 
              color: 'white',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              fontWeight: 600,
              fontSize: '1rem'
            }}
          >
            Everything you need for your meal plan
          </Typography>
        </Box>
      </Fade>

      <Slide direction="down" in={true} timeout={1200}>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4, gap: 2 }}>
          <Button 
            onClick={handleCopyList} 
            variant="contained" 
            startIcon={<ContentCopyIcon />} 
            sx={{
              borderRadius: '50px',
              px: 3,
              py: 1,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
              }
            }}
            size="small"
          >
            Copy List
          </Button>
          <Button 
            onClick={handlePrintList} 
            variant="contained" 
            startIcon={<PrintIcon />} 
            sx={{
              borderRadius: '50px',
              px: 3,
              py: 1,
              background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
              boxShadow: '0 4px 15px rgba(76, 175, 80, 0.3)',
              '&:hover': {
                background: 'linear-gradient(135deg, #45a049 0%, #388e3c 100%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(76, 175, 80, 0.4)',
              }
            }}
            size="small"
          >
            Print List
          </Button>
        </Box>
      </Slide>

      {categories.map((category) => (
          <Box key={category} sx={{ mb: 3 }}>
            <Chip
            icon={<CategoryIcon />}
              label={category}
            color="secondary"
            sx={{ mb: 1.5, fontWeight: 'medium', fontSize: '1.1rem', p: 0.5, borderRadius: '8px' }}
            />
          <List sx={{ backgroundColor: (theme: Theme) => theme.palette.action.hover, borderRadius: '8px', p: 1}} dense>
              {items
                .filter(item => item.category === category)
              .map((item, itemIndex, arr) => (
                <React.Fragment key={`${item.name}-${item.category}-${itemIndex}`}>
                  <ListItem sx={{
                    py: 0.8,
                    backgroundColor: 'background.paper',
                    mb: 0.5,
                    borderRadius: '6px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                    '&:hover': { backgroundColor: (theme: Theme) => theme.palette.action.selected }
                  }}>
                    <ListItemIcon sx={{minWidth: 'auto', mr: 1.5}}>
                          <Checkbox
                            edge="start"
                            checked={item.checked}
                        onChange={() => handleToggle(item.name, item.category)}
                        size="small"
                          />
                        </ListItemIcon>
                        <ListItemText
                      primary={<Typography variant="body1" component="span">{item.name}</Typography>}
                      secondary={<Typography variant="body2" component="span" sx={{ fontWeight: 'bold', color: 'text.primary', ml: 0.5 }}>{`[${item.amount}]`}</Typography>}
                          sx={{
                            textDecoration: item.checked ? 'line-through' : 'none',
                            color: item.checked ? 'text.secondary' : 'text.primary',
                        opacity: item.checked ? 0.6 : 1,
                          }}
                        />
                      </ListItem>
                  {itemIndex < arr.length - 1 && (
                    <Divider variant="inset" component="li" sx={{my: 0.5, borderColor: 'transparent'}} />
                      )}
                    </React.Fragment>
              ))}
            </List>
          </Box>
        ))}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4, borderTop: '1px solid lightgrey', pt: 3 }}>
          <Button
            variant="outlined"
            onClick={() => navigate(-1)}
            startIcon={<NavigateBeforeIcon />}
            sx={{ borderRadius: '20px', px: 3 }}
          >
            Back to Recipes
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/')}
            startIcon={<RefreshIcon />}
            sx={{ borderRadius: '20px', px: 3 }}
          >
            Start New Plan
          </Button>
        </Box>
      </Box>
  );
};

export default ShoppingList; 