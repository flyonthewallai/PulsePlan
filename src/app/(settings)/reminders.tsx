import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowLeft, ChevronRight, Bell, Mail, Clock, Calendar } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const REMINDERS_SETTINGS_KEY = '@pulse_reminders_settings';

interface ReminderSettings {
  weeklyPulse: boolean;
  morningBriefing: boolean;
  taskReminders: boolean;
  missedTaskSummary: boolean;
}

interface SettingRowProps {
  title: string;
  description?: string;
  icon: React.ReactNode;
  value: boolean;
  onValueChange: (value: boolean) => void;
  showChevron?: boolean;
  onPress?: () => void;
}

const SettingRow: React.FC<SettingRowProps> = ({
  title,
  description,
  icon,
  value,
  onValueChange,
  showChevron = false,
  onPress,
}) => {
  const { currentTheme } = useTheme();

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else {
      onValueChange(!value);
    }
  };

  return (
    <TouchableOpacity 
      style={[styles.settingRow, { backgroundColor: currentTheme.colors.surface }]} 
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <View style={styles.settingLeft}>
        {icon}
        <View style={styles.settingInfo}>
          <Text style={[styles.settingTitle, { color: currentTheme.colors.textPrimary }]}>
            {title}
          </Text>
          {description && (
            <Text style={[styles.settingDescription, { color: currentTheme.colors.textSecondary }]}>
              {description}
            </Text>
          )}
        </View>
      </View>
      <View style={styles.settingRight}>
        {showChevron ? (
          <ChevronRight size={20} color={currentTheme.colors.textSecondary} />
        ) : (
          <Switch
            value={value}
            onValueChange={onValueChange}
            trackColor={{ false: currentTheme.colors.border, true: currentTheme.colors.primary + '40' }}
            thumbColor={value ? currentTheme.colors.primary : currentTheme.colors.textSecondary}
            ios_backgroundColor={currentTheme.colors.border}
          />
        )}
      </View>
    </TouchableOpacity>
  );
};

export default function RemindersScreen() {
  const { currentTheme } = useTheme();
  const router = useRouter();
  const [settings, setSettings] = useState<ReminderSettings>({
    weeklyPulse: false,
    morningBriefing: false,
    taskReminders: true,
    missedTaskSummary: true,
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const savedSettings = await AsyncStorage.getItem(REMINDERS_SETTINGS_KEY);
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings));
      }
    } catch (error) {
      console.error('Error loading reminder settings:', error);
    }
  };

  const saveSettings = async (newSettings: ReminderSettings) => {
    try {
      await AsyncStorage.setItem(REMINDERS_SETTINGS_KEY, JSON.stringify(newSettings));
      setSettings(newSettings);
    } catch (error) {
      console.error('Error saving reminder settings:', error);
    }
  };

  const updateSetting = (key: keyof ReminderSettings, value: boolean) => {
    const newSettings = { ...settings, [key]: value };
    saveSettings(newSettings);
  };

  const handleDeliveryPreferences = () => {
    router.push('/(settings)/delivery-preferences');
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={currentTheme.colors.background} />
      
      {/* Header */}
      <View style={[styles.header, { backgroundColor: currentTheme.colors.background }]}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => router.back()}
        >
          <ArrowLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
          Reminders
        </Text>
        
        <View style={styles.headerRight} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Weekly Pulse Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
            WEEKLY PULSE
          </Text>
          
          <View style={[styles.sectionContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <SettingRow
              title="Weekly Pulse"
              description="Get an email every Monday with your personalized weekly plan and insights"
              icon={<Mail size={24} color={currentTheme.colors.textSecondary} />}
              value={settings.weeklyPulse}
              onValueChange={(value) => updateSetting('weeklyPulse', value)}
            />
          </View>
        </View>

        {/* Agent Notifications Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
            AGENT NOTIFICATIONS
          </Text>
          
          <View style={[styles.sectionContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <SettingRow
              title="Morning Briefing"
              description="Daily push notification and email with your schedule and priorities"
              icon={<Clock size={24} color={currentTheme.colors.textSecondary} />}
              value={settings.morningBriefing}
              onValueChange={(value) => updateSetting('morningBriefing', value)}
            />
          </View>
        </View>

        {/* Task Reminders Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
            TASK REMINDERS
          </Text>
          
          <View style={[styles.sectionContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <SettingRow
              title="Task Reminders"
              description="Get notified before tasks are due"
              icon={<Bell size={24} color={currentTheme.colors.textSecondary} />}
              value={settings.taskReminders}
              onValueChange={(value) => updateSetting('taskReminders', value)}
            />
            
            <View style={[styles.separator, { backgroundColor: currentTheme.colors.border }]} />
            
            <SettingRow
              title="Missed Task Summary"
              description="Daily summary of incomplete tasks at the end of each day"
              icon={<Calendar size={24} color={currentTheme.colors.textSecondary} />}
              value={settings.missedTaskSummary}
              onValueChange={(value) => updateSetting('missedTaskSummary', value)}
            />
          </View>
        </View>

        {/* Delivery Preferences Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
            DELIVERY PREFERENCES
          </Text>
          
          <View style={[styles.sectionContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <TouchableOpacity
              style={styles.deliveryRow}
              onPress={handleDeliveryPreferences}
              activeOpacity={0.7}
            >
              <View style={styles.deliveryLeft}>
                <Mail size={24} color={currentTheme.colors.textSecondary} />
                <View style={styles.settingInfo}>
                  <Text style={[styles.settingTitle, { color: currentTheme.colors.textPrimary }]}>
                    Delivery Preferences
                  </Text>
                  <Text style={[styles.settingDescription, { color: currentTheme.colors.textSecondary }]}>
                    Configure when and how you receive notifications
                  </Text>
                </View>
              </View>
              <ChevronRight size={20} color={currentTheme.colors.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Bottom spacing */}
        <View style={styles.bottomSpacing} />
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
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 8,
    marginLeft: -8,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  headerRight: {
    width: 32,
  },
  content: {
    flex: 1,
  },
  section: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  sectionContainer: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 16,
  },
  settingInfo: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  settingDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  settingRight: {
    marginLeft: 12,
  },
  separator: {
    height: 0.5,
    marginLeft: 40,
  },
  deliveryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  deliveryLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 16,
  },
  bottomSpacing: {
    height: 40,
  },
}); 