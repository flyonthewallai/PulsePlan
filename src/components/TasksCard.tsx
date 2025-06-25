import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  Animated,
} from 'react-native';
import { X, Calendar, Clock } from 'lucide-react-native';
import { GestureHandlerRootView, PanGestureHandler as RNGHPanGestureHandler, State as GestureState } from 'react-native-gesture-handler';
import { useTheme } from '@/contexts/ThemeContext';
import { useTasks } from '@/contexts/TaskContext';

interface TasksCardProps {
  onPress?: () => void;
}

const TasksCard: React.FC<TasksCardProps> = ({ onPress }) => {
  const { currentTheme } = useTheme();
  const { tasks, toggleTask } = useTasks();
  const [showModal, setShowModal] = useState(false);
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
  const cardTranslateX = React.useRef(new Animated.Value(0)).current;

  // Filter to current/upcoming tasks (not completed)
  const currentTasks = tasks.filter(task => task.status !== 'completed');

  // Card swipe handlers
  const onCardGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: cardTranslateX } }],
    { useNativeDriver: true }
  );

  const onCardHandlerStateChange = (event: any) => {
    const { state, translationX: gestureTranslationX, velocityX } = event.nativeEvent;
    
    if (state === GestureState.END) {
      // If swiped left significantly or with high velocity, go to next task
      if ((gestureTranslationX < -40 || velocityX < -200) && currentTasks.length > 1) {
        // Animate slide out to left
        Animated.timing(cardTranslateX, {
          toValue: -400,
          duration: 150,
          useNativeDriver: true,
        }).start(() => {
          // Update to next task
          setCurrentTaskIndex((prevIndex) => (prevIndex + 1) % currentTasks.length);
          // Reset position and animate in from right
          cardTranslateX.setValue(400);
          Animated.timing(cardTranslateX, {
            toValue: 0,
            duration: 150,
            useNativeDriver: true,
          }).start();
        });
      }
      // If swiped right significantly or with high velocity, go to previous task
      else if ((gestureTranslationX > 40 || velocityX > 200) && currentTasks.length > 1) {
        // Animate slide out to right
        Animated.timing(cardTranslateX, {
          toValue: 400,
          duration: 150,
          useNativeDriver: true,
        }).start(() => {
          // Update to previous task
          setCurrentTaskIndex((prevIndex) => (prevIndex - 1 + currentTasks.length) % currentTasks.length);
          // Reset position and animate in from left
          cardTranslateX.setValue(-400);
          Animated.timing(cardTranslateX, {
            toValue: 0,
            duration: 150,
            useNativeDriver: true,
          }).start();
        });
      } else {
        // Snap back to original position
        Animated.spring(cardTranslateX, {
          toValue: 0,
          tension: 120,
          friction: 10,
          useNativeDriver: true,
        }).start();
      }
    } else if (state === GestureState.CANCELLED || state === GestureState.FAILED) {
      // Reset position if gesture is cancelled
      Animated.spring(cardTranslateX, {
        toValue: 0,
        tension: 120,
        friction: 10,
        useNativeDriver: true,
      }).start();
    }
  };

  const currentTask = currentTasks[currentTaskIndex] || currentTasks[0];

  const handleToggleTask = (taskId: string) => {
    toggleTask(taskId);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#FF3B30';
      case 'medium': return '#FF9500';
      case 'low': return '#34C759';
      default: return '#666666';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <GestureHandlerRootView>
      <RNGHPanGestureHandler
        onGestureEvent={onCardGestureEvent}
        onHandlerStateChange={onCardHandlerStateChange}
        activeOffsetX={[-10, 10]}
        failOffsetY={[-30, 30]}
        shouldCancelWhenOutside={false}
      >
        <Animated.View
          style={{
            transform: [{ translateX: cardTranslateX }],
          }}
        >
          <TouchableOpacity
            style={styles.card}
            onPress={() => setShowModal(true)}
            activeOpacity={0.8}
          >
            <View style={styles.cardContent}>
              {/* Current task item */}
              <View style={styles.taskItem}>
                <TouchableOpacity
                  style={[
                    styles.checkbox,
                    currentTask?.status === 'completed' && styles.checkboxCompleted
                  ]}
                  onPress={() => currentTask && handleToggleTask(currentTask.id)}
                >
                  {currentTask?.status === 'completed' && (
                    <Text style={styles.checkmark}>✓</Text>
                  )}
                </TouchableOpacity>
                <View style={styles.taskContent}>
                  <Text style={[
                    styles.taskText,
                    { color: currentTheme.colors.textPrimary },
                    currentTask?.status === 'completed' && { 
                      textDecorationLine: 'line-through',
                      color: currentTheme.colors.textSecondary 
                    }
                  ]}>
                    {currentTask?.title || 'No tasks yet'}
                  </Text>
                  {currentTask && (
                    <Text style={[styles.taskMeta, { color: currentTheme.colors.textSecondary }]}>
                      {formatDate(currentTask.due_date)} • {formatTime(currentTask.due_date)}
                    </Text>
                  )}
                </View>
              </View>

              {/* Status indicator */}
              {currentTasks.length > 1 && (
                <Text style={[styles.statusText, { color: currentTheme.colors.textSecondary }]}>
                  {currentTaskIndex + 1} of {currentTasks.length}
                </Text>
              )}

              {/* Progress indicators */}
              <View style={styles.progressContainer}>
                {currentTasks.slice(0, 4).map((task, index) => (
                  <View
                    key={task.id}
                    style={[
                      styles.progressDot,
                      { backgroundColor: getPriorityColor(task.priority) },
                      index === currentTaskIndex && styles.progressDotActive
                    ]}
                  />
                ))}
                {currentTasks.length > 4 && (
                  <Text style={styles.moreIndicator}>•••</Text>
                )}
              </View>
            </View>
          </TouchableOpacity>
        </Animated.View>
      </RNGHPanGestureHandler>

      {/* Full Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <GestureHandlerRootView style={{ flex: 1 }}>
          <View style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
          {/* Header */}
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowModal(false)}>
              <X size={24} color={currentTheme.colors.textPrimary} />
            </TouchableOpacity>
            <Text style={[styles.modalTitle, { color: currentTheme.colors.textPrimary }]}>
              Tasks
            </Text>
            <View style={{ width: 24 }} />
          </View>

          {/* Tasks list */}
          <ScrollView style={styles.tasksList} showsVerticalScrollIndicator={false}>
            {currentTasks.map((task) => (
              <TouchableOpacity
                key={task.id}
                style={[styles.modalTaskItem, { backgroundColor: currentTheme.colors.surface }]}
                onPress={() => handleToggleTask(task.id)}
              >
                <TouchableOpacity
                  style={[
                    styles.modalCheckbox,
                    { borderColor: currentTheme.colors.border },
                    task.status === 'completed' && { backgroundColor: getPriorityColor(task.priority), borderColor: getPriorityColor(task.priority) }
                  ]}
                  onPress={() => handleToggleTask(task.id)}
                >
                  {task.status === 'completed' && (
                    <Text style={styles.modalCheckmark}>✓</Text>
                  )}
                </TouchableOpacity>
                <View style={styles.modalTaskContent}>
                  <Text style={[
                    styles.modalTaskText,
                    { color: currentTheme.colors.textPrimary },
                    task.status === 'completed' && { 
                      textDecorationLine: 'line-through',
                      color: currentTheme.colors.textSecondary 
                    }
                  ]}>
                    {task.title}
                  </Text>
                  <View style={styles.modalTaskMeta}>
                    <View style={styles.taskMetaItem}>
                      <Calendar size={12} color={currentTheme.colors.textSecondary} />
                      <Text style={[styles.taskMetaText, { color: currentTheme.colors.textSecondary }]}>
                        {formatDate(task.due_date)}
                      </Text>
                    </View>
                    <View style={styles.taskMetaItem}>
                      <Clock size={12} color={currentTheme.colors.textSecondary} />
                      <Text style={[styles.taskMetaText, { color: currentTheme.colors.textSecondary }]}>
                        {formatTime(task.due_date)}
                      </Text>
                    </View>
                    <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(task.priority) + '20' }]}>
                      <Text style={[styles.priorityText, { color: getPriorityColor(task.priority) }]}>
                        {task.priority.toUpperCase()}
                      </Text>
                    </View>
                  </View>
                </View>
              </TouchableOpacity>
            ))}

            {currentTasks.length === 0 && (
              <View style={styles.emptyState}>
                <Text style={[styles.emptyText, { color: currentTheme.colors.textSecondary }]}>
                  No current tasks
                </Text>
                <Text style={[styles.emptySubtext, { color: currentTheme.colors.textSecondary }]}>
                  Create a new task to get started
                </Text>
              </View>
            )}
          </ScrollView>
        </View>
        </GestureHandlerRootView>
      </Modal>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#000000',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    padding: 16,
    marginBottom: 24,
  },
  cardContent: {
    gap: 8,
  },
  taskItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#666666',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  checkboxCompleted: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  checkmark: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  taskContent: {
    flex: 1,
  },
  taskText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  taskMeta: {
    fontSize: 12,
    fontWeight: '500',
  },
  statusText: {
    fontSize: 14,
    marginLeft: 32,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginLeft: 32,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  progressDotActive: {
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.6)',
  },
  moreIndicator: {
    color: '#666666',
    fontSize: 16,
    fontWeight: '600',
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  tasksList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  modalTaskItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    borderRadius: 12,
    gap: 12,
    marginBottom: 8,
  },
  modalCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  modalCheckmark: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  modalTaskContent: {
    flex: 1,
  },
  modalTaskText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  modalTaskMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
  },
  taskMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  taskMetaText: {
    fontSize: 12,
    fontWeight: '500',
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
  },
});

export default TasksCard; 