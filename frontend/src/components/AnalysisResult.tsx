import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  DollarSign, 
  Volume2, 
  MapPin, 
  Clock,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  Home,
  Building
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import OverviewTab from './tabs/OverviewTab';
import CrimeTab from './tabs/CrimeTab';
import CostTab from './tabs/CostTab';
import NoiseTab from './tabs/NoiseTab';
import AmenitiesTab from './tabs/AmenitiesTab';
import CommuteTab from './tabs/CommuteTab';
import type { Analysis } from '../types';

interface AnalysisResultProps {
  analysis: Analysis;
  onBack: () => void;
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({ analysis, onBack }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [showScoreAnimation, setShowScoreAnimation] = useState(true);

  useEffect(() => {
    // Trigger score animation on mount
    const timer = setTimeout(() => setShowScoreAnimation(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const getGrade = (score: number) => {
    if (score >= 90) return { grade: 'A+', color: 'text-green-600', bgColor: 'bg-green-50', borderColor: 'border-green-200' };
    if (score >= 80) return { grade: 'A', color: 'text-green-500', bgColor: 'bg-green-50', borderColor: 'border-green-200' };
    if (score >= 70) return { grade: 'B', color: 'text-blue-500', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' };
    if (score >= 60) return { grade: 'C', color: 'text-yellow-500', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-200' };
    if (score >= 50) return { grade: 'D', color: 'text-orange-500', bgColor: 'bg-orange-50', borderColor: 'border-orange-200' };
    return { grade: 'F', color: 'text-red-500', bgColor: 'bg-red-50', borderColor: 'border-red-200' };
  };

  const gradeInfo = getGrade(analysis.overall_score || 0);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'crime', label: 'Safety', icon: Shield },
    { id: 'cost', label: 'Cost', icon: DollarSign },
    { id: 'noise', label: 'Noise', icon: Volume2 },
    { id: 'amenities', label: 'Lifestyle', icon: Building },
    { id: 'commute', label: 'Commute', icon: Clock }
  ];

  const scores = {
    safety: analysis.safety_score || 0,
    affordability: analysis.affordability_score || 0,
    environment: analysis.environment_score || 0,
    lifestyle: analysis.lifestyle_score || 0,
    convenience: analysis.convenience_score || 0
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white shadow-sm border-b border-gray-200"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={onBack}
                className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-2 transition-colors"
              >
                <ChevronRight className="h-4 w-4 rotate-180 mr-1" />
                Back to analyses
              </button>
              <div className="flex items-center space-x-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    {analysis.current_address}
                  </h1>
                  <div className="flex items-center text-gray-600 mt-1">
                    <MapPin className="h-4 w-4 mr-2" />
                    <span className="text-sm">to {analysis.destination_address}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Overall Score Card */}
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className={`${gradeInfo.bgColor} ${gradeInfo.borderColor} border-2 rounded-2xl p-6 min-w-[200px]`}
            >
              <div className="text-center">
                <div className="text-sm font-medium text-gray-600 mb-2">Overall Score</div>
                <AnimatePresence>
                  {showScoreAnimation ? (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1, rotate: 360 }}
                      exit={{ scale: 0 }}
                      transition={{ type: "spring", stiffness: 260, damping: 20 }}
                      className={`text-5xl font-bold ${gradeInfo.color}`}
                    >
                      {Math.round(analysis.overall_score || 0)}
                    </motion.div>
                  ) : (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-baseline justify-center"
                    >
                      <span className={`text-5xl font-bold ${gradeInfo.color}`}>
                        {Math.round(analysis.overall_score || 0)}
                      </span>
                      <span className="text-2xl text-gray-400 ml-1">/100</span>
                    </motion.div>
                  )}
                </AnimatePresence>
                <div className={`text-xl font-semibold ${gradeInfo.color} mt-2`}>
                  Grade: {gradeInfo.grade}
                </div>
              </div>
            </motion.div>
          </div>

          {/* Score Breakdown Mini Cards */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="grid grid-cols-5 gap-3 mt-6"
          >
            {Object.entries(scores).map(([key, value], idx) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + idx * 0.1 }}
                className="bg-white rounded-lg p-3 shadow-sm border border-gray-200"
              >
                <div className="text-xs text-gray-500 capitalize mb-1">{key}</div>
                <div className="flex items-baseline">
                  <span className="text-2xl font-bold text-gray-900">{Math.round(value)}</span>
                  <span className="text-sm text-gray-400 ml-1">/100</span>
                </div>
                <div className="mt-2 bg-gray-200 rounded-full h-1.5">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${value}%` }}
                    transition={{ delay: 0.5 + idx * 0.1, duration: 0.8 }}
                    className={`h-1.5 rounded-full ${
                      value >= 70 ? 'bg-green-500' : value >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                  />
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    relative flex items-center py-4 px-1 text-sm font-medium transition-colors
                    ${activeTab === tab.id
                      ? 'text-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                    }
                  `}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.label}
                  {activeTab === tab.id && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && <OverviewTab analysis={analysis} />}
            {activeTab === 'crime' && <CrimeTab data={analysis.crime_data || {}} />}
            {activeTab === 'cost' && <CostTab data={analysis.cost_data || {}} />}
            {activeTab === 'noise' && <NoiseTab data={analysis.noise_data || {}} />}
            {activeTab === 'amenities' && <AmenitiesTab data={analysis.amenities_data || {}} />}
            {activeTab === 'commute' && <CommuteTab data={analysis.commute_data || {}} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AnalysisResult;
