import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TextInput,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { X } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const INSTRUCTIONS_KEY = '@pulse_agent_instructions';

interface AgentInstructionsModalProps {
  visible: boolean;
  onClose: () => void;
}

export default function AgentInstructionsModal({ visible, onClose }: AgentInstructionsModalProps) {
  const { currentTheme } = useTheme();
  const [instructions, setInstructions] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (visible) {
      loadInstructions();
    }
  }, [visible]);

  const loadInstructions = async () => {
    try {
      const savedInstructions = await AsyncStorage.getItem(INSTRUCTIONS_KEY);
      if (savedInstructions) {
        setInstructions(savedInstructions);
      }
    } catch (error) {
      console.error('Error loading instructions:', error);
    }
  };

  const saveInstructions = async () => {
    try {
      await AsyncStorage.setItem(INSTRUCTIONS_KEY, instructions);
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving instructions:', error);
    }
  };

  const handleTextChange = (text: string) => {
    setInstructions(text);
    setHasChanges(true);
  };

  const handleClose = () => {
    if (hasChanges) {
      saveInstructions();
    }
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={currentTheme.colors.background} />
        
        {/* Header */}
        <View style={[styles.header, { backgroundColor: currentTheme.colors.background }]}>
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={handleClose}
          >
            <X color={currentTheme.colors.textPrimary} size={24} />
          </TouchableOpacity>
          
          <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
            Instructions
          </Text>
          
          <TouchableOpacity 
            style={styles.doneButton}
            onPress={handleClose}
          >
            <Text style={[styles.doneButtonText, { color: currentTheme.colors.primary }]}>
              Done
            </Text>
          </TouchableOpacity>
        </View>

        {/* Content */}
        <View style={styles.content}>
          {/* Section Header */}
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
              ADDITIONAL INSTRUCTIONS
            </Text>
            <Text style={[styles.characterCount, { color: currentTheme.colors.textSecondary }]}>
              {instructions.length}/500
            </Text>
          </View>

          {/* Text Input */}
          <View style={[styles.inputContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <TextInput
              style={[styles.textInput, { color: currentTheme.colors.textPrimary }]}
              value={instructions}
              onChangeText={handleTextChange}
              placeholder="Ex: Speak in a formal and professional tone, use emojis in your responses, call me sir."
              placeholderTextColor={currentTheme.colors.textSecondary}
              multiline
              maxLength={500}
              textAlignVertical="top"
            />
          </View>

          {/* Description */}
          <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
            Specify any personality traits or speaking styles you'd like Martin to have. Provide additional context about your life or your work for Martin to take into account.
          </Text>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 8,
    marginLeft: -8,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  doneButton: {
    padding: 8,
    marginRight: -8,
  },
  doneButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  characterCount: {
    fontSize: 13,
    fontWeight: '500',
  },
  inputContainer: {
    borderRadius: 12,
    minHeight: 120,
    padding: 16,
    marginBottom: 16,
  },
  textInput: {
    fontSize: 16,
    lineHeight: 22,
    minHeight: 88,
  },
  description: {
    fontSize: 15,
    lineHeight: 20,
    marginTop: 8,
  },
}); 