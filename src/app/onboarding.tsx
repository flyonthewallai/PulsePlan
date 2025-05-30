import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity,
  StatusBar,
  Image,
  ScrollView,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { ArrowLeft, ArrowRight, Check, Brain, BookOpen } from 'lucide-react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { colors } from '@/constants/theme';
import OnboardingProgress from '@/components/OnboardingProgress';

const STEPS = [
  {
    title: 'Welcome to PulsePlan',
    description: 'The AI-powered academic planner that helps you achieve your educational goals.',
    image: 'https://images.pexels.com/photos/4145153/pexels-photo-4145153.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
  {
    title: 'What type of student are you?',
    description: 'Tell us a bit about yourself so we can personalize your experience.',
    options: ['Undergraduate', 'Graduate', 'High School', 'Self-Learner'],
  },
  {
    title: 'Your School & Major',
    description: 'Help us tailor your experience to your specific academic needs.',
    fields: ['School/Institution', 'Major/Field of Study'],
  },
  {
    title: 'Study Preferences',
    description: 'When are you most productive? We\'ll optimize your schedule accordingly.',
    preferences: [
      { title: 'Focus Hours', options: ['Morning', 'Afternoon', 'Evening', 'Night'] },
      { title: 'Break Habits', options: ['Short Frequent', 'Long Infrequent'] },
    ],
  },
  {
    title: 'Connect Your Tools',
    description: 'Integrate with your existing academic tools for a seamless experience.',
    integrations: ['Canvas', 'Google Calendar', 'Microsoft Outlook'],
  },
  {
    title: 'Notification Settings',
    description: 'How would you like to be reminded about your tasks and deadlines?',
    notifications: ['Task Reminders', 'Study Session Alerts', 'AI Suggestions'],
  },
  {
    title: 'All Set!',
    description: 'Your personalized academic planner is ready to help you succeed.',
    image: 'https://images.pexels.com/photos/3184639/pexels-photo-3184639.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
];

export default function OnboardingScreen() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [selections, setSelections] = useState({
    studentType: '',
    school: '',
    major: '',
    focusHours: '',
    breakHabits: '',
    integrations: [] as string[],
    notifications: [] as string[],
  });
  
  const handleNext = async () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete onboarding
      try {
        await AsyncStorage.setItem('onboarding_completed', 'true');
        router.replace('/(tabs)/home');
      } catch (error) {
        console.error('Error saving onboarding status:', error);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSelect = (type: string, value: string) => {
    setSelections(prev => ({
      ...prev,
      [type]: value,
    }));
  };

  const handleToggle = (type: string, value: string) => {
    setSelections(prev => {
      const current = prev[type as keyof typeof prev] || [];
      if (Array.isArray(current)) {
        if (current.includes(value)) {
          return {
            ...prev,
            [type]: current.filter(item => item !== value),
          };
        } else {
          return {
            ...prev,
            [type]: [...current, value],
          };
        }
      }
      return prev;
    });
  };

  const currentStepData = STEPS[currentStep];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" />
      
      <OnboardingProgress steps={STEPS.length} currentStep={currentStep} />
      
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {currentStepData.image && (
          <Image source={{ uri: currentStepData.image }} style={styles.image} />
        )}
        
        <View style={styles.textContent}>
          <Text style={styles.title}>{currentStepData.title}</Text>
          <Text style={styles.description}>{currentStepData.description}</Text>
        </View>
        
        {currentStepData.options && (
          <View style={styles.optionsContainer}>
            {currentStepData.options.map((option, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.optionButton,
                  selections.studentType === option && styles.optionButtonSelected
                ]}
                onPress={() => handleSelect('studentType', option)}
              >
                <Text style={[
                  styles.optionText,
                  selections.studentType === option && styles.optionTextSelected
                ]}>
                  {option}
                </Text>
                {selections.studentType === option && (
                  <Check size={20} color={colors.primaryBlue} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        )}
        
        {currentStepData.fields && (
          <View style={styles.fieldsContainer}>
            {currentStepData.fields.map((field, index) => (
              <View key={index} style={styles.inputContainer}>
                <Text style={styles.inputLabel}>{field}</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder={`Enter your ${field.toLowerCase()}`}
                  placeholderTextColor="rgba(255, 255, 255, 0.5)"
                  value={field === 'School/Institution' ? selections.school : selections.major}
                  onChangeText={(text) => 
                    handleSelect(field === 'School/Institution' ? 'school' : 'major', text)
                  }
                />
              </View>
            ))}
          </View>
        )}
        
        {currentStepData.preferences && (
          <View style={styles.preferencesContainer}>
            {currentStepData.preferences.map((pref, index) => (
              <View key={index} style={styles.preferenceGroup}>
                <Text style={styles.preferenceTitle}>{pref.title}</Text>
                <View style={styles.preferenceOptions}>
                  {pref.options.map((option, optionIndex) => (
                    <TouchableOpacity
                      key={optionIndex}
                      style={[
                        styles.preferenceButton,
                        (pref.title === 'Focus Hours' ? selections.focusHours : selections.breakHabits) === option && 
                        styles.preferenceButtonSelected
                      ]}
                      onPress={() => 
                        handleSelect(pref.title === 'Focus Hours' ? 'focusHours' : 'breakHabits', option)
                      }
                    >
                      <Text style={[
                        styles.preferenceText,
                        (pref.title === 'Focus Hours' ? selections.focusHours : selections.breakHabits) === option && 
                        styles.preferenceTextSelected
                      ]}>
                        {option}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            ))}
          </View>
        )}
        
        {currentStepData.integrations && (
          <View style={styles.integrationsContainer}>
            {currentStepData.integrations.map((integration, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.integrationButton,
                  selections.integrations.includes(integration) && styles.integrationButtonSelected
                ]}
                onPress={() => handleToggle('integrations', integration)}
              >
                <View style={styles.integrationContent}>
                  <BookOpen size={24} color={selections.integrations.includes(integration) ? colors.primaryBlue : colors.textSecondary} />
                  <Text style={[
                    styles.integrationText,
                    selections.integrations.includes(integration) && styles.integrationTextSelected
                  ]}>
                    {integration}
                  </Text>
                </View>
                {selections.integrations.includes(integration) && (
                  <Check size={20} color={colors.primaryBlue} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        )}
        
        {currentStepData.notifications && (
          <View style={styles.notificationsContainer}>
            {currentStepData.notifications.map((notification, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.notificationButton,
                  selections.notifications.includes(notification) && styles.notificationButtonSelected
                ]}
                onPress={() => handleToggle('notifications', notification)}
              >
                <View style={styles.notificationContent}>
                  <Brain size={24} color={selections.notifications.includes(notification) ? colors.primaryBlue : colors.textSecondary} />
                  <Text style={[
                    styles.notificationText,
                    selections.notifications.includes(notification) && styles.notificationTextSelected
                  ]}>
                    {notification}
                  </Text>
                </View>
                {selections.notifications.includes(notification) && (
                  <Check size={20} color={colors.primaryBlue} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>
      
      <View style={styles.footer}>
        {currentStep > 0 && (
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <ArrowLeft size={20} color={colors.textSecondary} />
            <Text style={styles.backText}>Back</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
          <LinearGradient
            colors={[colors.primaryBlue, colors.accentPurple]}
            style={styles.nextButtonGradient}
          >
            <Text style={styles.nextText}>
              {currentStep === STEPS.length - 1 ? 'Get Started' : 'Continue'}
            </Text>
            <ArrowRight size={20} color="white" />
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  image: {
    width: '100%',
    height: 200,
    borderRadius: 16,
    marginBottom: 32,
  },
  textContent: {
    marginBottom: 32,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: 16,
  },
  description: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  optionsContainer: {
    gap: 12,
    marginBottom: 32,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  optionButtonSelected: {
    backgroundColor: 'rgba(74, 144, 226, 0.1)',
    borderColor: colors.primaryBlue,
  },
  optionText: {
    fontSize: 16,
    color: colors.textPrimary,
    fontWeight: '500',
  },
  optionTextSelected: {
    color: colors.primaryBlue,
  },
  fieldsContainer: {
    gap: 16,
    marginBottom: 32,
  },
  inputContainer: {
    gap: 8,
  },
  inputLabel: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  textInput: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    color: colors.textPrimary,
    fontSize: 16,
  },
  preferencesContainer: {
    gap: 24,
    marginBottom: 32,
  },
  preferenceGroup: {
    gap: 12,
  },
  preferenceTitle: {
    fontSize: 16,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  preferenceOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  preferenceButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  preferenceButtonSelected: {
    backgroundColor: 'rgba(74, 144, 226, 0.1)',
    borderColor: colors.primaryBlue,
  },
  preferenceText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  preferenceTextSelected: {
    color: colors.primaryBlue,
  },
  integrationsContainer: {
    gap: 12,
    marginBottom: 32,
  },
  integrationButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  integrationButtonSelected: {
    backgroundColor: 'rgba(74, 144, 226, 0.1)',
    borderColor: colors.primaryBlue,
  },
  integrationContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  integrationText: {
    fontSize: 16,
    color: colors.textPrimary,
    fontWeight: '500',
  },
  integrationTextSelected: {
    color: colors.primaryBlue,
  },
  notificationsContainer: {
    gap: 12,
    marginBottom: 32,
  },
  notificationButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  notificationButtonSelected: {
    backgroundColor: 'rgba(74, 144, 226, 0.1)',
    borderColor: colors.primaryBlue,
  },
  notificationContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  notificationText: {
    fontSize: 16,
    color: colors.textPrimary,
    fontWeight: '500',
  },
  notificationTextSelected: {
    color: colors.primaryBlue,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
  },
  backText: {
    color: colors.textSecondary,
    fontSize: 16,
  },
  nextButton: {
    flex: 1,
    marginLeft: 16,
  },
  nextButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
  },
  nextText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});