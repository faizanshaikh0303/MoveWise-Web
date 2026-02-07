import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI, authAPI } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import AddressAutocomplete from '../components/AddressAutocomplete';
import type { UserProfile } from '../types';

const ProfileSettings = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  
  const [activeTab, setActiveTab] = useState<'profile' | 'password'>('profile');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalData, setOriginalData] = useState<any>(null);
  
  // Profile form
  const [profileData, setProfileData] = useState({
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
  
  // Password form
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const profile = await profileAPI.get();
      if (profile) {
        // Parse work hours
        const workHours = profile.work_hours?.split(' - ') || ['', ''];
        const sleepHours = profile.sleep_hours?.split(' - ') || ['', ''];
        
        const data = {
          work_hours_start: workHours[0] || '',
          work_hours_end: workHours[1] || '',
          work_address: profile.work_address || '',
          commute_preference: profile.commute_preference || 'driving',
          sleep_hours_start: sleepHours[0] || '',
          sleep_hours_end: sleepHours[1] || '',
          noise_preference: profile.noise_preference || 'quiet',
          hobbies: profile.hobbies || [],
        };
        
        setProfileData(data);
        setOriginalData(JSON.parse(JSON.stringify(data))); // Deep copy
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  // Check for changes whenever profileData updates
  useEffect(() => {
    if (originalData) {
      const changed = JSON.stringify(profileData) !== JSON.stringify(originalData);
      setHasChanges(changed);
    }
  }, [profileData, originalData]);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      const work_hours = `${profileData.work_hours_start} - ${profileData.work_hours_end}`;
      const sleep_hours = `${profileData.sleep_hours_start} - ${profileData.sleep_hours_end}`;
      
      await profileAPI.update({
        work_hours,
        work_address: profileData.work_address,
        commute_preference: profileData.commute_preference,
        sleep_hours,
        noise_preference: profileData.noise_preference,
        hobbies: profileData.hobbies.length > 0 ? profileData.hobbies : undefined,
      });
      
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setOriginalData(JSON.parse(JSON.stringify(profileData))); // Update original to new saved state
      setHasChanges(false);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update profile. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match!' });
      return;
    }
    
    if (passwordData.newPassword.length < 6) {
      setMessage({ type: 'error', text: 'Password must be at least 6 characters!' });
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      await authAPI.changePassword(passwordData.currentPassword, passwordData.newPassword);
      setMessage({ type: 'success', text: 'Password changed successfully! Please login again.' });
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      
      // Logout after password change
      setTimeout(() => {
        logout();
        navigate('/');
      }, 2000);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to change password. Please check your current password.';
      setMessage({ type: 'error', text: errorMessage });
    } finally {
      setSaving(false);
    }
  };

  const addHobby = () => {
    if (hobbyInput.trim() && !profileData.hobbies.includes(hobbyInput.trim())) {
      setProfileData({
        ...profileData,
        hobbies: [...profileData.hobbies, hobbyInput.trim()],
      });
      setHobbyInput('');
    }
  };

  const removeHobby = (hobby: string) => {
    setProfileData({
      ...profileData,
      hobbies: profileData.hobbies.filter((h) => h !== hobby),
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-gray-600 mt-4">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Profile Settings</h1>
              <p className="text-sm text-gray-600">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              navigate('/');
            }}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('profile')}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === 'profile'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Profile Information
              </div>
            </button>
            <button
              onClick={() => setActiveTab('password')}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === 'password'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                Change Password
              </div>
            </button>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-50 border border-green-200 text-green-700'
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <form onSubmit={handleProfileSave} className="space-y-6">
              {/* Work Schedule */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Work Schedule</h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Time
                    </label>
                    <input
                      type="time"
                      value={profileData.work_hours_start}
                      onChange={(e) => setProfileData({ ...profileData, work_hours_start: e.target.value })}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Time
                    </label>
                    <input
                      type="time"
                      value={profileData.work_hours_end}
                      onChange={(e) => setProfileData({ ...profileData, work_hours_end: e.target.value })}
                      className="input"
                    />
                  </div>
                </div>

                <div className="mb-4">
                  <AddressAutocomplete
                    label="Work Address"
                    value={profileData.work_address}
                    onChange={(value) => setProfileData({ ...profileData, work_address: value })}
                    placeholder="e.g., 123 Main St, San Francisco, CA"
                    icon="current"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Commute Preference
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {['driving', 'transit', 'bicycling', 'walking'].map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => setProfileData({ ...profileData, commute_preference: mode })}
                        className={`p-2 rounded-lg border-2 text-sm transition-all ${
                          profileData.commute_preference === mode
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

              <hr />

              {/* Sleep Schedule */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Sleep Schedule</h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sleep Time
                    </label>
                    <input
                      type="time"
                      value={profileData.sleep_hours_start}
                      onChange={(e) => setProfileData({ ...profileData, sleep_hours_start: e.target.value })}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Wake Time
                    </label>
                    <input
                      type="time"
                      value={profileData.sleep_hours_end}
                      onChange={(e) => setProfileData({ ...profileData, sleep_hours_end: e.target.value })}
                      className="input"
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
                        onClick={() => setProfileData({ ...profileData, noise_preference: option.value })}
                        className={`w-full p-3 rounded-lg border-2 transition-all text-left ${
                          profileData.noise_preference === option.value
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

              <hr />

              {/* Hobbies */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Hobbies & Interests</h3>
                <div className="flex gap-2 mb-4">
                  <input
                    type="text"
                    value={hobbyInput}
                    onChange={(e) => setHobbyInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addHobby();
                      }
                    }}
                    placeholder="Add a hobby"
                    className="input flex-1"
                  />
                  <button
                    type="button"
                    onClick={addHobby}
                    className="btn btn-secondary px-6"
                  >
                    Add
                  </button>
                </div>

                {profileData.hobbies.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {profileData.hobbies.map((hobby) => (
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
                )}
              </div>

              {/* Save Button */}
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="btn btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || !hasChanges}
                  className="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Password Tab */}
        {activeTab === 'password' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <form onSubmit={handlePasswordChange} className="space-y-6 max-w-md">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  className="input"
                  required
                  minLength={6}
                />
                <p className="text-sm text-gray-500 mt-1">At least 6 characters</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  className="input"
                  required
                />
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })}
                  className="btn btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn btn-primary flex-1 disabled:opacity-50"
                >
                  {saving ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileSettings;
