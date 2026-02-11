import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { wakeUpBackend } from '@/utils/wakeBackend';

// Pages (we'll create these next)
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import ProfileSetup from '@/pages/ProfileSetup';
import LocationInput from '@/pages/LocationInput';
import AnalysisReport from '@/pages/AnalysisReport';

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
        {/* Public route */}
        <Route path="/" element={<Login />} />

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
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
          path="/new-analysis"
          element={
            <ProtectedRoute>
              <LocationInput />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analysis/:id"
          element={
            <ProtectedRoute>
              <AnalysisReport />
            </ProtectedRoute>
          }
        />

        {/* Catch all - redirect to dashboard if authenticated, login otherwise */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
    </>
  );
}

export default App;
