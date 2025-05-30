import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView,
  StatusBar,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Award, ChevronRight, Sparkles, Zap } from 'lucide-react-native';

import { colors } from '../../constants/theme';
import CompletionRing from '../../components/CompletionRing';
import AIAssistantButton from '../../components/AIAssistantButton';
import AIAssistantModal from '../../components/AIAssistantModal';
import BarChart from '../../components/BarChart';

const CATEGORIES = [
  { name: 'Math', color: '#FF5757', hours: 5.5 },
  { name: 'Science', color: '#4F8CFF', hours: 7.2 },
  { name: 'History', color: '#8E6FFF', hours: 3.8 },
  { name: 'English', color: '#4CD964', hours: 4.5 },
];

const ACHIEVEMENTS = [
  { 
    id: '1', 
    title: 'Early Bird', 
    description: 'Completed 5 tasks before 10 AM this week',
    icon: <Zap color="#FFD700" size={24} />,
    achieved: true
  },
  { 
    id: '2', 
    title: 'Consistency King', 
    description: '5-day streak of completing all planned tasks',
    icon: <Award color="#FFD700\" size={24} />,
    achieved: true
  },
  { 
    id: '3', 
    title: 'Focus Master', 
    description: 'Maintained 3 focused study sessions of 50+ minutes',
    icon: <Sparkles color="#FFD700" size={24} />,
    achieved: false
  },
];

export default function ProgressScreen() {
  const [showAIModal, setShowAIModal] = useState(false);
  const weeklyCompletion = 78; // Mock completion percentage
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <Text style={styles.title}>Your Progress</Text>
      </View>

      <ScrollView 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <View style={styles.weeklyProgressContainer}>
          <CompletionRing 
            percentage={weeklyCompletion} 
            size={150} 
            strokeWidth={15}
            showText
          />
          <Text style={styles.progressLabel}>Weekly Completion</Text>
        </View>

        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Time Spent by Subject</Text>
          <BarChart data={CATEGORIES} />
          <Text style={styles.chartLabel}>Total: 21 hours this week</Text>
        </View>

        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Achievements</Text>
          {ACHIEVEMENTS.map(achievement => (
            <View 
              key={achievement.id} 
              style={[
                styles.achievementCard,
                !achievement.achieved && styles.unachievedCard
              ]}
            >
              <View style={styles.achievementIcon}>
                {achievement.icon}
              </View>
              <View style={styles.achievementContent}>
                <Text style={styles.achievementTitle}>{achievement.title}</Text>
                <Text style={styles.achievementDescription}>
                  {achievement.description}
                </Text>
              </View>
              {!achievement.achieved && (
                <Text style={styles.inProgressLabel}>In Progress</Text>
              )}
            </View>
          ))}
        </View>

        <LinearGradient
          colors={[colors.primaryBlue, colors.accentPurple]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.optimizationCard}
        >
          <Sparkles color="#fff" size={24} />
          <Text style={styles.optimizationTitle}>AI Optimization</Text>
          <Text style={styles.optimizationText}>
            Based on your study patterns, we recommend focusing more on History to balance your workload.
          </Text>
          <TouchableOpacity 
            style={styles.optimizationButton}
            onPress={() => setShowAIModal(true)}
          >
            <Text style={styles.optimizationButtonText}>Get Personalized Tips</Text>
            <ChevronRight color="#fff" size={16} />
          </TouchableOpacity>
        </LinearGradient>
      </ScrollView>

      <AIAssistantButton onPress={() => setShowAIModal(true)} />

      <AIAssistantModal
        visible={showAIModal}
        onClose={() => setShowAIModal(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  content: {
    paddingHorizontal: 24,
    paddingBottom: 100,
  },
  weeklyProgressContainer: {
    alignItems: 'center',
    marginVertical: 24,
  },
  progressLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginTop: 16,
  },
  sectionContainer: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 16,
  },
  chartLabel: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 8,
  },
  achievementCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
  },
  unachievedCard: {
    opacity: 0.7,
  },
  achievementIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  achievementContent: {
    flex: 1,
  },
  achievementTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  achievementDescription: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  inProgressLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    fontStyle: 'italic',
  },
  optimizationCard: {
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 24,
  },
  optimizationTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginVertical: 8,
  },
  optimizationText: {
    fontSize: 14,
    color: colors.textPrimary,
    textAlign: 'center',
    opacity: 0.9,
    marginBottom: 16,
  },
  optimizationButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  optimizationButtonText: {
    color: colors.textPrimary,
    fontSize: 14,
    fontWeight: '500',
    marginRight: 4,
  },
});