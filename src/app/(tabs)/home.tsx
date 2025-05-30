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
import { Plus } from 'lucide-react-native';

import { colors } from '../../constants/theme';
import TaskCard from '../../components/TaskCard';
import CompletionRing from '../../components/CompletionRing';
import AIAssistantButton from '../../components/AIAssistantButton';
import TaskCreateModal from '../../components/TaskCreateModal';
import AIAssistantModal from '../../components/AIAssistantModal';
import { useTasks } from '../../contexts/TaskContext';

export default function HomeScreen() {
  const { tasks, loading, refreshTasks } = useTasks();
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  
  // Calculate completion percentage based on real tasks
  const completedTasks = tasks.filter(task => task.status === 'completed').length;
  const completion = tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0;
  
  // Filter tasks for today
  const today = new Date().toDateString();
  const todayTasks = tasks.filter(task => {
    const taskDate = new Date(task.due_date).toDateString();
    return taskDate === today;
  });
  
  // Get current time of day for greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>{getGreeting()}, Conner</Text>
          <Text style={styles.date}>
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long',
              month: 'long', 
              day: 'numeric' 
            })}
          </Text>
        </View>
        <View style={styles.progressContainer}>
          <CompletionRing 
            percentage={completion} 
            size={50} 
            strokeWidth={5}
          />
          <Text style={styles.progressText}>{completion}%</Text>
        </View>
      </View>

      <View style={styles.todayContainer}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Today's Plan</Text>
          <TouchableOpacity 
            style={styles.addTaskButton}
            onPress={() => setShowTaskModal(true)}
          >
            <Plus size={16} color={colors.primaryBlue} />
            <Text style={styles.addTaskText}>Add Task</Text>
          </TouchableOpacity>
        </View>
        <ScrollView 
          style={styles.taskContainer}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.taskList}
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
          {loading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Loading tasks...</Text>
            </View>
          ) : todayTasks.length > 0 ? (
            todayTasks.map((task, index) => (
              <TaskCard 
                key={task.id} 
                task={task} 
                isFirst={index === 0}
                isLast={index === todayTasks.length - 1}
              />
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyTitle}>No tasks for today</Text>
              <Text style={styles.emptyText}>
                Create your first task to get started with PulsePlan!
              </Text>
            </View>
          )}
        </ScrollView>
      </View>

      <AIAssistantButton onPress={() => setShowAIModal(true)} />

      <TaskCreateModal 
        visible={showTaskModal} 
        onClose={() => setShowTaskModal(false)} 
      />

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
    paddingBottom: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  date: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  progressContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressText: {
    position: 'absolute',
    color: colors.textPrimary,
    fontSize: 12,
    fontWeight: '600',
  },
  todayContainer: {
    flex: 1,
    paddingHorizontal: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  addTaskButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  addTaskText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primaryBlue,
    marginLeft: 8,
  },
  taskContainer: {
    paddingBottom: 100,
  },
  taskList: {
    paddingBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: colors.textSecondary,
  },
});