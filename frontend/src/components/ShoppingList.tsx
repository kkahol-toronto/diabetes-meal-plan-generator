import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Box,
  CircularProgress,
  Checkbox,
  Divider,
  ListItemIcon,
  Chip,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import PrintIcon from '@mui/icons-material/Print';
import { ShoppingItem } from '../types';

interface ShoppingListProps {
  shoppingList: ShoppingItem[];
}

const ShoppingList: React.FC<ShoppingListProps> = ({ shoppingList }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<ShoppingItem[]>(
    shoppingList.map(item => ({ ...item, checked: false }))
  );

  useEffect(() => {
    const fetchShoppingList = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:8000/user/shopping-list', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch shopping list');
        }
        const data = await response.json();
        setItems((data.items || []).map((item: Omit<ShoppingItem, 'checked'>) => ({
          ...item,
          checked: false
        })));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchShoppingList();
  }, []);

  const handleToggle = (index: number) => {
    const newItems = [...items];
    newItems[index] = {
      ...newItems[index],
      checked: !newItems[index].checked,
    };
    setItems(newItems);
  };

  const handleCopyList = () => {
    const text = items
      .map(item => `${item.name} - ${item.amount}`)
      .join('\n');
    navigator.clipboard.writeText(text);
  };

  const handlePrintList = () => {
    window.print();
  };

  const categories = Array.from(new Set(items.map(item => item.category)));

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography color="error" variant="h6">
            {error}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/')}
            sx={{ mt: 2 }}
          >
            Back to Form
          </Button>
        </Paper>
      </Container>
    );
  }

  if (!items.length) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No shopping list generated yet
        </Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Shopping List
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <IconButton onClick={handleCopyList} color="primary" sx={{ mr: 1 }}>
            <ContentCopyIcon />
          </IconButton>
          <IconButton onClick={handlePrintList} color="primary">
            <PrintIcon />
          </IconButton>
        </Box>

        {categories.map((category, categoryIndex) => (
          <Box key={category} sx={{ mb: 3 }}>
            <Chip
              label={category}
              color="primary"
              variant="outlined"
              sx={{ mb: 2 }}
            />
            <List>
              {items
                .filter(item => item.category === category)
                .map((item, itemIndex) => {
                  const index = items.findIndex(i => i === item);
                  return (
                    <React.Fragment key={item.name}>
                      <ListItem>
                        <ListItemIcon>
                          <Checkbox
                            edge="start"
                            checked={item.checked}
                            onChange={() => handleToggle(index)}
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.name}
                          secondary={item.amount}
                          sx={{
                            textDecoration: item.checked ? 'line-through' : 'none',
                            color: item.checked ? 'text.secondary' : 'text.primary',
                          }}
                        />
                      </ListItem>
                      {itemIndex < items.filter(i => i.category === category).length - 1 && (
                        <Divider />
                      )}
                    </React.Fragment>
                  );
                })}
            </List>
          </Box>
        ))}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            variant="outlined"
            color="primary"
            onClick={() => navigate('/recipes')}
          >
            Back to Recipes
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/')}
          >
            Start New Plan
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default ShoppingList; 