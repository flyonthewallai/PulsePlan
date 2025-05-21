import React, { useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ViewStyle, TextStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { Task } from '../contexts/TaskContext';
import { useSettings } from '../contexts/SettingsContext';

interface DailyScheduleProps {
  tasks: Task[];
  onTaskPress?: (task: Task) => void;
}

interface TimeSlot {
  hour: number;
  tasks: Task[];
  isBreak?: boolean;
  isLunchBreak?: boolean;
  isStudyTime?: boolean;
}

export const DailySchedule = ({ tasks, onTaskPress }: DailyScheduleProps) => {
  const { theme } = useTheme();
  const { workingHours, studyTimes } = useSettings();

  // Generate time slots based on working hours and study times
  const timeSlots = useMemo(() => {
    const slots: TimeSlot[] = [];
    const startHour = workingHours.startHour;
    const endHour = workingHours.endHour;
    const today = new Date();
    const dayOfWeek = today.getDay();

    // Get study times for today
    const todaysStudyTimes = studyTimes.filter(block => block.days.includes(dayOfWeek));

    // Sort tasks by due date
    const sortedTasks = [...tasks].sort((a, b) => 
      new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
    );

    // Create time slots
    for (let hour = startHour; hour <= endHour; hour++) {
      // Check if this is lunch break hour
      if (hour >= workingHours.lunchBreakStart && hour < workingHours.lunchBreakEnd) {
        slots.push({ 
          hour, 
          tasks: [], 
          isBreak: true,
          isLunchBreak: true 
        });
        continue;
      }

      // Check if this hour is part of a study time block
      const isStudyTime = todaysStudyTimes.some(block => 
        hour >= block.startHour && hour < block.endHour
      );

      const hourTasks = sortedTasks.filter(task => {
        const taskDate = new Date(task.due_date);
        return taskDate.getHours() === hour;
      });

      // Add break slots if there's a gap of more than 2 hours between tasks
      if (hour > startHour && hour < endHour && !isStudyTime) {
        const prevHourTasks = sortedTasks.filter(task => {
          const taskDate = new Date(task.due_date);
          return taskDate.getHours() === hour - 1;
        });

        if (hourTasks.length === 0 && prevHourTasks.length === 0) {
          slots.push({ hour, tasks: [], isBreak: true });
          continue;
        }
      }

      slots.push({ 
        hour, 
        tasks: hourTasks,
        isStudyTime 
      });
    }

    return slots;
  }, [tasks, workingHours, studyTimes]);

  const styles = useMemo(() => StyleSheet.create({
    container: {
      marginTop: 16,
      borderRadius: 16,
      overflow: 'hidden',
    },
    timeSlot: {
      flexDirection: 'row',
      minHeight: 80,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border + '40',
    },
    timeColumn: {
      width: 60,
      paddingVertical: 12,
      paddingHorizontal: 8,
      borderRightWidth: 1,
      borderRightColor: theme.colors.border + '40',
      alignItems: 'center',
    },
    timeText: {
      fontSize: 14,
      fontWeight: '500',
      color: theme.colors.text,
    },
    contentColumn: {
      flex: 1,
      padding: 12,
    },
    breakSlot: {
      backgroundColor: theme.colors.cardBackground + '80',
    },
    lunchBreakSlot: {
      backgroundColor: theme.colors.secondary + '15',
    },
    studyTimeSlot: {
      backgroundColor: theme.colors.primary + '15',
    },
    breakText: {
      fontSize: 14,
      color: theme.colors.subtext,
      fontStyle: 'italic',
    },
    lunchBreakText: {
      fontSize: 14,
      color: theme.colors.secondary,
      fontStyle: 'italic',
    },
    studyTimeText: {
      fontSize: 14,
      color: theme.colors.primary,
      fontStyle: 'italic',
      fontWeight: '500',
      marginBottom: 8,
    },
    studyTimeContent: {
      marginTop: 4,
    },
    taskItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 8,
      borderRadius: 8,
      marginBottom: 8,
      backgroundColor: theme.colors.cardBackground,
    },
    taskIcon: {
      marginRight: 8,
    },
    taskContent: {
      flex: 1,
    },
    taskTitle: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.colors.text,
      marginBottom: 2,
    },
    taskDetails: {
      fontSize: 12,
      color: theme.colors.subtext,
    },
    emptySlot: {
      justifyContent: 'center',
      alignItems: 'center',
      padding: 12,
    },
    emptyText: {
      fontSize: 14,
      color: theme.colors.subtext,
      fontStyle: 'italic',
    },
  }), [theme]);

  const formatHour = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour} ${period}`;
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {timeSlots.map((slot, index) => (
        <View 
          key={index} 
          style={[
            styles.timeSlot,
            slot.isBreak && styles.breakSlot,
            slot.isLunchBreak && styles.lunchBreakSlot,
            slot.isStudyTime && styles.studyTimeSlot
          ]}
        >
          <View style={styles.timeColumn}>
            <Text style={styles.timeText}>{formatHour(slot.hour)}</Text>
          </View>
          <View style={styles.contentColumn}>
            {slot.isBreak ? (
              <Text style={[
                styles.breakText,
                slot.isLunchBreak && styles.lunchBreakText
              ]}>
                {slot.isLunchBreak ? 'Lunch Break' : 'Break Time'}
              </Text>
            ) : slot.isStudyTime ? (
              <View>
                <Text style={styles.studyTimeText}>Study Time</Text>
                <View style={styles.studyTimeContent}>
                  {slot.tasks.map((task, taskIndex) => (
                    <TouchableOpacity
                      key={task.id}
                      style={styles.taskItem}
                      onPress={() => onTaskPress?.(task)}
                    >
                      <Ionicons
                        name="time-outline"
                        size={16}
                        color={theme.colors.primary}
                        style={styles.taskIcon}
                      />
                      <View style={styles.taskContent}>
                        <Text style={styles.taskTitle}>{task.title}</Text>
                        <Text style={styles.taskDetails}>
                          {task.estimated_minutes} min
                        </Text>
                      </View>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            ) : slot.tasks.length > 0 ? (
              slot.tasks.map((task, taskIndex) => (
                <TouchableOpacity
                  key={task.id}
                  style={styles.taskItem}
                  onPress={() => onTaskPress?.(task)}
                >
                  <Ionicons
                    name="time-outline"
                    size={16}
                    color={theme.colors.primary}
                    style={styles.taskIcon}
                  />
                  <View style={styles.taskContent}>
                    <Text style={styles.taskTitle}>{task.title}</Text>
                    <Text style={styles.taskDetails}>
                      {task.estimated_minutes} min
                    </Text>
                  </View>
                </TouchableOpacity>
              ))
            ) : (
              <View style={styles.emptySlot}>
                <Text style={styles.emptyText}>No tasks scheduled</Text>
              </View>
            )}
          </View>
        </View>
      ))}
    </View>
  );
}; 