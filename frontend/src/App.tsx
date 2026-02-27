import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import ValidationHub from './pages/ValidationHub';
import Chat from './pages/Chat';
import ChatbotPage from './pages/ChatbotPage';
import IntentSelectionPage from './pages/IntentSelectionPage';
import Monitor from './pages/Monitor';
import ErrorBoundary from './components/ErrorBoundary';
import { ProtectedRoute } from './components/ProtectedRoute';
import ReclaimApp from './reclaim/ReclaimApp';
import './index.css';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Navigate to="/reclaim" replace />} />


          {/* Group project Reclaim UI — manages its own auth flow internally */}
          <Route path="/reclaim/*" element={<ReclaimApp />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<IntentSelectionPage />} />
            <Route path="chatbot" element={<ChatbotPage />} />
            <Route path="validation" element={<ValidationHub />} />
            <Route path="results" element={<ValidationHub />} />
            <Route path="chat" element={<Chat />} />
            <Route path="monitor" element={<Monitor />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
