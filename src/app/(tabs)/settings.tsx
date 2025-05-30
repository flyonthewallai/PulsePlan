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

const themes = [
  { id: 'midnight', name: 'Midnight', primary: '#4F8CFF', accent: '#8E6FFF' },
  { id: 'ocean', name: 'Ocean', primary: '#00C2FF', accent: '#0066FF' },
  { id: 'forest', name: 'Forest', primary: '#4CD964', accent: '#0A84FF' },
  { id: 'sunset', name: 'Sunset', primary: '#FF9500', accent: '#FF2D55' },
];

interface SubjectColor {
  id: string;
  name: string;
  color: string;
}

export default function SettingsScreen() {
  const router = useRouter();
  const { user, refreshAuth } = useAuth();
  const { workingHours, updateWorkingHours } = useSettings();
  const [selectedTheme, setSelectedTheme] = useState('midnight');
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
    Alert.alert(
      'Confirm Logout',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Log Out', 
          style: 'destructive',
          onPress: async () => {
            try {
              console.log('🔓 Starting logout process...');
              await signOut();
              console.log('🔓 Sign out completed, refreshing auth...');
              await refreshAuth();
              console.log('🔓 Auth refreshed - navigation will be handled by AuthContext');
            } catch (error) {
              console.error('Error logging out:', error);
              Alert.alert('Logout Error', 'An error occurred while logging out.');
            }
          }
        }
      ]
    );
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
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>

      <ScrollView 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        {/* Profile Section */}
        <View style={styles.profileCard}>
          <View style={styles.profileCircle}>
            <Text style={styles.profileInitial}>
              {user?.user_metadata?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
            </Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>
              {user?.user_metadata?.full_name || 'User'}
            </Text>
            <Text style={styles.profileEmail}>
              {user?.email || 'user@example.com'}
            </Text>
          </View>
          <TouchableOpacity style={styles.editButton} onPress={handleEditProfile}>
            <Text style={styles.editButtonText}>Edit</Text>
          </TouchableOpacity>
        </View>

        {/* Theme Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Edit size={20} color={colors.textSecondary} />
            <Text style={styles.sectionTitle}>Theme</Text>
          </View>
          
          <ThemeSelector 
            themes={themes} 
            selectedTheme={selectedTheme}
            onSelectTheme={setSelectedTheme}
          />
        </View>

        {/* Study Time Preferences */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Clock size={20} color={colors.textPrimary} />
            <Text style={styles.sectionTitle}>Study Time Preferences</Text>
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Study Start Time</Text>
            <TouchableOpacity
              style={styles.timeInput}
              onPress={() => setShowStartTimePicker(true)}
            >
              <Text style={styles.timeInputText}>{formatTimeDisplay(workingHours.startHour)}</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Study End Time</Text>
            <TouchableOpacity
              style={styles.timeInput}
              onPress={() => setShowEndTimePicker(true)}
            >
              <Text style={styles.timeInputText}>{formatTimeDisplay(workingHours.endHour)}</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Break Duration (minutes)</Text>
            <TextInput
              style={[styles.timeInput, styles.textInput]}
              value={breakDuration}
              onChangeText={setBreakDuration}
              keyboardType="numeric"
              placeholder="30"
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Enable Notifications</Text>
            <Switch
              value={enableNotifications}
              onValueChange={setEnableNotifications}
              trackColor={{ false: '#767577', true: colors.primaryBlue }}
              thumbColor={enableNotifications ? '#fff' : '#f4f3f4'}
            />
          </View>
        </View>

        {/* Subject Colors */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Palette size={20} color={colors.textPrimary} />
            <Text style={styles.sectionTitle}>Subject Colors</Text>
          </View>

          {subjectColors.map((subject) => (
            <TouchableOpacity
              key={subject.id}
              style={styles.subjectItem}
              onPress={() => {
                // TODO: Implement subject color edit
                Alert.alert('Coming Soon', 'Subject color editing will be available in the next update!');
              }}
            >
              <View style={styles.subjectColorInfo}>
                <View style={[styles.colorDot, { backgroundColor: subject.color }]} />
                <Text style={styles.subjectName}>{subject.name}</Text>
              </View>
              <ChevronRight size={20} color={colors.textSecondary} />
            </TouchableOpacity>
          ))}

          <TouchableOpacity
            style={styles.addSubjectButton}
            onPress={handleAddSubject}
          >
            <Plus size={20} color={colors.primaryBlue} />
            <Text style={styles.addSubjectText}>Add Subject</Text>
          </TouchableOpacity>
        </View>

        {/* Integrations Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Calendar size={20} color={colors.textSecondary} />
            <Text style={styles.sectionTitle}>Integrations</Text>
          </View>
          
          <View style={styles.toggleItem}>
            <Text style={styles.toggleLabel}>Canvas</Text>
            <Switch
              trackColor={{ false: '#767577', true: colors.primaryBlue }}
              thumbColor={integrations.canvas ? '#fff' : '#f4f3f4'}
              ios_backgroundColor="#3e3e3e"
              onValueChange={() => toggleIntegration('canvas')}
              value={integrations.canvas}
            />
          </View>
          
          <View style={styles.toggleItem}>
            <Text style={styles.toggleLabel}>Google Calendar</Text>
            <Switch
              trackColor={{ false: '#767577', true: colors.primaryBlue }}
              thumbColor={integrations.googleCalendar ? '#fff' : '#f4f3f4'}
              ios_backgroundColor="#3e3e3e"
              onValueChange={() => toggleIntegration('googleCalendar')}
              value={integrations.googleCalendar}
            />
          </View>
        </View>

        {/* Notifications Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Bell size={20} color={colors.textSecondary} />
            <Text style={styles.sectionTitle}>Notifications</Text>
          </View>
          
          <View style={styles.toggleItem}>
            <Text style={styles.toggleLabel}>Task Reminders</Text>
            <Switch
              trackColor={{ false: '#767577', true: colors.primaryBlue }}
              thumbColor={true ? '#fff' : '#f4f3f4'}
              ios_backgroundColor="#3e3e3e"
              value={true}
            />
          </View>
          
          <View style={styles.toggleItem}>
            <Text style={styles.toggleLabel}>AI Suggestions</Text>
            <Switch
              trackColor={{ false: '#767577', true: colors.primaryBlue }}
              thumbColor={true ? '#fff' : '#f4f3f4'}
              ios_backgroundColor="#3e3e3e"
              value={true}
            />
          </View>
        </View>

        {/* Subscription Section */}
        <LinearGradient
          colors={[colors.primaryBlue, colors.accentPurple]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.subscriptionCard}
        >
          <CreditCard size={24} color="#fff" />
          <Text style={styles.subscriptionTitle}>PulsePlan Premium</Text>
          <Text style={styles.subscriptionStatus}>Active • $3.99/month</Text>
          <TouchableOpacity style={styles.subscriptionButton}>
            <Text style={styles.subscriptionButtonText}>Manage Subscription</Text>
          </TouchableOpacity>
        </LinearGradient>

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <LogOut size={20} color={colors.textSecondary} />
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Edit Profile Modal */}
      <Modal
        visible={showEditModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowEditModal(false)}>
              <Text style={styles.cancelButton}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Edit Profile</Text>
            <TouchableOpacity onPress={handleSaveProfile}>
              <Text style={styles.modalSaveButton}>Save</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Full Name</Text>
              <TextInput
                style={styles.modalInput}
                value={editedName}
                onChangeText={setEditedName}
                placeholder="Enter your full name"
                placeholderTextColor={colors.textSecondary}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Email</Text>
              <TextInput
                style={styles.modalInput}
                value={editedEmail}
                onChangeText={setEditedEmail}
                placeholder="Enter your email"
                placeholderTextColor={colors.textSecondary}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>

            <Text style={styles.modalNote}>
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
            style={styles.datePickerOverlay}
            activeOpacity={1}
            onPress={() => setShowStartTimePicker(false)}
          >
            <View style={styles.datePickerContainer}>
              <View style={styles.datePickerModal}>
                <View style={styles.datePickerHeader}>
                  <TouchableOpacity onPress={() => setShowStartTimePicker(false)}>
                    <Text style={styles.datePickerCancel}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={styles.datePickerTitle}>Study Start Time</Text>
                  <TouchableOpacity onPress={saveStartTime}>
                    <Text style={styles.datePickerDone}>Done</Text>
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={tempStartTime}
                  mode="time"
                  display="spinner"
                  onChange={handleStartTimeChange}
                  textColor={colors.textPrimary}
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
            style={styles.datePickerOverlay}
            activeOpacity={1}
            onPress={() => setShowEndTimePicker(false)}
          >
            <View style={styles.datePickerContainer}>
              <View style={styles.datePickerModal}>
                <View style={styles.datePickerHeader}>
                  <TouchableOpacity onPress={() => setShowEndTimePicker(false)}>
                    <Text style={styles.datePickerCancel}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={styles.datePickerTitle}>Study End Time</Text>
                  <TouchableOpacity onPress={saveEndTime}>
                    <Text style={styles.datePickerDone}>Done</Text>
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={tempEndTime}
                  mode="time"
                  display="spinner"
                  onChange={handleEndTimeChange}
                  textColor={colors.textPrimary}
                />
              </View>
            </View>
          </TouchableOpacity>
        </Modal>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  content: {
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    marginVertical: 16,
  },
  profileCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: colors.primaryBlue,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileInitial: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  profileInfo: {
    marginLeft: 16,
    flex: 1,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  profileEmail: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  editButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  editButtonText: {
    fontSize: 14,
    color: colors.textPrimary,
  },
  section: {
    marginBottom: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
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
    color: colors.textPrimary,
    marginLeft: 8,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  settingLabel: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  timeInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    width: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeInputText: {
    fontSize: 14,
    color: colors.textPrimary,
  },
  toggleItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  toggleLabel: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  subscriptionCard: {
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 24,
  },
  subscriptionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginTop: 8,
  },
  subscriptionStatus: {
    fontSize: 14,
    color: colors.textPrimary,
    opacity: 0.8,
    marginTop: 4,
    marginBottom: 16,
  },
  subscriptionButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  subscriptionButtonText: {
    color: colors.textPrimary,
    fontSize: 14,
    fontWeight: '500',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    marginTop: 8,
  },
  logoutText: {
    fontSize: 16,
    color: colors.textSecondary,
    marginLeft: 8,
  },
  subjectItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
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
    color: colors.textPrimary,
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
    color: colors.primaryBlue,
    marginLeft: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
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
    color: colors.textPrimary,
  },
  cancelButton: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  modalSaveButton: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primaryBlue,
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
    color: colors.textPrimary,
    marginBottom: 8,
  },
  modalInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.textPrimary,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  modalNote: {
    fontSize: 14,
    color: colors.textSecondary,
    fontStyle: 'italic',
    marginTop: 16,
    lineHeight: 20,
  },
  datePickerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  datePickerContainer: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  datePickerModal: {
    backgroundColor: colors.backgroundDark,
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
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
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