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
import { X, Lock } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const INSTRUCTIONS_KEY = '@pulse_agent_instructions';
const MEMORIES_KEY = '@pulse_agent_memories';

interface AgentInstructionsModalProps {
  visible: boolean;
  onClose: () => void;
}

export default function AgentInstructionsModal({ visible, onClose }: AgentInstructionsModalProps) {
  const { currentTheme } = useTheme();
  const { subscriptionPlan } = useAuth();
  const isPremium = subscriptionPlan === 'premium';
  const [instructions, setInstructions] = useState('');
  const [memories, setMemories] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (visible) {
      loadInstructions();
      loadMemories();
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

  const loadMemories = async () => {
    try {
      const savedMemories = await AsyncStorage.getItem(MEMORIES_KEY);
      if (savedMemories) {
        setMemories(savedMemories);
      }
    } catch (error) {
      console.error('Error loading memories:', error);
    }
  };

  const saveInstructions = async () => {
    try {
      await AsyncStorage.setItem(INSTRUCTIONS_KEY, instructions);
    } catch (error) {
      console.error('Error saving instructions:', error);
    }
  };

  const saveMemories = async () => {
    try {
      await AsyncStorage.setItem(MEMORIES_KEY, memories);
    } catch (error) {
      console.error('Error saving memories:', error);
    }
  };

  const handleInstructionsChange = (text: string) => {
    setInstructions(text);
    setHasChanges(true);
  };

  const handleMemoriesChange = (text: string) => {
    setMemories(text);
    setHasChanges(true);
  };

  const handleClose = async () => {
    if (hasChanges) {
      await saveInstructions();
      await saveMemories();
      setHasChanges(false);
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
              Save
            </Text>
          </TouchableOpacity>
        </View>

        {/* Content */}
        <View style={styles.content}>
          {/* Additional Instructions Section */}
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
              ADDITIONAL INSTRUCTIONS
            </Text>
            <Text style={[styles.characterCount, { color: currentTheme.colors.textSecondary }]}>
              {instructions.length}/500
            </Text>
          </View>

          <View style={[styles.inputContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <TextInput
              style={[styles.textInput, { color: currentTheme.colors.textPrimary }]}
              value={instructions}
              onChangeText={handleInstructionsChange}
              placeholder="Ex: Speak in a formal and professional tone, use emojis in your responses, call me sir."
              placeholderTextColor={currentTheme.colors.textSecondary}
              multiline
              maxLength={500}
              textAlignVertical="top"
            />
          </View>

          <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
            Specify any personality traits or speaking styles you'd like Pulse to have. Provide additional context about your life or your work for Pulse to take into account.
          </Text>

          {/* Memories Section */}
          <View style={styles.memoriesContainer}>
            <View style={[styles.sectionHeader, styles.memoriesSection]}>
              <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
                MEMORIES
              </Text>
              <Text style={[styles.characterCount, { color: currentTheme.colors.textSecondary }]}>
                {memories.length}/500
              </Text>
            </View>

            <View style={[styles.inputContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <TextInput
                style={[styles.textInput, { color: currentTheme.colors.textPrimary }]}
                value={memories}
                onChangeText={handleMemoriesChange}
                placeholder="Ex: I'm a college student majoring in computer science, I work part-time at a coffee shop, I prefer studying in the evenings."
                placeholderTextColor={currentTheme.colors.textSecondary}
                multiline
                maxLength={500}
                textAlignVertical="top"
                editable={isPremium}
              />
            </View>

            <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
              Provide context about your life, preferences, schedule, and any important details you'd like Pulse to remember when assisting you.
            </Text>

            {/* Premium Overlay */}
            {!isPremium && (
              <View style={[styles.premiumOverlay, { backgroundColor: `${currentTheme.colors.background}CC` }]}>
                <View style={[styles.premiumContent, { backgroundColor: currentTheme.colors.surface }]}>
                  <Lock color={currentTheme.colors.textSecondary} size={24} />
                  <Text style={[styles.premiumTitle, { color: currentTheme.colors.textPrimary }]}>
                    Premium Feature
                  </Text>
                  <Text style={[styles.premiumSubtitle, { color: currentTheme.colors.textSecondary }]}>
                    Upgrade to Premium to access memories
                  </Text>
                </View>
              </View>
            )}
          </View>
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
  memoriesSection: {
    marginTop: 32,
  },
  memoriesContainer: {
    position: 'relative',
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
  premiumOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
  },
  premiumContent: {
    alignItems: 'center',
    padding: 24,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  premiumTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 4,
  },
  premiumSubtitle: {
    fontSize: 14,
    textAlign: 'center',
  },
}); 