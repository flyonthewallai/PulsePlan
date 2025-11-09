import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity,
  StatusBar,
  Image,
  ScrollView,
  TextInput,
  Alert,
  Animated,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { colors } from '@/constants/theme';
import { GlowingOrb } from '@/components/GlowingOrb';
import { supabase } from '@/lib/supabase';

// University suggestions - expandable for future additions
const UNIVERSITY_SUGGESTIONS = [
  'University of Colorado Boulder',
  'University of Colorado Denver',
  'University of Colorado Colorado Springs',
  'University of California Berkeley',
  'University of California Los Angeles',
  'University of California San Diego',
  'University of California Santa Barbara',
  'University of Southern California',
  'University of Texas Austin',
  'University of Texas Dallas',
  'University of Michigan',
  'University of Washington',
  'University of Florida',
  'University of Georgia',
  'University of Illinois',
  'University of Wisconsin Madison',
  'University of North Carolina Chapel Hill',
  'University of Virginia',
  'University of Pennsylvania',
  'University of Miami',
];

interface UserPreferences {
  userType: 'student' | 'professional' | 'educator' | '';
  studyPreferences: {
    preferredStudyTimes: string[];
    sessionDuration: number;
    breakDuration: number;
  };
  workPreferences: {
    preferredWorkTimes: string[];
    focusSessionDuration: number;
    meetingPreference: string;
  };
  integrations: {
    canvas: boolean;
    gmail: boolean;
    appleCalendar: boolean;
    outlook: boolean;
  };
  notifications: {
    taskReminders: boolean;
    missedTaskSummary: boolean;
    emailDelivery: boolean;
    inAppDelivery: boolean;
    pushDelivery: boolean;
  };
}

export default function OnboardingScreen() {
  const { markOnboardingComplete, user } = useAuth();
  const { currentTheme } = useTheme();
  const [step, setStep] = useState(0);
  const [isLoadingStep, setIsLoadingStep] = useState(true);
  
  // Animation values
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  
  // ScrollView ref for resetting scroll position
  const scrollViewRef = useRef<ScrollView>(null);
  
  // User data collection
  const [school, setSchool] = useState('');
  const [graduationYear, setGraduationYear] = useState('');
  const [schoolSuggestions, setSchoolSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [preferences, setPreferences] = useState<UserPreferences>({
    userType: '',
    studyPreferences: {
      preferredStudyTimes: [],
      sessionDuration: 25,
      breakDuration: 5,
    },
    workPreferences: {
      preferredWorkTimes: [],
      focusSessionDuration: 45,
      meetingPreference: 'morning',
    },
    integrations: {
      canvas: false,
      gmail: false,
      appleCalendar: false,
      outlook: false,
    },
    notifications: {
      taskReminders: true,
      missedTaskSummary: true,
      emailDelivery: false,
      inAppDelivery: true,
      pushDelivery: false,
    },
  });

  const getSteps = () => {
    const baseSteps = [
    {
      id: 'welcome',
      title: 'Welcome to PulsePlan',
        description: 'The AI planner that adapts to you.',
      component: 'welcome'
    },
    {
      id: 'profile',
      title: 'Your Background',
      description: 'Tell us about your organization (optional)',
      component: 'profile'
    },
    {
      id: 'userType',
      title: 'What describes you best?',
        description: 'We\'ll personalize your experience',
      component: 'userType'
      }
    ];

    // Add preferences step based on user type
    if (preferences.userType === 'student') {
      baseSteps.push({
      id: 'studyPreferences',
      title: 'Study Preferences',
        description: 'Your ideal study setup',
      component: 'studyPreferences'
      });
    } else if (preferences.userType === 'professional' || preferences.userType === 'educator') {
      baseSteps.push({
        id: 'workPreferences',
        title: preferences.userType === 'professional' ? 'Work Preferences' : 'Teaching Preferences',
        description: preferences.userType === 'professional' ? 'Your ideal work environment' : 'Your teaching and planning style',
        component: 'workPreferences'
      });
    }

        // Add remaining steps
    baseSteps.push(
      {
        id: 'integrations',
        title: 'Connect Your Tools',
        description: 'Sync with your existing platforms for a seamless experience',
        component: 'integrations'
      },
      {
        id: 'premium',
        title: 'Unlock Your Full Potential',
        description: 'Get the most out of PulsePlan with Premium features',
        component: 'premium'
      },
      {
        id: 'complete',
        title: 'You\'re All Set!',
        description: 'PulsePlan is ready to help you achieve your goals',
        component: 'complete'
      }
    );

    return baseSteps;
  };

  const steps = getSteps();

  // Load saved onboarding step on mount
  useEffect(() => {
    const loadSavedStep = async () => {
      try {
        if (user?.id) {
          const { data, error } = await supabase
            .from('users')
            .select('onboarding_step, name, school, academic_year, user_type, study_preferences, work_preferences, integration_preferences, notification_preferences')
            .eq('id', user.id)
            .single();

          if (data && !error) {
            // Load saved step
            if (data.onboarding_step && data.onboarding_step > 0) {
              setStep(data.onboarding_step);
            }
            
            // Load saved user data
            if (data.school) setSchool(data.school);
            if (data.academic_year) setGraduationYear(data.academic_year);
            
            // Load saved preferences
            if (data.user_type || data.study_preferences || data.work_preferences || data.integration_preferences || data.notification_preferences) {
              setPreferences(prev => ({
                ...prev,
                userType: data.user_type || '',
                studyPreferences: data.study_preferences || prev.studyPreferences,
                workPreferences: data.work_preferences || prev.workPreferences,
                integrations: data.integration_preferences || prev.integrations,
                notifications: data.notification_preferences || prev.notifications,
              }));
            }
          }
        }
      } catch (error) {
        console.error('Error loading saved onboarding step:', error);
      } finally {
        setIsLoadingStep(false);
      }
    };

    loadSavedStep();
  }, [user?.id]);

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

  // Save current step and all onboarding data to database
  const saveStep = async (stepNumber: number) => {
    try {
      if (user?.id) {
        // Prepare the data to save
        const updateData: any = {
          onboarding_step: stepNumber,
        };

        // Add user profile data if available
        if (school.trim() !== '') {
          updateData.school = school;
        }
        if (graduationYear.trim() !== '') {
          updateData.academic_year = graduationYear;
        }

        // Add user type if selected
        if (preferences.userType !== '') {
          updateData.user_type = preferences.userType;
        }

        // Add preferences based on user type
        if (preferences.userType === 'student') {
          updateData.study_preferences = preferences.studyPreferences;
        } else if (preferences.userType === 'professional' || preferences.userType === 'educator') {
          updateData.work_preferences = preferences.workPreferences;
        }

        // Add integration preferences
        updateData.integration_preferences = preferences.integrations;

        // Add notification preferences
        updateData.notification_preferences = preferences.notifications;

        const { error } = await supabase
          .from('users')
          .update(updateData)
          .eq('id', user.id);

        if (error) {
          console.error('Error saving onboarding data:', error);
        }
      }
    } catch (error) {
      console.error('Error saving onboarding data:', error);
    }
  };

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
      // Reset scroll position to top
      scrollViewRef.current?.scrollTo({ y: 0, animated: false });
      // Reset animation values for next step
      slideAnim.setValue(50);
      fadeAnim.setValue(0);
      scaleAnim.setValue(1.05);
    });
  };

  const nextStep = async () => {
    if (step < steps.length - 1) {
      const newStep = step + 1;
      animateStepChange(() => {
        setStep(newStep);
        saveStep(newStep);
      });
    } else {
      // Complete onboarding
      try {
        // Save user preferences to AsyncStorage
        const onboardingData = {
          school,
          graduationYear,
          userType: preferences.userType,
          preferences: preferences,
          completedAt: new Date().toISOString()
        };
        
        await AsyncStorage.setItem('user_preferences', JSON.stringify(onboardingData));

        // Save user type and preferences to Supabase
        if (user?.id) {
          const { error } = await supabase
            .from('users')
            .update({
              school: school,
              academic_year: graduationYear,
              user_type: preferences.userType,
              study_preferences: preferences.userType === 'student' ? preferences.studyPreferences : null,
              work_preferences: (preferences.userType === 'professional' || preferences.userType === 'educator') ? preferences.workPreferences : null,
              integration_preferences: preferences.integrations,
              notification_preferences: preferences.notifications,
              onboarding_step: 0 // Reset step when onboarding is completed
            })
            .eq('id', user.id);

          if (error) {
            console.error('Error saving to database:', error);
            // Don't block onboarding completion for database errors
          }
        }
        
        // Mark onboarding as complete using AuthContext
        await markOnboardingComplete();
        
        console.log('🎉 Onboarding completed successfully!');
        
        // Navigation will be handled automatically by AuthContext
        // No need to manually navigate since AuthContext will detect completion
      } catch (error) {
        console.error('Error completing onboarding:', error);
        Alert.alert('Error', 'Failed to save your preferences. Please try again.');
      }
    }
  };

  const prevStep = () => {
    if (step > 0) {
      const newStep = step - 1;
      animateStepChange(() => {
        setStep(newStep);
        saveStep(newStep);
      });
    }
  };

  // Utility functions
  const isEducationalInstitution = (schoolName: string) => {
    const educationKeywords = [
      'university', 'college', 'school', 'academy', 'institute', 'institution',
      'high school', 'elementary', 'middle school', 'prep', 'preparatory',
      'campus', 'education', 'learning', 'study', 'academic'
    ];
    
    const lowerCaseName = schoolName.toLowerCase();
    return educationKeywords.some(keyword => lowerCaseName.includes(keyword));
  };

  const canProceed = () => {
    switch (steps[step].component) {
      case 'userType':
        return preferences.userType !== '';
      default:
        return true;
    }
  };

  // Handler functions for user input
  const handleSchoolChange = (text: string) => {
    setSchool(text);
    
    if (text.length >= 3) {
      const filtered = UNIVERSITY_SUGGESTIONS.filter(university =>
        university.toLowerCase().includes(text.toLowerCase())
      ).slice(0, 5);
      
      setSchoolSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setShowSuggestions(false);
      setSchoolSuggestions([]);
    }
  };

  const selectSuggestion = (suggestion: string) => {
    setSchool(suggestion);
    setShowSuggestions(false);
    setSchoolSuggestions([]);
  };

  // Preference handlers with auto-save
  const selectUserType = (userType: string) => {
    setPreferences(prev => ({ ...prev, userType: userType as any }));
    setTimeout(() => saveStep(step), 100);
  };

  const toggleStudyTime = (timeId: string) => {
    setPreferences(prev => ({
      ...prev,
      studyPreferences: {
        ...prev.studyPreferences,
        preferredStudyTimes: prev.studyPreferences.preferredStudyTimes.includes(timeId)
          ? prev.studyPreferences.preferredStudyTimes.filter(t => t !== timeId)
          : [...prev.studyPreferences.preferredStudyTimes, timeId]
      }
    }));
    setTimeout(() => saveStep(step), 100);
  };

  const selectStudyDuration = (duration: number) => {
    setPreferences(prev => ({
      ...prev,
      studyPreferences: { ...prev.studyPreferences, sessionDuration: duration }
    }));
    setTimeout(() => saveStep(step), 100);
  };

  const toggleWorkTime = (timeId: string) => {
    setPreferences(prev => ({
      ...prev,
      workPreferences: {
        ...prev.workPreferences,
        preferredWorkTimes: prev.workPreferences.preferredWorkTimes.includes(timeId)
          ? prev.workPreferences.preferredWorkTimes.filter(t => t !== timeId)
          : [...prev.workPreferences.preferredWorkTimes, timeId]
      }
    }));
    setTimeout(() => saveStep(step), 100);
  };

  const selectWorkDuration = (duration: number) => {
    setPreferences(prev => ({
      ...prev,
      workPreferences: { ...prev.workPreferences, focusSessionDuration: duration }
    }));
    setTimeout(() => saveStep(step), 100);
  };

  const selectMeetingPreference = (preference: string) => {
    setPreferences(prev => ({
      ...prev,
      workPreferences: { ...prev.workPreferences, meetingPreference: preference }
    }));
    setTimeout(() => saveStep(step), 100);
  };

  const toggleIntegration = (integrationKey: string) => {
    setPreferences(prev => ({
      ...prev,
      integrations: {
        ...prev.integrations,
        [integrationKey]: !prev.integrations[integrationKey as keyof typeof prev.integrations]
      }
    }));
    setTimeout(() => saveStep(step), 100);
  };

  const getIntegrationsForUserType = () => {
    const baseIntegrations = [
      { 
        key: 'appleCalendar', 
        title: 'Apple Calendar', 
        description: 'Sync your calendar events',
        icon: 'calendar-outline',
        iconSource: require('@/assets/images/applecalendar.png')
      },
      { 
        key: 'outlook', 
        title: 'Microsoft Outlook', 
        description: 'Sync calendar and tasks',
        icon: 'mail-outline',
        iconSource: require('@/assets/images/applecalendar.png')
      }
    ];

    // Add user-type specific integrations
    if (preferences.userType === 'student' || preferences.userType === 'educator') {
      baseIntegrations.unshift({
        key: 'canvas', 
        title: 'Canvas LMS', 
        description: preferences.userType === 'student' ? 'Sync assignments and due dates' : 'Manage course content and assignments',
        icon: 'school-outline',
        iconSource: require('@/assets/images/canvas.png')
      });
    } else if (preferences.userType === 'professional') {
      baseIntegrations.unshift({
        key: 'gmail', 
        title: 'Gmail', 
        description: 'Sync emails and manage communication',
        icon: 'mail-outline',
        iconSource: require('@/assets/images/gmail.png')
      });
    }

    return baseIntegrations;
  };

  const renderStepContent = () => {
    const currentStep = steps[step];
    
    switch (currentStep.component) {
      case 'welcome':
        return (
          <View style={styles.welcomeStepContent}>
            <View style={styles.welcomeOrbContainer}>
              <GlowingOrb size="lg" color="blue" glowIntensity={0.8} glowOpacity={1.2} />
            </View>
            <Text style={styles.welcomeText}>
            Just answer a few quick questions — we'll handle the rest.
            </Text>
          </View>
        );
        
      case 'profile':
        return (
          <View style={styles.stepContent}>
            <View style={styles.formContainer}>
              <View style={school.trim() !== '' && isEducationalInstitution(school) ? styles.inputContainer : styles.inputContainerLast}>
                <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>School/Organization (Optional)</Text>
                <View style={styles.autocompleteContainer}>
                  <TextInput
                    style={[
                      styles.input,
                      {
                        backgroundColor: currentTheme.colors.surface,
                        borderColor: currentTheme.colors.border,
                        color: currentTheme.colors.textPrimary
                      }
                    ]}
                    placeholder="Enter your school or organization"
                    value={school}
                    onChangeText={handleSchoolChange}
                    placeholderTextColor={currentTheme.colors.textSecondary}
                    onFocus={() => {
                      if (school.length >= 3 && schoolSuggestions.length > 0) {
                        setShowSuggestions(true);
                      }
                    }}
                  />
                  {showSuggestions && schoolSuggestions.length > 0 && (
                    <View style={[styles.suggestionsContainer, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
                      <ScrollView 
                        style={styles.suggestionsScrollView}
                        nestedScrollEnabled={true}
                        keyboardShouldPersistTaps="handled"
                        showsVerticalScrollIndicator={false}
                      >
                        {schoolSuggestions.map((suggestion, index) => (
                          <TouchableOpacity
                            key={index}
                            style={[
                              styles.suggestionItem,
                              index < schoolSuggestions.length - 1 && { borderBottomColor: currentTheme.colors.border, borderBottomWidth: 1 }
                            ]}
                            onPress={() => selectSuggestion(suggestion)}
                          >
                            <Text style={[styles.suggestionText, { color: currentTheme.colors.textPrimary }]}>
                              {suggestion}
                            </Text>
                          </TouchableOpacity>
                        ))}
                      </ScrollView>
                    </View>
                  )}
                </View>
              </View>
              {school.trim() !== '' && isEducationalInstitution(school) && (
                <View style={styles.inputContainerLast}>
                  <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>Graduation Year</Text>
                  <TextInput
                    style={[
                      styles.input,
                      {
                        backgroundColor: currentTheme.colors.surface,
                        borderColor: currentTheme.colors.border,
                        color: currentTheme.colors.textPrimary
                      }
                    ]}
                    placeholder="Enter your expected graduation year"
                    value={graduationYear}
                    onChangeText={setGraduationYear}
                    placeholderTextColor={currentTheme.colors.textSecondary}
                    keyboardType="numeric"
                    maxLength={4}
                  />
                </View>
              )}
            </View>
          </View>
        );
        
      case 'userType':
        return (
          <View style={styles.stepContent}>
            <View style={styles.optionsContainer}>
              {[
                { id: 'student', title: 'Student', description: 'High school, college, or university student', icon: 'school-outline' },
                { id: 'professional', title: 'Professional', description: 'Working professional or career-focused', icon: 'briefcase-outline' },
                { id: 'educator', title: 'Educator', description: 'Teacher, professor, or educational professional', icon: 'library-outline' }
              ].map((option) => (
                <TouchableOpacity
                  key={option.id}
                  style={[
                    styles.optionCard,
                    {
                      backgroundColor: preferences.userType === option.id ? currentTheme.colors.primary : currentTheme.colors.surface,
                      borderColor: preferences.userType === option.id ? currentTheme.colors.primary : currentTheme.colors.border
                    }
                  ]}
                  onPress={() => selectUserType(option.id)}
                >
                  <Ionicons 
                    name={option.icon as any} 
                    size={32} 
                    color={preferences.userType === option.id ? '#FFFFFF' : currentTheme.colors.textSecondary} 
                  />
                  <Text style={[
                    styles.optionTitle,
                    { 
                      color: preferences.userType === option.id ? '#FFFFFF' : currentTheme.colors.textPrimary 
                    }
                  ]}>
                    {option.title}
                  </Text>
                  <Text style={[
                    styles.optionDescription,
                    { 
                      color: preferences.userType === option.id ? 'rgba(255, 255, 255, 0.8)' : currentTheme.colors.textSecondary 
                    }
                  ]}>
                    {option.description}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        );
        
      case 'studyPreferences':
        return (
          <View style={styles.stepContent}>
            <View style={styles.preferencesContainer}>
              <View style={styles.preferenceSection}>
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>When do you prefer to study?</Text>
                <View style={styles.timeOptionsContainer}>
                  {[
                    { id: 'morning', label: 'Morning (6-12 PM)' },
                    { id: 'afternoon', label: 'Afternoon (12-6 PM)' },
                    { id: 'evening', label: 'Evening (6-10 PM)' },
                    { id: 'night', label: 'Night (10 PM+)' }
                  ].map((timeOption) => (
                    <TouchableOpacity
                      key={timeOption.id}
                      style={[
                        styles.timeOption,
                        {
                          backgroundColor: preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) ? currentTheme.colors.primary : currentTheme.colors.surface,
                          borderColor: preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) ? currentTheme.colors.primary : currentTheme.colors.border
                        }
                      ]}
                      onPress={() => toggleStudyTime(timeOption.id)}
                    >
                      <Ionicons 
                        name={preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) ? 'checkmark-circle' : 'ellipse-outline'} 
                        size={20} 
                        color={preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) ? '#FFFFFF' : currentTheme.colors.textSecondary} 
                      />
                      <Text style={[
                        styles.timeOptionText,
                        { 
                          color: preferences.studyPreferences.preferredStudyTimes.includes(timeOption.id) ? '#FFFFFF' : currentTheme.colors.textPrimary 
                        }
                      ]}>
                        {timeOption.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
              
              <View style={styles.preferenceSectionLast}>
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>Study Session Duration</Text>
                <View style={styles.sliderContainer}>
                  {[25, 45, 60, 90].map((duration) => (
                    <TouchableOpacity
                      key={duration}
                      style={[
                        styles.durationOption,
                        {
                          backgroundColor: preferences.studyPreferences.sessionDuration === duration ? currentTheme.colors.primary : currentTheme.colors.surface,
                          borderColor: preferences.studyPreferences.sessionDuration === duration ? currentTheme.colors.primary : currentTheme.colors.border
                        }
                      ]}
                      onPress={() => selectStudyDuration(duration)}
                    >
                      <Text style={[
                        styles.durationText,
                        { 
                          color: preferences.studyPreferences.sessionDuration === duration ? '#FFFFFF' : currentTheme.colors.textPrimary 
                        }
                      ]}>
                        {duration}m
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </View>
          </View>
        );
        
      case 'workPreferences':
        return (
          <View style={styles.stepContent}>
            <View style={styles.preferencesContainer}>
              <View style={styles.preferenceSection}>
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
                  {preferences.userType === 'professional' ? 'When do you prefer to focus?' : 'When do you prefer to plan and teach?'}
              </Text>
                <View style={styles.timeOptionsContainer}>
                {[
                    { id: 'morning', label: 'Morning (6-12 PM)' },
                    { id: 'afternoon', label: 'Afternoon (12-6 PM)' },
                    { id: 'evening', label: 'Evening (6-10 PM)' },
                    { id: 'night', label: 'Night (10 PM+)' }
                  ].map((timeOption) => (
                    <TouchableOpacity
                      key={timeOption.id}
                      style={[
                        styles.timeOption,
                  { 
                          backgroundColor: preferences.workPreferences.preferredWorkTimes.includes(timeOption.id) ? currentTheme.colors.primary : currentTheme.colors.surface,
                          borderColor: preferences.workPreferences.preferredWorkTimes.includes(timeOption.id) ? currentTheme.colors.primary : currentTheme.colors.border
                        }
                      ]}
                      onPress={() => toggleWorkTime(timeOption.id)}
                    >
                      <Ionicons 
                        name={preferences.workPreferences.preferredWorkTimes.includes(timeOption.id) ? 'checkmark-circle' : 'ellipse-outline'} 
                        size={20} 
                        color={preferences.workPreferences.preferredWorkTimes.includes(timeOption.id) ? '#FFFFFF' : currentTheme.colors.textSecondary} 
                      />
                      <Text style={[
                        styles.timeOptionText,
                        { 
                          color: preferences.workPreferences.preferredWorkTimes.includes(timeOption.id) ? '#FFFFFF' : currentTheme.colors.textPrimary 
                        }
                      ]}>
                        {timeOption.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                      </View>
                    </View>
              
              <View style={styles.preferenceSection}>
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
                  {preferences.userType === 'professional' ? 'Focus Session Duration' : 'Planning Session Duration'}
                </Text>
                <View style={styles.sliderContainer}>
                  {[30, 45, 60, 90].map((duration) => (
                    <TouchableOpacity
                      key={duration}
                      style={[
                        styles.durationOption,
                        {
                          backgroundColor: preferences.workPreferences.focusSessionDuration === duration ? currentTheme.colors.primary : currentTheme.colors.surface,
                          borderColor: preferences.workPreferences.focusSessionDuration === duration ? currentTheme.colors.primary : currentTheme.colors.border
                        }
                      ]}
                      onPress={() => selectWorkDuration(duration)}
                    >
                      <Text style={[
                        styles.durationText,
                        { 
                          color: preferences.workPreferences.focusSessionDuration === duration ? '#FFFFFF' : currentTheme.colors.textPrimary 
                        }
                      ]}>
                        {duration}m
                      </Text>
                    </TouchableOpacity>
                ))}
                </View>
              </View>
              
              <View style={styles.preferenceSection}>
                <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
                  {preferences.userType === 'professional' ? 'Meeting Preference' : 'Collaboration Preference'}
              </Text>
                <View style={styles.timeOptionsContainer}>
                  {[
                    { id: 'morning', label: preferences.userType === 'professional' ? 'Morning meetings' : 'Morning collaboration' },
                    { id: 'afternoon', label: preferences.userType === 'professional' ? 'Afternoon meetings' : 'Afternoon planning' },
                    { id: 'minimal', label: preferences.userType === 'professional' ? 'Minimal meetings' : 'Independent work' }
                  ].map((option) => (
                    <TouchableOpacity
                      key={option.id}
                      style={[
                        styles.timeOption,
                        {
                          backgroundColor: preferences.workPreferences.meetingPreference === option.id ? currentTheme.colors.primary : currentTheme.colors.surface,
                          borderColor: preferences.workPreferences.meetingPreference === option.id ? currentTheme.colors.primary : currentTheme.colors.border
                        }
                      ]}
                      onPress={() => selectMeetingPreference(option.id)}
                    >
                      <Ionicons 
                        name={preferences.workPreferences.meetingPreference === option.id ? 'checkmark-circle' : 'ellipse-outline'} 
                        size={20} 
                        color={preferences.workPreferences.meetingPreference === option.id ? '#FFFFFF' : currentTheme.colors.textSecondary} 
                      />
                      <Text style={[
                        styles.timeOptionText,
                        { 
                          color: preferences.workPreferences.meetingPreference === option.id ? '#FFFFFF' : currentTheme.colors.textPrimary 
                        }
                      ]}>
                        {option.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </View>
          </View>
        );
        
      case 'integrations':
        return (
          <View style={styles.stepContent}>
            <View style={styles.integrationsContainer}>
              <Text style={[styles.integrationNote, { color: currentTheme.colors.textSecondary }]}>
                Which tools would you like to connect? We'll help you set them up after onboarding.
              </Text>
              
              <View style={styles.integrationsList}>
                {getIntegrationsForUserType().map((integration) => (
                  <TouchableOpacity
                    key={integration.key}
                    style={[
                      styles.integrationItem,
                      {
                        backgroundColor: preferences.integrations[integration.key as keyof typeof preferences.integrations] ? currentTheme.colors.primary : currentTheme.colors.surface,
                        borderColor: preferences.integrations[integration.key as keyof typeof preferences.integrations] ? currentTheme.colors.primary : currentTheme.colors.border
                  }
                    ]}
                                      onPress={() => toggleIntegration(integration.key)}
                  >
                    <View style={styles.integrationInfo}>
                      <Image 
                        source={integration.iconSource} 
                        style={[
                          styles.integrationIcon,
                          preferences.integrations[integration.key as keyof typeof preferences.integrations] && { opacity: 0.9 }
                        ]} 
                      />
                      <View style={styles.integrationText}>
                        <Text style={[
                          styles.integrationTitle,
                          { color: preferences.integrations[integration.key as keyof typeof preferences.integrations] ? '#FFFFFF' : currentTheme.colors.textPrimary }
                        ]}>
                          {integration.title}
                        </Text>
                        <Text style={[
                          styles.integrationDescription,
                          { color: preferences.integrations[integration.key as keyof typeof preferences.integrations] ? 'rgba(255, 255, 255, 0.9)' : currentTheme.colors.textSecondary }
                        ]}>
                          {integration.description}
                        </Text>
                      </View>
                    </View>
                    <Ionicons 
                      name={preferences.integrations[integration.key as keyof typeof preferences.integrations] ? 'checkmark-circle' : 'ellipse-outline'} 
                      size={24} 
                      color={preferences.integrations[integration.key as keyof typeof preferences.integrations] ? '#FFFFFF' : currentTheme.colors.textSecondary} 
                    />
                  </TouchableOpacity>
                ))}
              </View>
              
              <Text style={[styles.integrationFooter, { color: currentTheme.colors.textSecondary }]}>
                Don't worry - we'll guide you through the setup process in Settings after you complete onboarding.
              </Text>
            </View>
          </View>
        );
        
      case 'premium':
        return (
          <View style={styles.stepContent}>
            <View style={styles.premiumContainer}>
              <View style={styles.premiumBrandingSection}>
                <View style={[styles.premiumLogoContainer, { borderColor: currentTheme.colors.primary }]}>
                  <Ionicons name="shield-checkmark" size={32} color={currentTheme.colors.primary} />
                </View>
                <Text style={[styles.premiumMainTitle, { color: currentTheme.colors.textPrimary }]}>
                  Get unlimited usage with
                </Text>
                <Text style={[styles.premiumAppName, { color: currentTheme.colors.textPrimary }]}>
                  PulsePlan <Text style={{ color: currentTheme.colors.primary }}>Premium</Text>
                </Text>
              </View>

              <View style={styles.premiumFeaturesSection}>
                {[
                  'Unlimited AI assistant messages',
                  'Intelligent schedule optimization',
                  'Long-term memory & personalization',
                  'Proactive task suggestions',
                  'Advanced progress tracking & insights',
                  'Early access to new features',
                ].map((feature, index) => (
                  <View key={index} style={styles.premiumFeatureItem}>
                    <Ionicons name="checkmark-circle" size={16} color={currentTheme.colors.primary} />
                    <Text style={[styles.premiumFeatureText, { color: currentTheme.colors.textPrimary }]}>{feature}</Text>
                  </View>
                ))}
              </View>
              
              <View style={styles.premiumPlanSection}>
                <Text style={[styles.premiumPlanTitle, { color: currentTheme.colors.textPrimary }]}>Unlock Your Potential</Text>
                <Text style={[styles.premiumPlanSubtitle, { color: currentTheme.colors.textSecondary }]}>
                  Cancel anytime. 7 day free-trial.
                </Text>
              </View>

              <View style={[styles.premiumPriceCard, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.primary }]}>
                <View>
                  <Text style={[styles.premiumPlanName, { color: currentTheme.colors.textPrimary }]}>Premium</Text>
                  <Text style={[styles.premiumPrice, { color: currentTheme.colors.textPrimary }]}>$6.99</Text>
                  <Text style={[styles.premiumBillingCycle, { color: currentTheme.colors.textSecondary }]}>Billed Monthly</Text>
                </View>
                <View style={[styles.premiumRadioSelected, { borderColor: currentTheme.colors.primary }]}>
                  <View style={[styles.premiumRadioInner, { backgroundColor: currentTheme.colors.primary }]} />
                </View>
              </View>

              <View style={styles.premiumButtonsContainer}>
                <TouchableOpacity 
                  style={[styles.premiumCtaButton, { backgroundColor: currentTheme.colors.primary }]}
                  onPress={() => {
                    // TODO: Handle premium upgrade
                    console.log('Premium upgrade pressed');
                    nextStep();
                  }}
                >
                  <Text style={[styles.premiumCtaButtonText, { color: '#FFFFFF' }]}>
                    Start 7-day free trial
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.premiumSkipButton}
                  onPress={nextStep}
                >
                  <Text style={[styles.premiumSkipButtonText, { color: currentTheme.colors.textSecondary }]}>
                    Continue as Free
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        );
        
      case 'complete':
        return (
          <View style={styles.completeStepContent}>
            <View style={styles.completionContainer}>
              <View style={styles.checkmarkContainer}>
                <Ionicons name="checkmark-circle" size={64} color={currentTheme.colors.primary} />
              </View>
              <Text style={[styles.completionText, { color: currentTheme.colors.textPrimary }]}>
                You're all set!
              </Text>
              <Text style={[styles.completionSubtext, { color: currentTheme.colors.textSecondary }]}>
                PulsePlan is ready to help you achieve your goals.
              </Text>
              
              {/* Button inside content for proper centering */}
              <View style={styles.completeButtonContainer}>
                <TouchableOpacity 
                  onPress={nextStep}
                  style={[
                    styles.firstPageButton,
                    {
                      backgroundColor: currentTheme.colors.primary,
                    }
                  ]}
                >
                  <Text style={styles.firstPageButtonText}>Get Started</Text>
                  <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        );
        
      default:
        return null;
    }
  };

  // Show loading while we load the saved step
  if (isLoadingStep) {
  return (
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
        <StatusBar barStyle="light-content" backgroundColor={currentTheme.colors.background} />
        <View style={styles.loadingContainer}>
          <Text style={[styles.loadingText, { color: currentTheme.colors.textPrimary }]}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={currentTheme.colors.background} />
      
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
      <ScrollView 
          ref={scrollViewRef}
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View 
          style={[
            styles.content, 
            steps[step].component === 'complete' && {
              flex: 1,
              justifyContent: 'center',
              paddingTop: 0,
              paddingBottom: 0,
            },
            {
              opacity: fadeAnim,
              transform: [
                { translateX: slideAnim },
                { scale: scaleAnim }
              ]
            }
          ]}
        >
          {/* Header - Hide for premium and complete pages */}
          {steps[step].component !== 'premium' && steps[step].component !== 'complete' && (
            <View style={styles.header}>
              <Text style={styles.title}>{steps[step].title}</Text>
              <Text style={styles.description}>{steps[step].description}</Text>
            </View>
          )}
          
          {/* Progress indicator - Hide for premium and complete pages */}
          {steps[step].component !== 'premium' && steps[step].component !== 'complete' && (
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
          )}
          
          {/* Step content */}
          {renderStepContent()}
          
                    {/* Navigation buttons - Hide for premium and complete pages */}
          {steps[step].component !== 'premium' && steps[step].component !== 'complete' && (
            <View style={styles.navigationContainer}>
              {step > 0 && steps[step].component !== 'complete' && (
                <TouchableOpacity style={styles.backButton} onPress={prevStep}>
                  <Ionicons name="arrow-back" size={20} color={currentTheme.colors.textSecondary} />
                  <Text style={[styles.backButtonText, { color: currentTheme.colors.textSecondary }]}>Back</Text>
                </TouchableOpacity>
              )}
              
              {step === 0 || steps[step].component === 'complete' ? (
                // First page and complete page - centered prominent button
                <View style={styles.firstPageButtonContainer}>
                  <TouchableOpacity 
                    onPress={nextStep}
                    disabled={!canProceed()}
                    style={[
                      styles.firstPageButton,
                      {
                        backgroundColor: !canProceed() ? 'rgba(79, 140, 255, 0.4)' : currentTheme.colors.primary,
                        opacity: !canProceed() ? 0.7 : 1,
                      }
                    ]}
                  >
                    <Text style={styles.firstPageButtonText}>Get Started</Text>
                    <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
                  </TouchableOpacity>
                </View>
              ) : (
                // Other pages - settings-style text button
                <View style={styles.nextButtonContainer}>
                  <TouchableOpacity 
                    onPress={nextStep}
                    disabled={!canProceed()}
                    style={styles.nextButton}
                  >
                    <Text style={[
                      styles.nextButtonText,
                      { 
                        color: !canProceed() ? currentTheme.colors.textSecondary : currentTheme.colors.primary,
                        opacity: !canProceed() ? 0.6 : 1,
                      }
                    ]}>
                      {step === steps.length - 1 ? 'Get Started' : 'Continue'}
                    </Text>
                    <Ionicons 
                      name="arrow-forward" 
                      size={20} 
                      color={!canProceed() ? currentTheme.colors.textSecondary : currentTheme.colors.primary}
                      style={{ opacity: !canProceed() ? 0.6 : 1 }}
                    />
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )}
        </Animated.View>
      </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '500',
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingBottom: 24,
    minHeight: '100%',
  },
  content: {
    justifyContent: 'flex-start',
    paddingTop: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 24,
    marginTop: 32,
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 38,
    marginTop: 16,
  },
  description: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 8,
  },
  progressContainer: {
    marginBottom: 24,
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  progressBar: {
    width: '100%',
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
    backgroundColor: colors.primaryBlue,
  },
  progressText: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: '500',
  },
  stepContent: {
    justifyContent: 'flex-start',
    paddingHorizontal: 4,
    paddingTop: 12,
    paddingBottom: 12,
  },

  welcomeStepContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
    paddingVertical: 40,
  },
  welcomeOrbContainer: {
    alignItems: 'center',
    marginBottom: 60,
  },
  completeStepContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    minHeight: 400,
  },
  welcomeText: {
    fontSize: 17,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 26,
    paddingHorizontal: 16,
  },
  formContainer: {
    width: '100%',
    paddingHorizontal: 4,
    paddingTop: 16,
  },
  inputContainer: {
    marginBottom: 20,
    width: '100%',
  },
  inputContainerLast: {
    marginBottom: 8,
    width: '100%',
  },
  inputLabel: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  input: {
    width: '100%',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    fontSize: 16,
    borderWidth: 1,
  },
  autocompleteContainer: {
    position: 'relative',
    zIndex: 1000,
  },
  suggestionsContainer: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    borderRadius: 12,
    marginTop: 4,
    maxHeight: 200,
    borderWidth: 1,
    zIndex: 1001,
    elevation: 5,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  suggestionsScrollView: {
    maxHeight: 200,
  },
  suggestionItem: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  suggestionText: {
    fontSize: 16,
    lineHeight: 20,
  },
  optionsContainer: {
    width: '100%',
    gap: 10,
    paddingHorizontal: 4,
    marginTop: 8,
  },
  optionCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    minHeight: 100,
    justifyContent: 'center',
  },

  optionTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginTop: 10,
    marginBottom: 6,
    textAlign: 'center',
  },
  optionDescription: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 8,
  },
  preferencesContainer: {
    width: '100%',
    paddingHorizontal: 4,
    marginTop: 8,
  },
  preferenceSection: {
    marginBottom: 28,
    width: '100%',
  },
  preferenceSectionLast: {
    marginBottom: 8,
    width: '100%',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 20,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 8,
  },
  timeOptionsContainer: {
    gap: 12,
  },
  timeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  timeOptionText: {
    fontSize: 16,
    marginLeft: 12,
    fontWeight: '500',
  },
  sliderContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  durationOption: {
    flex: 1,
    paddingVertical: 16,
    paddingHorizontal: 8,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  durationText: {
    fontSize: 16,
    fontWeight: '600',
  },
  integrationsContainer: {
    width: '100%',
    paddingHorizontal: 4,
    marginTop: 8,
  },
  integrationNote: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
    paddingHorizontal: 8,
  },
  integrationsList: {
    marginBottom: 24,
    gap: 16,
  },
  integrationItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
  },
  integrationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  integrationIcon: {
    width: 24,
    height: 24,
  },
  integrationText: {
    marginLeft: 16,
    flex: 1,
  },
  integrationTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  integrationDescription: {
    fontSize: 14,
    lineHeight: 18,
  },
  integrationFooter: {
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },

  completionContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 0,
  },
  checkmarkContainer: {
    marginBottom: 40,
  },
  completionText: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 38,
  },
  completionSubtext: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: 16,
  },
  completeButtonContainer: {
    marginTop: 40,
    alignItems: 'center',
  },
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 4,
    paddingHorizontal: 4,
    gap: 16,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    minHeight: 44,
    minWidth: 80,
    borderRadius: 8,
  },
  backButtonText: {
    fontSize: 17,
    fontWeight: '500',
    marginLeft: 8,
  },
  nextButtonContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  nextButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    minHeight: 44,
    minWidth: 100,
    borderRadius: 8,
    gap: 8,
  },
  nextButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  firstPageButtonContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  firstPageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    paddingHorizontal: 32,
    borderRadius: 14,
    minHeight: 56,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
    minWidth: 180,
  },
  firstPageButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.2,
  },

  // Premium page styles
  premiumContainer: {
    paddingHorizontal: 4,
    paddingTop: 8,
  },
  premiumBrandingSection: {
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 24,
  },
  premiumLogoContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  premiumMainTitle: {
    fontSize: 20,
    fontWeight: '500',
    textAlign: 'center',
  },
  premiumAppName: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 4,
  },
  premiumFeaturesSection: {
    marginTop: 12,
    marginBottom: 24,
    gap: 12,
  },
  premiumFeatureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  premiumFeatureText: {
    fontSize: 15,
    lineHeight: 20,
    flex: 1,
  },
  premiumPlanSection: {
    marginBottom: 16,
    alignItems: 'center',
  },
  premiumPlanTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  premiumPlanSubtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  premiumPriceCard: {
    borderWidth: 2,
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  premiumPlanName: {
    fontSize: 16,
    fontWeight: '600',
  },
  premiumPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    marginVertical: 4,
  },
  premiumBillingCycle: {
    fontSize: 14,
  },
  premiumRadioSelected: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  premiumRadioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  premiumButtonsContainer: {
    gap: 12,
    marginBottom: 8,
  },
  premiumCtaButton: {
    paddingVertical: 16,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  premiumCtaButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  premiumSkipButton: {
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  premiumSkipButtonText: {
    fontSize: 16,
    fontWeight: '500',
    textDecorationLine: 'underline',
  },
});