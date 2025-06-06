import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity,
  Switch,
  StatusBar,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import DateTimePicker from '@react-native-community/datetimepicker';
import { 
  Calendar, 
  Clock, 
  CreditCard, 
  LogOut, 
  Moon, 
  PaintBucket, 
  Palette, 
  Sun, 
  User,
  Bell,
  Edit,
  ChevronRight,
  Plus,
} from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';

import { colors } from '../../constants/theme';
import ThemeSelector from '../../components/ThemeSelector';
import { signOut } from '../../lib/supabase-rn';
import { useAuth } from '../../contexts/AuthContext';
import { useSettings } from '../../contexts/SettingsContext';
import { useTheme } from '../../contexts/ThemeContext';
import CalendarIntegrationModal from '../../components/CalendarIntegrationModal';
import CanvasModal from '../../components/CanvasModal';

interface SubjectColor {
  id: string;
  name: string;
  color: string;
}

export default function SettingsScreen() {
  const router = useRouter();
  const { user, refreshAuth } = useAuth();
  const { workingHours, updateWorkingHours } = useSettings();
  const { currentTheme, allThemes, setTheme, isThemeUnlocked } = useTheme();

  // Get dynamic colors from current theme
  const themeColors = {
    background: currentTheme.colors.background,
    surface: currentTheme.colors.surface,
    primary: currentTheme.colors.primary,
    textPrimary: currentTheme.colors.textPrimary,
    textSecondary: currentTheme.colors.textSecondary,
    border: currentTheme.colors.border,
    card: currentTheme.colors.card,
    success: currentTheme.colors.success,
    warning: currentTheme.colors.warning,
    error: currentTheme.colors.error,
  };

  const [integrations, setIntegrations] = useState({
    canvas: true,
    googleCalendar: true,
  });
  const [breakDuration, setBreakDuration] = useState('30');
  const [enableNotifications, setEnableNotifications] = useState(true);
  const [subjectColors, setSubjectColors] = useState<SubjectColor[]>([
    { id: '1', name: 'Mathematics', color: '#FF6B6B' },
    { id: '2', name: 'Science', color: '#4ECDC4' },
    { id: '3', name: 'History', color: '#FFD93D' },
    { id: '4', name: 'Literature', color: '#95E1D3' },
  ]);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCalendarModal, setShowCalendarModal] = useState(false);
  const [showCanvasModal, setShowCanvasModal] = useState(false);
  const [editedName, setEditedName] = useState(user?.user_metadata?.full_name || '');
  const [editedEmail, setEditedEmail] = useState(user?.email || '');
  
  // Time picker states
  const [showStartTimePicker, setShowStartTimePicker] = useState(false);
  const [showEndTimePicker, setShowEndTimePicker] = useState(false);
  const [tempStartTime, setTempStartTime] = useState(new Date());
  const [tempEndTime, setTempEndTime] = useState(new Date());

  // Initialize temp times based on workingHours
  React.useEffect(() => {
    const startTime = new Date();
    startTime.setHours(workingHours.startHour, 0, 0, 0);
    setTempStartTime(startTime);

    const endTime = new Date();
    endTime.setHours(workingHours.endHour, 0, 0, 0);
    setTempEndTime(endTime);
  }, [workingHours]);

  const toggleIntegration = (key: keyof typeof integrations) => {
    setIntegrations(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleLogout = async () => {
    console.log('🚪 handleLogout function called - START');
    
    // Web-compatible confirmation dialog
    const confirmLogout = () => {
      if (typeof window !== 'undefined') {
        // Web environment - use browser confirm
        return window.confirm('Are you sure you want to log out?');
      } else {
        // Mobile environment - use Alert.alert
        return new Promise((resolve) => {
          Alert.alert(
            'Confirm Logout',
            'Are you sure you want to log out?',
            [
              { text: 'Cancel', style: 'cancel', onPress: () => resolve(false) },
              { text: 'Log Out', style: 'destructive', onPress: () => resolve(true) }
            ]
          );
        });
      }
    };

    const shouldLogout = await confirmLogout();
    console.log('🔍 User confirmation result:', shouldLogout);
    
    if (!shouldLogout) {
      console.log('❌ User cancelled logout');
      return;
    }

    console.log('✅ User confirmed logout, proceeding...');
    console.log('👤 Current user before logout:', {
      email: user?.email,
      id: user?.id,
      fullName: user?.user_metadata?.full_name
    });
    
    try {
      console.log('🔄 Calling enhanced signOut function...');
      
      // Call the enhanced signOut function
      const result = await signOut();
      
      console.log('📊 SignOut result:', result);
      
      if (result && !result.success) {
        console.error('⚠️ SignOut reported failure but continuing...');
      }
      
      console.log('🔄 Refreshing auth context after signOut...');
      await refreshAuth();
      
      console.log('✅ Settings logout process completed');
      console.log('📱 User should now be redirected to login screen');
      
      // Note: Navigation will be handled automatically by AuthContext
      // when it detects the user is no longer authenticated
      
    } catch (error) {
      console.error('❌ Unexpected error during settings logout:', error);
      console.log('🛠️ Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : 'No stack trace'
      });
      
      // Web-compatible error alert
      if (typeof window !== 'undefined') {
        window.alert('An unexpected error occurred while logging out. You may need to restart the app.');
      } else {
        Alert.alert(
          'Logout Error', 
          'An unexpected error occurred while logging out. You may need to restart the app.'
        );
      }
    }
  };

  const handleThemeChange = async (themeId: string) => {
    try {
      const theme = allThemes.find(t => t.id === themeId);
      if (!theme) return;

      if (theme.premium && !isThemeUnlocked(themeId)) {
        Alert.alert(
          'Premium Theme',
          'This theme requires PulsePlan Premium. Would you like to upgrade?',
          [
            { text: 'Cancel', style: 'cancel' },
            { 
              text: 'Upgrade', 
              onPress: () => {
                // TODO: Navigate to premium upgrade screen
                Alert.alert('Coming Soon', 'Premium upgrade will be available soon!');
              }
            }
          ]
        );
        return;
      }

      await setTheme(themeId);
    } catch (error) {
      console.error('Error changing theme:', error);
      Alert.alert('Error', 'Failed to change theme. Please try again.');
    }
  };

  const handleSaveProfile = () => {
    // TODO: Implement profile update logic with Supabase
    Alert.alert('Success', 'Profile updated successfully!');
    setShowEditModal(false);
  };

  const handleEditProfile = () => {
    setEditedName(user?.user_metadata?.full_name || '');
    setEditedEmail(user?.email || '');
    setShowEditModal(true);
  };

  const handleAddSubject = () => {
    // TODO: Implement add subject logic
    Alert.alert('Coming Soon', 'Subject management will be available in the next update!');
  };

  const formatTimeDisplay = (hour: number) => {
    const time = new Date();
    time.setHours(hour, 0, 0, 0);
    return time.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const handleStartTimeChange = (event: any, selectedTime?: Date) => {
    if (selectedTime) {
      setTempStartTime(selectedTime);
    }
  };

  const handleEndTimeChange = (event: any, selectedTime?: Date) => {
    if (selectedTime) {
      setTempEndTime(selectedTime);
    }
  };

  const saveStartTime = async () => {
    const newHour = tempStartTime.getHours();
    try {
      await updateWorkingHours({
        ...workingHours,
        startHour: newHour
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to save start time');
    }
    setShowStartTimePicker(false);
  };

  const saveEndTime = async () => {
    const newHour = tempEndTime.getHours();
    try {
      await updateWorkingHours({
        ...workingHours,
        endHour: newHour
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to save end time');
    }
    setShowEndTimePicker(false);
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: themeColors.background }]} edges={['top']}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <Text style={[styles.title, { color: themeColors.textPrimary }]}>Settings</Text>
      </View>

      <ScrollView 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        {/* Profile Section */}
        <View style={[styles.profileCard, { backgroundColor: themeColors.surface }]}>
          <View style={[styles.profileCircle, { backgroundColor: themeColors.primary }]}>
            <Text style={[styles.profileInitial, { color: themeColors.textPrimary }]}>
              {user?.user_metadata?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
            </Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={[styles.profileName, { color: themeColors.textPrimary }]}>
              {user?.user_metadata?.full_name || 'User'}
            </Text>
            <Text style={[styles.profileEmail, { color: themeColors.textSecondary }]}>
              {user?.email || 'user@example.com'}
            </Text>
          </View>
          <TouchableOpacity style={[styles.editButton, { backgroundColor: themeColors.card }]} onPress={handleEditProfile}>
            <Text style={[styles.editButtonText, { color: themeColors.textPrimary }]}>Edit</Text>
          </TouchableOpacity>
        </View>

        {/* Theme Section */}
        <View style={[styles.section, { backgroundColor: themeColors.surface }]}>
          <View style={styles.sectionHeader}>
            <Edit size={20} color={themeColors.textSecondary} />
            <Text style={[styles.sectionTitle, { color: themeColors.textPrimary }]}>Theme</Text>
          </View>
          
          <ThemeSelector 
            themes={allThemes} 
            selectedTheme={currentTheme.id}
            onSelectTheme={handleThemeChange}
            isPremium={true}
          />
        </View>

        {/* Study Time Preferences */}
        <View style={[styles.section, { backgroundColor: themeColors.surface }]}>
          <View style={styles.sectionHeader}>
            <Clock size={20} color={themeColors.textPrimary} />
            <Text style={[styles.sectionTitle, { color: themeColors.textPrimary }]}>Study Time Preferences</Text>
          </View>

          <View style={[styles.settingItem, { borderBottomColor: themeColors.border }]}>
            <Text style={[styles.settingLabel, { color: themeColors.textSecondary }]}>Study Start Time</Text>
            <TouchableOpacity
              style={[styles.timeInput, { backgroundColor: themeColors.card }]}
              onPress={() => setShowStartTimePicker(true)}
            >
              <Text style={[styles.timeInputText, { color: themeColors.textPrimary }]}>{formatTimeDisplay(workingHours.startHour)}</Text>
            </TouchableOpacity>
          </View>

          <View style={[styles.settingItem, { borderBottomColor: themeColors.border }]}>
            <Text style={[styles.settingLabel, { color: themeColors.textSecondary }]}>Study End Time</Text>
            <TouchableOpacity
              style={[styles.timeInput, { backgroundColor: themeColors.card }]}
              onPress={() => setShowEndTimePicker(true)}
            >
              <Text style={[styles.timeInputText, { color: themeColors.textPrimary }]}>{formatTimeDisplay(workingHours.endHour)}</Text>
            </TouchableOpacity>
          </View>

          <View style={[styles.settingItem, { borderBottomColor: themeColors.border }]}>
            <Text style={[styles.settingLabel, { color: themeColors.textSecondary }]}>Break Duration (minutes)</Text>
            <TextInput
              style={[styles.timeInput, styles.textInput, { backgroundColor: themeColors.card, color: themeColors.textPrimary }]}
              value={breakDuration}
              onChangeText={setBreakDuration}
              keyboardType="numeric"
              placeholder="30"
              placeholderTextColor={themeColors.textSecondary}
            />
          </View>

          <View style={[styles.settingItem, { borderBottomColor: themeColors.border }]}>
            <Text style={[styles.settingLabel, { color: themeColors.textSecondary }]}>Enable Notifications</Text>
            <Switch
              value={enableNotifications}
              onValueChange={setEnableNotifications}
              trackColor={{ false: '#767577', true: themeColors.primary }}
              thumbColor={enableNotifications ? '#fff' : '#f4f3f4'}
            />
          </View>
        </View>

        {/* Subject Colors */}
        <View style={[styles.section, { backgroundColor: themeColors.surface }]}>
          <View style={styles.sectionHeader}>
            <Palette size={20} color={themeColors.textPrimary} />
            <Text style={[styles.sectionTitle, { color: themeColors.textPrimary }]}>Subject Colors</Text>
          </View>

          {subjectColors.map((subject) => (
            <TouchableOpacity
              key={subject.id}
              style={[styles.subjectItem, { borderBottomColor: themeColors.border }]}
              onPress={() => {
                // TODO: Implement subject color edit
                Alert.alert('Coming Soon', 'Subject color editing will be available in the next update!');
              }}
            >
              <View style={[styles.subjectColorInfo, { borderBottomColor: themeColors.border }]}>
                <View style={[styles.colorDot, { backgroundColor: subject.color }]} />
                <Text style={[styles.subjectName, { color: themeColors.textPrimary }]}>{subject.name}</Text>
              </View>
              <ChevronRight size={20} color={themeColors.textSecondary} />
            </TouchableOpacity>
          ))}

          <TouchableOpacity
            style={[styles.addSubjectButton]}
            onPress={handleAddSubject}
            activeOpacity={0.7}
          >
            <Plus size={20} color={themeColors.primary} />
            <Text style={[styles.addSubjectText, { color: themeColors.primary }]}>Add Subject</Text>
          </TouchableOpacity>
        </View>

        {/* Integrations Section */}
        <View style={[styles.section, { backgroundColor: themeColors.surface }]}>
          <View style={styles.sectionHeader}>
            <Calendar size={20} color={themeColors.textSecondary} />
            <Text style={[styles.sectionTitle, { color: themeColors.textPrimary }]}>Integrations</Text>
          </View>
          
          <TouchableOpacity
            style={[styles.settingItem, { borderBottomColor: themeColors.border }]}
            onPress={() => setShowCalendarModal(true)}
            activeOpacity={0.7}
          >
            <View style={styles.settingItemContent}>
              <View style={styles.settingItemLeft}>
                <Calendar size={20} color={themeColors.primary} />
                <View style={styles.settingItemText}>
                  <Text style={[styles.settingLabel, { color: themeColors.textPrimary }]}>Calendar Integration</Text>
                  <Text style={[styles.settingDescription, { color: themeColors.textSecondary }]}>
                    Connect Google Calendar & Outlook
                  </Text>
                </View>
              </View>
              <ChevronRight size={20} color={themeColors.textSecondary} />
            </View>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.settingItem, { borderBottomColor: themeColors.border }]}
            onPress={() => setShowCanvasModal(true)}
            activeOpacity={0.7}
          >
            <View style={styles.settingItemContent}>
              <View style={styles.settingItemLeft}>
                <Calendar size={20} color={themeColors.primary} />
                <View style={styles.settingItemText}>
                  <Text style={[styles.settingLabel, { color: themeColors.textPrimary }]}>Canvas LMS</Text>
                  <Text style={[styles.settingDescription, { color: themeColors.textSecondary }]}>
                    Sync assignments and grades
                  </Text>
                </View>
              </View>
              <ChevronRight size={20} color={themeColors.textSecondary} />
            </View>
          </TouchableOpacity>
        </View>

        {/* Notifications Section */}
        <View style={[styles.section, { backgroundColor: themeColors.surface }]}>
          <View style={styles.sectionHeader}>
            <Bell size={20} color={themeColors.textSecondary} />
            <Text style={[styles.sectionTitle, { color: themeColors.textPrimary }]}>Notifications</Text>
          </View>
          
          <View style={[styles.toggleItem, { borderBottomColor: themeColors.border }]}>
            <Text style={[styles.toggleLabel, { color: themeColors.textSecondary }]}>Task Reminders</Text>
            <Switch
              trackColor={{ false: '#767577', true: themeColors.primary }}
              thumbColor={true ? '#fff' : '#f4f3f4'}
              ios_backgroundColor="#3e3e3e"
              value={true}
            />
          </View>
          
          <View style={[styles.toggleItem, { borderBottomColor: themeColors.border }]}>
            <Text style={[styles.toggleLabel, { color: themeColors.textSecondary }]}>AI Suggestions</Text>
            <Switch
              trackColor={{ false: '#767577', true: themeColors.primary }}
              thumbColor={true ? '#fff' : '#f4f3f4'}
              ios_backgroundColor="#3e3e3e"
              value={true}
            />
          </View>
        </View>

        {/* Subscription Section */}
        <View style={[styles.section, { backgroundColor: themeColors.surface }]}>
          <LinearGradient
            colors={['rgba(79, 140, 255, 0.15)', 'rgba(148, 77, 255, 0.15)']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[styles.subscriptionCard, { backgroundColor: themeColors.card }]}
          >
            <View style={styles.subscriptionHeader}>
              <View style={styles.subscriptionIconContainer}>
                <CreditCard size={16} color={themeColors.primary} />
              </View>
              <View style={styles.subscriptionBadge}>
                <Text style={[styles.subscriptionBadgeText, { color: themeColors.textPrimary }]}>PREMIUM</Text>
              </View>
            </View>
            
            <View style={styles.subscriptionContent}>
              <Text style={[styles.subscriptionTitle, { color: themeColors.textPrimary }]}>PulsePlan Premium</Text>
              <Text style={[styles.subscriptionDescription, { color: themeColors.textSecondary }]}>
                Premium themes, advanced AI features, and unlimited task organization
              </Text>
              
              <View style={styles.subscriptionPricing}>
                <Text style={[styles.subscriptionPrice, { color: themeColors.textPrimary }]}>$3.99</Text>
                <Text style={[styles.subscriptionPeriod, { color: themeColors.textSecondary }]}>/month</Text>
              </View>
              
              <View style={styles.subscriptionStatusContainer}>
                <View style={[styles.subscriptionStatusDot, { backgroundColor: themeColors.primary }]} />
                <Text style={[styles.subscriptionStatus, { color: themeColors.textPrimary }]}>Active Subscription</Text>
              </View>
            </View>
            
            <TouchableOpacity style={[styles.subscriptionButton, { backgroundColor: themeColors.card }]}>
              <Text style={[styles.subscriptionButtonText, { color: themeColors.textPrimary }]}>Manage Subscription</Text>
            </TouchableOpacity>
          </LinearGradient>
        </View>

        {/* Logout Button */}
        <TouchableOpacity 
          style={[styles.logoutButton, { backgroundColor: themeColors.surface }]} 
          onPress={() => {
            console.log('🔴 LOGOUT BUTTON PRESSED - This should show in console');
            handleLogout();
          }}
          activeOpacity={0.7}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <LogOut size={20} color={themeColors.error || '#FF6B6B'} />
          <Text style={[styles.logoutText, { color: themeColors.error || '#FF6B6B' }]}>Log Out</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Edit Profile Modal */}
      <Modal
        visible={showEditModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={[styles.modalContainer, { backgroundColor: themeColors.background }]}>
          <View style={[styles.modalHeader, { borderBottomColor: themeColors.border }]}>
            <TouchableOpacity onPress={() => setShowEditModal(false)}>
              <Text style={[styles.cancelButton, { color: themeColors.textSecondary }]}>Cancel</Text>
            </TouchableOpacity>
            <Text style={[styles.modalTitle, { color: themeColors.textPrimary }]}>Edit Profile</Text>
            <TouchableOpacity onPress={handleSaveProfile}>
              <Text style={[styles.modalSaveButton, { color: themeColors.primary }]}>Save</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, { color: themeColors.textPrimary }]}>Full Name</Text>
              <TextInput
                style={[styles.modalInput, { backgroundColor: themeColors.card, color: themeColors.textPrimary, borderColor: themeColors.border }]}
                value={editedName}
                onChangeText={setEditedName}
                placeholder="Enter your full name"
                placeholderTextColor={themeColors.textSecondary}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, { color: themeColors.textPrimary }]}>Email</Text>
              <TextInput
                style={[styles.modalInput, { backgroundColor: themeColors.card, color: themeColors.textPrimary, borderColor: themeColors.border }]}
                value={editedEmail}
                onChangeText={setEditedEmail}
                placeholder="Enter your email"
                placeholderTextColor={themeColors.textSecondary}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>

            <Text style={[styles.modalNote, { color: themeColors.textSecondary }]}>
              Note: Email changes may require verification and will take effect after confirmation.
            </Text>
          </View>
        </View>
      </Modal>

      {/* Time picker modals */}
      {showStartTimePicker && (
        <Modal
          visible={showStartTimePicker}
          animationType="slide"
          transparent={true}
          onRequestClose={() => setShowStartTimePicker(false)}
        >
          <TouchableOpacity 
            style={[styles.datePickerOverlay, { backgroundColor: 'rgba(0, 0, 0, 0.5)' }]}
            activeOpacity={1}
            onPress={() => setShowStartTimePicker(false)}
          >
            <View style={[styles.datePickerContainer, { justifyContent: 'flex-end' }]}>
              <View style={[styles.datePickerModal, { backgroundColor: themeColors.background }]}>
                <View style={[styles.datePickerHeader, { borderBottomColor: themeColors.border }]}>
                  <TouchableOpacity onPress={() => setShowStartTimePicker(false)}>
                    <Text style={[styles.datePickerCancel, { color: themeColors.textSecondary }]}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={[styles.datePickerTitle, { color: themeColors.textPrimary }]}>Study Start Time</Text>
                  <TouchableOpacity onPress={saveStartTime}>
                    <Text style={[styles.datePickerDone, { color: themeColors.primary }]}>Done</Text>
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={tempStartTime}
                  mode="time"
                  display="spinner"
                  onChange={handleStartTimeChange}
                  textColor={themeColors.textPrimary}
                />
              </View>
            </View>
          </TouchableOpacity>
        </Modal>
      )}

      {showEndTimePicker && (
        <Modal
          visible={showEndTimePicker}
          animationType="slide"
          transparent={true}
          onRequestClose={() => setShowEndTimePicker(false)}
        >
          <TouchableOpacity 
            style={[styles.datePickerOverlay, { backgroundColor: 'rgba(0, 0, 0, 0.5)' }]}
            activeOpacity={1}
            onPress={() => setShowEndTimePicker(false)}
          >
            <View style={[styles.datePickerContainer, { justifyContent: 'flex-end' }]}>
              <View style={[styles.datePickerModal, { backgroundColor: themeColors.background }]}>
                <View style={[styles.datePickerHeader, { borderBottomColor: themeColors.border }]}>
                  <TouchableOpacity onPress={() => setShowEndTimePicker(false)}>
                    <Text style={[styles.datePickerCancel, { color: themeColors.textSecondary }]}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={[styles.datePickerTitle, { color: themeColors.textPrimary }]}>Study End Time</Text>
                  <TouchableOpacity onPress={saveEndTime}>
                    <Text style={[styles.datePickerDone, { color: themeColors.primary }]}>Done</Text>
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={tempEndTime}
                  mode="time"
                  display="spinner"
                  onChange={handleEndTimeChange}
                  textColor={themeColors.textPrimary}
                />
              </View>
            </View>
          </TouchableOpacity>
        </Modal>
      )}

      {/* Calendar Integration Modal */}
      <CalendarIntegrationModal
        visible={showCalendarModal}
        onClose={() => setShowCalendarModal(false)}
      />

      {/* Canvas Integration Modal */}
      <CanvasModal
        visible={showCanvasModal}
        onClose={() => setShowCanvasModal(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
  },
  content: {
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    padding: 16,
    marginVertical: 16,
  },
  profileCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileInitial: {
    fontSize: 20,
    fontWeight: '600',
  },
  profileInfo: {
    marginLeft: 16,
    flex: 1,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
  },
  profileEmail: {
    fontSize: 14,
  },
  editButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  editButtonText: {
    fontSize: 14,
  },
  section: {
    marginBottom: 24,
    borderRadius: 16,
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  settingLabel: {
    fontSize: 14,
  },
  settingItemContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flex: 1,
  },
  settingItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingItemText: {
    marginLeft: 12,
    flex: 1,
  },
  settingDescription: {
    fontSize: 12,
    marginTop: 2,
  },
  timeInput: {
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    width: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeInputText: {
    fontSize: 14,
  },
  toggleItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  toggleLabel: {
    fontSize: 14,
  },
  subscriptionCard: {
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    overflow: 'hidden',
  },
  subscriptionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 16,
  },
  subscriptionIconContainer: {
    backgroundColor: 'rgba(79, 140, 255, 0.2)',
    borderRadius: 8,
    padding: 6,
  },
  subscriptionBadge: {
    backgroundColor: 'rgba(79, 140, 255, 0.2)',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: 'rgba(79, 140, 255, 0.3)',
  },
  subscriptionBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.primaryBlue,
    letterSpacing: 0.5,
  },
  subscriptionContent: {
    alignItems: 'center',
    marginBottom: 16,
  },
  subscriptionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  subscriptionDescription: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 12,
    paddingHorizontal: 8,
  },
  subscriptionPricing: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  subscriptionPrice: {
    fontSize: 18,
    fontWeight: '700',
  },
  subscriptionPeriod: {
    fontSize: 13,
    fontWeight: '500',
    marginLeft: 2,
  },
  subscriptionStatusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(52, 211, 153, 0.15)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  subscriptionStatusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#34D399',
    marginRight: 6,
  },
  subscriptionStatus: {
    fontSize: 12,
    fontWeight: '500',
  },
  subscriptionButton: {
    backgroundColor: 'rgba(79, 140, 255, 0.2)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(79, 140, 255, 0.3)',
  },
  subscriptionButtonText: {
    color: colors.primaryBlue,
    fontSize: 14,
    fontWeight: '600',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    marginTop: 8,
    marginHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FF6B6B',
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
  },
  logoutText: {
    fontSize: 16,
    marginLeft: 8,
  },
  subjectItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  subjectColorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  colorDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    marginRight: 12,
  },
  subjectName: {
    fontSize: 16,
  },
  addSubjectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    marginTop: 8,
  },
  addSubjectText: {
    fontSize: 16,
    marginLeft: 8,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  cancelButton: {
    fontSize: 16,
  },
  modalSaveButton: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalContent: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  modalInput: {
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
  },
  modalNote: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 16,
    lineHeight: 20,
  },
  datePickerOverlay: {
    flex: 1,
  },
  datePickerContainer: {
    flex: 1,
  },
  datePickerModal: {
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: 400,
  },
  datePickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  datePickerCancel: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  datePickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  datePickerDone: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primaryBlue,
  },
  textInput: {
    color: colors.textPrimary,
    textAlign: 'center',
  },
});