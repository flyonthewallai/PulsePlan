import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Bell, Calendar, Mail, Smartphone } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';

const SettingsSection = ({ title, children }: { title: string; children: React.ReactNode }) => {
  const { currentTheme } = useTheme();
  return (
    <View style={styles.sectionContainer}>
      <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>{title.toUpperCase()}</Text>
      <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
        {children}
      </View>
    </View>
  );
};

const SettingsRow = ({
  icon,
  title,
  subtitle,
  value,
  onPress,
  showSwitch = false,
  switchValue = false,
  onSwitchChange,
  isLastItem = false,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  value?: string;
  onPress?: () => void;
  showSwitch?: boolean;
  switchValue?: boolean;
  onSwitchChange?: (value: boolean) => void;
  isLastItem?: boolean;
}) => {
  const { currentTheme } = useTheme();
  
  return (
    <View>
      <TouchableOpacity 
        style={styles.fieldContainer} 
        onPress={onPress}
        disabled={!onPress && !showSwitch}
        activeOpacity={onPress ? 0.7 : 1}
      >
        <View style={styles.fieldLeft}>
          {icon}
          <View style={styles.fieldContent}>
            <Text style={[styles.fieldTitle, { color: currentTheme.colors.textPrimary }]}>{title}</Text>
            {subtitle && (
              <Text style={[styles.fieldSubtitle, { color: currentTheme.colors.textSecondary }]}>{subtitle}</Text>
            )}
          </View>
        </View>
        <View style={styles.fieldRight}>
          {value && <Text style={[styles.fieldValue, { color: currentTheme.colors.textSecondary }]}>{value}</Text>}
          {showSwitch && (
            <Switch
              value={switchValue}
              onValueChange={onSwitchChange}
              trackColor={{ false: currentTheme.colors.border, true: currentTheme.colors.primary }}
              thumbColor={switchValue ? '#ffffff' : '#f4f3f4'}
            />
          )}
          {onPress && !showSwitch && <ChevronLeft color={currentTheme.colors.textSecondary} size={16} style={{ transform: [{ rotate: '180deg' }] }} />}
        </View>
      </TouchableOpacity>
      {!isLastItem && (
        <View style={[styles.divider, { backgroundColor: currentTheme.colors.border }]} />
      )}
    </View>
  );
};



export default function RemindersScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  
  // State for reminder settings
  const [taskReminders, setTaskReminders] = useState(true);
  const [missedTaskSummary, setMissedTaskSummary] = useState(true);
  
  // Delivery method toggles (can enable multiple)
  const [emailDelivery, setEmailDelivery] = useState(false);
  const [inAppDelivery, setInAppDelivery] = useState(true);
  const [pushDelivery, setPushDelivery] = useState(false);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Reminders</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
          Configure your notification preferences and delivery methods
        </Text>

        <SettingsSection title="Task Reminders">
          <SettingsRow
            icon={<Bell size={24} color={currentTheme.colors.textSecondary} />}
            title="Task Reminders"
            subtitle="Get notified before tasks are due"
            showSwitch
            switchValue={taskReminders}
            onSwitchChange={setTaskReminders}
          />
          <SettingsRow
            icon={<Calendar size={24} color={currentTheme.colors.textSecondary} />}
            title="Missed Task Summary"
            subtitle="Daily summary of incomplete tasks"
            showSwitch
            switchValue={missedTaskSummary}
            onSwitchChange={setMissedTaskSummary}
            isLastItem
          />
        </SettingsSection>

        <SettingsSection title="Delivery Method">
          <SettingsRow
            icon={<Mail size={24} color={currentTheme.colors.textSecondary} />}
            title="Email"
            subtitle="Receive notifications via email"
            showSwitch
            switchValue={emailDelivery}
            onSwitchChange={setEmailDelivery}
          />
          <SettingsRow
            icon={<Bell size={24} color={currentTheme.colors.textSecondary} />}
            title="In-App"
            subtitle="Show notifications within the app"
            showSwitch
            switchValue={inAppDelivery}
            onSwitchChange={setInAppDelivery}
          />
          <SettingsRow
            icon={<Smartphone size={24} color={currentTheme.colors.textSecondary} />}
            title="Push"
            subtitle="Send push notifications to your device"
            showSwitch
            switchValue={pushDelivery}
            onSwitchChange={setPushDelivery}
            isLastItem
          />
        </SettingsSection>
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
  sectionContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '400',
    marginBottom: 8,
    marginLeft: 16,
  },
  sectionBody: {
    borderRadius: 10,
    marginHorizontal: 16,
    overflow: 'hidden',
    borderWidth: 1,
  },
  fieldContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  fieldLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    flex: 1,
  },
  fieldContent: {
    flex: 1,
  },
  fieldTitle: {
    fontSize: 17,
    marginBottom: 2,
  },
  fieldSubtitle: {
    fontSize: 13,
    lineHeight: 16,
  },
  fieldRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  fieldValue: {
    fontSize: 17,
  },
  divider: {
    height: 1,
    marginLeft: 56,
    marginRight: 0, // Extend to the end of the card
    opacity: 1,
  },
}); 