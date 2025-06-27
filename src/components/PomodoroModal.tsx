import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Easing,
  Alert,
} from 'react-native';
import { X, Play, Pause, RotateCcw } from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';

type PomodoroModalProps = {
  visible: boolean;
  onClose: () => void;
  taskTitle: string;
  estimatedMinutes?: number;
};

export default function PomodoroModal({ visible, onClose, taskTitle, estimatedMinutes = 25 }: PomodoroModalProps) {
  const { currentTheme } = useTheme();
  const [timeLeft, setTimeLeft] = useState(estimatedMinutes * 60); // Convert to seconds
  const [isRunning, setIsRunning] = useState(false);
  const [initialTime] = useState(estimatedMinutes * 60);
  const animatedValue = useRef(new Animated.Value(0)).current;
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isRunning && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            setIsRunning(false);
            Alert.alert('Time\'s up!', 'Your focus session is complete.');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, timeLeft]);

  useEffect(() => {
    const progress = 1 - (timeLeft / initialTime);
    Animated.timing(animatedValue, {
      toValue: progress,
      duration: 200,
      easing: Easing.linear,
      useNativeDriver: false,
    }).start();
  }, [timeLeft, initialTime, animatedValue]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    setIsRunning(!isRunning);
  };

  const handleReset = () => {
    setIsRunning(false);
    setTimeLeft(initialTime);
    animatedValue.setValue(0);
  };

  const handleClose = () => {
    setIsRunning(false);
    onClose();
  };

  const progress = timeLeft / initialTime;

  return (
    <Modal
      visible={visible}
      animationType="fade"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <View style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
            <X color={currentTheme.colors.textSecondary} size={24} />
          </TouchableOpacity>
        </View>

        {/* Content */}
        <View style={styles.content}>
          <View style={styles.titleSection}>
            <Text style={[styles.taskTitle, { color: currentTheme.colors.textPrimary }]}>
              {taskTitle}
            </Text>
            <Text style={[styles.subtitle, { color: currentTheme.colors.textSecondary }]}>
              Focus Session
            </Text>
          </View>

          {/* Timer Circle */}
          <View style={styles.timerContainer}>
            <View style={[styles.timerCircle, { borderColor: currentTheme.colors.surface }]}>
              <Animated.View
                style={[
                  styles.progressCircle,
                  {
                    borderColor: currentTheme.colors.primary,
                    transform: [
                      {
                        rotate: animatedValue.interpolate({
                          inputRange: [0, 1],
                          outputRange: ['0deg', '360deg'],
                        }),
                      },
                    ],
                  },
                ]}
              />
              <View style={styles.innerCircle}>
                <Text style={[styles.timeText, { color: currentTheme.colors.textPrimary }]}>
                  {formatTime(timeLeft)}
                </Text>
              </View>
            </View>
          </View>

          {/* Controls */}
          <View style={styles.controls}>
            <TouchableOpacity
              style={[styles.controlButton, { backgroundColor: currentTheme.colors.surface }]}
              onPress={handleReset}
            >
              <RotateCcw size={24} color={currentTheme.colors.textSecondary} />
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.playButton, { backgroundColor: currentTheme.colors.primary }]}
              onPress={handlePlayPause}
            >
              {isRunning ? (
                <Pause size={32} color="white" />
              ) : (
                <Play size={32} color="white" />
              )}
            </TouchableOpacity>

            <View style={styles.spacer} />
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 20,
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    paddingBottom: 100,
  },
  titleSection: {
    alignItems: 'center',
    marginBottom: 80,
  },
  taskTitle: {
    fontSize: 24,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
    lineHeight: 30,
  },
  subtitle: {
    fontSize: 16,
    fontWeight: '500',
    opacity: 0.7,
  },
  timerContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 80,
  },
  timerCircle: {
    width: 240,
    height: 240,
    borderRadius: 120,
    borderWidth: 8,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  progressCircle: {
    position: 'absolute',
    width: 240,
    height: 240,
    borderRadius: 120,
    borderWidth: 8,
    borderTopColor: 'transparent',
    borderRightColor: 'transparent',
    borderBottomColor: 'transparent',
  },
  innerCircle: {
    width: 200,
    height: 200,
    borderRadius: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeText: {
    fontSize: 42,
    fontWeight: '300',
    letterSpacing: 2,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 40,
  },
  controlButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  spacer: {
    width: 56,
  },
}); 