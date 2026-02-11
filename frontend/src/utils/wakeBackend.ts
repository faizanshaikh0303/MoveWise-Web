// Wake up backend service to prevent cold starts
export const wakeUpBackend = async () => {
  try {
    const startTime = Date.now();
    console.log('🚀 Waking up backend...');
    
    const response = await fetch(`${import.meta.env.VITE_API_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const duration = Date.now() - startTime;
    
    if (response.ok) {
      console.log(`✅ Backend awake! (${duration}ms)`);
      return true;
    } else {
      console.warn('⚠️ Backend responded with error');
      return false;
    }
  } catch (error) {
    console.error('❌ Failed to wake backend:', error);
    return false;
  }
};

// Auto-wake backend when module loads
if (import.meta.env.VITE_API_URL) {
  // Wake up immediately
  wakeUpBackend();
  
  // Set up periodic pings every 10 minutes to keep it alive
  setInterval(() => {
    wakeUpBackend();
  }, 15 * 60 * 1000); // 10 minutes
}

export default wakeUpBackend;