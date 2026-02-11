import { useState, useEffect } from 'react';

export const BackendStatusIndicator = () => {
  const [status, setStatus] = useState<'checking' | 'awake' | 'sleeping' | 'hidden'>('checking');
  const [showIndicator, setShowIndicator] = useState(true);

  useEffect(() => {
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const startTime = Date.now();
      const response = await fetch(`${import.meta.env.VITE_API_URL}/health`, {
        method: 'GET',
      });

      const duration = Date.now() - startTime;

      if (response.ok) {
        if (duration > 5000) {
          // Took more than 5 seconds - was sleeping
          setStatus('awake');
          // Hide after 3 seconds
          setTimeout(() => setShowIndicator(false), 3000);
        } else {
          // Quick response - already awake
          setStatus('hidden');
          setShowIndicator(false);
        }
      } else {
        setStatus('sleeping');
      }
    } catch (error) {
      setStatus('sleeping');
    }
  };

  if (!showIndicator || status === 'hidden') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-fade-in">
      <div className="bg-white/90 backdrop-blur-lg rounded-xl shadow-lg p-4 border border-white/20 flex items-center gap-3 max-w-xs">
        {status === 'checking' && (
          <>
            <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Waking up server...</p>
              <p className="text-xs text-gray-600">This may take 30-60 seconds</p>
            </div>
          </>
        )}
        
        {status === 'awake' && (
          <>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Server is ready! ✓</p>
              <p className="text-xs text-gray-600">You can now use the app</p>
            </div>
          </>
        )}
        
        {status === 'sleeping' && (
          <>
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Server unavailable</p>
              <p className="text-xs text-gray-600">Please try again in a moment</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default BackendStatusIndicator;
