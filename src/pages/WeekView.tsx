import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Animated } from 'react-native';
import { TaskCard } from '../components/TaskCard';
import { useTheme } from '../contexts/ThemeContext';
import { Ionicons } from '@expo/vector-icons';

export const WeekView = ({
  onTaskClick
}) => {
  const { theme } = useTheme();
  const [selectedDay, setSelectedDay] = useState(new Date());
  const scaleAnim = React.useRef(new Animated.Value(1)).current;
  const days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - date.getDay() + i);
    return date;
  });

  const isSelected = (day) => {
    return day.toDateString() === selectedDay.toDateString();
  };

  const handleDayPress = (day) => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 0.95,
        useNativeDriver: true,
        speed: 50,
        bounciness: 4
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        speed: 50,
        bounciness: 4
      })
    ]).start();
    setSelectedDay(day);
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
        { backgroundColor: theme.colors.background }
      ]}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <View>
          <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
            Week View
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.colors.subtext }]}>
            Plan your week ahead
          </Text>
        </View>
        <TouchableOpacity
          style={[
            styles.calendarButton,
            { backgroundColor: theme.colors.cardBackground }
          ]}
          onPress={() => {/* Handle calendar */}}
        >
          <Ionicons name="calendar-outline" size={24} color={theme.colors.text} />
        </TouchableOpacity>
      </View>

      <Animated.View 
        style={[
          styles.daysContainer,
          { transform: [{ scale: scaleAnim }] }
        ]}
      >
        {days.map((day, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.dayButton,
              isSelected(day) && { 
                backgroundColor: theme.colors.primary,
                shadowColor: theme.colors.primary,
                shadowOpacity: 0.3,
              }
            ]}
            onPress={() => handleDayPress(day)}
            activeOpacity={0.9}
          >
            <Text style={[
              styles.dayName,
              { 
                color: isSelected(day) ? '#FFFFFF' : theme.colors.text,
                opacity: isSelected(day) ? 1 : 0.7
              }
            ]}>
              {day.toLocaleDateString('en-US', { weekday: 'short' })}
            </Text>
            <Text style={[
              styles.dayNumber,
              { 
                color: isSelected(day) ? '#FFFFFF' : theme.colors.text,
                opacity: isSelected(day) ? 1 : 0.9
              }
            ]}>
              {day.getDate()}
            </Text>
            {isSelected(day) && (
              <View style={[
                styles.selectedIndicator,
                { backgroundColor: '#FFFFFF' }
              ]} />
            )}
          </TouchableOpacity>
        ))}
      </Animated.View>

      {days.findIndex(day => isSelected(day)) > 1 && (
        <View style={[
          styles.suggestionContainer,
          { 
            backgroundColor: theme.colors.cardBackground,
            borderColor: theme.colors.primary + '30',
            shadowColor: theme.colors.text,
            shadowOpacity: 0.1,
          }
        ]}>
          <View style={styles.suggestionContent}>
            <View style={[
              styles.suggestionIconContainer,
              { backgroundColor: theme.colors.primary + '15' }
            ]}>
              <Ionicons 
                name="bulb-outline" 
                size={20} 
                color={theme.colors.primary} 
              />
            </View>
            <View style={styles.suggestionTextContainer}>
              <Text style={[styles.suggestionTitle, { color: theme.colors.text }]}>
                Plan Ahead
              </Text>
              <Text style={[styles.suggestionText, { color: theme.colors.subtext }]}>
                Consider scheduling tasks for later in the week
              </Text>
            </View>
          </View>
        </View>
      )}

      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          {selectedDay.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
        </Text>
        <TouchableOpacity
          style={[
            styles.addTaskButton,
            { backgroundColor: theme.colors.primary + '15' }
          ]}
          onPress={() => {/* Handle add task */}}
        >
          <Ionicons 
            name="add" 
            size={20} 
            color={theme.colors.primary} 
          />
          <Text style={[styles.addTaskText, { color: theme.colors.primary }]}>
            Add Task
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.tasksContainer}>
        {mockTasks.length > 0 ? (
          <View style={styles.taskList}>
            {mockTasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                onPress={() => onTaskClick(task)}
              />
            ))}
          </View>
        ) : (
          <View style={[
            styles.emptyState,
            { 
              backgroundColor: theme.colors.cardBackground,
              shadowColor: theme.colors.text,
              shadowOpacity: 0.1,
            }
          ]}>
            <Ionicons 
              name="calendar-outline" 
              size={32} 
              color={theme.colors.subtext} 
            />
            <Text style={[styles.emptyStateText, { color: theme.colors.text }]}>
              No tasks scheduled
            </Text>
            <Text style={[styles.emptyStateSubtext, { color: theme.colors.subtext }]}>
              Add tasks to plan your day
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
    paddingBottom: 100,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
    letterSpacing: 0.3,
  },
  headerSubtitle: {
    fontSize: 16,
    letterSpacing: 0.2,
  },
  calendarButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 3,
  },
  daysContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    paddingHorizontal: 4,
  },
  dayButton: {
    alignItems: 'center',
    padding: 12,
    borderRadius: 16,
    minWidth: 48,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 3,
  },
  dayName: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
    letterSpacing: 0.2,
  },
  dayNumber: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  selectedIndicator: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginTop: 6,
  },
  suggestionContainer: {
    marginBottom: 24,
    padding: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderStyle: 'dashed',
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 12,
    elevation: 4,
  },
  suggestionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  suggestionIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  suggestionTextContainer: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
    letterSpacing: 0.2,
  },
  suggestionText: {
    fontSize: 14,
    letterSpacing: 0.2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  addTaskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    gap: 4,
  },
  addTaskText: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  tasksContainer: {
    flex: 1,
  },
  taskList: {
    gap: 12,
  },
  emptyState: {
    padding: 32,
    borderRadius: 20,
    alignItems: 'center',
    gap: 12,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 12,
    elevation: 4,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  emptyStateSubtext: {
    fontSize: 14,
    letterSpacing: 0.2,
  },
});