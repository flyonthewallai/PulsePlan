import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X, BookOpen, ExternalLink, CheckCircle } from 'lucide-react-native';

import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { CanvasService } from '../services/canvasService';

interface CanvasAPIConnectionModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function CanvasAPIConnectionModal({ 
  visible, 
  onClose, 
  onSuccess 
}: CanvasAPIConnectionModalProps) {
  const { currentTheme } = useTheme();
  const { session } = useAuth();
  
  const [canvasDomain, setCanvasDomain] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  const handleConnect = async () => {
    if (!session?.access_token) {
      Alert.alert('Error', 'Please sign in to connect your Canvas account');
      return;
    }

    if (!canvasDomain.trim() || !apiKey.trim()) {
      Alert.alert('Error', 'Please enter both Canvas domain and API key');
      return;
    }

    // Validate domain format
    const domainRegex = /^https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!domainRegex.test(canvasDomain.trim())) {
      Alert.alert('Error', 'Please enter a valid Canvas domain (e.g., https://your-school.instructure.com)');
      return;
    }

    try {
      setIsConnecting(true);
      
      // Call the backend to connect Canvas with API key
      const result = await CanvasService.connectWithAPIKey(
        session.access_token,
        canvasDomain.trim(),
        apiKey.trim()
      );
      
      if (result.success) {
        setIsConnected(true);
        Alert.alert(
          'Success!', 
          'Canvas integration connected successfully. Your assignments will now sync to PulsePlan.',
          [
            {
              text: 'OK',
              onPress: () => {
                onSuccess?.();
                onClose();
              }
            }
          ]
        );
      } else {
        throw new Error(result.message || 'Connection failed');
      }
    } catch (error) {
      console.error('Canvas connection error:', error);
      Alert.alert('Connection Failed', error.message || 'Failed to connect Canvas account. Please check your credentials and try again.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleClose = () => {
    if (!isConnecting) {
      setCanvasDomain('');
      setApiKey('');
      setIsConnected(false);
      onClose();
    }
  };

  return (
    <Modal 
      visible={visible} 
      animationType="slide" 
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        {/* Header */}
        <View style={[styles.modalHeader, { borderBottomColor: currentTheme.colors.border }]}>
          <TouchableOpacity onPress={handleClose} style={styles.closeButton} disabled={isConnecting}>
            <X size={24} color={currentTheme.colors.textPrimary} />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Image 
              source={require('../assets/images/canvas.png')} 
              style={styles.canvasLogo}
              resizeMode="contain"
            />
            <Text style={[styles.modalTitle, { color: currentTheme.colors.textPrimary }]}>
              Canvas
            </Text>
          </View>
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Instructions Section */}
          <View style={[styles.instructionsSection, { backgroundColor: currentTheme.colors.surface }]}>
            <Text style={[styles.instructionsTitle, { color: currentTheme.colors.textPrimary }]}>
              How to get your Canvas API key
            </Text>
            
            <View style={styles.stepsList}>
              <View style={styles.stepItem}>
                <View style={[styles.stepNumber, { backgroundColor: currentTheme.colors.primary }]}>
                  <Text style={styles.stepNumberText}>1</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={[styles.stepText, { color: currentTheme.colors.textPrimary }]}>
                    Go to your Canvas domain
                  </Text>
                  <Text style={[styles.stepSubtext, { color: currentTheme.colors.textSecondary }]}>
                    Navigate to your school's Canvas website
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={[styles.stepNumber, { backgroundColor: currentTheme.colors.primary }]}>
                  <Text style={styles.stepNumberText}>2</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={[styles.stepText, { color: currentTheme.colors.textPrimary }]}>
                    Go to Profile Settings
                  </Text>
                  <Text style={[styles.stepSubtext, { color: currentTheme.colors.textSecondary }]}>
                    Click on your profile picture → Settings
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={[styles.stepNumber, { backgroundColor: currentTheme.colors.primary }]}>
                  <Text style={styles.stepNumberText}>3</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={[styles.stepText, { color: currentTheme.colors.textPrimary }]}>
                    Create Access Token
                  </Text>
                  <Text style={[styles.stepSubtext, { color: currentTheme.colors.textSecondary }]}>
                    Under "Approved Integrations" → "New Access Token"
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={[styles.stepNumber, { backgroundColor: currentTheme.colors.primary }]}>
                  <Text style={styles.stepNumberText}>4</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={[styles.stepText, { color: currentTheme.colors.textPrimary }]}>
                    Enter details and copy token
                  </Text>
                  <Text style={[styles.stepSubtext, { color: currentTheme.colors.textSecondary }]}>
                    Purpose: "PulsePlan" → Leave other fields blank → Copy the token
                  </Text>
                </View>
              </View>
            </View>
          </View>

          {/* Input Section */}
          <View style={[styles.inputSection, { backgroundColor: currentTheme.colors.surface }]}>
            <Text style={[styles.inputSectionTitle, { color: currentTheme.colors.textPrimary }]}>
              Enter your Canvas details
            </Text>

            <View style={styles.inputContainer}>
              <Text style={[styles.inputLabel, { color: currentTheme.colors.textPrimary }]}>
                Canvas Domain
              </Text>
              <TextInput
                style={[
                  styles.textInput,
                  {
                    backgroundColor: currentTheme.colors.background,
                    borderColor: currentTheme.colors.border,
                    color: currentTheme.colors.textPrimary,
                  }
                ]}
                placeholder="https://your-school.instructure.com"
                placeholderTextColor={currentTheme.colors.textSecondary}
                value={canvasDomain}
                onChangeText={setCanvasDomain}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="url"
                editable={!isConnecting}
              />
            </View>

            <View style={styles.inputContainer}>
              <Text style={[styles.inputLabel, { color: currentTheme.colors.textPrimary }]}>
                API Key
              </Text>
              <TextInput
                style={[
                  styles.textInput,
                  {
                    backgroundColor: currentTheme.colors.background,
                    borderColor: currentTheme.colors.border,
                    color: currentTheme.colors.textPrimary,
                  }
                ]}
                placeholder="Paste your Canvas API token here"
                placeholderTextColor={currentTheme.colors.textSecondary}
                value={apiKey}
                onChangeText={setApiKey}
                autoCapitalize="none"
                autoCorrect={false}
                secureTextEntry
                editable={!isConnecting}
              />
            </View>
          </View>

          {/* Connect Button */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[
                styles.connectButton,
                {
                  backgroundColor: isConnecting ? currentTheme.colors.textSecondary : '#FFFFFF',
                  opacity: isConnecting ? 0.6 : 1,
                }
              ]}
              onPress={handleConnect}
              disabled={isConnecting}
            >
              {isConnecting ? (
                <ActivityIndicator size="small" color="#000000" />
              ) : (
                <CheckCircle size={20} color="#000000" />
              )}
              <Text style={[styles.connectButtonText, { color: '#000000' }]}>
                {isConnecting ? 'Connecting...' : 'Connect'}
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  modalHeader: {
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
  headerCenter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  canvasLogo: {
    width: 24,
    height: 24,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  placeholder: {
    width: 32,
  },
  content: {
    flex: 1,
  },
  instructionsSection: {
    margin: 20,
    padding: 20,
    borderRadius: 16,
  },
  instructionsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  stepsList: {
    gap: 16,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  stepNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  stepNumberText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'white',
  },
  stepContent: {
    flex: 1,
  },
  stepText: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  stepSubtext: {
    fontSize: 14,
    lineHeight: 20,
  },
  inputSection: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
  },
  inputSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
  },
  buttonContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  connectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 8,
  },
  connectButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
