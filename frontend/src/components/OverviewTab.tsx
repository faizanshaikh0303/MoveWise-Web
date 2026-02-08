import { useState } from 'react';

interface OverviewTabProps {
  analysis: any;
  onNavigateToTab?: (tab: string) => void;
}

const OverviewTab = ({ analysis, onNavigateToTab }: OverviewTabProps) => {
  const [showAIInsights, setShowAIInsights] = useState(false);
  const [activeView, setActiveView] = useState<'pros' | 'cons'>('pros');

  // Calculate move score (0-100)
  const calculateMoveScore = () => {
    let score = 50; // Base score

    // Cost impact (-20 to +20)
    const costChange = analysis.cost_data?.change_percentage || 0;
    if (costChange < -15) score += 20;
    else if (costChange < -5) score += 10;
    else if (costChange > 15) score -= 20;
    else if (costChange > 5) score -= 10;

    // Crime impact (-15 to +15)
    const currentCrime = analysis.crime_data?.current_crime_rate || 0;
    const destCrime = analysis.crime_data?.destination_crime_rate || 0;
    const crimeChange = ((destCrime - currentCrime) / currentCrime) * 100;
    if (crimeChange < -20) score += 15;
    else if (crimeChange < -10) score += 8;
    else if (crimeChange > 20) score -= 15;
    else if (crimeChange > 10) score -= 8;

    // Amenities impact (-15 to +15)
    const currentAmenities = Object.values(analysis.amenities_data?.current_amenities || {}).reduce((a: number, b: any) => a + b, 0);
    const destAmenities = Object.values(analysis.amenities_data?.destination_amenities || {}).reduce((a: number, b: any) => a + b, 0);
    const amenitiesChange = ((destAmenities - currentAmenities) / currentAmenities) * 100;
    if (amenitiesChange > 20) score += 15;
    else if (amenitiesChange > 10) score += 8;
    else if (amenitiesChange < -20) score -= 15;
    else if (amenitiesChange < -10) score -= 8;

    return Math.min(Math.max(Math.round(score), 0), 100);
  };

  const moveScore = calculateMoveScore();
  const getScoreColor = (score: number) => {
    if (score >= 70) return 'from-green-400 to-emerald-600';
    if (score >= 50) return 'from-yellow-400 to-orange-500';
    return 'from-red-400 to-pink-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent Move';
    if (score >= 70) return 'Great Choice';
    if (score >= 60) return 'Good Option';
    if (score >= 50) return 'Consider Carefully';
    if (score >= 40) return 'Some Concerns';
    return 'Major Tradeoffs';
  };

  // Extract key metrics
  const commuteDuration = analysis.commute_data?.duration_minutes || 0;
  const costChange = analysis.cost_data?.change_percentage || 0;
  const currentCrime = analysis.crime_data?.current_crime_rate || 0;
  const destCrime = analysis.crime_data?.destination_crime_rate || 0;
  const crimeChange = currentCrime > 0 ? ((destCrime - currentCrime) / currentCrime * 100) : 0;
  const amenitiesCount = Object.values(analysis.amenities_data?.destination_amenities || {}).reduce((a: number, b: any) => a + b, 0);

  // Categorize lifestyle changes
  const improvements: string[] = [];
  const concerns: string[] = [];

  if (costChange < -5) improvements.push(`${Math.abs(costChange).toFixed(0)}% lower cost of living`);
  else if (costChange > 5) concerns.push(`${costChange.toFixed(0)}% higher cost of living`);

  // Use already declared currentCrime and destCrime from line 63-64
  if (destCrime < currentCrime * 0.9) improvements.push('Safer neighborhood');
  else if (destCrime > currentCrime * 1.1) concerns.push('Higher crime rate');

  const currentAmenities = Object.values(analysis.amenities_data?.current_amenities || {}).reduce((a: number, b: any) => a + b, 0);
  const destAmenities = Object.values(analysis.amenities_data?.destination_amenities || {}).reduce((a: number, b: any) => a + b, 0);
  if (destAmenities > currentAmenities * 1.1) improvements.push('More nearby amenities');
  else if (destAmenities < currentAmenities * 0.9) concerns.push('Fewer nearby amenities');

  if (commuteDuration < 30) improvements.push('Short commute time');
  else if (commuteDuration > 45) concerns.push('Long commute time');

  return (
    <div className="space-y-6">
      {/* Move Score Hero Card */}
      <div className={`bg-gradient-to-br ${getScoreColor(moveScore)} rounded-2xl shadow-xl p-8 text-white relative overflow-hidden`}>
        {/* Decorative background elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>
        
        <div className="text-center relative z-10">
          <div className="inline-flex flex-col items-center justify-center mb-4">
            <div className="text-sm font-semibold uppercase tracking-wider mb-2 text-white/80">Your Move Score</div>
            <div className="w-40 h-40 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border-4 border-white/30">
              <div>
                <div className="text-7xl font-bold leading-none">{moveScore}</div>
                <div className="text-sm font-semibold text-white/90 mt-1">out of 100</div>
              </div>
            </div>
          </div>
          <h2 className="text-3xl font-bold mb-2">{getScoreLabel(moveScore)}</h2>
          <p className="text-white/90 text-lg">Your personalized move compatibility assessment</p>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Commute Card */}
        <div className="bg-white rounded-xl shadow-sm p-5 border-2 border-gray-100 hover:border-primary transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            {commuteDuration < 30 ? (
              <span className="text-green-500 text-xl">✓</span>
            ) : commuteDuration > 45 ? (
              <span className="text-yellow-500 text-xl">⚠</span>
            ) : null}
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">{commuteDuration}<span className="text-lg text-gray-500">min</span></div>
          <div className="text-sm text-gray-600">Commute Time</div>
        </div>

        {/* Cost Card */}
        <div className="bg-white rounded-xl shadow-sm p-5 border-2 border-gray-100 hover:border-primary transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            {costChange < 0 ? (
              <span className="text-green-500 text-xl">✓</span>
            ) : costChange > 10 ? (
              <span className="text-red-500 text-xl">✗</span>
            ) : null}
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {costChange > 0 ? '+' : ''}{costChange.toFixed(0)}<span className="text-lg text-gray-500">%</span>
          </div>
          <div className="text-sm text-gray-600">Cost Change</div>
        </div>

        {/* Safety Card */}
        <div className="bg-white rounded-xl shadow-sm p-5 border-2 border-gray-100 hover:border-primary transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            {crimeChange < -10 ? (
              <span className="text-green-500 text-xl">✓</span>
            ) : crimeChange > 10 ? (
              <span className="text-yellow-500 text-xl">⚠</span>
            ) : null}
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {crimeChange > 0 ? '+' : ''}{crimeChange.toFixed(0)}<span className="text-lg text-gray-500">%</span>
          </div>
          <div className="text-sm text-gray-600">Crime Change</div>
        </div>

        {/* Amenities Card */}
        <div className="bg-white rounded-xl shadow-sm p-5 border-2 border-gray-100 hover:border-primary transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <span className="text-green-500 text-xl">✓</span>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">{amenitiesCount}</div>
          <div className="text-sm text-gray-600">Nearby Places</div>
        </div>
      </div>

      {/* Pros & Cons Toggle */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {/* Toggle Buttons */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveView('pros')}
            className={`flex-1 px-6 py-4 font-semibold text-center transition-all ${
              activeView === 'pros'
                ? 'bg-green-50 text-green-700 border-b-2 border-green-500'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Benefits ({improvements.length})
            </div>
          </button>
          <button
            onClick={() => setActiveView('cons')}
            className={`flex-1 px-6 py-4 font-semibold text-center transition-all ${
              activeView === 'cons'
                ? 'bg-yellow-50 text-yellow-700 border-b-2 border-yellow-500'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Concerns ({concerns.length})
            </div>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeView === 'pros' ? (
            <div className="space-y-3">
              {improvements.length > 0 ? (
                improvements.map((item, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-100">
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <p className="text-gray-800 font-medium">{item}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>Similar conditions to your current location</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {concerns.length > 0 ? (
                concerns.map((item, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 bg-yellow-50 rounded-lg border border-yellow-100">
                    <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <p className="text-gray-800 font-medium">{item}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>No major concerns identified</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Scoring Transparency */}
      <div className="bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-white/70 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">How We Calculate Your Score</h3>
              <p className="text-sm text-gray-600">Score breakdown: Base 50 + factors</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Cost Impact */}
          <div className="flex items-start gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
              costChange < -5 ? 'bg-green-100' : costChange > 5 ? 'bg-red-100' : 'bg-gray-100'
            }`}>
              <svg className={`w-5 h-5 ${
                costChange < -5 ? 'text-green-600' : costChange > 5 ? 'text-red-600' : 'text-gray-600'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">Cost of Living</span>
                <span className={`font-semibold ${
                  costChange < -15 ? 'text-green-600' : costChange < -5 ? 'text-green-500' : 
                  costChange > 15 ? 'text-red-600' : costChange > 5 ? 'text-red-500' : 'text-gray-600'
                }`}>
                  {costChange < -15 ? '+20' : costChange < -5 ? '+10' : costChange > 15 ? '-20' : costChange > 5 ? '-10' : '0'} pts
                </span>
              </div>
              <p className="text-sm text-gray-600">
                {costChange < -15 ? 'Major savings (15%+)' : 
                 costChange < -5 ? 'Moderate savings (5-15%)' :
                 costChange > 15 ? 'Major cost increase (15%+)' :
                 costChange > 5 ? 'Moderate cost increase (5-15%)' :
                 'Similar cost of living'}
              </p>
            </div>
          </div>

          {/* Crime Impact */}
          <div className="flex items-start gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
              crimeChange < -10 ? 'bg-green-100' : crimeChange > 10 ? 'bg-red-100' : 'bg-gray-100'
            }`}>
              <svg className={`w-5 h-5 ${
                crimeChange < -10 ? 'text-green-600' : crimeChange > 10 ? 'text-red-600' : 'text-gray-600'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">Safety</span>
                <span className={`font-semibold ${
                  crimeChange < -20 ? 'text-green-600' : crimeChange < -10 ? 'text-green-500' :
                  crimeChange > 20 ? 'text-red-600' : crimeChange > 10 ? 'text-red-500' : 'text-gray-600'
                }`}>
                  {crimeChange < -20 ? '+15' : crimeChange < -10 ? '+8' : 
                   crimeChange > 20 ? '-15' : crimeChange > 10 ? '-8' : '0'} pts
                </span>
              </div>
              <p className="text-sm text-gray-600">
                {crimeChange < -20 ? 'Much safer (20%+ lower crime)' :
                 crimeChange < -10 ? 'Safer (10-20% lower crime)' :
                 crimeChange > 20 ? 'Less safe (20%+ higher crime)' :
                 crimeChange > 10 ? 'Slightly less safe (10-20% higher)' :
                 'Similar safety level'}
              </p>
            </div>
          </div>

          {/* Amenities Impact */}
          <div className="flex items-start gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
              destAmenities > currentAmenities * 1.1 ? 'bg-green-100' : 
              destAmenities < currentAmenities * 0.9 ? 'bg-red-100' : 'bg-gray-100'
            }`}>
              <svg className={`w-5 h-5 ${
                destAmenities > currentAmenities * 1.1 ? 'text-green-600' : 
                destAmenities < currentAmenities * 0.9 ? 'text-red-600' : 'text-gray-600'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">Nearby Amenities</span>
                <span className={`font-semibold ${
                  destAmenities > currentAmenities * 1.2 ? 'text-green-600' : 
                  destAmenities > currentAmenities * 1.1 ? 'text-green-500' :
                  destAmenities < currentAmenities * 0.8 ? 'text-red-600' :
                  destAmenities < currentAmenities * 0.9 ? 'text-red-500' : 'text-gray-600'
                }`}>
                  {destAmenities > currentAmenities * 1.2 ? '+15' : 
                   destAmenities > currentAmenities * 1.1 ? '+8' :
                   destAmenities < currentAmenities * 0.8 ? '-15' :
                   destAmenities < currentAmenities * 0.9 ? '-8' : '0'} pts
                </span>
              </div>
              <p className="text-sm text-gray-600">
                {destAmenities > currentAmenities * 1.2 ? 'Many more amenities (20%+)' :
                 destAmenities > currentAmenities * 1.1 ? 'More amenities (10-20%)' :
                 destAmenities < currentAmenities * 0.8 ? 'Much fewer amenities (20%+)' :
                 destAmenities < currentAmenities * 0.9 ? 'Fewer amenities (10-20%)' :
                 'Similar amenity access'}
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Final Score Range:</span>
              <span className="font-semibold text-gray-900">0-100 (capped)</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Insights - Collapsible */}
      {analysis.llm_analysis && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl shadow-sm border border-purple-100 overflow-hidden">
          <button
            onClick={() => setShowAIInsights(!showAIInsights)}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-white/50 transition-all"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="text-left">
                <h3 className="font-semibold text-gray-900">AI-Powered Insights</h3>
                <p className="text-sm text-gray-600">Personalized analysis based on your preferences</p>
              </div>
            </div>
            <svg
              className={`w-5 h-5 text-gray-600 transition-transform ${showAIInsights ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showAIInsights && (
            <div className="px-6 py-4 bg-white/50 border-t border-purple-100">
              <div className="prose prose-sm max-w-none text-gray-700">
                {analysis.llm_analysis}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick Actions */}
      <button
        onClick={() => onNavigateToTab?.('environment')}
        className="w-full bg-gradient-to-r from-primary to-blue-600 rounded-xl shadow-lg p-6 text-white hover:shadow-xl transition-all group"
      >
        <div className="flex items-center justify-between">
          <div className="text-left">
            <h3 className="text-xl font-semibold mb-1">Ready to dive deeper?</h3>
            <p className="text-white/90">Click to explore detailed breakdowns starting with Environment</p>
          </div>
          <svg className="w-12 h-12 text-white/30 group-hover:text-white/50 group-hover:translate-x-2 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </div>
      </button>
    </div>
  );
};

export default OverviewTab;
