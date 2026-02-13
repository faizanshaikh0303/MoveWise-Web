import React from 'react';
import { motion } from 'framer-motion';
import { Volume2, Volume1, VolumeX, TrendingDown, TrendingUp } from 'lucide-react';

interface NoiseData {
  current?: {
    estimated_db?: number;
    noise_category?: string;
    noise_score?: number;
    road_breakdown?: Record<string, number>;
    dominant_noise_source?: string;
  };
  destination?: {
    estimated_db?: number;
    noise_category?: string;
    noise_score?: number;
    road_breakdown?: Record<string, number>;
    dominant_noise_source?: string;
    recommendations?: string[];
  };
  comparison?: {
    db_difference?: number;
    category_change?: string;
    is_quieter?: boolean;
    recommendation?: string;
    preference_match?: {
      is_good_match?: boolean;
    };
  };
}

interface NoiseTabProps {
  data: NoiseData;
}

const NoiseTab: React.FC<NoiseTabProps> = ({ data }) => {
  const current = data?.current || {};
  const destination = data?.destination || {};
  const comparison = data?.comparison || {};

  const getNoiseIcon = (db: number = 0) => {
    if (db < 45) return VolumeX;
    if (db < 65) return Volume1;
    return Volume2;
  };

  const getNoiseColor = (category: string = 'Moderate') => {
    const colors: Record<string, { text: string; bg: string; border: string }> = {
      'Very Quiet': { text: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
      'Quiet': { text: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
      'Moderate': { text: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
      'Noisy': { text: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
      'Very Noisy': { text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' }
    };
    return colors[category] || colors['Moderate'];
  };

  const destColors = getNoiseColor(destination.noise_category);
  const NoiseIcon = getNoiseIcon(destination.estimated_db);

  const noiseScore = destination.noise_score || 0;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`${destColors.bg} ${destColors.border} rounded-xl p-6 border-2`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Noise Score</span>
            <NoiseIcon className={`h-5 w-5 ${destColors.text}`} />
          </div>
          <div className={`text-4xl font-bold ${destColors.text}`}>
            {Math.round(noiseScore)}
            <span className="text-xl text-gray-400">/100</span>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {destination.noise_category || 'Moderate'}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Noise Level</span>
          </div>
          <div className="text-4xl font-bold text-gray-900">
            {destination.estimated_db?.toFixed(1) || 0} dB
          </div>
          <div className="mt-2 flex items-center text-sm">
            {(comparison.db_difference || 0) < 0 ? (
              <>
                <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-green-600">{Math.abs(comparison.db_difference || 0).toFixed(1)} dB quieter</span>
              </>
            ) : (comparison.db_difference || 0) > 0 ? (
              <>
                <TrendingUp className="h-4 w-4 text-red-500 mr-1" />
                <span className="text-red-600">+{(comparison.db_difference || 0).toFixed(1)} dB louder</span>
              </>
            ) : (
              <span className="text-gray-600">No change</span>
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Category Change</span>
          </div>
          <div className="text-xl font-bold text-gray-900">
            {comparison.category_change || 'No change'}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {comparison.is_quieter ? 'Quieter environment' : 'Similar noise'}
          </div>
        </motion.div>
      </div>

      {/* Visual Comparison */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-6">Noise Level Comparison</h3>
        
        <div className="space-y-6">
          {/* Current Location */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Current Location</span>
              <span className="text-sm font-bold text-gray-900">{current.estimated_db?.toFixed(1) || 0} dB</span>
            </div>
            <div className="relative h-8 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${((current.estimated_db || 0) / 100) * 100}%` }}
                transition={{ duration: 1, delay: 0.5 }}
                className={`h-full ${getNoiseColor(current.noise_category).bg} flex items-center justify-end pr-3`}
              >
                <span className="text-xs font-medium text-gray-700">{current.noise_category || 'Moderate'}</span>
              </motion.div>
            </div>
          </div>

          {/* Destination Location */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">New Location</span>
              <span className="text-sm font-bold text-gray-900">{destination.estimated_db?.toFixed(1) || 0} dB</span>
            </div>
            <div className="relative h-8 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${((destination.estimated_db || 0) / 100) * 100}%` }}
                transition={{ duration: 1, delay: 0.7 }}
                className={`h-full ${destColors.bg} flex items-center justify-end pr-3`}
              >
                <span className="text-xs font-medium text-gray-700">{destination.noise_category || 'Moderate'}</span>
              </motion.div>
            </div>
          </div>
        </div>

        {/* dB Scale Reference */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Noise Level Reference</h4>
          <div className="grid grid-cols-5 gap-2 text-xs">
            <div className="text-center p-2 bg-green-50 rounded">
              <div className="font-semibold text-green-700">20-40 dB</div>
              <div className="text-gray-600 mt-1">Whisper</div>
            </div>
            <div className="text-center p-2 bg-blue-50 rounded">
              <div className="font-semibold text-blue-700">40-55 dB</div>
              <div className="text-gray-600 mt-1">Library</div>
            </div>
            <div className="text-center p-2 bg-yellow-50 rounded">
              <div className="font-semibold text-yellow-700">55-70 dB</div>
              <div className="text-gray-600 mt-1">Normal Talk</div>
            </div>
            <div className="text-center p-2 bg-orange-50 rounded">
              <div className="font-semibold text-orange-700">70-85 dB</div>
              <div className="text-gray-600 mt-1">Traffic</div>
            </div>
            <div className="text-center p-2 bg-red-50 rounded">
              <div className="font-semibold text-red-700">85+ dB</div>
              <div className="text-gray-600 mt-1">Loud</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Road Breakdown */}
      <div className="grid grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-4">Current Location Sources</h3>
          <div className="space-y-3">
            {Object.entries(current.road_breakdown || {}).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700 capitalize">{type} roads</span>
                <span className="text-lg font-bold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Dominant source:</span>
              <span className="font-semibold text-gray-900 capitalize">{current.dominant_noise_source || 'Unknown'}</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-4">New Location Sources</h3>
          <div className="space-y-3">
            {Object.entries(destination.road_breakdown || {}).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700 capitalize">{type} roads</span>
                <span className="text-lg font-bold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Dominant source:</span>
              <span className="font-semibold text-gray-900 capitalize">{destination.dominant_noise_source || 'Unknown'}</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Recommendations */}
      {destination.recommendations && destination.recommendations.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-blue-50 border-blue-200 rounded-xl p-6 border-2"
        >
          <h4 className="font-semibold text-gray-900 mb-3">Recommendations</h4>
          <ul className="space-y-2">
            {destination.recommendations.map((rec, idx) => (
              <li key={idx} className="text-sm text-gray-700 flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-gray-50 border-gray-200 rounded-xl p-6 border-2"
        >
          <p className="text-gray-600 text-center">
            {comparison.is_quieter 
              ? "✅ This location is quieter than your current area."
              : "The noise level is similar to your current location."}
          </p>
        </motion.div>
      )}

      {/* Preference Match */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className={`${
          comparison.preference_match?.is_good_match 
            ? 'bg-green-50 border-green-200' 
            : 'bg-yellow-50 border-yellow-200'
        } rounded-xl p-6 border-2`}
      >
        <p className="text-gray-700">{comparison.recommendation || 'Noise analysis complete.'}</p>
      </motion.div>
    </div>
  );
};

export default NoiseTab;
