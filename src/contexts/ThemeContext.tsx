import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Theme {
  id: string;
  name: string;
  premium: boolean;
  colors: {
    primary: string;
    accent: string;
    background: string;
    surface: string;
    textPrimary: string;
    textSecondary: string;
    border: string;
    card: string;
    success: string;
    warning: string;
    error: string;
  };
}

export const themes: Theme[] = [
  {
    id: 'midnight',
    name: 'Midnight',
    premium: false,
    colors: {
      primary: '#4F8CFF',
      accent: '#8E6FFF',
      background: '#000117',
      surface: 'rgba(255, 255, 255, 0.06)',
      textPrimary: '#FFFFFF',
      textSecondary: 'rgba(255, 255, 255, 0.7)',
      border: 'rgba(255, 255, 255, 0.12)',
      card: 'rgba(255, 255, 255, 0.08)',
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'ocean',
    name: 'Ocean',
    premium: false,
    colors: {
      primary: '#00C2FF',
      accent: '#0066FF',
      background: '#0A1420',
      surface: 'rgba(0, 194, 255, 0.08)',
      textPrimary: '#FFFFFF',
      textSecondary: 'rgba(255, 255, 255, 0.7)',
      border: 'rgba(0, 194, 255, 0.2)',
      card: 'rgba(0, 194, 255, 0.1)',
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'forest',
    name: 'Forest',
    premium: true,
    colors: {
      primary: '#4CD964',
      accent: '#0A84FF',
      background: '#0A1A0F',
      surface: 'rgba(76, 217, 100, 0.08)',
      textPrimary: '#FFFFFF',
      textSecondary: 'rgba(255, 255, 255, 0.7)',
      border: 'rgba(76, 217, 100, 0.2)',
      card: 'rgba(76, 217, 100, 0.1)',
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'sunset',
    name: 'Sunset',
    premium: true,
    colors: {
      primary: '#FF9500',
      accent: '#FF2D55',
      background: '#1A0F05',
      surface: 'rgba(255, 149, 0, 0.08)',
      textPrimary: '#FFFFFF',
      textSecondary: 'rgba(255, 255, 255, 0.7)',
      border: 'rgba(255, 149, 0, 0.2)',
      card: 'rgba(255, 149, 0, 0.1)',
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'cosmic',
    name: 'Cosmic',
    premium: true,
    colors: {
      primary: '#9F7AEA',
      accent: '#ED64A6',
      background: '#0F051A',
      surface: 'rgba(159, 122, 234, 0.08)',
      textPrimary: '#FFFFFF',
      textSecondary: 'rgba(255, 255, 255, 0.7)',
      border: 'rgba(159, 122, 234, 0.2)',
      card: 'rgba(159, 122, 234, 0.1)',
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'emerald',
    name: 'Emerald',
    premium: true,
    colors: {
      primary: '#10B981',
      accent: '#059669',
      background: '#051A14',
      surface: 'rgba(16, 185, 129, 0.08)',
      textPrimary: '#FFFFFF',
      textSecondary: 'rgba(255, 255, 255, 0.7)',
      border: 'rgba(16, 185, 129, 0.2)',
      card: 'rgba(16, 185, 129, 0.1)',
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
];

interface ThemeContextType {
  currentTheme: Theme;
  setTheme: (themeId: string) => Promise<void>;
  allThemes: Theme[];
  isThemeUnlocked: (themeId: string) => boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
  isPremium?: boolean;
}

export function ThemeProvider({ children, isPremium = false }: ThemeProviderProps) {
  const [currentTheme, setCurrentTheme] = useState<Theme>(themes[0]); // Default to midnight

  useEffect(() => {
    loadTheme();
  }, []);

  const loadTheme = async () => {
    try {
      const savedThemeId = await AsyncStorage.getItem('selectedTheme');
      if (savedThemeId) {
        const theme = themes.find(t => t.id === savedThemeId);
        if (theme && (!theme.premium || isPremium)) {
          setCurrentTheme(theme);
        }
      }
    } catch (error) {
      console.error('Error loading theme:', error);
    }
  };

  const setTheme = async (themeId: string) => {
    try {
      const theme = themes.find(t => t.id === themeId);
      if (!theme) return;

      // Check if theme is premium and user doesn't have premium
      if (theme.premium && !isPremium) {
        throw new Error('Premium theme requires subscription');
      }

      setCurrentTheme(theme);
      await AsyncStorage.setItem('selectedTheme', themeId);
    } catch (error) {
      console.error('Error setting theme:', error);
      throw error;
    }
  };

  const isThemeUnlocked = (themeId: string) => {
    const theme = themes.find(t => t.id === themeId);
    return theme ? (!theme.premium || isPremium) : false;
  };

  return (
    <ThemeContext.Provider value={{
      currentTheme,
      setTheme,
      allThemes: themes,
      isThemeUnlocked
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
} 