import React, { useEffect, useRef } from 'react';
import { View, Text, Animated, StyleSheet } from 'react-native';

interface AnimatedThinkingTextProps {
  text?: string;
  textStyle?: any;
}

export default function AnimatedThinkingText({ 
  text = "Pulse is thinking...", 
  textStyle = {} 
}: AnimatedThinkingTextProps) {
  const animatedValues = useRef(
    text.split('').map(() => new Animated.Value(0.3))
  ).current;

  useEffect(() => {
    // Reset all values to dim state initially
    animatedValues.forEach(value => value.setValue(0.3));
    
    const createWaveAnimation = () => {
      // Create parallel animations for all characters with staggered timing
      const parallelAnimations = animatedValues.map((value, index) => {
        return Animated.loop(
          Animated.sequence([
            // Initial delay based on character position
            Animated.delay(index * 60),
            // Smooth fade in
            Animated.timing(value, {
              toValue: 1,
              duration: 400,
              useNativeDriver: false,
            }),
            // Smooth fade out
            Animated.timing(value, {
              toValue: 0.3,
              duration: 400,
              useNativeDriver: false,
            }),
            // Wait for wave to complete and pause before next cycle
            Animated.delay((animatedValues.length - index - 1) * 60 + 800),
          ])
        );
      });
      
      return Animated.parallel(parallelAnimations);
    };

    const waveAnimation = createWaveAnimation();
    waveAnimation.start();

    // Cleanup function
    return () => {
      waveAnimation.stop();
      // Reset values when cleaning up
      animatedValues.forEach(value => value.setValue(0.3));
    };
  }, [text]);

  return (
    <View style={styles.container}>
      {text.split('').map((char, index) => (
        <Animated.Text
          key={index}
          style={[
            textStyle,
            {
              opacity: animatedValues[index],
            },
          ]}
        >
          {char}
        </Animated.Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
}); 