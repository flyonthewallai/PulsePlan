import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ScrollView,
  Dimensions,
} from 'react-native';
import { X, Flame, Trophy, Target, Calendar, TrendingUp, Clock, Award } from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  useAnimatedProps,
  withTiming,
  Easing,
  withDelay,
} from 'react-native-reanimated';
import { Svg, Circle } from 'react-native-svg';

import { useTheme } from '../contexts/ThemeContext';
import { useStreak } from '../contexts/StreakContext';
import { useTasks } from '../contexts/TaskContext';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface StreakModalProps {
  visible: boolean;
  onClose: () => void;
}

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  delay?: number;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, icon, color, delay = 0 }) => {
  const { currentTheme } = useTheme();

  return (
    <View style={[styles.statCard, { backgroundColor: currentTheme.colors.surface }]}>
      <View style={styles.statCardHeader}>
        <Text style={[styles.statTitle, { color: currentTheme.colors.textSecondary }]}>{title}</Text>
      </View>
      <Text style={[styles.statValue, { color: currentTheme.colors.textPrimary }]}>{value}</Text>
      {subtitle && (
        <Text style={[styles.statSubtitle, { color: currentTheme.colors.textSecondary }]}>{subtitle}</Text>
      )}
    </View>
  );
};

interface StreakRingProps {
  currentStreak: number;
  bestStreak: number;
  size: number;
}

const StreakRing: React.FC<StreakRingProps> = ({ currentStreak, bestStreak, size }) => {
  const { currentTheme } = useTheme();
  const progress = useSharedValue(0);
  
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  
  useEffect(() => {
    const percentage = Math.min(currentStreak / Math.max(bestStreak, 30), 1);
    progress.value = withTiming(percentage, {
      duration: 1500,
      easing: Easing.bezier(0.25, 0.1, 0.25, 1),
    });
  }, [currentStreak, bestStreak]);
  
  const animatedProps = useAnimatedProps(() => {
    const strokeDashoffset = circumference * (1 - progress.value);
    return {
      strokeDashoffset,
    };
  });

  return (
    <View style={[styles.ringContainer, { width: size, height: size }]}>
      <Svg width={size} height={size}>
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth={12}
          fill="transparent"
        />
        <AnimatedCircle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={currentTheme.colors.primary}
          strokeWidth={12}
          strokeLinecap="round"
          strokeDasharray={circumference}
          animatedProps={animatedProps}
          fill="transparent"
          rotation="-90"
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      <View style={[styles.ringContent, { width: size, height: size }]}>
        <Flame size={24} color={currentTheme.colors.primary} />
        <Text style={[styles.ringValue, { color: currentTheme.colors.textPrimary }]}>
          {currentStreak}
        </Text>
        <Text style={[styles.ringLabel, { color: currentTheme.colors.textSecondary }]}>
          day{currentStreak !== 1 ? 's' : ''}
        </Text>
      </View>
    </View>
  );
};

export const StreakModal: React.FC<StreakModalProps> = ({ visible, onClose }) => {
  const { currentTheme } = useTheme();
  const { currentStreak } = useStreak();
  const { tasks } = useTasks();

  // Calculate streak stats (since they're not in context yet)
  const bestStreak = Math.max(currentStreak, 7); // Placeholder - could be stored in AsyncStorage
  const totalDays = 30; // Placeholder - could be calculated from first app use date

  // Calculate stats
  const completedToday = tasks.filter(task => {
    const today = new Date().toDateString();
    const taskDate = new Date(task.due_date).toDateString();
    return taskDate === today && task.status === 'completed';
  }).length;

  const totalCompleted = tasks.filter(task => task.status === 'completed').length;
  
  const thisWeekCompleted = tasks.filter(task => {
    const now = new Date();
    const weekStart = new Date(now.setDate(now.getDate() - now.getDay()));
    const taskDate = new Date(task.due_date);
    return taskDate >= weekStart && task.status === 'completed';
  }).length;

  const averagePerDay = totalDays > 0 ? Math.round(totalCompleted / totalDays * 10) / 10 : 0;

  const getStreakMessage = () => {
    if (currentStreak >= 30) return "Incredible dedication!";
    if (currentStreak >= 14) return "You're on fire!";
    if (currentStreak >= 7) return "Building momentum!";
    if (currentStreak >= 3) return "Great start!";
    return "Every day counts!";
  };

  const getStreakLevel = () => {
    if (currentStreak >= 30) return "Master";
    if (currentStreak >= 14) return "Expert";
    if (currentStreak >= 7) return "Committed";
    if (currentStreak >= 3) return "Getting Started";
    return "Beginner";
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={currentTheme.colors.background} />
        
        {/* Header */}
        <View style={[styles.header, { backgroundColor: currentTheme.colors.background }]}>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <X color={currentTheme.colors.textPrimary} size={24} />
          </TouchableOpacity>
          
          <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
            Your Streak
          </Text>
          
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Hero Section */}
          <View style={styles.heroSection}>
            <StreakRing
              currentStreak={currentStreak}
              bestStreak={bestStreak}
              size={120}
            />
            
            <View style={styles.heroText}>
              <Text style={[styles.streakLevel, { color: currentTheme.colors.primary }]}>
                {getStreakLevel()}
              </Text>
              <Text style={[styles.streakMessage, { color: currentTheme.colors.textSecondary }]}>
                {getStreakMessage()}
              </Text>
            </View>
          </View>

          {/* Stats Grid */}
          <View style={styles.statsSection}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
              Your Analytics
            </Text>
            
            <View style={styles.statsGrid}>
                           <StatCard
               title="Best Streak"
               value={bestStreak.toString()}
               subtitle="days in a row"
               icon={<Trophy size={20} color={currentTheme.colors.accent} />}
               color={currentTheme.colors.accent}
             />
             
             <StatCard
               title="Today"
               value={completedToday.toString()}
               subtitle="tasks completed"
               icon={<Target size={20} color="#34D399" />}
               color="#34D399"
             />
             
             <StatCard
               title="This Week"
               value={thisWeekCompleted.toString()}
               subtitle="tasks completed"
               icon={<Calendar size={20} color="#60A5FA" />}
               color="#60A5FA"
             />
             
             <StatCard
               title="Daily Average"
               value={averagePerDay.toString()}
               subtitle="tasks per day"
               icon={<TrendingUp size={20} color="#F59E0B" />}
               color="#F59E0B"
             />
             
             <StatCard
               title="Total Days"
               value={totalDays.toString()}
               subtitle="using PulsePlan"
               icon={<Clock size={20} color="#8B5CF6" />}
               color="#8B5CF6"
             />
             
             <StatCard
               title="Total Completed"
               value={totalCompleted.toString()}
               subtitle="all time"
               icon={<Award size={20} color="#EF4444" />}
               color="#EF4444"
             />
            </View>
          </View>

        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  placeholder: {
    width: 32,
  },
  content: {
    flex: 1,
  },
  heroSection: {
    alignItems: 'center',
    paddingVertical: 24,
    paddingHorizontal: 20,
  },
  ringContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    position: 'relative',
  },
  ringContent: {
    position: 'absolute',
    top: 0,
    left: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ringValue: {
    fontSize: 28,
    fontWeight: '700',
    marginTop: 2,
  },
  ringLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  heroText: {
    alignItems: 'center',
  },
  streakLevel: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 4,
  },
  streakMessage: {
    fontSize: 16,
    textAlign: 'center',
  },
  statsSection: {
    paddingHorizontal: 20,
    paddingBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 20,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: (SCREEN_WIDTH - 60) / 2,
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  statCardHeader: {
    marginBottom: 8,
  },
  statTitle: {
    fontSize: 13,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statValue: {
    fontSize: 28,
    fontWeight: '600',
    marginBottom: 4,
  },
  statSubtitle: {
    fontSize: 13,
    fontWeight: '400',
  },
  motivationSection: {
    paddingHorizontal: 20,
    paddingBottom: 32,
  },
  motivationCard: {
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  motivationTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  motivationText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
}); 