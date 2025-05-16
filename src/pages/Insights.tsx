import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Dimensions } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

export const Insights = ({ darkMode }) => {
  const [activeTab, setActiveTab] = useState('productivity');
  const tabs = [
    { id: 'productivity', name: 'Productivity' },
    { id: 'subjects', name: 'Subjects' },
    { id: 'habits', name: 'Habits' }
  ];

  const renderProductivityTab = () => (
    <View style={styles.tabContent}>
      <View style={[
        styles.card,
        darkMode ? styles.darkCard : styles.lightCard
      ]}>
        <Text style={[styles.cardTitle, darkMode ? styles.darkText : styles.lightText]}>
          Weekly Productivity
        </Text>
        <View style={styles.barChart}>
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => (
            <View key={day} style={styles.barContainer}>
              <View 
                style={[
                  styles.bar,
                  { height: `${[70, 85, 65, 90, 75, 40, 30][i]}%` },
                  i < 5 ? styles.activeBar : styles.inactiveBar
                ]} 
              />
              <Text style={[styles.barLabel, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                {day}
              </Text>
            </View>
          ))}
        </View>
      </View>

      <View style={[
        styles.card,
        darkMode ? styles.darkCard : styles.lightCard
      ]}>
        <Text style={[styles.cardTitle, darkMode ? styles.darkText : styles.lightText]}>
          Focus Time
        </Text>
        <View style={styles.focusTimeContainer}>
          <View style={styles.pieChart}>
            <Svg width={64} height={64} viewBox="0 0 64 64">
              <Circle cx="32" cy="32" r="32" fill="#1F2937" />
              <Path
                d="M32 0 A32 32 0 0 1 32 64"
                fill="#00AEEF"
                transform="rotate(234, 32, 32)"
              />
              <Path
                d="M32 0 A32 32 0 0 1 32 64"
                fill="#FF6B6B"
                transform="rotate(306, 32, 32)"
              />
              <Path
                d="M32 0 A32 32 0 0 1 32 64"
                fill="#C9C9FF"
                transform="rotate(342, 32, 32)"
              />
              <Circle cx="32" cy="32" r="20" fill={darkMode ? '#1F2937' : '#FFFFFF'} />
            </Svg>
            <Text style={[styles.pieChartLabel, darkMode ? styles.darkText : styles.lightText]}>
              24h
            </Text>
          </View>
          <View style={styles.legend}>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#00AEEF' }]} />
              <Text style={[styles.legendText, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                Focused Work (65%)
              </Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#FF6B6B' }]} />
              <Text style={[styles.legendText, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                Distractions (20%)
              </Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#C9C9FF' }]} />
              <Text style={[styles.legendText, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                Breaks (15%)
              </Text>
            </View>
          </View>
        </View>
      </View>

      <View style={[
        styles.card,
        styles.proCard,
        darkMode ? styles.darkCard : styles.lightCard
      ]}>
        <View style={styles.proContent}>
          <View style={styles.proIconContainer}>
            <Text style={styles.proIcon}>🔒</Text>
          </View>
          <View style={styles.proTextContainer}>
            <Text style={[styles.proTitle, darkMode ? styles.darkText : styles.lightText]}>
              Advanced Insights
            </Text>
            <Text style={[styles.proDescription, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
              Upgrade to Pro to unlock detailed productivity analytics and AI recommendations
            </Text>
          </View>
        </View>
        <TouchableOpacity 
          style={styles.proButton}
          onPress={() => {/* Handle upgrade */}}
        >
          <Text style={styles.proButtonText}>Upgrade to Pro</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderSubjectsTab = () => (
    <View style={[
      styles.card,
      darkMode ? styles.darkCard : styles.lightCard
    ]}>
      <Text style={[styles.cardTitle, darkMode ? styles.darkText : styles.lightText]}>
        Subject Distribution
      </Text>
      <View style={styles.subjectsList}>
        {[
          { name: 'Math', percentage: 30, color: '#3B82F6' },
          { name: 'Computer Science', percentage: 25, color: '#8B5CF6' },
          { name: 'Biology', percentage: 20, color: '#10B981' },
          { name: 'English', percentage: 15, color: '#F59E0B' },
          { name: 'History', percentage: 10, color: '#EF4444' }
        ].map(subject => (
          <View key={subject.name} style={styles.subjectItem}>
            <View style={styles.subjectHeader}>
              <Text style={[styles.subjectName, darkMode ? styles.darkText : styles.lightText]}>
                {subject.name}
              </Text>
              <Text style={[styles.subjectPercentage, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                {subject.percentage}%
              </Text>
            </View>
            <View style={[
              styles.progressBar,
              darkMode ? styles.darkProgressBar : styles.lightProgressBar
            ]}>
              <View 
                style={[
                  styles.progressFill,
                  { width: `${subject.percentage}%`, backgroundColor: subject.color }
                ]} 
              />
            </View>
          </View>
        ))}
      </View>
    </View>
  );

  const renderHabitsTab = () => (
    <View style={[
      styles.card,
      darkMode ? styles.darkCard : styles.lightCard
    ]}>
      <Text style={[styles.cardTitle, darkMode ? styles.darkText : styles.lightText]}>
        Study Habits
      </Text>
      <View style={styles.habitsContent}>
        <View>
          <Text style={[styles.habitTitle, darkMode ? styles.darkText : styles.lightText]}>
            Peak Productivity Hours
          </Text>
          <View style={styles.timeChart}>
            {['6am', '9am', '12pm', '3pm', '6pm', '9pm'].map((time, i) => (
              <View key={time} style={styles.timeColumn}>
                <View style={[
                  styles.timeBars,
                  { opacity: i === 1 || i === 4 ? 1 : 0.5 }
                ]}>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <View 
                      key={j} 
                      style={[
                        styles.timeBar,
                        j < [2, 4, 3, 2, 4, 1][i] ? styles.activeTimeBar : styles.inactiveTimeBar
                      ]} 
                    />
                  ))}
                </View>
                <Text style={[styles.timeLabel, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                  {time}
                </Text>
              </View>
            ))}
          </View>
          <Text style={[styles.timeInsight, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
            You're most productive around 9am and 6pm
          </Text>
        </View>

        <View style={styles.consistencyContainer}>
          <Text style={[styles.habitTitle, darkMode ? styles.darkText : styles.lightText]}>
            Consistency Score
          </Text>
          <View style={styles.consistencyContent}>
            <View style={styles.consistencyChart}>
              <Svg width={64} height={64} viewBox="0 0 64 64">
                <Circle cx="32" cy="32" r="32" fill={darkMode ? '#1F2937' : '#E5E7EB'} />
                <Path
                  d="M32 0 A32 32 0 0 1 32 64"
                  fill="#00AEEF"
                  transform="rotate(306, 32, 32)"
                />
                <Circle cx="32" cy="32" r="20" fill={darkMode ? '#1F2937' : '#FFFFFF'} />
              </Svg>
              <Text style={[styles.consistencyScore, darkMode ? styles.darkText : styles.lightText]}>
                85
              </Text>
            </View>
            <Text style={[styles.consistencyText, darkMode ? styles.darkText : styles.lightText]}>
              Great job! Your consistency score is higher than 80% of users.
            </Text>
          </View>
        </View>
      </View>
    </View>
  );

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
          Insights
        </Text>
        <Text style={darkMode ? styles.darkSubtext : styles.lightSubtext}>
          Your academic patterns and progress
        </Text>
      </View>

      <View style={[
        styles.tabsContainer,
        darkMode ? styles.darkTabsContainer : styles.lightTabsContainer
      ]}>
        {tabs.map(tab => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tab,
              activeTab === tab.id && styles.activeTab
            ]}
            onPress={() => setActiveTab(tab.id)}
          >
            <Text style={[
              styles.tabText,
              activeTab === tab.id ? styles.activeTabText : (darkMode ? styles.darkText : styles.lightText)
            ]}>
            {tab.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {activeTab === 'productivity' && renderProductivityTab()}
      {activeTab === 'subjects' && renderSubjectsTab()}
      {activeTab === 'habits' && renderHabitsTab()}
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
  tabsContainer: {
    flexDirection: 'row',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 24,
  },
  darkTabsContainer: {
    backgroundColor: '#1F2937',
  },
  lightTabsContainer: {
    backgroundColor: '#FFFFFF',
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: '#00AEEF',
  },
  tabText: {
    fontSize: 14,
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  tabContent: {
    gap: 16,
  },
  card: {
    padding: 16,
    borderRadius: 12,
  },
  darkCard: {
    backgroundColor: '#1F2937',
  },
  lightCard: {
    backgroundColor: '#FFFFFF',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 12,
  },
  barChart: {
    height: 160,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  barContainer: {
    alignItems: 'center',
  },
  bar: {
    width: 32,
    borderRadius: 4,
  },
  activeBar: {
    backgroundColor: '#00AEEF',
  },
  inactiveBar: {
    backgroundColor: '#00AEEF',
    opacity: 0.5,
  },
  barLabel: {
    fontSize: 12,
    marginTop: 8,
  },
  focusTimeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  pieChart: {
    width: 64,
    height: 64,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pieChartLabel: {
    position: 'absolute',
    fontSize: 12,
  },
  legend: {
    flex: 1,
    marginLeft: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  legendText: {
    fontSize: 12,
  },
  proCard: {
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  proContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  proIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(201, 201, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  proIcon: {
    fontSize: 20,
  },
  proTextContainer: {
    flex: 1,
  },
  proTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  proDescription: {
    fontSize: 12,
  },
  proButton: {
    backgroundColor: '#FF6B6B',
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  proButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  subjectsList: {
    gap: 12,
  },
  subjectItem: {
    gap: 4,
  },
  subjectHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  subjectName: {
    fontSize: 14,
  },
  subjectPercentage: {
    fontSize: 12,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  darkProgressBar: {
    backgroundColor: '#374151',
  },
  lightProgressBar: {
    backgroundColor: '#E5E7EB',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  habitsContent: {
    gap: 24,
  },
  habitTitle: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  timeChart: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timeColumn: {
    alignItems: 'center',
  },
  timeBars: {
    width: 32,
    height: 80,
    flexDirection: 'column-reverse',
  },
  timeBar: {
    height: 16,
    borderTopWidth: 1,
  },
  activeTimeBar: {
    backgroundColor: '#00AEEF',
  },
  inactiveTimeBar: {
    backgroundColor: 'transparent',
  },
  timeLabel: {
    fontSize: 12,
    marginTop: 8,
  },
  timeInsight: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 12,
  },
  consistencyContainer: {
    marginTop: 24,
  },
  consistencyContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  consistencyChart: {
    width: 64,
    height: 64,
    alignItems: 'center',
    justifyContent: 'center',
  },
  consistencyScore: {
    position: 'absolute',
    fontSize: 18,
    fontWeight: 'bold',
  },
  consistencyText: {
    flex: 1,
    marginLeft: 16,
    fontSize: 14,
  },
});