import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoadingSpinner } from './LoadingSpinner';

export function ProtectedRoute({ children }) {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background-dark">
                <LoadingSpinner center label="Authenticating..." />
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/reclaim" replace state={{ from: location.pathname }} />;
    }

    return children;
}
