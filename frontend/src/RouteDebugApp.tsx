import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useParams } from 'react-router-dom';

// Simple test component
const TestUserProfile: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const location = useLocation();
  
  return (
    <div style={{ padding: '20px', border: '2px solid green', margin: '20px' }}>
      <h1>🎉 SUCCESS! Route Working!</h1>
      <p><strong>URL:</strong> {location.pathname}</p>
      <p><strong>User ID:</strong> {userId}</p>
      <p><strong>Params:</strong> {JSON.stringify(useParams())}</p>
    </div>
  );
};

// Minimal working app
function RouteDebugApp() {
  return (
    <Router>
      <div style={{ padding: '20px', backgroundColor: '#f0f0f0' }}>
        <h1>Route Debug App</h1>
        <p>Testing basic routing functionality</p>
        
        <div style={{ margin: '20px 0', padding: '10px', backgroundColor: 'yellow' }}>
          <strong>Test these URLs:</strong>
          <ul>
            <li>http://localhost:3000/test/123</li>
            <li>http://localhost:3000/admin/users/KURQYMQ6</li>
            <li>http://localhost:3000/anything-else (should show 404)</li>
          </ul>
        </div>
      </div>
      
      <Routes>
        <Route path="/test/:userId" element={<TestUserProfile />} />
        <Route path="/admin/users/:userId" element={<TestUserProfile />} />
        <Route path="*" element={<div style={{padding: '20px', color: 'red'}}>❌ 404 - No route matched</div>} />
      </Routes>
    </Router>
  );
}

export default RouteDebugApp; 