import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ShoppingItem } from '../types';

const ShoppingListPage: React.FC = () => {
  const [shoppingLists, setShoppingLists] = useState<{ items: ShoppingItem[]; created_at: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchShoppingLists = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('No authentication token found');
        }

        const response = await fetch('http://localhost:8000/user/shopping-list', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!response.ok) throw new Error('Failed to fetch shopping lists');
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

  const handleExport = async (items: ShoppingItem[]) => {
    try {
      const response = await fetch('http://localhost:8000/export/shopping-list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ items }),
      });

      if (!response.ok) throw new Error('Failed to export shopping list');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `shopping-list-${new Date().toISOString()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom color="primary">
            My Shopping Lists
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {shoppingLists.length === 0 ? (
            <Typography>No shopping lists found</Typography>
          ) : (
            shoppingLists.map((list, index) => (
              <Accordion key={index}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>
                    Shopping List - {new Date(list.created_at).toLocaleDateString()}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
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
                              <ListItemText
                                primary={item.name}
                                secondary={item.amount}
                              />
                            </ListItem>
                            {itemIndex < items.length - 1 && <Divider />}
                          </React.Fragment>
                        ))}
                      </List>
                    </Box>
                  ))}
                  <Button
                    variant="outlined"
                    onClick={() => handleExport(list.items)}
                    sx={{ mt: 2 }}
                  >
                    Export PDF
                  </Button>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default ShoppingListPage; 