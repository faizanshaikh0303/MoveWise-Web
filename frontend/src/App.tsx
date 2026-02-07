import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from './stores/authStore';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProfileSetup from './pages/ProfileSetup';
import LocationInput from './pages/LocationInput';
import AnalysisReport from './pages/AnalysisReport';

// Components
import ProtectedRoute from './components/ProtectedRoute';
import ProfileCheckRoute from './components/ProfileCheckRoute';

function App() {
  const fetchUser = useAuthStore((state) => state.fetchUser);

  useEffect(() => {
    // Check if user is logged in on mount
    fetchUser();
  }, [fetchUser]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public route */}
        <Route path="/" element={<Login />} />

        {/* Profile Setup - Protected but doesn't require profile */}
        <Route
          path="/profile-setup"
          element={
            <ProtectedRoute>
              <ProfileSetup />
            </ProtectedRoute>
          }
        />

        {/* Protected routes that REQUIRE profile completion */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <ProfileCheckRoute>
                <Dashboard />
              </ProfileCheckRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/new-analysis"
          element={
            <ProtectedRoute>
              <ProfileCheckRoute>
                <LocationInput />
              </ProfileCheckRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/analysis/:id"
          element={
            <ProtectedRoute>
              <ProfileCheckRoute>
                <AnalysisReport />
              </ProfileCheckRoute>
            </ProtectedRoute>
          }
        />

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
