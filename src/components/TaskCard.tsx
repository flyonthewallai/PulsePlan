import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Animated } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Ionicons } from '@expo/vector-icons';

const getSubjectColor = (subject) => {
  const colors = {
    'Mathematics': '#3B82F6',
    'Physics': '#8B5CF6',
    'Biology': '#10B981',
    'English': '#F59E0B',
    'History': '#EF4444',
    'Computer Science': '#EC4899',
    'Chemistry': '#6366F1',
    'default': '#6B7280'
  };
  return colors[subject] || colors.default;
};

const getPriorityColor = (priority) => {
  const colors = {
    'high': '#EF4444',
    'medium': '#F59E0B',
    'low': '#10B981',
    'default': '#6B7280'
  };
  return colors[priority] || colors.default;
};

const getStatusIcon = (status) => {
  const icons = {
    'pending': 'time-outline',
    'in_progress': 'sync-outline',
    'completed': 'checkmark-circle-outline',
    'default': 'document-text-outline'
  };
  return icons[status] || icons.default;
};

export const TaskCard = ({ task, onPress }) => {
  const { theme } = useTheme();
  const scaleAnim = React.useRef(new Animated.Value(1)).current;
  
  // Safely parse due_date
  let timeString = '-';
  if (task.due_date) {
    try {
      const dateObj = typeof task.due_date === 'string' ? new Date(task.due_date) : task.due_date;
      if (!isNaN(dateObj.getTime())) {
        timeString = dateObj.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
      }
    } catch (e) {
      // leave timeString as '-'
    }
  }

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.98,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4
    }).start();
  };

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <TouchableOpacity 
        style={[
          styles.container,
          { 
            backgroundColor: theme.colors.cardBackground,
            borderLeftColor: getSubjectColor(task.subject),
            borderLeftWidth: 4,
            shadowColor: theme.colors.text,
            shadowOpacity: 0.1,
          }
        ]}
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={0.9}
      >
        <View style={styles.content}>
          <View style={styles.header}>
            <View style={styles.titleContainer}>
              <Text style={[styles.title, { color: theme.colors.text }]} numberOfLines={1}>
                {task.title}
              </Text>
              <View style={[
                styles.priorityBadge,
                { backgroundColor: getPriorityColor(task.priority) + '15' }
              ]}>
                <Text style={[
                  styles.priorityText,
                  { color: getPriorityColor(task.priority) }
                ]}>
                  {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                </Text>
              </View>
            </View>
            <View style={[
              styles.statusContainer,
              { backgroundColor: theme.colors.background + '80' }
            ]}>
              <Ionicons 
                name={getStatusIcon(task.status)} 
                size={20} 
                color={theme.colors.text} 
              />
            </View>
          </View>
          
          <View style={styles.footer}>
            <View style={styles.subjectContainer}>
              <Ionicons 
                name="book-outline" 
                size={14} 
                color={theme.colors.subtext} 
                style={styles.subjectIcon}
              />
              <Text style={[styles.subject, { color: theme.colors.subtext }]} numberOfLines={1}>
                {task.subject}
              </Text>
            </View>
            <View style={styles.timeContainer}>
              <Ionicons 
                name="time-outline" 
                size={14} 
                color={theme.colors.subtext} 
                style={styles.timeIcon}
              />
              <Text style={[styles.time, { color: theme.colors.subtext }]}>
                {timeString}
              </Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 16,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 3,
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  titleContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
    gap: 8,
  },
  title: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  statusContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  subjectContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 12,
  },
  subjectIcon: {
    marginRight: 4,
  },
  subject: {
    fontSize: 13,
    fontWeight: '500',
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeIcon: {
    marginRight: 4,
  },
  time: {
    fontSize: 13,
    fontWeight: '500',
  }
});