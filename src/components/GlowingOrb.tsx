import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { colors } from '../constants/theme';

interface GlowingOrbProps {
  size?: 'sm' | 'ms' | 'md' | 'lg';
  color?: 'lavender' | 'coral' | 'blue' | string;
  glowIntensity?: number; // 0.1 to 1.0, controls radius/size
  glowOpacity?: number; // 0.1 to 2.0, controls opacity/visual intensity
  style?: any;
}

export const GlowingOrb = ({ size = 'md', color = 'blue', glowIntensity = 1.0, glowOpacity = 1.0, style }: GlowingOrbProps) => {
  const glowAnim = useRef(new Animated.Value(0.4)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const floatAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const createGlow = () => {
      return Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 0.8,
          duration: 3000,
          useNativeDriver: false,
        }),
        Animated.timing(glowAnim, {
          toValue: 0.4,
          duration: 3000,
          useNativeDriver: false,
        }),
      ]);
    };

    const createPulse = () => {
      return Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.08,
          duration: 2500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2500,
          useNativeDriver: true,
        }),
      ]);
    };

    const createFloat = () => {
      return Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: 1,
          duration: 4000,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 4000,
          useNativeDriver: true,
        }),
      ]);
    };

    const glowLoop = Animated.loop(createGlow());
    const pulseLoop = Animated.loop(createPulse());
    const floatLoop = Animated.loop(createFloat());

    glowLoop.start();
    pulseLoop.start();
    floatLoop.start();

    return () => {
      glowLoop.stop();
      pulseLoop.stop();
      floatLoop.stop();
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
          outerGlow: colors.accentPurple + '15', // 8% opacity
          middleGlow: colors.accentPurple + '25', // 15% opacity
          innerGlow: colors.accentPurple + '40', // 25% opacity
          core: colors.accentPurple,
          shadowColor: colors.accentPurple,
        };
      case 'coral':
        return {
          outerGlow: '#FF6B6B15', // 8% opacity
          middleGlow: '#FF6B6B25', // 15% opacity
          innerGlow: '#FF6B6B40', // 25% opacity
          core: '#FF6B6B',
          shadowColor: '#FF6B6B',
        };
      case 'blue':
        return {
          outerGlow: colors.primaryBlue + '15', // 8% opacity
          middleGlow: colors.primaryBlue + '25', // 15% opacity
          innerGlow: colors.primaryBlue + '40', // 25% opacity
          core: colors.primaryBlue,
          shadowColor: colors.primaryBlue,
        };
      default:
        // Handle custom color strings
        const customColor = typeof color === 'string' ? color : colors.primaryBlue;
        return {
          outerGlow: customColor + '15', // 8% opacity
          middleGlow: customColor + '25', // 15% opacity
          innerGlow: customColor + '40', // 25% opacity
          core: customColor,
          shadowColor: customColor,
        };
    }
  };

  const sizeStyles = getSizeStyles();
  const colorStyles = getColorStyles();
  const coreSize = Math.floor(Math.min(sizeStyles.width, sizeStyles.height) * 0.3);

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
                outputRange: [0, -2],
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
            width: sizeStyles.width * (2.5 * glowIntensity),
            height: sizeStyles.height * (2.5 * glowIntensity),
            backgroundColor: colorStyles.outerGlow,
            shadowColor: colorStyles.shadowColor,
            shadowRadius: 40 * glowIntensity,
            shadowOpacity: glowAnim.interpolate({
              inputRange: [0.4, 0.8],
              outputRange: [0.1 * glowOpacity, 0.3 * glowOpacity],
            }),
            opacity: glowAnim.interpolate({
              inputRange: [0.4, 0.8],
              outputRange: [0.3 * glowOpacity, 0.6 * glowOpacity],
            }),
          },
        ]}
      />

      {/* Large diffused glow */}
      <Animated.View
        style={[
          styles.glowLayer,
          {
            width: sizeStyles.width * (1.8 * glowIntensity),
            height: sizeStyles.height * (1.8 * glowIntensity),
            backgroundColor: colorStyles.middleGlow,
            shadowColor: colorStyles.shadowColor,
            shadowRadius: 25 * glowIntensity,
            shadowOpacity: glowAnim.interpolate({
              inputRange: [0.4, 0.8],
              outputRange: [0.2 * glowOpacity, 0.5 * glowOpacity],
            }),
            opacity: glowAnim.interpolate({
              inputRange: [0.4, 0.8],
              outputRange: [0.4 * glowOpacity, 0.7 * glowOpacity],
            }),
          },
        ]}
      />
      
      {/* Medium glow */}
      <Animated.View
        style={[
          styles.glowLayer,
          {
            width: sizeStyles.width * (1.3 * glowIntensity),
            height: sizeStyles.height * (1.3 * glowIntensity),
            backgroundColor: colorStyles.innerGlow,
            shadowColor: colorStyles.shadowColor,
            shadowRadius: 15 * glowIntensity,
            shadowOpacity: glowAnim.interpolate({
              inputRange: [0.4, 0.8],
              outputRange: [0.3 * glowOpacity, 0.6 * glowOpacity],
            }),
            opacity: glowAnim.interpolate({
              inputRange: [0.4, 0.8],
              outputRange: [0.5 * glowOpacity, 0.8 * glowOpacity],
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
            shadowRadius: 8 * glowIntensity,
            shadowOpacity: 0.8 * glowOpacity,
            opacity: glowAnim.interpolate({
              inputRange: [0.4, 0.8],
              outputRange: [0.6 * glowOpacity, 0.9 * glowOpacity],
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
    elevation: 20,
  },
  core: {
    borderRadius: 1000,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 4,
    elevation: 10,
  },
}); 