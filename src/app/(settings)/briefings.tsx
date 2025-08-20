import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch, TextInput, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Clock, Bell } from 'lucide-react-native';
import DateTimePicker from '@react-native-community/datetimepicker';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';




const BriefingSection = ({ 
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
    <View style={styles.briefingSection}>
      <Text style={[styles.briefingSectionTitle, { color: currentTheme.colors.textPrimary }]}>
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

export default function BriefingsScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const { user } = useAuth();
  
  // State for briefing settings
  const [isEnabled, setIsEnabled] = useState(true);
  const [deliveryTime, setDeliveryTime] = useState('7:00 AM');
  const [showTimePicker, setShowTimePicker] = useState(false);
  
  // Content customization state
  const [scheduleContent, setScheduleContent] = useState('Show me today\'s schedule with time blocks, priorities, and any potential conflicts or gaps.');
  const [suggestionsContent, setSuggestionsContent] = useState('Provide AI-powered recommendations for optimizing my day, including schedule adjustments and productivity tips.');
  const [motivationContent, setMotivationContent] = useState('Include a brief motivational message or academic tip to start my day with focus and energy.');
  const [remindersContent, setRemindersContent] = useState('Highlight important deadlines, upcoming assignments, and tasks that need my attention today.');

  const getUserName = () => {
    const fullName = user?.user_metadata?.full_name;
    if (fullName) {
      return fullName.split(' ')[0]; // Get first name
    }
    return 'there'; // Fallback greeting
  };

  const getPickerDate = () => {
    const [time, period] = deliveryTime.split(' ');
    const [hour, minute] = time.split(':');
    let hour24 = parseInt(hour);
    
    if (period === 'PM' && hour24 !== 12) {
      hour24 += 12;
    } else if (period === 'AM' && hour24 === 12) {
      hour24 = 0;
    }
    
    const date = new Date();
    date.setHours(hour24, parseInt(minute), 0, 0);
    return date;
  };

  const onTimeChange = (event: any, selectedDate?: Date) => {
    const currentDate = selectedDate || new Date();
    
    // Hide picker on Android after selection, keep visible on iOS until manually closed
    if (Platform.OS === 'android') {
      setShowTimePicker(false);
    }
    
    if (currentDate) {
      const timeString = currentDate.toLocaleTimeString([], { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
      setDeliveryTime(timeString);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Briefings</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
          Customize your daily morning briefing to start each day informed and focused
        </Text>

        {/* General Settings */}
        <View style={[styles.settingsCard, { backgroundColor: currentTheme.colors.surface }]}>
          <View style={styles.settingRow}>
            <View style={styles.settingLeft}>
              <Bell size={20} color={currentTheme.colors.textSecondary} />
              <Text style={[styles.settingTitle, { color: currentTheme.colors.textPrimary }]}>Daily Briefings Enabled</Text>
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
            onPress={isEnabled ? () => setShowTimePicker(!showTimePicker) : undefined}
            disabled={!isEnabled}
          >
            <View style={styles.settingLeft}>
              <Clock size={20} color={currentTheme.colors.textSecondary} />
              <Text style={[styles.settingTitle, { color: currentTheme.colors.textPrimary }]}>Delivery Time</Text>
            </View>
            <Text style={[styles.settingValue, { color: currentTheme.colors.textSecondary }]}>
              {isEnabled ? deliveryTime : 'None'}
            </Text>
          </TouchableOpacity>
        </View>



        {/* Time Picker */}
        {(Platform.OS === 'ios' && showTimePicker && isEnabled) && (
          <View>
            <Text style={[styles.pickerTitle, { color: currentTheme.colors.textSecondary }]}>DELIVERY TIME</Text>
            <View style={[styles.pickerContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <DateTimePicker
                value={getPickerDate()}
                mode="time"
                display="spinner"
                onChange={onTimeChange}
                textColor={currentTheme.colors.textPrimary}
              />
            </View>
          </View>
        )}

        {Platform.OS === 'android' && showTimePicker && isEnabled && (
          <DateTimePicker
            value={getPickerDate()}
            mode="time"
            is24Hour={false}
            display="default"
            onChange={onTimeChange}
          />
        )}

        {isEnabled && (
          <>
            {/* Morning Briefing Structure */}
            <View style={[styles.briefingContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.briefingHeader}>
                <Text style={[styles.briefingTitle, { color: currentTheme.colors.textPrimary }]}>
                  Good Morning {getUserName()}
                </Text>
                <Text style={[styles.briefingSubtitle, { color: currentTheme.colors.textSecondary }]}>
                  Here's your morning briefing
                </Text>
              </View>

              <BriefingSection
                title="Schedule Overview"
                placeholder="Describe what you want to see in your schedule overview..."
                value={scheduleContent}
                onChangeText={setScheduleContent}
                defaultText="Show me today's schedule with time blocks, priorities, and any potential conflicts or gaps."
              />

              <BriefingSection
                title="Suggested Adjustments"
                placeholder="Describe what AI suggestions you want to receive..."
                value={suggestionsContent}
                onChangeText={setSuggestionsContent}
                defaultText="Provide AI-powered recommendations for optimizing my day, including schedule adjustments and productivity tips."
              />

              <BriefingSection
                title="Motivational Blurb"
                placeholder="Describe what kind of motivation you want to receive..."
                value={motivationContent}
                onChangeText={setMotivationContent}
                defaultText="Include a brief motivational message or academic tip to start my day with focus and energy."
              />

              <BriefingSection
                title="Important Reminders"
                placeholder="Describe what reminders you want to see..."
                value={remindersContent}
                onChangeText={setRemindersContent}
                defaultText="Highlight important deadlines, upcoming assignments, and tasks that need my attention today."
              />
            </View>
          </>
        )}

        <View style={styles.footerNote}>
          <Text style={[styles.footerText, { color: currentTheme.colors.textSecondary }]}>
            {isEnabled 
              ? `Your daily briefing will be delivered every morning at ${deliveryTime}. Customize each section above to receive exactly the insights you need to start your day.`
              : 'Enable Daily Briefings to receive personalized morning insights, schedule overviews, AI recommendations, and important reminders delivered to start your day informed and focused.'
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
  pickerTitle: {
    fontSize: 13,
    fontWeight: '400',
    marginBottom: 8,
    marginLeft: 16,
  },
  pickerContainer: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 12,
    overflow: 'hidden',
  },
  briefingContainer: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
  },
  briefingHeader: {
    paddingVertical: 20,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: '#000000',
  },
  briefingTitle: {
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 4,
  },
  briefingSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  briefingSection: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  briefingSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  textInputContainer: {
    borderRadius: 8,
    padding: 12,
    minHeight: 60,
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