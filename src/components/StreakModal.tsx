import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  Animated,
} from 'react-native';
import { BlurView } from 'expo-blur';
import {
  X,
  Flame,
  TrendingUp,
  Calendar,
  Target,
  Award,
  Trophy,
  Zap,
  BookOpen,
  Brain,
  Code,
  Heart,
} from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../contexts/ThemeContext';

interface StreakModalProps {
  visible: boolean;
  onClose: () => void;
}

type StreakMode = 'daily' | 'weekly' | 'custom';

interface StreakData {
  currentStreak: number;
  longestStreak: number;
  activeRhythm: string;
  missedDays: number;
  totalHours: number;
  weeklyAverage: number;
}

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress?: number;
  maxProgress?: number;
}

export default function StreakModal({ visible, onClose }: StreakModalProps) {
  const { currentTheme } = useTheme();
  const [selectedMode, setSelectedMode] = useState<StreakMode>('daily');
  const [plantAnimation] = useState(new Animated.Value(0));
  const [pulseAnimation] = useState(new Animated.Value(1));

  // Mock streak data (would come from context/API in real app)
  const streakData: StreakData = {
    currentStreak: 6,
    longestStreak: 14,
    activeRhythm: 'Daily Planning',
    missedDays: 3,
    totalHours: 42,
    weeklyAverage: 8.5,
  };

  // Mock logged days for the current month
  const getMonthData = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDayOfMonth = new Date(year, month, 1).getDay();
    
    // Mock logged days (randomly for demo)
    const loggedDays = new Set([
      1, 2, 4, 5, 8, 9, 10, 12, 15, 16, 17, 19, 22, 23, 24, 26
    ]);
    
    return {
      year,
      month,
      daysInMonth,
      firstDayOfMonth,
      loggedDays,
      monthName: new Date(year, month).toLocaleDateString('en-US', { month: 'long' })
    };
  };

  // Mock subject breakdown data
  const subjectBreakdown = [
    { subject: 'CS', percentage: 35, color: '#4F8CFF', hours: 14.7 },
    { subject: 'AI', percentage: 28, color: '#8E6FFF', hours: 11.8 },
    { subject: 'Research', percentage: 22, color: '#FF6B9D', hours: 9.2 },
    { subject: 'Self-care', percentage: 15, color: '#34D399', hours: 6.3 },
  ];

  // Mock achievements
  const achievements: Achievement[] = [
    {
      id: '1',
      title: '7-Day Streak',
      description: 'Planned consistently for a week',
      icon: '🔥',
      unlocked: true,
    },
    {
      id: '2',
      title: 'Study Master',
      description: '25h planned in a week',
      icon: '🎓',
      unlocked: true,
    },
    {
      id: '3',
      title: 'Consistency King',
      description: 'Complete 30-day streak',
      icon: '👑',
      unlocked: false,
      progress: 6,
      maxProgress: 30,
    },
    {
      id: '4',
      title: 'Early Bird',
      description: '5 morning sessions',
      icon: '🌅',
      unlocked: false,
      progress: 2,
      maxProgress: 5,
    },
  ];

  useEffect(() => {
    if (visible) {
      // Animate plant growth
      Animated.timing(plantAnimation, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }).start();

      // Pulse animation for active streak
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnimation, {
            toValue: 1.1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnimation, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      plantAnimation.setValue(0);
      pulseAnimation.setValue(1);
    }
  }, [visible]);

  const getPlantStage = (streak: number) => {
    if (streak < 3) return '🌱';
    if (streak < 7) return '🌿';
    if (streak < 14) return '🪴';
    if (streak < 30) return '🌳';
    return '🌲';
  };

  const getStreakLevel = (streak: number) => {
    if (streak < 3) return 'Sprout';
    if (streak < 7) return 'Growing';
    if (streak < 14) return 'Flourishing';
    if (streak < 30) return 'Thriving';
    return 'Legendary';
  };

  const monthData = getMonthData();

  const renderMonthView = () => {
    const { daysInMonth, firstDayOfMonth, loggedDays, monthName } = monthData;
    const today = new Date().getDate();
    
    // Create array for calendar grid
    const calendarDays = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfMonth; i++) {
      calendarDays.push(null);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      calendarDays.push(day);
    }

    return (
      <View style={styles.monthContainer}>
        <Text style={[styles.monthTitle, { color: currentTheme.colors.textPrimary }]}>
          {monthName} Progress
        </Text>
        <Text style={[styles.monthSubtitle, { color: currentTheme.colors.textSecondary }]}>
          Track your daily consistency
        </Text>
        
        {/* Days of week header */}
        <View style={styles.weekHeader}>
          {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((dayLabel, index) => (
            <Text key={index} style={[styles.dayLabel, { color: currentTheme.colors.textSecondary }]}>
              {dayLabel}
            </Text>
          ))}
        </View>
        
        {/* Calendar grid */}
        <View style={styles.calendarGrid}>
          {calendarDays.map((day, index) => (
            <View key={index} style={styles.dayCell}>
              {day && (
                <>
                  <Text style={[
                    styles.dayNumber, 
                    { color: currentTheme.colors.textPrimary },
                    day === today && styles.todayNumber
                  ]}>
                    {day}
                  </Text>
                  <Text style={styles.dayStatus}>
                    {loggedDays.has(day) ? '🌱' : day <= today ? '❌' : ''}
                  </Text>
                </>
              )}
            </View>
          ))}
        </View>
        
        <View style={styles.legendContainer}>
          <View style={styles.legendItem}>
            <Text style={styles.legendEmoji}>🌱</Text>
            <Text style={[styles.legendText, { color: currentTheme.colors.textSecondary }]}>
              Logged day
            </Text>
          </View>
          <View style={styles.legendItem}>
            <Text style={styles.legendEmoji}>❌</Text>
            <Text style={[styles.legendText, { color: currentTheme.colors.textSecondary }]}>
              Missed day
            </Text>
          </View>
        </View>
      </View>
    );
  };

  const renderSubjectBreakdown = () => (
    <View style={styles.breakdownContainer}>
      <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
        Subject Breakdown
      </Text>
      <View style={styles.subjectList}>
        {subjectBreakdown.map((item, index) => (
          <View key={index} style={styles.subjectItem}>
            <View style={styles.subjectInfo}>
              <View style={[styles.subjectColor, { backgroundColor: item.color }]} />
              <Text style={[styles.subjectName, { color: currentTheme.colors.textPrimary }]}>
                {item.subject}
              </Text>
            </View>
            <View style={styles.subjectStats}>
              <Text style={[styles.subjectPercentage, { color: currentTheme.colors.textPrimary }]}>
                {item.percentage}%
              </Text>
              <Text style={[styles.subjectHours, { color: currentTheme.colors.textSecondary }]}>
                {item.hours}h
              </Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );

  const renderAchievements = () => (
    <View style={styles.achievementsContainer}>
      <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
        Achievements & Milestones
      </Text>
      <View style={styles.achievementsList}>
        {achievements.map((achievement) => (
          <View
            key={achievement.id}
            style={[
              styles.achievementItem,
              {
                backgroundColor: achievement.unlocked
                  ? `${currentTheme.colors.primary}20`
                  : currentTheme.colors.surface,
                borderColor: achievement.unlocked
                  ? currentTheme.colors.primary
                  : currentTheme.colors.border,
              },
            ]}
          >
            <Text style={styles.achievementIcon}>{achievement.icon}</Text>
            <View style={styles.achievementContent}>
              <Text style={[styles.achievementTitle, { color: currentTheme.colors.textPrimary }]}>
                {achievement.title}
              </Text>
              <Text style={[styles.achievementDescription, { color: currentTheme.colors.textSecondary }]}>
                {achievement.description}
              </Text>
              {!achievement.unlocked && achievement.progress && achievement.maxProgress && (
                <View style={styles.progressContainer}>
                  <View style={[styles.progressBar, { backgroundColor: currentTheme.colors.border }]}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width: `${(achievement.progress / achievement.maxProgress) * 100}%`,
                          backgroundColor: currentTheme.colors.primary,
                        },
                      ]}
                    />
                  </View>
                  <Text style={[styles.progressText, { color: currentTheme.colors.textSecondary }]}>
                    {achievement.progress}/{achievement.maxProgress}
                  </Text>
                </View>
              )}
            </View>
            {achievement.unlocked && (
              <View style={[styles.unlockedBadge, { backgroundColor: currentTheme.colors.primary }]}>
                <Award size={16} color="#FFFFFF" />
              </View>
            )}
          </View>
        ))}
      </View>
    </View>
  );

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <BlurView intensity={20} style={styles.overlay}>
        <View style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
          {/* Header */}
          <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <X color={currentTheme.colors.textSecondary} size={24} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
              🌿 PulsePlan Streak
            </Text>
            <View style={styles.closeButton} />
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Streak Visual */}
            <View style={styles.streakHeader}>
              <Animated.View
                style={[
                  styles.plantContainer,
                  {
                    transform: [
                      { scale: pulseAnimation },
                      { translateY: Animated.multiply(plantAnimation, -10) },
                    ],
                  },
                ]}
              >
                <Text style={styles.plantEmoji}>{getPlantStage(streakData.currentStreak)}</Text>
                <LinearGradient
                  colors={[`${currentTheme.colors.primary}40`, `${currentTheme.colors.primary}10`]}
                  style={styles.plantGlow}
                />
              </Animated.View>
              <Text style={[styles.streakLevel, { color: currentTheme.colors.textPrimary }]}>
                {getStreakLevel(streakData.currentStreak)}
              </Text>
            </View>

            {/* Streak Stats */}
            <View style={[styles.streakCard, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.streakStats}>
                <View style={styles.statItem}>
                  <Text style={styles.statEmoji}>🔥</Text>
                  <Text style={[styles.statValue, { color: currentTheme.colors.textPrimary }]}>
                    {streakData.currentStreak}
                  </Text>
                  <Text style={[styles.statLabel, { color: currentTheme.colors.textSecondary }]}>
                    Current Streak
                  </Text>
                </View>

                <View style={styles.statItem}>
                  <Text style={styles.statEmoji}>📈</Text>
                  <Text style={[styles.statValue, { color: currentTheme.colors.textPrimary }]}>
                    {streakData.longestStreak}
                  </Text>
                  <Text style={[styles.statLabel, { color: currentTheme.colors.textSecondary }]}>
                    Longest Streak
                  </Text>
                </View>

                <View style={styles.statItem}>
                  <Text style={styles.statEmoji}>🧠</Text>
                  <Text style={[styles.statValue, { color: currentTheme.colors.textPrimary }]}>
                    {streakData.activeRhythm}
                  </Text>
                  <Text style={[styles.statLabel, { color: currentTheme.colors.textSecondary }]}>
                    Active Rhythm
                  </Text>
                </View>

                <View style={styles.statItem}>
                  <Text style={styles.statEmoji}>🗓️</Text>
                  <Text style={[styles.statValue, { color: currentTheme.colors.textPrimary }]}>
                    {streakData.missedDays}
                  </Text>
                  <Text style={[styles.statLabel, { color: currentTheme.colors.textSecondary }]}>
                    Missed This Month
                  </Text>
                </View>
              </View>
            </View>

            {/* Month View */}
            <View style={[styles.monthCard, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.sectionHeader}>
                <Calendar size={20} color={currentTheme.colors.primary} />
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
                  Monthly Overview
                </Text>
              </View>
              {renderMonthView()}
            </View>

            {/* Subject Breakdown */}
            <View style={[styles.subjectCard, { backgroundColor: currentTheme.colors.surface }]}>
              {renderSubjectBreakdown()}
            </View>

            {/* Achievements */}
            <View style={[styles.achievementsCard, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.sectionHeader}>
                <Trophy size={20} color={currentTheme.colors.primary} />
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
                  Achievements
                </Text>
              </View>
              {renderAchievements()}
            </View>
          </ScrollView>
        </View>
      </BlurView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContainer: {
    flex: 1,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    marginTop: 60,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },

  // Streak Header
  streakHeader: {
    alignItems: 'center',
    paddingTop: 24,
    paddingBottom: 20,
  },
  plantContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  plantEmoji: {
    fontSize: 64,
    textAlign: 'center',
  },
  plantGlow: {
    position: 'absolute',
    width: 90,
    height: 90,
    borderRadius: 50,
    top: -6,
    zIndex: -1,
  },
  streakLevel: {
    fontSize: 18,
    fontWeight: '600',
  },

  // Cards
  streakCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  monthCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  subjectCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  achievementsCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 32,
  },

  // Section Headers
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
  },

  // Streak Stats
  streakStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    width: '48%',
    alignItems: 'center',
    marginBottom: 16,
    padding: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  statEmoji: {
    fontSize: 24,
    marginBottom: 8,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
    textAlign: 'center',
  },
  statLabel: {
    fontSize: 12,
    textAlign: 'center',
  },

  // Month View
  monthContainer: {
    
  },
  monthTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  monthSubtitle: {
    fontSize: 14,
    marginBottom: 20,
  },
  weekHeader: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  dayLabel: {
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
    width: '14.28%',
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  dayCell: {
    width: '14.28%',
    aspectRatio: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  dayNumber: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  todayNumber: {
    fontWeight: '700',
    color: '#4F8CFF',
  },
  dayStatus: {
    fontSize: 14,
  },
  legendContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 32,
    marginTop: 8,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  legendEmoji: {
    fontSize: 16,
  },
  legendText: {
    fontSize: 12,
  },

  // Subject Breakdown
  breakdownContainer: {
    
  },
  subjectList: {
    gap: 12,
  },
  subjectItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  subjectInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  subjectColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  subjectName: {
    fontSize: 14,
    fontWeight: '500',
  },
  subjectStats: {
    alignItems: 'flex-end',
  },
  subjectPercentage: {
    fontSize: 16,
    fontWeight: '600',
  },
  subjectHours: {
    fontSize: 12,
  },

  // Achievements
  achievementsContainer: {
    
  },
  achievementsList: {
    gap: 12,
  },
  achievementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  achievementIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  achievementContent: {
    flex: 1,
  },
  achievementTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  achievementDescription: {
    fontSize: 13,
    marginBottom: 6,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  progressBar: {
    flex: 1,
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '500',
  },
  unlockedBadge: {
    padding: 8,
    borderRadius: 8,
  },
}); 