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
import { 
  Plus,
  CheckSquare,
  ListTodo,
  BarChart3,
  Calendar,
} from 'lucide-react-native';


import CompletionRing from '../../components/CompletionRing';
import AIAssistantButton from '../../components/AgentButton';
import TaskCreateModal from '../../components/TaskCreateModal';
import AIAssistantModal from '../../components/AgentModal';
import DailySummaryCard from '../../components/DailySummaryCard';
import SimpleTodosCard from '../../components/SimpleTodosCard';
import TasksCard from '../../components/TasksCard';
import EventsCard from '../../components/EventsCard';
import { useTasks, Task } from '../../contexts/TaskContext';
import { useTheme } from '../../contexts/ThemeContext';

export default function HomeScreen() {
  const { tasks, refreshTasks, loading } = useTasks();
  const { currentTheme } = useTheme();
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  
  // Calculate completion percentage
  const completedTasks = tasks.filter(task => task.status === 'completed').length;
  const completion = tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0;
  
  // Get current time of day for greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  const handleCloseTaskModal = () => {
    setShowTaskModal(false);
    setEditingTask(null);
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <StatusBar barStyle="light-content" />
      
      <View style={{ flex: 1 }}>
        {/* Header with Greeting and Progress */}
        <View style={styles.header}>
          <View>
            <Text style={[styles.greeting, { color: currentTheme.colors.textPrimary }]}>{getGreeting()}, Conner</Text>
            <Text style={[styles.date, { color: currentTheme.colors.textSecondary }]}>
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
            <Text style={[styles.progressText, { color: currentTheme.colors.textPrimary }]}>{completion}%</Text>
          </View>
        </View>

        <ScrollView 
          style={styles.content}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={refreshTasks}
              tintColor="#FFFFFF"
              colors={["#FFFFFF"]}
              progressBackgroundColor="transparent"
            />
          }
        >
          <DailySummaryCard />

          {/* To-Dos Section */}
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionLabel, { color: currentTheme.colors.textSecondary }]}>
              TO-DOS
            </Text>
            <ListTodo size={16} color={currentTheme.colors.textSecondary} />
          </View>
          <SimpleTodosCard />

          {/* Tasks Section */}
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionLabel, { color: currentTheme.colors.textSecondary }]}>
              TASKS
            </Text>
            <CheckSquare size={16} color={currentTheme.colors.textSecondary} />
          </View>
          <TasksCard />

          {/* Events Section */}
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionLabel, { color: currentTheme.colors.textSecondary }]}>
              EVENTS
            </Text>
            <Calendar size={16} color={currentTheme.colors.textSecondary} />
          </View>
          <EventsCard />
        </ScrollView>
      </View>

      <AIAssistantButton onPress={() => setShowAIModal(true)} />

      <TaskCreateModal 
        visible={showTaskModal} 
        onClose={handleCloseTaskModal}
        editingTask={editingTask}
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
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  date: {
    fontSize: 16,
  },
  progressContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressText: {
    position: 'absolute',
    fontSize: 12,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  
  // Section Styles
  section: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  sectionTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  
  // Sort Toggles
  sortToggles: {
    flexDirection: 'row',
    gap: 6,
  },
  sortToggle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    backgroundColor: 'transparent',
  },
  sortToggleActive: {
    borderColor: 'rgba(255, 255, 255, 0.4)',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  
  // Priority Items
  priorityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    paddingVertical: 4,
  },
  urgencyIndicator: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  priorityContent: {
    flex: 1,
  },
  priorityTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  priorityMeta: {
    fontSize: 13,
    opacity: 0.8,
  },
  
  // Time Blocks
  timeBlock: {
    marginBottom: 24,
  },
  timeBlockHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  timeBlockTitle: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    opacity: 0.7,
    marginRight: 12,
  },
  timeBlockDivider: {
    flex: 1,
    height: 1,
    opacity: 0.1,
  },
  timeBlockTaskCard: {
    marginBottom: 8,
  },
  
  // Add Task Button
  addTaskButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  addTaskText: {
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 3,
  },
  
  // Loading & Empty States
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    fontSize: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
  },
});