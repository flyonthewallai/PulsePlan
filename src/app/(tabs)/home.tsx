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
  Flame, 
  Clock, 
  AlertTriangle, 
  BookOpen,
  Target,
  Timer,
  FileText,
  Zap,
} from 'lucide-react-native';

import TaskCard from '../../components/TaskCard';
import CompletionRing from '../../components/CompletionRing';
import AIAssistantButton from '../../components/AIAssistantButton';
import TaskCreateModal from '../../components/TaskCreateModal';
import AIAssistantModal from '../../components/AIAssistantModal';
import StreakModal from '../../components/StreakModal';
import { useTasks, Task } from '../../contexts/TaskContext';
import { useTheme } from '../../contexts/ThemeContext';

type SortType = 'due' | 'priority' | 'subject';

export default function HomeScreen() {
  const { tasks, loading, refreshTasks } = useTasks();
  const { currentTheme } = useTheme();
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const [showStreakModal, setShowStreakModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [sortBy, setSortBy] = useState<SortType>('due');
  
  // Calculate completion percentage and streak
  const completedTasks = tasks.filter(task => task.status === 'completed').length;
  const completion = tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0;
  
  // Mock streak data (would come from context/storage in real app)
  const streakData = {
    currentStreak: 3,
    weeklyHours: 9,
    isActive: true
  };
  
  // Filter tasks for today
  const today = new Date().toDateString();
  const todayTasks = tasks.filter(task => {
    const taskDate = new Date(task.due_date).toDateString();
    return taskDate === today;
  });
  
  // Get priority tasks (high priority or due soon)
  const getPriorityTasks = () => {
    const now = new Date();
    const urgent = tasks.filter(task => {
      const dueDate = new Date(task.due_date);
      const hoursUntilDue = (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60);
      return (task.priority === 'high' || hoursUntilDue <= 24) && task.status !== 'completed';
    });
    
    // Sort based on selected criteria
    return urgent.sort((a, b) => {
      if (sortBy === 'due') {
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      } else if (sortBy === 'priority') {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      } else {
        return a.subject.localeCompare(b.subject);
      }
    }).slice(0, 3); // Show max 3 priority tasks
  };
  
  // Group today's tasks by time blocks
  const getTimeBlocks = () => {
    const blocks = {
      morning: [] as Task[],
      afternoon: [] as Task[],
      evening: [] as Task[]
    };
    
    todayTasks.forEach(task => {
      const hour = new Date(task.due_date).getHours();
      if (hour < 12) {
        blocks.morning.push(task);
      } else if (hour < 18) {
        blocks.afternoon.push(task);
      } else {
        blocks.evening.push(task);
      }
    });
    
    return blocks;
  };
  
  // Get current time of day for greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };
  
  const formatDuration = (minutes?: number) => {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0 && mins > 0) return `${hours}h ${mins}m`;
    if (hours > 0) return `${hours}h`;
    return `${mins}m`;
  };
  
  const getUrgencyEmoji = (task: Task) => {
    const now = new Date();
    const dueDate = new Date(task.due_date);
    const hoursUntilDue = (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60);
    
    if (hoursUntilDue <= 2) return '🔥🔥';
    if (hoursUntilDue <= 24 || task.priority === 'high') return '🔥';
    return '⚠️';
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setShowTaskModal(true);
  };

  const handleCloseTaskModal = () => {
    setShowTaskModal(false);
    setEditingTask(null);
  };
  
  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'quick_task':
        setShowTaskModal(true);
        break;
      case 'focus_mode':
        // TODO: Implement focus mode/timer
        break;
      case 'templates':
        // TODO: Implement templates
        break;
    }
  };

  const priorityTasks = getPriorityTasks();
  const timeBlocks = getTimeBlocks();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <StatusBar barStyle="light-content" />
      
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
            tintColor={currentTheme.colors.primary}
            colors={[currentTheme.colors.primary]}
            progressBackgroundColor="transparent"
          />
        }
      >
        {/* Streak + Progress Widget */}
        <TouchableOpacity 
          style={[styles.streakWidget, { backgroundColor: currentTheme.colors.surface }]}
          onPress={() => setShowStreakModal(true)}
          activeOpacity={0.7}
        >
          <View style={styles.streakContent}>
            <Text style={styles.streakEmoji}>🌱</Text>
            <View style={styles.streakInfo}>
              <Text style={[styles.streakText, { color: currentTheme.colors.textPrimary }]}>
                {streakData.currentStreak}-day streak
              </Text>
              <Text style={[styles.streakSubtext, { color: currentTheme.colors.textSecondary }]}>
                {streakData.weeklyHours}h completed this week
              </Text>
            </View>
            {streakData.isActive && (
              <View style={[styles.streakBadge, { backgroundColor: currentTheme.colors.primary }]}>
                <Zap size={12} color="#FFFFFF" />
              </View>
            )}
          </View>
        </TouchableOpacity>

        {/* Priority Overview Section */}
        {priorityTasks.length > 0 && (
          <View style={[styles.section, { backgroundColor: currentTheme.colors.surface }]}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionTitleContainer}>
                <Flame size={18} color="#FF5757" />
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>Priority Focus</Text>
              </View>
              <View style={styles.sortToggles}>
                <TouchableOpacity
                  style={[styles.sortToggle, sortBy === 'due' && { backgroundColor: currentTheme.colors.primary }]}
                  onPress={() => setSortBy('due')}
                >
                  <Clock size={12} color={sortBy === 'due' ? '#FFFFFF' : currentTheme.colors.textSecondary} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.sortToggle, sortBy === 'priority' && { backgroundColor: currentTheme.colors.primary }]}
                  onPress={() => setSortBy('priority')}
                >
                  <AlertTriangle size={12} color={sortBy === 'priority' ? '#FFFFFF' : currentTheme.colors.textSecondary} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.sortToggle, sortBy === 'subject' && { backgroundColor: currentTheme.colors.primary }]}
                  onPress={() => setSortBy('subject')}
                >
                  <BookOpen size={12} color={sortBy === 'subject' ? '#FFFFFF' : currentTheme.colors.textSecondary} />
                </TouchableOpacity>
              </View>
            </View>
            
            {priorityTasks.map((task, index) => (
              <View key={task.id} style={styles.priorityItem}>
                <Text style={styles.urgencyIndicator}>{getUrgencyEmoji(task)}</Text>
                <View style={styles.priorityContent}>
                  <Text style={[styles.priorityTitle, { color: currentTheme.colors.textPrimary }]} numberOfLines={1}>
                    {task.title}
                  </Text>
                  <Text style={[styles.priorityMeta, { color: currentTheme.colors.textSecondary }]}>
                    Due {new Date(task.due_date).toDateString() === today ? 'Today' : 'Tomorrow'}
                    {task.estimated_minutes && ` • ${formatDuration(task.estimated_minutes)}`}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Today's Plan - Time Blocks with Task Cards */}
        <View style={[styles.section, { backgroundColor: currentTheme.colors.surface }]}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>Today's Plan</Text>
            <TouchableOpacity 
              style={styles.addTaskButton}
              onPress={() => setShowTaskModal(true)}
            >
              <Plus size={16} color={currentTheme.colors.primary} />
              <Text style={[styles.addTaskText, { color: currentTheme.colors.primary }]}>Add Task</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <Text style={[styles.loadingText, { color: currentTheme.colors.textSecondary }]}>Loading tasks...</Text>
            </View>
          ) : todayTasks.length > 0 ? (
            <>
              {timeBlocks.morning.length > 0 && (
                <View style={styles.timeBlock}>
                  <Text style={[styles.timeBlockTitle, { color: currentTheme.colors.textSecondary }]}>🕛 Morning</Text>
                  {timeBlocks.morning.map((task, index) => (
                    <View key={task.id} style={styles.timeBlockTaskCard}>
                      <TaskCard 
                        task={task} 
                        isFirst={index === 0}
                        isLast={index === timeBlocks.morning.length - 1}
                        onEdit={handleEditTask}
                      />
                    </View>
                  ))}
                </View>
              )}
              
              {timeBlocks.afternoon.length > 0 && (
                <View style={styles.timeBlock}>
                  <Text style={[styles.timeBlockTitle, { color: currentTheme.colors.textSecondary }]}>🕒 Afternoon</Text>
                  {timeBlocks.afternoon.map((task, index) => (
                    <View key={task.id} style={styles.timeBlockTaskCard}>
                      <TaskCard 
                        task={task} 
                        isFirst={index === 0}
                        isLast={index === timeBlocks.afternoon.length - 1}
                        onEdit={handleEditTask}
                      />
                    </View>
                  ))}
                </View>
              )}
              
              {timeBlocks.evening.length > 0 && (
                <View style={styles.timeBlock}>
                  <Text style={[styles.timeBlockTitle, { color: currentTheme.colors.textSecondary }]}>🕖 Evening</Text>
                  {timeBlocks.evening.map((task, index) => (
                    <View key={task.id} style={styles.timeBlockTaskCard}>
                      <TaskCard 
                        task={task} 
                        isFirst={index === 0}
                        isLast={index === timeBlocks.evening.length - 1}
                        onEdit={handleEditTask}
                      />
                    </View>
                  ))}
                </View>
              )}
            </>
          ) : (
            <View style={styles.emptyState}>
              <Text style={[styles.emptyTitle, { color: currentTheme.colors.textPrimary }]}>No tasks for today</Text>
              <Text style={[styles.emptyText, { color: currentTheme.colors.textSecondary }]}>
                Create your first task to get started!
              </Text>
            </View>
          )}
        </View>
      </ScrollView>

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
  
  // Streak Widget
  streakWidget: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
  },
  streakContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  streakEmoji: {
    fontSize: 24,
    marginRight: 12,
  },
  streakInfo: {
    flex: 1,
  },
  streakText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  streakSubtext: {
    fontSize: 14,
  },
  streakBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
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
    marginBottom: 16,
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
    gap: 8,
  },
  sortToggle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  
  // Priority Items
  priorityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  urgencyIndicator: {
    fontSize: 16,
    marginRight: 12,
  },
  priorityContent: {
    flex: 1,
  },
  priorityTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  priorityMeta: {
    fontSize: 14,
  },
  
  // Time Blocks
  timeBlock: {
    marginBottom: 20,
  },
  timeBlockTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
    opacity: 0.7,
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
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
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