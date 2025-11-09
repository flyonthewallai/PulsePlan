import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useAgentStatus } from '../hooks/useAgentStatus';
import { useTheme } from '../contexts/ThemeContext';
import AnimatedThinkingText from './AnimatedThinkingText';

interface AgentStatusIndicatorProps {
  userId: string | null;
  style?: any;
}

const AgentStatusIndicator: React.FC<AgentStatusIndicatorProps> = ({ userId, style }) => {
  const { status, isConnected, error } = useAgentStatus(userId);
  const { currentTheme } = useTheme();
  const spinValue = React.useRef(new Animated.Value(0)).current;
  const waveValue = React.useRef(new Animated.Value(0)).current;

  // Spinning animation for active status
  React.useEffect(() => {
    if (status?.status === 'active') {
      const spinAnimation = Animated.loop(
        Animated.timing(spinValue, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        })
      );
      spinAnimation.start();
      return () => spinAnimation.stop();
    }
  }, [status?.status, spinValue]);

  // Wave animation for all states
  React.useEffect(() => {
    const waveAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(waveValue, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(waveValue, {
          toValue: 0,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    );
    waveAnimation.start();
    return () => waveAnimation.stop();
  }, [waveValue]);

  const spin = spinValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const waveOpacity = waveValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.8],
  });

  const waveScale = waveValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0.95, 1.05],
  });

  // Don't show anything if not connected or no user
  if (!userId || !isConnected) {
    return null;
  }

  // Show error state
  if (error) {
    return (
      <Animated.View style={[
        styles.container, 
        styles.errorContainer, 
        style,
        {
          opacity: waveOpacity,
          transform: [{ scale: waveScale }]
        }
      ]}>
        <Text style={[styles.errorIcon]}>⚠️</Text>
        <Text style={[styles.errorText, { color: '#FFFFFF' }]}>
          Connection error
        </Text>
      </Animated.View>
    );
  }

  // Show thinking state (default when idle or no status)
  if (!status || status.status === 'idle') {
    return (
      <Animated.View style={[
        styles.container, 
        styles.thinkingContainer, 
        style,
        {
          opacity: waveOpacity,
          transform: [{ scale: waveScale }]
        }
      ]}>
        <View style={[styles.statusDot, styles.thinkingDot, { backgroundColor: currentTheme.colors.primary }]} />
        <AnimatedThinkingText 
          text="Pulse is thinking..."
          textStyle={[styles.statusText, { color: currentTheme.colors.textPrimary }]}
        />
      </Animated.View>
    );
  }

  // Show error state
  if (status.status === 'error') {
    return (
      <Animated.View style={[
        styles.container, 
        styles.errorContainer, 
        style,
        {
          opacity: waveOpacity,
          transform: [{ scale: waveScale }]
        }
      ]}>
        <Text style={[styles.errorIcon]}>⚠️</Text>
        <Text style={[styles.statusText, { color: '#FFFFFF' }]}>
          Pulse encountered an error
          {status.currentTool && ` with ${status.currentTool}`}
        </Text>
      </Animated.View>
    );
  }

  // Show active state
  return (
    <Animated.View style={[
      styles.container, 
      styles.activeContainer, 
      style,
      {
        opacity: waveOpacity,
        transform: [{ scale: waveScale }]
      }
    ]}>
      <Animated.View style={[
        styles.spinner,
        { 
          borderColor: currentTheme.colors.primary,
          transform: [{ rotate: spin }] 
        }
      ]} />
      <View style={styles.textContainer}>
        <Text style={[styles.statusText, { color: currentTheme.colors.textPrimary }]}>
          Pulse is using {status.currentTool}...
        </Text>
        {status.toolHistory[0]?.message && (
          <Text style={[styles.messageText, { color: currentTheme.colors.textSecondary }]}>
            {status.toolHistory[0].message}
          </Text>
        )}
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    marginHorizontal: 16,
    marginVertical: 8,
  },
  thinkingContainer: {
    backgroundColor: 'rgba(0, 122, 255, 0.08)',
  },
  activeContainer: {
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
  },
  errorContainer: {
    backgroundColor: '#E53E3E',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  thinkingDot: {
    opacity: 0.8,
  },
  spinner: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
    borderTopColor: 'transparent',
    marginRight: 12,
  },
  textContainer: {
    flex: 1,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  messageText: {
    fontSize: 12,
    marginTop: 2,
    opacity: 0.8,
  },
  errorText: {
    fontSize: 14,
    fontWeight: '500',
  },
  errorIcon: {
    fontSize: 16,
    marginRight: 8,
  },
});

export default AgentStatusIndicator; 