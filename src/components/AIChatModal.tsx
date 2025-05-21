import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Animated,
  Dimensions,
  Easing
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { API_URL, getApiUrl } from '../config/api';
import { useAuth } from '../contexts/AuthContext';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface AIChatModalProps {
  visible: boolean;
  onClose: () => void;
  initialTask?: any;
}

const WELCOME_MESSAGE = "Hi! I'm your AI assistant. I can help you manage your tasks, set reminders, and provide insights about your productivity. How can I help you today?";

const SUGGESTED_MESSAGES = [
  "Can you help me organize my tasks for today?",
  "What's the best way to prioritize my workload?",
  "Can you analyze my productivity patterns?",
  "How can I improve my study habits?",
  "What tasks should I focus on first?",
  "Can you help me break down this big project?",
  "What's a good schedule for my upcoming deadline?",
  "How can I better manage my time?",
];

const PLACEHOLDER_MESSAGES = [
  "Type a message...",
  "Ask about your tasks...",
  "Get productivity tips...",
  "Plan your schedule...",
  "Organize your workload...",
];

export const AIChatModal = ({ visible, onClose, initialTask }: AIChatModalProps) => {
  const { theme, darkMode } = useTheme();
  const { session } = useAuth();
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingText, setTypingText] = useState('');
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [placeholderText, setPlaceholderText] = useState('');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [shouldPreventInput, setShouldPreventInput] = useState(true);
  const [isWelcomeComplete, setIsWelcomeComplete] = useState(false);
  const [isSuggestionReady, setIsSuggestionReady] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const inputRef = useRef<TextInput>(null);
  const modalHeight = useRef(Dimensions.get('window').height * 0.8).current;
  const typingTimeout = useRef<NodeJS.Timeout | null>(null);
  const suggestionTimeout = useRef<NodeJS.Timeout | null>(null);
  const placeholderTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (visible) {
      setInputText('');
      setPlaceholderText('');
      setPlaceholderIndex(0);
      setIsInputFocused(false);
      setShouldPreventInput(true);
      setIsInitialized(false);
      setIsTyping(false);
      setIsSuggesting(false);
      setTypingText('');
      setMessages([]);
      setIsWelcomeComplete(false);
      setIsSuggestionReady(false);
      
      if (typingTimeout.current) clearTimeout(typingTimeout.current);
      if (placeholderTimeout.current) clearTimeout(placeholderTimeout.current);
      if (suggestionTimeout.current) clearTimeout(suggestionTimeout.current);
      
      if (inputRef.current) {
        inputRef.current.clear();
      }
    }
  }, [visible]);

  useEffect(() => {
    let isMounted = true;
    
    if (visible && !isWelcomeComplete && messages.length === 0) {
      setIsTyping(true);
      setShouldPreventInput(false);
      setInputText('');
      
      let currentIndex = 0;
      const typeNextChar = () => {
        if (!isMounted) return;
        
        if (currentIndex < WELCOME_MESSAGE.length) {
          setTypingText(WELCOME_MESSAGE.slice(0, currentIndex + 1));
          currentIndex++;
          typingTimeout.current = setTimeout(typeNextChar, 10);
        } else {
          if (!isMounted) return;
          
          setIsTyping(false);
          setMessages([{
            id: Date.now().toString(),
            text: WELCOME_MESSAGE,
            isUser: false,
            timestamp: new Date(),
          }]);
          setTypingText('');
          setIsWelcomeComplete(true);
          setTimeout(() => {
            if (isMounted) {
              setIsSuggestionReady(true);
            }
          }, 500);
        }
      };

      typeNextChar();
    }

    return () => {
      isMounted = false;
      if (typingTimeout.current) {
        clearTimeout(typingTimeout.current);
      }
    };
  }, [visible, isWelcomeComplete, messages.length]);

  useEffect(() => {
    if (!isSuggestionReady || !visible || isTyping || isSuggesting || inputText || !messages.length) {
      return;
    }

    const startSuggestion = () => {
      if (!isSuggestionReady) return;
      
      setIsSuggesting(true);
      let currentIndex = 0;
      const currentSuggestion = SUGGESTED_MESSAGES[suggestionIndex];

      const typeNextChar = () => {
        if (currentIndex < currentSuggestion.length) {
          setInputText(currentSuggestion.slice(0, currentIndex + 1));
          currentIndex++;
          typingTimeout.current = setTimeout(typeNextChar, 30);
        } else {
          suggestionTimeout.current = setTimeout(() => {
            let clearIndex = currentSuggestion.length;
            const clearText = () => {
              if (clearIndex > 0) {
                setInputText(currentSuggestion.slice(0, clearIndex - 1));
                clearIndex--;
                typingTimeout.current = setTimeout(clearText, 20);
              } else {
                setInputText('');
                setIsSuggesting(false);
                setSuggestionIndex((prev) => (prev + 1) % SUGGESTED_MESSAGES.length);
                suggestionTimeout.current = setTimeout(startSuggestion, 1000);
              }
            };
            clearText();
          }, 3000);
        }
      };

      typeNextChar();
    };

    suggestionTimeout.current = setTimeout(startSuggestion, 1000);

    return () => {
      if (typingTimeout.current) clearTimeout(typingTimeout.current);
      if (suggestionTimeout.current) clearTimeout(suggestionTimeout.current);
    };
  }, [visible, isTyping, messages.length, inputText, suggestionIndex, isSuggestionReady]);

  useEffect(() => {
    if (!isWelcomeComplete || !visible || inputText || isInputFocused || !messages.length) {
      return;
    }

    const animatePlaceholder = () => {
      let currentIndex = 0;
      const currentPlaceholder = PLACEHOLDER_MESSAGES[placeholderIndex];

      const typeNextChar = () => {
        if (currentIndex < currentPlaceholder.length) {
          setPlaceholderText(currentPlaceholder.slice(0, currentIndex + 1));
          currentIndex++;
          typingTimeout.current = setTimeout(typeNextChar, 30);
        } else {
          placeholderTimeout.current = setTimeout(() => {
            let clearIndex = currentPlaceholder.length;
            const clearText = () => {
              if (clearIndex > 0) {
                setPlaceholderText(currentPlaceholder.slice(0, clearIndex - 1));
                clearIndex--;
                typingTimeout.current = setTimeout(clearText, 20);
              } else {
                setPlaceholderText('');
                setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDER_MESSAGES.length);
                placeholderTimeout.current = setTimeout(animatePlaceholder, 300);
              }
            };
            clearText();
          }, 1200);
        }
      };

      typeNextChar();
    };

    const startDelay = setTimeout(() => {
      animatePlaceholder();
    }, 500);

    return () => {
      if (typingTimeout.current) clearTimeout(typingTimeout.current);
      if (placeholderTimeout.current) clearTimeout(placeholderTimeout.current);
      clearTimeout(startDelay);
    };
  }, [visible, inputText, placeholderIndex, isInputFocused, messages.length, isWelcomeComplete]);

  const handleSend = async () => {
    if (!inputText.trim()) return;

    if (typingTimeout.current) clearTimeout(typingTimeout.current);
    if (suggestionTimeout.current) clearTimeout(suggestionTimeout.current);
    setIsSuggesting(false);

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    try {
      // Log the API URL in development
      if (__DEV__) {
        console.log('Sending chat request to:', getApiUrl('/chat/message'));
      }

      // Convert messages to chat format with proper typing
      const chatMessages: ChatMessage[] = messages.map(msg => ({
        role: msg.isUser ? 'user' as const : 'assistant' as const,
        content: msg.text
      })).concat({
        role: 'user' as const,
        content: inputText
      });

      // Get the access token from session
      const token = session?.access_token;
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(getApiUrl('/chat/message'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ messages: chatMessages }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        console.error('Server error response:', {
          status: response.status,
          statusText: response.statusText,
          errorData
        });
        throw new Error(errorData?.message || `Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (!data.content) {
        console.error('Invalid server response format:', data);
        throw new Error('Invalid response format from server');
      }

      const aiResponse = data.content;
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: aiResponse,
        isUser: false,
        timestamp: new Date(),
      }]);
    } catch (error) {
      console.error('Error getting AI response:', error);
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: error instanceof Error 
          ? `I'm sorry, I encountered an error: ${error.message}. Please try again.`
          : "I'm sorry, I encountered an error. Please try again.",
        isUser: false,
        timestamp: new Date(),
      }]);
    }
  };

  const handleInputChange = (text: string) => {
    if (isSuggesting) {
      return;
    }
    if (suggestionTimeout.current) {
      clearTimeout(suggestionTimeout.current);
      setIsSuggesting(false);
    }
    setInputText(text);
    setPlaceholderText('');
  };

  const handleInputFocus = () => {
    setIsInputFocused(true);
    setPlaceholderText('');
    if (suggestionTimeout.current) {
      clearTimeout(suggestionTimeout.current);
      setIsSuggesting(false);
    }
  };

  const styles = StyleSheet.create({
    modalOverlay: {
      flex: 1,
      backgroundColor: 'rgba(0, 0, 0, 0.35)',
      justifyContent: 'center',
      alignItems: 'center',
    },
    modalContainer: {
      flex: 1,
      backgroundColor: theme.colors.background,
      shadowColor: theme.colors.primary,
      shadowOffset: {
        width: 0,
        height: 8,
      },
      shadowOpacity: 0.15,
      shadowRadius: 24,
      elevation: 12,
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      flexDirection: 'column',
    },
    header: {
      marginBottom: 24,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 20,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border + '40',
      backgroundColor: theme.colors.background,
    },
    headerTitle: {
      fontSize: 28,
      fontWeight: 'bold',
      color: theme.colors.text,
      letterSpacing: 0.3,
      marginBottom: 0,
      flex: 1,
      textAlign: 'center',
    },
    messagesContainer: {
      flex: 1,
    },
    scrollViewContent: {
      flexGrow: 1,
      padding: 16,
      paddingBottom: 100,
    },
    messageBubble: {
      maxWidth: '85%',
      padding: 12,
      borderRadius: 20,
      marginBottom: 12,
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 1,
      },
      shadowOpacity: 0.1,
      shadowRadius: 2,
      elevation: 2,
    },
    userMessage: {
      backgroundColor: theme.colors.primary,
      alignSelf: 'flex-end',
      borderBottomRightRadius: 4,
      paddingHorizontal: 16,
      paddingVertical: 10,
      maxWidth: '85%',
      width: 'auto',
    },
    aiMessage: {
      backgroundColor: theme.colors.cardBackground,
      borderWidth: 1,
      borderColor: theme.colors.border + '40',
      alignSelf: 'flex-start',
      borderBottomLeftRadius: 4,
      flexDirection: 'row',
      alignItems: 'flex-start',
      gap: 8,
      paddingRight: 16,
      paddingLeft: 12,
      paddingVertical: 10,
      maxWidth: '85%',
      width: 'auto',
    },
    aiIconContainer: {
      width: 24,
      height: 24,
      borderRadius: 12,
      backgroundColor: theme.colors.primary + '15',
      justifyContent: 'center',
      alignItems: 'center',
      marginTop: 2,
      flexShrink: 0,
    },
    aiIcon: {
      width: 14,
      height: 14,
    },
    messageContent: {
      flex: 0,
      flexShrink: 1,
    },
    messageText: {
      fontSize: 15,
      lineHeight: 20,
      letterSpacing: 0.2,
    },
    userMessageText: {
      color: '#FFFFFF',
    },
    aiMessageText: {
      color: theme.colors.text,
    },
    inputContainer: {
      flexDirection: 'row',
      paddingHorizontal: 12,
      paddingTop: 4,
      paddingBottom: Platform.OS === 'ios' ? 8 : 4,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border + '40',
      backgroundColor: theme.colors.background,
      borderBottomLeftRadius: 24,
      borderBottomRightRadius: 24,
      gap: 8,
      position: 'relative',
      zIndex: 1,
    },
    input: {
      flex: 1,
      backgroundColor: theme.colors.cardBackground,
      borderRadius: 12,
      paddingHorizontal: 12,
      paddingVertical: 8,
      color: theme.colors.text,
      fontSize: 15,
      maxHeight: 100,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    inputPlaceholder: {
      color: theme.colors.subtext + '80',
    },
    sendButton: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 12,
      borderRadius: 12,
      backgroundColor: theme.colors.primary + '15',
      gap: 8,
      borderWidth: 1,
      borderColor: theme.colors.primary,
    },
    sendButtonDisabled: {
      opacity: 0.5,
      backgroundColor: theme.colors.cardBackground,
      borderColor: theme.colors.border,
    },
    typingMessage: {
      borderStyle: 'dashed',
    },
    typingCursor: {
      opacity: 0.7,
      fontWeight: 'bold',
    },
    buttonText: {
      fontSize: 15,
      fontWeight: '600',
      color: theme.colors.primary,
      letterSpacing: 0.2,
    },
    typingDotsContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 4,
      paddingHorizontal: 4,
      minHeight: 24,
      marginTop: 2,
    },
    typingDot: {
      width: 6,
      height: 6,
      borderRadius: 3,
      backgroundColor: theme.colors.text + '80',
      marginVertical: 2,
    },
  });

  const renderMessage = (message: Message) => (
    <View
      key={message.id}
      style={[
        styles.messageBubble,
        message.isUser ? styles.userMessage : styles.aiMessage,
      ]}
    >
      {!message.isUser && (
        <View style={styles.aiIconContainer}>
          <Ionicons 
            name="sparkles" 
            size={14} 
            color={theme.colors.primary}
            style={styles.aiIcon}
          />
        </View>
      )}
      <View style={styles.messageContent}>
        <Text
          style={[
            styles.messageText,
            message.isUser ? styles.userMessageText : styles.aiMessageText,
          ]}
          numberOfLines={0}
        >
          {message.text}
        </Text>
      </View>
    </View>
  );

  const renderTypingMessage = () => (
    <View
      style={[
        styles.messageBubble,
        styles.aiMessage,
        styles.typingMessage,
      ]}
    >
      <View style={styles.aiIconContainer}>
        <Ionicons 
          name="sparkles" 
          size={14} 
          color={theme.colors.primary}
          style={styles.aiIcon}
        />
      </View>
      <View style={styles.messageContent}>
        {!isWelcomeComplete ? (
          <Text
            style={[
              styles.messageText,
              styles.aiMessageText,
            ]}
            numberOfLines={0}
          >
            {typingText}
            <Text style={styles.typingCursor}>|</Text>
          </Text>
        ) : (
          <TypingIndicator />
        )}
      </View>
    </View>
  );

  const TypingIndicator = () => {
    const [dot1] = useState(new Animated.Value(0));
    const [dot2] = useState(new Animated.Value(0));
    const [dot3] = useState(new Animated.Value(0));

    useEffect(() => {
      const animate = () => {
        Animated.sequence([
          Animated.parallel([
            Animated.timing(dot1, {
              toValue: 1,
              duration: 400,
              easing: Easing.ease,
              useNativeDriver: true,
            }),
            Animated.timing(dot2, {
              toValue: 1,
              duration: 400,
              delay: 150,
              easing: Easing.ease,
              useNativeDriver: true,
            }),
            Animated.timing(dot3, {
              toValue: 1,
              duration: 400,
              delay: 300,
              easing: Easing.ease,
              useNativeDriver: true,
            }),
          ]),
          Animated.parallel([
            Animated.timing(dot1, {
              toValue: 0,
              duration: 400,
              easing: Easing.ease,
              useNativeDriver: true,
            }),
            Animated.timing(dot2, {
              toValue: 0,
              duration: 400,
              delay: 150,
              easing: Easing.ease,
              useNativeDriver: true,
            }),
            Animated.timing(dot3, {
              toValue: 0,
              duration: 400,
              delay: 300,
              easing: Easing.ease,
              useNativeDriver: true,
            }),
          ]),
        ]).start(() => animate());
      };

      animate();
      return () => {
        dot1.stopAnimation();
        dot2.stopAnimation();
        dot3.stopAnimation();
      };
    }, []);

    return (
      <View style={styles.typingDotsContainer}>
        <Animated.View style={[
          styles.typingDot,
          {
            opacity: dot1,
            transform: [{
              translateY: dot1.interpolate({
                inputRange: [0, 1],
                outputRange: [0, -4],
              }),
            }],
          },
        ]} />
        <Animated.View style={[
          styles.typingDot,
          {
            opacity: dot2,
            transform: [{
              translateY: dot2.interpolate({
                inputRange: [0, 1],
                outputRange: [0, -4],
              }),
            }],
          },
        ]} />
        <Animated.View style={[
          styles.typingDot,
          {
            opacity: dot3,
            transform: [{
              translateY: dot3.interpolate({
                inputRange: [0, 1],
                outputRange: [0, -4],
              }),
            }],
          },
        ]} />
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="fade"
      onRequestClose={onClose}
      statusBarTranslucent={true}
    >
      <View style={styles.modalOverlay}>
        <TouchableOpacity 
          activeOpacity={1} 
          onPress={onClose}
          style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
        />
        <View style={styles.modalContainer}>
          <SafeAreaView edges={['top']} style={{ backgroundColor: theme.colors.background }}>
            <View style={styles.header}>
              <View style={{ width: 40 }} />
              <Text style={styles.headerTitle}>AI Assistant</Text>
              <TouchableOpacity
                onPress={onClose}
                style={{ width: 40, height: 40, justifyContent: 'center', alignItems: 'center' }}
              >
                <Ionicons name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>
          </SafeAreaView>
          
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={{ flex: 1 }}
            keyboardVerticalOffset={Platform.OS === 'ios' ? -16 : 0}
          >
            <ScrollView
              ref={scrollViewRef}
              style={styles.messagesContainer}
              contentContainerStyle={styles.scrollViewContent}
              onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
              showsVerticalScrollIndicator={false}
            >
              {messages.map(renderMessage)}
              {isTyping && !isWelcomeComplete && renderTypingMessage()}
              {isTyping && isWelcomeComplete && renderTypingMessage()}
            </ScrollView>
            
            <View style={[
              styles.inputContainer,
              { paddingBottom: Platform.OS === 'ios' ? insets.bottom : 0 }
            ]}>
              <TextInput
                ref={inputRef}
                style={styles.input}
                value={inputText}
                onChangeText={handleInputChange}
                onFocus={handleInputFocus}
                onBlur={() => {
                  setIsInputFocused(false);
                  if (!inputText) {
                    setPlaceholderText('');
                    setPlaceholderIndex(0);
                  }
                }}
                placeholder={isInputFocused ? "Type a message..." : placeholderText}
                placeholderTextColor={theme.colors.subtext + '80'}
                multiline
                maxLength={500}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="default"
                returnKeyType="default"
                blurOnSubmit={false}
                editable={!isTyping && !isSuggesting}
                keyboardAppearance={darkMode ? 'dark' : 'light'}
                onSubmitEditing={() => {
                  if (inputText.trim() && !isTyping && !isSuggesting) {
                    handleSend();
                  }
                }}
              />
              <TouchableOpacity
                style={[
                  styles.sendButton,
                  (!inputText.trim() || isTyping) && styles.sendButtonDisabled
                ]}
                onPress={handleSend}
                disabled={!inputText.trim() || isTyping}
              >
                <Text style={[
                  styles.buttonText,
                  (!inputText.trim() || isTyping) && { color: theme.colors.text }
                ]}>
                  Send
                </Text>
                <Ionicons
                  name="send"
                  size={20}
                  color={(!inputText.trim() || isTyping) ? theme.colors.text : theme.colors.primary}
                  style={{ marginLeft: 2 }}
                />
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </View>
      </View>
    </Modal>
  );
}; 