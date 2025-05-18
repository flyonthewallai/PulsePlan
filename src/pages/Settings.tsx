import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, Modal, TextInput, FlatList, Animated, Dimensions, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard, Easing } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme, themes } from '../contexts/ThemeContext';
import { usePremium } from '../../App';

export const Settings = ({
  darkMode,
  onToggleDarkMode
}) => {
  const { theme, setTheme, availableThemes, isPremium } = useTheme();
  const { togglePremium } = usePremium();
  const [activeModal, setActiveModal] = useState(null);
  const [notificationSettings, setNotificationSettings] = useState({
    taskReminders: true,
    deadlineAlerts: true,
    studyReminders: false,
    weeklyReports: true
  });
  const [profileData, setProfileData] = useState({
    name: 'Alex Johnson',
    email: 'alex@example.com',
    school: 'State University',
    major: 'Computer Science'
  });
  const [focusSettings, setFocusSettings] = useState({
    allowNotifications: false,
    autoEnable: true,
    duration: 25
  });
  
  const modalAnimation = useRef(new Animated.Value(0)).current;
  const { height: screenHeight } = Dimensions.get('window');

  const showModal = (modalType) => {
    setActiveModal(modalType);
    Animated.timing(modalAnimation, {
      toValue: 1,
      duration: 250,
      useNativeDriver: true,
      easing: Easing.out(Easing.ease)
    }).start();
  };

  const hideModal = () => {
    Animated.timing(modalAnimation, {
      toValue: 0,
      duration: 200,
      useNativeDriver: true,
      easing: Easing.in(Easing.ease)
    }).start(() => setActiveModal(null));
  };

  const modalTranslateY = modalAnimation.interpolate({
    inputRange: [0, 1],
    outputRange: [screenHeight, 0]
  });

  // Group themes by family (light/dark pairs)
  const themeGroups = Object.values(availableThemes).reduce((groups, item) => {
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

  const settingsGroups = [{
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

  const handleModalPress = (e) => {
    // Only close if clicking the overlay, not the modal content
    if (e.target === e.currentTarget) {
      hideModal();
    }
  };

  const renderModalContent = () => {
    const headerStyle = [
      styles.modalHeader,
      { borderBottomColor: theme.colors.border }
    ];
    const textStyle = { color: theme.colors.text };
    const subtextStyle = { color: theme.colors.subtext };
    const inputStyle = [
      styles.input,
      { 
        borderColor: theme.colors.border,
        backgroundColor: theme.colors.cardBackground,
        color: theme.colors.text
      }
    ];

    const wrapWithKeyboardAvoiding = (content) => {
      if (activeModal === 'profile' || activeModal === 'notifications' || activeModal === 'focusMode') {
        return (
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={styles.keyboardAvoidingView}
            keyboardVerticalOffset={Platform.OS === 'ios' ? 40 : 0}
          >
            {content}
          </KeyboardAvoidingView>
        );
      }
      return content;
    };

    const modalContent = (() => {
      switch (activeModal) {
        case 'profile':
          return (
            <View style={styles.modalWrapper}>
              <View style={headerStyle}>
                <Text style={[styles.modalTitle, textStyle]}>Profile</Text>
                <TouchableOpacity onPress={hideModal}>
                  <Ionicons name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.modalScrollView}>
                <View style={styles.modalContent}>
                  <View style={styles.profileImageContainer}>
                    <View style={[styles.profileImage, { backgroundColor: theme.colors.primary }]}>
                      <Text style={styles.profileInitials}>
                        {profileData.name.split(' ').map(n => n[0]).join('')}
                      </Text>
                    </View>
                    <TouchableOpacity style={styles.changePhotoButton}>
                      <Text style={{ color: theme.colors.primary }}>Change Photo</Text>
                    </TouchableOpacity>
                  </View>
                  <View style={styles.formGroup}>
                    <Text style={[styles.label, textStyle]}>Name</Text>
                    <TextInput 
                      style={inputStyle}
                      value={profileData.name}
                      onChangeText={(text) => setProfileData({...profileData, name: text})}
                    />
                  </View>
                  <View style={styles.formGroup}>
                    <Text style={[styles.label, textStyle]}>Email</Text>
                    <TextInput 
                      style={inputStyle}
                      value={profileData.email}
                      onChangeText={(text) => setProfileData({...profileData, email: text})}
                      keyboardType="email-address"
                    />
                  </View>
                  <View style={styles.formGroup}>
                    <Text style={[styles.label, textStyle]}>School</Text>
                    <TextInput 
                      style={inputStyle}
                      value={profileData.school}
                      onChangeText={(text) => setProfileData({...profileData, school: text})}
                    />
                  </View>
                  <View style={styles.formGroup}>
                    <Text style={[styles.label, textStyle]}>Major</Text>
                    <TextInput 
                      style={inputStyle}
                      value={profileData.major}
                      onChangeText={(text) => setProfileData({...profileData, major: text})}
                    />
                  </View>
                  <TouchableOpacity style={[styles.saveButton, { backgroundColor: theme.colors.primary }]}>
                    <Text style={styles.saveButtonText}>Save Changes</Text>
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          );
        
        case 'notifications':
          return (
            <View style={styles.modalWrapper}>
              <View style={headerStyle}>
                <Text style={[styles.modalTitle, textStyle]}>Notifications</Text>
                <TouchableOpacity onPress={hideModal}>
                  <Ionicons name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.modalScrollView}>
                <View style={styles.modalContent}>
                  <View style={[styles.switchSetting, { borderBottomColor: theme.colors.border }]}>
                    <View>
                      <Text style={[styles.switchTitle, textStyle]}>Task Reminders</Text>
                      <Text style={[styles.switchDescription, subtextStyle]}>
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
                  <View style={[styles.switchSetting, { borderBottomColor: theme.colors.border }]}>
                    <View>
                      <Text style={[styles.switchTitle, textStyle]}>Deadline Alerts</Text>
                      <Text style={[styles.switchDescription, subtextStyle]}>
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
                  <View style={[styles.switchSetting, { borderBottomColor: theme.colors.border }]}>
                    <View>
                      <Text style={[styles.switchTitle, textStyle]}>Study Reminders</Text>
                      <Text style={[styles.switchDescription, subtextStyle]}>
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
                  <View style={[styles.switchSetting, { borderBottomColor: theme.colors.border }]}>
                    <View>
                      <Text style={[styles.switchTitle, textStyle]}>Weekly Reports</Text>
                      <Text style={[styles.switchDescription, subtextStyle]}>
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
                  <TouchableOpacity style={[styles.saveButton, { backgroundColor: theme.colors.primary }]}>
                    <Text style={styles.saveButtonText}>Save Preferences</Text>
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          );
        
        case 'focusMode':
          return (
            <View style={styles.modalWrapper}>
              <View style={headerStyle}>
                <Text style={[styles.modalTitle, textStyle]}>Focus Mode Settings</Text>
                <TouchableOpacity onPress={hideModal}>
                  <Ionicons name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.modalScrollView}>
                <View style={styles.modalContent}>
                  <View style={[styles.switchSetting, { borderBottomColor: theme.colors.border }]}>
                    <View>
                      <Text style={[styles.switchTitle, textStyle]}>Allow Notifications</Text>
                      <Text style={[styles.switchDescription, subtextStyle]}>
                        Allow notifications during focus mode
                      </Text>
                    </View>
                    <Switch
                      value={focusSettings.allowNotifications}
                      onValueChange={(value) => setFocusSettings({...focusSettings, allowNotifications: value})}
                      trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                      thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                    />
                  </View>
                  <View style={[styles.switchSetting, { borderBottomColor: theme.colors.border }]}>
                    <View>
                      <Text style={[styles.switchTitle, textStyle]}>Auto-enable for Study Tasks</Text>
                      <Text style={[styles.switchDescription, subtextStyle]}>
                        Automatically enable focus mode for study tasks
                      </Text>
                    </View>
                    <Switch
                      value={focusSettings.autoEnable}
                      onValueChange={(value) => setFocusSettings({...focusSettings, autoEnable: value})}
                      trackColor={{ false: '#E5E7EB', true: theme.colors.primary }}
                      thumbColor={darkMode ? '#FFFFFF' : '#FFFFFF'}
                    />
                  </View>
                  <View style={[styles.sliderSetting, { borderBottomColor: theme.colors.border }]}>
                    <Text style={[styles.switchTitle, textStyle]}>Focus Duration</Text>
                    <Text style={[styles.sliderValue, textStyle]}>{focusSettings.duration} minutes</Text>
                    <View style={styles.sliderButtons}>
                      <TouchableOpacity 
                        style={[styles.sliderButton, { borderColor: theme.colors.border }]}
                        onPress={() => setFocusSettings({...focusSettings, duration: Math.max(5, focusSettings.duration - 5)})}
                      >
                        <Text style={textStyle}>-5</Text>
                      </TouchableOpacity>
                      <TouchableOpacity 
                        style={[styles.sliderButton, { borderColor: theme.colors.border }]}
                        onPress={() => setFocusSettings({...focusSettings, duration: Math.min(120, focusSettings.duration + 5)})}
                      >
                        <Text style={textStyle}>+5</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                  <TouchableOpacity style={[styles.saveButton, { backgroundColor: theme.colors.primary }]}>
                    <Text style={styles.saveButtonText}>Save Settings</Text>
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          );
        
        case 'themes':
          return (
            <View style={styles.modalWrapper}>
              <View style={headerStyle}>
                <Text style={[styles.modalTitle, textStyle]}>Choose Theme</Text>
                <TouchableOpacity onPress={hideModal}>
                  <Ionicons name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.modalScrollView}>
                <View style={styles.modalContent}>
                  <Text style={[styles.themesDescription, subtextStyle]}>
                    Personalize your app with themes
                  </Text>
                  <FlatList
                    data={Object.values(themeGroups)}
                    keyExtractor={(item) => item.name}
                    scrollEnabled={false}
                    renderItem={({ item }) => (
                      <View style={styles.themeFamily}>
                        <View style={styles.themeFamilyHeader}>
                          <Text style={[styles.themeFamilyName, textStyle]}>{item.name}</Text>
                          {item.premium && !isPremium && (
                            <View style={styles.premiumBadge}>
                              <Text style={styles.premiumBadgeText}>PRO</Text>
                            </View>
                          )}
                        </View>
                        <View style={styles.themeVariants}>
                          {item.themes.map((themeItem) => {
                            const isSelected = theme.id === themeItem.id;
                            const isDisabled = themeItem.premium && !isPremium;
                            
                            return (
                              <TouchableOpacity 
                                key={themeItem.id}
                                style={[
                                  styles.themeOption,
                                  { 
                                    borderColor: isSelected ? theme.colors.primary : theme.colors.border,
                                    opacity: isDisabled ? 0.5 : 1
                                  }
                                ]}
                                onPress={() => {
                                  if (!isDisabled) {
                                    setTheme(themeItem.id);
                                  } else {
                                    showModal('subscription');
                                  }
                                }}
                                disabled={isDisabled}
                              >
                                <View style={[
                                  styles.themePreview, 
                                  { backgroundColor: themeItem.colors.background }
                                ]}>
                                  <View style={[
                                    styles.themePreviewCard, 
                                    { backgroundColor: themeItem.colors.cardBackground }
                                  ]}>
                                    <View style={[
                                      styles.themePreviewItem,
                                      { backgroundColor: themeItem.colors.primary }
                                    ]} />
                                  </View>
                                </View>
                                <Text style={[
                                  styles.themeVariantName, 
                                  { color: theme.colors.text }
                                ]}>
                                  {themeItem.isDark ? 'Dark' : 'Light'}
                                </Text>
                                {isSelected && (
                                  <Ionicons 
                                    name="checkmark-circle" 
                                    size={24} 
                                    color={theme.colors.primary}
                                    style={styles.selectedIcon}
                                  />
                                )}
                              </TouchableOpacity>
                            );
                          })}
                        </View>
                      </View>
                    )}
                  />
                  
                  {!isPremium && (
                    <TouchableOpacity 
                      style={[styles.upgradeButton, { backgroundColor: theme.colors.secondary }]}
                      onPress={() => showModal('subscription')}
                    >
                      <Text style={styles.upgradeButtonText}>Upgrade to Pro</Text>
                      <Text style={styles.upgradeButtonSubtext}>Unlock all premium themes</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </ScrollView>
            </View>
          );
        
        case 'subscription':
          return (
            <View style={styles.modalWrapper}>
              <View style={headerStyle}>
                <Text style={[styles.modalTitle, textStyle]}>PulsePlan Pro</Text>
                <TouchableOpacity onPress={hideModal}>
                  <Ionicons name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.modalScrollView}>
                <View style={styles.modalContent}>
                  <View style={styles.subscriptionHeader}>
                    <Ionicons name="star" size={40} color="#FFD700" />
                    <Text style={[styles.subscriptionTitle, textStyle]}>Upgrade to Pro</Text>
                    <Text style={[styles.subscriptionPrice, textStyle]}>$4.99/month</Text>
                  </View>
                  
                  <View style={styles.featuresList}>
                    <View style={styles.featureItem}>
                      <Ionicons name="checkmark-circle" size={24} color={theme.colors.primary} />
                      <Text style={[styles.featureText, textStyle]}>Premium themes</Text>
                    </View>
                    <View style={styles.featureItem}>
                      <Ionicons name="checkmark-circle" size={24} color={theme.colors.primary} />
                      <Text style={[styles.featureText, textStyle]}>Advanced analytics</Text>
                    </View>
                    <View style={styles.featureItem}>
                      <Ionicons name="checkmark-circle" size={24} color={theme.colors.primary} />
                      <Text style={[styles.featureText, textStyle]}>AI task suggestions</Text>
                    </View>
                    <View style={styles.featureItem}>
                      <Ionicons name="checkmark-circle" size={24} color={theme.colors.primary} />
                      <Text style={[styles.featureText, textStyle]}>Cloud sync across devices</Text>
                    </View>
                    <View style={styles.featureItem}>
                      <Ionicons name="checkmark-circle" size={24} color={theme.colors.primary} />
                      <Text style={[styles.featureText, textStyle]}>Priority support</Text>
                    </View>
                  </View>
                  
                  <TouchableOpacity style={[styles.subscribeButton, { backgroundColor: theme.colors.secondary }]}>
                    <Text style={styles.subscribeButtonText}>Subscribe Now</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity style={styles.annualPlanButton}>
                    <Text style={{ color: theme.colors.primary }}>Save 20% with annual plan</Text>
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          );
        
        default:
          return (
            <View style={styles.modalWrapper}>
              <View style={headerStyle}>
                <Text style={[styles.modalTitle, textStyle]}>Setting Details</Text>
                <TouchableOpacity onPress={hideModal}>
                  <Ionicons name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
              <View style={styles.modalContent}>
                <Text style={[styles.modalText, textStyle]}>
                  This setting is not yet implemented.
                </Text>
                <TouchableOpacity 
                  style={[styles.closeButton, { backgroundColor: theme.colors.primary }]}
                  onPress={hideModal}
                >
                  <Text style={styles.closeButtonText}>Close</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
      }
    })();

    return wrapWithKeyboardAvoiding(
      <View style={styles.modalOverlay}>
        <TouchableWithoutFeedback onPress={hideModal}>
          <View style={styles.modalOverlayTouchable} />
        </TouchableWithoutFeedback>
        <Animated.View 
          style={[
            styles.modalContainer,
            { 
              backgroundColor: theme.colors.cardBackground,
              transform: [{ translateY: modalTranslateY }]
            }
          ]}
        >
          {modalContent}
        </Animated.View>
      </View>
    );
  };

  return (
    <>
      <ScrollView 
        style={[
          styles.container,
          { backgroundColor: theme.colors.background }
        ]}
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
                      <View style={[
                        styles.iconContainer,
                        { backgroundColor: theme.colors.primary + '15' }
                      ]}>
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
        animationType="none"
        onRequestClose={hideModal}
        statusBarTranslucent
      >
        {renderModalContent()}
      </Modal>
    </>
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
    marginBottom: 32,
  },
  headerTitle: {
    fontSize: 32,
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
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalOverlayTouchable: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  modalContainer: {
    width: '100%',
    maxHeight: '85%',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    overflow: 'hidden',
  },
  modalWrapper: {
    flex: 1,
    backgroundColor: theme.colors.cardBackground,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    backgroundColor: theme.colors.cardBackground,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  modalText: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 16,
  },
  closeButton: {
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '500',
  },
  profileImageContainer: {
    alignItems: 'center',
    marginVertical: 24,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
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
    fontSize: 16,
  },
  formGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    marginBottom: 8,
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    marginBottom: 16,
  },
  saveButton: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 32,
    marginBottom: 16,
  },
  saveButtonText: {
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
    marginBottom: 8,
  },
  switchTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
    letterSpacing: 0.2,
  },
  switchDescription: {
    fontSize: 14,
    letterSpacing: 0.1,
    opacity: 0.8,
  },
  sliderSetting: {
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  sliderValue: {
    fontSize: 18,
    fontWeight: 'bold',
    marginVertical: 8,
  },
  sliderButtons: {
    flexDirection: 'row',
    marginTop: 8,
  },
  sliderButton: {
    width: 60,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 8,
    marginRight: 12,
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
    position: 'relative',
  },
  themePreview: {
    height: 100,
    padding: 12,
  },
  themePreviewCard: {
    flex: 1,
    borderRadius: 8,
    padding: 8,
    justifyContent: 'flex-end',
  },
  themePreviewItem: {
    height: 16,
    width: '70%',
    borderRadius: 4,
  },
  themeVariantName: {
    textAlign: 'center',
    padding: 8,
    fontWeight: '500',
  },
  selectedIcon: {
    position: 'absolute',
    top: 8,
    right: 8,
  },
  themesDescription: {
    marginBottom: 24,
    fontSize: 14,
  },
  upgradeButton: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
  },
  upgradeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  upgradeButtonSubtext: {
    color: '#FFFFFF',
    opacity: 0.8,
    fontSize: 12,
    marginTop: 4,
  },
  proFeatureText: {
    fontSize: 12,
  },
  subscriptionHeader: {
    alignItems: 'center',
    marginVertical: 32,
  },
  subscriptionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginVertical: 8,
  },
  subscriptionPrice: {
    fontSize: 18,
  },
  featuresList: {
    marginVertical: 24,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  featureText: {
    fontSize: 16,
    marginLeft: 12,
  },
  subscribeButton: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 16,
  },
  subscribeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  annualPlanButton: {
    padding: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  annualPlanText: {
    fontSize: 14,
  },
});