import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { analysisAPI } from '../services/api';
import AnalysisResult from '../components/AnalysisResult';
import type { Analysis } from '../types';

const POLL_INTERVAL_MS = 4000;

const AnalysisDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const fetchAnalysis = async () => {
    if (!id) return;
    try {
      const data = await analysisAPI.getById(parseInt(id));
      setAnalysis(data);
      setError(null);
      // Stop polling once the job finishes (either way)
      if (data.status === 'completed' || data.status === 'failed') {
        stopPolling();
      }
    } catch (err) {
      console.error('Failed to fetch analysis:', err);
      setError('Failed to load analysis. Please try again.');
      stopPolling();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysis();
    return stopPolling;
  }, [id]);

  // Start polling when analysis is pending/processing
  useEffect(() => {
    if (!analysis) return;
    if (analysis.status === 'pending' || analysis.status === 'processing') {
      if (!pollRef.current) {
        pollRef.current = setInterval(fetchAnalysis, POLL_INTERVAL_MS);
      }
    } else {
      stopPolling();
    }
  }, [analysis?.status]);

  const handleBack = () => {
    stopPolling();
    navigate('/dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Failed to Load Analysis</h3>
          <p className="text-gray-600 mb-6">{error || 'Analysis not found'}</p>
          <button
            onClick={handleBack}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (analysis.status === 'pending' || analysis.status === 'processing') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
            <div className="w-14 h-14 border-4 border-amber-400/30 border-t-amber-500 rounded-full animate-spin"></div>
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">Generating Your Report</h3>
          <p className="text-gray-600 mb-2">
            {analysis.current_address} → {analysis.destination_address}
          </p>
          <p className="text-sm text-gray-500 mb-8">
            We're gathering crime data, cost of living, amenities, noise levels, and AI insights in the background. This takes about 15–30 seconds.
          </p>
          <div className="flex flex-col gap-3 items-center">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></div>
              Checking every few seconds for updates...
            </div>
            <button
              onClick={handleBack}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              Go back to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (analysis.status === 'failed') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Analysis Failed</h3>
          <p className="text-gray-600 mb-6">Something went wrong while generating your report. Please try again.</p>
          <button
            onClick={handleBack}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <AnalysisResult analysis={analysis} onBack={handleBack} />;
};

export default AnalysisDetailPage;
