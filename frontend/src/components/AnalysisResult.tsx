import React, { useState } from 'react';
import {
  Shield,
  DollarSign,
  Volume2,
  MapPin,
  Clock,
  ChevronRight,
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

  const tabs = [
    { id: 'overview',  label: 'Overview',  icon: Home },
    { id: 'crime',     label: 'Safety',    icon: Shield },
    { id: 'cost',      label: 'Cost',      icon: DollarSign },
    { id: 'noise',     label: 'Noise',     icon: Volume2 },
    { id: 'amenities', label: 'Lifestyle', icon: Building },
    { id: 'commute',   label: 'Commute',   icon: Clock },
  ];

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

          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <nav className="flex gap-2 overflow-x-auto scrollbar-hide">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    relative flex-shrink-0 flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-200
                    ${isActive
                      ? 'bg-blue-600 text-white shadow-lg scale-105'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
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
