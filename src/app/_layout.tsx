import '../../polyfills';
import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../contexts/AuthContext';
import { TaskProvider } from '../contexts/TaskContext';
import { SettingsProvider } from '../contexts/SettingsContext';
import { ThemeProvider, useTheme } from '../contexts/ThemeContext';
import { StreakProvider } from '../contexts/StreakContext';
import { useAuth } from '../contexts/AuthContext';
import { ProfileProvider } from '../contexts/ProfileContext';
import { navigationAnimations } from '../config/animations';

function AppWithTheme() {
  const { currentTheme } = useTheme();
  
  return (
    <>
      <Stack screenOptions={{ 
        headerShown: false,
        contentStyle: { backgroundColor: currentTheme.colors.background },
        animation: 'slide_from_right',
        animationDuration: 300,
        animationTypeForReplace: 'push',
      }}>
        <Stack.Screen 
          name="index" 
          options={navigationAnimations.fade} 
        />
        <Stack.Screen 
          name="onboarding" 
          options={navigationAnimations.elegantSlide} 
        />
        <Stack.Screen 
          name="auth" 
          options={navigationAnimations.fastFade} 
        />
        <Stack.Screen 
          name="(tabs)" 
          options={navigationAnimations.fade} 
        />
        <Stack.Screen 
          name="(settings)" 
          options={navigationAnimations.slideFromRight} 
        />
        <Stack.Screen 
          name="+not-found" 
          options={navigationAnimations.slideFromBottom} 
        />
      </Stack>
      <StatusBar style="light" backgroundColor={currentTheme.colors.background} />
    </>
  );
}

function ThemeWrapper({ children }: { children: React.ReactNode }) {
  const { subscriptionPlan } = useAuth();
  const isPremium = subscriptionPlan === 'premium';
  
  return (
    <ThemeProvider isPremium={isPremium}>
      {children}
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <ProfileProvider>
          <ThemeWrapper>
            <SettingsProvider>
              <TaskProvider>
                <StreakProvider>
                  <AppWithTheme />
                </StreakProvider>
              </TaskProvider>
            </SettingsProvider>
          </ThemeWrapper>
        </ProfileProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
