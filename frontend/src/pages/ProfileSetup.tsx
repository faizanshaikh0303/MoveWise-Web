import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import AddressAutocomplete from '../components/AddressAutocomplete';

const ProfileSetup = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const isSubmitting = useRef(false);
  const explicitSubmit = useRef(false);
  
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [checkingProfile, setCheckingProfile] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Form data
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

  const [hobbyInput, setHobbyInput] = useState('');

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
      setCheckingProfile(false);
    }
  };

  const validateStep1 = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.work_hours_start) {
      newErrors.work_hours_start = 'Work start time is required';
    }
    if (!formData.work_hours_end) {
      newErrors.work_hours_end = 'Work end time is required';
    }
    if (!formData.work_address) {
      newErrors.work_address = 'Work address is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.sleep_hours_start) {
      newErrors.sleep_hours_start = 'Sleep start time is required';
    }
    if (!formData.sleep_hours_end) {
      newErrors.sleep_hours_end = 'Wake up time is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    console.log('handleNext called, current step:', step);
    
    if (step === 1 && !validateStep1()) {
      return;
    }
    if (step === 2 && !validateStep2()) {
      return;
    }
    
    // Don't auto-advance from step 3, user must click "Complete Setup"
    if (step < 3) {
      console.log('Advancing to step:', step + 1);
      setStep(step + 1);
      setErrors({});
    } else {
      console.log('Already on step 3, not advancing');
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
      setErrors({});
    }
  };

  const addHobby = () => {
    if (hobbyInput.trim() && !formData.hobbies.includes(hobbyInput.trim())) {
      setFormData({
        ...formData,
        hobbies: [...formData.hobbies, hobbyInput.trim()],
      });
      setHobbyInput('');
    }
  };

  const removeHobby = (hobby: string) => {
    setFormData({
      ...formData,
      hobbies: formData.hobbies.filter((h) => h !== hobby),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('=== FORM SUBMIT TRIGGERED ===');
    console.log('ProfileSetup: explicitSubmit.current =', explicitSubmit.current);
    console.log('ProfileSetup: Starting submission, step =', step);
    
    // Only allow submit if user explicitly clicked the button
    if (!explicitSubmit.current) {
      console.warn('WARNING: Form auto-submitted! Blocking. User must click Complete Setup button.');
      explicitSubmit.current = false; // Reset
      return;
    }
    
    // Reset flag
    explicitSubmit.current = false;
    
    console.log('ProfileSetup: Current hobbies:', formData.hobbies);
    console.log('ProfileSetup: Form data:', formData);
    
    // Block submit unless we're on step 3
    if (step !== 3) {
      console.warn('WARNING: Form submitted but not on step 3! Current step:', step);
      return;
    }
    
    // Double check - don't allow submit if we just transitioned to step 3
    if (loading) {
      console.warn('WARNING: Already processing, ignoring duplicate submit');
      return;
    }
    
    // Prevent any navigation during submission
    isSubmitting.current = true;
    
    // Format work hours
    const work_hours = `${formData.work_hours_start} - ${formData.work_hours_end}`;
    const sleep_hours = `${formData.sleep_hours_start} - ${formData.sleep_hours_end}`;
    
    setLoading(true);

    try {
      console.log('ProfileSetup: Calling API to save profile...');
      await profileAPI.createOrUpdate({
        work_hours,
        work_address: formData.work_address,
        commute_preference: formData.commute_preference,
        sleep_hours,
        noise_preference: formData.noise_preference,
        hobbies: formData.hobbies.length > 0 ? formData.hobbies : undefined,
      });
      
      console.log('ProfileSetup: Profile saved successfully');
      
      // Wait a bit to ensure profile is saved
      await new Promise(resolve => setTimeout(resolve, 500));
      
      console.log('ProfileSetup: Navigating to dashboard');
      // Navigate to dashboard with replace to prevent back button issues
      navigate('/dashboard', { replace: true });
    } catch (error) {
      console.error('ProfileSetup: Failed to save profile:', error);
      alert('Failed to save profile. Please try again.');
      isSubmitting.current = false;
    } finally {
      setLoading(false);
    }
  };

  const handleAddressChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      work_address: value
    }));
  };

  if (checkingProfile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-gray-600 mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  const progress = (step / 3) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Complete Your Profile</h1>
          <p className="text-gray-600 mt-2">Help us personalize your location analysis</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Step {step} of 3</span>
            <span className="text-sm text-gray-500">{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit}>
            {/* Step 1: Work Schedule */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-1">Work Schedule</h2>
                  <p className="text-gray-600 text-sm mb-6">Tell us about your work routine</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Work Start Time *
                    </label>
                    <input
                      type="time"
                      value={formData.work_hours_start}
                      onChange={(e) => setFormData({ ...formData, work_hours_start: e.target.value })}
                      className={`input ${errors.work_hours_start ? 'border-red-500' : ''}`}
                    />
                    {errors.work_hours_start && (
                      <p className="text-red-500 text-sm mt-1">{errors.work_hours_start}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Work End Time *
                    </label>
                    <input
                      type="time"
                      value={formData.work_hours_end}
                      onChange={(e) => setFormData({ ...formData, work_hours_end: e.target.value })}
                      className={`input ${errors.work_hours_end ? 'border-red-500' : ''}`}
                    />
                    {errors.work_hours_end && (
                      <p className="text-red-500 text-sm mt-1">{errors.work_hours_end}</p>
                    )}
                  </div>
                </div>

                <div>
                  <AddressAutocomplete
                    label="Work Address *"
                    value={formData.work_address}
                    onChange={handleAddressChange}
                    placeholder="e.g., 123 Main St, San Francisco, CA"
                    icon="current"
                  />
                  {errors.work_address && (
                    <p className="text-red-500 text-sm mt-1">{errors.work_address}</p>
                  )}
                  <p className="mt-1 text-sm text-gray-500">We'll calculate commute times for you</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Commute Preference
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { value: 'driving', label: 'Driving' },
                      { value: 'transit', label: 'Transit' },
                      { value: 'bicycling', label: 'Bicycling' },
                      { value: 'walking', label: 'Walking' },
                    ].map((mode) => (
                      <button
                        key={mode.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, commute_preference: mode.value })}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          formData.commute_preference === mode.value
                            ? 'border-primary bg-primary/5 text-primary font-medium'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {mode.label}
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
                  <p className="text-gray-600 text-sm mb-6">Help us assess noise compatibility</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sleep Time *
                    </label>
                    <input
                      type="time"
                      value={formData.sleep_hours_start}
                      onChange={(e) => setFormData({ ...formData, sleep_hours_start: e.target.value })}
                      className={`input ${errors.sleep_hours_start ? 'border-red-500' : ''}`}
                    />
                    {errors.sleep_hours_start && (
                      <p className="text-red-500 text-sm mt-1">{errors.sleep_hours_start}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Wake Up Time *
                    </label>
                    <input
                      type="time"
                      value={formData.sleep_hours_end}
                      onChange={(e) => setFormData({ ...formData, sleep_hours_end: e.target.value })}
                      className={`input ${errors.sleep_hours_end ? 'border-red-500' : ''}`}
                    />
                    {errors.sleep_hours_end && (
                      <p className="text-red-500 text-sm mt-1">{errors.sleep_hours_end}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Noise Preference
                  </label>
                  <div className="space-y-2">
                    {[
                      { value: 'quiet', label: 'Quiet', desc: 'I prefer peaceful, low-noise environments' },
                      { value: 'moderate', label: 'Moderate', desc: 'Some noise is okay, typical urban sounds' },
                      { value: 'doesnt-matter', label: "Doesn't Matter", desc: 'Noise level is not a concern for me' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, noise_preference: option.value })}
                        className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                          formData.noise_preference === option.value
                            ? 'border-primary bg-primary/5'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="font-medium text-gray-900">{option.label}</div>
                        <div className="text-sm text-gray-600 mt-1">{option.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Hobbies */}
            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-1">Hobbies & Interests</h2>
                  <p className="text-gray-600 text-sm mb-6">We'll find amenities that match your lifestyle</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Add Your Hobbies
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={hobbyInput}
                      onChange={(e) => setHobbyInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          e.stopPropagation();
                          addHobby();
                        }
                      }}
                      placeholder="e.g., gym, hiking, restaurants"
                      className="input flex-1"
                    />
                    <button
                      type="button"
                      onClick={addHobby}
                      className="btn btn-primary px-6"
                    >
                      Add
                    </button>
                  </div>
                </div>

                {formData.hobbies.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Your Hobbies ({formData.hobbies.length})
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {formData.hobbies.map((hobby) => (
                        <span
                          key={hobby}
                          className="inline-flex items-center gap-2 px-3 py-2 bg-primary/10 text-primary rounded-lg"
                        >
                          {hobby}
                          <button
                            type="button"
                            onClick={() => removeHobby(hobby)}
                            className="hover:text-primary-dark"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {formData.hobbies.length === 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex gap-3">
                      <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p className="text-sm text-blue-900">
                        Add hobbies like: gym, hiking, restaurants, coffee shops, parks, museums, nightlife, sports, etc.
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
                  disabled={loading}
                  onClick={() => {
                    console.log('Complete Setup button clicked');
                    explicitSubmit.current = true;
                  }}
                  className="btn btn-primary flex-1 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : 'Complete Setup'}
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Required Fields Notice */}
        <div className="text-center mt-4 text-sm text-gray-600">
          * Required fields
        </div>
      </div>
    </div>
  );
};

export default ProfileSetup;
