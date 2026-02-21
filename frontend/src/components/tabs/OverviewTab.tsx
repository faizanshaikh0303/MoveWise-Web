import React from 'react';
import { motion } from 'framer-motion';
import {
  Shield, DollarSign, Volume2, MapPin, Clock,
  ArrowRight, TrendingUp, TrendingDown,
  CheckCircle, Lightbulb, Sparkles, ArrowUpRight, ArrowDownRight
} from 'lucide-react';

interface OverviewTabProps {
  analysis: any;
}

// Animated SVG circular progress ring
const ScoreRing = ({
  score,
  size = 80,
  strokeWidth = 7,
  delay = 0,
}: {
  score: number;
  size?: number;
  strokeWidth?: number;
  delay?: number;
}) => {
  const r = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * r;
  const progress = (score / 100) * circumference;

  const color =
    score >= 80 ? '#16a34a' :
    score >= 65 ? '#2563eb' :
    score >= 50 ? '#d97706' : '#dc2626';

  const trackColor =
    score >= 80 ? '#dcfce7' :
    score >= 65 ? '#dbeafe' :
    score >= 50 ? '#fef3c7' : '#fee2e2';

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" style={{ display: 'block' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={trackColor} strokeWidth={strokeWidth} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeLinecap="round"
          initial={{ strokeDasharray: `0 ${circumference}` }}
          animate={{ strokeDasharray: `${progress} ${circumference - progress}` }}
          transition={{ duration: 1.2, ease: 'easeOut', delay }}
        />
      </svg>
      <div
        className="absolute inset-0 flex items-center justify-center"
        style={{ color }}
      >
        <span className="text-lg font-bold">{Math.round(score)}</span>
      </div>
    </div>
  );
};

const OverviewTab: React.FC<OverviewTabProps> = ({ analysis }) => {
  const crimeData    = analysis.crime_data?.comparison   || {};
  const costData     = analysis.cost_data?.comparison    || {};
  const noiseData    = analysis.noise_data?.comparison   || {};
  const amenitiesData = analysis.amenities_data          || {};
  const commuteData  = analysis.commute_data             || {};

  const isWFH = commuteData.method === 'none' || commuteData.duration_minutes === 0;

  const overallScore = analysis.overall_score || 0;
  const grade =
    overallScore >= 90 ? 'A+' :
    overallScore >= 80 ? 'A'  :
    overallScore >= 70 ? 'B'  :
    overallScore >= 60 ? 'C'  :
    overallScore >= 50 ? 'D'  : 'F';

  const gradeColor =
    overallScore >= 80 ? 'text-emerald-400' :
    overallScore >= 65 ? 'text-blue-400'    :
    overallScore >= 50 ? 'text-yellow-400'  : 'text-red-400';

  const scoreCards = [
    {
      icon: Shield,
      label: 'Safety',
      score: analysis.safety_score || 0,
      description: crimeData.is_safer ? 'Safer than current' : 'Similar safety level',
      delay: 0.2,
    },
    {
      icon: DollarSign,
      label: 'Affordability',
      score: analysis.affordability_score || 0,
      description: costData.is_more_expensive === false ? 'More affordable' : 'Higher cost of living',
      delay: 0.3,
    },
    {
      icon: Volume2,
      label: 'Environment',
      score: analysis.environment_score || 0,
      description: noiseData.is_quieter ? 'Quieter environment' : 'Similar noise levels',
      delay: 0.4,
    },
    {
      icon: MapPin,
      label: 'Lifestyle',
      score: analysis.lifestyle_score || 0,
      description: `${amenitiesData.destination?.total_count || 0} nearby amenities`,
      delay: 0.5,
    },
    {
      icon: Clock,
      label: 'Convenience',
      score: analysis.convenience_score || 0,
      description: isWFH ? 'Work from home' : commuteData.duration_minutes ? `${commuteData.duration_minutes} min commute` : 'No commute data',
      delay: 0.6,
    },
  ];

  const highlights: { label: string; value: string; good: boolean; icon: any }[] = [];

  if (crimeData.crime_change_percent !== undefined) {
    const pct = Math.abs(Math.round(crimeData.crime_change_percent));
    highlights.push({
      label: 'Crime rate',
      value: crimeData.is_safer ? `${pct}% less crime` : `${pct}% more crime`,
      good: crimeData.is_safer,
      icon: Shield,
    });
  }

  if (costData.percent_change !== undefined) {
    const pct = Math.abs(Math.round(costData.percent_change));
    highlights.push({
      label: 'Cost of living',
      value: costData.is_more_expensive ? `${pct}% more expensive` : `${pct}% cheaper`,
      good: !costData.is_more_expensive,
      icon: DollarSign,
    });
  }

  if (noiseData.db_difference !== undefined) {
    const db = Math.abs(Math.round(noiseData.db_difference));
    highlights.push({
      label: 'Noise level',
      value: noiseData.is_quieter ? `${db} dB quieter` : `${db} dB louder`,
      good: noiseData.is_quieter,
      icon: Volume2,
    });
  }

  if (isWFH) {
    highlights.push({ label: 'Commute', value: 'Work from home', good: true, icon: Clock });
  } else if (commuteData.duration_minutes) {
    const mins = commuteData.duration_minutes;
    highlights.push({
      label: 'Commute',
      value: mins <= 20 ? `${mins} min (excellent)` : mins <= 45 ? `${mins} min` : `${mins} min (long)`,
      good: mins <= 30,
      icon: Clock,
    });
  }

  return (
    <div className="space-y-6">

      {/* ── Hero banner ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 text-white p-8"
      >
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-72 h-72 bg-blue-500/10 rounded-full -translate-y-36 translate-x-36 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-56 h-56 bg-indigo-500/10 rounded-full translate-y-28 -translate-x-28 pointer-events-none" />

        <div className="relative flex items-center justify-between gap-6">
          {/* Addresses */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="min-w-0">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-0.5">From</p>
                <p className="font-semibold text-white truncate text-lg leading-tight">
                  {analysis.current_address}
                </p>
              </div>
              <ArrowRight className="w-5 h-5 text-blue-400 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-0.5">To</p>
                <p className="font-semibold text-white truncate text-lg leading-tight">
                  {analysis.destination_address}
                </p>
              </div>
            </div>

            {analysis.overview_summary && (
              <p className="mt-4 text-slate-300 text-sm leading-relaxed line-clamp-3 max-w-xl">
                {analysis.overview_summary}
              </p>
            )}
          </div>

          {/* Overall score badge */}
          <div className="flex-shrink-0 text-center">
            <div className="w-28 h-28 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex flex-col items-center justify-center">
              <span className={`text-4xl font-black ${gradeColor}`}>{grade}</span>
              <span className="text-slate-300 text-xs mt-0.5">{Math.round(overallScore)}/100</span>
            </div>
            <p className="text-slate-400 text-xs mt-2">Overall grade</p>
          </div>
        </div>
      </motion.div>

      {/* ── Score breakdown ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6"
      >
        <h3 className="text-base font-bold text-gray-900 mb-5 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-500" />
          Score Breakdown
        </h3>
        <div className="grid grid-cols-5 gap-4">
          {scoreCards.map(({ icon: Icon, label, score, description, delay }) => {
            const textColor =
              score >= 80 ? 'text-green-600' :
              score >= 65 ? 'text-blue-600'  :
              score >= 50 ? 'text-yellow-600': 'text-red-600';

            return (
              <motion.div
                key={label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay }}
                className="flex flex-col items-center text-center gap-2"
              >
                <ScoreRing score={score} delay={delay} />
                <div>
                  <div className="flex items-center justify-center gap-1 mb-0.5">
                    <Icon className={`w-3.5 h-3.5 ${textColor}`} />
                    <span className="text-sm font-semibold text-gray-800">{label}</span>
                  </div>
                  <p className="text-xs text-gray-500 leading-tight">{description}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* ── At-a-glance highlights ── */}
      {highlights.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6"
        >
          <h3 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            At a Glance
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {highlights.map(({ label, value, good, icon: Icon }) => (
              <div
                key={label}
                className={`rounded-xl p-4 border ${
                  good
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <Icon className={`w-4 h-4 ${good ? 'text-emerald-500' : 'text-red-400'}`} />
                  {good
                    ? <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                    : <ArrowDownRight className="w-4 h-4 text-red-400" />
                  }
                </div>
                <p className="text-xs text-gray-500 mb-0.5">{label}</p>
                <p className={`text-sm font-bold ${good ? 'text-emerald-700' : 'text-red-700'}`}>
                  {value}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── What to expect ── */}
      {analysis.lifestyle_changes && analysis.lifestyle_changes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6"
        >
          <h3 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-blue-500" />
            What to Expect
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {analysis.lifestyle_changes.slice(0, 8).map((change: string, idx: number) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + idx * 0.04 }}
                className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{change.replace(/^[✓√✔]\s*/, '')}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── AI Bottom line ── */}
      {analysis.ai_insights && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="relative overflow-hidden bg-gradient-to-br from-violet-600 to-indigo-700 rounded-2xl p-6 text-white"
        >
          <div className="absolute top-0 right-0 w-48 h-48 bg-white/5 rounded-full -translate-y-24 translate-x-24 pointer-events-none" />
          <div className="relative flex items-start gap-4">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <Lightbulb className="w-5 h-5 text-white" />
            </div>
            <div>
              <h4 className="font-bold text-white mb-2 text-base">AI Verdict</h4>
              <p className="text-indigo-100 text-sm leading-relaxed">
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
