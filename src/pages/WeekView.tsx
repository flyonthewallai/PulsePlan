import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { TaskCard } from '../components/TaskCard';

export const WeekView = ({
  onTaskClick,
  darkMode
}) => {
  const [selectedDay, setSelectedDay] = useState(new Date());
  const days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - date.getDay() + i);
    return date;
  });

  const isSelected = (day) => {
    return day.toDateString() === selectedDay.toDateString();
  };

  const mockTasks = [
    {
      id: '1',
      title: 'Math Assignment',
      subject: 'Mathematics',
      priority: 'high',
      status: 'pending',
      dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000), // 2 days from now
    },
    {
      id: '2',
      title: 'Physics Lab Report',
      subject: 'Physics',
      priority: 'medium',
      status: 'in_progress',
      dueDate: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000), // 4 days from now
    },
    // ... rest of mock data ...
  ];

  return (
    <ScrollView 
      style={[
        styles.container,
        darkMode ? styles.darkContainer : styles.lightContainer
      ]}
      contentContainerStyle={styles.contentContainer}
    >
      <View style={styles.header}>
        <Text style={[styles.headerTitle, darkMode ? styles.darkText : styles.lightText]}>
          Week View
        </Text>
        <Text style={darkMode ? styles.darkSubtext : styles.lightSubtext}>
          Plan your week ahead
        </Text>
      </View>

      <View style={styles.daysContainer}>
        {days.map((day, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.dayButton,
              isSelected(day) && styles.selectedDay
            ]}
            onPress={() => setSelectedDay(day)}
          >
            <Text style={[
              styles.dayName,
              isSelected(day) ? styles.selectedDayText : (darkMode ? styles.darkText : styles.lightText)
            ]}>
              {day.toLocaleDateString('en-US', { weekday: 'short' })}
            </Text>
            <Text style={[
              styles.dayNumber,
              isSelected(day) ? styles.selectedDayText : (darkMode ? styles.darkText : styles.lightText)
            ]}>
              {day.getDate()}
            </Text>
            {isSelected(day) && (
              <View style={styles.selectedIndicator} />
            )}
          </TouchableOpacity>
        ))}
      </View>

      {days.findIndex(day => isSelected(day)) > 1 && (
        <View style={[
          styles.suggestionContainer,
          darkMode ? styles.darkSuggestionContainer : styles.lightSuggestionContainer
        ]}>
          <View style={styles.suggestionContent}>
            <View style={styles.suggestionIconContainer}>
              <Text style={styles.suggestionIcon}>💡</Text>
            </View>
            <View style={styles.suggestionTextContainer}>
              <Text style={[styles.suggestionTitle, darkMode ? styles.darkText : styles.lightText]}>
                Plan Ahead
              </Text>
              <Text style={darkMode ? styles.darkSubtext : styles.lightSubtext}>
                Consider scheduling tasks for later in the week
              </Text>
            </View>
          </View>
        </View>
      )}

      <View style={styles.tasksContainer}>
        {mockTasks.length > 0 ? (
          <View style={styles.taskList}>
            {mockTasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                onPress={() => onTaskClick(task)}
                darkMode={darkMode}
              />
            ))}
          </View>
        ) : (
          <View style={[
            styles.emptyState,
            darkMode ? styles.darkEmptyState : styles.lightEmptyState
          ]}>
            <Text style={[styles.emptyStateText, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
              No tasks scheduled for this day
            </Text>
            <Text style={[styles.emptyStateSubtext, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
              Add tasks to get started
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
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
  daysContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  dayButton: {
    alignItems: 'center',
    padding: 8,
    borderRadius: 8,
  },
  selectedDay: {
    backgroundColor: '#00AEEF',
  },
  dayName: {
    fontSize: 14,
    marginBottom: 4,
  },
  dayNumber: {
    fontSize: 16,
    fontWeight: '500',
  },
  selectedDayText: {
    color: '#FFFFFF',
  },
  selectedIndicator: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#00AEEF',
    marginTop: 4,
  },
  suggestionContainer: {
    marginBottom: 24,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  darkSuggestionContainer: {
    backgroundColor: '#1F2937',
    borderColor: '#374151',
  },
  lightSuggestionContainer: {
    backgroundColor: '#FFFFFF',
    borderColor: '#E5E7EB',
  },
  suggestionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  suggestionIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(201, 201, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  suggestionIcon: {
    fontSize: 16,
  },
  suggestionTextContainer: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  tasksContainer: {
    flex: 1,
  },
  taskList: {
    gap: 8,
  },
  emptyState: {
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  darkEmptyState: {
    backgroundColor: '#1F2937',
  },
  lightEmptyState: {
    backgroundColor: '#FFFFFF',
  },
  emptyStateText: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  emptyStateSubtext: {
    fontSize: 14,
  },
});