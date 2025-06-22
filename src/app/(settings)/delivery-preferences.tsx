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
import { ArrowLeft, Mail, Smartphone, Clock, Volume2 } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const DELIVERY_PREFERENCES_KEY = '@pulse_delivery_preferences';

interface DeliveryPreferences {
  emailNotifications: boolean;
  pushNotifications: boolean;
  quietHoursEnabled: boolean;
  soundEnabled: boolean;
}

interface SettingRowProps {
  title: string;
  description?: string;
  icon: React.ReactNode;
  value: boolean;
  onValueChange: (value: boolean) => void;
}

const SettingRow: React.FC<SettingRowProps> = ({
  title,
  description,
  icon,
  value,
  onValueChange,
}) => {
  const { currentTheme } = useTheme();

  return (
    <TouchableOpacity 
      style={[styles.settingRow, { backgroundColor: currentTheme.colors.surface }]} 
      onPress={() => onValueChange(!value)}
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
        <Switch
          value={value}
          onValueChange={onValueChange}
          trackColor={{ false: currentTheme.colors.border, true: currentTheme.colors.primary + '40' }}
          thumbColor={value ? currentTheme.colors.primary : currentTheme.colors.textSecondary}
          ios_backgroundColor={currentTheme.colors.border}
        />
      </View>
    </TouchableOpacity>
  );
};

export default function DeliveryPreferencesScreen() {
  const { currentTheme } = useTheme();
  const router = useRouter();
  const [preferences, setPreferences] = useState<DeliveryPreferences>({
    emailNotifications: true,
    pushNotifications: true,
    quietHoursEnabled: false,
    soundEnabled: true,
  });

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const savedPreferences = await AsyncStorage.getItem(DELIVERY_PREFERENCES_KEY);
      if (savedPreferences) {
        setPreferences(JSON.parse(savedPreferences));
      }
    } catch (error) {
      console.error('Error loading delivery preferences:', error);
    }
  };

  const savePreferences = async (newPreferences: DeliveryPreferences) => {
    try {
      await AsyncStorage.setItem(DELIVERY_PREFERENCES_KEY, JSON.stringify(newPreferences));
      setPreferences(newPreferences);
    } catch (error) {
      console.error('Error saving delivery preferences:', error);
    }
  };

  const updatePreference = (key: keyof DeliveryPreferences, value: boolean) => {
    const newPreferences = { ...preferences, [key]: value };
    savePreferences(newPreferences);
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
          Delivery Preferences
        </Text>
        
        <View style={styles.headerRight} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Notification Methods Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
            NOTIFICATION METHODS
          </Text>
          
          <View style={[styles.sectionContainer, { backgroundColor: currentTheme.colors.surface }]}>
                         <SettingRow
               title="Email Notifications"
               description="Receive notifications via email"
               icon={<Mail size={24} color={currentTheme.colors.textSecondary} />}
               value={preferences.emailNotifications}
               onValueChange={(value) => updatePreference('emailNotifications', value)}
             />
            
            <View style={[styles.separator, { backgroundColor: currentTheme.colors.border }]} />
            
            <SettingRow
              title="Push Notifications"
              description="Receive notifications on your device"
              icon={<Smartphone size={24} color={currentTheme.colors.textSecondary} />}
              value={preferences.pushNotifications}
              onValueChange={(value) => updatePreference('pushNotifications', value)}
            />
          </View>
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
  infoContainer: {
    borderRadius: 12,
    padding: 16,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
  },
  bottomSpacing: {
    height: 40,
  },
}); 