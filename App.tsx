import React, { useState, useEffect, createContext, useContext } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  Platform,
  KeyboardAvoidingView,
  ActivityIndicator,
  Linking
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { NavigationContainer } from '@react-navigation/native';
import { Onboarding } from './src/pages/Onboarding';
import { Dashboard } from './src/pages/Dashboard';
import { WeekView } from './src/pages/WeekView';
import { Settings } from './src/pages/Settings';
import { Progress } from './src/pages/Progress';
import { AIModal } from './src/components/AIModal';
import { AuthProvider, useAuth } from './src/contexts/AuthContext';
import { AuthStack } from './src/navigation/AuthStack';
import { ThemeProvider, useTheme } from './src/contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Deep link configuration
const linking = {
  prefixes: ['rhythm://', 'exp://127.0.0.1:8081/--', 'https://rhythm.app'],
  config: {
    screens: {
      ForgotPassword: 'reset-password',
      AuthCallback: 'auth/callback',
    },
  },
};

// Premium context
interface PremiumContextType {
  isPremium: boolean;
  togglePremium: () => Promise<void>;
}

const PremiumContext = createContext<PremiumContextType | undefined>(undefined);

export const usePremium = () => {
  const context = useContext(PremiumContext);
  if (context === undefined) {
    throw new Error('usePremium must be used within a PremiumProvider');
  }
  return context;
};

const PremiumProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isPremium, setIsPremium] = useState(false);

  useEffect(() => {
    const checkPremiumStatus = async () => {
      try {
        const premiumStatus = await AsyncStorage.getItem('isPremiumUser');
        setIsPremium(premiumStatus === 'true');
      } catch (error) {
        console.log('Error loading premium status:', error);
      }
    };
    
    checkPremiumStatus();
  }, []);

  const togglePremium = async () => {
    try {
      const newStatus = !isPremium;
      await AsyncStorage.setItem('isPremiumUser', newStatus.toString());
      setIsPremium(newStatus);
    } catch (error) {
      console.log('Error saving premium status:', error);
    }
  };

  return (
    <PremiumContext.Provider value={{ isPremium, togglePremium }}>
      {children}
    </PremiumContext.Provider>
  );
};

function AppContent() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [showAIModal, setShowAIModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const { user, loading } = useAuth();
  const { theme, darkMode, setDarkMode } = useTheme();
  const insets = useSafeAreaInsets();

  // Handle deep links
  useEffect(() => {
    const handleDeepLink = (event: { url: string }) => {
      console.log('Deep link received:', event.url);
      
      // Handle auth callback URLs
      if (event.url.includes('/auth/callback')) {
        console.log('Auth callback received');
      }
    };

    // Get the initial URL
    Linking.getInitialURL().then(url => {
      if (url) {
        console.log('Initial URL:', url);
        handleDeepLink({ url });
      }
    });

    // Add event listener for deep links
    const subscription = Linking.addEventListener('url', handleDeepLink);

    return () => {
      subscription.remove();
    };
  }, []);

  // Show loading state while checking authentication
  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  // Show auth screens if user is not authenticated
  if (!user) {
    return (
      <NavigationContainer linking={linking}>
        <AuthStack />
      </NavigationContainer>
    );
  }

  const handleNavigate = (page: string) => {
    setCurrentPage(page);
  };

  const handleTaskClick = (task: any) => {
    setSelectedTask(task);
    setShowAIModal(true);
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onTaskClick={handleTaskClick} darkMode={darkMode} />;
      case 'week':
        return <WeekView onTaskClick={handleTaskClick} darkMode={darkMode} />;
      case 'settings':
        return <Settings darkMode={darkMode} onToggleDarkMode={toggleDarkMode} />;
      case 'progress':
        return <Progress darkMode={darkMode} />;
      default:
        return <Dashboard onTaskClick={handleTaskClick} darkMode={darkMode} />;
    }
  };

  return (
    <View 
      style={[
        styles.container,
        { backgroundColor: theme.colors.background }
      ]}
    >
      <StatusBar style={darkMode ? 'light' : 'dark'} />
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardAvoidingView}
        >
          <View style={styles.content}>
            {renderCurrentPage()}
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>

      <SafeAreaView style={styles.navbarContainer} edges={['bottom']}>
        <View 
          style={[
            styles.navbar,
            { 
              backgroundColor: theme.colors.cardBackground,
              borderTopColor: theme.colors.border
            }
          ]}
        >
          <TouchableOpacity 
            onPress={() => handleNavigate('dashboard')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'dashboard' ? 'today' : 'today-outline'} 
              size={24} 
              color={currentPage === 'dashboard' ? theme.colors.primary : theme.colors.subtext} 
            />
            <Text style={[
              styles.navText,
              { color: currentPage === 'dashboard' ? theme.colors.primary : theme.colors.subtext }
            ]}>
              Today
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => handleNavigate('week')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'week' ? 'calendar' : 'calendar-outline'} 
              size={24} 
              color={currentPage === 'week' ? theme.colors.primary : theme.colors.subtext} 
            />
            <Text style={[
              styles.navText,
              { color: currentPage === 'week' ? theme.colors.primary : theme.colors.subtext }
            ]}>
              Week
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => handleNavigate('progress')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'progress' ? 'stats-chart' : 'stats-chart-outline'} 
              size={24} 
              color={currentPage === 'progress' ? theme.colors.primary : theme.colors.subtext} 
            />
            <Text style={[
              styles.navText,
              { color: currentPage === 'progress' ? theme.colors.primary : theme.colors.subtext }
            ]}>
              Progress
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => handleNavigate('settings')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'settings' ? 'settings' : 'settings-outline'} 
              size={24} 
              color={currentPage === 'settings' ? theme.colors.primary : theme.colors.subtext} 
            />
            <Text style={[
              styles.navText,
              { color: currentPage === 'settings' ? theme.colors.primary : theme.colors.subtext }
            ]}>
              Settings
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>

      {showAIModal && (
        <AIModal
          isVisible={showAIModal}
          onClose={() => setShowAIModal(false)}
          task={selectedTask}
          darkMode={darkMode}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  safeArea: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  navbarContainer: {
    backgroundColor: 'transparent',
  },
  navbar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 8,
    borderTopWidth: 1,
  },
  navItem: {
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
  navText: {
    fontSize: 12,
    marginTop: 4,
  }
});

export default function App() {
  const [darkMode, setDarkMode] = useState(false);
  
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <PremiumProvider>
          <ThemeProvider initialDarkMode={darkMode}>
            <AppContent />
          </ThemeProvider>
        </PremiumProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
} 