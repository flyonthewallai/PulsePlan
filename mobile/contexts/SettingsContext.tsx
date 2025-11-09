import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface WorkingHours {
  startHour: number;
  endHour: number;
  lunchBreakStart: number;
  lunchBreakEnd: number;
}

export interface StudyTimeBlock {
  id: string;
  startHour: number;
  endHour: number;
  days: number[]; // 0-6 for Sunday-Saturday
}

interface SettingsContextType {
  workingHours: WorkingHours;
  updateWorkingHours: (hours: WorkingHours) => Promise<void>;
  studyTimes: StudyTimeBlock[];
  addStudyTime: (block: Omit<StudyTimeBlock, 'id'>) => Promise<void>;
  removeStudyTime: (id: string) => Promise<void>;
  updateStudyTime: (id: string, block: Omit<StudyTimeBlock, 'id'>) => Promise<void>;
}

const defaultWorkingHours: WorkingHours = {
  startHour: 9,
  endHour: 17,
  lunchBreakStart: 12,
  lunchBreakEnd: 13
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [workingHours, setWorkingHours] = useState<WorkingHours>(defaultWorkingHours);
  const [studyTimes, setStudyTimes] = useState<StudyTimeBlock[]>([]);

  // Load settings from storage
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const savedWorkingHours = await AsyncStorage.getItem('workingHours');
        if (savedWorkingHours) {
          setWorkingHours(JSON.parse(savedWorkingHours));
        }

        const savedStudyTimes = await AsyncStorage.getItem('studyTimes');
        if (savedStudyTimes) {
          setStudyTimes(JSON.parse(savedStudyTimes));
        }
      } catch (error) {
        console.error('Error loading settings:', error);
      }
    };

    loadSettings();
  }, []);

  const updateWorkingHours = async (hours: WorkingHours) => {
    try {
      await AsyncStorage.setItem('workingHours', JSON.stringify(hours));
      setWorkingHours(hours);
    } catch (error) {
      console.error('Error saving working hours:', error);
      throw error;
    }
  };

  const addStudyTime = async (block: Omit<StudyTimeBlock, 'id'>) => {
    try {
      const newBlock = {
        ...block,
        id: Date.now().toString() // Simple unique ID
      };
      const updatedStudyTimes = [...studyTimes, newBlock];
      await AsyncStorage.setItem('studyTimes', JSON.stringify(updatedStudyTimes));
      setStudyTimes(updatedStudyTimes);
    } catch (error) {
      console.error('Error adding study time:', error);
      throw error;
    }
  };

  const removeStudyTime = async (id: string) => {
    try {
      const updatedStudyTimes = studyTimes.filter(block => block.id !== id);
      await AsyncStorage.setItem('studyTimes', JSON.stringify(updatedStudyTimes));
      setStudyTimes(updatedStudyTimes);
    } catch (error) {
      console.error('Error removing study time:', error);
      throw error;
    }
  };

  const updateStudyTime = async (id: string, block: Omit<StudyTimeBlock, 'id'>) => {
    try {
      const updatedStudyTimes = studyTimes.map(existingBlock => 
        existingBlock.id === id ? { ...block, id } : existingBlock
      );
      await AsyncStorage.setItem('studyTimes', JSON.stringify(updatedStudyTimes));
      setStudyTimes(updatedStudyTimes);
    } catch (error) {
      console.error('Error updating study time:', error);
      throw error;
    }
  };

  const contextValue = React.useMemo(() => ({
    workingHours,
    updateWorkingHours,
    studyTimes,
    addStudyTime,
    removeStudyTime,
    updateStudyTime
  }), [workingHours, studyTimes, addStudyTime, removeStudyTime, updateStudyTime]);

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}; 