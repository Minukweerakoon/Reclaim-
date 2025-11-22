import React from 'react';
import { useAuth } from '../context/AuthContext';

const Header = () => {
  const { user, logout, isSecurity } = useAuth();

  return (
    <header style={styles.header}>
      <div style={styles.logo}>
        <h1 style={styles.title}>Campus Theft Prevention</h1>
        <p style={styles.subtitle}>Real-time Device Security</p>
      </div>
      
      <div style={styles.userInfo}>
        {user && (
          <>
            <span style={styles.welcome}>
              {user.username} ({user.role})
            </span>
            <button 
              onClick={logout}
              style={styles.logoutButton}
            >
              Logout
            </button>
          </>
        )}
      </div>
    </header>
  );
};

const styles = {
  header: {
    backgroundColor: '#1f2937',
    color: 'white',
    padding: '1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    flexWrap: 'wrap',
  },
  logo: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    minWidth: '200px',
  },
  title: {
    fontSize: 'clamp(1.2rem, 4vw, 1.5rem)',
    fontWeight: 'bold',
    margin: 0,
  },
  subtitle: {
    fontSize: 'clamp(0.7rem, 3vw, 0.9rem)',
    opacity: 0.8,
    margin: 0,
    marginTop: '0.2rem',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  welcome: {
    fontSize: '0.9rem',
    textAlign: 'right',
  },
  logoutButton: {
    backgroundColor: '#ef4444',
    color: 'white',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    whiteSpace: 'nowrap',
  },
};

// Mobile styles
const mobileStyles = {
  header: {
    padding: '0.75rem',
  },
  title: {
    fontSize: '1.1rem',
  },
  subtitle: {
    fontSize: '0.7rem',
  },
  welcome: {
    fontSize: '0.8rem',
  },
  logoutButton: {
    padding: '0.4rem 0.8rem',
    fontSize: '0.8rem',
  },
};

export default Header;