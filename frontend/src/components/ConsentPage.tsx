import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsentModal from './ConsentModal';

// A simple wrapper page that shows the ConsentModal in an always-open state
// so that it can be displayed at the /consent route defined in App.tsx.
const ConsentPage: React.FC = () => {
  const navigate = useNavigate();
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);

  const handleClose = () => {
    // Close the modal by navigating back to the previous page
    navigate(-1);
  };

  const handleScrolled = () => {
    setHasScrolledToBottom(true);
  };

  return (
    <ConsentModal
      open={true}
      onClose={handleClose}
      onScrolled={handleScrolled}
      hasScrolledToBottom={hasScrolledToBottom}
    />
  );
};

export default ConsentPage; 