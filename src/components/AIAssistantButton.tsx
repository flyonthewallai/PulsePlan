import React from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import { GlowingOrb } from './GlowingOrb';
import { useTheme } from '../contexts/ThemeContext';

interface AIAssistantButtonProps {
  onPress: () => void;
}

export default function AIAssistantButton({ onPress }: AIAssistantButtonProps) {
  const { currentTheme } = useTheme();
  
  return (
    <TouchableOpacity 
      style={styles.container} 
      onPress={onPress}
      activeOpacity={0.8}
    >
      <GlowingOrb size="ms" color={currentTheme.colors.primary} glowIntensity={0.7} />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 30,
    right: 27,
    zIndex: 1000,
  },
}); 