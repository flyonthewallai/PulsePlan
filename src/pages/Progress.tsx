import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Dimensions } from 'react-native';
import Svg, { Circle, Path, G, Rect } from 'react-native-svg';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';

export const Progress = () => {
  const { theme } = useTheme();
  // Sample data - would be replaced with real user data in production
  const weeklyData = {
    completed: 32,
    planned: 40,
    streak: 5,
    categories: {
      Classes: 12,
      Studying: 15,
      Personal: 8,
      Breaks: 5
    }
  };

  const focusData = {
    productiveHours: [
      { hour: '6am', value: 40 },
      { hour: '9am', value: 85 },
      { hour: '12pm', value: 60 },
      { hour: '3pm', value: 50 },
      { hour: '6pm', value: 75 },
      { hour: '9pm', value: 30 }
    ],
    frequentlyMoved: [
      { task: 'ECON', count: 8 },
      { task: 'GYM', count: 5 },
      { task: 'STUDY', count: 3 }
    ],
    timeBreakdown: {
      Study: 45,
      Class: 30,
      Personal: 25
    }
  };

  const renderWeeklyOverview = () => (
    <View style={[
      styles.card,
      { 
        backgroundColor: theme.colors.cardBackground,
        shadowColor: theme.colors.text,
        shadowOpacity: 0.05,
      }
    ]}>
      <View style={styles.cardHeader}>
        <View style={styles.cardTitleContainer}>
          <View style={[styles.cardIconContainer, { backgroundColor: theme.colors.primary + '10' }]}>
            <Ionicons name="stats-chart" size={20} color={theme.colors.primary} />
          </View>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
            Weekly Overview
          </Text>
        </View>
      </View>

      <View style={styles.tasksCompletionContainer}>
        <View style={styles.completionRingContainer}>
          <Svg width={100} height={100} viewBox="0 0 100 100">
            {/* Background Ring */}
            <Circle cx="50" cy="50" r="40" stroke={theme.colors.border} strokeWidth="10" fill="none" />
            
            {/* Progress Ring */}
            <Circle 
              cx="50"
              cy="50"
              r="40"
              stroke={theme.colors.primary}
              strokeWidth="10"
              fill="none"
              strokeDasharray={`${(weeklyData.completed / weeklyData.planned) * 251.2} 251.2`}
              strokeLinecap="round"
              transform="rotate(-90, 50, 50)"
            />
            
            {/* Center Text Container */}
            <Circle cx="50" cy="50" r="30" fill={theme.colors.cardBackground} />
          </Svg>
          <View style={styles.ringTextContainer}>
            <Text style={[styles.ringPercentage, { color: theme.colors.text }]}>
              {Math.round((weeklyData.completed / weeklyData.planned) * 100)}%
            </Text>
          </View>
        </View>
        
        <View style={styles.completionDetails}>
          <Text style={[styles.completionTitle, { color: theme.colors.text }]}>
            Tasks Completed
          </Text>
          <Text style={[styles.completionNumbers, { color: theme.colors.text }]}>
            {weeklyData.completed} / {weeklyData.planned}
          </Text>
          <View style={styles.streakContainer}>
            <View style={[styles.streakIconContainer, { backgroundColor: theme.colors.secondary + '10' }]}>
              <Ionicons name="flame" size={16} color={theme.colors.secondary} />
            </View>
            <Text style={[styles.streakText, { color: theme.colors.subtext }]}>
              {weeklyData.streak} day streak
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.categoriesContainer}>
        <Text style={[styles.categoryTitle, { color: theme.colors.text }]}>
          Hours per Category
        </Text>
        <View style={styles.categoryBars}>
          {Object.entries(weeklyData.categories).map(([category, hours], index) => (
            <View key={category} style={styles.categoryBar}>
              <View style={styles.categoryLabelContainer}>
                <View style={styles.categoryLabelLeft}>
                  <View style={[
                    styles.categoryIconContainer,
                    { backgroundColor: [theme.colors.primary, theme.colors.secondary, theme.colors.success, theme.colors.accent][index % 4] + '10' }
                  ]}>
                    <Ionicons 
                      name={['book', 'school', 'person', 'cafe'][index % 4]} 
                      size={14} 
                      color={[theme.colors.primary, theme.colors.secondary, theme.colors.success, theme.colors.accent][index % 4]} 
                    />
                  </View>
                  <Text style={[styles.categoryLabel, { color: theme.colors.text }]}>
                    {category}
                  </Text>
                </View>
                <Text style={[styles.categoryHours, { color: theme.colors.subtext }]}>
                  {hours}h
                </Text>
              </View>
              <View style={[
                styles.barBackground,
                { backgroundColor: theme.colors.border }
              ]}>
                <View 
                  style={[
                    styles.barFill,
                    { 
                      width: `${(hours / Object.values(weeklyData.categories).reduce((sum, current) => sum + current, 0)) * 100}%`,
                      backgroundColor: [theme.colors.primary, theme.colors.secondary, theme.colors.success, theme.colors.accent][index % 4]
                    }
                  ]} 
                />
              </View>
            </View>
          ))}
        </View>
      </View>

      {weeklyData.completed >= weeklyData.planned * 0.8 && (
        <View style={[styles.motivationalContainer, { backgroundColor: theme.colors.accent + '10' }]}>
          <View style={[styles.motivationalIconContainer, { backgroundColor: theme.colors.accent + '20' }]}>
            <Ionicons name="trophy" size={18} color={theme.colors.accent} />
          </View>
          <Text style={[styles.motivationalText, { color: theme.colors.text }]}>
            You crushed it this week! Want to plan next week now?
          </Text>
        </View>
      )}
    </View>
  );

  const renderFocusTrends = () => (
    <View style={[
      styles.card,
      { 
        backgroundColor: theme.colors.cardBackground,
        shadowColor: theme.colors.text,
        shadowOpacity: 0.05,
      }
    ]}>
      <View style={styles.cardHeader}>
        <View style={styles.cardTitleContainer}>
          <View style={[styles.cardIconContainer, { backgroundColor: theme.colors.primary + '10' }]}>
            <Ionicons name="trending-up" size={20} color={theme.colors.primary} />
          </View>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
            Focus Trends
          </Text>
        </View>
      </View>

      <View style={styles.productivityHoursContainer}>
        <Text style={[styles.focusSectionTitle, { color: theme.colors.text }]}>
          Most Productive Times
        </Text>
        <View style={styles.productivityChart}>
          {focusData.productiveHours.map((hourData, index) => (
            <View key={hourData.hour} style={styles.hourColumn}>
              <View style={[styles.hourBar, { backgroundColor: theme.colors.border }]}>
                <View 
                  style={[
                    styles.hourBarFill, 
                    { 
                      height: `${hourData.value}%`,
                      backgroundColor: hourData.value > 70 ? theme.colors.success : theme.colors.primary
                    }
                  ]} 
                />
              </View>
              <Text style={[styles.hourLabel, { color: theme.colors.subtext }]}>
                {hourData.hour}
              </Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.movedTasksContainer}>
        <Text style={[styles.focusSectionTitle, { color: theme.colors.text }]}>
          Most Frequently Moved Tasks
        </Text>
        {focusData.frequentlyMoved.map(task => (
          <View key={task.task} style={styles.movedTaskItem}>
            <View style={styles.movedTaskHeader}>
              <View style={styles.movedTaskLeft}>
                <View style={[styles.taskIconContainer, { backgroundColor: theme.colors.secondary + '10' }]}>
                  <Ionicons name="repeat" size={14} color={theme.colors.secondary} />
                </View>
                <Text style={[styles.movedTaskName, { color: theme.colors.text }]}>
                  {task.task}
                </Text>
              </View>
              <Text style={[styles.movedTaskCount, { color: theme.colors.subtext }]}>
                moved {task.count} times
              </Text>
            </View>
            <View style={[
              styles.progressBar,
              { backgroundColor: theme.colors.border }
            ]}>
              <View 
                style={[
                  styles.progressFill,
                  { 
                    width: `${(task.count / focusData.frequentlyMoved[0].count) * 100}%`, 
                    backgroundColor: theme.colors.secondary 
                  }
                ]} 
              />
            </View>
          </View>
        ))}
        <View style={styles.aiSuggestionContainer}>
          <View style={[styles.aiIconContainer, { backgroundColor: theme.colors.primary + '10' }]}>
            <Ionicons name="bulb-outline" size={16} color={theme.colors.primary} />
          </View>
          <Text style={[styles.aiSuggestion, { color: theme.colors.subtext }]}>
            You often reschedule ECON—want to set a default block?
          </Text>
        </View>
      </View>

      <View style={styles.timeBreakdownContainer}>
        <Text style={[styles.focusSectionTitle, { color: theme.colors.text }]}>
          Time Breakdown
        </Text>
        <View style={styles.timeBreakdownChart}>
          <Svg width={120} height={120} viewBox="0 0 100 100">
            <G>
              {/* Study section */}
              <Path
                d={`M 50 50 L 50 0 A 50 50 0 0 1 ${50 + 50 * Math.cos(2 * Math.PI * (focusData.timeBreakdown.Study / 100))} ${50 - 50 * Math.sin(2 * Math.PI * (focusData.timeBreakdown.Study / 100))} Z`}
                fill={theme.colors.primary}
              />
              
              {/* Class section */}
              <Path
                d={`M 50 50 L ${50 + 50 * Math.cos(2 * Math.PI * (focusData.timeBreakdown.Study / 100))} ${50 - 50 * Math.sin(2 * Math.PI * (focusData.timeBreakdown.Study / 100))} A 50 50 0 0 1 ${50 + 50 * Math.cos(2 * Math.PI * ((focusData.timeBreakdown.Study + focusData.timeBreakdown.Class) / 100))} ${50 - 50 * Math.sin(2 * Math.PI * ((focusData.timeBreakdown.Study + focusData.timeBreakdown.Class) / 100))} Z`}
                fill={theme.colors.secondary}
              />
              
              {/* Personal section */}
              <Path
                d={`M 50 50 L ${50 + 50 * Math.cos(2 * Math.PI * ((focusData.timeBreakdown.Study + focusData.timeBreakdown.Class) / 100))} ${50 - 50 * Math.sin(2 * Math.PI * ((focusData.timeBreakdown.Study + focusData.timeBreakdown.Class) / 100))} A 50 50 0 0 1 50 0 Z`}
                fill={theme.colors.success}
              />
              
              {/* Center circle */}
              <Circle cx="50" cy="50" r="25" fill={theme.colors.cardBackground} />
            </G>
          </Svg>
          
          <View style={styles.timeBreakdownLegend}>
            {Object.entries(focusData.timeBreakdown).map(([category, percentage], index) => (
              <View key={category} style={styles.legendItem}>
                <View style={styles.legendItemLeft}>
                  <View 
                    style={[
                      styles.legendDot, 
                      { backgroundColor: [theme.colors.primary, theme.colors.secondary, theme.colors.success][index % 3] }
                    ]} 
                  />
                  <Text style={[styles.legendText, { color: theme.colors.subtext }]}>
                    {category}
                  </Text>
                </View>
                <Text style={[styles.legendPercentage, { color: theme.colors.text }]}>
                  {percentage}%
                </Text>
              </View>
            ))}
          </View>
        </View>
      </View>
    </View>
  );

  const renderAIRecommendations = () => (
    <View style={[
      styles.card,
      { 
        backgroundColor: theme.colors.cardBackground,
        shadowColor: theme.colors.text,
        shadowOpacity: 0.1,
      }
    ]}>
      <View style={styles.cardHeader}>
        <View style={styles.cardTitleContainer}>
          <View style={[styles.cardIconContainer, { backgroundColor: theme.colors.primary + '15' }]}>
            <Ionicons name="sparkles" size={20} color={theme.colors.primary} />
          </View>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
            AI Recommendations
          </Text>
        </View>
      </View>

      <View style={styles.recommendationsContainer}>
        {[
          {
            icon: 'time-outline',
            text: 'You\'ve been most productive at 10am—want to shift your deep work time?',
            action: 'Adjust Schedule'
          },
          {
            icon: 'alert-circle-outline',
            text: 'You missed 3 planned study blocks for CS—schedule make-up time?',
            action: 'Schedule Now'
          },
          {
            icon: 'battery-charging-outline',
            text: 'You\'ve worked 18 hours this week. Want to schedule a rest day?',
            action: 'Add Rest Day'
          }
        ].map((recommendation, index) => (
          <View 
            key={index} 
            style={[
              styles.recommendationItem,
              index < 2 && { borderBottomColor: theme.colors.border, borderBottomWidth: 1 }
            ]}
          >
            <View style={[styles.recommendationIcon, { backgroundColor: theme.colors.primary + '15' }]}>
              <Ionicons 
                name={recommendation.icon} 
                size={24} 
                color={theme.colors.primary} 
              />
            </View>
            <View style={styles.recommendationContent}>
              <Text style={[styles.recommendationText, { color: theme.colors.text }]}>
                {recommendation.text}
              </Text>
              <TouchableOpacity 
                style={[styles.recommendationButton, { backgroundColor: theme.colors.primary + '15' }]}
              >
                <Text style={[styles.recommendationButtonText, { color: theme.colors.primary }]}>
                  {recommendation.action}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </View>
    </View>
  );

  const renderAchievements = () => (
    <View style={[
      styles.card,
      { 
        backgroundColor: theme.colors.cardBackground,
        shadowColor: theme.colors.text,
        shadowOpacity: 0.1,
      }
    ]}>
      <View style={styles.cardHeader}>
        <View style={styles.cardTitleContainer}>
          <View style={[styles.cardIconContainer, { backgroundColor: theme.colors.primary + '15' }]}>
            <Ionicons name="trophy" size={20} color={theme.colors.primary} />
          </View>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
            Achievements
          </Text>
        </View>
      </View>

      <View style={styles.badgesContainer}>
        {[
          {
            name: '3-Week Streak',
            icon: 'flame',
            color: theme.colors.accent,
            earned: true
          },
          {
            name: 'Taskmaster',
            icon: 'checkmark-circle',
            color: theme.colors.success,
            earned: true
          },
          {
            name: 'Night Owl',
            icon: 'moon',
            color: theme.colors.secondary,
            earned: false
          }
        ].map(badge => (
          <View 
            key={badge.name} 
            style={[
              styles.badgeItem,
              !badge.earned && { opacity: 0.5 }
            ]}
          >
            <View 
              style={[
                styles.badgeIconContainer,
                { backgroundColor: badge.earned ? `${badge.color}15` : theme.colors.border }
              ]}
            >
              <Ionicons 
                name={badge.icon} 
                size={24} 
                color={badge.earned ? badge.color : theme.colors.subtext} 
              />
            </View>
            <Text 
              style={[
                styles.badgeName,
                { color: badge.earned ? theme.colors.text : theme.colors.subtext }
              ]}
            >
              {badge.name}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );

  return (
    <ScrollView 
      style={[
        styles.container,
        { backgroundColor: theme.colors.background }
      ]}
      contentContainerStyle={styles.contentContainer}
    >
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
          Progress
        </Text>
        <Text style={[styles.headerSubtitle, { color: theme.colors.subtext }]}>
          Your productivity insights and achievements
        </Text>
      </View>

      {renderWeeklyOverview()}
      {renderFocusTrends()}
      {renderAIRecommendations()}
      {renderAchievements()}
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
  header: {
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
  card: {
    padding: 20,
    borderRadius: 16,
    marginBottom: 16,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 12,
    elevation: 4,
  },
  cardHeader: {
    marginBottom: 20,
  },
  cardTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  tasksCompletionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  completionRingContainer: {
    width: 100,
    height: 100,
    position: 'relative',
  },
  ringTextContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ringPercentage: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  completionDetails: {
    marginLeft: 20,
    flex: 1,
  },
  completionTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  completionNumbers: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  streakContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  streakIconContainer: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  streakText: {
    fontSize: 14,
  },
  categoriesContainer: {
    marginBottom: 16,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 16,
  },
  categoryBars: {
    gap: 16,
  },
  categoryBar: {
    gap: 8,
  },
  categoryLabelContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  categoryLabelLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryIconContainer: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  categoryLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  categoryHours: {
    fontSize: 14,
  },
  barBackground: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
  },
  motivationalContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  motivationalIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  motivationalText: {
    fontSize: 14,
    flex: 1,
  },
  productivityHoursContainer: {
    marginBottom: 24,
  },
  focusSectionTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 16,
  },
  productivityChart: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    height: 140,
    alignItems: 'flex-end',
  },
  hourColumn: {
    alignItems: 'center',
  },
  hourBar: {
    width: 24,
    height: 100,
    borderRadius: 6,
    overflow: 'hidden',
    justifyContent: 'flex-end',
  },
  hourBarFill: {
    width: '100%',
    borderRadius: 6,
  },
  hourLabel: {
    fontSize: 12,
    marginTop: 8,
  },
  movedTasksContainer: {
    marginBottom: 24,
  },
  movedTaskItem: {
    marginBottom: 16,
  },
  movedTaskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  movedTaskLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  taskIconContainer: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  movedTaskName: {
    fontSize: 14,
    fontWeight: '500',
  },
  movedTaskCount: {
    fontSize: 12,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  aiSuggestionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    padding: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(0, 174, 239, 0.05)',
  },
  aiIconContainer: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  aiSuggestion: {
    fontSize: 14,
    flex: 1,
  },
  timeBreakdownContainer: {
    marginBottom: 8,
  },
  timeBreakdownChart: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeBreakdownLegend: {
    marginLeft: 20,
    flex: 1,
  },
  legendItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  legendItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  legendText: {
    fontSize: 14,
  },
  legendPercentage: {
    fontSize: 14,
    fontWeight: '500',
  },
  recommendationsContainer: {
    gap: 4,
  },
  recommendationItem: {
    flexDirection: 'row',
    paddingVertical: 16,
  },
  recommendationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  recommendationContent: {
    flex: 1,
  },
  recommendationText: {
    fontSize: 14,
    marginBottom: 12,
    lineHeight: 20,
  },
  recommendationButton: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  recommendationButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  badgesContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  badgeItem: {
    alignItems: 'center',
    width: '30%',
  },
  badgeIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  badgeName: {
    fontSize: 13,
    textAlign: 'center',
    fontWeight: '500',
  }
}); 