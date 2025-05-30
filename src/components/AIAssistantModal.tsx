import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Modal, 
  TouchableOpacity,
  TextInput,
  ScrollView,
  Animated,
  Easing,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { X, Send } from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { colors } from '../constants/theme';
import { GlowingOrb } from './GlowingOrb';

type AIAssistantModalProps = {
  visible: boolean;
  onClose: () => void;
};

type Message = {
  id: string;
  text: string;
  isUser: boolean;
};

export default function AIAssistantModal({ visible, onClose }: AIAssistantModalProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: "Hi, I'm your AI study assistant! How can I help you today?", isUser: false },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  
  const sendMessage = () => {
    if (input.trim() === '') return;
    
    const newUserMessage = {
      id: Date.now().toString(),
      text: input.trim(),
      isUser: true,
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setInput('');
    setIsTyping(true);
    
    // Simulate AI response
    setTimeout(() => {
      const aiResponses = [
        "I've analyzed your schedule. Try focusing on your Math assignment first as it's due tomorrow.",
        "Looking at your progress, you're doing great in Science but might need to spend more time on History.",
        "Based on your study patterns, your most productive hours are in the morning. Want me to reschedule some tasks to that time?",
        "I notice you have 3 assignments due this Friday. Would you like me to create a study plan to complete them all on time?",
      ];
      
      const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];
      
      const newAIMessage = {
        id: (Date.now() + 1).toString(),
        text: randomResponse,
        isUser: false,
      };
      
      setMessages(prev => [...prev, newAIMessage]);
      setIsTyping(false);
    }, 1500);
  };
  
  useEffect(() => {
    if (scrollViewRef.current) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <BlurView intensity={20} style={styles.overlay}>
        <View style={styles.modalContainer}>
          <View style={styles.header}>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <X color={colors.textSecondary} size={24} />
            </TouchableOpacity>
            
            <View style={styles.aiInfo}>
              <GlowingOrb size="sm" glowIntensity={0.3} glowOpacity={1.0} />
              <Text style={styles.aiName}>Pulse</Text>
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
                  message.isUser ? styles.userBubble : styles.aiBubble,
                ]}
              >
                <Text style={styles.messageText}>{message.text}</Text>
              </View>
            ))}
            
            {isTyping && (
              <View style={[styles.messageBubble, styles.aiBubble]}>
                <View style={styles.typingIndicator}>
                  <View style={styles.typingDot} />
                  <View style={[styles.typingDot, styles.typingDotMiddle]} />
                  <View style={styles.typingDot} />
                </View>
              </View>
            )}
          </ScrollView>
          
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            keyboardVerticalOffset={80}
          >
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Ask your AI assistant..."
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                value={input}
                onChangeText={setInput}
                multiline
              />
              <TouchableOpacity 
                style={styles.sendButton}
                onPress={sendMessage}
                disabled={input.trim() === ''}
              >
                <View style={styles.sendButtonGradient}>
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
    backgroundColor: colors.backgroundDark,
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
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
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
    color: colors.textPrimary,
  },
  messageContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  messageContent: {
    paddingTop: 16,
    paddingBottom: 16,
  },
  messageBubble: {
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 12,
    maxWidth: '80%',
  },
  userBubble: {
    backgroundColor: colors.primaryBlue,
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    color: colors.textPrimary,
    fontSize: 16,
  },
  typingIndicator: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    height: 24,
    width: 50,
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.textSecondary,
    marginHorizontal: 2,
    opacity: 0.6,
  },
  typingDotMiddle: {
    opacity: 0.8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  input: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: colors.textPrimary,
    fontSize: 16,
    maxHeight: 100,
    marginRight: 12,
  },
  sendButton: {
    marginBottom: 4,
  },
  sendButtonGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primaryBlue,
    justifyContent: 'center',
    alignItems: 'center',
  },
});