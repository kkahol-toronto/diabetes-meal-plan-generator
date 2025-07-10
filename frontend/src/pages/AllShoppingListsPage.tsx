import React, { useState, useEffect } from 'react';
import config from '../config/environment';
import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  Divider,
  ListItemIcon,
  Chip,
} from '@mui/material';
import { ShoppingItem } from '../types'; // Assuming ShoppingItem type is in ../types
import { useNavigate } from 'react-router-dom';

// Icons
import CategoryIcon from '@mui/icons-material/Category';
import ShoppingBasketIcon from '@mui/icons-material/ShoppingBasket';
import EventNoteIcon from '@mui/icons-material/EventNote';


interface StoredShoppingList {
  id: string; // Or a timestamp
  createdAt: string; // Or Date
  items: Array<ShoppingItem & { checked?: boolean }>; // Checked is optional for display purposes here
  // Add any other metadata for a shopping list, e.g., mealPlanId it was generated from
}

const AllShoppingListsPage: React.FC = () => {
  const [shoppingLists, setShoppingLists] = useState<StoredShoppingList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAllShoppingLists = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }
        // Assuming backend endpoint /user/shopping-lists returns an array of StoredShoppingList
        const response = await fetch(`${config.API_URL}/user/shopping-list`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch shopping lists' }));
          throw new Error(errorData.detail || 'Failed to fetch shopping lists');
        }
        const data = await response.json();
        // Backend currently returns the latest shopping list as { items: [...] }
        // or an empty object/array if no lists.
        // For history, backend needs to return an array of StoredShoppingList.
        // Temporary adaptation:

        console.log('Fetched data from /user/shopping-list:', JSON.stringify(data, null, 2));

        if (Array.isArray(data) && data.length > 0 && data[0].items) {
            // Ideal case: Backend returns StoredShoppingList[]
            setShoppingLists(data.map((list: StoredShoppingList) => ({...list, items: list.items.map((item: ShoppingItem) => ({...item, checked: !!item.checked})) })));
        } else if (data && data.items && Array.isArray(data.items)) {
            // Temporary adaptation: Backend returns a single { items: [...] }
            console.log('Adapting single shopping list to StoredShoppingList array.');
            setShoppingLists([{
                id: new Date().toISOString() + '-current', // Placeholder
                createdAt: new Date().toLocaleString(), // Placeholder
                items: data.items.map((item: ShoppingItem) => ({...item, checked: false })) 
            }]);
        } else if (Array.isArray(data) && data.length === 0) {
            // Backend returns an empty array, meaning no shopping lists found
            console.log('Backend returned an empty array for shopping lists.');
            setShoppingLists([]);
        } else if (typeof data === 'object' && data !== null && Object.keys(data).length === 0) {
            // Backend returns an empty object {}
            console.log('Backend returned an empty object for shopping lists.');
            setShoppingLists([]);
        } else if (data === null) {
            // Backend returns null
            console.log('Backend returned null for shopping lists.');
            setShoppingLists([]);
        } else {
             // Unexpected data structure
            console.warn('Unexpected data structure from /user/shopping-list:', data);
            setError('Received unexpected data format for shopping lists.');
            setShoppingLists([]);
        }

      } catch (err) {
        console.error("Error in fetchAllShoppingLists:", err);
        setError(err instanceof Error ? err.message : 'An unexpected error occurred while fetching shopping lists.');
      } finally {
        setLoading(false);
      }
    };

    fetchAllShoppingLists();
  }, [navigate]);

  // Toggling checked state here is for local display convenience within this page only.
  // It does not persist back to the server or affect other views.
  const handleToggleItem = (listId: string, itemName: string, itemCategory: string) => {
    setShoppingLists(prevLists =>
      prevLists.map(list =>
        list.id === listId
          ? {
              ...list,
              items: list.items.map(item =>
                item.name === itemName && item.category === itemCategory
                  ? { ...item, checked: !item.checked }
                  : item
              ),
            }
          : list
      )
    );
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography>Loading your saved shopping lists...</Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (shoppingLists.length === 0) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: 'center' }}>
         <Paper sx={{p:3, borderRadius: '12px'}}>
            <Typography variant="h6">No Saved Shopping Lists Found</Typography>
            <Typography color="text.secondary">Generate a meal plan to create your first shopping list!</Typography>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 4 }}>
        My Saved Shopping Lists
      </Typography>
      {shoppingLists.map((listSet) => {
        const categories = Array.from(new Set(listSet.items.map(item => item.category))).sort();
        return (
          <Paper key={listSet.id} elevation={2} sx={{ p: {xs:2, sm:3}, mb: 3, borderRadius: '16px' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid lightgrey', pb:1, mb:2}}>
                <ListItemIcon sx={{minWidth:'auto', mr: 1, color: 'primary.main'}}><EventNoteIcon /></ListItemIcon>
                <Typography variant="h6" component="h3">
                    List from: {listSet.createdAt} (ID: {listSet.id.substring(0,10)})
                </Typography>
            </Box>
            {categories.map((category) => (
              <Box key={category} sx={{ mb: 2.5 }}>
                <Chip
                  icon={<CategoryIcon />}
                  label={category}
                  color="secondary"
                  sx={{ mb: 1.5, fontWeight: 'medium', fontSize: '1.1rem', p: 0.5, borderRadius: '8px' }}
                />
                <List sx={{ backgroundColor: (theme) => theme.palette.action.hover, borderRadius: '8px', p: 1}} dense>
                  {listSet.items
                    .filter(item => item.category === category)
                    .map((item, itemIndex, arr) => (
                      <React.Fragment key={`${listSet.id}-${item.name}-${item.category}-${itemIndex}`}> 
                        <ListItem sx={{
                          py: 0.8,
                          backgroundColor: 'background.paper',
                          mb: 0.5,
                          borderRadius: '6px',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          '&:hover': { backgroundColor: (theme) => theme.palette.action.selected }
                        }}>
                          <ListItemIcon sx={{minWidth: 'auto', mr: 1.5}}>
                            <Checkbox
                              edge="start"
                              checked={!!item.checked} // Ensure boolean value
                              onChange={() => handleToggleItem(listSet.id, item.name, item.category)}
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
          </Paper>
        );
      })}
    </Container>
  );
};

export default AllShoppingListsPage; 