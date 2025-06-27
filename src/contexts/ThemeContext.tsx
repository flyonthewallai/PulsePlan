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
    id: 'dark-agent',
    name: 'Dark Agent',
    premium: false,
    colors: {
      primary: '#4F8CFF',
      accent: '#8E6FFF',
      background: '#000000',
      surface: '#1C1C1E',
      textPrimary: '#FFFFFF',
      textSecondary: '#8A8A8E',
      border: '#262628',
      card: '#333333',
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
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
      primary: '#06B6D4',
      accent: '#0891B2',
      background: '#0F172A',
      surface: '#1E293B',
      textPrimary: '#F8FAFC',
      textSecondary: '#CBD5E1',
      border: '#334155',
      card: '#1E293B',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'forest',
    name: 'Forest',
    premium: true,
    colors: {
      primary: '#22C55E',
      accent: '#16A34A',
      background: '#0F1419',
      surface: '#1C2A1E',
      textPrimary: '#F0FDF4',
      textSecondary: '#BBF7D0',
      border: '#22543D',
      card: '#1C2A1E',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'sunset',
    name: 'Sunset',
    premium: true,
    colors: {
      primary: '#F97316',
      accent: '#EA580C',
      background: '#1C1917',
      surface: '#292524',
      textPrimary: '#FEF7ED',
      textSecondary: '#FDE68A',
      border: '#78716C',
      card: '#292524',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'cosmic',
    name: 'Cosmic',
    premium: true,
    colors: {
      primary: '#8B5CF6',
      accent: '#7C3AED',
      background: '#1E1B4B',
      surface: '#312E81',
      textPrimary: '#F3F4F6',
      textSecondary: '#C7D2FE',
      border: '#6366F1',
      card: '#312E81',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    },
  },
  {
    id: 'emerald',
    name: 'Emerald',
    premium: true,
    colors: {
      primary: '#059669',
      accent: '#047857',
      background: '#064E3B',
      surface: '#065F46',
      textPrimary: '#ECFDF5',
      textSecondary: '#A7F3D0',
      border: '#047857',
      card: '#065F46',
      success: '#10B981',
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