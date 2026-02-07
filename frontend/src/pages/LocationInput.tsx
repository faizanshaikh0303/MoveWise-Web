import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analysisAPI } from '../services/api';
import AddressAutocomplete from '../components/AddressAutocomplete';

const LocationInput = () => {
  const navigate = useNavigate();
  const [currentAddress, setCurrentAddress] = useState('');
  const [destinationAddress, setDestinationAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!currentAddress.trim() || !destinationAddress.trim()) {
      setError('Please enter both addresses');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const analysis = await analysisAPI.create({
        current_address: currentAddress,
        destination_address: destinationAddress,
      });

      // Redirect to the analysis report
      navigate(`/analysis/${analysis.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate analysis. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">New Analysis</h1>
            <p className="text-sm text-gray-600">Compare two locations</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
              <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Location Comparison</h2>
            <p className="text-gray-600">Enter your current and destination addresses to get a comprehensive analysis</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Current Address */}
            <AddressAutocomplete
              label="Current Location"
              value={currentAddress}
              onChange={setCurrentAddress}
              placeholder="e.g., San Francisco, CA"
              icon="current"
              disabled={loading}
            />
            <p className="mt-2 text-sm text-gray-500">Enter city and state (e.g., "Austin, TX" or "123 Main St, Seattle, WA")</p>

            {/* Arrow Divider */}
            <div className="flex items-center justify-center py-2">
              <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
            </div>

            {/* Destination Address */}
            <AddressAutocomplete
              label="Destination Location"
              value={destinationAddress}
              onChange={setDestinationAddress}
              placeholder="e.g., Austin, TX"
              icon="destination"
              disabled={loading}
            />
            <p className="mt-2 text-sm text-gray-500">Where are you considering moving to?</p>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex gap-3">
                <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-blue-900">
                  <p className="font-medium mb-1">What you'll get:</p>
                  <ul className="space-y-1 text-blue-800">
                    <li>• Crime rate comparison</li>
                    <li>• Cost of living breakdown</li>
                    <li>• Nearby amenities (1-mile radius)</li>
                    <li>• Noise level analysis</li>
                    <li>• AI-powered insights</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !currentAddress || !destinationAddress}
              className="w-full btn btn-primary py-4 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Generating Analysis...
                </>
              ) : (
                <>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  Generate Analysis
                </>
              )}
            </button>

            {loading && (
              <p className="text-center text-sm text-gray-600">
                This may take 5-10 seconds while we gather data from multiple sources...
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default LocationInput;
