import React, { useState, useEffect, useRef, useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, Modal, TextInput, FlatList, KeyboardAvoidingView, Platform, Dimensions, PanResponder, Animated, ViewStyle, TextStyle, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme, themes } from '../contexts/ThemeContext';
import { usePremium } from '../contexts/PremiumContext';
import { useProfile } from '../contexts/ProfileContext';

// Add type definitions for modal types
type ModalType = 'profile' | 'notifications' | 'privacy' | 'canvas' | 'googleCalendar' | 'outlook' | 'studyTimes' | 'focusMode' | 'aiAssistant' | 'subscription' | 'restorePurchase' | 'themes' | null;

// Add type definition for theme group
interface ThemeGroup {
  name: string;
  themes: Array<{
    id: string;
    name: string;
    colors: any;
    premium: boolean;
  }>;
  premium: boolean;
}

// Add type definition for styles
interface SettingsStyles {
  container: ViewStyle;
  contentContainer: ViewStyle;
  header: ViewStyle;
  headerTitle: TextStyle;
  headerSubtitle: TextStyle;
  groupsContainer: ViewStyle;
  group: ViewStyle;
  groupTitle: TextStyle;
  settingsContainer: ViewStyle;
  settingItem: ViewStyle;
  settingItemBorder: ViewStyle;
  highlightedSetting: ViewStyle;
  settingLeft: ViewStyle;
  iconContainer: ViewStyle;
  settingName: TextStyle;
  settingRight: ViewStyle;
  connectionStatus: TextStyle;
  proBadge: ViewStyle;
  proBadgeText: TextStyle;
  footer: ViewStyle;
  footerText: TextStyle;
  modalOverlay: ViewStyle;
  modalContainer: ViewStyle;
  dragIndicator: ViewStyle;
  modalHeader: ViewStyle;
  modalTitle: TextStyle;
  modalBody: ViewStyle;
  input: TextStyle;
  label: TextStyle;
  saveButton: ViewStyle;
  saveButtonText: TextStyle;
  profileImageContainer: ViewStyle;
  profileImage: ViewStyle;
  profileInitials: TextStyle;
  changePhotoButton: ViewStyle;
  changePhotoText: TextStyle;
  themeFamily: ViewStyle;
  themeFamilyHeader: ViewStyle;
  themeFamilyName: TextStyle;
  themeVariants: ViewStyle;
  themeOption: ViewStyle;
  themeOptionSelected: ViewStyle;
  themePreview: ViewStyle;
  themeName: TextStyle;
  featureItem: ViewStyle;
  featureText: TextStyle;
  upgradeButton: ViewStyle;
  upgradeButtonText: TextStyle;
  switchSetting: ViewStyle;
  switchTitle: TextStyle;
  switchDescription: TextStyle;
  formGroup: ViewStyle;
  proFeatureText: TextStyle;
  deleteButton: ViewStyle;
  deleteButtonText: TextStyle;
}

// Add type definition for setting item
type IconName = 
  | 'person-circle-outline'
  | 'notifications-outline'
  | 'shield-checkmark-outline'
  | 'school-outline'
  | 'calendar-outline'
  | 'mail-outline'
  | 'moon-outline'
  | 'sunny-outline'
  | 'time-outline'
  | 'fitness-outline'
  | 'sparkles-outline'
  | 'star-outline'
  | 'refresh-circle-outline'
  | 'color-palette-outline';

interface SettingItem {
  name: string;
  icon: IconName;
  connected?: boolean;
  onPress?: () => void;
  customRight?: React.ReactNode;
  highlight?: boolean;
  proFeature?: boolean;
}

// Add type definition for settings group
interface SettingsGroup {
  title: string;
  settings: SettingItem[];
}

// Add privacy settings state type
interface PrivacySettings {
  shareAnalytics: boolean;
  shareUsageData: boolean;
  allowPersonalization: boolean;
  showTaskDetails: boolean;
  syncAcrossDevices: boolean;
}

export const Settings = ({
  onToggleDarkMode
}: {
  onToggleDarkMode: () => void;
}) => {
  const { theme, darkMode, setTheme, availableThemes } = useTheme();
  const { isPremium, togglePremium } = usePremium();
  const { profileData, updateProfile } = useProfile();
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [notificationSettings, setNotificationSettings] = useState({
    taskReminders: true,
    deadlineAlerts: true,
    studyReminders: false,
    weeklyReports: true
  });
  const [focusSettings, setFocusSettings] = useState({
    allowNotifications: false,
    autoEnable: true,
    duration: 25
  });
  const [privacySettings, setPrivacySettings] = useState<PrivacySettings>({
    shareAnalytics: true,
    shareUsageData: true,
    allowPersonalization: true,
    showTaskDetails: true,
    syncAcrossDevices: true
  });
  const pan = useRef(new Animated.ValueXY()).current;
  const modalHeight = useRef(Dimensions.get('window').height * 0.8).current;

  const panResponder = useMemo(() => PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: (_, gestureState) => {
      return gestureState.dy > 0; // Only respond to downward gestures
    },
    onPanResponderMove: (_, gestureState) => {
      if (gestureState.dy > 0) { // Only allow downward movement
        pan.y.setValue(gestureState.dy);
      }
    },
    onPanResponderRelease: (_, gestureState) => {
      if (gestureState.dy > modalHeight * 0.3) { // If dragged down more than 30% of modal height
        Animated.timing(pan, {
          toValue: { x: 0, y: modalHeight },
          duration: 200,
          useNativeDriver: true,
        }).start(() => {
          hideModal();
          pan.setValue({ x: 0, y: 0 });
        });
      } else {
        Animated.spring(pan, {
          toValue: { x: 0, y: 0 },
          useNativeDriver: true,
        }).start();
      }
    },
  }), [modalHeight]);

  // Create styles after theme is available
  const styles = useMemo(() => {
    if (!theme) return {} as SettingsStyles;
    
    return StyleSheet.create<SettingsStyles>({
      container: {
        flex: 1,
        backgroundColor: theme.colors.background,
      },
      contentContainer: {
        padding: 16,
        paddingBottom: 80,
      },
      header: {
        marginBottom: 32,
      },
      headerTitle: {
        fontSize: 28,
        fontWeight: '700',
        marginBottom: 8,
        letterSpacing: -0.5,
      },
      headerSubtitle: {
        fontSize: 16,
        opacity: 0.8,
        letterSpacing: 0.2,
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
        marginBottom: 4,
      },
      settingsContainer: {
        borderRadius: 12,
        overflow: 'hidden',
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
      highlightedSetting: {
        backgroundColor: 'rgba(201, 201, 255, 0.1)',
      },
      settingLeft: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
      },
      iconContainer: {
        width: 36,
        height: 36,
        borderRadius: 18,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
        backgroundColor: 'transparent',
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
      proBadge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12,
      },
      proBadgeText: {
        color: '#FFFFFF',
        fontSize: 10,
        fontWeight: 'bold',
      },
      footer: {
        marginTop: 40,
        alignItems: 'center',
      },
      footerText: {
        fontSize: 12,
        marginBottom: 4,
      },
      modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.35)',
        justifyContent: 'center',
        alignItems: 'center',
      },
      modalContainer: {
        width: '100%',
        maxHeight: modalHeight,
        backgroundColor: theme.colors.background + 'F0', // 94% opacity for frosted effect
        borderRadius: 28,
        shadowColor: theme.colors.primary,
        shadowOffset: {
          width: 0,
          height: 8,
        },
        shadowOpacity: 0.15,
        shadowRadius: 24,
        elevation: 12,
        borderWidth: 1,
        borderColor: theme.colors.border + '20',
      },
      dragIndicator: {
        width: 40,
        height: 4,
        backgroundColor: theme.colors.border + '60',
        borderRadius: 2,
        alignSelf: 'center',
        marginTop: 12,
        marginBottom: 16,
      },
      modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.border + '40',
      },
      modalTitle: {
        fontSize: 20,
        fontWeight: '600',
        color: theme.colors.text,
      },
      modalBody: {
        padding: 20,
      },
      input: {
        height: 50,
        borderWidth: 1,
        borderRadius: 12,
        paddingHorizontal: 16,
        fontSize: 16,
        marginBottom: 16,
        color: theme.colors.text,
        backgroundColor: theme.colors.cardBackground,
        borderColor: theme.colors.border,
      },
      label: {
        fontSize: 14,
        marginBottom: 8,
        color: theme.colors.text,
      },
      saveButton: {
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 16,
        alignItems: 'center',
        marginTop: 24,
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        borderColor: theme.colors.primary,
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 8,
      },
      saveButtonText: {
        color: theme.colors.primary,
        fontSize: 16,
        fontWeight: '600',
        letterSpacing: 0.2,
      },
      profileImageContainer: {
        alignItems: 'center',
        marginBottom: 24,
      },
      profileImage: {
        width: 100,
        height: 100,
        borderRadius: 50,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: theme.colors.primary,
      },
      profileInitials: {
        fontSize: 36,
        fontWeight: 'bold',
        color: '#FFFFFF',
      },
      changePhotoButton: {
        marginTop: 12,
      },
      changePhotoText: {
        color: theme.colors.primary,
        fontSize: 16,
      },
      themeFamily: {
        marginBottom: 32,
      },
      themeFamilyHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
      },
      themeFamilyName: {
        fontSize: 18,
        fontWeight: '600',
        marginRight: 8,
      },
      themeVariants: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        marginBottom: 8,
      },
      themeOption: {
        width: '48%',
        borderWidth: 2,
        borderRadius: 12,
        overflow: 'hidden',
        marginBottom: 16,
        padding: 12,
        borderColor: theme.colors.border,
      },
      themeOptionSelected: {
        borderColor: theme.colors.primary,
      },
      themePreview: {
        height: 80,
        borderRadius: 8,
        marginBottom: 8,
      },
      themeName: {
        fontSize: 14,
        textAlign: 'center',
        color: theme.colors.text,
      },
      featureItem: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 16,
      },
      featureText: {
        fontSize: 16,
        marginLeft: 12,
        color: theme.colors.text,
      },
      upgradeButton: {
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 16,
        alignItems: 'center',
        marginTop: 24,
        backgroundColor: theme.colors.primary,
        borderWidth: 0,
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 8,
      },
      upgradeButtonText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
        letterSpacing: 0.2,
      },
      switchSetting: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 16,
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.border,
      },
      switchTitle: {
        fontSize: 16,
        fontWeight: '500',
        color: theme.colors.text,
        marginBottom: 4,
        flex: 1,
        paddingRight: 16,
      },
      switchDescription: {
        fontSize: 14,
        color: theme.colors.subtext,
        flex: 1,
        paddingRight: 16,
      },
      formGroup: {
        marginBottom: 24,
      },
      proFeatureText: {
        fontSize: 12,
        color: theme.colors.secondary,
        marginTop: 2,
      },
      deleteButton: {
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 16,
        alignItems: 'center',
        marginTop: 16,
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        borderColor: theme.colors.error || '#FF3B30',
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 8,
      },
      deleteButtonText: {
        color: theme.colors.error || '#FF3B30',
        fontSize: 16,
        fontWeight: '600',
        letterSpacing: 0.2,
      },
    });
  }, [theme, modalHeight]);

  // Early return if theme is not yet available
  if (!theme) {
    return null;
  }

  const showModal = (modalType: ModalType) => {
    setActiveModal(modalType);
  };

  const hideModal = () => {
    setActiveModal(null);
  };

  // Group themes by family (light/dark pairs)
  const themeGroups: Record<string, ThemeGroup> = Object.values(availableThemes).reduce((groups, item) => {
    // Remove Light/Dark suffix to get base name
    const baseName = item.name.replace(' Light', '').replace(' Dark', '');
    if (!groups[baseName]) {
      groups[baseName] = { 
        name: baseName, 
        themes: [],
        premium: item.premium
      };
    }
    groups[baseName].themes.push(item);
    return groups;
  }, {});

  const settingsGroups: SettingsGroup[] = [{
    title: 'Account',
    settings: [{
      name: 'Profile',
      icon: 'person-circle-outline',
      onPress: () => showModal('profile')
    }, {
      name: 'Notifications',
      icon: 'notifications-outline',
      onPress: () => showModal('notifications')
    }, {
      name: 'Privacy',
      icon: 'shield-checkmark-outline',
      onPress: () => showModal('privacy')
    }]
  }, {
    title: 'Connections',
    settings: [{
      name: 'Canvas',
      icon: 'school-outline',
      connected: true,
      onPress: () => showModal('canvas')
    }, {
      name: 'Google Calendar',
      icon: 'calendar-outline',
      connected: true,
      onPress: () => showModal('googleCalendar')
    }, {
      name: 'Outlook',
      icon: 'mail-outline',
      connected: false,
      onPress: () => showModal('outlook')
    }]
  }, {
    title: 'Preferences',
    settings: [{
      name: 'Dark Mode',
      icon: darkMode ? 'moon-outline' : 'sunny-outline',
      customRight: (
        <Switch
          value={darkMode}
          onValueChange={onToggleDarkMode}
          trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
          thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
        />
      )
    }, {
      name: 'Study Times',
      icon: 'time-outline',
      onPress: () => showModal('studyTimes')
    }, {
      name: 'Focus Mode',
      icon: 'fitness-outline',
      onPress: () => showModal('focusMode')
    }, {
      name: 'AI Assistant',
      icon: 'sparkles-outline',
      onPress: () => showModal('aiAssistant')
    }]
  }, {
    title: 'Subscription',
    settings: [{
      name: 'PulsePlan Pro',
      icon: 'star-outline',
      highlight: true,
      onPress: () => showModal('subscription'),
      customRight: (
        <Switch
          value={isPremium}
          onValueChange={togglePremium}
          trackColor={{ false: '#E5E7EB', true: theme.colors.secondary }}
          thumbColor={isPremium ? '#FFFFFF' : '#FFFFFF'}
        />
      )
    }, {
      name: 'Restore Purchase',
      icon: 'refresh-circle-outline',
      onPress: () => showModal('restorePurchase')
    }]
  }, {
    title: 'Theme',
    settings: [{
      name: 'Choose Theme',
      icon: 'color-palette-outline',
      onPress: () => showModal('themes'),
      proFeature: !isPremium && Object.values(themeGroups).filter(g => g.premium).length > 0
    }]
  }];

  const renderModalContent = () => {
    if (!activeModal) return null;

    const modalContent = (
      <>
        <View style={{ width: '100%' }} {...panResponder.panHandlers}>
          <View style={styles.dragIndicator} />
          {(() => {
            switch (activeModal) {
              case 'profile':
                return (
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>Profile</Text>
                  </View>
                );
              case 'notifications':
                return (
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>Notifications</Text>
                  </View>
                );
              case 'focusMode':
                return (
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>Focus Mode</Text>
                  </View>
                );
              case 'themes':
                return (
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>Choose Theme</Text>
                  </View>
                );
              case 'subscription':
                return (
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>PulsePlan Pro</Text>
                  </View>
                );
              case 'privacy':
                return (
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>Privacy Settings</Text>
                  </View>
                );
              default:
                return (
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>Settings</Text>
                  </View>
                );
            }
          })()}
        </View>
        {(() => {
          switch (activeModal) {
            case 'profile':
              return (
                <ScrollView>
                  <View style={styles.modalBody}>
                    <View style={styles.profileImageContainer}>
                      <View style={styles.profileImage}>
                        <Text style={styles.profileInitials}>
                          {profileData.name.split(' ').map(n => n[0]).join('')}
                        </Text>
                      </View>
                      <TouchableOpacity style={styles.changePhotoButton}>
                        <Text style={styles.changePhotoText}>Change Photo</Text>
                      </TouchableOpacity>
                    </View>
                    <View style={styles.formGroup}>
                      <Text style={styles.label}>Name</Text>
                      <TextInput 
                        style={styles.input}
                        value={profileData.name}
                        onChangeText={(text) => updateProfile({ name: text })}
                        placeholder="Enter your name"
                        placeholderTextColor={theme.colors.subtext}
                      />
                    </View>
                    <View style={styles.formGroup}>
                      <Text style={styles.label}>Email</Text>
                      <TextInput 
                        style={styles.input}
                        value={profileData.email}
                        onChangeText={(text) => updateProfile({ email: text })}
                        keyboardType="email-address"
                        placeholder="Enter your email"
                        placeholderTextColor={theme.colors.subtext}
                      />
                    </View>
                    <View style={styles.formGroup}>
                      <Text style={styles.label}>School</Text>
                      <TextInput 
                        style={styles.input}
                        value={profileData.school}
                        onChangeText={(text) => updateProfile({ school: text })}
                        placeholder="Enter your school"
                        placeholderTextColor={theme.colors.subtext}
                      />
                    </View>
                    <View style={styles.formGroup}>
                      <Text style={styles.label}>Major</Text>
                      <TextInput 
                        style={styles.input}
                        value={profileData.major}
                        onChangeText={(text) => updateProfile({ major: text })}
                        placeholder="Enter your major"
                        placeholderTextColor={theme.colors.subtext}
                      />
                    </View>
                    <TouchableOpacity 
                      style={styles.saveButton}
                      onPress={() => setActiveModal(null)}
                    >
                      <Text style={styles.saveButtonText}>Save Changes</Text>
                    </TouchableOpacity>
                  </View>
                </ScrollView>
              );
            case 'notifications':
              return (
                <ScrollView>
                  <View style={styles.modalBody}>
                    <View style={styles.switchSetting}>
                      <View>
                        <Text style={styles.switchTitle}>Task Reminders</Text>
                        <Text style={styles.switchDescription}>
                          Get notified about upcoming tasks
                        </Text>
                      </View>
                      <Switch
                        value={notificationSettings.taskReminders}
                        onValueChange={(value) => setNotificationSettings({...notificationSettings, taskReminders: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>
                    <View style={styles.switchSetting}>
                      <View>
                        <Text style={styles.switchTitle}>Deadline Alerts</Text>
                        <Text style={styles.switchDescription}>
                          Alerts for approaching deadlines
                        </Text>
                      </View>
                      <Switch
                        value={notificationSettings.deadlineAlerts}
                        onValueChange={(value) => setNotificationSettings({...notificationSettings, deadlineAlerts: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>
                    <View style={styles.switchSetting}>
                      <View>
                        <Text style={styles.switchTitle}>Study Reminders</Text>
                        <Text style={styles.switchDescription}>
                          Reminders for scheduled study sessions
                        </Text>
                      </View>
                      <Switch
                        value={notificationSettings.studyReminders}
                        onValueChange={(value) => setNotificationSettings({...notificationSettings, studyReminders: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>
                    <View style={styles.switchSetting}>
                      <View>
                        <Text style={styles.switchTitle}>Weekly Reports</Text>
                        <Text style={styles.switchDescription}>
                          Weekly summary of your productivity
                        </Text>
                      </View>
                      <Switch
                        value={notificationSettings.weeklyReports}
                        onValueChange={(value) => setNotificationSettings({...notificationSettings, weeklyReports: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>
                    <TouchableOpacity style={styles.saveButton} onPress={() => setActiveModal(null)}>
                      <Text style={styles.saveButtonText}>Save Preferences</Text>
                    </TouchableOpacity>
                  </View>
                </ScrollView>
              );
            case 'focusMode':
              return (
                <ScrollView>
                  <View style={styles.modalBody}>
                    <View style={styles.switchSetting}>
                      <View style={{ flex: 1, paddingRight: 16 }}>
                        <Text style={styles.switchTitle}>Allow Notifications</Text>
                        <Text style={styles.switchDescription}>
                          Receive notifications while in focus mode
                        </Text>
                      </View>
                      <Switch
                        value={focusSettings.allowNotifications}
                        onValueChange={(value) => setFocusSettings({...focusSettings, allowNotifications: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>
                    <View style={styles.switchSetting}>
                      <View style={{ flex: 1, paddingRight: 16 }}>
                        <Text style={styles.switchTitle}>Auto-Enable</Text>
                        <Text style={styles.switchDescription}>
                          Automatically enable focus mode during study times
                        </Text>
                      </View>
                      <Switch
                        value={focusSettings.autoEnable}
                        onValueChange={(value) => setFocusSettings({...focusSettings, autoEnable: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>
                    <View style={{ marginTop: 16 }}>
                      <Text style={styles.label}>Focus Duration (minutes)</Text>
                      <TextInput 
                        style={styles.input}
                        value={focusSettings.duration.toString()}
                        onChangeText={(text) => setFocusSettings({...focusSettings, duration: parseInt(text) || 25})}
                        keyboardType="number-pad"
                        placeholder="25"
                        placeholderTextColor={theme.colors.subtext}
                      />
                    </View>
                    <TouchableOpacity style={styles.saveButton} onPress={() => setActiveModal(null)}>
                      <Text style={styles.saveButtonText}>Save Settings</Text>
                    </TouchableOpacity>
                  </View>
                </ScrollView>
              );
            case 'themes':
              return (
                <ScrollView>
                  <View style={styles.modalBody}>
                    {Object.entries(themeGroups).map(([familyName, group]) => (
                      <View key={familyName} style={{ marginBottom: 24 }}>
                        <Text style={[styles.switchTitle, { marginBottom: 16 }]}>{familyName}</Text>
                        <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
                          {group.themes.map((themeOption) => (
                            <TouchableOpacity
                              key={themeOption.name}
                              style={[
                                styles.themeOption,
                                theme.name === themeOption.name && styles.themeOptionSelected
                              ]}
                              onPress={() => setTheme(themeOption.id)}
                            >
                              <View style={[
                                styles.themePreview,
                                { backgroundColor: themeOption.colors.background }
                              ]} />
                              <Text style={styles.themeName}>{themeOption.name}</Text>
                              {themeOption.premium && !isPremium && (
                                <View style={[styles.proBadge, { backgroundColor: theme.colors.secondary }]}>
                                  <Text style={styles.proBadgeText}>PRO</Text>
                                </View>
                              )}
                            </TouchableOpacity>
                          ))}
                        </View>
                      </View>
                    ))}
                    {!isPremium && (
                      <TouchableOpacity style={styles.upgradeButton} onPress={() => showModal('subscription')}>
                        <Text style={styles.upgradeButtonText}>Upgrade to Pro for More Themes</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </ScrollView>
              );
            case 'subscription':
              return (
                <ScrollView>
                  <View style={styles.modalBody}>
                    <Text style={[styles.switchTitle, { marginBottom: 16 }]}>Premium Features</Text>
                    <View style={styles.featureItem}>
                      <Ionicons name="color-palette-outline" size={24} color={theme.colors.primary} />
                      <Text style={styles.featureText}>Premium Themes</Text>
                    </View>
                    <View style={styles.featureItem}>
                      <Ionicons name="analytics-outline" size={24} color={theme.colors.primary} />
                      <Text style={styles.featureText}>Advanced Analytics</Text>
                    </View>
                    <View style={styles.featureItem}>
                      <Ionicons name="cloud-upload-outline" size={24} color={theme.colors.primary} />
                      <Text style={styles.featureText}>Cloud Backup</Text>
                    </View>
                    <View style={styles.featureItem}>
                      <Ionicons name="infinite-outline" size={24} color={theme.colors.primary} />
                      <Text style={styles.featureText}>Unlimited Tasks</Text>
                    </View>
                    <TouchableOpacity 
                      style={[styles.upgradeButton, { backgroundColor: theme.colors.secondary }]}
                      onPress={togglePremium}
                    >
                      <Text style={styles.upgradeButtonText}>
                        {isPremium ? 'Manage Subscription' : 'Upgrade to Pro'}
                      </Text>
                    </TouchableOpacity>
                  </View>
                </ScrollView>
              );
            case 'privacy':
              return (
                <ScrollView
                  showsVerticalScrollIndicator={true}
                  bounces={true}
                  contentContainerStyle={{}}
                >
                  <View style={styles.modalBody}>
                    <Text style={[styles.switchDescription, { 
                      marginBottom: 24,
                      lineHeight: 20
                    }]}
                    >
                      Control how your data is used to improve your experience. These settings help us provide you with a better service while respecting your privacy.
                    </Text>
                    
                    <View style={[styles.switchSetting, { marginBottom: 8 }]}>
                      <View style={{ flex: 1, paddingRight: 16 }}>
                        <Text style={styles.switchTitle}>Share Analytics</Text>
                        <Text style={[styles.switchDescription, { lineHeight: 18 }]}>
                          Help us improve by sharing anonymous usage statistics. This data is aggregated and cannot be used to identify you.
                        </Text>
                      </View>
                      <Switch
                        value={privacySettings.shareAnalytics}
                        onValueChange={(value) => setPrivacySettings({...privacySettings, shareAnalytics: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>

                    <View style={[styles.switchSetting, { marginBottom: 8 }]}>
                      <View style={{ flex: 1, paddingRight: 16 }}>
                        <Text style={styles.switchTitle}>Share Usage Data</Text>
                        <Text style={[styles.switchDescription, { lineHeight: 18 }]}>
                          Allow us to collect data about how you use the app to improve features and fix issues.
                        </Text>
                      </View>
                      <Switch
                        value={privacySettings.shareUsageData}
                        onValueChange={(value) => setPrivacySettings({...privacySettings, shareUsageData: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>

                    <View style={[styles.switchSetting, { marginBottom: 8 }]}>
                      <View style={{ flex: 1, paddingRight: 16 }}>
                        <Text style={styles.switchTitle}>Personalization</Text>
                        <Text style={[styles.switchDescription, { lineHeight: 18 }]}>
                          Allow AI to personalize your experience based on your usage patterns and preferences.
                        </Text>
                      </View>
                      <Switch
                        value={privacySettings.allowPersonalization}
                        onValueChange={(value) => setPrivacySettings({...privacySettings, allowPersonalization: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>

                    <View style={[styles.switchSetting, { marginBottom: 8 }]}>
                      <View style={{ flex: 1, paddingRight: 16 }}>
                        <Text style={styles.switchTitle}>Show Task Details</Text>
                        <Text style={[styles.switchDescription, { lineHeight: 18 }]}>
                          Display detailed task information in shared views and calendar integrations.
                        </Text>
                      </View>
                      <Switch
                        value={privacySettings.showTaskDetails}
                        onValueChange={(value) => setPrivacySettings({...privacySettings, showTaskDetails: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>

                    <View style={[styles.switchSetting, { marginBottom: 24 }]}>
                      <View style={{ flex: 1, paddingRight: 16 }}>
                        <Text style={styles.switchTitle}>Sync Across Devices</Text>
                        <Text style={[styles.switchDescription, { lineHeight: 18 }]}>
                          Keep your data synchronized across all your devices for a seamless experience.
                        </Text>
                      </View>
                      <Switch
                        value={privacySettings.syncAcrossDevices}
                        onValueChange={(value) => setPrivacySettings({...privacySettings, syncAcrossDevices: value})}
                        trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                        thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                      />
                    </View>

                    <TouchableOpacity 
                      style={[styles.saveButton, { marginTop: 16 }]}
                      onPress={() => {
                        // TODO: Implement privacy settings save logic
                        setActiveModal(null);
                      }}
                    >
                      <Text style={styles.saveButtonText}>Save Privacy Settings</Text>
                    </TouchableOpacity>

                    <TouchableOpacity 
                      style={[styles.deleteButton, { 
                        marginTop: 16, 
                        marginBottom: 16
                      }]}
                      onPress={() => {
                        Alert.alert(
                          'Delete All Data',
                          'Are you sure you want to delete all your data? This action cannot be undone.',
                          [
                            {
                              text: 'Cancel',
                              style: 'cancel'
                            },
                            {
                              text: 'Delete',
                              style: 'destructive',
                              onPress: () => {
                                // TODO: Implement data deletion
                                setActiveModal(null);
                              }
                            }
                          ]
                        );
                      }}
                    >
                      <Text style={styles.deleteButtonText}>Delete All Data</Text>
                    </TouchableOpacity>
                  </View>
                </ScrollView>
              );
            default:
              return (
                <View style={styles.modalBody}>
                  <Text style={{ color: theme.colors.text }}>Settings content coming soon...</Text>
                </View>
              );
          }
        })()}
      </>
    );

    return (
      <Animated.View style={styles.modalContainer}>
        {modalContent}
      </Animated.View>
    );
  };

  return (
    <View style={{ flex: 1 }}>
      <ScrollView 
        style={[styles.container, { backgroundColor: theme.colors.background }]}
        contentContainerStyle={styles.contentContainer}
      >
        <View style={styles.header}>
          <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
            Settings
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.colors.subtext }]}>
            Customize your PulsePlan experience
          </Text>
        </View>

        <View style={styles.groupsContainer}>
          {settingsGroups.map((group, index) => (
            <View key={index} style={styles.group}>
              <Text style={[styles.groupTitle, { color: theme.colors.primary }]}>{group.title}</Text>
              <View style={[
                styles.settingsContainer,
                { backgroundColor: theme.colors.cardBackground }
              ]}>
                {group.settings.map((setting, settingIndex) => (
                  <TouchableOpacity
                    key={settingIndex}
                    style={[
                      styles.settingItem,
                      settingIndex !== group.settings.length - 1 && styles.settingItemBorder,
                      { borderBottomColor: theme.colors.border },
                      setting.highlight && styles.highlightedSetting
                    ]}
                    onPress={setting.onPress || undefined}
                  >
                    <View style={styles.settingLeft}>
                      <View style={styles.iconContainer}>
                        <Ionicons 
                          name={setting.icon} 
                          size={20} 
                          color={theme.colors.primary} 
                        />
                      </View>
                      <View>
                        <Text style={[styles.settingName, { color: theme.colors.text }]}>
                          {setting.name}
                        </Text>
                        {setting.proFeature && (
                          <Text style={[styles.proFeatureText, { color: theme.colors.secondary }]}>
                            Pro feature
                          </Text>
                        )}
                      </View>
                    </View>
                    <View style={styles.settingRight}>
                      {setting.connected !== undefined && (
                        <Text style={[
                          styles.connectionStatus,
                          { color: setting.connected ? theme.colors.success : theme.colors.subtext }
                        ]}>
                          {setting.connected ? 'Connected' : 'Not Connected'}
                        </Text>
                      )}
                      {setting.customRight ? (
                        setting.customRight
                      ) : setting.highlight ? (
                        <View style={[styles.proBadge, { backgroundColor: theme.colors.secondary }]}>
                          <Text style={styles.proBadgeText}>PRO</Text>
                        </View>
                      ) : (
                        <Ionicons name="chevron-forward" size={20} color={theme.colors.subtext} />
                      )}
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          ))}
        </View>

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.colors.subtext }]}>PulsePlan v1.0.0</Text>
          <Text style={[styles.footerText, { color: theme.colors.subtext }]}>© {new Date().getFullYear()} PulsePlan App</Text>
        </View>
      </ScrollView>

      <Modal
        visible={activeModal !== null}
        transparent={true}
        onRequestClose={hideModal}
        animationType="fade"
      >
        <View style={styles.modalOverlay}>
          <TouchableOpacity 
            style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
            activeOpacity={1} 
            onPress={hideModal}
          />
          <Animated.View 
            style={[
              styles.modalContainer,
              { transform: [{ translateY: pan.y }] }
            ]} 
          >
            {renderModalContent()}
          </Animated.View>
        </View>
      </Modal>
    </View>
  );
};