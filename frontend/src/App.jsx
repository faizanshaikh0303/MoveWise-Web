import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore.ts';
import { wakeUpBackend } from '@/utils/wakeBackend.ts';

// Pages
import LandingPage from '@/pages/LandingPage';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import ProfileSetup from '@/pages/ProfileSetup';
import ProfileSettings from '@/pages/ProfileSettings';
import LocationInput from '@/pages/LocationInput';
import AnalysisDetailPage from './pages/AnalysisDetailPage';

// Components
import ProtectedRoute from '@/components/ProtectedRoute';
import BackendStatusIndicator from '@/components/BackendStatusIndicator';

function App() {
  const fetchUser = useAuthStore((state) => state.fetchUser);

  useEffect(() => {
    // Wake up backend immediately on app load
    wakeUpBackend();
    
    // Check if user is logged in on mount
    fetchUser();
  }, [fetchUser]);

  return (
    <>
      {/* Backend Status Indicator */}
      <BackendStatusIndicator />
      
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute requiresProfile>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile-setup"
            element={
              <ProtectedRoute>
                <ProfileSetup />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile-settings"
            element={
              <ProtectedRoute>
                <ProfileSettings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/new-analysis"
            element={
              <ProtectedRoute requiresProfile>
                <LocationInput />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analysis/:id"
            element={
              <ProtectedRoute requiresProfile>
                <AnalysisDetailPage />
              </ProtectedRoute>
            }
          />

          {/* Catch all - redirect to landing page */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
