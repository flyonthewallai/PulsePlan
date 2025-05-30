import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { 
  Calculator, 
  FlaskConical, 
  Library, 
  Book, 
  GraduationCap, 
  Clock, 
  MoreHorizontal, 
  Check 
} from 'lucide-react-native';
import { colors } from '../constants/theme';
import { Task } from '../contexts/TaskContext';

interface TaskCardProps {
  task: Task;
  isFirst?: boolean;
  isLast?: boolean;
}

export default function TaskCard({ task, isFirst, isLast }: TaskCardProps) {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#FF5757';
      case 'medium': return '#FFD60A'; 
      case 'low': return '#30D158';
      default: return colors.textSecondary;
    }
  };

  const getSubjectIcon = (subject: string) => {
    const iconProps = { size: 12, color: colors.textSecondary };
    
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
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return ''; // fallback if parsing fails
    }
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours > 0 && mins > 0) {
      return `${hours}h ${mins}m`;
    } else if (hours > 0) {
      return `${hours}h`;
    } else {
      return `${mins} min`;
    }
  };

  const isCompleted = task.status === 'completed';

  return (
    <View style={[
      styles.container,
      isFirst && styles.firstCard,
      isLast && styles.lastCard
    ]}>
      <View style={[styles.leftBorder, { backgroundColor: getPriorityColor(task.priority) }]} />
      
      {/* Menu button - on left */}
      <TouchableOpacity style={styles.menuButton}>
        <MoreHorizontal size={16} color={colors.textSecondary} />
      </TouchableOpacity>
      
      <View style={styles.content}>
        <Text style={[
          styles.title,
          isCompleted && styles.titleCompleted
        ]}>
          {task.title}
        </Text>
        
        <View style={styles.details}>
          <View style={styles.subjectContainer}>
            {getSubjectIcon(task.subject)}
            <Text style={styles.subject}>{task.subject}</Text>
          </View>
          
          <View style={styles.timeContainer}>
            <Clock size={12} color={colors.textSecondary} />
            <Text style={styles.time}>{formatTime(task.due_date)}</Text>
          </View>
          
          <Text style={styles.duration}>{formatDuration(task.estimated_minutes)}</Text>
        </View>
      </View>
      
      {/* Completion checkbox - on right */}
      <TouchableOpacity style={[
        styles.checkbox,
        isCompleted && styles.checkboxCompleted
      ]}>
        {isCompleted && (
          <Check size={14} color="#fff" />
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    marginBottom: 8,
    paddingVertical: 14,
    paddingHorizontal: 16,
    position: 'relative',
    shadowColor: 'rgba(0, 0, 0, 0.3)',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  firstCard: {
    marginTop: 4,
  },
  lastCard: {
    marginBottom: 16,
  },
  leftBorder: {
    position: 'absolute',
    left: 0,
    top: '25%',
    bottom: '25%',
    width: 4,
    borderRadius: 2,
  },
  menuButton: {
    padding: 6,
    marginRight: 10,
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 6,
    letterSpacing: 0.2,
  },
  titleCompleted: {
    textDecorationLine: 'line-through',
    color: colors.textSecondary,
    opacity: 0.7,
  },
  details: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  subjectContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  subject: {
    fontSize: 13,
    color: colors.textSecondary,
    marginLeft: 4,
    fontWeight: '500',
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  time: {
    fontSize: 13,
    color: colors.textSecondary,
    marginLeft: 4,
    fontWeight: '500',
  },
  duration: {
    fontSize: 12,
    color: colors.textSecondary,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    fontWeight: '500',
    minWidth: 40,
    textAlign: 'center',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#4A4A4A',
    marginLeft: 10,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
  },
  checkboxCompleted: {
    backgroundColor: colors.primaryBlue,
    borderColor: colors.primaryBlue,
  },
});