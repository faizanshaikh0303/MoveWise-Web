import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { analysisAPI } from '../services/api';
import type { Analysis } from '../types';

type TabType = 'overview' | 'environment' | 'safety' | 'amenities' | 'cost' | 'actions';

const AnalysisReport = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      fetchAnalysis(parseInt(id));
    }
  }, [id]);

  const fetchAnalysis = async (analysisId: number) => {
    try {
      const data = await analysisAPI.getById(analysisId);
      setAnalysis(data);
    } catch (err) {
      setError('Failed to load analysis. Please try again.');
      console.error('Failed to fetch analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-gray-600 mt-4">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Analysis not found'}</p>
          <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'environment', label: 'Environment' },
    { id: 'safety', label: 'Safety' },
    { id: 'amenities', label: 'Amenities' },
    { id: 'cost', label: 'Cost' },
    { id: 'actions', label: 'Action Steps' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Lifestyle Analysis Report</h1>
          <p className="text-gray-600">Comprehensive comparison of your potential move</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-sm font-medium whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'text-primary border-b-2 border-primary bg-primary/5'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Lifestyle Changes Summary */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-start gap-3 mb-4">
                <svg className="w-6 h-6 text-primary mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Lifestyle Changes Summary</h2>
                  <p className="text-gray-600 text-sm">Key changes you can expect from this move</p>
                </div>
              </div>
              
              {analysis.lifestyle_changes && analysis.lifestyle_changes.length > 0 ? (
                <div className="space-y-3">
                  {analysis.lifestyle_changes.map((change, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                      <svg className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <p className="text-gray-800">{change.replace('✓', '').trim()}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No lifestyle changes data available</p>
              )}
            </div>

            {/* Commute & Cost Overview - Side by Side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Commute Impact */}
              {analysis.commute_data && Object.keys(analysis.commute_data).length > 0 && (
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
                    </svg>
                    <h3 className="text-lg font-semibold text-gray-900">Commute Impact</h3>
                  </div>
                  
                  <div className="space-y-3">
                    {analysis.commute_data.duration_minutes && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Duration:</span>
                        <span className="text-lg font-semibold text-gray-900">{analysis.commute_data.duration_minutes} minutes</span>
                      </div>
                    )}
                    {analysis.commute_data.method && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Method:</span>
                        <span className="text-gray-900 font-medium capitalize">{analysis.commute_data.method}</span>
                      </div>
                    )}
                    {analysis.commute_data.description && (
                      <p className="text-sm text-gray-600 mt-4 p-3 bg-blue-50 rounded-lg">
                        {analysis.commute_data.description}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Cost Overview */}
              {analysis.cost_data && (
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 className="text-lg font-semibold text-gray-900">Cost Overview</h3>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Current:</span>
                      <span className="text-lg font-semibold text-gray-900">${analysis.cost_data.current_cost.toLocaleString()}/month (avg)</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">New:</span>
                      <span className="text-lg font-semibold text-gray-900">${analysis.cost_data.destination_cost.toLocaleString()}/month (avg)</span>
                    </div>
                    <div className="flex justify-between items-center pt-3 border-t">
                      <span className="text-gray-600">Change:</span>
                      <span className={`text-lg font-semibold flex items-center gap-1 ${
                        analysis.cost_data.change_percentage > 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {analysis.cost_data.change_percentage > 0 ? '↑' : '↓'}
                        {Math.abs(analysis.cost_data.change_percentage)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* AI Insights */}
            {analysis.ai_insights && (
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl shadow-sm p-6 border border-purple-100">
                <div className="flex items-start gap-3 mb-4">
                  <svg className="w-6 h-6 text-purple-600 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">AI-Powered Insights</h3>
                    <p className="text-sm text-gray-600">Personalized analysis based on your profile</p>
                  </div>
                </div>
                <div className="prose prose-sm max-w-none text-gray-700">
                  {analysis.ai_insights.split('\n\n').map((paragraph, index) => (
                    <p key={index} className="mb-4 leading-relaxed">{paragraph}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Environment Tab */}
        {activeTab === 'environment' && analysis.noise_data && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-start gap-3 mb-6">
              <svg className="w-6 h-6 text-primary mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15.536a5 5 0 001.414 1.414m2.828-9.9a9 9 0 012.828 2.828" />
              </svg>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Noise Level Analysis</h2>
                <p className="text-gray-600 text-sm">How the noise environment compares</p>
              </div>
            </div>

            {/* Comparison Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Current Location */}
              <div className="p-6 bg-blue-50 rounded-xl">
                <h3 className="text-sm font-medium text-gray-600 mb-3">Current Location</h3>
                <p className="text-2xl font-bold text-gray-900 mb-2">{analysis.noise_data.current_noise_level}</p>
                <p className="text-sm text-gray-600 mb-3">{analysis.noise_data.current_description}</p>
                {analysis.noise_data.current_indicators && analysis.noise_data.current_indicators.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {analysis.noise_data.current_indicators.map((indicator, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {indicator}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* New Location */}
              <div className="p-6 bg-green-50 rounded-xl">
                <h3 className="text-sm font-medium text-gray-600 mb-3">New Location</h3>
                <p className="text-2xl font-bold text-gray-900 mb-2">{analysis.noise_data.destination_noise_level}</p>
                <p className="text-sm text-gray-600 mb-3">{analysis.noise_data.destination_description}</p>
                {analysis.noise_data.destination_indicators && analysis.noise_data.destination_indicators.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {analysis.noise_data.destination_indicators.map((indicator, index) => (
                      <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        {indicator}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Impact Analysis */}
            <div className={`p-4 rounded-lg ${
              analysis.noise_data.impact === 'Positive' ? 'bg-green-50 border border-green-200' :
              analysis.noise_data.impact === 'Concerning' ? 'bg-red-50 border border-red-200' :
              'bg-blue-50 border border-blue-200'
            }`}>
              <p className="text-gray-800">
                <span className="font-semibold">{analysis.noise_data.impact}</span> - {analysis.noise_data.analysis}
              </p>
            </div>

            {/* Bottom Warning */}
            <div className="mt-6 p-4 bg-purple-100 rounded-xl border border-purple-200">
              <p className="text-purple-900 text-center">
                Ready to make your move? Remember to verify all information with official sources and visit the new location before making your final decision.
              </p>
            </div>
          </div>
        )}

        {/* Safety Tab */}
        {activeTab === 'safety' && analysis.crime_data && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-start gap-3 mb-6">
              <svg className="w-6 h-6 text-primary mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Crime Rate Comparison</h2>
                <p className="text-gray-600 text-sm">Safety statistics for both locations</p>
              </div>
            </div>

            {/* Crime Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="p-6 bg-blue-50 rounded-xl text-center">
                <p className="text-sm text-gray-600 mb-2">Current Location</p>
                <p className="text-3xl font-bold text-gray-900 mb-1">{analysis.crime_data.current_crime_rate.toLocaleString()}</p>
                <p className="text-xs text-gray-500">crimes per 100k people</p>
              </div>

              <div className="p-6 bg-gradient-to-br from-purple-100 to-blue-100 rounded-xl text-center flex flex-col justify-center">
                <p className="text-sm font-semibold text-purple-900 mb-2">Comparison</p>
                <p className="text-lg font-bold text-purple-900">{analysis.crime_data.comparison}</p>
              </div>

              <div className="p-6 bg-green-50 rounded-xl text-center">
                <p className="text-sm text-gray-600 mb-2">New Location</p>
                <p className="text-3xl font-bold text-gray-900 mb-1">{analysis.crime_data.destination_crime_rate.toLocaleString()}</p>
                <p className="text-xs text-gray-500">crimes per 100k people</p>
              </div>
            </div>

            {/* Data Source */}
            {analysis.crime_data.data_source && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Data Source:</span> {analysis.crime_data.data_source}
                </p>
              </div>
            )}

            {/* Safety Tips */}
            <div className="mt-6 p-4 bg-yellow-50 rounded-xl border border-yellow-200">
              <div className="flex gap-3">
                <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-yellow-900">Safety Recommendation</p>
                  <p className="text-sm text-yellow-800 mt-1">
                    Research specific neighborhoods within your destination city, as crime rates can vary significantly by area. 
                    Consider visiting at different times of day to get a feel for the neighborhood.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Amenities Tab */}
        {activeTab === 'amenities' && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            {analysis.amenities_data ? (
              <>
                <div className="flex items-start gap-3 mb-6">
                  <svg className="w-6 h-6 text-primary mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Nearby Amenities</h2>
                    <p className="text-gray-600 text-sm">Compare available facilities and services</p>
                  </div>
                </div>

                {/* Comparison Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Current Location */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Location</h3>
                    <div className="space-y-3">
                      {Object.entries(analysis.amenities_data.current_amenities).map(([amenity, count]) => (
                        <div key={amenity} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="text-gray-700 capitalize">{amenity}</span>
                          </div>
                          <span className="font-semibold text-gray-900">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* New Location */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">New Location</h3>
                    <div className="space-y-3">
                      {Object.entries(analysis.amenities_data.destination_amenities).map(([amenity, count]) => {
                        const currentCount = analysis.amenities_data!.current_amenities[amenity] || 0;
                        const isMore = count > currentCount;
                        
                        return (
                          <div key={amenity} className={`flex items-center justify-between p-3 rounded-lg ${
                            isMore ? 'bg-green-50' : count < currentCount ? 'bg-red-50' : 'bg-gray-50'
                          }`}>
                            <div className="flex items-center gap-2">
                              <svg className={`w-4 h-4 ${
                                isMore ? 'text-green-600' : count < currentCount ? 'text-red-600' : 'text-gray-600'
                              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <span className="text-gray-700 capitalize">{amenity}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-900">{count}</span>
                              {count !== currentCount && (
                                <span className={`text-xs ${isMore ? 'text-green-600' : 'text-red-600'}`}>
                                  ({isMore ? '+' : ''}{count - currentCount})
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Summary */}
                {analysis.amenities_data.comparison_text && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
                    <p className="text-blue-900">{analysis.amenities_data.comparison_text}</p>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500">No amenities data available for this analysis.</p>
              </div>
            )}
          </div>
        )}

        {/* Cost Tab */}
        {activeTab === 'cost' && (
          <div className="space-y-6">
            {analysis.cost_data ? (
              <>
                {/* Cost Overview */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <div className="flex items-start gap-3 mb-6">
                    <svg className="w-6 h-6 text-primary mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">Cost of Living</h2>
                      <p className="text-gray-600 text-sm">Financial impact of your move</p>
                    </div>
                  </div>

                  {/* Cost Comparison Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div className="p-6 bg-blue-50 rounded-xl">
                      <p className="text-sm text-gray-600 mb-2">Current</p>
                      <p className="text-3xl font-bold text-gray-900">${analysis.cost_data.current_cost.toLocaleString()}/month (avg)</p>
                    </div>

                    <div className="p-6 bg-purple-50 rounded-xl">
                      <p className="text-sm text-gray-600 mb-2">New Location</p>
                      <p className="text-3xl font-bold text-gray-900">${analysis.cost_data.destination_cost.toLocaleString()}/month (avg)</p>
                    </div>

                    <div className={`p-6 rounded-xl ${
                      analysis.cost_data.change_percentage > 0 ? 'bg-red-50' : 'bg-green-50'
                    }`}>
                      <p className="text-sm text-gray-600 mb-2">Change</p>
                      <p className={`text-3xl font-bold flex items-center gap-2 ${
                        analysis.cost_data.change_percentage > 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {analysis.cost_data.change_percentage > 0 ? '↑' : '↓'}
                        {Math.abs(analysis.cost_data.change_percentage)}%
                      </p>
                    </div>
                  </div>

                  {/* Financial Tip */}
                  {analysis.cost_data.tip && (
                    <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
                      <p className="text-sm">
                        <span className="font-semibold text-yellow-900">Financial Planning Tip:</span>
                        <span className="text-yellow-800"> {analysis.cost_data.tip}</span>
                      </p>
                    </div>
                  )}
                </div>

                {/* Cost Breakdown */}
                {analysis.cost_data.current_breakdown && analysis.cost_data.destination_breakdown && (
                  <div className="bg-white rounded-xl shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Cost Breakdown</h3>
                    
                    <div className="space-y-4">
                      {Object.keys(analysis.cost_data.current_breakdown).map((category) => {
                        const currentAmount = analysis.cost_data!.current_breakdown![category];
                        const newAmount = analysis.cost_data!.destination_breakdown![category];
                        const difference = newAmount - currentAmount;
                        const percentChange = ((difference / currentAmount) * 100);
                        
                        return (
                          <div key={category} className="border-b border-gray-100 pb-4 last:border-0">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-medium text-gray-900 capitalize">{category}</span>
                              <div className="flex items-center gap-4">
                                <span className="text-gray-600">${currentAmount.toFixed(0)}</span>
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                </svg>
                                <span className="text-gray-900 font-semibold">${newAmount.toFixed(0)}</span>
                                <span className={`text-sm ${difference > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                  ({difference > 0 ? '+' : ''}{percentChange.toFixed(1)}%)
                                </span>
                              </div>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${difference > 0 ? 'bg-red-500' : 'bg-green-500'}`}
                                style={{ width: `${Math.min(Math.abs(percentChange), 100)}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="text-center py-12">
                  <p className="text-gray-500">No cost data available for this analysis.</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Steps Tab */}
        {activeTab === 'actions' && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-start gap-3 mb-6">
              <svg className="w-6 h-6 text-primary mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Next Steps</h2>
                <p className="text-gray-600 text-sm">Recommended actions for your move</p>
              </div>
            </div>

            <div className="space-y-4">
              {[
                {
                  title: 'Visit the New Location',
                  description: 'Spend a few days in the destination city to explore neighborhoods, try local amenities, and get a feel for the area.',
                  priority: 'high'
                },
                {
                  title: 'Research Neighborhoods',
                  description: 'Drill down into specific neighborhoods within the destination city. Crime rates and amenities can vary significantly by area.',
                  priority: 'high'
                },
                {
                  title: 'Calculate Moving Costs',
                  description: 'Get quotes from moving companies, factor in deposits, and plan for any overlap in rent or mortgage payments.',
                  priority: 'medium'
                },
                {
                  title: 'Update Your Budget',
                  description: 'Create a detailed budget based on the cost of living differences. Account for changes in housing, transportation, and daily expenses.',
                  priority: 'medium'
                },
                {
                  title: 'Test Your Commute',
                  description: 'If possible, do a trial commute during rush hour to understand the real-time impact on your daily routine.',
                  priority: 'medium'
                },
                {
                  title: 'Connect with Locals',
                  description: 'Join local community groups, attend events, or connect with residents online to get insider perspectives on the area.',
                  priority: 'low'
                },
              ].map((step, index) => (
                <div key={index} className="flex gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold text-white ${
                      step.priority === 'high' ? 'bg-red-500' :
                      step.priority === 'medium' ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}>
                      {index + 1}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{step.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        step.priority === 'high' ? 'bg-red-100 text-red-700' :
                        step.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {step.priority} priority
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Final CTA */}
            <div className="mt-8 p-6 bg-gradient-to-r from-purple-100 to-blue-100 rounded-xl border border-purple-200">
              <h3 className="text-lg font-semibold text-purple-900 mb-2">Ready to Make Your Move?</h3>
              <p className="text-purple-800 mb-4">
                Remember to verify all information with official sources and visit the new location before making your final decision. 
                This analysis is meant to guide your research, not replace it.
              </p>
              <button
                onClick={() => navigate('/new-analysis')}
                className="btn btn-primary"
              >
                Create Another Analysis
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisReport;
