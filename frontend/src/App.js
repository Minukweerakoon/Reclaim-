import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Header from './components/Header';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

// Mobile detection hook
const useMobileDetection = () => {
  const [isMobile, setIsMobile] = React.useState(false);
  
  React.useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const mobile = /mobile|android|iphone|ipad|windows phone/.test(userAgent);
      setIsMobile(mobile);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  return isMobile;
};

const AppContent = () => {
  const { isAuthenticated } = useAuth();
  const isMobile = useMobileDetection();

  return (
    <div style={{
      ...styles.app,
      ...(isMobile ? styles.mobileApp : {})
    }}>
      {isAuthenticated ? (
        <>
          <Header />
          <Dashboard />
        </>
      ) : (
        <Login />
      )}
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const styles = {
  app: {
    minHeight: '100vh',
    backgroundColor: '#f3f4f6',
  },
  mobileApp: {
    fontSize: '14px',
  },
};

export default App;