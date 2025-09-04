import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity,
  StatusBar,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { ChevronLeft, ChevronRight, Sparkles, Sprout, Calendar } from 'lucide-react-native';

import TaskCard from '../../components/TaskCard';
import HourlyScheduleView from '../../components/HourlyScheduleView';
import AIAssistantButton from '../../components/AgentButton';
import AIAssistantModal from '../../components/AgentModal';
import { StreakModal } from '../../components/StreakModal';
import MonthViewModal from '../../components/MonthViewModal';
import { useTasks } from '../../contexts/TaskContext';
import { useSettings } from '../../contexts/SettingsContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useStreak } from '../../contexts/StreakContext';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function WeekScreen() {
  const { tasks, refreshTasks, loading } = useTasks();
  const { workingHours } = useSettings();
  const { currentTheme } = useTheme();
  const { currentStreak } = useStreak();
  const [selectedDay, setSelectedDay] = useState(new Date().getDay());
  const [currentWeek, setCurrentWeek] = useState(0); // 0 = current week
  const [showAIModal, setShowAIModal] = useState(false);
  const [showStreakModal, setShowStreakModal] = useState(false);
  const [showMonthView, setShowMonthView] = useState(false);
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);

  // Get tasks for the selected day
  const getTasksForDay = (dayIndex: number) => {
    const targetDate = new Date();
    const currentDayOfWeek = targetDate.getDay();
    const diff = dayIndex - currentDayOfWeek + (currentWeek * 7);
    
    targetDate.setDate(targetDate.getDate() + diff);
    const targetDateString = targetDate.toDateString();
    
    return tasks.filter(task => {
      const taskDate = new Date(task.due_date).toDateString();
      return taskDate === targetDateString;
    });
  };

  const tasksForSelectedDay = getTasksForDay(selectedDay);

  const getDateForDay = (dayIndex: number) => {
    const today = new Date();
    const currentDayOfWeek = today.getDay();
    const diff = dayIndex - currentDayOfWeek + (currentWeek * 7);
    
    const date = new Date(today);
    date.setDate(today.getDate() + diff);
    return date;
  };

  const getCurrentMonthYear = () => {
    const firstDayOfWeek = getDateForDay(0);
    const lastDayOfWeek = getDateForDay(6);
    
    const firstMonth = firstDayOfWeek.toLocaleString('default', { month: 'long' });
    const lastMonth = lastDayOfWeek.toLocaleString('default', { month: 'long' });
    const year = firstDayOfWeek.getFullYear();
    
    if (firstMonth === lastMonth) {
      return `${firstMonth} ${year}`;
    }
    return `${firstMonth}-${lastMonth} ${year}`;
  };

  const changeWeek = (increment: number) => {
    setCurrentWeek(prev => prev + increment);
  };

  const isToday = (dayIndex: number) => {
    return currentWeek === 0 && dayIndex === new Date().getDay();
  };

  const handleManualRefresh = async () => {
    setIsManualRefreshing(true);
    try {
      await refreshTasks();
    } finally {
      setIsManualRefreshing(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <StatusBar barStyle="light-content" />
      <View style={{ flex: 1 }}>
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.titleContainer}
            onPress={() => setShowMonthView(true)}
          >
            <Calendar size={28} color={currentTheme.colors.textSecondary} />
          </TouchableOpacity>
          
          <View style={styles.weekSelector}>
            <TouchableOpacity onPress={() => changeWeek(-1)} style={styles.weekButton}>
              <ChevronLeft size={24} color={currentTheme.colors.textSecondary} />
            </TouchableOpacity>
            
            <View style={styles.weekTitleContainer}>
              <Text style={[styles.monthTitle, { color: currentTheme.colors.textPrimary }]}>
                {getCurrentMonthYear()}
              </Text>
              <Text style={[styles.weekTitle, { color: currentTheme.colors.textSecondary }]}>
                {currentWeek === 0 
                  ? 'This Week' 
                  : currentWeek === 1 
                    ? 'Next Week' 
                    : currentWeek === -1 
                      ? 'Last Week' 
                      : `Week ${currentWeek > 0 ? '+' : ''}${currentWeek}`}
              </Text>
            </View>
            
            <TouchableOpacity onPress={() => changeWeek(1)} style={styles.weekButton}>
              <ChevronRight size={24} color={currentTheme.colors.textSecondary} />
            </TouchableOpacity>
          </View>

          <TouchableOpacity 
            style={[styles.streakButton, { backgroundColor: currentTheme.colors.primary + '20' }]}
            onPress={() => setShowStreakModal(true)}
          >
            <Sprout size={16} color={currentTheme.colors.primary} />
            <Text style={[styles.streakText, { color: currentTheme.colors.primary }]}>
              {currentStreak} day{currentStreak !== 1 ? 's' : ''}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.daysContainer}>
          {DAYS.map((day, index) => (
            <TouchableOpacity
              key={day}
              style={[
                styles.dayButton,
                selectedDay === index && [styles.selectedDayButton, { backgroundColor: 'rgba(79, 140, 255, 0.15)', borderColor: currentTheme.colors.primary }]
              ]}
              onPress={() => setSelectedDay(index)}
            >
              <Text 
                style={[
                  styles.dayText, 
                  { color: currentTheme.colors.textSecondary },
                  selectedDay === index && { color: currentTheme.colors.primary, fontWeight: '600' }
                ]}
              >
                {day}
              </Text>
              <Text 
                style={[
                  styles.dateText, 
                  { color: currentTheme.colors.textPrimary },
                  selectedDay === index && { color: currentTheme.colors.textPrimary },
                  isToday(index) && { color: currentTheme.colors.primary }
                ]}
              >
                {getDateForDay(index).getDate()}
              </Text>
              {isToday(index) && <View style={[styles.todayIndicator, { backgroundColor: currentTheme.colors.primary }]} />}
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.content}>
          {tasksForSelectedDay.length > 0 || workingHours ? (
            <HourlyScheduleView
              tasks={tasksForSelectedDay}
              studyStartHour={workingHours.startHour}
              studyEndHour={workingHours.endHour}
              date={getDateForDay(selectedDay)}
            />
          ) : (
                          <ScrollView 
              showsVerticalScrollIndicator={false}
              refreshControl={
                <RefreshControl
                  refreshing={isManualRefreshing || loading}
                  onRefresh={handleManualRefresh}
                  tintColor={currentTheme.colors.primary}
                  colors={[currentTheme.colors.primary]}
                  progressBackgroundColor="transparent"
                />
              }
            >
              <View style={styles.emptyState}>
                <Text style={[styles.emptyTitle, { color: currentTheme.colors.textPrimary }]}>No study schedule set</Text>
                <Text style={[styles.emptyText, { color: currentTheme.colors.textSecondary }]}>
                  Set your study hours in Settings to see your hourly schedule here.
                </Text>
                
                <LinearGradient
                  colors={[currentTheme.colors.primary, currentTheme.colors.accent]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.planAheadCard}
                >
                  <Sparkles size={20} color="#fff" />
                  <Text style={[styles.planAheadTitle, { color: currentTheme.colors.textPrimary }]}>Plan Ahead</Text>
                  <Text style={[styles.planAheadText, { color: currentTheme.colors.textPrimary }]}>
                    Configure your study hours and let our AI help you organize your week for optimal productivity
                  </Text>
                </LinearGradient>
              </View>
            </ScrollView>
          )}
        </View>
      </View>

      <AIAssistantButton onPress={() => setShowAIModal(true)} />

      <AIAssistantModal
        visible={showAIModal}
        onClose={() => setShowAIModal(false)}
      />

      <StreakModal
        visible={showStreakModal}
        onClose={() => setShowStreakModal(false)}
      />

      <MonthViewModal
        visible={showMonthView}
        onClose={() => setShowMonthView(false)}
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
    paddingBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 16,
  },
  titleContainer: {
    alignSelf: 'flex-start',
    marginBottom: 16,
    padding: 4,
  },
  weekSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  weekButton: {
    padding: 8,
  },
  weekTitleContainer: {
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 16,
  },
  monthTitle: {
    fontSize: 18,
    fontWeight: '500',
    marginBottom: 2,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  weekTitle: {
    fontSize: 13,
    fontWeight: '400',
    opacity: 0.7,
    letterSpacing: 0.3,
  },
  daysContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  dayButton: {
    flex: 1,
    height: 72,
    borderRadius: 12,
    marginHorizontal: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectedDayButton: {
    borderWidth: 1,
  },
  dayText: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
    opacity: 0.8,
  },
  dateText: {
    fontSize: 20,
    fontWeight: '600',
  },
  todayIndicator: {
    position: 'absolute',
    bottom: 8,
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  content: {
    flex: 1,
    paddingTop: 16,
  },
  emptyState: {
    marginTop: 32,
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 32,
  },
  planAheadCard: {
    borderRadius: 16,
    padding: 20,
    width: '100%',
    alignItems: 'center',
  },
  planAheadTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginVertical: 8,
  },
  planAheadText: {
    fontSize: 14,
    textAlign: 'center',
    opacity: 0.8,
  },
  streakButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
  },
  streakText: {
    fontSize: 13,
    fontWeight: '600',
  },
});