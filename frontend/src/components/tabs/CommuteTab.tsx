import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Car, Bike, Train, FootprintsIcon, MapPin } from 'lucide-react';

interface CommuteData {
  duration_minutes?: number;
  distance?: string;
  method?: string;
  description?: string;
  alternatives?: {
    driving?: { duration_minutes?: number; distance?: string };
    transit?: { duration_minutes?: number; distance?: string };
    bicycling?: { duration_minutes?: number; distance?: string };
    walking?: { duration_minutes?: number; distance?: string };
  };
}

interface CommuteTabProps {
  data: CommuteData;
}

const CommuteTab: React.FC<CommuteTabProps> = ({ data }) => {
  const isWorkFromHome = data?.method === 'none' || data?.duration_minutes === 0;

  const duration = data?.duration_minutes || 0;
  const distance = data?.distance || '0 km';
  const method = data?.method || 'driving';
  const description = data?.description || 'No commute data available';
  const alternatives = data?.alternatives || {};

  const getMethodIcon = (method: string) => {
    const icons: Record<string, any> = {
      'driving': Car,
      'bicycling': Bike,
      'transit': Train,
      'walking': FootprintsIcon
    };
    return icons[method] || Car;
  };

  const getMethodColor = (method: string) => {
    const colors: Record<string, string> = {
      'driving': 'blue',
      'bicycling': 'green',
      'transit': 'purple',
      'walking': 'orange'
    };
    return colors[method] || 'blue';
  };

  const MethodIcon = getMethodIcon(method);
  const methodColor = getMethodColor(method);

  const getCommuteQuality = (minutes: number) => {
    if (minutes < 20) return { label: 'Excellent', color: 'green', score: 95 };
    if (minutes < 30) return { label: 'Good', color: 'blue', score: 80 };
    if (minutes < 45) return { label: 'Fair', color: 'yellow', score: 65 };
    if (minutes < 60) return { label: 'Long', color: 'orange', score: 50 };
    return { label: 'Very Long', color: 'red', score: 30 };
  };

  const quality = getCommuteQuality(duration);

  // Calculate CO2 estimates
  const getCO2Estimate = () => {
    const distanceKm = parseFloat(distance) || 0;
    switch(method) {
      case 'driving':
        return (distanceKm * 0.12 * 22).toFixed(1);
      case 'transit':
        return (distanceKm * 0.04 * 22).toFixed(1);
      case 'bicycling':
      case 'walking':
        return '0';
      default:
        return 'N/A';
    }
  };

  // Get real times from alternatives, fallback to estimates if not available
  const getAlternativeTime = (mode: string) => {
    const alt = alternatives[mode as keyof typeof alternatives];
    if (alt?.duration_minutes) {
      return alt.duration_minutes;
    }
    
    // Fallback estimates if API didn't return data
    const estimates: Record<string, number> = {
      'driving': Math.round(duration * 0.7),
      'transit': Math.round(duration * 1.3),
      'bicycling': Math.round(duration * 2.5),
      'walking': Math.round(duration * 4)
    };
    return estimates[mode] || duration;
  };

  if (isWorkFromHome) {
    return (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-green-50 border-2 border-green-200 rounded-xl p-8 text-center"
        >
          <div className="text-5xl mb-4">🏠</div>
          <h3 className="text-2xl font-bold text-green-700 mb-2">You Work from Home</h3>
          <p className="text-green-600 text-lg">No commute needed — enjoy the extra time and savings!</p>
        </motion.div>

        <div className="grid grid-cols-3 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 text-center"
          >
            <div className="text-3xl font-bold text-green-600">0 min</div>
            <div className="text-sm text-gray-500 mt-1">Daily commute</div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 text-center"
          >
            <div className="text-3xl font-bold text-green-600">$0</div>
            <div className="text-sm text-gray-500 mt-1">Monthly commute cost</div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 text-center"
          >
            <div className="text-3xl font-bold text-green-600">0 kg</div>
            <div className="text-sm text-gray-500 mt-1">Monthly CO₂ emissions</div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-3">Annual Savings (vs. average 30-min commute)</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Time saved per year</div>
              <div className="text-2xl font-bold text-blue-600">220 hrs</div>
              <div className="text-xs text-gray-500 mt-1">~9 full days</div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">CO₂ avoided per year</div>
              <div className="text-2xl font-bold text-green-600">~600 kg</div>
              <div className="text-xs text-gray-500 mt-1">vs. average driver</div>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`bg-${quality.color}-50 border-${quality.color}-200 rounded-xl p-6 border-2`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Commute Quality</span>
            <Clock className={`h-5 w-5 text-${quality.color}-600`} />
          </div>
          <div className={`text-4xl font-bold text-${quality.color}-600`}>
            {quality.label}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Score: {quality.score}/100
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Duration</span>
            <MethodIcon className={`h-5 w-5 text-${methodColor}-500`} />
          </div>
          <div className="text-4xl font-bold text-gray-900">
            {duration}
            <span className="text-xl text-gray-400"> min</span>
          </div>
          <div className="mt-2 text-sm text-gray-600 capitalize">
            By {method}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Distance</span>
            <MapPin className="h-5 w-5 text-gray-400" />
          </div>
          <div className="text-4xl font-bold text-gray-900">
            {distance}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            one-way
          </div>
        </motion.div>
      </div>

      {/* Commute Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-4">Daily Commute Impact</h3>
        
        <div className="grid grid-cols-2 gap-6">
          {/* Time Investment */}
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Daily Time</div>
              <div className="text-2xl font-bold text-blue-600">
                {duration * 2} min
              </div>
              <div className="text-xs text-gray-500 mt-1">Round trip</div>
            </div>
            
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Weekly Time</div>
              <div className="text-2xl font-bold text-purple-600">
                {Math.round((duration * 2 * 5) / 60)} hrs
              </div>
              <div className="text-xs text-gray-500 mt-1">5 work days</div>
            </div>

            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Annual Time</div>
              <div className="text-2xl font-bold text-orange-600">
                {Math.round((duration * 2 * 220) / 60)} hrs
              </div>
              <div className="text-xs text-gray-500 mt-1">~220 work days</div>
            </div>
          </div>

          {/* Environmental Impact */}
          <div className="space-y-4">
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Monthly CO₂</div>
              <div className="text-2xl font-bold text-green-600">
                {getCO2Estimate()} kg
              </div>
              <div className="text-xs text-gray-500 mt-1">Estimated emissions</div>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Commute Cost</div>
              <div className="text-2xl font-bold text-gray-600">
                {method === 'driving' ? `$${(parseFloat(distance) * 0.5 * 22).toFixed(0)}` : 
                 method === 'transit' ? '$150' : '$0'}
              </div>
              <div className="text-xs text-gray-500 mt-1">Estimated monthly</div>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Flexibility</div>
              <div className="text-lg font-bold text-yellow-600">
                {method === 'driving' ? 'High' : 
                 method === 'transit' ? 'Medium' : 'Low'}
              </div>
              <div className="text-xs text-gray-500 mt-1">Schedule flexibility</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Alternative Commute Methods - USING REAL GOOGLE API DATA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-4">Alternative Commute Options</h3>
        
        <div className="grid grid-cols-4 gap-3">
          {[
            { method: 'driving', icon: Car, color: 'blue' },
            { method: 'transit', icon: Train, color: 'purple' },
            { method: 'bicycling', icon: Bike, color: 'green' },
            { method: 'walking', icon: FootprintsIcon, color: 'orange' }
          ].map(({ method: m, icon: Icon, color }) => {
            const time = getAlternativeTime(m);
            const isCurrentMethod = m === method;
            
            return (
              <div
                key={m}
                className={`p-4 rounded-lg border-2 transition-all ${
                  isCurrentMethod
                    ? `bg-${color}-50 border-${color}-500` 
                    : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                }`}
              >
                <Icon className={`h-6 w-6 mx-auto mb-2 ${
                  isCurrentMethod ? `text-${color}-600` : 'text-gray-400'
                }`} />
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-900 capitalize mb-1">{m}</div>
                  <div className={`text-lg font-bold ${
                    isCurrentMethod ? `text-${color}-600` : 'text-gray-600'
                  }`}>
                    {time ? `${time} min` : 'N/A'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Show note if using estimates */}
        {(!alternatives.driving?.duration_minutes && !alternatives.transit?.duration_minutes) && (
          <div className="mt-3 text-xs text-gray-500 text-center">
            Times are estimated based on your {method} commute
          </div>
        )}
      </motion.div>

      {/* Description */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-blue-50 border-blue-200 rounded-xl p-6 border-2"
      >
        <p className="text-gray-700">{description}</p>
        
        {duration > 45 && (
          <div className="mt-4 p-3 bg-white rounded-lg border border-blue-300">
            <p className="text-sm text-gray-700">
              💡 <strong>Tip:</strong> Consider remote work options or flexible schedules to reduce commute frequency.
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default CommuteTab;
