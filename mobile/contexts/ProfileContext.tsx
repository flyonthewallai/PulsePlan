import React, { createContext, useState, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { userService, UserProfile } from '@/services/userService';
import { useAuth } from './AuthContext';

interface ProfileData extends Partial<UserProfile> {
  // Legacy fields for backward compatibility
  email?: string;
  school?: string;
  major?: string;
  lastLocationUpdate?: string;
}

interface ProfileContextType {
  profileData: ProfileData;
  updateProfile: (data: Partial<ProfileData>) => Promise<void>;
  updateLocation: (city: string, timezone: string) => Promise<void>;
  updatePreferences: (preferences: any) => Promise<void>;
  updateWorkingHours: (workingHours: any) => Promise<void>;
  updateStudyPreferences: (studyPreferences: any) => Promise<void>;
  updateOnboardingStatus: (onboardingComplete: boolean, onboardingStep?: number) => Promise<void>;
  getLocationData: () => { city: string | null; timezone: string | null };
  refreshProfile: () => Promise<void>;
}

const defaultProfileData: ProfileData = {
  name: 'Ronan Healy',
  email: 'ronan@colorado.edu',
  school: 'CU Boulder',
  major: 'Biology'
};

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

export const ProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profileData, setProfileData] = useState<ProfileData>(defaultProfileData);
  const { user } = useAuth();

  const updateProfile = async (data: Partial<ProfileData>) => {
    const newProfileData = { ...profileData, ...data };
    setProfileData(newProfileData);
    await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
  };

  const updateLocation = async (city: string, timezone: string) => {
    try {
      // Update on server if user is authenticated
      if (user?.id) {
        const updatedProfile = await userService.updateLocation(user.id, city, timezone);
        if (updatedProfile) {
          // Update local state with server data
          const newProfileData = { ...profileData, ...updatedProfile };
          setProfileData(newProfileData);
          await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
        }
      } else {
        // Fallback to local storage only
        const locationData = {
          city,
          timezone,
          lastLocationUpdate: new Date().toISOString()
        };
        
        const newProfileData = { ...profileData, ...locationData };
        setProfileData(newProfileData);
        await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
      }
      
      console.log('📍 Location updated:', { city, timezone });
    } catch (error) {
      console.error('❌ Error updating location:', error);
      throw error;
    }
  };

  const updatePreferences = async (preferences: any) => {
    try {
      if (user?.id) {
        const updatedProfile = await userService.updatePreferences(user.id, preferences);
        if (updatedProfile) {
          const newProfileData = { ...profileData, ...updatedProfile };
          setProfileData(newProfileData);
          await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
        }
      }
      console.log('⚙️ Preferences updated:', preferences);
    } catch (error) {
      console.error('❌ Error updating preferences:', error);
      throw error;
    }
  };

  const updateWorkingHours = async (workingHours: any) => {
    try {
      if (user?.id) {
        const updatedProfile = await userService.updateWorkingHours(user.id, workingHours);
        if (updatedProfile) {
          const newProfileData = { ...profileData, ...updatedProfile };
          setProfileData(newProfileData);
          await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
        }
      }
      console.log('🕐 Working hours updated:', workingHours);
    } catch (error) {
      console.error('❌ Error updating working hours:', error);
      throw error;
    }
  };

  const updateStudyPreferences = async (studyPreferences: any) => {
    try {
      if (user?.id) {
        const updatedProfile = await userService.updateStudyPreferences(user.id, studyPreferences);
        if (updatedProfile) {
          const newProfileData = { ...profileData, ...updatedProfile };
          setProfileData(newProfileData);
          await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
        }
      }
      console.log('📚 Study preferences updated:', studyPreferences);
    } catch (error) {
      console.error('❌ Error updating study preferences:', error);
      throw error;
    }
  };

  const updateOnboardingStatus = async (onboardingComplete: boolean, onboardingStep?: number) => {
    try {
      if (user?.id) {
        const updatedProfile = await userService.updateOnboardingStatus(user.id, onboardingComplete, onboardingStep);
        if (updatedProfile) {
          const newProfileData = { ...profileData, ...updatedProfile };
          setProfileData(newProfileData);
          await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
        }
      }
      console.log('🎯 Onboarding status updated:', { onboardingComplete, onboardingStep });
    } catch (error) {
      console.error('❌ Error updating onboarding status:', error);
      throw error;
    }
  };

  const getLocationData = () => {
    return {
      city: profileData.city || null,
      timezone: profileData.timezone || null
    };
  };

  const refreshProfile = async () => {
    if (!user?.id) return;

    try {
      const serverProfile = await userService.getUserProfile(user.id);
      if (serverProfile) {
        // Merge server data with local data, prioritizing server data
        const mergedData = { ...profileData, ...serverProfile };
        setProfileData(mergedData);
        await AsyncStorage.setItem('profileData', JSON.stringify(mergedData));
        console.log('✅ Server profile refreshed:', serverProfile);
      }
    } catch (error) {
      console.error('Error refreshing server profile:', error);
    }
  };

  // Get user's current timezone
  const getCurrentTimezone = () => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (error) {
      console.error('Error getting timezone:', error);
      return 'UTC';
    }
  };

  // Load saved profile data on mount and set timezone if not already set
  React.useEffect(() => {
    const loadProfileData = async () => {
      try {
        const savedData = await AsyncStorage.getItem('profileData');
        if (savedData) {
          const parsedData = JSON.parse(savedData);
          
          // If timezone is not set, set it automatically
          if (!parsedData.timezone) {
            parsedData.timezone = getCurrentTimezone();
            await AsyncStorage.setItem('profileData', JSON.stringify(parsedData));
          }
          
          setProfileData(parsedData);
        } else {
          // If no saved data, set timezone on initial load
          const initialData = {
            ...defaultProfileData,
            timezone: getCurrentTimezone()
          };
          setProfileData(initialData);
          await AsyncStorage.setItem('profileData', JSON.stringify(initialData));
        }
      } catch (error) {
        console.error('Error loading profile data:', error);
        // Fallback to default with current timezone
        const fallbackData = {
          ...defaultProfileData,
          timezone: getCurrentTimezone()
        };
        setProfileData(fallbackData);
      }
    };
    loadProfileData();
  }, []);

  // Load user profile from server when user is authenticated
  React.useEffect(() => {
    const loadServerProfile = async () => {
      if (!user?.id) return;

      try {
        const serverProfile = await userService.getUserProfile(user.id);
        if (serverProfile) {
          // Merge server data with local data, prioritizing server data
          const mergedData = { ...profileData, ...serverProfile };
          setProfileData(mergedData);
          await AsyncStorage.setItem('profileData', JSON.stringify(mergedData));
          console.log('✅ Server profile loaded:', serverProfile);
        }
      } catch (error) {
        console.error('Error loading server profile:', error);
        // Fallback to Supabase direct query
        try {
          const supabaseProfile = await userService.getUserProfileFromSupabase(user.id);
          if (supabaseProfile) {
            const mergedData = { ...profileData, ...supabaseProfile };
            setProfileData(mergedData);
            await AsyncStorage.setItem('profileData', JSON.stringify(mergedData));
            console.log('✅ Supabase profile loaded as fallback:', supabaseProfile);
          }
        } catch (supabaseError) {
          console.error('Error loading Supabase profile:', supabaseError);
        }
      }
    };

    loadServerProfile();
  }, [user?.id]);

  return (
    <ProfileContext.Provider value={{ 
      profileData, 
      updateProfile, 
      updateLocation, 
      updatePreferences,
      updateWorkingHours,
      updateStudyPreferences,
      updateOnboardingStatus,
      getLocationData,
      refreshProfile
    }}>
      {children}
    </ProfileContext.Provider>
  );
};

export const useProfile = () => {
  const context = useContext(ProfileContext);
  if (context === undefined) {
    throw new Error('useProfile must be used within a ProfileProvider');
  }
  return context;
}; 