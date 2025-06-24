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
import { PremiumProvider, usePremium } from '../contexts/PremiumContext';
import { ProfileProvider } from '../contexts/ProfileContext';

function AppWithTheme() {
  const { currentTheme } = useTheme();
  
  return (
    <>
      <Stack screenOptions={{ 
        headerShown: false,
        contentStyle: { backgroundColor: currentTheme.colors.background }
      }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="onboarding" />
        <Stack.Screen name="auth" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(settings)" />
        <Stack.Screen name="+not-found" />
      </Stack>
      <StatusBar style="light" backgroundColor={currentTheme.colors.background} />
    </>
  );
}

function ThemeWrapper({ children }: { children: React.ReactNode }) {
  const { isPremium } = usePremium();
  
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
        <PremiumProvider>
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
        </PremiumProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
