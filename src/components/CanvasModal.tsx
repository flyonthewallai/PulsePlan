import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  Alert,
  ActivityIndicator,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X, QrCode, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react-native';

import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { CanvasService } from '../services/canvasService';

interface CanvasModalProps {
  visible: boolean;
  onClose: () => void;
}

export default function CanvasModal({ visible, onClose }: CanvasModalProps) {
  const { currentTheme } = useTheme();
  const { session } = useAuth();
  
  const [status, setStatus] = useState<any>(null);
  const [qrData, setQrData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible && session?.access_token) {
      loadStatus();
    }
  }, [visible, session?.access_token]);

  const loadStatus = async () => {
    if (!session?.access_token) return;
    
    try {
      setLoading(true);
      const result = await CanvasService.getIntegrationStatus(session.access_token);
      setStatus(result);
    } catch (error) {
      console.error('Error loading Canvas status:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateQR = async () => {
    if (!session?.access_token) return;

    try {
      setLoading(true);
      const result = await CanvasService.generateConnectionCode(session.access_token);
      setQrData(result);
    } catch (error) {
      console.error('Error generating QR:', error);
      Alert.alert('Error', 'Failed to generate QR code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
          <TouchableOpacity onPress={onClose}>
            <X size={24} color={currentTheme.colors.textPrimary} />
          </TouchableOpacity>
          <Text style={[styles.title, { color: currentTheme.colors.textPrimary }]}>
            Canvas Integration
          </Text>
          <View style={{ width: 24 }} />
        </View>

        <ScrollView style={styles.content}>
          {status && (
            <View style={[styles.statusCard, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.statusRow}>
                {status.connected ? (
                  <CheckCircle size={24} color={currentTheme.colors.success} />
                ) : (
                  <AlertCircle size={24} color={currentTheme.colors.textSecondary} />
                )}
                <View style={styles.statusText}>
                  <Text style={[styles.statusTitle, { color: currentTheme.colors.textPrimary }]}>
                    {status.connected ? 'Connected' : 'Not Connected'}
                  </Text>
                  <Text style={[styles.statusSubtitle, { color: currentTheme.colors.textSecondary }]}>
                    {status.connected 
                      ? `${status.totalCanvasTasks} assignments synced`
                      : 'Connect your Chrome extension'
                    }
                  </Text>
                </View>
              </View>
            </View>
          )}

          {qrData && (
            <View style={styles.qrSection}>
              <Text style={[styles.qrTitle, { color: currentTheme.colors.textPrimary }]}>
                Scan with Chrome Extension
              </Text>
              <View style={[styles.qrContainer, { backgroundColor: currentTheme.colors.surface }]}>
                <Image
                  source={{ uri: qrData.qrCodeUrl }}
                  style={styles.qrImage}
                  resizeMode="contain"
                />
              </View>
              <Text style={[styles.qrNote, { color: currentTheme.colors.textSecondary }]}>
                Code expires in 10 minutes
              </Text>
            </View>
          )}

          <View style={styles.actions}>
            {status?.connected ? (
              <TouchableOpacity
                style={[styles.button, { borderColor: currentTheme.colors.primary }]}
                onPress={loadStatus}
                disabled={loading}
              >
                <RefreshCw size={20} color={currentTheme.colors.primary} />
                <Text style={[styles.buttonText, { color: currentTheme.colors.primary }]}>
                  Refresh
                </Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={[styles.button, styles.primaryButton, { backgroundColor: currentTheme.colors.primary }]}
                onPress={generateQR}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <QrCode size={20} color="white" />
                )}
                <Text style={[styles.buttonText, { color: 'white' }]}>
                  Connect Canvas
                </Text>
              </TouchableOpacity>
            )}
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  statusCard: {
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    marginLeft: 16,
    flex: 1,
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  statusSubtitle: {
    fontSize: 14,
  },
  qrSection: {
    alignItems: 'center',
    marginBottom: 20,
  },
  qrTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 20,
  },
  qrContainer: {
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
  },
  qrImage: {
    width: 200,
    height: 200,
  },
  qrNote: {
    fontSize: 14,
  },
  actions: {
    marginTop: 20,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
    borderWidth: 2,
  },
  primaryButton: {
    borderWidth: 0,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
}); 