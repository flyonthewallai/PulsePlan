import React, { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import PulseLoadingScreen from '@/components/PulseLoadingScreen';

// This is the index page - the first page users land on
// Navigation logic is handled in AuthContext, so this just shows loading
export default function Index() {
  const { loading } = useAuth();
  const { currentTheme } = useTheme();
  const router = useRouter();

  // Manual fallback navigation in case auth context doesn't handle it
  useEffect(() => {
    if (!loading) {
      // Small delay to let auth context handle navigation first
      const timer = setTimeout(() => {
        // Only navigate if we're still on the index page after auth context should have handled it
        router.replace('/(tabs)/home');
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [loading, router]);

  return (
    <PulseLoadingScreen visible={loading} text="Initializing PulsePlan..." />
  );
}