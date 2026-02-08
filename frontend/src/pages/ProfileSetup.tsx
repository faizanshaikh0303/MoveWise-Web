import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI } from '../services/api';
import AddressAutocomplete from '../components/AddressAutocomplete';

const ProfileSetup = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const isSubmitting = useRef(false);
  const explicitSubmit = useRef(false);

  const [formData, setFormData] = useState({
    work_hours_start: '',
    work_hours_end: '',
    work_address: '',
    commute_preference: 'driving',
    sleep_hours_start: '',
    sleep_hours_end: '',
    noise_preference: 'quiet',
    hobbies: [] as string[],
  });

  useEffect(() => {
    checkExistingProfile();
  }, []);

  const checkExistingProfile = async () => {
    // Don't check if we're in the middle of submitting
    if (isSubmitting.current) {
      return;
    }

    try {
      const profile = await profileAPI.get();
      if (profile && !isSubmitting.current) {
        // Profile exists, redirect to dashboard
        navigate('/dashboard', { replace: true });
        return;
      }
    } catch (error) {
      // No profile exists, continue with setup
      console.log('No profile found, continuing with setup');
    } finally {
      setLoading(false);
    }
  };

  const validateStep = () => {
    if (step === 1) {
      if (!formData.work_hours_start || !formData.work_hours_end || !formData.work_address) {
        setError('Please complete all work schedule fields');
        return false;
      }
    } else if (step === 2) {
      if (!formData.sleep_hours_start || !formData.sleep_hours_end) {
        setError('Please complete all sleep schedule fields');
        return false;
      }
    }
    setError('');
    return true;
  };

  const handleNext = () => {
    if (validateStep()) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    setError('');
    setStep(step - 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Only proceed if user explicitly clicked Complete Setup
    if (!explicitSubmit.current) {
      console.log('WARNING: Form auto-submitted! Blocking.');
      return;
    }

    console.log('Complete Setup button clicked - proceeding with submission');

    if (!validateStep()) {
      explicitSubmit.current = false;
      return;
    }

    setLoading(true);
    isSubmitting.current = true;

    try {
      const work_hours = `${formData.work_hours_start} - ${formData.work_hours_end}`;
      const sleep_hours = `${formData.sleep_hours_start} - ${formData.sleep_hours_end}`;
      
      await profileAPI.createOrUpdate({
        work_hours,
        work_address: formData.work_address,
        commute_preference: formData.commute_preference,
        sleep_hours,
        noise_preference: formData.noise_preference,
        hobbies: formData.hobbies.length > 0 ? formData.hobbies : undefined,
      });

      console.log('Profile saved successfully with hobbies:', formData.hobbies);
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      console.error('Profile creation error:', err);
      console.error('Error response:', err.response);
      console.error('Error data:', err.response?.data);
      
      let errorMessage = 'Failed to create profile. Please try again.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((d: any) => d.msg).join(', ');
        }
      }
      
      setError(errorMessage);
      isSubmitting.current = false;
      explicitSubmit.current = false;
    } finally {
      setLoading(false);
    }
  };

  const handleAddressChange = useCallback((value: string) => {
    setFormData(prev => ({
      ...prev,
      work_address: value
    }));
  }, []);

  const toggleHobby = (hobbyValue: string) => {
    if (formData.hobbies.includes(hobbyValue)) {
      setFormData({
        ...formData,
        hobbies: formData.hobbies.filter(h => h !== hobbyValue)
      });
    } else {
      setFormData({
        ...formData,
        hobbies: [...formData.hobbies, hobbyValue]
      });
    }
  };

  const HOBBY_OPTIONS = [
    { value: 'gym', label: 'Gym & Fitness', icon: '💪' },
    { value: 'hiking', label: 'Hiking', icon: '🥾' },
    { value: 'parks', label: 'Parks', icon: '🌳' },
    { value: 'restaurants', label: 'Restaurants', icon: '🍽️' },
    { value: 'coffee', label: 'Coffee Shops', icon: '☕' },
    { value: 'bars', label: 'Bars', icon: '🍺' },
    { value: 'movies', label: 'Movies', icon: '🎬' },
    { value: 'shopping', label: 'Shopping', icon: '🛍️' },
    { value: 'library', label: 'Libraries', icon: '📚' },
    { value: 'sports', label: 'Sports', icon: '⚽' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to MoveWise!</h1>
          <p className="text-gray-600">Let's personalize your experience</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Step {step} of 3</span>
            <span className="text-sm text-gray-500">{Math.round((step / 3) * 100)}% complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 3) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {/* Step 1: Work Schedule */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-1">Work Schedule</h2>
                <p className="text-gray-600 text-sm mb-6">Help us understand your daily routine</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Work Start Time
                  </label>
                  <input
                    type="time"
                    value={formData.work_hours_start}
                    onChange={(e) => setFormData({ ...formData, work_hours_start: e.target.value })}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Work End Time
                  </label>
                  <input
                    type="time"
                    value={formData.work_hours_end}
                    onChange={(e) => setFormData({ ...formData, work_hours_end: e.target.value })}
                    className="input"
                    required
                  />
                </div>
              </div>

              <AddressAutocomplete
                label="Work Address"
                value={formData.work_address}
                onChange={handleAddressChange}
                placeholder="e.g., 123 Main St, San Francisco, CA"
                icon="current"
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Commute Preference
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {['driving', 'transit', 'bicycling', 'walking'].map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() => setFormData({ ...formData, commute_preference: mode })}
                      className={`p-2 rounded-lg border-2 text-sm transition-all ${
                        formData.commute_preference === mode
                          ? 'border-primary bg-primary/5 text-primary font-medium'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {mode.charAt(0).toUpperCase() + mode.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Sleep Schedule */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-1">Sleep Schedule</h2>
                <p className="text-gray-600 text-sm mb-6">Tell us about your rest preferences</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sleep Time
                  </label>
                  <input
                    type="time"
                    value={formData.sleep_hours_start}
                    onChange={(e) => setFormData({ ...formData, sleep_hours_start: e.target.value })}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wake Time
                  </label>
                  <input
                    type="time"
                    value={formData.sleep_hours_end}
                    onChange={(e) => setFormData({ ...formData, sleep_hours_end: e.target.value })}
                    className="input"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Noise Preference
                </label>
                <div className="space-y-2">
                  {[
                    { value: 'quiet', label: 'Quiet', desc: 'Peaceful, low-noise environments' },
                    { value: 'moderate', label: 'Moderate', desc: 'Typical urban sounds are okay' },
                    { value: 'doesnt-matter', label: "Doesn't Matter", desc: 'Noise is not a concern' },
                  ].map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, noise_preference: option.value })}
                      className={`w-full p-3 rounded-lg border-2 transition-all text-left ${
                        formData.noise_preference === option.value
                          ? 'border-primary bg-primary/5'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="font-medium text-gray-900">{option.label}</div>
                      <div className="text-sm text-gray-600">{option.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Hobbies - Checkbox Selection */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-1">Hobbies & Interests</h2>
                <p className="text-gray-600 text-sm mb-6">Select activities you enjoy - we'll find matching amenities</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {HOBBY_OPTIONS.map((hobby) => {
                  const isSelected = formData.hobbies.includes(hobby.value);
                  return (
                    <button
                      key={hobby.value}
                      type="button"
                      onClick={() => toggleHobby(hobby.value)}
                      className={`p-4 rounded-lg border-2 transition-all text-left ${
                        isSelected
                          ? 'border-primary bg-primary/10 shadow-sm'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{hobby.icon}</span>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{hobby.label}</div>
                        </div>
                        {isSelected && (
                          <svg className="w-5 h-5 text-primary flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              {formData.hobbies.length > 0 && (
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-sm text-green-900">
                    <span className="font-semibold">{formData.hobbies.length} selected:</span> We'll show amenities for {formData.hobbies.join(', ')} in your area reports.
                  </p>
                </div>
              )}

              {formData.hobbies.length === 0 && (
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex gap-3">
                    <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-blue-900">
                      Select hobbies to personalize your reports. If you don't select any, we'll show all amenity types.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex gap-4 mt-8">
            {step > 1 && (
              <button
                type="button"
                onClick={handleBack}
                disabled={loading}
                className="btn btn-secondary flex-1"
              >
                Back
              </button>
            )}
            
            {step < 3 ? (
              <button
                type="button"
                onClick={handleNext}
                className="btn btn-primary flex-1"
              >
                Next
              </button>
            ) : (
              <button
                type="submit"
                onClick={() => {
                  console.log('Complete Setup button clicked');
                  explicitSubmit.current = true;
                }}
                disabled={loading}
                className="btn btn-primary flex-1 disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Complete Setup'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileSetup;
