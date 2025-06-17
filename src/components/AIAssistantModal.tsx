import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Modal, 
  TouchableOpacity,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Keyboard,
  Dimensions,
  Animated,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft, Send, Calendar, Clock, Zap, BarChart3, CheckCircle2, BrainCircuit, ArrowUp } from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { GlowingOrb } from './GlowingOrb';
import { useTheme } from '../contexts/ThemeContext';
import { useTasks } from '../contexts/TaskContext';
import { useSettings } from '../contexts/SettingsContext';
import { chatAPIService, ChatMessage } from '../services/chatService';
import { schedulingAPIService } from '../services/schedulingService';
import { formatAIResponse } from '../utils/markdownParser';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

type AIAssistantModalProps = {
  visible: boolean;
  onClose: () => void;
};

type Message = {
  id: string;
  text: string;
  isUser: boolean;
};

type QuickAction = {
  id: string;
  title: string;
  icon: React.ReactNode;
  prompt: string;
};

export default function AIAssistantModal({ visible, onClose }: AIAssistantModalProps) {
  const { currentTheme } = useTheme();
  const { tasks } = useTasks();
  const { workingHours } = useSettings();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);
  const inputRef = useRef<TextInput>(null);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  
  const quickActions: QuickAction[] = [
    {
      id: 'priority',
      title: 'Priority Tasks',
      icon: <Zap size={18} color="#fff" />,
      prompt: 'What are my highest priority tasks that I should focus on right now?'
    },
    {
      id: 'next',
      title: 'Next Task',
      icon: <CheckCircle2 size={18} color="#fff" />,
      prompt: 'Based on my current tasks and schedule, what should I work on next?'
    },
    {
      id: 'schedule',
      title: 'Quick Schedule',
      icon: <Calendar size={18} color="#fff" />,
      prompt: 'Create a quick schedule for my remaining tasks today.'
    },
    {
      id: 'progress',
      title: 'Progress Check',
      icon: <BarChart3 size={18} color="#fff" />,
      prompt: 'How am I doing with my tasks today? Give me a quick progress update.'
    },
  ];

  // Set initial welcome message when modal opens
  useEffect(() => {
    if (visible) {
      setMessages([{ 
        id: '1', 
        text: "How can I help?", 
        isUser: false 
      }]);
      
      setShowQuickActions(true);
      setConversationHistory([]);
      
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 300);
    }
  }, [visible]);

  // Keyboard event listeners for better handling
  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      (event) => {
        setKeyboardHeight(event.endCoordinates.height);
      }
    );

    const keyboardDidHideListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        setKeyboardHeight(0);
      }
    );

    return () => {
      keyboardDidShowListener.remove();
      keyboardDidHideListener.remove();
    };
  }, []);
  
  const sendMessage = async (messageText?: string) => {
    const textToSend = messageText || input.trim();
    if (textToSend === '' || isTyping) return;
    
    const newUserMessage = {
      id: Date.now().toString(),
      text: textToSend,
      isUser: true,
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    if (!messageText) setInput('');
    setIsTyping(true);
    setShowQuickActions(false);
    
    try {
      // Special handling for scheduling requests
      if (textToSend.toLowerCase().includes('schedule') && textToSend.toLowerCase().includes('optimized')) {
        await handleIntelligentScheduling(textToSend);
        return;
      }
      
      // Build conversation history for API
      const messagesToSend: ChatMessage[] = [
        ...conversationHistory,
        { role: 'user', content: textToSend }
      ];
      
      // Send to GPT API
      const response = await chatAPIService.sendMessage(messagesToSend);
      
      // Format the AI response to clean markdown
      const formattedResponse = formatAIResponse(response.content);
      
      // Add AI response
      const newAIMessage = {
        id: (Date.now() + 1).toString(),
        text: formattedResponse,
        isUser: false,
      };
      
      setMessages(prev => [...prev, newAIMessage]);
      
      // Update conversation history
      setConversationHistory(prev => [
        ...prev,
        { role: 'user', content: textToSend },
        { role: 'assistant', content: response.content }
      ]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: error instanceof Error ? error.message : 'Sorry, I encountered an error. Please try again.',
        isUser: false,
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      // Show alert for critical errors
      if (error instanceof Error && error.message.includes('Authentication')) {
        Alert.alert(
          'Authentication Error',
          'Please log in again to continue using the AI assistant.',
          [{ text: 'OK', onPress: onClose }]
        );
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleIntelligentScheduling = async (userPrompt: string) => {
    try {
      // Filter pending tasks
      const pendingTasks = tasks.filter(task => task.status === 'pending');
      
      if (pendingTasks.length === 0) {
        const noTasksMessage = {
          id: (Date.now() + 1).toString(),
          text: "You don't have any pending tasks to schedule. Create some tasks first, and I'll help you organize them optimally!",
          isUser: false,
        };
        setMessages(prev => [...prev, noTasksMessage]);
        return;
      }

      // Convert tasks to scheduling format
      const schedulingTasks = schedulingAPIService.convertTasksToSchedulingFormat(pendingTasks);
      
      // Generate time slots for today
      const today = new Date();
      const timeSlots = schedulingAPIService.generateDefaultTimeSlots(
        today,
        workingHours?.startHour || 9,
        workingHours?.endHour || 17
      );
      
      // Get user preferences
      const userPreferences = schedulingAPIService.getUserPreferences(workingHours);
      
      // Generate schedule
      const schedulingResult = await schedulingAPIService.generateSchedule(
        schedulingTasks,
        timeSlots,
        userPreferences
      );
      
      // Format the response with markdown cleaning
      const scheduleText = schedulingResult.schedule.map(block => {
        const startTime = new Date(block.startTime).toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
        const endTime = new Date(block.endTime).toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
        return `${startTime} - ${endTime}: ${block.title}`;
      }).join('\n');
      
      const fullResponse = `📅 Here's your optimized schedule for today:\n\n${scheduleText}\n\n${formatAIResponse(schedulingResult.explanation)}`;
      
      const scheduleMessage = {
        id: (Date.now() + 1).toString(),
        text: fullResponse,
        isUser: false,
      };
      
      setMessages(prev => [...prev, scheduleMessage]);
      
    } catch (error) {
      console.error('Error generating schedule:', error);
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: error instanceof Error ? error.message : 'Sorry, I had trouble creating your schedule. Please try again.',
        isUser: false,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleQuickAction = (action: QuickAction) => {
    sendMessage(action.prompt);
  };
  
  useEffect(() => {
    if (scrollViewRef.current) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  const handleKeyPress = () => {
    if (Platform.OS === 'web') {
      sendMessage();
    }
  };

  // Calculate dynamic margins based on keyboard state
  const getKeyboardAvoidingViewProps = () => {
    if (Platform.OS === 'ios') {
      return {
        behavior: 'padding' as const,
        keyboardVerticalOffset: 0,
      };
    } else {
      return {
        behavior: 'height' as const,
        keyboardVerticalOffset: 0,
      };
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
        <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <ArrowLeft color={currentTheme.colors.textSecondary} size={24} />
          </TouchableOpacity>
          
          <View style={styles.aiInfo}>
            <BrainCircuit size={20} color={currentTheme.colors.primary} />
            <Text style={[styles.aiName, { color: currentTheme.colors.textPrimary }]}>Pulse</Text>
          </View>
          
          <View style={styles.headerRight} />
        </View>
        
        <ScrollView
          ref={scrollViewRef}
          style={styles.messageContainer}
          contentContainerStyle={styles.messageContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {messages.map(message => (
            <View key={message.id} style={styles.chatContainer}>
              {!message.isUser && (
                <View style={[styles.logoContainer, { backgroundColor: currentTheme.colors.card }]}>
                  <BrainCircuit color={currentTheme.colors.textPrimary} size={24} />
                </View>
              )}
              <View style={[
                styles.messageWrapper,
                message.isUser ? styles.userMessageWrapper : null
              ]}>
                {!message.isUser && (
                  <Text style={[styles.agentName, { color: currentTheme.colors.textPrimary }]}>
                    Pulse
                  </Text>
                )}
                <Text style={[
                  styles.messageText,
                  { color: currentTheme.colors.textPrimary }
                ]}>
                  {message.text}
                </Text>
              </View>
            </View>
          ))}
          
          {showQuickActions && (
            <View style={styles.suggestionsWrapper}>
              <Animated.View style={{ opacity: fadeAnim }}>
                <View style={styles.suggestionsContainer}>
                  {quickActions.map((action) => (
                    <TouchableOpacity
                      key={action.id}
                      style={styles.suggestionButton}
                      onPress={() => handleQuickAction(action)}
                    >
                      <View style={styles.suggestionIcon}>
                        {action.icon}
                      </View>
                      <Text style={styles.suggestionText}>{action.title}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </Animated.View>
            </View>
          )}
          
          {isTyping && (
            <View style={styles.chatContainer}>
              <View style={[styles.logoContainer, { backgroundColor: currentTheme.colors.card }]}>
                <BrainCircuit color={currentTheme.colors.textPrimary} size={24} />
              </View>
              <View style={styles.messageWrapper}>
                <Text style={[styles.agentName, { color: currentTheme.colors.textPrimary }]}>
                  Pulse
                </Text>
                <View style={styles.typingIndicator}>
                  <View style={[styles.typingDot, { backgroundColor: currentTheme.colors.textSecondary }]} />
                  <View style={[styles.typingDot, styles.typingDotMiddle, { backgroundColor: currentTheme.colors.textSecondary }]} />
                  <View style={[styles.typingDot, { backgroundColor: currentTheme.colors.textSecondary }]} />
                </View>
              </View>
            </View>
          )}
        </ScrollView>
        
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
        >
          <View style={styles.bottomSection}>
            <View style={styles.inputContainer}>
              <TextInput
                ref={inputRef}
                style={[styles.input, { 
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  color: '#FFFFFF',
                }]}
                placeholder="Message"
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                value={input}
                onChangeText={(text) => {
                  setInput(text);
                  if (showQuickActions) {
                    Animated.timing(fadeAnim, {
                      toValue: text.length > 0 ? 0 : 1,
                      duration: 200,
                      useNativeDriver: true
                    }).start();
                  }
                }}
                multiline
                maxLength={500}
                onSubmitEditing={handleKeyPress}
                editable={!isTyping}
                autoFocus={false}
                textAlignVertical="center"
                returnKeyType="send"
                blurOnSubmit={false}
              />
              <TouchableOpacity 
                style={[
                  styles.sendButton,
                  { opacity: input.trim() === '' || isTyping ? 0.5 : 1 }
                ]}
                onPress={() => sendMessage()}
                disabled={input.trim() === '' || isTyping}
              >
                <ArrowUp color="#000000" size={20} />
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalContainer: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  closeButton: {
    padding: 4,
  },
  headerRight: {
    width: 32,
  },
  aiInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  aiName: {
    fontSize: 18,
    fontWeight: '600',
  },
  messageContainer: {
    flex: 1,
  },
  messageContent: {
    padding: 16,
    paddingBottom: 20,
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
    justifyContent: 'center',
    alignItems: 'center',
  },
  messageWrapper: {
    flex: 1,
    paddingRight: 16,
  },
  userMessageWrapper: {
    alignItems: 'flex-end',
  },
  agentName: {
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 8,
  },
  messageText: {
    fontSize: 19,
    lineHeight: 26,
    marginBottom: 10,
    flexWrap: 'wrap',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingBottom: Platform.OS === 'ios' ? 0 : 20,
  },
  input: {
    flex: 1,
    minHeight: 42,
    maxHeight: 100,
    borderRadius: 21,
    paddingHorizontal: 16,
    paddingVertical: 10,
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
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  typingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    opacity: 0.5,
  },
  typingDotMiddle: {
    opacity: 0.7,
  },
  suggestionsWrapper: {
    width: '100%',
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  suggestionsContainer: {
    width: '100%',
    gap: 8,
  },
  suggestionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    width: '100%',
  },
  suggestionIcon: {
    marginRight: 12,
  },
  suggestionText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '500',
  },
  bottomSection: {
    position: 'relative',
    width: '100%',
    backgroundColor: '#000000',
    paddingTop: 12,
  },
});