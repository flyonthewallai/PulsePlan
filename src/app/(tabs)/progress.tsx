import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView,
  StatusBar,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { 
  Award, 
  ChevronRight, 
  Sparkles, 
  Zap, 
  Clock,
  BookOpen,
  Target,
  TrendingUp,
  Calendar,
  Brain,
  Coffee,
  Moon,
  Sun,
  ChevronDown,
  ChevronUp,
  Flame,
  Trophy,
  Edit3,
} from 'lucide-react-native';

import CompletionRing from '../../components/CompletionRing';
import AIAssistantButton from '../../components/AIAssistantButton';
import AIAssistantModal from '../../components/AIAssistantModal';
import BarChart from '../../components/BarChart';
import StreakModal from '../../components/StreakModal';
import { useTheme } from '../../contexts/ThemeContext';
import { useTasks } from '../../contexts/TaskContext';

const { width } = Dimensions.get('window');

type ViewMode = 'daily' | 'weekly' | 'monthly';

// Mock data - in real app, this would come from analytics/calculations
const WEEK_DATA = [
  { day: 'Mon', hours: 3.5, tasks: 8, subjects: { 'Computer Science': 2, 'Math': 1.5 } },
  { day: 'Tue', hours: 4.2, tasks: 6, subjects: { 'Computer Science': 2.5, 'Physics': 1.7 } },
  { day: 'Wed', hours: 2.8, tasks: 5, subjects: { 'Math': 1.8, 'Physics': 1 } },
  { day: 'Thu', hours: 5.1, tasks: 7, subjects: { 'Computer Science': 3, 'Math': 2.1 } },
  { day: 'Fri', hours: 3.0, tasks: 4, subjects: { 'Physics': 2, 'Biology': 1 } },
  { day: 'Sat', hours: 2.5, tasks: 3, subjects: { 'Biology': 2.5 } },
  { day: 'Sun', hours: 1.8, tasks: 2, subjects: { 'Computer Science': 1.8 } },
];

const SUBJECT_BREAKDOWN = [
  { name: 'Computer Science', color: '#4F8CFF', hours: 9.3, percentage: 41 },
  { name: 'Math', color: '#FF6B9D', hours: 5.4, percentage: 24 },
  { name: 'Physics', color: '#8E6FFF', hours: 4.7, percentage: 21 },
  { name: 'Biology', color: '#34D399', hours: 3.5, percentage: 14 },
];

const TASK_TYPES = [
  { type: 'Study', hours: 12.5, percentage: 55 },
  { type: 'Project', hours: 6.2, percentage: 27 },
  { type: 'Review', hours: 3.1, percentage: 14 },
  { type: 'Writing', hours: 1.1, percentage: 4 },
];

const BADGES_EARNED = [
  { id: '1', title: 'Planned 5 days in a row', icon: '📅', earned: true },
  { id: '2', title: 'Completed 15 hours total', icon: '⏰', earned: true },
  { id: '3', title: 'Improved consistency by 20%', icon: '📈', earned: true },
];

const SMART_INSIGHTS = [
  {
    id: '1',
    type: 'pattern',
    title: 'Friday Pattern Detected',
    message: "You're skipping Friday tasks often. Want to reduce load that day?",
    action: 'Adjust Schedule',
  },
  {
    id: '2',
    type: 'productivity',
    title: 'Morning Productivity Peak',
    message: 'Your mornings are the most productive. Try scheduling your toughest tasks earlier!',
    action: 'Optimize Schedule',
  },
  {
    id: '3',
    type: 'subject',
    title: 'Biology Tasks Piling Up',
    message: 'Biology tasks are accumulating — consider blocking time tomorrow.',
    action: 'Block Time',
  },
];

export default function ProgressScreen() {
  const { currentTheme } = useTheme();
  const { tasks } = useTasks();
  const [showAIModal, setShowAIModal] = useState(false);
  const [showStreakModal, setShowStreakModal] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('weekly');
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [showReflection, setShowReflection] = useState(false);
  const [reflectionText, setReflectionText] = useState('');
  
  // Calculate stats
  const weeklyCompletion = 75; // Keep existing weekly completion
  const totalPlanned = 14;
  const totalCompleted = 10.5;
  const completionRate = Math.round((totalCompleted / totalPlanned) * 100);
  const mostFocusedSubject = 'Computer Science';
  
  // Current streak data
  const streakData = {
    currentStreak: 6,
    isActive: true,
  };

  const getTimeOfDayIcon = (hour: number) => {
    if (hour < 12) return <Sun size={16} color="#FFD700" />;
    if (hour < 18) return <Coffee size={16} color="#8B4513" />;
    return <Moon size={16} color="#4169E1" />;
  };

  const renderDayBreakdown = (dayData: typeof WEEK_DATA[0]) => (
    <View style={styles.dayBreakdown}>
      <Text style={[styles.dayBreakdownTitle, { color: currentTheme.colors.textPrimary }]}>
        {dayData.day} - {dayData.hours}h
      </Text>
      {Object.entries(dayData.subjects).map(([subject, hours]) => (
        <View key={subject} style={styles.subjectRow}>
          <View style={[styles.subjectDot, { 
            backgroundColor: SUBJECT_BREAKDOWN.find(s => s.name === subject)?.color || '#999' 
          }]} />
          <Text style={[styles.subjectText, { color: currentTheme.colors.textSecondary }]}>
            {subject}: {hours}h
          </Text>
        </View>
      ))}
    </View>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <Text style={[styles.title, { color: currentTheme.colors.textPrimary }]}>Your Progress</Text>
      </View>

      <ScrollView 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        {/* Weekly Completion Ring */}
        <View style={styles.weeklyProgressContainer}>
          <CompletionRing 
            percentage={weeklyCompletion} 
            size={140} 
            strokeWidth={14}
            showText
          />
          <Text style={[styles.progressLabel, { color: currentTheme.colors.textPrimary }]}>
            Weekly Completion
          </Text>
        </View>

        {/* 📆 Mid Section: Interactive Weekly Breakdown */}
        <View style={styles.sectionSpacing}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
            Weekly Breakdown
          </Text>
          
          <View style={[styles.weekChart, { backgroundColor: currentTheme.colors.surface }]}>
            {WEEK_DATA.map((day, index) => (
              <TouchableOpacity
                key={day.day}
                style={styles.dayColumn}
                onPress={() => setSelectedDay(selectedDay === day.day ? null : day.day)}
              >
                <View style={styles.dayHeader}>
                  <Text style={[styles.dayLabel, { color: currentTheme.colors.textSecondary }]}>
                    {day.day}
                  </Text>
                  <Text style={[styles.dayHours, { color: currentTheme.colors.textPrimary }]}>
                    {day.hours}h
                  </Text>
                </View>
                
                <View style={styles.barContainer}>
                  <View 
                    style={[
                      styles.dayBar,
                      { 
                        height: Math.max((day.hours / 6) * 60, 8),
                        backgroundColor: currentTheme.colors.primary 
                      }
                    ]}
                  />
                </View>
                
                <Text style={[styles.taskCount, { color: currentTheme.colors.textSecondary }]}>
                  {day.tasks} tasks
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          
          {selectedDay && (
            <View style={[styles.dayDetail, { backgroundColor: currentTheme.colors.surface }]}>
              {renderDayBreakdown(WEEK_DATA.find(d => d.day === selectedDay)!)}
            </View>
          )}
        </View>

        {/* 📚 Task Analytics - Subject Breakdown */}
        <View style={styles.sectionSpacing}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
            Subject Analytics
          </Text>
          
          <View style={styles.chartSpacing}>
            <BarChart data={SUBJECT_BREAKDOWN} />
          </View>
          
          <View style={styles.insightBox}>
            <Text style={[styles.insightText, { color: currentTheme.colors.textSecondary }]}>
              💡 You spent 41% of your time on Computer Science — want to rebalance?
            </Text>
          </View>
        </View>

        {/* Task Type Stats */}
        <View style={styles.sectionSpacing}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
            Task Type Distribution
          </Text>
          
          <View style={styles.typeGrid}>
            {TASK_TYPES.map((type) => (
              <View key={type.type} style={[styles.typeItem, { backgroundColor: currentTheme.colors.surface }]}>
                <Text style={[styles.typePercentage, { color: currentTheme.colors.primary }]}>
                  {type.percentage}%
                </Text>
                <Text style={[styles.typeLabel, { color: currentTheme.colors.textPrimary }]}>
                  {type.type}
                </Text>
                <Text style={[styles.typeHours, { color: currentTheme.colors.textSecondary }]}>
                  {type.hours}h
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* 🔥 Streak Integration + Achievements */}
        <View style={styles.sectionSpacing}>
          <View style={styles.streakHeader}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
              Streak & Achievements
            </Text>
            
            <TouchableOpacity 
              style={[styles.streakWidget, { backgroundColor: currentTheme.colors.surface }]}
              onPress={() => setShowStreakModal(true)}
            >
              <Flame size={16} color="#FF5757" />
              <Text style={[styles.streakText, { color: currentTheme.colors.textPrimary }]}>
                {streakData.currentStreak}-day streak
              </Text>
            </TouchableOpacity>
          </View>
          
          <Text style={[styles.badgesTitle, { color: currentTheme.colors.textPrimary }]}>
            Badges Earned This Week:
          </Text>
          
          <View style={styles.badgesList}>
            {BADGES_EARNED.map((badge) => (
              <View key={badge.id} style={[styles.badgeItem, { backgroundColor: currentTheme.colors.surface }]}>
                <Text style={styles.badgeIcon}>{badge.icon}</Text>
                <Text style={[styles.badgeText, { color: currentTheme.colors.textPrimary }]}>
                  {badge.title}
                </Text>
                <Trophy size={16} color="#FFD700" />
              </View>
            ))}
          </View>
        </View>

        {/* 🤖 Smart Insights */}
        <View style={styles.sectionSpacing}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
            Smart Insights
          </Text>
          
          {SMART_INSIGHTS.map((insight) => (
            <View key={insight.id} style={[styles.insightCard, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.insightHeader}>
                <Brain size={16} color={currentTheme.colors.primary} />
                <Text style={[styles.insightTitle, { color: currentTheme.colors.textPrimary }]}>
                  {insight.title}
                </Text>
              </View>
              <Text style={[styles.insightMessage, { color: currentTheme.colors.textSecondary }]}>
                {insight.message}
              </Text>
              <TouchableOpacity style={[styles.insightAction, { borderColor: currentTheme.colors.primary }]}>
                <Text style={[styles.insightActionText, { color: currentTheme.colors.primary }]}>
                  {insight.action}
                </Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* 🏁 Weekly Reflection Prompt */}
        <View style={[styles.reflectionCard, { backgroundColor: currentTheme.colors.surface }]}>
          <TouchableOpacity 
            style={styles.reflectionHeader}
            onPress={() => setShowReflection(!showReflection)}
          >
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
            Weekly Reflection
            </Text>
            {showReflection ? 
              <ChevronUp size={20} color={currentTheme.colors.textSecondary} /> :
              <ChevronDown size={20} color={currentTheme.colors.textSecondary} />
            }
          </TouchableOpacity>
          
          {showReflection && (
            <View style={styles.reflectionContent}>
              <Text style={[styles.reflectionPrompt, { color: currentTheme.colors.textSecondary }]}>
                💭 "What went well this week?"
              </Text>
              <Text style={[styles.reflectionPrompt, { color: currentTheme.colors.textSecondary }]}>
                🎯 "What would you like to improve?"
              </Text>
              
              <TouchableOpacity 
                style={[styles.reflectionButton, { backgroundColor: currentTheme.colors.primary }]}
                onPress={() => setShowAIModal(true)}
              >
                <Edit3 size={16} color="#FFFFFF" />
                <Text style={styles.reflectionButtonText}>Start Weekly Review</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </ScrollView>

      <AIAssistantButton onPress={() => setShowAIModal(true)} />

      <AIAssistantModal
        visible={showAIModal}
        onClose={() => setShowAIModal(false)}
      />

      <StreakModal
        visible={showStreakModal}
        onClose={() => setShowStreakModal(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
  },
  content: {
    paddingHorizontal: 24,
    paddingBottom: 100,
  },
  snapshotSection: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 20,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 0,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    textAlign: 'center',
    fontWeight: '500',
  },
  weeklyProgressContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  progressLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 16,
  },
  sectionSpacing: {
    marginBottom: 40,
  },
  weekChart: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 20,
    borderRadius: 16,
  },
  dayColumn: {
    alignItems: 'center',
    flex: 1,
  },
  dayHeader: {
    alignItems: 'center',
    marginBottom: 8,
  },
  dayLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 2,
  },
  dayHours: {
    fontSize: 14,
    fontWeight: '500',
  },
  barContainer: {
    width: 24,
    height: 80,
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginVertical: 8,
  },
  dayBar: {
    width: 24,
    borderRadius: 12,
    minHeight: 8,
  },
  taskCount: {
    fontSize: 14,
    marginTop: 8,
  },
  dayDetail: {
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  dayBreakdown: {
    
  },
  dayBreakdownTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  subjectRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  subjectDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  subjectText: {
    fontSize: 14,
  },
  chartSpacing: {
    marginBottom: 16,
  },
  insightBox: {
    marginTop: 0,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  insightText: {
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  typeGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  typeItem: {
    alignItems: 'center',
    flex: 1,
    padding: 16,
    borderRadius: 12,
  },
  typePercentage: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 4,
  },
  typeLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  typeHours: {
    fontSize: 12,
  },
  streakHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  streakWidget: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  streakText: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  badgesTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  badgesList: {
    gap: 8,
  },
  badgeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  badgeIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  badgeText: {
    fontSize: 12,
    flex: 1,
    fontWeight: '500',
  },
  insightCard: {
    padding: 18,
    borderRadius: 16,
    marginBottom: 16,
  },
  insightHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  insightMessage: {
    fontSize: 14,
    marginBottom: 14,
    lineHeight: 20,
  },
  insightAction: {
    borderWidth: 1,
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  insightActionText: {
    fontSize: 14,
    fontWeight: '600',
  },
  reflectionCard: {
    borderRadius: 20,
    padding: 24,
    marginBottom: 40,
  },
  reflectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reflectionContent: {
    marginTop: 20,
  },
  reflectionPrompt: {
    fontSize: 15,
    marginBottom: 12,
    lineHeight: 22,
  },
  reflectionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 16,
    marginTop: 8,
  },
  reflectionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
    color: '#FFFFFF',
  },
});