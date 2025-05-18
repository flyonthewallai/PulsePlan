import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { TaskCard } from '../components/TaskCard';
import { TaskCreateModal } from '../components/TaskCreateModal';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { API_URL, getApiUrl } from '../config/api';
import { Ionicons } from '@expo/vector-icons';

// Define task type
interface Task {
  id: string;
  title: string;
  description: string;
  due_date: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed';
  user_id: string;
}

// Define the form data type for creating a task
type TaskFormData = Omit<Task, 'id' | 'user_id'>;

export const Dashboard = ({ onTaskClick }: { onTaskClick: (task: Task) => void }) => {
  const { theme } = useTheme();
  const { session } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      console.log('Fetching tasks from:', API_URL);
      const res = await fetch(`${API_URL}/tasks`, {
        headers: {
          Authorization: `Bearer ${session?.access_token}`,
        },
      });
      if (!res.ok) {
        const errorText = await res.text();
        console.error('Fetch tasks error:', errorText);
        throw new Error('Failed to fetch tasks');
      }
      const data = await res.json();
      setTasks(data);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError('Could not load tasks.');
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const createTask = async (taskData: TaskFormData) => {
    try {
      console.log('Creating task with data:', taskData);
      console.log('Using API URL:', API_URL);
      console.log('Session token available:', !!session?.access_token);

      const response = await fetch(getApiUrl('/tasks'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify(taskData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Create task error details:', {
          status: response.status,
          statusText: response.statusText,
          errorText,
          headers: Object.fromEntries(response.headers.entries()),
        });
        throw new Error(`Failed to create task: ${response.status} ${response.statusText}`);
      }
      
      const responseData = await response.json();
      console.log('Task created successfully:', responseData);
      
      setShowCreateModal(false);
      fetchTasks();
    } catch (err: unknown) {
      console.error('Task creation error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      Alert.alert('Error', `Could not create task: ${errorMessage}`);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <ScrollView
        style={[
          styles.container,
          { backgroundColor: theme.colors.background }
        ]}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View>
            <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
              Welcome back!
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
                  85%
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
                      width: '85%'
                    }
                  ]} 
                />
              </View>
            </View>
          </View>

          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
              Today's Tasks
            </Text>
            <TouchableOpacity
              style={[
                styles.addTaskButton,
                { backgroundColor: theme.colors.primary }
              ]}
              onPress={() => setShowCreateModal(true)}
            >
              <Ionicons 
                name="add" 
                size={20} 
                color="#FFFFFF" 
              />
              <Text style={styles.addTaskText}>
                Add Task
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.tasksList}>
            {loading ? (
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
              </View>
            ) : tasks.length === 0 ? (
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
              tasks.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onPress={() => onTaskClick(task)}
                />
              ))
            )}
          </View>

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
                  styles.quickStatsButton,
                  { backgroundColor: theme.colors.primary }
                ]}
                onPress={() => {/* Handle view all */}}
              >
                <Text style={styles.quickStatsButtonText}>View All</Text>
                <Ionicons name="chevron-forward" size={16} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>
      <TaskCreateModal
        visible={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={createTask}
        theme={theme}
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
  addTaskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    gap: 4,
    shadowColor: '#00AEEF',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  addTaskText: {
    color: '#FFFFFF',
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
  quickStatsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    gap: 4,
  },
  quickStatsButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
});