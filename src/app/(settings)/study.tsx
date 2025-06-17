import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Clock, Sun, Moon } from 'lucide-react-native';
import DateTimePicker from '@react-native-community/datetimepicker';

import { useTheme } from '@/contexts/ThemeContext';
import { useSettings } from '@/contexts/SettingsContext';

const TimeBlock = ({ 
  label, 
  time, 
  icon, 
  onPress 
}: { 
  label: string; 
  time: string; 
  icon: React.ReactNode;
  onPress: () => void;
}) => {
  const { currentTheme } = useTheme();
  return (
    <TouchableOpacity 
      style={[styles.timeBlock, { backgroundColor: currentTheme.colors.surface }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.timeBlockContent}>
        {icon}
        <View style={styles.timeBlockText}>
          <Text style={[styles.timeBlockLabel, { color: currentTheme.colors.textSecondary }]}>{label}</Text>
          <Text style={[styles.timeBlockValue, { color: currentTheme.colors.textPrimary }]}>{time}</Text>
        </View>
      </View>
      <Clock size={20} color={currentTheme.colors.textSecondary} />
    </TouchableOpacity>
  );
};

const TimeRange = ({ startHour, endHour }: { startHour: number; endHour: number }) => {
  const { currentTheme } = useTheme();
  const hours = Array.from({ length: 24 }, (_, i) => i);
  
  return (
    <View style={styles.timeRangeContainer}>
      <View style={styles.timeRangeLabels}>
        <Text style={[styles.timeRangeLabel, { color: currentTheme.colors.textSecondary }]}>12 AM</Text>
        <Text style={[styles.timeRangeLabel, { color: currentTheme.colors.textSecondary }]}>12 PM</Text>
        <Text style={[styles.timeRangeLabel, { color: currentTheme.colors.textSecondary }]}>11 PM</Text>
      </View>
      <View style={[styles.timeRange, { backgroundColor: currentTheme.colors.surface }]}>
        {hours.map((hour) => {
          const isInRange = (startHour <= endHour)
            ? (hour >= startHour && hour <= endHour)
            : (hour >= startHour || hour <= endHour);
          return (
            <View
              key={hour}
              style={[
                styles.timeRangeHour,
                { backgroundColor: isInRange ? currentTheme.colors.primary : 'transparent' }
              ]}
            />
          );
        })}
      </View>
    </View>
  );
};

export default function StudyScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const { workingHours, updateWorkingHours } = useSettings();
  const [showStartTimePicker, setShowStartTimePicker] = useState(Platform.OS === 'ios');
  const [showEndTimePicker, setShowEndTimePicker] = useState(Platform.OS === 'ios');

  const formatTime = (hour: number) => {
    const date = new Date();
    date.setHours(hour, 0);
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  };

  const onStartTimeChange = async (event: any, selectedDate?: Date) => {
    const currentDate = selectedDate || new Date();
    setShowStartTimePicker(Platform.OS === 'ios');
    if (currentDate) {
      try {
        await updateWorkingHours({ ...workingHours, startHour: currentDate.getHours() });
      } catch (error) {
        Alert.alert("Error", "Failed to update start time.");
      }
    }
  };

  const onEndTimeChange = async (event: any, selectedDate?: Date) => {
    const currentDate = selectedDate || new Date();
    setShowEndTimePicker(Platform.OS === 'ios');
    if (currentDate) {
      try {
        await updateWorkingHours({ ...workingHours, endHour: currentDate.getHours() });
      } catch (error) {
        Alert.alert("Error", "Failed to update end time.");
      }
    }
  };

  const getPickerDate = (hour: number) => {
    const date = new Date();
    date.setHours(hour, 0, 0, 0);
    return date;
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Study Times</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
          Set your preferred study hours. PulsePlan will schedule tasks and send reminders during these times.
        </Text>

        <View style={styles.timeBlocksContainer}>
          <TimeBlock
            label="Start Time"
            time={formatTime(workingHours.startHour)}
            icon={<Sun size={24} color={currentTheme.colors.primary} />}
            onPress={() => setShowStartTimePicker(true)}
          />
          <TimeBlock
            label="End Time"
            time={formatTime(workingHours.endHour)}
            icon={<Moon size={24} color={currentTheme.colors.primary} />}
            onPress={() => setShowEndTimePicker(true)}
          />
        </View>

        <View style={styles.timeRangeSection}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>DAILY SCHEDULE</Text>
          <TimeRange startHour={workingHours.startHour} endHour={workingHours.endHour} />
        </View>

        {(Platform.OS === 'ios' && showStartTimePicker) && (
          <View>
            <Text style={[styles.pickerTitle, { color: currentTheme.colors.textSecondary }]}>START TIME</Text>
            <View style={[styles.pickerContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <DateTimePicker
                value={getPickerDate(workingHours.startHour)}
                mode="time"
                display="spinner"
                onChange={onStartTimeChange}
                textColor={currentTheme.colors.textPrimary}
              />
            </View>
          </View>
        )}

        {(Platform.OS === 'ios' && showEndTimePicker) && (
          <View>
            <Text style={[styles.pickerTitle, { color: currentTheme.colors.textSecondary }]}>END TIME</Text>
            <View style={[styles.pickerContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <DateTimePicker
                value={getPickerDate(workingHours.endHour)}
                mode="time"
                display="spinner"
                onChange={onEndTimeChange}
                textColor={currentTheme.colors.textPrimary}
              />
            </View>
          </View>
        )}

        {Platform.OS === 'android' && (showStartTimePicker || showEndTimePicker) && (
          <DateTimePicker
            value={getPickerDate(showStartTimePicker ? workingHours.startHour : workingHours.endHour)}
            mode="time"
            is24Hour={false}
            display="default"
            onChange={showStartTimePicker ? onStartTimeChange : onEndTimeChange}
          />
        )}
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
    borderBottomWidth: 1,
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
    padding: 16,
  },
  description: {
    fontSize: 15,
    lineHeight: 20,
    marginBottom: 24,
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  timeBlocksContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  timeBlock: {
    flex: 1,
    borderRadius: 12,
    padding: 16,
  },
  timeBlockContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  timeBlockText: {
    flex: 1,
  },
  timeBlockLabel: {
    fontSize: 13,
    marginBottom: 4,
  },
  timeBlockValue: {
    fontSize: 17,
    fontWeight: '600',
  },
  timeRangeSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 12,
    marginLeft: 4,
  },
  timeRangeContainer: {
    marginHorizontal: 4,
  },
  timeRangeLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  timeRangeLabel: {
    fontSize: 13,
  },
  timeRange: {
    flexDirection: 'row',
    height: 24,
    borderRadius: 12,
    overflow: 'hidden',
  },
  timeRangeHour: {
    flex: 1,
    borderRightWidth: 1,
    borderRightColor: 'rgba(0, 0, 0, 0.1)',
  },
  pickerTitle: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 8,
    marginLeft: 4,
    letterSpacing: 0.5,
  },
  pickerContainer: {
    borderRadius: 12,
    marginBottom: 16,
    overflow: 'hidden',
  },
}); 
 
 
 