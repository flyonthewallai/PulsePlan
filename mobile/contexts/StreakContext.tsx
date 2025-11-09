import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface StreakContextType {
  currentStreak: number;
  updateStreak: (completed: boolean) => Promise<void>;
}

const StreakContext = createContext<StreakContextType>({
  currentStreak: 0,
  updateStreak: async () => {},
});

export const useStreak = () => useContext(StreakContext);

export function StreakProvider({ children }: { children: React.ReactNode }) {
  const [currentStreak, setCurrentStreak] = useState(0);

  useEffect(() => {
    loadStreak();
  }, []);

  const loadStreak = async () => {
    try {
      const streak = await AsyncStorage.getItem('currentStreak');
      const lastUpdate = await AsyncStorage.getItem('lastStreakUpdate');
      
      if (streak && lastUpdate) {
        const lastUpdateDate = new Date(lastUpdate);
        const today = new Date();
        const diffDays = Math.floor((today.getTime() - lastUpdateDate.getTime()) / (1000 * 60 * 60 * 24));
        
        if (diffDays > 1) {
          // Reset streak if more than 1 day has passed
          setCurrentStreak(0);
          await AsyncStorage.setItem('currentStreak', '0');
        } else {
          setCurrentStreak(parseInt(streak));
        }
      }
    } catch (error) {
      console.error('Error loading streak:', error);
    }
  };

  const updateStreak = async (completed: boolean) => {
    try {
      const today = new Date();
      const lastUpdate = await AsyncStorage.getItem('lastStreakUpdate');
      
      if (completed) {
        if (!lastUpdate) {
          // First completion
          setCurrentStreak(1);
          await AsyncStorage.setItem('currentStreak', '1');
        } else {
          const lastUpdateDate = new Date(lastUpdate);
          const diffDays = Math.floor((today.getTime() - lastUpdateDate.getTime()) / (1000 * 60 * 60 * 24));
          
          if (diffDays === 1) {
            // Consecutive day
            const newStreak = currentStreak + 1;
            setCurrentStreak(newStreak);
            await AsyncStorage.setItem('currentStreak', newStreak.toString());
          } else if (diffDays > 1) {
            // Break in streak
            setCurrentStreak(1);
            await AsyncStorage.setItem('currentStreak', '1');
          }
        }
        await AsyncStorage.setItem('lastStreakUpdate', today.toISOString());
      }
    } catch (error) {
      console.error('Error updating streak:', error);
    }
  };

  return (
    <StreakContext.Provider value={{ currentStreak, updateStreak }}>
      {children}
    </StreakContext.Provider>
  );
} 