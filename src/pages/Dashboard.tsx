import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { TaskCard } from '../components/TaskCard';
import { TaskCreateModal } from '../components/TaskCreateModal';
import { useAuth } from '../contexts/AuthContext';
import { API_URL, getApiUrl } from '../config/api';

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

export const Dashboard = ({ darkMode, onTaskClick }: { darkMode: boolean, onTaskClick: (task: Task) => void }) => {
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
          darkMode ? styles.darkContainer : styles.lightContainer
        ]}
        contentContainerStyle={styles.contentContainer}
      >
        <View style={styles.header}>
          <Text style={[styles.headerTitle, darkMode ? styles.darkText : styles.lightText]}>
            Welcome back!
          </Text>
          <Text style={darkMode ? styles.darkSubtext : styles.lightSubtext}>
            Let's make today productive
          </Text>
        </View>

        <View style={styles.statsContainer}>
          <View style={[
            styles.statsCard,
            darkMode ? styles.darkStatsCard : styles.lightStatsCard
          ]}>
            <View style={styles.statsContent}>
              <View>
                <Text style={[styles.statsValue, darkMode ? styles.darkText : styles.lightText]}>
                  85%
                </Text>
                <Text style={[styles.statsLabel, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                  Weekly Progress
                </Text>
              </View>
              <View style={styles.statsIconContainer}>
                <View style={styles.statsIconBackground}>
                  <View style={[
                    styles.statsIconInner,
                    darkMode ? styles.darkStatsIconInner : styles.lightStatsIconInner
                  ]}>
                    <Text style={styles.statsIconText}>📚</Text>
                  </View>
                </View>
              </View>
            </View>
          </View>

          <View style={styles.tasksList}>
            {loading ? (
              <ActivityIndicator size="large" color="#00AEEF" />
            ) : error ? (
              <Text style={{ color: 'red', textAlign: 'center' }}>{error}</Text>
            ) : tasks.length === 0 ? (
              <Text style={{ textAlign: 'center', color: darkMode ? '#D1D5DB' : '#6B7280' }}>
                No tasks for today. Add one!
              </Text>
            ) : (
              tasks.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onPress={() => onTaskClick(task)}
                  darkMode={darkMode}
                />
              ))
            )}
          </View>

          <View style={[
            styles.quickStatsCard,
            darkMode ? styles.darkQuickStatsCard : styles.lightQuickStatsCard
          ]}>
            <View style={styles.quickStatsHeader}>
              <View>
                <Text style={[styles.quickStatsTitle, darkMode ? styles.darkText : styles.lightText]}>
                  Quick Stats
                </Text>
                <Text style={[styles.quickStatsSubtitle, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                  Your study overview
                </Text>
              </View>
              <TouchableOpacity
                style={styles.quickStatsButton}
                onPress={() => {/* Handle view all */}}
              >
                <Text style={styles.quickStatsButtonText}>View All</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>
      <TouchableOpacity
        style={[styles.fab, darkMode ? styles.darkFab : styles.lightFab]}
        onPress={() => setShowCreateModal(true)}
        activeOpacity={0.8}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
      <TaskCreateModal
        visible={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={createTask}
        darkMode={darkMode}
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
    paddingBottom: 80,
  },
  darkContainer: {
    backgroundColor: '#0D1B2A',
  },
  lightContainer: {
    backgroundColor: '#F9FAFB',
  },
  header: {
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  darkText: {
    color: '#FFFFFF',
  },
  lightText: {
    color: '#0D1B2A',
  },
  darkSubtext: {
    color: '#D1D5DB',
  },
  lightSubtext: {
    color: '#6B7280',
  },
  statsContainer: {
    gap: 16,
  },
  statsCard: {
    height: 96,
    borderRadius: 12,
    padding: 16,
  },
  darkStatsCard: {
    backgroundColor: 'rgba(0, 174, 239, 0.2)',
  },
  lightStatsCard: {
    backgroundColor: 'rgba(0, 174, 239, 0.1)',
  },
  statsContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  statsValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statsLabel: {
    fontSize: 14,
  },
  statsIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(0, 174, 239, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statsIconBackground: {
    width: 48,
    height: 48,
    borderRadius: 24,
  },
  statsIconInner: {
    width: 32,
    height: 32,
    borderRadius: 16,
    margin: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  darkStatsIconInner: {
    backgroundColor: '#0D1B2A',
  },
  lightStatsIconInner: {
    backgroundColor: '#FFFFFF',
  },
  statsIconText: {
    fontSize: 16,
  },
  tasksList: {
    gap: 8,
  },
  quickStatsCard: {
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  darkQuickStatsCard: {
    backgroundColor: '#1F2937',
  },
  lightQuickStatsCard: {
    backgroundColor: '#FFFFFF',
  },
  quickStatsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  quickStatsTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  quickStatsSubtitle: {
    fontSize: 12,
  },
  quickStatsButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: '#00AEEF',
  },
  quickStatsButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '500',
  },
  fab: {
    position: 'absolute',
    right: 24,
    bottom: 32,
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    zIndex: 10,
  },
  fabText: {
    fontSize: 32,
    color: '#fff',
    fontWeight: 'bold',
    marginTop: -2,
  },
  darkFab: {
    backgroundColor: '#00AEEF',
  },
  lightFab: {
    backgroundColor: '#00AEEF',
  },
});