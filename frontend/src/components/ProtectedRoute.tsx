import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useAnalysisStore } from '@/stores/analysisStore';

const ANALYSIS_LIMIT = Number(import.meta.env.VITE_ANALYSIS_LIMIT) || 20;

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiresProfile?: boolean;
  requiresAnalysisSlot?: boolean;
}

const ProtectedRoute = ({ children, requiresProfile = false, requiresAnalysisSlot = false }: ProtectedRouteProps) => {
  const { isAuthenticated, user } = useAuthStore();
  const { analyses, fetched } = useAnalysisStore();
  const [hydrated, setHydrated] = useState(() => useAuthStore.persist.hasHydrated());

  useEffect(() => {
    if (!hydrated) {
      const unsub = useAuthStore.persist.onFinishHydration(() => setHydrated(true));
      return unsub;
    }
  }, [hydrated]);

  if (!hydrated) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (requiresProfile && !user?.profile_setup_complete) {
    return <Navigate to="/profile-setup" replace />;
  }

  if (requiresAnalysisSlot && fetched && analyses.length >= ANALYSIS_LIMIT) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
