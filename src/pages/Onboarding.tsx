import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  Image, 
  TextInput, 
  ScrollView,
  Alert,
  Switch,
  Animated,
  Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../contexts/AuthContext';
import { useProfile } from '../contexts/ProfileContext';

const { width: screenWidth } = Dimensions.get('window');

interface OnboardingProps {
  onComplete: () => void;
}

interface UserPreferences {
  userType: 'student' | 'professional' | 'educator' | '';
  studyPreferences: {
    preferredStudyTimes: string[];
    sessionDuration: number;
    breakDuration: number;
  };
  integrations: {
    canvas: boolean;
    googleCalendar: boolean;
    outlook: boolean;
  };
  notifications: {
    deadlineReminders: boolean;
    studyReminders: boolean;
    weeklyReports: boolean;
  };
}

export const Onboarding = ({
  onComplete
}: OnboardingProps) => {
  const [step, setStep] = useState(0);
  const { completeOnboarding } = useAuth();
  const { updateProfile } = useProfile();
  
  // Animation values
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  
  // User data collection
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [school, setSchool] = useState('');
  const [preferences, setPreferences] = useState<UserPreferences>({
    userType: '',
    studyPreferences: {
      preferredStudyTimes: [],
      sessionDuration: 25,
      breakDuration: 5,
    },
    integrations: {
      canvas: false,
      googleCalendar: false,
      outlook: false,
    },
    notifications: {
      deadlineReminders: true,
      studyReminders: true,
      weeklyReports: false,
    },
  });

  const steps = [
    {
      id: 'welcome',
      title: 'Welcome to PulsePlan',
      description: 'Your AI-powered academic scheduling assistant that adapts to your learning style',
      component: 'welcome'
    },
    {
      id: 'profile',
      title: 'Tell us about yourself',
      description: 'Help us personalize your experience',
      component: 'profile'
    },
    {
      id: 'userType',
      title: 'What describes you best?',
      description: 'We\'ll customize PulsePlan based on your role',
      component: 'userType'
    },
    {
      id: 'studyPreferences',
      title: 'Study Preferences',
      description: 'When and how do you prefer to study?',
      component: 'studyPreferences'
    },
    {
      id: 'integrations',
      title: 'Connect Your Tools',
      description: 'Sync with your existing platforms for a seamless experience',
      component: 'integrations'
    },
    {
      id: 'notifications',
      title: 'Stay on Track',
      description: 'Choose how you\'d like to be reminded',
      component: 'notifications'
    },
    {
      id: 'complete',
      title: 'You\'re All Set!',
      description: 'PulsePlan is ready to help you achieve your goals',
      component: 'complete'
    }
  ];

  // Animation effect for step changes
  useEffect(() => {
    // Animate in when step changes
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();
  }, [step]);

  const animateStepChange = (callback: () => void) => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: -50,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 0.95,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      callback();
      // Reset animation values for next step
      slideAnim.setValue(50);
      fadeAnim.setValue(0);
      scaleAnim.setValue(1.05);
    });
  };

  const nextStep = async () => {
    if (step < steps.length - 1) {
      animateStepChange(() => setStep(step + 1));
    } else {
      // Complete onboarding
      try {
        // Save user profile
        await updateProfile({
          name,
          email,
          school,
          userType: preferences.userType,
          preferences: preferences
        });
        
        // Mark onboarding as completed
        await completeOnboarding();
        
        onComplete();
      } catch (error) {
        console.error('Error completing onboarding:', error);
        Alert.alert('Error', 'Failed to save your preferences. Please try again.');
      }
    }
  };

  const prevStep = () => {
    if (step > 0) {
      animateStepChange(() => setStep(step - 1));
    }
  };

  const canProceed = () => {
    switch (steps[step].component) {
      case 'profile':
        return name.trim() !== '' && email.trim() !== '';
      case 'userType':
        return preferences.userType !== '';
      default:
        return true;
    }
  };

  const renderStepContent = () => {
    const currentStep = steps[step];
    
    switch (currentStep.component) {
      case 'welcome':
        return (
          <View style={styles.stepContent}>
            <View style={styles.logoContainer}>
              <View style={styles.logoOuter}>
                <View style={styles.logoInner}>
                  <Text style={styles.logoText}>P</Text>
                </View>
              </View>
            </View>
            <Text style={styles.welcomeText}>
              Let's get you set up with a personalized learning experience that adapts to your schedule and goals.
            </Text>
          </View>
        );
        
      case 'profile':
        return (
          <View style={styles.stepContent}>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Full Name</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your full name"
                value={name}
                onChangeText={setName}
                placeholderTextColor="#9CA3AF"
              />
            </View>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Email</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your email"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                placeholderTextColor="#9CA3AF"
              />
            </View>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>School/Organization (Optional)</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your school or organization"
                value={school}
                onChangeText={setSchool}
                placeholderTextColor="#9CA3AF"
              />
            </View>
          </View>
        );
        
      case 'userType':
        return (
          <View style={styles.stepContent}>
            <View style={styles.optionsContainer}>
              {[
                { id: 'student', title: 'Student', description: 'High school, college, or university student', icon: 'school-outline' },
                { id: 'professional', title: 'Professional', description: 'Working professional seeking skill development', icon: 'briefcase-outline' },
                { id: 'educator', title: 'Educator', description: 'Teacher, professor, or educational professional', icon: 'library-outline' }
              ].map((option) => (
                <TouchableOpacity
                  key={option.id}
                  style={[
                    styles.optionCard,
                    preferences.userType === option.id && styles.optionCardSelected
                  ]}
                  onPress={() => setPreferences(prev => ({ ...prev, userType: option.id as any }))}
                >
                  <Ionicons 
                    name={option.icon as any} 
                    size={32} 
                    color={preferences.userType === option.id ? '#00AEEF' : '#6B7280'} 
                  />
                  <Text style={[
                    styles.optionTitle,
                    preferences.userType === option.id && styles.optionTitleSelected
                  ]}>
                    {option.title}
                  </Text>
                  <Text style={styles.optionDescription}>{option.description}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        );
        
      case 'studyPreferences':
        return (
          <View style={styles.stepContent}>
            <View style={styles.preferenceSection}>
              <Text style={styles.sectionTitle}>Preferred Study Session Length</Text>
              <View style={styles.sliderContainer}>
                {[15, 25, 45, 60].map((duration) => (
                  <TouchableOpacity
                    key={duration}
                    style={[
                      styles.durationOption,
                      preferences.studyPreferences.sessionDuration === duration && styles.durationOptionSelected
                    ]}
                    onPress={() => setPreferences(prev => ({
                      ...prev,
                      studyPreferences: { ...prev.studyPreferences, sessionDuration: duration }
                    }))}
                  >
                    <Text style={[
                      styles.durationText,
                      preferences.studyPreferences.sessionDuration === duration && styles.durationTextSelected
                    ]}>
                      {duration}m
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            
            <View style={styles.preferenceSection}>
              <Text style={styles.sectionTitle}>Preferred Study Times</Text>
              <View style={styles.timeOptionsContainer}>
                {[
                  { id: 'morning', label: 'Morning (6-12 PM)', icon: 'sunny-outline' },
                  { id: 'afternoon', label: 'Afternoon (12-6 PM)', icon: 'partly-sunny-outline' },
                  { id: 'evening', label: 'Evening (6-10 PM)', icon: 'moon-outline' },
                  { id: 'night', label: 'Night (10 PM-2 AM)', icon: 'moon' }
                ].map((timeOption) => (
                  <TouchableOpacity
                    key={timeOption.id}
                    style={[
                      styles.timeOption,
                      preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) && styles.timeOptionSelected
                    ]}
                    onPress={() => {
                      const currentTimes = preferences.studyPreferences.preferredStudyTimes;
                      const newTimes = currentTimes.includes(timeOption.id)
                        ? currentTimes.filter(t => t !== timeOption.id)
                        : [...currentTimes, timeOption.id];
                      setPreferences(prev => ({
                        ...prev,
                        studyPreferences: { ...prev.studyPreferences, preferredStudyTimes: newTimes }
                      }));
                    }}
                  >
                    <Ionicons 
                      name={timeOption.icon as any} 
                      size={20} 
                      color={preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) ? '#00AEEF' : '#6B7280'} 
                    />
                    <Text style={[
                      styles.timeOptionText,
                      preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) && styles.timeOptionTextSelected
                    ]}>
                      {timeOption.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        );
        
      case 'integrations':
        return (
          <View style={styles.stepContent}>
            <Text style={styles.integrationNote}>
              Connect your existing tools to automatically sync assignments and calendar events.
            </Text>
            
            <View style={styles.integrationsList}>
              {[
                { 
                  key: 'canvas', 
                  title: 'Canvas LMS', 
                  description: 'Sync assignments and due dates',
                  icon: 'school-outline',
                  available: true
                },
                { 
                  key: 'googleCalendar', 
                  title: 'Google Calendar', 
                  description: 'Sync your calendar events',
                  icon: 'calendar-outline',
                  available: true
                },
                { 
                  key: 'outlook', 
                  title: 'Microsoft Outlook', 
                  description: 'Sync calendar and tasks',
                  icon: 'mail-outline',
                  available: true
                }
              ].map((integration) => (
                <View key={integration.key} style={styles.integrationItem}>
                  <View style={styles.integrationInfo}>
                    <Ionicons name={integration.icon as any} size={24} color="#00AEEF" />
                    <View style={styles.integrationText}>
                      <Text style={styles.integrationTitle}>{integration.title}</Text>
                      <Text style={styles.integrationDescription}>{integration.description}</Text>
                    </View>
                  </View>
                  <Switch
                    value={preferences.integrations[integration.key as keyof typeof preferences.integrations]}
                    onValueChange={(value) => setPreferences(prev => ({
                      ...prev,
                      integrations: { ...prev.integrations, [integration.key]: value }
                    }))}
                    trackColor={{ false: '#E5E7EB', true: '#00AEEF' }}
                    thumbColor="#FFFFFF"
                  />
                </View>
              ))}
            </View>
            
            <Text style={styles.integrationFooter}>
              You can always connect these later in Settings.
            </Text>
          </View>
        );
        
      case 'notifications':
        return (
          <View style={styles.stepContent}>
            <Text style={styles.notificationNote}>
              Choose how you'd like PulsePlan to keep you on track.
            </Text>
            
            <View style={styles.notificationsList}>
              {[
                { 
                  key: 'deadlineReminders', 
                  title: 'Deadline Reminders', 
                  description: 'Get notified about upcoming due dates',
                  icon: 'alarm-outline'
                },
                { 
                  key: 'studyReminders', 
                  title: 'Study Session Reminders', 
                  description: 'Reminders for your scheduled study time',
                  icon: 'time-outline'
                },
                { 
                  key: 'weeklyReports', 
                  title: 'Weekly Progress Reports', 
                  description: 'Summary of your weekly achievements',
                  icon: 'stats-chart-outline'
                }
              ].map((notification) => (
                <View key={notification.key} style={styles.notificationItem}>
                  <View style={styles.notificationInfo}>
                    <Ionicons name={notification.icon as any} size={24} color="#00AEEF" />
                    <View style={styles.notificationText}>
                      <Text style={styles.notificationTitle}>{notification.title}</Text>
                      <Text style={styles.notificationDescription}>{notification.description}</Text>
                    </View>
                  </View>
                  <Switch
                    value={preferences.notifications[notification.key as keyof typeof preferences.notifications]}
                    onValueChange={(value) => setPreferences(prev => ({
                      ...prev,
                      notifications: { ...prev.notifications, [notification.key]: value }
                    }))}
                    trackColor={{ false: '#E5E7EB', true: '#00AEEF' }}
                    thumbColor="#FFFFFF"
                  />
                </View>
              ))}
            </View>
          </View>
        );
        
      case 'complete':
        return (
          <View style={styles.stepContent}>
            <View style={styles.completionContainer}>
              <View style={styles.checkmarkContainer}>
                <Ionicons name="checkmark-circle" size={80} color="#10B981" />
              </View>
              <Text style={styles.completionText}>
                Perfect! PulsePlan is now customized for your learning style and preferences.
              </Text>
              <Text style={styles.completionSubtext}>
                You can always adjust these settings later in your profile.
              </Text>
            </View>
          </View>
        );
        
      default:
        return null;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View 
          style={[
            styles.content, 
            {
              opacity: fadeAnim,
              transform: [
                { translateX: slideAnim },
                { scale: scaleAnim }
              ]
            }
          ]}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>{steps[step].title}</Text>
            <Text style={styles.description}>{steps[step].description}</Text>
          </View>
          
          {/* Progress indicator */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View 
                style={[
                  styles.progressFill, 
                  { width: `${((step + 1) / steps.length) * 100}%` }
                ]} 
              />
            </View>
            <Text style={styles.progressText}>{step + 1} of {steps.length}</Text>
          </View>
          
          {/* Step content */}
          {renderStepContent()}
          
          {/* Navigation buttons */}
          <View style={styles.navigationContainer}>
            {step > 0 && (
              <TouchableOpacity style={styles.backButton} onPress={prevStep}>
                <Ionicons name="arrow-back" size={20} color="#6B7280" />
                <Text style={styles.backButtonText}>Back</Text>
              </TouchableOpacity>
            )}
            
            <TouchableOpacity 
              style={[
                styles.nextButton, 
                !canProceed() && styles.nextButtonDisabled,
                step === 0 && styles.nextButtonFull
              ]} 
              onPress={nextStep}
              disabled={!canProceed()}
            >
              <Text style={styles.nextButtonText}>
                {step === steps.length - 1 ? 'Get Started' : 'Continue'}
              </Text>
              <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
            </TouchableOpacity>
          </View>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D1B2A',
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  content: {
    flex: 1,
    minHeight: '100%',
  },
  header: {
    marginBottom: 32,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 24,
  },
  progressContainer: {
    marginBottom: 40,
    alignItems: 'center',
  },
  progressBar: {
    width: '100%',
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
    backgroundColor: '#00AEEF',
  },
  progressText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 14,
    fontWeight: '500',
  },
  stepContent: {
    flex: 1,
    justifyContent: 'center',
    minHeight: 400,
  },
  logoContainer: {
    marginBottom: 32,
    alignItems: 'center',
  },
  logoOuter: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0D1B2A',
  },
  welcomeText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: 20,
  },
  inputContainer: {
    marginBottom: 20,
    width: '100%',
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  input: {
    width: '100%',
    height: 50,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    color: '#FFFFFF',
    fontSize: 16,
  },
  optionsContainer: {
    width: '100%',
    gap: 16,
  },
  optionCard: {
    padding: 20,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    minHeight: 120,
  },
  optionCardSelected: {
    backgroundColor: 'rgba(0, 174, 239, 0.2)',
    borderColor: '#00AEEF',
  },
  optionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 12,
    marginBottom: 8,
    textAlign: 'center',
  },
  optionTitleSelected: {
    color: '#00AEEF',
  },
  optionDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 20,
  },
  preferenceSection: {
    marginBottom: 32,
    width: '100%',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
    textAlign: 'center',
  },
  sliderContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  durationOption: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
  },
  durationOptionSelected: {
    backgroundColor: '#00AEEF',
    borderColor: '#00AEEF',
  },
  durationText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  durationTextSelected: {
    color: '#FFFFFF',
  },
  timeOptionsContainer: {
    gap: 12,
  },
  timeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  timeOptionSelected: {
    backgroundColor: 'rgba(0, 174, 239, 0.2)',
    borderColor: '#00AEEF',
  },
  timeOptionText: {
    fontSize: 16,
    color: '#FFFFFF',
    marginLeft: 12,
    fontWeight: '500',
  },
  timeOptionTextSelected: {
    color: '#00AEEF',
  },
  integrationNote: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  integrationsList: {
    marginBottom: 24,
    gap: 16,
  },
  integrationItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  integrationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  integrationText: {
    marginLeft: 16,
    flex: 1,
  },
  integrationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  integrationDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 18,
  },
  integrationFooter: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  notificationNote: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  notificationsList: {
    gap: 16,
  },
  notificationItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  notificationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  notificationText: {
    marginLeft: 16,
    flex: 1,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  notificationDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 18,
  },
  completionContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  checkmarkContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
  },
  completionText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 26,
    paddingHorizontal: 20,
  },
  completionSubtext: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 20,
  },
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 40,
    paddingTop: 20,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.8)',
    marginLeft: 8,
  },
  nextButton: {
    backgroundColor: '#00AEEF',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: '#00AEEF',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  nextButtonDisabled: {
    backgroundColor: 'rgba(0, 174, 239, 0.5)',
    shadowOpacity: 0,
    elevation: 0,
  },
  nextButtonFull: {
    flex: 1,
    marginLeft: 0,
  },
  nextButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});