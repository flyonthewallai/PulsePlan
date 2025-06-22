import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Dimensions, Text } from 'react-native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface PulseLoadingScreenProps {
  visible?: boolean;
  text?: string;
}

export default function PulseLoadingScreen({ 
  visible = true, 
  text = 'Loading...' 
}: PulseLoadingScreenProps) {
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const sweepAnim = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;
  const textOpacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      // Heartbeat pulse animation (realistic ECG pattern)
      const createHeartbeat = () => {
        return Animated.sequence([
          // P wave (small)
          Animated.timing(pulseAnim, {
            toValue: 0.2,
            duration: 50,
            useNativeDriver: false,
          }),
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 50,
            useNativeDriver: false,
          }),
          // PR interval
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 100,
            useNativeDriver: false,
          }),
          // QRS complex (main spike)
          Animated.timing(pulseAnim, {
            toValue: -0.3,
            duration: 30,
            useNativeDriver: false,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 40,
            useNativeDriver: false,
          }),
          Animated.timing(pulseAnim, {
            toValue: -0.2,
            duration: 30,
            useNativeDriver: false,
          }),
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 40,
            useNativeDriver: false,
          }),
          // T wave
          Animated.timing(pulseAnim, {
            toValue: 0.15,
            duration: 80,
            useNativeDriver: false,
          }),
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 80,
            useNativeDriver: false,
          }),
          // Rest period
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 600,
            useNativeDriver: false,
          }),
        ]);
      };

      // Sweeping scanner line
      const sweepAnimation = Animated.loop(
        Animated.timing(sweepAnim, {
          toValue: 1,
          duration: 3000,
          useNativeDriver: true,
        })
      );

      // Glow effect
      const glowAnimation = Animated.loop(
        Animated.sequence([
          Animated.timing(glowAnim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(glowAnim, {
            toValue: 0,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      );

      // Text fade in
      const textAnimation = Animated.timing(textOpacityAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      });

      // Start all animations
      const heartbeatLoop = Animated.loop(createHeartbeat());
      heartbeatLoop.start();
      sweepAnimation.start();
      glowAnimation.start();
      textAnimation.start();

      return () => {
        heartbeatLoop.stop();
        sweepAnimation.stop();
        glowAnimation.stop();
        textAnimation.stop();
      };
    }
  }, [visible, pulseAnim, sweepAnim, glowAnim, textOpacityAnim]);

  if (!visible) return null;

  const sweepTranslateX = sweepAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-200, SCREEN_WIDTH + 200],
  });

  const glowOpacity = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.8],
  });

  const pulseHeight = pulseAnim.interpolate({
    inputRange: [-0.3, 0, 1],
    outputRange: [60, 2, 40],
  });

  const pulseY = pulseAnim.interpolate({
    inputRange: [-0.3, 0, 1],
    outputRange: [30, 0, -20],
  });

  return (
    <View style={styles.container}>
      {/* Background glow effect */}
      <Animated.View
        style={[
          styles.backgroundGlow,
          {
            opacity: glowOpacity,
          },
        ]}
      />

      {/* Main heartbeat line container */}
      <View style={styles.heartbeatContainer}>
        {/* Grid lines for medical monitor effect */}
        <View style={styles.gridContainer}>
          {Array.from({ length: 20 }).map((_, i) => (
            <View key={`v-${i}`} style={[styles.gridLineVertical, { left: (i * SCREEN_WIDTH) / 20 }]} />
          ))}
          {Array.from({ length: 8 }).map((_, i) => (
            <View key={`h-${i}`} style={[styles.gridLineHorizontal, { top: (i * 80) / 8 }]} />
          ))}
        </View>

        {/* Base line */}
        <View style={styles.baseLine} />
        
        {/* Heartbeat pulse */}
        <Animated.View
          style={[
            styles.heartbeatLine,
            {
              height: pulseHeight,
              transform: [{ translateY: pulseY }],
            },
          ]}
        />
        
        {/* Sweeping scanner line */}
        <Animated.View
          style={[
            styles.sweepLine,
            {
              transform: [{ translateX: sweepTranslateX }],
            },
          ]}
        />

        {/* Scanner line glow */}
        <Animated.View
          style={[
            styles.sweepGlow,
            {
              transform: [{ translateX: sweepTranslateX }],
            },
          ]}
        />
      </View>

      {/* Loading text */}
      <Animated.Text
        style={[
          styles.loadingText,
          {
            opacity: textOpacityAnim,
          },
        ]}
      >
        {text}
      </Animated.Text>

      {/* Pulse indicator dots */}
      <View style={styles.dotsContainer}>
        {[0, 1, 2].map((index) => (
          <Animated.View
            key={index}
            style={[
              styles.dot,
              {
                opacity: glowAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0.3, 1],
                }),
                transform: [
                  {
                    scale: glowAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0.8, 1.2],
                    }),
                  },
                ],
              },
            ]}
          />
        ))}
      </View>
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
  backgroundGlow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
  },
  heartbeatContainer: {
    width: SCREEN_WIDTH,
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    marginBottom: 40,
  },
  gridContainer: {
    position: 'absolute',
    width: '100%',
    height: '100%',
  },
  gridLineVertical: {
    position: 'absolute',
    width: 1,
    height: '100%',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  gridLineHorizontal: {
    position: 'absolute',
    width: '100%',
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  baseLine: {
    position: 'absolute',
    width: SCREEN_WIDTH * 0.9,
    height: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  heartbeatLine: {
    position: 'absolute',
    width: 3,
    backgroundColor: '#FFFFFF',
    borderRadius: 1.5,
    shadowColor: '#FFFFFF',
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 1,
    shadowRadius: 6,
    elevation: 12,
  },
  sweepLine: {
    position: 'absolute',
    width: 2,
    height: '100%',
    backgroundColor: '#00FF88',
    shadowColor: '#00FF88',
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 1,
    shadowRadius: 8,
    elevation: 15,
  },
  sweepGlow: {
    position: 'absolute',
    width: 20,
    height: '100%',
    backgroundColor: 'rgba(0, 255, 136, 0.3)',
    shadowColor: '#00FF88',
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 0.8,
    shadowRadius: 15,
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '300',
    letterSpacing: 2,
    textAlign: 'center',
    marginTop: 20,
  },
  dotsContainer: {
    flexDirection: 'row',
    marginTop: 30,
    gap: 8,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#FFFFFF',
    shadowColor: '#FFFFFF',
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 0.8,
    shadowRadius: 4,
  },
}); 