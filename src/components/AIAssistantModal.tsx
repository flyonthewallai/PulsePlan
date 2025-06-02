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
} from 'react-native';
import { BlurView } from 'expo-blur';
import { X, Send, Calendar, Clock, Zap, BarChart3 } from 'lucide-react-native';

import { GlowingOrb } from './GlowingOrb';
import { useTheme } from '../contexts/ThemeContext';
import { useTasks } from '../contexts/TaskContext';
import { useSettings } from '../contexts/SettingsContext';
import { chatAPIService, ChatMessage } from '../services/chatService';
import { schedulingAPIService } from '../services/schedulingService';
import { formatAIResponse } from '../utils/markdownParser';

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
  const scrollViewRef = useRef<ScrollView>(null);
  
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
  
  // Reset conversation when modal opens
  useEffect(() => {
    if (visible) {
      setConversationHistory([]);
      setMessages([
        { id: '1', text: "Hi, I'm Pulse, your AI study assistant! I can help you manage your tasks, analyze your schedule, and provide productivity insights. How can I help you today?", isUser: false },
      ]);
      setShowQuickActions(true);
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

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <BlurView intensity={20} style={styles.overlay}>
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
            contentContainerStyle={styles.messageContent}
            showsVerticalScrollIndicator={false}
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
            
            {showQuickActions && messages.length === 1 && (
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
          
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            keyboardVerticalOffset={80}
          >
            <View style={[styles.inputContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <TextInput
                style={[styles.input, { 
                  color: currentTheme.colors.textPrimary,
                  borderColor: currentTheme.colors.border
                }]}
                placeholder="Ask your AI assistant..."
                placeholderTextColor={currentTheme.colors.textSecondary}
                value={input}
                onChangeText={setInput}
                multiline
                maxLength={500}
                onSubmitEditing={handleKeyPress}
                editable={!isTyping}
              />
              <TouchableOpacity 
                style={[styles.sendButton, { opacity: input.trim() === '' || isTyping ? 0.5 : 1 }]}
                onPress={() => sendMessage()}
                disabled={input.trim() === '' || isTyping}
              >
                <View style={[styles.sendButtonGradient, { backgroundColor: currentTheme.colors.primary }]}>
                  <Send color="#fff" size={20} />
                </View>
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </View>
      </BlurView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
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
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 100,
    marginRight: 12,
  },
  sendButton: {
    marginBottom: 2,
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