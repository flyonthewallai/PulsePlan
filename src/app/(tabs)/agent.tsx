import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  useColorScheme,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  User,
  Bell,
  Mic,
  Plus,
  ArrowUp,
  ListTodo,
  Calendar,
  MessageSquare,
  FilePlus,
  BrainCircuit,
} from 'lucide-react-native';
import { SvgUri } from 'react-native-svg';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import SubscriptionModal from '@/components/SubscriptionModal';

const FIRST_VISIT_KEY = '@pulse_first_visit';

export default function AgentScreen() {
  const { currentTheme } = useTheme();
  const { subscriptionPlan } = useAuth();
  const colorScheme = useColorScheme();
  const keyboardAppearance = colorScheme === 'dark' ? 'dark' : 'light';
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [messageText, setMessageText] = useState('');
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const [isSubscriptionModalVisible, setIsSubscriptionModalVisible] = useState(false);

  useEffect(() => {
    checkFirstVisit();
  }, []);

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: messageText.length > 0 ? 0 : 1,
      duration: 200,
      useNativeDriver: true,
    }).start();
  }, [messageText]);

  const checkFirstVisit = async () => {
    try {
      const hasVisited = await AsyncStorage.getItem(FIRST_VISIT_KEY);
      if (!hasVisited) {
        await AsyncStorage.setItem(FIRST_VISIT_KEY, 'true');
        setIsFirstVisit(true);
      } else {
        setIsFirstVisit(false);
      }
    } catch (error) {
      console.error('Error checking first visit:', error);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
    },
    safeArea: {
      flex: 1,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 16,
      paddingTop: 20,
    },
    headerCenter: {
      flex: 1,
      alignItems: 'center',
      marginHorizontal: 16,
    },
    headerIcon: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
    },
    trialButton: {
      backgroundColor: currentTheme.colors.card,
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 20,
      minWidth: 120,
      alignItems: 'center',
    },
    trialButtonText: {
      color: currentTheme.colors.textPrimary,
      fontWeight: '600',
      fontSize: 15,
    },
    scrollView: {
      flex: 1,
    },
    scrollContent: {
      flexGrow: 1,
      paddingHorizontal: 16,
    },
    chatContainer: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginTop: 12,
      marginBottom: 24,
      gap: 12,
    },
    logoContainer: {
      width: 32,
      height: 32,
      borderRadius: 8,
      backgroundColor: currentTheme.colors.card,
      justifyContent: 'center',
      alignItems: 'center',
    },
    agentName: {
      color: currentTheme.colors.textPrimary,
      fontWeight: 'bold',
      fontSize: 16,
      marginBottom: 8,
    },
    messageContainer: {
      flex: 1,
      paddingRight: 16,
    },
    chatMessage: {
      color: currentTheme.colors.textPrimary,
      fontSize: 19,
      lineHeight: 26,
      marginBottom: 10,
      flexWrap: 'wrap',
    },
    actionsContainer: {
      gap: 12,
      marginBottom: 24,
    },
    actionButton: {
      backgroundColor: currentTheme.colors.surface,
      borderRadius: 20,
      padding: 16,
      flexDirection: 'row',
      alignItems: 'center',
      gap: 16,
    },
    actionButtonIconContainer: {
      width: 32,
      height: 32,
      justifyContent: 'center',
      alignItems: 'center',
    },
    actionButtonText: {
      color: currentTheme.colors.textPrimary,
      fontSize: 17,
      flex: 1,
    },
    bottomSection: {
      position: 'relative',
      width: '100%',
      backgroundColor: '#000000',
      paddingTop: 12,
    },
    suggestionsWrapper: {
      position: 'absolute',
      bottom: '100%',
      left: 0,
      right: 0,
      paddingBottom: 16,
    },
    suggestionsScroll: {
      paddingLeft: 16,
    },
    suggestionsContainer: {
      paddingRight: 16,
      gap: 8,
    },
    suggestionButton: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      paddingVertical: 8,
      paddingHorizontal: 14,
      borderRadius: 16,
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      height: 36,
    },
    suggestionButtonText: {
      color: '#FFFFFF',
      fontSize: 14,
      fontWeight: '500',
    },
    inputContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
      paddingHorizontal: 16,
      paddingBottom: 12,
    },
    plusButton: {
      width: 36,
      height: 36,
      borderRadius: 18,
      backgroundColor: currentTheme.colors.card,
      justifyContent: 'center',
      alignItems: 'center',
    },
    input: {
      flex: 1,
      minHeight: 42,
      maxHeight: 100,
      backgroundColor: currentTheme.colors.card,
      borderRadius: 21,
      paddingHorizontal: 16,
      paddingVertical: 10,
      color: currentTheme.colors.textPrimary,
      fontSize: 15,
      lineHeight: 20,
    },
    sendButton: {
      width: 42,
      height: 42,
      borderRadius: 21,
      backgroundColor: '#FFFFFF',
      justifyContent: 'center',
      alignItems: 'center',
    },
  });

  const Header = () => (
    <View style={styles.header}>
      <TouchableOpacity style={styles.headerIcon}>
        <User size={24} color={currentTheme.colors.textSecondary} />
      </TouchableOpacity>
      <View style={styles.headerCenter}>
        {subscriptionPlan === 'free' && (
          <TouchableOpacity 
            style={styles.trialButton}
            onPress={() => setIsSubscriptionModalVisible(true)}
            activeOpacity={0.7}
          >
            <Text style={styles.trialButtonText}>Start free trial</Text>
          </TouchableOpacity>
        )}
      </View>
      <TouchableOpacity style={styles.headerIcon}>
        <Bell size={24} color={currentTheme.colors.textSecondary} />
      </TouchableOpacity>
    </View>
  );

  const ActionButton = ({ icon, text, onPress }: { icon: React.ReactNode; text: string; onPress: () => void; }) => (
    <TouchableOpacity style={styles.actionButton} onPress={onPress}>
      <View style={styles.actionButtonIconContainer}>{icon}</View>
      <Text style={styles.actionButtonText}>{text}</Text>
    </TouchableOpacity>
  );

  const suggestions = [
    { icon: <Plus color={currentTheme.colors.textPrimary} size={20}/>, text: "Add to-do" },
    { icon: <ListTodo color={currentTheme.colors.textPrimary} size={20}/>, text: "List to-dos" },
    { icon: <FilePlus color={currentTheme.colors.textPrimary} size={20}/>, text: "Create note" },
    { icon: <Calendar color={currentTheme.colors.textPrimary} size={20}/>, text: "Schedule meeting" },
    { icon: <MessageSquare color={currentTheme.colors.textPrimary} size={20}/>, text: "Send message" },
  ];

  const SuggestionButton = ({ icon, text, onPress }: { icon: React.ReactNode; text: string; onPress: () => void; }) => (
    <TouchableOpacity style={styles.suggestionButton} onPress={onPress}>
      {icon}
      <Text style={styles.suggestionButtonText}>{text}</Text>
    </TouchableOpacity>
  );

  const handleActionPress = (action: string) => {
    console.log(`Action: ${action}`);
    // Handle action press
  };

  const actions = [
    {
      icon: <SvgUri width="28" height="28" uri="https://www.google.com/chrome/static/images/chrome-logo.svg" />,
      text: 'Review my calendar for rest of this week',
    },
    {
      icon: <SvgUri width="28" height="28" uri="https://www.vectorlogo.zone/logos/gmail/gmail-icon.svg" />,
      text: 'Review my unread emails from today',
    },
    {
      icon: <ListTodo color={currentTheme.colors.textPrimary} size={28} />,
      text: 'Make my to-do list for tomorrow',
    },
    {
      icon: <SvgUri width="28" height="28" uri="https://www.svgrepo.com/download/474329/slack.svg" />,
      text: 'Join Slack and send a message',
    },
    {
      icon: <MessageSquare color="#4CAF50" size={28} />,
      text: 'Send a text message to my contact',
    },
  ];

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
    >
      <SafeAreaView style={[styles.safeArea, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
        <Header />
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="interactive"
        >
          <View style={styles.chatContainer}>
            <View style={styles.logoContainer}>
              <BrainCircuit color={currentTheme.colors.textPrimary} size={24} />
            </View>
            <View style={styles.messageContainer}>
              <Text style={styles.agentName}>Pulse</Text>
              {isFirstVisit ? (
                <>
                  <Text style={styles.chatMessage}>
                    Hi. I'm Pulse, your new personal AI.
                  </Text>
                  <Text style={styles.chatMessage}>
                    I'm excited to get to know you and help out! Give me a task to start with:
                  </Text>
                </>
              ) : (
                <>
                  <Text style={styles.chatMessage}>
                    {getGreeting()}! What can I help you with today?
                  </Text>
                </>
              )}
            </View>
          </View>

          <View style={styles.actionsContainer}>
            {actions.map((action, index) => (
              <ActionButton
                key={index}
                icon={action.icon}
                text={action.text}
                onPress={() => handleActionPress(action.text)}
              />
            ))}
          </View>
        </ScrollView>

        <View style={styles.bottomSection}>
          <Animated.View style={[
            styles.suggestionsWrapper,
            { opacity: fadeAnim }
          ]}>
            <ScrollView 
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.suggestionsContainer}
              style={styles.suggestionsScroll}
              keyboardShouldPersistTaps="handled"
            >
              {suggestions.map((suggestion, index) => (
                <SuggestionButton
                  key={index}
                  icon={suggestion.icon}
                  text={suggestion.text}
                  onPress={() => {}}
                />
              ))}
            </ScrollView>
          </Animated.View>
          
          <View style={styles.inputContainer}>
            <TouchableOpacity style={[styles.plusButton, { backgroundColor: 'rgba(255, 255, 255, 0.1)' }]}>
              <Plus color="#FFFFFF" size={24} />
            </TouchableOpacity>
            <TextInput
              style={[styles.input, { 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                color: '#FFFFFF',
              }]}
              placeholder="Message"
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              keyboardAppearance={keyboardAppearance}
              returnKeyType="send"
              enablesReturnKeyAutomatically={true}
              multiline
              textAlignVertical="center"
              autoCorrect={undefined}
              autoCapitalize="sentences"
              keyboardType="default"
              spellCheck={undefined}
              dataDetectorTypes="all"
              textContentType="none"
              importantForAutofill="no"
              value={messageText}
              onChangeText={setMessageText}
            />
            <TouchableOpacity style={[styles.sendButton, { backgroundColor: '#FFFFFF' }]}>
              <ArrowUp color="#000000" size={20} />
            </TouchableOpacity>
          </View>
        </View>

        <SubscriptionModal 
          visible={isSubscriptionModalVisible}
          onClose={() => setIsSubscriptionModalVisible(false)}
        />
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
} 