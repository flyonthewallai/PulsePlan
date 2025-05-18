import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { usePremium } from '../../App';

// Theme interfaces
export interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  cardBackground: string;
  text: string;
  subtext: string;
  border: string;
  success: string;
  warning: string;
  error: string;
}

export interface Theme {
  id: string;
  name: string;
  isDark: boolean;
  colors: ThemeColors;
  premium: boolean;
}

// Available themes
export const themes: { [key: string]: Theme } = {
  defaultLight: {
    id: 'defaultLight',
    name: 'Default Light',
    isDark: false,
    premium: false,
    colors: {
      primary: '#00AEEF',
      secondary: '#FF6B6B',
      accent: '#F59E0B',
      background: '#F9FAFB',
      cardBackground: '#FFFFFF',
      text: '#0D1B2A',
      subtext: '#6B7280',
      border: '#E5E7EB',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  defaultDark: {
    id: 'defaultDark',
    name: 'Default Dark',
    isDark: true,
    premium: false,
    colors: {
      primary: '#00AEEF',
      secondary: '#FF6B6B',
      accent: '#F59E0B',
      background: '#0D1B2A',
      cardBackground: '#1F2937',
      text: '#FFFFFF',
      subtext: '#D1D5DB',
      border: '#374151',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  ocean: {
    id: 'ocean',
    name: 'Ocean',
    isDark: false,
    premium: true,
    colors: {
      primary: '#0066CC',
      secondary: '#FF6B6B',
      accent: '#F59E0B',
      background: '#E6F3FF',
      cardBackground: '#FFFFFF',
      text: '#0D1B2A',
      subtext: '#6B7280',
      border: '#CCE5FF',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  oceanDark: {
    id: 'oceanDark',
    name: 'Ocean Dark',
    isDark: true,
    premium: true,
    colors: {
      primary: '#0066CC',
      secondary: '#FF6B6B',
      accent: '#F59E0B',
      background: '#0A1929',
      cardBackground: '#102A43',
      text: '#FFFFFF',
      subtext: '#D1D5DB',
      border: '#1E4976',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  forest: {
    id: 'forest',
    name: 'Forest',
    isDark: false,
    premium: true,
    colors: {
      primary: '#2E7D32',
      secondary: '#FF6B6B',
      accent: '#F59E0B',
      background: '#F1F8E9',
      cardBackground: '#FFFFFF',
      text: '#1B2D1B',
      subtext: '#6B7280',
      border: '#DCEDC8',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  forestDark: {
    id: 'forestDark',
    name: 'Forest Dark',
    isDark: true,
    premium: true,
    colors: {
      primary: '#2E7D32',
      secondary: '#FF6B6B',
      accent: '#F59E0B',
      background: '#0F1F12',
      cardBackground: '#1B2D1B',
      text: '#FFFFFF',
      subtext: '#D1D5DB',
      border: '#2C592C',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  sunset: {
    id: 'sunset',
    name: 'Sunset',
    isDark: false,
    premium: true,
    colors: {
      primary: '#FF5722',
      secondary: '#9C27B0',
      accent: '#F59E0B',
      background: '#FBE9E7',
      cardBackground: '#FFFFFF',
      text: '#3E2723',
      subtext: '#6B7280',
      border: '#FFCCBC',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  sunsetDark: {
    id: 'sunsetDark',
    name: 'Sunset Dark',
    isDark: true,
    premium: true,
    colors: {
      primary: '#FF5722',
      secondary: '#9C27B0',
      accent: '#F59E0B',
      background: '#3E2723',
      cardBackground: '#5D4037',
      text: '#FFFFFF',
      subtext: '#D1D5DB',
      border: '#BF360C',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  },
  midnight: {
    id: 'midnight',
    name: 'Midnight',
    isDark: true,
    premium: true,
    colors: {
      primary: '#6200EA',
      secondary: '#00BCD4',
      accent: '#F59E0B',
      background: '#0C0032',
      cardBackground: '#190061',
      text: '#FFFFFF',
      subtext: '#D1D5DB',
      border: '#3700B3',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    }
  }
};

// Theme context
interface ThemeContextType {
  theme: Theme;
  darkMode: boolean;
  setDarkMode: (isDark: boolean) => void;
  setTheme: (themeId: string) => void;
  isPremium: boolean;
  availableThemes: Theme[];
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Theme provider
interface ThemeProviderProps {
  children: React.ReactNode;
  initialDarkMode: boolean;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ 
  children, 
  initialDarkMode
}) => {
  const { isPremium } = usePremium();
  const [darkMode, setDarkMode] = useState(initialDarkMode);
  const [currentThemeId, setCurrentThemeId] = useState(initialDarkMode ? 'defaultDark' : 'defaultLight');
  
  // Get current theme object
  const theme = themes[currentThemeId] || (darkMode ? themes.defaultDark : themes.defaultLight);
  
  // Get available themes for user
  const availableThemes = Object.values(themes).filter(theme => 
    !theme.premium || isPremium
  );

  // Apply dark mode change
  const handleDarkModeChange = (isDark: boolean) => {
    setDarkMode(isDark);
    
    // Switch to the dark/light version of the current theme if available
    const currentThemeBase = Object.values(themes).find(t => t.id === currentThemeId);
    if (currentThemeBase) {
      const themeName = currentThemeBase.name.replace(' Dark', '').replace(' Light', '');
      
      // Find matching theme with the correct darkness
      const matchingTheme = Object.values(themes).find(t => 
        t.name.includes(themeName) && t.isDark === isDark
      );
      
      if (matchingTheme) {
        setCurrentThemeId(matchingTheme.id);
        AsyncStorage.setItem('themeId', matchingTheme.id);
      } else {
        // Fallback to default themes
        setCurrentThemeId(isDark ? 'defaultDark' : 'defaultLight');
        AsyncStorage.setItem('themeId', isDark ? 'defaultDark' : 'defaultLight');
      }
    }
    
    AsyncStorage.setItem('darkMode', isDark.toString());
  };

  // Change theme
  const handleThemeChange = (themeId: string) => {
    if (themes[themeId]) {
      // Check if it's a premium theme and user has premium access
      if (themes[themeId].premium && !isPremium) {
        // Don't change theme, user needs to upgrade
        return;
      }
      
      setCurrentThemeId(themeId);
      setDarkMode(themes[themeId].isDark);
      
      // Save preferences
      AsyncStorage.setItem('themeId', themeId);
      AsyncStorage.setItem('darkMode', themes[themeId].isDark.toString());
    }
  };

  // Load theme from storage on mount
  useEffect(() => {
    const loadSavedTheme = async () => {
      try {
        const savedThemeId = await AsyncStorage.getItem('themeId');
        const savedDarkMode = await AsyncStorage.getItem('darkMode');
        
        if (savedThemeId && themes[savedThemeId]) {
          // If theme is premium but user doesn't have premium, use default
          if (themes[savedThemeId].premium && !isPremium) {
            setCurrentThemeId(savedDarkMode === 'true' ? 'defaultDark' : 'defaultLight');
          } else {
            setCurrentThemeId(savedThemeId);
          }
        }
        
        if (savedDarkMode !== null) {
          setDarkMode(savedDarkMode === 'true');
        }
      } catch (error) {
        console.log('Error loading theme:', error);
      }
    };
    
    loadSavedTheme();
  }, [isPremium]);

  return (
    <ThemeContext.Provider
      value={{
        theme,
        darkMode,
        setDarkMode: handleDarkModeChange,
        setTheme: handleThemeChange,
        isPremium,
        availableThemes,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use the theme context
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}; 