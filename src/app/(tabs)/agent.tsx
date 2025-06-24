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
  Keyboard,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  Brain,
  Bell,
  Mic,
  Plus,
  ArrowUp,
  ListTodo,
  Calendar,
  MessageSquare,
  FilePlus,
  BrainCircuit,
  Slack,
} from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { useTasks } from '@/contexts/TaskContext';
import { agentAPIService } from '@/services/agentService';
import SubscriptionModal from '@/components/SubscriptionModal';
import AgentInstructionsModal from '@/components/AgentInstructionsModal';
import NotificationModal from '@/components/NotificationModal';
import { MarkdownText } from '@/components/MarkdownText';

const FIRST_VISIT_KEY = '@pulse_first_visit';

export default function AgentScreen() {
  const { currentTheme } = useTheme();
  const { subscriptionPlan } = useAuth();
  const { tasks } = useTasks();
  const colorScheme = useColorScheme();
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [messageText, setMessageText] = useState('');
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const [messages, setMessages] = useState<Array<{id: string, text: string, isUser: boolean}>>([]);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const actionsFadeAnim = useRef(new Animated.Value(1)).current;
  const scrollViewRef = useRef<ScrollView>(null);
  const [isSubscriptionModalVisible, setIsSubscriptionModalVisible] = useState(false);
  const [isInstructionsModalVisible, setIsInstructionsModalVisible] = useState(false);
  const [isNotificationModalVisible, setIsNotificationModalVisible] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);

  useEffect(() => {
    checkFirstVisit();
    
    // Add welcome message to conversation
    const welcomeMessage = {
      id: 'welcome',
      text: isFirstVisit 
        ? "Hi. I'm Pulse, your new personal AI.\n\nI'm excited to get to know you and help out! Give me a task to start with:"
        : `${getGreeting()}! What can I help you with today?`,
      isUser: false,
    };
    setMessages([welcomeMessage]);
  }, [isFirstVisit]);

  // Hide quick actions when there are user messages in the conversation
  useEffect(() => {
    const hasUserMessages = messages.some(msg => msg.isUser);
    setShowQuickActions(!hasUserMessages);
  }, [messages]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollViewRef.current && messages.length > 0) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  // Keyboard event listeners
  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      () => {
        setIsKeyboardVisible(true);
        // Fade out actions when keyboard appears
        Animated.timing(actionsFadeAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }).start();
      }
    );

    const keyboardDidHideListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        setIsKeyboardVisible(false);
        // Fade in actions when keyboard disappears
        Animated.timing(actionsFadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }).start();
      }
    );

    return () => {
      keyboardDidShowListener.remove();
      keyboardDidHideListener.remove();
    };
  }, [actionsFadeAnim]);

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: (messageText.length > 0 || !showQuickActions) ? 0 : 1,
      duration: 200,
      useNativeDriver: true,
    }).start();
  }, [messageText, showQuickActions]);

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
      marginTop: 0,
      lineHeight: 16,
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
    messageRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginVertical: 6,
    },
    userMessageRow: {
      justifyContent: 'flex-end',
      paddingLeft: 44, // 32px (icon width) + 12px (gap) to mirror Pulse's layout
      paddingRight: 0, // Remove extra padding since scrollContent already has 16px
      marginTop: 12,
      marginBottom: 24,
    },
    aiMessageRow: {
      justifyContent: 'flex-start',
    },
    messageBubble: {
      maxWidth: '85%',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderRadius: 24,
      marginHorizontal: 4,
      justifyContent: 'flex-start',
    },
    userBubble: {
      backgroundColor: '#3C3C3E',
      alignSelf: 'flex-end',
      maxWidth: '85%',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderRadius: 24,
      marginRight: 0, // Align to the right edge like Pulse's text aligns to the left
    },
    aiBubble: {
      backgroundColor: 'transparent',
    },
    userMessage: {
      color: '#FFFFFF',
      fontSize: 16,
      lineHeight: 20,
      fontWeight: '400',
    },
    aiMessage: {
      color: currentTheme.colors.textPrimary,
      fontSize: 19,
      lineHeight: 26,
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
      <TouchableOpacity 
        style={styles.headerIcon}
        onPress={() => setIsInstructionsModalVisible(true)}
      >
        <Brain size={24} color={currentTheme.colors.textSecondary} />
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
      <TouchableOpacity 
        style={styles.headerIcon}
        onPress={() => setIsNotificationModalVisible(true)}
      >
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
    { icon: <Image source={require('@/assets/images/notion.png')} style={{ width: 20, height: 20 }} />, text: "Create note" },
    { icon: <Calendar color={currentTheme.colors.textPrimary} size={20}/>, text: "Schedule meeting" },
    { icon: <MessageSquare color={currentTheme.colors.textPrimary} size={20}/>, text: "Send message" },
  ];

  const SuggestionButton = ({ icon, text, onPress }: { icon: React.ReactNode; text: string; onPress: () => void; }) => (
    <TouchableOpacity style={styles.suggestionButton} onPress={onPress}>
      {icon}
      <Text style={styles.suggestionButtonText}>{text}</Text>
    </TouchableOpacity>
  );

  const sendMessageToAgent = async (message: string) => {
    // Add user message to conversation
    const userMessage = {
      id: Date.now().toString(),
      text: message,
      isUser: true,
    };
    setMessages(prev => [...prev, userMessage]);
    
    setIsTyping(true);
    
    try {
      const context = {
        currentPage: 'agent',
        recentTasks: tasks.slice(0, 5),
      };

      const response = await agentAPIService.sendQuery({
        query: message,
        context
      });

      if (response.success) {
        let responseText = '';
        if (response.data && typeof response.data.response === 'string') {
          responseText = response.data.response;
        } else if (response.message) {
          responseText = response.message;
        } else if (response.data) {
          responseText = response.data.summary || 'Task completed successfully!';
        } else {
          responseText = 'I have successfully completed your request.';
        }
        
        // Add AI response to conversation
        const aiMessage = {
          id: (Date.now() + 1).toString(),
          text: responseText,
          isUser: false,
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        const errorText = response.error || 'I encountered an issue processing your request. Could you try rephrasing it?';
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          text: errorText,
          isUser: false,
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message to agent:', error);
      const errorText = 'Sorry, I encountered an error connecting to our servers. Please try again.';
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: errorText,
        isUser: false,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleActionPress = (action: string) => {
    console.log(`Action: ${action}`);
    sendMessageToAgent(action);
  };

  const handleSendMessage = () => {
    if (messageText.trim() === '' || isTyping) return;
    
    const message = messageText.trim();
    setMessageText('');
    sendMessageToAgent(message);
  };

  const handleSuggestionPress = (suggestion: string) => {
    sendMessageToAgent(suggestion);
  };

  const actions = [
    {
      icon: <Image source={require('@/assets/images/icon.png')} style={{ width: 28, height: 28 }} />,
      text: 'Make my schedule for this week',
    },
    {
      icon: <Image source={require('@/assets/images/applecalendar.png')} style={{ width: 28, height: 28 }} />,
      text: 'Review my calendar for this month',
    },
    {
      icon: <Image source={require('@/assets/images/gmail.png')} style={{ width: 28, height: 28 }} />,
      text: 'Review my unread emails from today',
    },
    {
      icon: <Image source={require('@/assets/images/canvas.png')} style={{ width: 28, height: 28 }} />,
      text: 'Make a plan for my chem exam',
    },
    {
      icon: <ListTodo color={currentTheme.colors.textPrimary} size={28} />,
      text: 'Make my to-do list for tomorrow',
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
          ref={scrollViewRef}
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="interactive"
          showsVerticalScrollIndicator={false}
        >
          {/* Conversation messages */}
          {messages.map(message => (
            <View key={message.id}>
              {message.isUser ? (
                // User message with gray bubble
                <View style={[styles.messageRow, styles.userMessageRow]}>
                  <View style={styles.userBubble}>
                    <Text style={styles.userMessage}>
                      {message.text}
                    </Text>
                  </View>
                </View>
              ) : (
                // AI message using original format
          <View style={styles.chatContainer}>
            <View style={styles.logoContainer}>
              <BrainCircuit color={currentTheme.colors.textPrimary} size={24} />
            </View>
            <View style={styles.messageContainer}>
              <Text style={styles.agentName}>Pulse</Text>
                    <MarkdownText style={styles.chatMessage}>
                      {message.text}
                    </MarkdownText>
                  </View>
                </View>
              )}
            </View>
          ))}
              
          {/* Typing indicator */}
              {isTyping && (
            <View style={styles.chatContainer}>
              <View style={styles.logoContainer}>
                <BrainCircuit color={currentTheme.colors.textPrimary} size={24} />
              </View>
              <View style={styles.messageContainer}>
                <Text style={styles.agentName}>Pulse</Text>
                <Text style={[styles.chatMessage, { opacity: 0.7 }]}>
                  Pulse is thinking...
                </Text>
              </View>
            </View>
          )}

          {showQuickActions && (
          <Animated.View 
            style={[
              styles.actionsContainer,
              {
                opacity: actionsFadeAnim,
                transform: [{
                  translateY: actionsFadeAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [-20, 0],
                  }),
                }],
              }
            ]}
            pointerEvents={isKeyboardVisible ? 'none' : 'auto'}
          >
            {actions.map((action, index) => (
              <ActionButton
                key={index}
                icon={action.icon}
                text={action.text}
                onPress={() => handleActionPress(action.text)}
              />
            ))}
          </Animated.View>
          )}
        </ScrollView>

        <View style={styles.bottomSection}>
          {showQuickActions && (
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
                  onPress={() => handleSuggestionPress(suggestion.text)}
                />
              ))}
            </ScrollView>
          </Animated.View>
          )}
          
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
              keyboardAppearance="default"
              returnKeyType="send"
              enablesReturnKeyAutomatically={true}
              multiline
              textAlignVertical="center"
              autoCapitalize="sentences"
              value={messageText}
              onChangeText={setMessageText}
            />
            <TouchableOpacity 
              style={[
                styles.sendButton, 
                { 
                  backgroundColor: '#FFFFFF',
                  opacity: messageText.trim() === '' || isTyping ? 0.5 : 1
                }
              ]}
              onPress={handleSendMessage}
              disabled={messageText.trim() === '' || isTyping}
            >
              <ArrowUp color="#000000" size={20} />
            </TouchableOpacity>
          </View>
        </View>

        <SubscriptionModal 
          visible={isSubscriptionModalVisible}
          onClose={() => setIsSubscriptionModalVisible(false)}
        />

        <AgentInstructionsModal
          visible={isInstructionsModalVisible}
          onClose={() => setIsInstructionsModalVisible(false)}
        />

        <NotificationModal 
          visible={isNotificationModalVisible}
          onClose={() => setIsNotificationModalVisible(false)}
        />
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
} 