import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { 
  Calculator, 
  FlaskConical, 
  Library, 
  Book, 
  GraduationCap, 
  Clock,
  Check,
  Square 
} from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Task, useTasks } from '../contexts/TaskContext';
import TaskDetailsModal from './TaskDetailsModal';

interface TaskCardProps {
  task: Task;
  onEdit?: (task: Task) => void;
}

export default function TaskCard({ task, onEdit }: TaskCardProps) {
  const { updateTask } = useTasks();
  const { currentTheme } = useTheme();
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const priorityColors = {
    high: '#FF3B30',
    medium: '#FF9500',
    low: '#34C759',
  };

  const getPriorityColor = (priority: string) => {
    return priorityColors[priority as keyof typeof priorityColors] || currentTheme.colors.textSecondary;
  };

  const getSubjectIcon = (subject: string) => {
    const iconProps = { size: 14, color: currentTheme.colors.textSecondary };
    
    switch (subject.toLowerCase()) {
      case 'math': return <Calculator {...iconProps} />;
      case 'science': return <FlaskConical {...iconProps} />;
      case 'history': return <Library {...iconProps} />;
      case 'english': return <Book {...iconProps} />;
      case 'psychology': return <GraduationCap {...iconProps} />;
      default: return <Book {...iconProps} />;
    }
  };

  const formatTime = (dueDate: string) => {
    try {
      const date = new Date(dueDate);
      if (isNaN(date.getTime())) return '';
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return '';
    }
  };

  const formatDuration = (minutes?: number) => {
    if (minutes === undefined || minutes === null) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours > 0 && mins > 0) return `${hours}h ${mins}m`;
    if (hours > 0) return `${hours}h`;
    return `${mins}m`;
  };

  const handleCompleteToggle = async (e: any) => {
    e.stopPropagation();
    try {
      const newStatus = task.status === 'completed' ? 'pending' : 'completed';
      await updateTask(task.id, { status: newStatus });
    } catch (error) {
      console.error('Error updating task status:', error);
    }
  };

  const handleCardPress = () => setShowDetailsModal(true);
  
  const isCompleted = task.status === 'completed';

  const styles = StyleSheet.create({
    container: {
      backgroundColor: currentTheme.colors.surface,
      borderRadius: 12,
      marginBottom: 12,
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    },
    contentContainer: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      gap: 16,
    },
    mainContent: {
      flex: 1,
      marginLeft: 8,
    },
    title: {
      fontSize: 16,
      fontWeight: '500',
      color: currentTheme.colors.textPrimary,
      marginBottom: 6,
    },
    titleCompleted: {
      textDecorationLine: 'line-through',
      color: currentTheme.colors.textSecondary,
    },
    detailsContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
    },
    timeContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
    },
    timeText: {
      fontSize: 13,
      color: currentTheme.colors.textSecondary,
      fontWeight: '500',
    },
    subjectText: {
      fontSize: 13,
      color: currentTheme.colors.textSecondary,
      fontWeight: '500',
      opacity: 0.8,
    },
    divider: {
      width: 3,
      height: 3,
      borderRadius: 1.5,
      backgroundColor: currentTheme.colors.textSecondary,
      opacity: 0.3,
    },
    checkbox: {
      width: 24,
      height: 24,
      borderRadius: 6,
      borderWidth: 2,
      borderColor: currentTheme.colors.border,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: isCompleted ? currentTheme.colors.primary : 'transparent',
    },
  });

  return (
    <>
      <TouchableOpacity 
        style={styles.container}
        onPress={handleCardPress}
        activeOpacity={0.8}
      >
        <View style={styles.contentContainer}>
          <TouchableOpacity 
            onPress={handleCompleteToggle}
            style={styles.checkbox}
          >
            {isCompleted && (
              <Check size={14} color="#fff" />
            )}
          </TouchableOpacity>
          
          <View style={styles.mainContent}>
            <Text style={[styles.title, isCompleted && styles.titleCompleted]}>
              {task.title}
            </Text>
            
            <View style={styles.detailsContainer}>
              <View style={styles.timeContainer}>
                <Clock size={13} color={currentTheme.colors.textSecondary} />
                <Text style={styles.timeText}>{formatTime(task.due_date)}</Text>
              </View>
              <View style={styles.divider} />
              <Text style={styles.subjectText}>{task.subject}</Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>

      <TaskDetailsModal
        visible={showDetailsModal}
        task={task}
        onClose={() => setShowDetailsModal(false)}
        onEdit={onEdit}
      />
    </>
  );
}