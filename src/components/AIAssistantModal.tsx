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
} from 'react-native';
import { BlurView } from 'expo-blur';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X, Send, Calendar, Clock, Zap, BarChart3 } from 'lucide-react-native';

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
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: "Hi, I'm Pulse, your AI study assistant! I can help you manage your tasks, analyze your schedule, and provide productivity insights. How can I help you today?", isUser: false },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);
  const inputRef = useRef<TextInput>(null);
  
  const quickActions: QuickAction[] = [
    {
      id: 'schedule',
      title: 'Smart Schedule',
      icon: <Calendar size={18} color={currentTheme.colors.primary} />,
      prompt: 'Please create an optimized schedule for my pending tasks today. Consider my working hours and break times.'
    },
    {
      id: 'today',
      title: "Today's Tasks",
      icon: <Clock size={18} color={currentTheme.colors.primary} />,
      prompt: 'Show me all my tasks for today and their status. What should I prioritize?'
    },
    {
      id: 'productivity',
      title: 'Productivity Tips',
      icon: <Zap size={18} color={currentTheme.colors.primary} />,
      prompt: 'Based on my current tasks and subjects, give me personalized productivity tips and study strategies.'
    },
    {
      id: 'analysis',
      title: 'Task Analysis',
      icon: <BarChart3 size={18} color={currentTheme.colors.primary} />,
      prompt: 'Analyze my task patterns, completion rates, and suggest improvements to my workflow.'
    },
  ];

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
  
  // Reset conversation when modal opens and auto-focus input
  useEffect(() => {
    if (visible) {
      setConversationHistory([]);
      setMessages([
        { id: '1', text: "Hi, I'm Pulse, your AI study assistant! I can help you manage your tasks, analyze your schedule, and provide productivity insights. How can I help you today?", isUser: false },
      ]);
      setShowQuickActions(true);
      
      // Automatically focus the input when modal opens
      // Use timeout to ensure modal is fully rendered first
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 300);
    } else {
      // Reset keyboard height when modal closes
      setKeyboardHeight(0);
    }
  }, [visible]);
  
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
      transparent
      animationType="slide"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <BlurView intensity={20} style={styles.overlay}>
        <KeyboardAvoidingView
          style={styles.keyboardAvoidingContainer}
          {...getKeyboardAvoidingViewProps()}
        >
          <View style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
            <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
              <TouchableOpacity style={styles.closeButton} onPress={onClose}>
                <X color={currentTheme.colors.textSecondary} size={24} />
              </TouchableOpacity>
              
              <View style={styles.aiInfo}>
                <GlowingOrb size="sm" color={currentTheme.colors.primary} glowIntensity={0.3} glowOpacity={1.0} />
                <Text style={[styles.aiName, { color: currentTheme.colors.textPrimary }]}>Pulse</Text>
              </View>
            </View>
            
            <ScrollView
              ref={scrollViewRef}
              style={styles.messageContainer}
              contentContainerStyle={[
                styles.messageContent,
                { paddingBottom: Platform.OS === 'android' ? keyboardHeight + 20 : 20 }
              ]}
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="handled"
            >
              {messages.map(message => (
                <View 
                  key={message.id} 
                  style={[
                    styles.messageBubble,
                    message.isUser 
                      ? [styles.userBubble, { backgroundColor: currentTheme.colors.primary }]
                      : [styles.aiBubble, { backgroundColor: currentTheme.colors.surface }],
                  ]}
                >
                  <Text style={[
                    styles.messageText, 
                    { 
                      color: message.isUser ? '#FFFFFF' : currentTheme.colors.textPrimary 
                    }
                  ]}>
                    {message.text}
                  </Text>
                </View>
              ))}
              
              {showQuickActions && (
                <View style={styles.quickActionsContainer}>
                  <Text style={[styles.quickActionsTitle, { color: currentTheme.colors.textSecondary }]}>
                    Quick Actions
                  </Text>
                  <View style={styles.quickActionsGrid}>
                    {quickActions.map(action => (
                      <TouchableOpacity
                        key={action.id}
                        style={[styles.quickActionButton, { 
                          backgroundColor: currentTheme.colors.surface,
                          borderColor: currentTheme.colors.border
                        }]}
                        onPress={() => handleQuickAction(action)}
                      >
                        {action.icon}
                        <Text style={[styles.quickActionText, { color: currentTheme.colors.textPrimary }]}>
                          {action.title}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
              
              {isTyping && (
                <View style={[styles.messageBubble, styles.aiBubble, { backgroundColor: currentTheme.colors.surface }]}>
                  <View style={styles.typingIndicator}>
                    <View style={[styles.typingDot, { backgroundColor: currentTheme.colors.textSecondary }]} />
                    <View style={[styles.typingDot, styles.typingDotMiddle, { backgroundColor: currentTheme.colors.textSecondary }]} />
                    <View style={[styles.typingDot, { backgroundColor: currentTheme.colors.textSecondary }]} />
                  </View>
                </View>
              )}
            </ScrollView>
            
            <View style={[styles.inputContainer, { 
              backgroundColor: currentTheme.colors.background,
              borderTopColor: currentTheme.colors.border,
              paddingBottom: keyboardHeight > 0 ? 8 : (Platform.OS === 'ios' ? 34 : 20),
            }]}>
              <View style={[styles.inputWrapper, { 
                backgroundColor: currentTheme.colors.surface,
                borderColor: input.trim() ? currentTheme.colors.primary : currentTheme.colors.border
              }]}>
                <TextInput
                  ref={inputRef}
                  style={[styles.input, { 
                    color: currentTheme.colors.textPrimary,
                  }]}
                  placeholder="Message Pulse..."
                  placeholderTextColor={currentTheme.colors.textSecondary}
                  value={input}
                  onChangeText={setInput}
                  multiline
                  maxLength={500}
                  onSubmitEditing={handleKeyPress}
                  editable={!isTyping}
                  autoFocus={false}
                  textAlignVertical="top"
                  returnKeyType="send"
                  blurOnSubmit={false}
                />
                <TouchableOpacity 
                  style={[styles.sendButton, { 
                    opacity: input.trim() === '' || isTyping ? 0.3 : 1,
                    backgroundColor: input.trim() ? currentTheme.colors.primary : currentTheme.colors.border
                  }]}
                  onPress={() => sendMessage()}
                  disabled={input.trim() === '' || isTyping}
                  activeOpacity={0.8}
                >
                  <Send color="#fff" size={18} />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </KeyboardAvoidingView>
      </BlurView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  keyboardAvoidingContainer: {
    flex: 1,
  },
  modalContainer: {
    flex: 1,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    marginTop: 60,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  closeButton: {
    position: 'absolute',
    left: 24,
    padding: 4,
  },
  aiInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  aiName: {
    fontSize: 16,
    fontWeight: '600',
  },
  messageContainer: {
    flex: 1,
    paddingHorizontal: 24,
  },
  messageContent: {
    paddingVertical: 16,
    paddingBottom: 20,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginVertical: 4,
  },
  userBubble: {
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginHorizontal: 2,
    opacity: 0.6,
  },
  typingDotMiddle: {
    animationDelay: '0.1s',
  },
  inputContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderWidth: 1.5,
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
    minHeight: 48,
    maxHeight: 120,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  input: {
    flex: 1,
    fontSize: 16,
    lineHeight: 20,
    paddingTop: 12,
    paddingBottom: 12,
    paddingHorizontal: 0,
    textAlignVertical: 'top',
  },
  sendButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 12,
    marginBottom: 2,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  sendButtonGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  quickActionsContainer: {
    marginVertical: 16,
  },
  quickActionsTitle: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 12,
    textAlign: 'center',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  quickActionButton: {
    width: '48%',
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    gap: 8,
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
});