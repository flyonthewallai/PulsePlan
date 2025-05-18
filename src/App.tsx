import React, { useState, useEffect } from 'react';
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
import { Onboarding } from './pages/Onboarding';
import { Dashboard } from './pages/Dashboard';
import { WeekView } from './pages/WeekView';
import { Settings } from './pages/Settings';
import { Insights } from './pages/Insights';
import { AIModal } from './components/AIModal';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AuthStack } from './navigation/AuthStack';
import { TaskCreateModal } from './components/TaskCreateModal';
import { useTheme } from '@react-navigation/native';

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

function AppContent() {
  const [currentPage, setCurrentPage] = useState('onboarding');
  const [darkMode, setDarkMode] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const { user, loading } = useAuth();
  const insets = useSafeAreaInsets();
  const theme = useTheme();
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Handle deep links
  useEffect(() => {
    const handleDeepLink = (event: { url: string }) => {
      console.log('Deep link received:', event.url);
      
      // Handle auth callback URLs
      if (event.url.includes('/auth/callback')) {
        // The URL will contain the access token and refresh token
        // Supabase will automatically handle this through the auth state change listener
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
      <View style={[styles.container, styles.centerContent]}>
        <ActivityIndicator size="large" color="#00AEEF" />
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

  // Show onboarding for new users
  if (currentPage === 'onboarding') {
    return <Onboarding onComplete={() => setCurrentPage('dashboard')} />;
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

  const createTask = (task: any) => {
    // Implementation of createTask function
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onTaskClick={handleTaskClick} darkMode={darkMode} />;
      case 'week':
        return <WeekView onTaskClick={handleTaskClick} darkMode={darkMode} />;
      case 'settings':
        return <Settings darkMode={darkMode} onToggleDarkMode={toggleDarkMode} />;
      case 'insights':
        return <Insights darkMode={darkMode} />;
      default:
        return <Dashboard onTaskClick={handleTaskClick} darkMode={darkMode} />;
    }
  };

  return (
    <View 
      style={[
        styles.container,
        darkMode ? styles.darkContainer : styles.lightContainer,
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
            darkMode ? styles.darkNavbar : styles.lightNavbar,
          ]}
        >
          <TouchableOpacity 
            onPress={() => handleNavigate('dashboard')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'dashboard' ? 'grid' : 'grid-outline'} 
              size={24} 
              color={currentPage === 'dashboard' ? '#00AEEF' : darkMode ? '#D1D5DB' : '#6B7280'} 
            />
            <Text style={[
              styles.navText,
              currentPage === 'dashboard' && styles.activeNav,
              darkMode ? styles.darkNavText : styles.lightNavText
            ]}>
              Home
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => handleNavigate('week')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'week' ? 'time' : 'time-outline'} 
              size={24} 
              color={currentPage === 'week' ? '#00AEEF' : darkMode ? '#D1D5DB' : '#6B7280'} 
            />
            <Text style={[
              styles.navText,
              currentPage === 'week' && styles.activeNav,
              darkMode ? styles.darkNavText : styles.lightNavText
            ]}>
              Week
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => handleNavigate('insights')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'insights' ? 'analytics' : 'analytics-outline'} 
              size={24} 
              color={currentPage === 'insights' ? '#00AEEF' : darkMode ? '#D1D5DB' : '#6B7280'} 
            />
            <Text style={[
              styles.navText,
              currentPage === 'insights' && styles.activeNav,
              darkMode ? styles.darkNavText : styles.lightNavText
            ]}>
              Insights
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => handleNavigate('settings')} 
            style={styles.navItem}
          >
            <Ionicons 
              name={currentPage === 'settings' ? 'settings-outline' : 'settings-outline'} 
              size={24} 
              color={currentPage === 'settings' ? '#00AEEF' : darkMode ? '#D1D5DB' : '#6B7280'} 
            />
            <Text style={[
              styles.navText,
              currentPage === 'settings' && styles.activeNav,
              darkMode ? styles.darkNavText : styles.lightNavText
            ]}>
              Settings
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>

      {showAIModal && (
        <AIModal
          task={selectedTask}
          onClose={() => {
            setShowAIModal(false);
            setSelectedTask(null);
          }}
          isVisible={showAIModal}
          darkMode={darkMode}
        />
      )}
      <TaskCreateModal
        visible={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={createTask}
        theme={theme}
      />
    </View>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </SafeAreaProvider>
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  lightContainer: {
    backgroundColor: '#F9FAFB',
  },
  darkContainer: {
    backgroundColor: '#0D1B2A',
  },
  navbar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.05)',
  },
  lightNavbar: {
    backgroundColor: '#FFFFFF',
  },
  darkNavbar: {
    backgroundColor: '#1F2937',
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    borderRadius: 12,
    marginHorizontal: 4,
  },
  navText: {
    fontSize: 12,
    marginTop: 4,
    fontWeight: '500',
  },
  activeNav: {
    color: '#00AEEF',
  },
  darkNavText: {
    color: '#D1D5DB',
  },
  lightNavText: {
    color: '#6B7280',
  },
});