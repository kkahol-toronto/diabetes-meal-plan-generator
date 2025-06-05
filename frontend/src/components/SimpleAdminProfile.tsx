import React from 'react';
import { useParams } from 'react-router-dom';

const SimpleAdminProfile: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  
  console.log('SimpleAdminProfile loaded with userId:', userId);
  
  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', margin: '20px' }}>
      <h1>🎉 SUCCESS!</h1>
      <h2>Route is working!</h2>
      <p><strong>User ID:</strong> {userId}</p>
      <p>If you can see this, the routing issue is fixed!</p>
    </div>
  );
};

export default SimpleAdminProfile; 