import React from 'react';
import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { colors } from '../constants/theme';

type OnboardingProgressProps = {
  steps: number;
  currentStep: number;
};

export default function OnboardingProgress({ steps, currentStep }: OnboardingProgressProps) {
  return (
    <View style={styles.container}>
      {Array.from({ length: steps }).map((_, index) => (
        <View
          key={index}
          style={[
            styles.step,
            index === currentStep && styles.activeStep,
            index < currentStep && styles.completedStep,
          ]}
        >
          {index <= currentStep && (
            <LinearGradient
              colors={[colors.primaryBlue, colors.accentPurple]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={[
                styles.stepGradient,
                { width: index === currentStep ? '100%' : '100%' }
              ]}
            />
          )}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 8,
  },
  step: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 2,
    marginHorizontal: 2,
    overflow: 'hidden',
  },
  activeStep: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  completedStep: {
    backgroundColor: colors.primaryBlue,
  },
  stepGradient: {
    height: '100%',
  },
});