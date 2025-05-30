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
import { ChevronLeft, ChevronRight, Sparkles } from 'lucide-react-native';

import { colors } from '../../constants/theme';
import TaskCard from '../../components/TaskCard';
import HourlyScheduleView from '../../components/HourlyScheduleView';
import AIAssistantButton from '../../components/AIAssistantButton';
import AIAssistantModal from '../../components/AIAssistantModal';
import { useTasks } from '../../contexts/TaskContext';
import { useSettings } from '../../contexts/SettingsContext';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function WeekScreen() {
  const { tasks, refreshTasks, loading } = useTasks();
  const { workingHours } = useSettings();
  const [selectedDay, setSelectedDay] = useState(new Date().getDay());
  const [currentWeek, setCurrentWeek] = useState(0); // 0 = current week
  const [showAIModal, setShowAIModal] = useState(false);

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

  const changeWeek = (increment: number) => {
    setCurrentWeek(prev => prev + increment);
  };

  const isToday = (dayIndex: number) => {
    return currentWeek === 0 && dayIndex === new Date().getDay();
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <Text style={styles.title}>Week View</Text>
        
        <View style={styles.weekSelector}>
          <TouchableOpacity onPress={() => changeWeek(-1)} style={styles.weekButton}>
            <ChevronLeft size={24} color={colors.textSecondary} />
          </TouchableOpacity>
          
          <Text style={styles.weekTitle}>
            {currentWeek === 0 
              ? 'This Week' 
              : currentWeek === 1 
                ? 'Next Week' 
                : currentWeek === -1 
                  ? 'Last Week' 
                  : `Week ${currentWeek > 0 ? '+' : ''}${currentWeek}`}
          </Text>
          
          <TouchableOpacity onPress={() => changeWeek(1)} style={styles.weekButton}>
            <ChevronRight size={24} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.daysContainer}>
        {DAYS.map((day, index) => (
          <TouchableOpacity
            key={day}
            style={[
              styles.dayButton,
              selectedDay === index && styles.selectedDayButton
            ]}
            onPress={() => setSelectedDay(index)}
          >
            <Text 
              style={[
                styles.dayText, 
                selectedDay === index && styles.selectedDayText
              ]}
            >
              {day}
            </Text>
            <Text 
              style={[
                styles.dateText, 
                selectedDay === index && styles.selectedDateText,
                isToday(index) && styles.todayText
              ]}
            >
              {getDateForDay(index).getDate()}
            </Text>
            {isToday(index) && <View style={styles.todayIndicator} />}
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
                refreshing={loading}
                onRefresh={refreshTasks}
                tintColor={colors.primaryBlue}
                colors={[colors.primaryBlue]}
                progressBackgroundColor="transparent"
              />
            }
          >
            <View style={styles.emptyState}>
              <Text style={styles.emptyTitle}>No study schedule set</Text>
              <Text style={styles.emptyText}>
                Set your study hours in Settings to see your hourly schedule here.
              </Text>
              
              <LinearGradient
                colors={[colors.primaryBlue, colors.accentPurple]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.planAheadCard}
              >
                <Sparkles size={20} color="#fff" />
                <Text style={styles.planAheadTitle}>Plan Ahead</Text>
                <Text style={styles.planAheadText}>
                  Configure your study hours and let our AI help you organize your week for optimal productivity
                </Text>
              </LinearGradient>
            </View>
          </ScrollView>
        )}
      </View>

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
    paddingBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 16,
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
  weekTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginHorizontal: 16,
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
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  selectedDayButton: {
    backgroundColor: 'rgba(79, 140, 255, 0.15)',
    borderWidth: 1,
    borderColor: colors.primaryBlue,
  },
  dayText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textSecondary,
    marginBottom: 4,
  },
  selectedDayText: {
    color: colors.primaryBlue,
    fontWeight: '600',
  },
  dateText: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  selectedDateText: {
    color: colors.textPrimary,
  },
  todayText: {
    color: colors.primaryBlue,
  },
  todayIndicator: {
    position: 'absolute',
    bottom: 8,
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.primaryBlue,
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
    color: colors.textPrimary,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: colors.textSecondary,
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
    color: colors.textPrimary,
    marginVertical: 8,
  },
  planAheadText: {
    fontSize: 14,
    color: colors.textPrimary,
    textAlign: 'center',
    opacity: 0.8,
  },
});