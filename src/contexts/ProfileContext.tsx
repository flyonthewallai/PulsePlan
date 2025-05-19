import React, { createContext, useState, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface ProfileData {
  name: string;
  email: string;
  school: string;
  major: string;
}

interface ProfileContextType {
  profileData: ProfileData;
  updateProfile: (data: Partial<ProfileData>) => Promise<void>;
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

  // Load saved profile data on mount
  React.useEffect(() => {
    const loadProfileData = async () => {
      try {
        const savedData = await AsyncStorage.getItem('profileData');
        if (savedData) {
          setProfileData(JSON.parse(savedData));
        }
      } catch (error) {
        console.error('Error loading profile data:', error);
      }
    };
    loadProfileData();
  }, []);

  return (
    <ProfileContext.Provider value={{ profileData, updateProfile }}>
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