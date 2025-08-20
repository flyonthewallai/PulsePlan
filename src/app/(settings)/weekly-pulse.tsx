import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Mail, Calendar } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';

const OptionButton = ({ 
  title, 
  isSelected, 
  onPress 
}: { 
  title: string; 
  isSelected: boolean; 
  onPress: () => void; 
}) => {
  const { currentTheme } = useTheme();
  
  return (
    <TouchableOpacity 
      style={[
        styles.optionButton, 
        { 
          backgroundColor: isSelected ? currentTheme.colors.primary : currentTheme.colors.surface,
          borderColor: isSelected ? currentTheme.colors.primary : currentTheme.colors.border,
        }
      ]} 
      onPress={onPress}
    >
      <Text style={[
        styles.optionButtonText, 
        { color: isSelected ? '#ffffff' : currentTheme.colors.textPrimary }
      ]}>
        {title}
      </Text>
    </TouchableOpacity>
  );
};

const NewspaperSection = ({ 
  title, 
  placeholder, 
  value, 
  onChangeText, 
  defaultText 
}: { 
  title: string; 
  placeholder: string; 
  value: string; 
  onChangeText: (text: string) => void; 
  defaultText: string;
}) => {
  const { currentTheme } = useTheme();
  
  return (
    <View style={styles.newspaperSection}>
      <Text style={[styles.newspaperSectionTitle, { color: currentTheme.colors.textPrimary }]}>
        {title}
      </Text>
      <View style={[styles.textInputContainer, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
        <TextInput
          style={[styles.textInput, { color: currentTheme.colors.textPrimary }]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={currentTheme.colors.textSecondary}
          multiline
          textAlignVertical="top"
        />
      </View>
      {value === '' && (
        <Text style={[styles.suggestionText, { color: currentTheme.colors.textSecondary }]}>
          Suggestion: {defaultText}
        </Text>
      )}
    </View>
  );
};

export default function WeeklyPulseScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  
  // State for weekly pulse settings
  const [isEnabled, setIsEnabled] = useState(true);
  const [dayOfWeek, setDayOfWeek] = useState<'sunday' | 'monday' | 'friday'>('sunday');
  const [timeOfDay, setTimeOfDay] = useState('6:00 AM');
  const [showDaySelection, setShowDaySelection] = useState(false);
  
  // Content customization state
  const [upcomingTasksContent, setUpcomingTasksContent] = useState('Show me my most important deadlines and assignments for the upcoming week, prioritized by due date and impact on my academic goals.');
  const [overdueItemsContent, setOverdueItemsContent] = useState('List any overdue tasks or assignments that need immediate attention, along with suggestions for catching up.');
  const [studyHabitsContent, setStudyHabitsContent] = useState('Provide insights into my study patterns, productivity trends, and time management effectiveness from the past week.');
  const [streaksContent, setStreaksContent] = useState('Highlight my current streaks, recent achievements, and progress toward personal and academic milestones.');
  const [optionalContent, setOptionalContent] = useState('');

  const getDayDisplayValue = () => {
    switch (dayOfWeek) {
      case 'sunday': return `Sunday, ${timeOfDay}`;
      case 'monday': return `Monday, ${timeOfDay}`;
      case 'friday': return `Friday, ${timeOfDay}`;
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Weekly Pulse</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
          Customize your weekly recap email by defining what you want to receive in each section
        </Text>

        {/* General Settings */}
        <View style={[styles.settingsCard, { backgroundColor: currentTheme.colors.surface }]}>
          <View style={styles.settingRow}>
            <View style={styles.settingLeft}>
              <Mail size={20} color={currentTheme.colors.textSecondary} />
              <Text style={[styles.settingTitle, { color: currentTheme.colors.textPrimary }]}>Weekly Pulse Enabled</Text>
            </View>
            <Switch
              value={isEnabled}
              onValueChange={setIsEnabled}
              trackColor={{ false: currentTheme.colors.border, true: currentTheme.colors.primary }}
              thumbColor={isEnabled ? '#ffffff' : '#f4f3f4'}
            />
          </View>
          
          <View style={[styles.divider, { backgroundColor: currentTheme.colors.border }]} />
          
                    <TouchableOpacity 
            style={styles.settingRow}
            onPress={isEnabled ? () => setShowDaySelection(!showDaySelection) : undefined}
            disabled={!isEnabled}
          >
            <View style={styles.settingLeft}>
              <Calendar size={20} color={currentTheme.colors.textSecondary} />
              <Text style={[styles.settingTitle, { color: currentTheme.colors.textPrimary }]}>Delivery Schedule</Text>
            </View>
            <Text style={[styles.settingValue, { color: currentTheme.colors.textSecondary }]}>
              {isEnabled ? getDayDisplayValue() : 'None'}
            </Text>
          </TouchableOpacity>
        </View>

                 {/* Day Selection */}
         {(showDaySelection && isEnabled) && (
           <View style={styles.daySelectionContainer}>
             <Text style={[styles.daySelectionTitle, { color: currentTheme.colors.textSecondary }]}>DELIVERY DAY</Text>
             <View style={styles.optionsContainer}>
               <OptionButton 
                 title="Sunday" 
                 isSelected={dayOfWeek === 'sunday'} 
                 onPress={() => setDayOfWeek('sunday')} 
               />
               <OptionButton 
                 title="Monday" 
                 isSelected={dayOfWeek === 'monday'} 
                 onPress={() => setDayOfWeek('monday')} 
               />
               <OptionButton 
                 title="Friday" 
                 isSelected={dayOfWeek === 'friday'} 
                 onPress={() => setDayOfWeek('friday')} 
               />
             </View>
           </View>
         )}

         {isEnabled && (
           <>

             {/* Newspaper Structure */}
             <View style={[styles.newspaperContainer, { backgroundColor: currentTheme.colors.surface }]}>
               <View style={styles.newspaperHeader}>
                 <Text style={[styles.newspaperTitle, { color: currentTheme.colors.textPrimary }]}>The Weekly Pulse</Text>
                 <Text style={[styles.newspaperSubtitle, { color: currentTheme.colors.textSecondary }]}>Your Personalized Academic Digest</Text>
               </View>

               <NewspaperSection
                 title="Upcoming Tasks"
                 placeholder="Describe what you want to see for upcoming tasks..."
                 value={upcomingTasksContent}
                 onChangeText={setUpcomingTasksContent}
                 defaultText="Show me my most important deadlines and assignments for the upcoming week, prioritized by due date and impact on my academic goals."
               />

               <NewspaperSection
                 title="Overdue Items"
                 placeholder="Describe what you want to see for overdue items..."
                 value={overdueItemsContent}
                 onChangeText={setOverdueItemsContent}
                 defaultText="List any overdue tasks or assignments that need immediate attention, along with suggestions for catching up."
               />

               <NewspaperSection
                 title="Study Habits Summary"
                 placeholder="Describe what insights you want about your study habits..."
                 value={studyHabitsContent}
                 onChangeText={setStudyHabitsContent}
                 defaultText="Provide insights into my study patterns, productivity trends, and time management effectiveness from the past week."
               />

               <NewspaperSection
                 title="Personal Streaks & Milestones"
                 placeholder="Describe what achievements and progress you want to see..."
                 value={streaksContent}
                 onChangeText={setStreaksContent}
                 defaultText="Highlight my current streaks, recent achievements, and progress toward personal and academic milestones."
               />

               <NewspaperSection
                 title="Optional Content"
                 placeholder="Add any additional content you'd like to receive (leave blank if not needed)..."
                 value={optionalContent}
                 onChangeText={setOptionalContent}
                 defaultText="Include academic tips, motivational quotes, or study strategies tailored to my current goals and challenges."
               />
             </View>
           </>
         )}

                <View style={styles.footerNote}>
          <Text style={[styles.footerText, { color: currentTheme.colors.textSecondary }]}>
            {isEnabled 
              ? `Your Weekly Pulse will be delivered every ${dayOfWeek.charAt(0).toUpperCase() + dayOfWeek.slice(1)} at ${timeOfDay}. Customize each section above to receive exactly the insights you need.`
              : 'Enable Weekly Pulse to receive personalized weekly insights, productivity analytics, upcoming task summaries, and progress tracking delivered directly to your email.'
            }
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingVertical: 20,
  },
  description: {
    fontSize: 15,
    lineHeight: 20,
    marginHorizontal: 16,
    marginBottom: 24,
    textAlign: 'center',
  },
  settingsCard: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingValue: {
    fontSize: 15,
  },
  divider: {
    height: 1,
    marginLeft: 48,
    marginRight: 0, // Extend to the end of the card
  },
  daySelectionContainer: {
    marginHorizontal: 16,
    marginBottom: 24,
  },
  daySelectionTitle: {
    fontSize: 13,
    fontWeight: '400',
    marginBottom: 12,
  },
  optionsContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  optionButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  optionButtonText: {
    fontSize: 15,
    fontWeight: '500',
  },
  newspaperContainer: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
  },
  newspaperHeader: {
    paddingVertical: 24,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: '#000000',
  },
  newspaperTitle: {
    fontSize: 28,
    fontWeight: '800',
    textAlign: 'center',
    fontFamily: 'serif',
    marginBottom: 4,
  },
  newspaperSubtitle: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  newspaperSection: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  newspaperSectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
    fontFamily: 'serif',
  },
  textInputContainer: {
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
  },
  textInput: {
    fontSize: 15,
    lineHeight: 20,
    textAlignVertical: 'top',
  },
  suggestionText: {
    fontSize: 13,
    lineHeight: 18,
    marginTop: 8,
    fontStyle: 'italic',
  },
  footerNote: {
    marginHorizontal: 16,
    marginTop: 16,
    padding: 16,
    borderRadius: 10,
  },
  footerText: {
    fontSize: 13,
    lineHeight: 18,
    textAlign: 'center',
  },
}); 