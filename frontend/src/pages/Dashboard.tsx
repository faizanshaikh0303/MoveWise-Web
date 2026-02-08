import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { analysisAPI } from '../services/api';
import type { AnalysisSummary } from '../types';

const Dashboard = () => {
  const navigate = useNavigate();
  const { logout, user } = useAuthStore();
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const fetchAnalyses = async () => {
    try {
      const data = await analysisAPI.getAll();
      setAnalyses(data);
    } catch (error) {
      console.error('Failed to fetch analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 relative overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      {/* Header with Glassmorphism */}
      <div className="relative bg-white/80 backdrop-blur-lg border-b border-white/20 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-primary to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">MoveWise</h1>
              <p className="text-sm text-gray-600">Welcome back, {user?.name || user?.email?.split('@')[0]}!</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/profile')}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-white/50 rounded-lg transition-all"
            >
              Profile
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-white/50 rounded-lg transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="relative max-w-7xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="mb-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-4xl font-bold text-gray-900 mb-2">Your Analyses</h2>
              <p className="text-lg text-gray-600">Compare locations and make informed decisions</p>
            </div>
            <button
              onClick={() => navigate('/new-analysis')}
              className="group px-6 py-3 bg-gradient-to-r from-primary to-blue-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
            >
              <svg className="w-5 h-5 group-hover:rotate-90 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Analysis
            </button>
          </div>

          {/* Stats Cards */}
          {!loading && analyses.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Total Analyses</p>
                    <p className="text-2xl font-bold text-gray-900">{analyses.length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Most Recent</p>
                    <p className="text-lg font-semibold text-gray-900">{formatDate(analyses[0].created_at)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Locations</p>
                    <p className="text-2xl font-bold text-gray-900">{analyses.length}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-block">
              <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
            </div>
            <p className="text-gray-600 mt-6 text-lg">Loading your analyses...</p>
          </div>
        )}

        {/* No Analyses State */}
        {!loading && analyses.length === 0 && (
          <div className="text-center py-20">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center shadow-xl">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">No analyses yet</h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Get started by creating your first location analysis. Compare cities, neighborhoods, and make informed moving decisions!
            </p>
            <button
              onClick={() => navigate('/new-analysis')}
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary to-blue-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Your First Analysis
            </button>
          </div>
        )}

        {/* Analyses Grid */}
        {!loading && analyses.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {analyses.map((analysis) => (
              <div
                key={analysis.id}
                className="group bg-white/80 backdrop-blur-lg rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden border border-white/20 hover:border-primary/20 cursor-pointer transform hover:scale-105"
                onClick={() => navigate(`/analysis/${analysis.id}`)}
              >
                {/* Card Header with Gradient */}
                <div className="h-2 bg-gradient-to-r from-primary via-blue-600 to-purple-600"></div>
                
                <div className="p-6">
                  {/* Icon and Date */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                      <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                      </svg>
                    </div>
                    <span className="text-xs font-medium text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                      {formatDate(analysis.created_at)}
                    </span>
                  </div>

                  {/* Locations */}
                  <div className="space-y-3 mb-4">
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-500 mb-1">From</p>
                        <p className="text-sm font-semibold text-gray-900 truncate">{analysis.current_address}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-center">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                    </div>

                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-500 mb-1">To</p>
                        <p className="text-sm font-semibold text-gray-900 truncate">{analysis.destination_address}</p>
                      </div>
                    </div>
                  </div>

                  {/* View Report Button */}
                  <button className="w-full py-3 bg-gradient-to-r from-primary to-blue-600 text-white rounded-xl font-medium group-hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2">
                    View Report
                    <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Floating Animation Styles */}
      <style>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          25% {
            transform: translate(20px, -50px) scale(1.1);
          }
          50% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          75% {
            transform: translate(50px, 50px) scale(1.05);
          }
        }
        
        .animate-blob {
          animation: blob 7s infinite;
        }
        
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
