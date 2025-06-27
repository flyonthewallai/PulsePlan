import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X, ChevronLeft, ChevronRight, Calendar, Clock } from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useTasks } from '../contexts/TaskContext';

const { width } = Dimensions.get('window');

interface MonthViewModalProps {
  visible: boolean;
  onClose: () => void;
}

export default function MonthViewModal({ visible, onClose }: MonthViewModalProps) {
  const { currentTheme } = useTheme();
  const { tasks } = useTasks();
  const [currentDate, setCurrentDate] = useState(new Date());

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const getTasksForDate = (day: number) => {
    const targetDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    const targetDateString = targetDate.toDateString();
    
    return tasks.filter(task => {
      const taskDate = new Date(task.due_date).toDateString();
      return taskDate === targetDateString;
    });
  };

  const getTasksForMonth = () => {
    const monthStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const monthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    
    return tasks.filter(task => {
      const taskDate = new Date(task.due_date);
      return taskDate >= monthStart && taskDate <= monthEnd;
    }).sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime());
  };

  const formatTaskDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const getTasksByDate = () => {
    const monthTasks = getTasksForMonth();
    const groupedTasks: { [key: string]: any[] } = {};
    
    monthTasks.forEach(task => {
      const dateKey = new Date(task.due_date).toDateString();
      if (!groupedTasks[dateKey]) {
        groupedTasks[dateKey] = [];
      }
      groupedTasks[dateKey].push(task);
    });
    
    return Object.entries(groupedTasks).map(([date, tasks]) => ({
      date,
      tasks,
      formattedDate: formatTaskDate(date)
    }));
  };

  const changeMonth = (increment: number) => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + increment, 1));
  };

  const renderCalendarDays = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const today = new Date();
    const isCurrentMonth = 
      currentDate.getMonth() === today.getMonth() && 
      currentDate.getFullYear() === today.getFullYear();

    const days = [];
    
    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(
        <View key={`empty-${i}`} style={styles.dayCell} />
      );
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const tasksForDay = getTasksForDate(day);
      const isToday = isCurrentMonth && day === today.getDate();
      
      days.push(
        <View key={day} style={styles.dayCell}>
          <View style={[
            styles.dayContainer,
            isToday && [styles.todayContainer, { backgroundColor: currentTheme.colors.primary }]
          ]}>
            <Text style={[
              styles.dayText,
              { color: currentTheme.colors.textPrimary },
              isToday && { color: '#fff' }
            ]}>
              {day}
            </Text>
            {tasksForDay.length > 0 && (
              <View style={[styles.taskIndicator, { backgroundColor: currentTheme.colors.accent }]}>
                <Text style={styles.taskCount}>{tasksForDay.length}</Text>
              </View>
            )}
          </View>
        </View>
      );
    }

    return days;
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => changeMonth(-1)} style={styles.navButton}>
            <ChevronLeft size={24} color={currentTheme.colors.textSecondary} />
          </TouchableOpacity>
          
          <Text style={[styles.monthTitle, { color: currentTheme.colors.textPrimary }]}>
            {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
          </Text>
          
          <TouchableOpacity onPress={() => changeMonth(1)} style={styles.navButton}>
            <ChevronRight size={24} color={currentTheme.colors.textSecondary} />
          </TouchableOpacity>
          
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color={currentTheme.colors.textSecondary} />
          </TouchableOpacity>
        </View>

        <View style={styles.weekDaysHeader}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <Text key={day} style={[styles.weekDayText, { color: currentTheme.colors.textSecondary }]}>
              {day}
            </Text>
          ))}
        </View>

        <View style={styles.calendarContainer}>
          <View style={styles.calendar}>
            {renderCalendarDays()}
          </View>
        </View>

        <View style={[styles.divider, { backgroundColor: currentTheme.colors.textSecondary + '20' }]} />

        <View style={styles.overviewSection}>
          <View style={styles.overviewHeader}>
            <Calendar size={20} color={currentTheme.colors.textPrimary} />
            <Text style={[styles.overviewTitle, { color: currentTheme.colors.textPrimary }]}>
              Monthly Overview
            </Text>
            <Text style={[styles.taskCountBadge, { 
              backgroundColor: currentTheme.colors.primary + '20',
              color: currentTheme.colors.primary 
            }]}>
              {getTasksForMonth().length}
            </Text>
          </View>

          <ScrollView style={styles.tasksScrollView} showsVerticalScrollIndicator={false}>
            {getTasksByDate().length > 0 ? (
              getTasksByDate().map((dayGroup, index) => (
                <View key={dayGroup.date} style={styles.dayGroup}>
                  <Text style={[styles.dayGroupDate, { color: currentTheme.colors.textPrimary }]}>
                    {dayGroup.formattedDate}
                  </Text>
                  {dayGroup.tasks.map((task: any, taskIndex: number) => (
                    <View key={task.id} style={[styles.taskItem, { 
                      backgroundColor: currentTheme.colors.background,
                      borderColor: currentTheme.colors.textSecondary + '20'
                    }]}>
                      <View style={styles.taskInfo}>
                        <Text style={[styles.taskTitle, { color: currentTheme.colors.textPrimary }]}>
                          {task.title}
                        </Text>
                        {task.description && (
                          <Text style={[styles.taskDescription, { color: currentTheme.colors.textSecondary }]}>
                            {task.description}
                          </Text>
                        )}
                      </View>
                      <View style={styles.taskMeta}>
                        <View style={[styles.priorityIndicator, { 
                          backgroundColor: task.priority === 'high' ? '#FF6B6B' : 
                                         task.priority === 'medium' ? '#FFD93D' : '#6BCF7F' 
                        }]} />
                        {task.due_time && (
                          <View style={styles.timeContainer}>
                            <Clock size={12} color={currentTheme.colors.textSecondary} />
                            <Text style={[styles.taskTime, { color: currentTheme.colors.textSecondary }]}>
                              {new Date(`1970-01-01T${task.due_time}`).toLocaleTimeString([], { 
                                hour: 'numeric', 
                                minute: '2-digit' 
                              })}
                            </Text>
                          </View>
                        )}
                      </View>
                    </View>
                  ))}
                </View>
              ))
            ) : (
              <View style={styles.emptyState}>
                <Calendar size={48} color={currentTheme.colors.textSecondary + '40'} />
                <Text style={[styles.emptyStateText, { color: currentTheme.colors.textSecondary }]}>
                  No tasks scheduled for this month
                </Text>
              </View>
            )}
          </ScrollView>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

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
  navButton: {
    padding: 8,
  },
  monthTitle: {
    fontSize: 20,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
  },
  closeButton: {
    padding: 8,
  },
  weekDaysHeader: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 12,
  },
  weekDayText: {
    width: (width - 40) / 7,
    textAlign: 'center',
    fontSize: 14,
    fontWeight: '500',
  },
  calendarContainer: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  calendar: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  dayCell: {
    width: (width - 40) / 7,
    height: 60,
    padding: 4,
  },
  dayContainer: {
    flex: 1,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  todayContainer: {
    backgroundColor: '#4F8CFF',
  },
  dayText: {
    fontSize: 16,
    fontWeight: '500',
  },
  taskIndicator: {
    position: 'absolute',
    top: 2,
    right: 2,
    width: 16,
    height: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  taskCount: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
  },
  divider: {
    height: 1,
    marginHorizontal: 20,
  },
  overviewSection: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  overviewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  overviewTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
  },
  taskCountBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    fontSize: 12,
    fontWeight: '600',
  },
  tasksScrollView: {
    flex: 1,
  },
  dayGroup: {
    marginBottom: 20,
  },
  dayGroupDate: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  taskItem: {
    flexDirection: 'row',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
  },
  taskInfo: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  taskDescription: {
    fontSize: 12,
    opacity: 0.8,
  },
  taskMeta: {
    alignItems: 'flex-end',
    gap: 4,
  },
  priorityIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  taskTime: {
    fontSize: 11,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
    gap: 12,
  },
  emptyStateText: {
    fontSize: 14,
    textAlign: 'center',
  },
}); 