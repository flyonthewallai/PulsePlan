import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export const Onboarding = ({
  onComplete
}) => {
  const [step, setStep] = useState(0);
  const [animation, setAnimation] = useState('');
  const steps = [{
    title: 'Welcome to PulsePlan',
    description: 'Your AI-powered academic scheduling assistant',
    image: 'https://images.unsplash.com/photo-1606327054629-64c8b0fd6e4f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80',
    action: 'Get Started'
  }, {
    title: 'Connect Canvas',
    description: 'Let PulsePlan sync with your Canvas assignments to keep track of due dates',
    image: 'https://images.unsplash.com/photo-1606327054629-64c8b0fd6e4f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80',
    action: 'Connect'
  }, {
    title: 'Connect Calendar',
    description: "Sync your calendar so PulsePlan knows when you're available",
    image: 'https://images.unsplash.com/photo-1606327054629-64c8b0fd6e4f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80',
    action: 'Connect'
  }, {
    title: 'Set Preferences',
    description: 'Tell PulsePlan when you prefer to study and how you like to work',
    image: 'https://images.unsplash.com/photo-1606327054629-64c8b0fd6e4f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80',
    action: 'Finish'
  }];

  const nextStep = () => {
    if (step < steps.length - 1) {
      setAnimation('slide-out');
      setTimeout(() => {
        setStep(step + 1);
        setAnimation('slide-in');
      }, 300);
    } else {
      onComplete();
    }
  };

  return (
    <View style={[styles.container, styles.gradient]}>
      <View style={[styles.content, animation === 'slide-out' ? styles.slideOut : styles.slideIn]}>
        <View style={styles.logoContainer}>
          <View style={styles.logoOuter}>
            <View style={styles.logoInner}>
              <Text style={styles.logoText}>R</Text>
            </View>
          </View>
        </View>
        <Text style={styles.title}>{steps[step].title}</Text>
        <Text style={styles.description}>{steps[step].description}</Text>
        <View style={styles.dotsContainer}>
          {steps.map((_, i) => (
            <View
              key={i}
              style={[
                styles.dot,
                i === step ? styles.activeDot : styles.inactiveDot
              ]}
            />
          ))}
        </View>
        <TouchableOpacity style={styles.button} onPress={nextStep}>
          <Text style={styles.buttonText}>{steps[step].action}</Text>
          <Ionicons name="arrow-forward" size={16} color="#0D1B2A" style={styles.buttonIcon} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  gradient: {
    backgroundColor: '#0D1B2A',
  },
  content: {
    width: '100%',
    maxWidth: 320,
  },
  slideOut: {
    transform: [{ translateX: -20 }],
    opacity: 0,
  },
  slideIn: {
    transform: [{ translateX: 0 }],
    opacity: 1,
  },
  logoContainer: {
    marginBottom: 32,
    alignItems: 'center',
  },
  logoOuter: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0D1B2A',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 32,
  },
  dotsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 40,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginHorizontal: 4,
  },
  activeDot: {
    backgroundColor: '#FFFFFF',
  },
  inactiveDot: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  button: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    color: '#0D1B2A',
    fontSize: 16,
    fontWeight: '500',
  },
  buttonIcon: {
    marginLeft: 8,
  },
});