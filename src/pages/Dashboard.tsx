import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { TaskCard } from '../components/TaskCard';

export const Dashboard = ({ darkMode, onTaskClick }) => {
  const upcomingTasks = [
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
    }
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
          Welcome back!
        </Text>
        <Text style={darkMode ? styles.darkSubtext : styles.lightSubtext}>
          Let's make today productive
        </Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={[
          styles.statsCard,
          darkMode ? styles.darkStatsCard : styles.lightStatsCard
        ]}>
          <View style={styles.statsContent}>
            <View>
              <Text style={[styles.statsValue, darkMode ? styles.darkText : styles.lightText]}>
                85%
              </Text>
              <Text style={[styles.statsLabel, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                Weekly Progress
              </Text>
            </View>
            <View style={styles.statsIconContainer}>
              <View style={styles.statsIconBackground}>
                <View style={[
                  styles.statsIconInner,
                  darkMode ? styles.darkStatsIconInner : styles.lightStatsIconInner
                ]}>
                  <Text style={styles.statsIconText}>📚</Text>
                </View>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.tasksList}>
          {upcomingTasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onPress={() => onTaskClick(task)}
              darkMode={darkMode}
            />
          ))}
        </View>

        <View style={[
          styles.quickStatsCard,
          darkMode ? styles.darkQuickStatsCard : styles.lightQuickStatsCard
        ]}>
          <View style={styles.quickStatsHeader}>
            <View>
              <Text style={[styles.quickStatsTitle, darkMode ? styles.darkText : styles.lightText]}>
                Quick Stats
              </Text>
              <Text style={[styles.quickStatsSubtitle, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                Your study overview
              </Text>
            </View>
            <TouchableOpacity 
              style={styles.quickStatsButton}
              onPress={() => {/* Handle view all */}}
            >
              <Text style={styles.quickStatsButtonText}>View All</Text>
            </TouchableOpacity>
          </View>
        </View>
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
  statsContainer: {
    gap: 16,
  },
  statsCard: {
    height: 96,
    borderRadius: 12,
    padding: 16,
  },
  darkStatsCard: {
    backgroundColor: 'rgba(0, 174, 239, 0.2)',
  },
  lightStatsCard: {
    backgroundColor: 'rgba(0, 174, 239, 0.1)',
  },
  statsContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  statsValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statsLabel: {
    fontSize: 14,
  },
  statsIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(0, 174, 239, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statsIconBackground: {
    width: 48,
    height: 48,
    borderRadius: 24,
  },
  statsIconInner: {
    width: 32,
    height: 32,
    borderRadius: 16,
    margin: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  darkStatsIconInner: {
    backgroundColor: '#0D1B2A',
  },
  lightStatsIconInner: {
    backgroundColor: '#FFFFFF',
  },
  statsIconText: {
    fontSize: 16,
  },
  tasksList: {
    gap: 8,
  },
  quickStatsCard: {
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  darkQuickStatsCard: {
    backgroundColor: '#1F2937',
  },
  lightQuickStatsCard: {
    backgroundColor: '#FFFFFF',
  },
  quickStatsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  quickStatsTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  quickStatsSubtitle: {
    fontSize: 12,
  },
  quickStatsButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: '#00AEEF',
  },
  quickStatsButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '500',
  },
});