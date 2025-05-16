import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch } from 'react-native';
import { ChevronRight } from 'lucide-react-native';
import { Ionicons } from '@expo/vector-icons';

export const Settings = ({
  darkMode,
  onToggleDarkMode
}) => {
  const settingsGroups = [{
    title: 'Account',
    settings: [{
      name: 'Profile',
      icon: '👤'
    }, {
      name: 'Notifications',
      icon: '🔔'
    }, {
      name: 'Privacy',
      icon: '🔒'
    }]
  }, {
    title: 'Connections',
    settings: [{
      name: 'Canvas',
      icon: '🎨',
      connected: true
    }, {
      name: 'Google Calendar',
      icon: '📅',
      connected: true
    }, {
      name: 'Outlook',
      icon: '📧',
      connected: false
    }]
  }, {
    title: 'Preferences',
    settings: [{
      name: 'Dark Mode',
      icon: darkMode ? '🌙' : '☀️',
      customRight: (
        <Switch
          value={darkMode}
          onValueChange={onToggleDarkMode}
          trackColor={{ false: '#E5E7EB', true: '#00AEEF' }}
          thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
        />
      )
    }, {
      name: 'Study Times',
      icon: '⏰'
    }, {
      name: 'Focus Mode',
      icon: '🧠'
    }, {
      name: 'AI Assistant',
      icon: '🤖'
    }]
  }, {
    title: 'Subscription',
    settings: [{
      name: 'Rhythm Pro',
      icon: '⭐',
      highlight: true
    }, {
      name: 'Restore Purchase',
      icon: '💳'
    }]
  }];

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
          Settings
        </Text>
        <Text style={darkMode ? styles.darkSubtext : styles.lightSubtext}>
          Customize your Rhythm experience
        </Text>
      </View>

      <View style={styles.groupsContainer}>
        {settingsGroups.map((group, index) => (
          <View key={index} style={styles.group}>
            <Text style={styles.groupTitle}>{group.title}</Text>
            <View style={[
              styles.settingsContainer,
              darkMode ? styles.darkSettingsContainer : styles.lightSettingsContainer
            ]}>
              {group.settings.map((setting, settingIndex) => (
                <TouchableOpacity
                  key={settingIndex}
                  style={[
                    styles.settingItem,
                    settingIndex !== group.settings.length - 1 && styles.settingItemBorder,
                    darkMode ? styles.darkSettingItemBorder : styles.lightSettingItemBorder,
                    setting.highlight && styles.highlightedSetting
                  ]}
                  onPress={setting.customRight ? undefined : () => {}}
                >
                  <View style={styles.settingLeft}>
                    <Text style={styles.settingIcon}>{setting.icon}</Text>
                    <Text style={[styles.settingName, darkMode ? styles.darkText : styles.lightText]}>
                      {setting.name}
                    </Text>
                  </View>
                  <View style={styles.settingRight}>
                    {setting.connected !== undefined && (
                      <Text style={[
                        styles.connectionStatus,
                        setting.connected ? styles.connected : styles.notConnected
                      ]}>
                        {setting.connected ? 'Connected' : 'Not Connected'}
                      </Text>
                    )}
                    {setting.customRight ? (
                      setting.customRight
                    ) : setting.highlight ? (
                      <View style={styles.proBadge}>
                        <Text style={styles.proBadgeText}>PRO</Text>
                      </View>
                    ) : (
                      <ChevronRight size={20} color={darkMode ? '#9CA3AF' : '#6B7280'} />
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Rhythm v1.0.0</Text>
        <Text style={styles.footerText}>© {new Date().getFullYear()} Rhythm App</Text>
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
  groupsContainer: {
    gap: 24,
  },
  group: {
    gap: 8,
  },
  groupTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#00AEEF',
    marginBottom: 4,
  },
  settingsContainer: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  darkSettingsContainer: {
    backgroundColor: '#1F2937',
  },
  lightSettingsContainer: {
    backgroundColor: '#FFFFFF',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
  },
  settingItemBorder: {
    borderBottomWidth: 1,
  },
  darkSettingItemBorder: {
    borderBottomColor: '#374151',
  },
  lightSettingItemBorder: {
    borderBottomColor: '#F3F4F6',
  },
  highlightedSetting: {
    backgroundColor: 'rgba(201, 201, 255, 0.1)',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  settingName: {
    fontSize: 16,
  },
  settingRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectionStatus: {
    fontSize: 12,
    marginRight: 8,
  },
  connected: {
    color: '#10B981',
  },
  notConnected: {
    color: '#9CA3AF',
  },
  proBadge: {
    backgroundColor: '#FF6B6B',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  proBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '500',
  },
  footer: {
    marginTop: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
});