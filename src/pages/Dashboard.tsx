import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert, RefreshControl } from 'react-native';
import { TaskCard } from '../components/TaskCard';
import { TaskCreateModal } from '../components/TaskCreateModal';
import { TaskDetailsModal } from '../components/TaskDetailsModal';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { API_URL, getApiUrl } from '../config/api';
import { Ionicons } from '@expo/vector-icons';
import { useProfile } from '../contexts/ProfileContext';
import { useTasks, Task, CreateTaskData } from '../contexts/TaskContext';
import { DailySchedule } from '../components/DailySchedule';
import { useSettings, StudyTimeBlock } from '../contexts/SettingsContext';
import { Task as TaskType } from '../types/task';
import { AIChatModal } from '../components/AIChatModal';

// Define the form data type for creating a task
type TaskFormData = Omit<Task, 'id' | 'user_id'>;

export const Dashboard = ({ onTaskClick }: { onTaskClick: (task: Task) => void }) => {
  const { theme } = useTheme();
  const { session } = useAuth();
  const { profileData } = useProfile();
  const { tasks, loading, error, refreshTasks, createTask, updateTask } = useTasks();
  const { workingHours, studyTimes } = useSettings();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showAIChat, setShowAIChat] = useState(false);

  const handleCreateTask = async (taskData: CreateTaskData) => {
    try {
      await createTask(taskData);
      setShowCreateModal(false);
    } catch (err) {
      Alert.alert('Error', 'Could not create task. Please try again.');
    }
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

  const weeklyProgress = useMemo(() => {
    if (!tasks.length) return 0;

    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setHours(0, 0, 0, 0);
    startOfWeek.setDate(now.getDate() - now.getDay()); // Start of week (Sunday)

    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6); // End of week (Saturday)

    const weeklyTasks = tasks.filter(task => {
      const taskDate = new Date(task.due_date);
      return taskDate >= startOfWeek && taskDate <= endOfWeek;
    });

    if (!weeklyTasks.length) return 0;

    const completedTasks = weeklyTasks.filter(task => task.status === 'completed');
    const progress = Math.round((completedTasks.length / weeklyTasks.length) * 100);
    return Math.min(progress, 100); // Cap at 100%
  }, [tasks]);

  // Get today's tasks and optimize their schedule
  const todaysTasks = useMemo(() => {
    const today = new Date();
    const dayOfWeek = today.getDay();

    // Filter tasks for today and sort by priority and duration
    const filteredTasks: Task[] = tasks
      .filter((task: Task) => {
        const taskDate = new Date(task.due_date);
        return (
          taskDate.getDate() === today.getDate() &&
          taskDate.getMonth() === today.getMonth() &&
          taskDate.getFullYear() === today.getFullYear()
        );
      })
      .sort((a: Task, b: Task) => {
        // First sort by priority (high > medium > low)
        const priorityOrder: Record<string, number> = { high: 0, medium: 1, low: 2 };
        const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
        if (priorityDiff !== 0) return priorityDiff;

        // Then sort by estimated duration (shorter tasks first)
        return (a.estimated_minutes || 0) - (b.estimated_minutes || 0);
      });

    // Get study times for today
    const todaysStudyTimes: StudyTimeBlock[] = studyTimes
      .filter((block: StudyTimeBlock) => block.days.includes(dayOfWeek))
      .sort((a: StudyTimeBlock, b: StudyTimeBlock) => a.startHour - b.startHour);

    // Schedule tasks considering study times
    return filteredTasks.map((task: Task) => {
      let optimalHour = workingHours.startHour;

      // If we have study times for today, try to schedule during them
      if (todaysStudyTimes.length > 0) {
        // Find the first study block that can fit this task
        const suitableStudyBlock = todaysStudyTimes.find((block: StudyTimeBlock) => {
          const blockDuration = block.endHour - block.startHour;
          return blockDuration >= (task.estimated_minutes || 0);
        });

        if (suitableStudyBlock) {
          // Schedule at the start of the study block
          optimalHour = suitableStudyBlock.startHour;
        } else {
          // If no suitable study block found, schedule after the last study block
          const lastStudyBlock = todaysStudyTimes[todaysStudyTimes.length - 1];
          optimalHour = Math.min(
            lastStudyBlock.endHour + 1, 
            workingHours.endHour - (task.estimated_minutes || 0)
          );
        }
      } else {
        // If no study times, use the original scheduling logic
        // Start with high priority tasks early in the day
        if (task.priority === 'high') {
          optimalHour = workingHours.startHour;
        } else if (task.priority === 'medium') {
          // Place medium priority tasks after lunch
          optimalHour = Math.max(workingHours.lunchBreakStart + 1, workingHours.startHour);
        } else {
          // Place low priority tasks later in the day
          optimalHour = Math.max(workingHours.lunchBreakStart + 2, workingHours.startHour);
        }

        // Ensure we don't exceed working hours
        if (optimalHour + (task.estimated_minutes || 0) > workingHours.endHour) {
          optimalHour = Math.max(
            workingHours.startHour, 
            workingHours.endHour - (task.estimated_minutes || 0)
          );
        }
      }

      // Avoid scheduling during lunch break
      if (optimalHour <= workingHours.lunchBreakStart && 
          optimalHour + (task.estimated_minutes || 0) > workingHours.lunchBreakStart) {
        optimalHour = workingHours.lunchBreakEnd + 1;
      }

      const scheduledDate = new Date(today);
      scheduledDate.setHours(optimalHour, 0, 0, 0);

      return {
        ...task,
        due_date: scheduledDate.toISOString(),
        scheduledHour: optimalHour
      };
    });
  }, [tasks, workingHours, studyTimes]);

  const buttonStyles = useMemo(() => ({
    addTaskButton: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 12,
      gap: 4,
      backgroundColor: theme.colors.primary + '15',
    },
    quickStatsButton: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 12,
      gap: 4,
      backgroundColor: theme.colors.primary + '15',
    },
    aiButton: {
      position: 'absolute' as const,
      bottom: 60,
      right: 20,
      width: 48,
      height: 48,
      borderRadius: 24,
      justifyContent: 'center' as const,
      alignItems: 'center' as const,
      backgroundColor: theme.colors.primary + '15',
      shadowColor: theme.colors.primary,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
      elevation: 4,
    },
  }), [theme]);

  return (
    <View style={{ flex: 1 }}>
      <ScrollView
        style={[
          styles.container,
          { backgroundColor: theme.colors.background }
        ]}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refreshTasks}
            tintColor={theme.colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <View>
            <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
              Welcome back, {profileData.name.split(' ')[0]}!
            </Text>
            <Text style={[styles.headerSubtitle, { color: theme.colors.subtext }]}>
              Let's make today productive
            </Text>
          </View>
        </View>

        <View style={styles.statsContainer}>
          <View style={[
            styles.statsCard,
            { 
              backgroundColor: theme.colors.cardBackground,
            }
          ]}>
            <View style={styles.statsContent}>
              <View>
                <Text style={[styles.statsValue, { color: theme.colors.text }]}>
                  {weeklyProgress}%
                </Text>
                <Text style={[styles.statsLabel, { color: theme.colors.subtext }]}>
                  Weekly Progress
                </Text>
              </View>
              <View style={[
                styles.statsIconContainer,
                { backgroundColor: theme.colors.primary + '15' }
              ]}>
                <Ionicons 
                  name="trending-up" 
                  size={24} 
                  color={theme.colors.primary} 
                />
              </View>
            </View>
            <View style={styles.progressBarContainer}>
              <View style={[
                styles.progressBar,
                { backgroundColor: theme.colors.background }
              ]}>
                <View 
                  style={[
                    styles.progressFill,
                    { 
                      backgroundColor: theme.colors.primary,
                      width: `${weeklyProgress}%`
                    }
                  ]} 
                />
              </View>
            </View>
          </View>

          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Today's Schedule
            </Text>
            <TouchableOpacity
              style={[
                buttonStyles.addTaskButton,
                { backgroundColor: theme.colors.primary + '15' }
              ]}
              onPress={() => setShowCreateModal(true)}
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

          {loading && !tasks.length ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={theme.colors.primary} />
            </View>
          ) : error ? (
            <View style={styles.errorContainer}>
              <Ionicons 
                name="alert-circle-outline" 
                size={24} 
                color={theme.colors.error} 
              />
              <Text style={[styles.errorText, { color: theme.colors.error }]}>
                {error}
              </Text>
              <TouchableOpacity
                style={[styles.retryButton, { backgroundColor: theme.colors.primary }]}
                onPress={refreshTasks}
              >
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          ) : todaysTasks.length === 0 ? (
            <View style={[
              styles.emptyState,
              { backgroundColor: theme.colors.cardBackground }
            ]}>
              <Ionicons 
                name="document-text-outline" 
                size={32} 
                color={theme.colors.subtext} 
              />
              <Text style={[styles.emptyStateText, { color: theme.colors.text }]}>
                No tasks for today
              </Text>
              <Text style={[styles.emptyStateSubtext, { color: theme.colors.subtext }]}>
                Add a task to get started
              </Text>
            </View>
          ) : (
            <DailySchedule
              tasks={todaysTasks}
              onTaskPress={handleTaskPress}
            />
          )}

          <View style={[
            styles.quickStatsCard,
            { 
              backgroundColor: theme.colors.cardBackground,
            }
          ]}>
            <View style={styles.quickStatsHeader}>
              <View>
                <Text style={[styles.quickStatsTitle, { color: theme.colors.text }]}>
                  Quick Stats
                </Text>
                <Text style={[styles.quickStatsSubtitle, { color: theme.colors.subtext }]}>
                  Your study overview
                </Text>
              </View>
              <TouchableOpacity
                style={[
                  buttonStyles.quickStatsButton,
                  { backgroundColor: theme.colors.primary + '15' }
                ]}
                onPress={() => {/* Handle view all */}}
              >
                <Text style={[styles.quickStatsButtonText, { color: theme.colors.primary }]}>
                  View All
                </Text>
                <Ionicons name="chevron-forward" size={16} color={theme.colors.primary} />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>

      <TaskCreateModal
        visible={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateTask}
        theme={theme}
      />

      <TaskDetailsModal
        visible={!!selectedTask}
        onClose={() => setSelectedTask(null)}
        task={selectedTask}
        theme={theme}
        onStatusChange={handleTaskStatusChange}
      />

      <TouchableOpacity
        style={[
          buttonStyles.aiButton,
          { bottom: 60 }
        ]}
        onPress={() => setShowAIChat(true)}
        activeOpacity={0.85}
      >
        <Ionicons name="sparkles" size={28} color={theme.colors.primary} />
      </TouchableOpacity>
      <AIChatModal
        visible={showAIChat}
        onClose={() => setShowAIChat(false)}
      />
    </View>
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
  statsContainer: {
    gap: 24,
  },
  statsCard: {
    borderRadius: 20,
    padding: 20,
  },
  statsContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  statsValue: {
    fontSize: 32,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  statsLabel: {
    fontSize: 15,
    letterSpacing: 0.2,
  },
  statsIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressBarContainer: {
    marginTop: 8,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
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
  addTaskText: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  tasksList: {
    gap: 12,
  },
  loadingContainer: {
    padding: 32,
    alignItems: 'center',
  },
  errorContainer: {
    padding: 32,
    alignItems: 'center',
    gap: 8,
  },
  errorText: {
    fontSize: 16,
    fontWeight: '500',
  },
  emptyState: {
    padding: 32,
    borderRadius: 20,
    alignItems: 'center',
    gap: 12,
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
  quickStatsCard: {
    borderRadius: 20,
    padding: 20,
  },
  quickStatsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  quickStatsTitle: {
    fontSize: 20,
    fontWeight: '600',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  quickStatsSubtitle: {
    fontSize: 14,
    letterSpacing: 0.2,
  },
  quickStatsButtonText: {
    fontSize: 14,
    fontWeight: '600',
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