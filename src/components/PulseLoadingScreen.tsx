import React from 'react';
import { View, StyleSheet, Image } from 'react-native';

interface PulseLoadingScreenProps {
  visible?: boolean;
  text?: string;
}

export default function PulseLoadingScreen({ 
  visible = true, 
}: PulseLoadingScreenProps) {
  if (!visible) return null;

  return (
    <View style={styles.container}>
      <Image 
        source={require('@/assets/images/icon.png')} 
        style={styles.icon}
        resizeMode="contain"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    width: 120,
    height: 120,
  },
}); 