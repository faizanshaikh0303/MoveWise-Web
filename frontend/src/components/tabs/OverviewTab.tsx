import React from 'react';
import { motion } from 'framer-motion';
import { 
  Shield,
  DollarSign,
  Volume2,
  MapPin,
  Car,
  CheckCircle,
  XCircle,
  Lightbulb,
  TrendingUp,
  TrendingDown
} from 'lucide-react';

const OverviewTab = ({ analysis }) => {
  // Extract key data
  const crimeData = analysis.crime_data?.comparison || {};
  const costData = analysis.cost_data?.comparison || {};
  const noiseData = analysis.noise_data?.comparison || {};
  const amenitiesData = analysis.amenities_data || {};
  const commuteData = analysis.commute_data || {};

  // Calculate changes
  const safetyChange = crimeData.score_difference || 0;
  const costChange = costData.score_difference || 0;
  const noiseChange = noiseData.score_difference || 0;
  const amenitiesCount = amenitiesData.destination?.total_count || 0;

  // Create visual metrics
  const metrics = [
    {
      icon: Shield,
      label: 'Safety',
      score: analysis.safety_score || 0,
      change: safetyChange,
      description: crimeData.is_safer ? 'Safer area' : 'Similar safety',
      isGood: safetyChange >= 0,
      color: safetyChange >= 0 ? 'green' : 'red'
    },
    {
      icon: DollarSign,
      label: 'Affordability',
      score: analysis.affordability_score || 0,
      change: costChange,
      description: costData.is_more_expensive === false ? 'More affordable' : 'More expensive',
      isGood: costChange >= 0,
      color: costChange >= 0 ? 'green' : 'red'
    },
    {
      icon: Volume2,
      label: 'Environment',
      score: analysis.environment_score || 0,
      change: noiseChange,
      description: noiseData.is_quieter ? 'Quieter area' : 'Similar noise',
      isGood: noiseChange >= 0,
      color: noiseChange >= 0 ? 'green' : 'red'
    },
    {
      icon: MapPin,
      label: 'Lifestyle',
      score: analysis.lifestyle_score || 0,
      change: 0,
      description: `${amenitiesCount} nearby amenities`,
      isGood: amenitiesCount > 30,
      color: amenitiesCount > 30 ? 'green' : 'gray'
    }
  ];

  const getScoreColor = (score) => {
    if (score >= 80) return { bg: 'bg-green-50', border: 'border-green-300', text: 'text-green-600' };
    if (score >= 60) return { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-600' };
    if (score >= 40) return { bg: 'bg-yellow-50', border: 'border-yellow-300', text: 'text-yellow-600' };
    return { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-600' };
  };

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200"
      >
        <div className="flex items-start space-x-3">
          <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
            <Lightbulb className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Move Summary</h3>
            <p className="text-gray-700 leading-relaxed line-clamp-3">
              {analysis.overview_summary || 'Your comprehensive location analysis is ready. Explore the tabs to see detailed insights.'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Visual Score Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, idx) => {
          const Icon = metric.icon;
          const colors = getScoreColor(metric.score);

          return (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className={`${colors.bg} ${colors.border} border-2 rounded-xl p-5`}
            >
              {/* Icon & Status */}
              <div className="flex items-center justify-between mb-3">
                <Icon className={`h-6 w-6 ${colors.text}`} />
                {metric.isGood ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-gray-400" />
                )}
              </div>

              {/* Label */}
              <div className="font-semibold text-gray-900 mb-1">{metric.label}</div>

              {/* Score */}
              <div className={`text-2xl font-bold ${colors.text} mb-2`}>
                {Math.round(metric.score)}
                <span className="text-sm text-gray-500">/100</span>
              </div>

              {/* Description */}
              <div className="text-xs text-gray-600">{metric.description}</div>

              {/* Change Indicator */}
              {metric.change !== 0 && (
                <div className="mt-2 flex items-center text-xs">
                  {metric.change > 0 ? (
                    <>
                      <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                      <span className="text-green-600">+{metric.change.toFixed(0)} pts</span>
                    </>
                  ) : (
                    <>
                      <TrendingDown className="h-3 w-3 text-red-500 mr-1" />
                      <span className="text-red-600">{metric.change.toFixed(0)} pts</span>
                    </>
                  )}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Quick Facts Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Commute */}
        {commuteData.duration_minutes && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl p-5 shadow-sm border border-gray-200"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <Car className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <div className="text-sm text-gray-600">Commute Time</div>
                <div className="text-xl font-bold text-gray-900">
                  {commuteData.duration_minutes} min
                </div>
                <div className="text-xs text-gray-500 capitalize">by {commuteData.method || 'driving'}</div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Monthly Cost */}
        {costData.monthly_difference !== undefined && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-white rounded-xl p-5 shadow-sm border border-gray-200"
          >
            <div className="flex items-center space-x-3">
              <div className={`w-10 h-10 ${costData.monthly_difference > 0 ? 'bg-red-100' : 'bg-green-100'} rounded-full flex items-center justify-center`}>
                <DollarSign className={`h-5 w-5 ${costData.monthly_difference > 0 ? 'text-red-600' : 'text-green-600'}`} />
              </div>
              <div>
                <div className="text-sm text-gray-600">Monthly Cost</div>
                <div className={`text-xl font-bold ${costData.monthly_difference > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {costData.monthly_difference > 0 ? '+' : ''}
                  ${Math.abs(costData.monthly_difference || 0).toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">vs current</div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Key Changes - Compact List */}
      {analysis.lifestyle_changes && analysis.lifestyle_changes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-4">What to Expect</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {analysis.lifestyle_changes.slice(0, 6).map((change, idx) => (
              <div key={idx} className="flex items-start space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-gray-700">{change}</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* AI Insights - Compact */}
      {analysis.ai_insights && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-5 border-2 border-purple-200"
        >
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
              <Lightbulb className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-bold text-gray-900 mb-2">Bottom Line</h4>
              <p className="text-sm text-gray-700 leading-relaxed line-clamp-4">
                {analysis.ai_insights}
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default OverviewTab;
