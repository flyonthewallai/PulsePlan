import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

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
    'pending': '⏳',
    'in_progress': '🔄',
    'completed': '✅',
    'default': '📝'
  };
  return icons[status] || icons.default;
};

export const TaskCard = ({ task, onPress, darkMode }) => {
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
  return (
    <TouchableOpacity 
      style={[
        styles.container,
        darkMode ? styles.darkContainer : styles.lightContainer
      ]}
      onPress={onPress}
    >
      <View style={[styles.subjectIndicator, { backgroundColor: getSubjectColor(task.subject) }]} />
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={[styles.title, darkMode ? styles.darkText : styles.lightText]}>
            {task.title}
          </Text>
          <Text style={[styles.status, { color: getPriorityColor(task.priority) }]}>
            {getStatusIcon(task.status)}
          </Text>
        </View>
        <View style={styles.footer}>
          <Text style={[styles.subject, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
            {task.subject}
          </Text>
          <Text style={[styles.time, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
            {timeString}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    marginBottom: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  darkContainer: {
    backgroundColor: '#1F2937',
  },
  lightContainer: {
    backgroundColor: '#FFFFFF',
  },
  subjectIndicator: {
    width: 4,
    height: 48,
    borderRadius: 2,
    marginRight: 12,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  title: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    marginRight: 8,
  },
  status: {
    fontSize: 16,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  subject: {
    fontSize: 14,
  },
  time: {
    fontSize: 14,
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
});