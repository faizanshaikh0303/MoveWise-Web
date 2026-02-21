import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import AddressAutocomplete from '../components/AddressAutocomplete';

const ProfileSetup = () => {
  const navigate = useNavigate();
  const fetchUser = useAuthStore((state) => state.fetchUser);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [workFromHome, setWorkFromHome] = useState(false);
  
  const isSubmitting = useRef(false);
  const explicitSubmit = useRef(false);

  const [formData, setFormData] = useState({
    work_hours_start: '09:00',  // Default 9 AM
    work_hours_end: '17:00',    // Default 5 PM
    work_address: '',
    commute_preference: 'driving',
    sleep_hours_start: '23:00', // Default 11 PM
    sleep_hours_end: '07:00',   // Default 7 AM
    noise_preference: 'quiet',
    hobbies: [] as string[],
  });

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

  useEffect(() => {
    checkExistingProfile();
  }, []);

  const checkExistingProfile = async () => {
    if (isSubmitting.current) {
      return;
    }

    try {
      const profile = await profileAPI.get();
      if (profile && !isSubmitting.current) {
        navigate('/dashboard', { replace: true });
        return;
      }
    } catch (error) {
      console.log('No profile found, continuing with setup');
    } finally {
      setLoading(false);
    }
  };

  const validateStep = () => {
    if (step === 1) {
      if (!formData.work_hours_start || !formData.work_hours_end) {
        setError('Please complete work schedule fields');
        return false;
      }
      if (!workFromHome && !formData.work_address) {
        setError('Please enter work address or select "Work from Home"');
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

  const handleWorkFromHomeToggle = () => {
    setWorkFromHome(!workFromHome);
    if (!workFromHome) {
      setFormData({ ...formData, work_address: 'Work from Home', commute_preference: 'none' });
    } else {
      setFormData({ ...formData, work_address: '', commute_preference: 'driving' });
    }
  };

  const handleAddressChange = useCallback((value: string) => {
    setFormData(prev => ({
      ...prev,
      work_address: value
    }));
  }, []);

  const toggleHobby = (hobbyValue: string) => {
    setFormData(prev => ({
      ...prev,
      hobbies: prev.hobbies.includes(hobbyValue)
        ? prev.hobbies.filter(h => h !== hobbyValue)
        : [...prev.hobbies, hobbyValue]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

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
      
      const profileData = {
        work_hours,
        work_address: formData.work_address,
        commute_preference: workFromHome ? 'none' : formData.commute_preference,
        sleep_hours,
        noise_preference: formData.noise_preference,
        hobbies: formData.hobbies.length > 0 ? formData.hobbies : undefined,
      };

      console.log('Submitting profile:', profileData);
      
      await profileAPI.createOrUpdate(profileData);
      await fetchUser();

      console.log('Profile created successfully, navigating to dashboard...');
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      console.error('Profile creation error:', err);
      console.error('Error response:', err.response);
      console.error('Error data:', err.response?.data);
      
      let errorMessage = 'Failed to create profile. Please try again.';
      
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((d: any) => d.msg).join(', ');
        } else {
          errorMessage = err.response.data.detail;
        }
      }
      
      setError(errorMessage);
      isSubmitting.current = false;
      explicitSubmit.current = false;
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteSetup = () => {
    console.log('Complete Setup button clicked');
    explicitSubmit.current = true;
    
    const form = document.querySelector('form');
    if (form) {
      form.requestSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Complete Your Profile</h1>
          <p className="text-gray-600">Make smarter moving decisions with AI-powered location analysis</p>
        </div>

        {/* Progress Steps */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-between mb-2 space-x-10">
            {/* Step 1 */}
            <div className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                step >= 1 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'
              }`}>
                1
              </div>
              <span className="ml-2 text-sm font-medium">Work</span>
            </div>
            
            {/* Connector Line */}
            <div className="flex-1 h-0.5 bg-gray-300 mx-4" />
            
            {/* Step 2 */}
            <div className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                step >= 2 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'
              }`}>
                2
              </div>
              <span className="ml-2 text-sm font-medium">Sleep</span>
            </div>
            
            {/* Connector Line */}
            <div className="flex-1 h-0.5 bg-gray-300 mx-4" />
            
            {/* Step 3 */}
            <div className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                step >= 3 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'
              }`}>
                3
              </div>
              <span className="ml-2 text-sm font-medium">Hobbies</span>
            </div>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            {/* Step 1: Work Schedule */}
            {step === 1 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Work Schedule</h2>
                
                {/* Work from Home Toggle */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={workFromHome}
                      onChange={handleWorkFromHomeToggle}
                      className="w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary"
                    />
                    <span className="ml-3 text-sm font-medium text-gray-900">
                      🏠 I work from home (No commute needed)
                    </span>
                  </label>
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

                {!workFromHome && (
                  <>
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
                  </>
                )}

                <button
                  type="button"
                  onClick={handleNext}
                  className="btn btn-primary w-full"
                >
                  Continue
                </button>
              </div>
            )}

            {/* Step 2: Sleep Schedule */}
            {step === 2 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Sleep & Environment</h2>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Bedtime
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
                      Wake-up Time
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
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Noise Preference
                  </label>
                  <div className="space-y-2">
                    {[
                      { value: 'quiet', label: 'Quiet', desc: 'Prefer peaceful, low-noise environments' },
                      { value: 'moderate', label: 'Moderate', desc: 'Some activity is fine' },
                      { value: 'lively', label: 'Lively', desc: 'Enjoy vibrant, bustling areas' },
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

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="btn btn-secondary flex-1"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={handleNext}
                    className="btn btn-primary flex-1"
                  >
                    Continue
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Hobbies */}
            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Hobbies & Interests</h2>
                  <p className="text-gray-600 text-sm">Select what matters to you (we'll include essentials like grocery stores automatically)</p>
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
                            ? 'border-primary bg-primary/5'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{hobby.icon}</span>
                          <span className="font-medium text-gray-900">{hobby.label}</span>
                          {isSelected && (
                            <svg className="w-5 h-5 text-primary ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-900">
                    {formData.hobbies.length > 0
                      ? `${formData.hobbies.length} selected: ${formData.hobbies.join(', ')}`
                      : 'No hobbies selected yet - we\'ll show all amenity types in your analysis'}
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="btn btn-secondary flex-1"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={handleCompleteSetup}
                    disabled={loading}
                    className="btn btn-primary flex-1"
                  >
                    {loading ? 'Creating Profile...' : 'Complete Setup'}
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProfileSetup;
