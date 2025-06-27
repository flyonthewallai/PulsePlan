import { Stack } from 'expo-router';
import { useTheme } from '@/contexts/ThemeContext';
import { navigationAnimations } from '@/config/animations';

export default function SettingsLayout() {
  const { currentTheme } = useTheme();

  return (
    <Stack screenOptions={{
      headerShown: false,
      contentStyle: {
        backgroundColor: currentTheme.colors.background,
      },
      ...navigationAnimations.slideFromRight,
    }} />
  );
} 
 
 
 