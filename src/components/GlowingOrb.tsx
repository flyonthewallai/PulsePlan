import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { colors } from '../constants/theme';

// Shared animation values for synchronization across all orbs
const sharedGlowAnim = new Animated.Value(0.4);
const sharedPulseAnim = new Animated.Value(1);
const sharedFloatAnim = new Animated.Value(0);

// Track if animations are already running
let animationsStarted = false;
let animationLoops: Animated.CompositeAnimation[] = [];

interface GlowingOrbProps {
  size?: 'sm' | 'ms' | 'md' | 'lg';
  color?: 'lavender' | 'coral' | 'blue' | string;
  glowIntensity?: number; // 0.1 to 1.0, controls radius/size
  glowOpacity?: number; // 0.1 to 2.0, controls opacity/visual intensity
  style?: any;
}

export const GlowingOrb = ({ size = 'md', color = 'blue', glowIntensity = 1.0, glowOpacity = 1.0, style }: GlowingOrbProps) => {
  // Use shared animation values instead of creating new ones
  const glowAnim = sharedGlowAnim;
  const pulseAnim = sharedPulseAnim;
  const floatAnim = sharedFloatAnim;

  useEffect(() => {
    // Only start animations once for the first orb instance
    if (!animationsStarted) {
      const createGlow = () => {
        return Animated.sequence([
          Animated.timing(glowAnim, {
            toValue: 0.7,
            duration: 4000,
            useNativeDriver: false,
          }),
          Animated.timing(glowAnim, {
            toValue: 0.3,
            duration: 4000,
            useNativeDriver: false,
          }),
        ]);
      };

      const createPulse = () => {
        return Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.04,
            duration: 3000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 3000,
            useNativeDriver: true,
          }),
        ]);
      };

      const createFloat = () => {
        return Animated.sequence([
          Animated.timing(floatAnim, {
            toValue: 1,
            duration: 5000,
            useNativeDriver: true,
          }),
          Animated.timing(floatAnim, {
            toValue: 0,
            duration: 5000,
            useNativeDriver: true,
          }),
        ]);
      };

      const glowLoop = Animated.loop(createGlow());
      const pulseLoop = Animated.loop(createPulse());
      const floatLoop = Animated.loop(createFloat());

      animationLoops = [glowLoop, pulseLoop, floatLoop];

      glowLoop.start();
      pulseLoop.start();
      floatLoop.start();

      animationsStarted = true;
    }

    // Cleanup function - only stop animations when the last orb is unmounted
    return () => {
      // This is a simplified cleanup - in a real app you might want to track orb instances
      // For now, we'll let the animations continue running
    };
  }, []);

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return { width: 32, height: 32 };
      case 'ms':
        return { width: 48, height: 48 };
      case 'md':
        return { width: 64, height: 64 };
      case 'lg':
        return { width: 96, height: 96 };
      default:
        return { width: 64, height: 64 };
    }
  };

  const getColorStyles = () => {
    switch (color) {
      case 'lavender':
        return {
          outerGlow: colors.accentPurple + '08', // 3% opacity
          middleGlow: colors.accentPurple + '12', // 7% opacity
          innerGlow: colors.accentPurple + '20', // 12% opacity
          core: colors.accentPurple,
          shadowColor: colors.accentPurple,
        };
      case 'coral':
        return {
          outerGlow: '#FF6B6B08', // 3% opacity
          middleGlow: '#FF6B6B12', // 7% opacity
          innerGlow: '#FF6B6B20', // 12% opacity
          core: '#FF6B6B',
          shadowColor: '#FF6B6B',
        };
      case 'blue':
        return {
          outerGlow: colors.primaryBlue + '08', // 3% opacity
          middleGlow: colors.primaryBlue + '12', // 7% opacity
          innerGlow: colors.primaryBlue + '20', // 12% opacity
          core: colors.primaryBlue,
          shadowColor: colors.primaryBlue,
        };
      default:
        // Handle custom color strings
        const customColor = typeof color === 'string' ? color : colors.primaryBlue;
        return {
          outerGlow: customColor + '08', // 3% opacity
          middleGlow: customColor + '12', // 7% opacity
          innerGlow: customColor + '20', // 12% opacity
          core: customColor,
          shadowColor: customColor,
        };
    }
  };

  const sizeStyles = getSizeStyles();
  const colorStyles = getColorStyles();
  const coreSize = Math.floor(Math.min(sizeStyles.width, sizeStyles.height) * 0.25);

  return (
    <Animated.View
      style={[
        styles.container,
        sizeStyles,
        {
          transform: [
            { scale: pulseAnim },
            { 
              translateY: floatAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0, -1],
              })
            }
          ],
        },
        style,
      ]}
    >
      {/* Outermost atmospheric glow */}
      <Animated.View
        style={[
          styles.glowLayer,
          {
            width: sizeStyles.width * (1.8 * glowIntensity),
            height: sizeStyles.height * (1.8 * glowIntensity),
            backgroundColor: colorStyles.outerGlow,
            shadowColor: colorStyles.shadowColor,
            shadowRadius: 20 * glowIntensity,
            shadowOpacity: glowAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0.05 * glowOpacity, 0.15 * glowOpacity],
            }),
            opacity: glowAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0.2 * glowOpacity, 0.4 * glowOpacity],
            }),
          },
        ]}
      />

      {/* Large diffused glow */}
      <Animated.View
        style={[
          styles.glowLayer,
          {
            width: sizeStyles.width * (1.4 * glowIntensity),
            height: sizeStyles.height * (1.4 * glowIntensity),
            backgroundColor: colorStyles.middleGlow,
            shadowColor: colorStyles.shadowColor,
            shadowRadius: 12 * glowIntensity,
            shadowOpacity: glowAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0.1 * glowOpacity, 0.25 * glowOpacity],
            }),
            opacity: glowAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0.3 * glowOpacity, 0.5 * glowOpacity],
            }),
          },
        ]}
      />
      
      {/* Medium glow */}
      <Animated.View
        style={[
          styles.glowLayer,
          {
            width: sizeStyles.width * (1.1 * glowIntensity),
            height: sizeStyles.height * (1.1 * glowIntensity),
            backgroundColor: colorStyles.innerGlow,
            shadowColor: colorStyles.shadowColor,
            shadowRadius: 8 * glowIntensity,
            shadowOpacity: glowAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0.15 * glowOpacity, 0.3 * glowOpacity],
            }),
            opacity: glowAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0.4 * glowOpacity, 0.6 * glowOpacity],
            }),
          },
        ]}
      />

      {/* Inner bright glow */}
      <Animated.View
        style={[
          styles.glowLayer,
          sizeStyles,
          {
            backgroundColor: colorStyles.core,
            shadowColor: colorStyles.shadowColor,
            shadowRadius: 4 * glowIntensity,
            shadowOpacity: 0.4 * glowOpacity,
            opacity: glowAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0.5 * glowOpacity, 0.7 * glowOpacity],
            }),
          },
        ]}
      />

      {/* Solid core */}
      <View
        style={[
          styles.core,
          {
            width: coreSize,
            height: coreSize,
            backgroundColor: colorStyles.core,
            shadowColor: colorStyles.shadowColor,
          },
        ]}
      />
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 1000,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  glowLayer: {
    position: 'absolute',
    borderRadius: 1000,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  core: {
    borderRadius: 1000,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 2,
    elevation: 4,
  },
}); 