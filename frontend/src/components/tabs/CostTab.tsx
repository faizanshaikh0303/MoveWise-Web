import React from 'react';
import { motion } from 'framer-motion';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  Home,
  Zap,
  ShoppingCart,
  Car,
  Heart,
  Film,
  MoreHorizontal
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const CostTab = ({ data }) => {
  const current = data?.current || {};
  const destination = data?.destination || {};
  const comparison = data?.comparison || {};

  const monthlyDiff = comparison.monthly_difference || 0;
  const percentChange = comparison.percent_change || 0;
  const isMoreExpensive = comparison.is_more_expensive;

  // Expense breakdown data
  const expenseCategories = [
    { 
      name: 'Housing', 
      current: current.housing?.monthly_rent || 0, 
      destination: destination.housing?.monthly_rent || 0,
      icon: Home,
      color: '#3b82f6'
    },
    { 
      name: 'Utilities', 
      current: current.expenses?.utilities || 0, 
      destination: destination.expenses?.utilities || 0,
      icon: Zap,
      color: '#f59e0b'
    },
    { 
      name: 'Groceries', 
      current: current.expenses?.groceries || 0, 
      destination: destination.expenses?.groceries || 0,
      icon: ShoppingCart,
      color: '#10b981'
    },
    { 
      name: 'Transportation', 
      current: current.expenses?.transportation || 0, 
      destination: destination.expenses?.transportation || 0,
      icon: Car,
      color: '#ef4444'
    },
    { 
      name: 'Healthcare', 
      current: current.expenses?.healthcare || 0, 
      destination: destination.expenses?.healthcare || 0,
      icon: Heart,
      color: '#8b5cf6'
    },
    { 
      name: 'Entertainment', 
      current: current.expenses?.entertainment || 0, 
      destination: destination.expenses?.entertainment || 0,
      icon: Film,
      color: '#ec4899'
    },
    { 
      name: 'Miscellaneous', 
      current: current.expenses?.miscellaneous || 0, 
      destination: destination.expenses?.miscellaneous || 0,
      icon: MoreHorizontal,
      color: '#6b7280'
    }
  ];

  // Pie chart data for destination breakdown
  const pieData = expenseCategories.map(cat => ({
    name: cat.name,
    value: cat.destination,
    color: cat.color
  }));

  const affordabilityScore = destination.affordability_score || 0;
  const scoreColor = affordabilityScore >= 70 ? 'text-green-600' : affordabilityScore >= 50 ? 'text-yellow-600' : 'text-red-600';
  const scoreBgColor = affordabilityScore >= 70 ? 'bg-green-50' : affordabilityScore >= 50 ? 'bg-yellow-50' : 'bg-red-50';

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`${scoreBgColor} rounded-xl p-6 border-2 ${
            affordabilityScore >= 70 ? 'border-green-200' : affordabilityScore >= 50 ? 'border-yellow-200' : 'border-red-200'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Affordability Score</span>
            <DollarSign className={`h-5 w-5 ${scoreColor}`} />
          </div>
          <div className={`text-4xl font-bold ${scoreColor}`}>
            {Math.round(affordabilityScore)}
            <span className="text-xl text-gray-400">/100</span>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {destination.data_source || 'Cost estimate'}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Monthly Cost</span>
          </div>
          <div className="text-4xl font-bold text-gray-900">
            ${destination.total_monthly?.toLocaleString() || 0}
          </div>
          <div className="mt-2 flex items-center text-sm">
            {monthlyDiff > 0 ? (
              <>
                <TrendingUp className="h-4 w-4 text-red-500 mr-1" />
                <span className="text-red-600">+${Math.abs(monthlyDiff).toLocaleString()}/mo</span>
              </>
            ) : monthlyDiff < 0 ? (
              <>
                <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-green-600">-${Math.abs(monthlyDiff).toLocaleString()}/mo</span>
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
            <span className="text-sm font-medium text-gray-600">Annual Cost</span>
          </div>
          <div className="text-4xl font-bold text-gray-900">
            ${destination.total_annual?.toLocaleString() || 0}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Cost Index: {destination.cost_index || 1.0}
          </div>
        </motion.div>
      </div>

      {/* Expense Comparison Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-4">Monthly Expense Comparison</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={expenseCategories}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={(value) => `$${value}`} />
            <Tooltip 
              formatter={(value) => `$${value.toLocaleString()}`}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            <Legend />
            <Bar dataKey="current" fill="#3b82f6" name="Current Location" radius={[8, 8, 0, 0]} />
            <Bar dataKey="destination" fill="#10b981" name="New Location" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Two column layout */}
      <div className="grid grid-cols-2 gap-6">
        {/* Expense Breakdown Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-4">Detailed Breakdown</h3>
          <div className="space-y-3">
            {expenseCategories.map((category, idx) => {
              const Icon = category.icon;
              const diff = category.destination - category.current;
              const percentDiff = category.current > 0 ? ((diff / category.current) * 100).toFixed(1) : 0;
              
              return (
                <motion.div
                  key={category.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + idx * 0.05 }}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${category.color}20` }}
                    >
                      <Icon className="h-5 w-5" style={{ color: category.color }} />
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{category.name}</div>
                      <div className="text-sm text-gray-500">
                        ${category.destination.toLocaleString()}/mo
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${
                      diff > 0 ? 'text-red-600' : diff < 0 ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {diff > 0 ? '+' : ''}{diff !== 0 ? `$${Math.abs(diff).toLocaleString()}` : 'Same'}
                    </div>
                    {diff !== 0 && (
                      <div className="text-xs text-gray-500">
                        {percentDiff > 0 ? '+' : ''}{percentDiff}%
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Pie Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-4">Cost Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${destination.total_monthly?.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Total Monthly Budget</div>
          </div>
        </motion.div>
      </div>

      {/* Recommendation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className={`${isMoreExpensive ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'} rounded-xl p-6 border-2`}
      >
        <div className="flex items-start space-x-3">
          {isMoreExpensive ? (
            <TrendingUp className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-0.5" />
          ) : (
            <TrendingDown className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
          )}
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">Cost Assessment</h4>
            <p className="text-gray-700">{comparison.recommendation}</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default CostTab;
