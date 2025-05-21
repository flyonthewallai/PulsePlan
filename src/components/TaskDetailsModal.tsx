import React from 'react';
import { View, Text, Modal, StyleSheet, TouchableOpacity, ScrollView, Animated, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Task } from '../contexts/TaskContext';
import { Theme } from '../contexts/ThemeContext';
import { useModalAnimation } from '../hooks/useModalAnimation';

interface TaskDetailsModalProps {
  visible: boolean;
  onClose: () => void;
  task: Task | null;
  theme: Theme;
  onStatusChange?: (status: Task['status']) => void;
  onPriorityChange?: (priority: Task['priority']) => void;
}

const getPriorityColor = (priority: Task['priority'], theme: Theme) => {
  const colors = {
    low: theme.colors.success,
    medium: theme.colors.warning,
    high: theme.colors.error,
  };
  return colors[priority];
};

const getStatusIcon = (status: Task['status']) => {
  const icons = {
    pending: 'time-outline',
    in_progress: 'sync-outline',
    completed: 'checkmark-circle-outline',
  };
  return icons[status];
};

export const TaskDetailsModal: React.FC<TaskDetailsModalProps> = ({
  visible,
  onClose,
  task,
  theme,
  onStatusChange,
  onPriorityChange,
}) => {
  if (!task) return null;

  const {
    translateY,
    opacity,
    overlayOpacity,
    handleClose,
    modalHeight
  } = useModalAnimation({
    isVisible: visible,
    onClose,
    modalHeight: Dimensions.get('window').height * 0.8,
    animationDuration: 300
  });

  const priorityColor = getPriorityColor(task.priority, theme);
  const statusIcon = getStatusIcon(task.status);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={handleClose}
    >
      <Animated.View 
        style={[
          styles.modalOverlay,
          { opacity: overlayOpacity }
        ]}
      >
        <TouchableOpacity 
          style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
          activeOpacity={1} 
          onPress={handleClose}
        />
        <Animated.View 
          style={[
            styles.modalContent,
            { 
              backgroundColor: theme.colors.background + 'F0',
              shadowColor: theme.colors.primary,
              shadowOffset: { width: 0, height: 8 },
              shadowOpacity: 0.15,
              shadowRadius: 24,
              elevation: 12,
              borderWidth: 1,
              borderColor: theme.colors.border + '20',
              transform: [{ translateY }],
              opacity,
              maxHeight: modalHeight
            }
          ]}
        >
          <View style={styles.modalHeader}>
            <TouchableOpacity
              style={[styles.closeButton, { backgroundColor: theme.colors.cardBackground }]}
              onPress={handleClose}
            >
              <Ionicons name="close" size={24} color={theme.colors.text} />
            </TouchableOpacity>
          </View>

          <ScrollView 
            style={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.taskHeader}>
              <Text style={[styles.taskTitle, { color: theme.colors.text }]}>
                {task.title}
              </Text>
              <View style={styles.taskMeta}>
                <View style={[styles.priorityBadge, { backgroundColor: priorityColor + '15' }]}>
                  <Text style={[styles.priorityText, { color: priorityColor }]}>
                    {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                  </Text>
                </View>
                <TouchableOpacity
                  style={[styles.statusButton, { backgroundColor: theme.colors.primary + '15' }]}
                  onPress={() => onStatusChange?.(task.status === 'completed' ? 'pending' : 'completed')}
                >
                  <Ionicons 
                    name={statusIcon} 
                    size={20} 
                    color={theme.colors.primary} 
                  />
                  <Text style={[styles.statusText, { color: theme.colors.primary }]}>
                    {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
                Description
              </Text>
              <Text style={[styles.description, { color: theme.colors.subtext }]}>
                {task.description || 'No description provided'}
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
                Details
              </Text>
              <View style={styles.detailsGrid}>
                <View style={styles.detailItem}>
                  <Ionicons name="book-outline" size={20} color={theme.colors.subtext} />
                  <Text style={[styles.detailText, { color: theme.colors.subtext }]}>
                    {task.subject}
                  </Text>
                </View>
                <View style={styles.detailItem}>
                  <Ionicons name="calendar-outline" size={20} color={theme.colors.subtext} />
                  <Text style={[styles.detailText, { color: theme.colors.subtext }]}>
                    {new Date(task.due_date).toLocaleDateString()}
                  </Text>
                </View>
                {task.estimated_minutes && (
                  <View style={styles.detailItem}>
                    <Ionicons name="time-outline" size={20} color={theme.colors.subtext} />
                    <Text style={[styles.detailText, { color: theme.colors.subtext }]}>
                      {task.estimated_minutes} minutes
                    </Text>
                  </View>
                )}
              </View>
            </View>

            <View style={[styles.section, styles.aiSection]}>
              <View style={styles.aiHeader}>
                <Ionicons name="sparkles" size={20} color={theme.colors.primary} />
                <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
                  AI Insights
                </Text>
              </View>
              <View style={[styles.aiContent, { backgroundColor: theme.colors.primary + '15' }]}>
                <Text style={[styles.aiText, { color: theme.colors.text }]}>
                  {task.status === 'completed' 
                    ? 'Great job completing this task! Consider reviewing similar tasks to optimize your workflow.'
                    : task.priority === 'high'
                    ? 'This high-priority task might benefit from breaking it down into smaller subtasks.'
                    : 'You\'re making good progress. Consider scheduling focused time blocks for this task.'}
                </Text>
              </View>
            </View>
          </ScrollView>
        </Animated.View>
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    minHeight: '80%',
    maxHeight: '90%',
  },
  modalHeader: {
    padding: 16,
    alignItems: 'flex-end',
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    padding: 16,
  },
  taskHeader: {
    marginBottom: 24,
  },
  taskTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  taskMeta: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  priorityBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  priorityText: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  statusButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 4,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  description: {
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.2,
  },
  detailsGrid: {
    gap: 12,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailText: {
    fontSize: 16,
    letterSpacing: 0.2,
  },
  aiSection: {
    marginTop: 8,
  },
  aiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  aiContent: {
    padding: 16,
    borderRadius: 16,
  },
  aiText: {
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.2,
  },
}); 