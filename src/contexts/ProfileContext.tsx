import React, { createContext, useState, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface ProfileData {
  name: string;
  email: string;
  school: string;
  major: string;
  city?: string;
  timezone?: string;
  lastLocationUpdate?: string;
}

interface ProfileContextType {
  profileData: ProfileData;
  updateProfile: (data: Partial<ProfileData>) => Promise<void>;
  updateLocation: (city: string, timezone: string) => Promise<void>;
  getLocationData: () => { city: string | null; timezone: string | null };
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

  const updateProfile = async (data: Partial<ProfileData>) => {
    const newProfileData = { ...profileData, ...data };
    setProfileData(newProfileData);
    await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
  };

  const updateLocation = async (city: string, timezone: string) => {
    const locationData = {
      city,
      timezone,
      lastLocationUpdate: new Date().toISOString()
    };
    
    const newProfileData = { ...profileData, ...locationData };
    setProfileData(newProfileData);
    await AsyncStorage.setItem('profileData', JSON.stringify(newProfileData));
    
    console.log('📍 Location updated:', { city, timezone });
  };

  const getLocationData = () => {
    return {
      city: profileData.city || null,
      timezone: profileData.timezone || null
    };
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

  return (
    <ProfileContext.Provider value={{ 
      profileData, 
      updateProfile, 
      updateLocation, 
      getLocationData 
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