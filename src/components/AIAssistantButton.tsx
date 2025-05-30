import React from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import { GlowingOrb } from './GlowingOrb';

interface AIAssistantButtonProps {
  onPress: () => void;
}

export default function AIAssistantButton({ onPress }: AIAssistantButtonProps) {
  return (
    <TouchableOpacity 
      style={styles.container} 
      onPress={onPress}
      activeOpacity={0.8}
    >
      <GlowingOrb size="ms" color="blue" glowIntensity={0.7} />
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