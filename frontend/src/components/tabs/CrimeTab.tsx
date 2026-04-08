import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertCircle,
  CheckCircle,
  Moon,
  Sun,
  Briefcase
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// ── Helpers ────────────────────────────────────────────────────────────────

/** Format "02-2024" → "Feb '24" */
function formatMonth(key: string): string {
  const [mm, yyyy] = key.split('-');
  const date = new Date(Number(yyyy), Number(mm) - 1);
  return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
}

/** Sum all values in a month-keyed rate dict */
function sumRates(dict: Record<string, number> = {}): number {
  return Object.values(dict).reduce((a, b) => a + b, 0);
}

/** Build sorted month keys union across any number of rate dicts */
function mergedMonths(...dicts: (Record<string, number> | undefined)[]): string[] {
  const keys = new Set<string>();
  for (const d of dicts) if (d) Object.keys(d).forEach(k => keys.add(k));
  return [...keys].sort();
}

// ── Component ──────────────────────────────────────────────────────────────

const CrimeTab = ({ data }) => {
  const [selectedLocation, setSelectedLocation] = useState('destination');

  const current     = data?.current     || {};
  const destination = data?.destination || {};
  const comparison  = data?.comparison  || {};

  const cMonthly = current.monthly     || {};
  const dMonthly = destination.monthly || {};

  // ── Chart 1: grouped bar chart — offense type × 3-month total, curr vs dest ──
  const offenseBarData = [
    {
      name: 'Violent',
      current:     sumRates(cMonthly.violent),
      destination: sumRates(dMonthly.violent),
    },
    {
      name: 'Property',
      current:     sumRates(cMonthly.property),
      destination: sumRates(dMonthly.property),
    },
    {
      name: 'Burglary',
      current:     sumRates(cMonthly.burglary),
      destination: sumRates(dMonthly.burglary),
    },
    {
      name: 'Larceny',
      current:     sumRates(cMonthly.larceny),
      destination: sumRates(dMonthly.larceny),
    },
  ];

  const hasOffenseData = offenseBarData.some(d => d.current > 0 || d.destination > 0);

  // ── Chart 2: line chart — total crime rate per month, curr vs dest ──────────
  const months = mergedMonths(cMonthly.violent, cMonthly.property, dMonthly.violent, dMonthly.property);

  const monthlyLineData = months.map(m => ({
    month: formatMonth(m),
    current:     Number(((cMonthly.violent?.[m] ?? 0) + (cMonthly.property?.[m] ?? 0)).toFixed(1)),
    destination: Number(((dMonthly.violent?.[m] ?? 0) + (dMonthly.property?.[m] ?? 0)).toFixed(1)),
  }));

  const hasMonthlyData = monthlyLineData.length > 0;

  // ── Hourly line chart (existing) ────────────────────────────────────────────
  const hourlyData = (selectedLocation === 'current' ? current : destination)
    .temporal_analysis?.hourly_distribution
    ?.map((count: number, hour: number) => ({
      hour: hour === 0 ? '12AM' : hour < 12 ? `${hour}AM` : hour === 12 ? '12PM' : `${hour - 12}PM`,
      crimes: count,
    })) || [];

  // ── Safety score styling ────────────────────────────────────────────────────
  const safetyScore  = destination.safety_score || 0;
  const scoreColor   = safetyScore >= 70 ? 'text-green-600' : safetyScore >= 50 ? 'text-yellow-600' : 'text-red-600';
  const scoreBgColor = safetyScore >= 70 ? 'bg-green-50'   : safetyScore >= 50 ? 'bg-yellow-50'   : 'bg-red-50';

  const tooltipStyle = { backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' };

  return (
    <div className="space-y-6">

      {/* ── Header Stats ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`${scoreBgColor} rounded-xl p-6 border-2 ${
            safetyScore >= 70 ? 'border-green-200' : safetyScore >= 50 ? 'border-yellow-200' : 'border-red-200'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Safety Score</span>
            <Shield className={`h-5 w-5 ${scoreColor}`} />
          </div>
          <div className={`text-4xl font-bold ${scoreColor}`}>
            {Math.round(safetyScore)}
            <span className="text-xl text-gray-400">/100</span>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {destination.data_source || 'Crime analysis'}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Total Crimes (30 days)</span>
            <AlertCircle className="h-5 w-5 text-gray-400" />
          </div>
          <div className="text-4xl font-bold text-gray-900">
            {destination.total_crimes || 0}
          </div>
          <div className="mt-2 flex items-center text-sm">
            {comparison.crime_change_percent > 0 ? (
              <>
                <TrendingUp className="h-4 w-4 text-red-500 mr-1" />
                <span className="text-red-600">+{Math.round(comparison.crime_change_percent)}% more</span>
              </>
            ) : comparison.crime_change_percent < 0 ? (
              <>
                <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-green-600">{Math.abs(Math.round(comparison.crime_change_percent))}% safer</span>
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
            <span className="text-sm font-medium text-gray-600">Daily Average</span>
            <Clock className="h-5 w-5 text-gray-400" />
          </div>
          <div className="text-4xl font-bold text-gray-900">
            {destination.daily_average?.toFixed(1) || 0}
          </div>
          <div className="mt-2 text-sm text-gray-600">crimes per day</div>
        </motion.div>
      </div>

      {/* ── Chart 1: Offense Type Bar Chart (3-month totals, per 100k) ───────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-1">
          Crime by Offense Type
        </h3>
        <p className="text-xs text-gray-500 mb-4">
          3-month total rate per 100k population — current vs destination
        </p>
        {hasOffenseData ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={offenseBarData} barGap={4} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `${v}`} width={40} />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value: number) => [`${value.toFixed(1)}/100k`, undefined]}
              />
              <Legend />
              <Bar dataKey="current"     fill="#3b82f6" name="Current"     radius={[6, 6, 0, 0]} />
              <Bar dataKey="destination" fill="#10b981" name="Destination" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[280px] flex items-center justify-center text-gray-400 text-sm">
            Monthly breakdown not available — using aggregated data
          </div>
        )}
      </motion.div>

      {/* ── Chart 2: Monthly Total Crime Rate Line Chart ─────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-1">
          Monthly Crime Rate Trend
        </h3>
        <p className="text-xs text-gray-500 mb-4">
          Total (violent + property) rate per 100k — month by month
        </p>
        {hasMonthlyData ? (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={monthlyLineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `${v}`} width={40} />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value: number) => [`${value.toFixed(1)}/100k`, undefined]}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="current"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Current"
              />
              <Line
                type="monotone"
                dataKey="destination"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Destination"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[240px] flex items-center justify-center text-gray-400 text-sm">
            Monthly trend data not available
          </div>
        )}
      </motion.div>

      {/* ── Time-wise Analysis (unchanged) ───────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-6">
        {/* Hourly distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900">Crime by Time of Day</h3>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1.5"
            >
              <option value="destination">Destination</option>
              <option value="current">Current</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip contentStyle={tooltipStyle} />
              <Line type="monotone" dataKey="crimes" stroke="#ef4444" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-gray-600">
            Peak hours:{' '}
            <span className="font-semibold">
              {(selectedLocation === 'current' ? current : destination)
                .temporal_analysis?.peak_hours?.slice(0, 3).join(', ') || 'N/A'}
            </span>
          </div>
        </motion.div>

        {/* Schedule safety */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-4">Your Schedule Safety</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Moon className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="font-medium text-gray-900">Sleep Hours</div>
                  <div className="text-sm text-gray-600">10 PM – 6 AM</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-gray-900">
                  {destination.temporal_analysis?.crimes_during_sleep_hours || 0}
                </div>
                <div className="text-xs text-gray-500">crimes</div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Briefcase className="h-5 w-5 text-yellow-600" />
                <div>
                  <div className="font-medium text-gray-900">Work Hours</div>
                  <div className="text-sm text-gray-600">9 AM – 5 PM</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-gray-900">
                  {destination.temporal_analysis?.crimes_during_work_hours || 0}
                </div>
                <div className="text-xs text-gray-500">crimes</div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Sun className="h-5 w-5 text-green-600" />
                <div>
                  <div className="font-medium text-gray-900">Commute Times</div>
                  <div className="text-sm text-gray-600">7–9 AM, 5–7 PM</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-gray-900">
                  {destination.temporal_analysis?.crimes_during_commute || 0}
                </div>
                <div className="text-xs text-gray-500">crimes</div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* ── Safety Assessment ─────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className={`${comparison.is_safer ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'} rounded-xl p-6 border-2`}
      >
        <div className="flex items-start space-x-3">
          {comparison.is_safer ? (
            <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-0.5" />
          )}
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">Safety Assessment</h4>
            <p className="text-gray-700">{comparison.recommendation}</p>
          </div>
        </div>
      </motion.div>

    </div>
  );
};

export default CrimeTab;
