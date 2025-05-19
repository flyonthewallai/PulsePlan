import React, { useState, useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Animated, RefreshControl, Alert } from 'react-native';
import { TaskCard } from '../components/TaskCard';
import { MonthView } from '../components/MonthView';
import { TaskDetailsModal } from '../components/TaskDetailsModal';
import { TaskCreateModal } from '../components/TaskCreateModal';
import { useTheme } from '../contexts/ThemeContext';
import { useTasks, Task, CreateTaskData } from '../contexts/TaskContext';
import { Ionicons } from '@expo/vector-icons';

export const WeekView = () => {
  const { theme } = useTheme();
  const { tasks, loading, error, refreshTasks, createTask, updateTask } = useTasks();
  const [selectedDay, setSelectedDay] = useState(new Date());
  const [showMonthView, setShowMonthView] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const scaleAnim = React.useRef(new Animated.Value(1)).current;

  // Get days of the week
  const days = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - date.getDay() + i);
      return date;
    });
  }, []);

  // Get tasks for selected day
  const tasksForSelectedDay = useMemo(() => {
    return tasks.filter(task => {
      const taskDate = new Date(task.due_date);
      return taskDate.toDateString() === selectedDay.toDateString();
    });
  }, [tasks, selectedDay]);

  // Get tasks for each day of the week
  const tasksByDay = useMemo(() => {
    return days.reduce((acc, day) => {
      acc[day.toDateString()] = tasks.filter(task => {
        const taskDate = new Date(task.due_date);
        return taskDate.toDateString() === day.toDateString();
      });
      return acc;
    }, {} as Record<string, typeof tasks>);
  }, [tasks, days]);

  const isSelected = (day: Date) => {
    return day.toDateString() === selectedDay.toDateString();
  };

  const handleDayPress = (day: Date) => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 0.95,
        useNativeDriver: true,
        speed: 50,
        bounciness: 4
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        speed: 50,
        bounciness: 4
      })
    ]).start();
    setSelectedDay(day);
  };

  const handleMonthViewDayPress = (date: Date) => {
    setSelectedDay(date);
    setShowMonthView(false);
  };

  const handleTaskPress = (task: Task) => {
    setSelectedTask(task);
  };

  const handleTaskStatusChange = async (status: Task['status']) => {
    if (!selectedTask) return;
    try {
      await updateTask(selectedTask.id, { status });
      setSelectedTask({ ...selectedTask, status });
    } catch (err) {
      Alert.alert('Error', 'Could not update task status. Please try again.');
    }
  };

  const handleCreateTask = async (taskData: CreateTaskData) => {
    try {
      // Set the due date to the selected day
      const taskWithDate = {
        ...taskData,
        due_date: selectedDay.toISOString(),
      };
      await createTask(taskWithDate);
      setShowCreateModal(false);
    } catch (err) {
      Alert.alert('Error', 'Could not create task. Please try again.');
    }
  };

  // Handle manual refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshTasks();
    setIsRefreshing(false);
  };

  return (
    <>
      <ScrollView 
        style={[
          styles.container,
          { backgroundColor: theme.colors.background }
        ]}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={theme.colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <View>
            <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
              Week View
            </Text>
            <Text style={[styles.headerSubtitle, { color: theme.colors.subtext }]}>
              Plan your week ahead
            </Text>
          </View>
          <TouchableOpacity
            style={[
              styles.calendarButton,
              { backgroundColor: theme.colors.cardBackground }
            ]}
            onPress={() => setShowMonthView(true)}
          >
            <Ionicons name="calendar-outline" size={24} color={theme.colors.text} />
          </TouchableOpacity>
        </View>

        <Animated.View 
          style={[
            styles.daysContainer,
            { transform: [{ scale: scaleAnim }] }
          ]}
        >
          {days.map((day, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.dayButton,
                isSelected(day) && { 
                  backgroundColor: theme.colors.primary,
                  shadowColor: theme.colors.primary,
                  shadowOpacity: 0.3,
                }
              ]}
              onPress={() => handleDayPress(day)}
              activeOpacity={0.9}
            >
              <Text style={[
                styles.dayName,
                { 
                  color: isSelected(day) ? '#FFFFFF' : theme.colors.text,
                  opacity: isSelected(day) ? 1 : 0.7
                }
              ]}>
                {day.toLocaleDateString('en-US', { weekday: 'short' })}
              </Text>
              <Text style={[
                styles.dayNumber,
                { 
                  color: isSelected(day) ? '#FFFFFF' : theme.colors.text,
                  opacity: isSelected(day) ? 1 : 0.9
                }
              ]}>
                {day.getDate()}
              </Text>
              {isSelected(day) && (
                <View style={[
                  styles.selectedIndicator,
                  { backgroundColor: '#FFFFFF' }
                ]} />
              )}
            </TouchableOpacity>
          ))}
        </Animated.View>

        {days.findIndex(day => isSelected(day)) > 1 && (
          <View style={[
            styles.suggestionContainer,
            { 
              backgroundColor: theme.colors.cardBackground,
              borderColor: theme.colors.primary + '30',
              shadowColor: theme.colors.text,
              shadowOpacity: 0.1,
            }
          ]}>
            <View style={styles.suggestionContent}>
              <View style={[
                styles.suggestionIconContainer,
                { backgroundColor: theme.colors.primary + '15' }
              ]}>
                <Ionicons 
                  name="bulb-outline" 
                  size={20} 
                  color={theme.colors.primary} 
                />
              </View>
              <View style={styles.suggestionTextContainer}>
                <Text style={[styles.suggestionTitle, { color: theme.colors.text }]}>
                  Plan Ahead
                </Text>
                <Text style={[styles.suggestionText, { color: theme.colors.subtext }]}>
                  Consider scheduling tasks for later in the week
                </Text>
              </View>
            </View>
          </View>
        )}

        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            {selectedDay.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </Text>
          <TouchableOpacity
            style={[
              styles.addTaskButton,
              { backgroundColor: theme.colors.primary + '15' }
            ]}
            onPress={() => {/* Handle add task */}}
          >
            <Ionicons 
              name="add" 
              size={20} 
              color={theme.colors.primary} 
            />
            <Text style={[styles.addTaskText, { color: theme.colors.primary }]}>
              Add Task
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.tasksContainer}>
          {error ? (
            <View style={[
              styles.emptyState,
              { 
                backgroundColor: theme.colors.cardBackground,
                shadowColor: theme.colors.text,
                shadowOpacity: 0.1,
              }
            ]}>
              <Ionicons 
                name="alert-circle-outline" 
                size={32} 
                color={theme.colors.error} 
              />
              <Text style={[styles.emptyStateText, { color: theme.colors.text }]}>
                Error loading tasks
              </Text>
              <TouchableOpacity
                style={[styles.retryButton, { backgroundColor: theme.colors.primary }]}
                onPress={refreshTasks}
              >
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          ) : tasksForSelectedDay.length > 0 ? (
            <View style={styles.taskList}>
              {tasksForSelectedDay.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onPress={() => onTaskClick(task)}
                />
              ))}
            </View>
          ) : (
            <View style={[
              styles.emptyState,
              { 
                backgroundColor: theme.colors.cardBackground,
                shadowColor: theme.colors.text,
                shadowOpacity: 0.1,
              }
            ]}>
              <Ionicons 
                name="calendar-outline" 
                size={32} 
                color={theme.colors.subtext} 
              />
              <Text style={[styles.emptyStateText, { color: theme.colors.text }]}>
                No tasks scheduled
              </Text>
              <Text style={[styles.emptyStateSubtext, { color: theme.colors.subtext }]}>
                Add tasks to plan your day
              </Text>
            </View>
          )}
        </View>
      </ScrollView>

      <MonthView
        visible={showMonthView}
        onClose={() => setShowMonthView(false)}
        tasks={tasks}
        onDayPress={handleMonthViewDayPress}
      />
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 100,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
    letterSpacing: 0.3,
  },
  headerSubtitle: {
    fontSize: 16,
    letterSpacing: 0.2,
  },
  calendarButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 3,
  },
  daysContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    paddingHorizontal: 4,
  },
  dayButton: {
    alignItems: 'center',
    padding: 12,
    borderRadius: 16,
    minWidth: 48,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 3,
  },
  dayName: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
    letterSpacing: 0.2,
  },
  dayNumber: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  selectedIndicator: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginTop: 6,
  },
  suggestionContainer: {
    marginBottom: 24,
    padding: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderStyle: 'dashed',
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 12,
    elevation: 4,
  },
  suggestionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  suggestionIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  suggestionTextContainer: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
    letterSpacing: 0.2,
  },
  suggestionText: {
    fontSize: 14,
    letterSpacing: 0.2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  addTaskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    gap: 4,
  },
  addTaskText: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  tasksContainer: {
    flex: 1,
  },
  taskList: {
    gap: 12,
  },
  emptyState: {
    padding: 32,
    borderRadius: 20,
    alignItems: 'center',
    gap: 12,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 12,
    elevation: 4,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  emptyStateSubtext: {
    fontSize: 14,
    letterSpacing: 0.2,
  },
  retryButton: {
    marginTop: 12,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
});