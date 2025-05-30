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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import PrintIcon from '@mui/icons-material/Print';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ShoppingItem } from '../types';

interface ShoppingListProps {
  shoppingList: ShoppingItem[];
}

const ShoppingList: React.FC<ShoppingListProps> = ({ shoppingList }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [shoppingLists, setShoppingLists] = useState<{ items: ShoppingItem[]; created_at: string }[]>([]);

  useEffect(() => {
    const fetchShoppingLists = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:8000/user/shopping-list', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch shopping lists');
        }
        const data = await response.json();
        setShoppingLists(Array.isArray(data) ? data : [data]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchShoppingLists();
  }, []);

  const handleCopyList = (items: ShoppingItem[]) => {
    const text = items
      .map(item => `${item.name} - ${item.amount}`)
      .join('\n');
    navigator.clipboard.writeText(text);
  };

  const handlePrintList = () => {
    window.print();
  };

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

  if (!shoppingLists.length) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No shopping lists generated yet
        </Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Shopping Lists History
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {shoppingLists.map((list, listIndex) => (
          <Accordion key={listIndex}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>
                Shopping List - {new Date(list.created_at).toLocaleDateString()}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                <IconButton onClick={() => handleCopyList(list.items)} color="primary" sx={{ mr: 1 }}>
                  <ContentCopyIcon />
                </IconButton>
                <IconButton onClick={handlePrintList} color="primary">
                  <PrintIcon />
                </IconButton>
              </Box>

              {Object.entries(
                list.items.reduce((acc: { [key: string]: ShoppingItem[] }, item) => {
                  if (!acc[item.category]) {
                    acc[item.category] = [];
                  }
                  acc[item.category].push(item);
                  return acc;
                }, {})
              ).map(([category, items]) => (
                <Box key={category} sx={{ mb: 3 }}>
                  <Chip
                    label={category}
                    color="primary"
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />
                  <List>
                    {items.map((item, itemIndex) => (
                      <React.Fragment key={itemIndex}>
                        <ListItem>
                          <ListItemIcon>
                            <Checkbox
                              edge="start"
                              checked={item.checked}
                              onChange={() => {
                                const newLists = [...shoppingLists];
                                const newItem = { ...item, checked: !item.checked };
                                const categoryItems = newLists[listIndex].items.map(i => 
                                  i === item ? newItem : i
                                );
                                newLists[listIndex] = {
                                  ...newLists[listIndex],
                                  items: categoryItems
                                };
                                setShoppingLists(newLists);
                              }}
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
                        {itemIndex < items.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
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