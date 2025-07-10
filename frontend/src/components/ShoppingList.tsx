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
      <Box display="flex" justifyContent="center" alignItems="center" sx={{ p: 4, minHeight: '300px' }}>
        <CircularProgress />
        <Typography sx={{ml: 2}}>Loading shopping list...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Paper elevation={3} sx={{ p: {xs: 2, sm:3}, borderRadius: '12px', m: 2 }}>
        <Alert severity="error" sx={{mb: 2}}>{error}</Alert>
          <Button
            variant="contained"
          onClick={() => navigate(-1)}
          startIcon={<NavigateBeforeIcon />}
          sx={{ borderRadius: '20px', px:3 }}
          >
          Go Back
          </Button>
        </Paper>
    );
  }

  if (!items.length) {
    return (
      <Paper elevation={3} sx={{ p: {xs: 2, sm:3}, textAlign: 'center', borderRadius: '12px', m: 2 }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Your Shopping List is Empty
        </Typography>
        <Typography variant="body1" color="text.secondary">
          It seems no items were added to the shopping list.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: {xs: 2, sm: 3, md: 4}, borderRadius: '16px' }}>
      <Typography variant="h5" component="h2" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 3 }}>
        Your Shopping List
        </Typography>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3, gap: 1 }}>
        <Button onClick={handleCopyList} variant="outlined" startIcon={<ContentCopyIcon />} sx={{borderRadius: '20px'}} size="small">
          Copy List
        </Button>
        <Button onClick={handlePrintList} variant="outlined" startIcon={<PrintIcon />} sx={{borderRadius: '20px'}} size="small">
          Print List
        </Button>
        </Box>

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
      </Paper>
  );
};

export default ShoppingList; 