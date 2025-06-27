import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Dimensions } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface LoadingScreenProps {
  visible?: boolean;
}

export default function LoadingScreen({ visible = true }: LoadingScreenProps) {
  const { currentTheme } = useTheme();
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const translateAnim = useRef(new Animated.Value(-SCREEN_WIDTH)).current;

  useEffect(() => {
    if (visible) {
      // Create the heartbeat pulse animation
      const pulseAnimation = Animated.loop(
        Animated.sequence([
          // Quick pulse up
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 100,
            useNativeDriver: true,
          }),
          // Quick pulse down
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 100,
            useNativeDriver: true,
          }),
          // Small pause
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 150,
            useNativeDriver: true,
          }),
          // Second quick pulse up
          Animated.timing(pulseAnim, {
            toValue: 0.8,
            duration: 80,
            useNativeDriver: true,
          }),
          // Second quick pulse down
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 80,
            useNativeDriver: true,
          }),
          // Longer pause before repeat
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );

      // Create the sweeping line animation
      const sweepAnimation = Animated.loop(
        Animated.timing(translateAnim, {
          toValue: SCREEN_WIDTH,
          duration: 2000,
          useNativeDriver: true,
        })
      );

      // Start both animations
      pulseAnimation.start();
      sweepAnimation.start();

      // Reset sweep animation when it completes
      const resetSweep = () => {
        translateAnim.setValue(-SCREEN_WIDTH);
      };

      const listener = translateAnim.addListener(({ value }) => {
        if (value >= SCREEN_WIDTH - 1) {
          setTimeout(resetSweep, 100);
        }
      });

      return () => {
        pulseAnimation.stop();
        sweepAnimation.stop();
        translateAnim.removeListener(listener);
      };
    }
  }, [visible, pulseAnim, translateAnim]);

  if (!visible) return null;

  const pulseHeight = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [2, 20],
  });

  const pulseOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 1],
  });

  return (
    <View style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
      {/* Heartbeat line container */}
      <View style={styles.heartbeatContainer}>
        {/* Base line */}
        <View style={[styles.baseLine, { backgroundColor: currentTheme.colors.border }]} />
        
        {/* Pulsing heartbeat */}
        <Animated.View
          style={[
            styles.heartbeatLine,
            {
              backgroundColor: currentTheme.colors.textPrimary,
              shadowColor: currentTheme.colors.textPrimary,
              height: pulseHeight,
              opacity: pulseOpacity,
            },
          ]}
        />
        
        {/* Sweeping line effect */}
        <Animated.View
          style={[
            styles.sweepLine,
            {
              backgroundColor: currentTheme.colors.textPrimary,
              shadowColor: currentTheme.colors.textPrimary,
              transform: [{ translateX: translateAnim }],
            },
          ]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  heartbeatContainer: {
    width: SCREEN_WIDTH,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  baseLine: {
    position: 'absolute',
    width: SCREEN_WIDTH * 0.8,
    height: 2,
  },
  heartbeatLine: {
    position: 'absolute',
    width: 4,
    borderRadius: 2,
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 0.8,
    shadowRadius: 4,
    elevation: 8,
  },
  sweepLine: {
    position: 'absolute',
    width: 100,
    height: 2,
    opacity: 0.6,
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 1,
    shadowRadius: 8,
    elevation: 10,
  },
}); 