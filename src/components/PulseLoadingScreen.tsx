import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { CachedImage } from './CachedImage';

interface PulseLoadingScreenProps {
  visible?: boolean;
  text?: string;
}

export default function PulseLoadingScreen({ 
  visible = true, 
}: PulseLoadingScreenProps) {
  const { currentTheme } = useTheme();
  
  if (!visible) return null;

  return (
    <View style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
      <CachedImage 
        imageKey="icon" 
        style={styles.icon}
        resizeMode="contain"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    width: 120,
    height: 120,
  },
}); 