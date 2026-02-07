import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { profileAPI } from '../services/api';

interface ProfileCheckRouteProps {
  children: React.ReactNode;
}

const ProfileCheckRoute = ({ children }: ProfileCheckRouteProps) => {
  const location = useLocation();
  const [hasProfile, setHasProfile] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Don't check if we're already on profile-setup
    if (location.pathname === '/profile-setup') {
      console.log('ProfileCheckRoute: Already on profile-setup, skipping check');
      setHasProfile(true); // Pretend profile exists to allow access
      setLoading(false);
      return;
    }
    
    checkProfile();
  }, [location.pathname]);

  const checkProfile = async () => {
    console.log('ProfileCheckRoute: Checking profile...');
    try {
      const profile = await profileAPI.get();
      console.log('ProfileCheckRoute: Profile found:', profile);
      setHasProfile(profile !== null);
    } catch (error) {
      console.log('ProfileCheckRoute: No profile found (error)');
      setHasProfile(false);
    } finally {
      setLoading(false);
    }
  };

  console.log('ProfileCheckRoute render:', { hasProfile, loading, path: location.pathname });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-gray-600 mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  if (hasProfile === false) {
    console.log('ProfileCheckRoute: Redirecting to profile-setup');
    return <Navigate to="/profile-setup" replace />;
  }

  console.log('ProfileCheckRoute: Rendering children');
  return <>{children}</>;
};

export default ProfileCheckRoute;
