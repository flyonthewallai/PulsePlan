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
  Dimensions,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  X,
  QrCode,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Clock,
  BookOpen,
  Smartphone,
  Monitor,
  Zap,
} from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { CanvasService, CanvasIntegrationStatus, QRConnectionData } from '../services/canvasService';

interface CanvasIntegrationModalProps {
  visible: boolean;
  onClose: () => void;
}

const { width: screenWidth } = Dimensions.get('window');

export default function CanvasIntegrationModal({ visible, onClose }: CanvasIntegrationModalProps) {
  const { currentTheme } = useTheme();
  const { user, session } = useAuth();
  
  const [integrationStatus, setIntegrationStatus] = useState<CanvasIntegrationStatus | null>(null);
  const [qrData, setQrData] = useState<QRConnectionData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGeneratingQR, setIsGeneratingQR] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [currentStep, setCurrentStep] = useState<'overview' | 'qr' | 'success'>('overview');

  useEffect(() => {
    if (visible && session?.access_token) {
      loadIntegrationStatus();
    }
  }, [visible, session?.access_token]);

  const loadIntegrationStatus = async () => {
    if (!session?.access_token) return;
    
    try {
      setIsLoading(true);
      const status = await CanvasService.getIntegrationStatus(session.access_token);
      setIntegrationStatus(status);
      
      if (status.connected) {
        setCurrentStep('success');
      }
    } catch (error) {
      console.error('Error loading Canvas integration status:', error);
      Alert.alert('Error', 'Failed to load Canvas integration status');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadIntegrationStatus();
    setRefreshing(false);
  };

  const generateQRCode = async () => {
    if (!session?.access_token) return;

    try {
      setIsGeneratingQR(true);
      const qrData = await CanvasService.generateConnectionCode(session.access_token);
      setQrData(qrData);
      setCurrentStep('qr');
    } catch (error) {
      console.error('Error generating QR code:', error);
      Alert.alert('Error', 'Failed to generate connection code');
    } finally {
      setIsGeneratingQR(false);
    }
  };

  const renderOverview = () => (
    <ScrollView 
      style={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor="#FFFFFF" />
      }
    >
      {/* Header */}
      <View style={[styles.header, { backgroundColor: currentTheme.colors.primary }]}>
        <BookOpen size={32} color="white" />
        <Text style={styles.headerTitle}>Canvas Integration</Text>
        <Text style={styles.headerSubtitle}>
          Seamlessly sync your Canvas assignments to PulsePlan
        </Text>
      </View>

      {/* Status Card */}
      {integrationStatus && (
        <View style={[styles.statusCard, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
          <View style={styles.statusHeader}>
            <View style={styles.statusIcon}>
              {integrationStatus.connected ? (
                <CheckCircle size={24} color={currentTheme.colors.success} />
              ) : (
                <AlertCircle size={24} color={currentTheme.colors.textSecondary} />
              )}
            </View>
            <View style={styles.statusInfo}>
              <Text style={[styles.statusTitle, { color: currentTheme.colors.textPrimary }]}>
                {integrationStatus.connected ? 'Connected' : 'Not Connected'}
              </Text>
              <Text style={[styles.statusSubtitle, { color: currentTheme.colors.textSecondary }]}>
                {integrationStatus.connected 
                  ? `Last sync: ${CanvasService.formatLastSync(integrationStatus.lastSync)}`
                  : 'Connect your Chrome extension to sync assignments'
                }
              </Text>
            </View>
          </View>

          {integrationStatus.connected && (
            <View style={[styles.statsContainer, { borderTopColor: currentTheme.colors.border }]}>
              <View style={styles.statItem}>
                <Text style={[styles.statValue, { color: currentTheme.colors.primary }]}>
                  {integrationStatus.totalCanvasTasks}
                </Text>
                <Text style={[styles.statLabel, { color: currentTheme.colors.textSecondary }]}>
                  Assignments Synced
                </Text>
              </View>
              <View style={styles.statItem}>
                <Text style={[styles.statValue, { color: currentTheme.colors.primary }]}>
                  {integrationStatus.extensionVersion || 'Unknown'}
                </Text>
                <Text style={[styles.statLabel, { color: currentTheme.colors.textSecondary }]}>
                  Extension Version
                </Text>
              </View>
            </View>
          )}
        </View>
      )}

      {/* How it works */}
      <View style={[styles.section, { backgroundColor: currentTheme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: currentTheme.colors.textPrimary }]}>
          How it works
        </Text>
        
        <View style={styles.stepsList}>
          <View style={styles.stepItem}>
            <View style={[styles.stepIcon, { backgroundColor: currentTheme.colors.primary }]}>
              <Monitor size={20} color="white" />
            </View>
            <View style={styles.stepContent}>
              <Text style={[styles.stepTitle, { color: currentTheme.colors.textPrimary }]}>
                Install Chrome Extension
              </Text>
              <Text style={[styles.stepDescription, { color: currentTheme.colors.textSecondary }]}>
                Add the PulsePlan Canvas Sync extension to your Chrome browser
              </Text>
            </View>
          </View>

          <View style={styles.stepItem}>
            <View style={[styles.stepIcon, { backgroundColor: currentTheme.colors.primary }]}>
              <QrCode size={20} color="white" />
            </View>
            <View style={styles.stepContent}>
              <Text style={[styles.stepTitle, { color: currentTheme.colors.textPrimary }]}>
                Scan QR Code
              </Text>
              <Text style={[styles.stepDescription, { color: currentTheme.colors.textSecondary }]}>
                Use the extension to scan the QR code and connect to your account
              </Text>
            </View>
          </View>

          <View style={styles.stepItem}>
            <View style={[styles.stepIcon, { backgroundColor: currentTheme.colors.primary }]}>
              <Zap size={20} color="white" />
            </View>
            <View style={styles.stepContent}>
              <Text style={[styles.stepTitle, { color: currentTheme.colors.textPrimary }]}>
                Auto-Sync Assignments
              </Text>
              <Text style={[styles.stepDescription, { color: currentTheme.colors.textSecondary }]}>
                Your Canvas assignments will automatically sync to PulsePlan
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* Action Button */}
      <View style={styles.actionContainer}>
        {integrationStatus?.connected ? (
          <TouchableOpacity
            style={[styles.actionButton, styles.refreshButton, { borderColor: currentTheme.colors.primary }]}
            onPress={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? (
              <ActivityIndicator size="small" color={currentTheme.colors.primary} />
            ) : (
              <RefreshCw size={20} color={currentTheme.colors.primary} />
            )}
            <Text style={[styles.actionButtonText, { color: currentTheme.colors.primary }]}>
              {refreshing ? 'Refreshing...' : 'Refresh Status'}
            </Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.actionButton, styles.connectButton, { backgroundColor: currentTheme.colors.primary }]}
            onPress={generateQRCode}
            disabled={isGeneratingQR}
          >
            {isGeneratingQR ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <QrCode size={20} color="white" />
            )}
            <Text style={[styles.actionButtonText, { color: 'white' }]}>
              {isGeneratingQR ? 'Generating...' : 'Connect Canvas'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );

  const renderQRCode = () => (
    <ScrollView style={styles.content}>
      <View style={styles.qrContainer}>
        <Text style={[styles.qrTitle, { color: currentTheme.colors.textPrimary }]}>
          Scan with Chrome Extension
        </Text>
        <Text style={[styles.qrSubtitle, { color: currentTheme.colors.textSecondary }]}>
          Open the PulsePlan extension in Chrome and scan this QR code
        </Text>

        {qrData && (
          <View style={[styles.qrCodeContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <Image
              source={{ uri: qrData.qrCodeUrl }}
              style={styles.qrCodeImage}
              resizeMode="contain"
            />
          </View>
        )}

        <View style={[styles.qrInfo, { backgroundColor: currentTheme.colors.card }]}>
          <Clock size={16} color={currentTheme.colors.textSecondary} />
          <Text style={[styles.qrInfoText, { color: currentTheme.colors.textSecondary }]}>
            This code expires in 10 minutes
          </Text>
        </View>

        <TouchableOpacity
          style={[styles.actionButton, styles.refreshButton, { borderColor: currentTheme.colors.primary }]}
          onPress={generateQRCode}
          disabled={isGeneratingQR}
        >
          <RefreshCw size={20} color={currentTheme.colors.primary} />
          <Text style={[styles.actionButtonText, { color: currentTheme.colors.primary }]}>
            Generate New Code
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderSuccess = () => (
    <ScrollView style={styles.content}>
      <View style={styles.successContainer}>
        <View style={[styles.successIcon, { backgroundColor: currentTheme.colors.success }]}>
          <CheckCircle size={48} color="white" />
        </View>
        
        <Text style={[styles.successTitle, { color: currentTheme.colors.textPrimary }]}>
          Canvas Connected!
        </Text>
        
        <Text style={[styles.successSubtitle, { color: currentTheme.colors.textSecondary }]}>
          Your Canvas assignments will now automatically sync to PulsePlan
        </Text>

        {integrationStatus && (
          <View style={[styles.successStats, { backgroundColor: currentTheme.colors.surface }]}>
            <View style={styles.successStatItem}>
              <Text style={[styles.successStatValue, { color: currentTheme.colors.primary }]}>
                {integrationStatus.totalCanvasTasks}
              </Text>
              <Text style={[styles.successStatLabel, { color: currentTheme.colors.textSecondary }]}>
                Assignments Synced
              </Text>
            </View>
            <View style={styles.successStatItem}>
              <Text style={[styles.successStatValue, { color: currentTheme.colors.primary }]}>
                {CanvasService.formatLastSync(integrationStatus.lastSync)}
              </Text>
              <Text style={[styles.successStatLabel, { color: currentTheme.colors.textSecondary }]}>
                Last Sync
              </Text>
            </View>
          </View>
        )}

        <TouchableOpacity
          style={[styles.actionButton, styles.connectButton, { backgroundColor: currentTheme.colors.primary }]}
          onPress={onClose}
        >
          <Text style={[styles.actionButtonText, { color: 'white' }]}>
            Done
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        {/* Header */}
        <View style={[styles.modalHeader, { borderBottomColor: currentTheme.colors.border }]}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color={currentTheme.colors.textPrimary} />
          </TouchableOpacity>
          <Text style={[styles.modalTitle, { color: currentTheme.colors.textPrimary }]}>
            Canvas Integration
          </Text>
          <View style={styles.placeholder} />
        </View>

        {/* Content */}
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={currentTheme.colors.primary} />
            <Text style={[styles.loadingText, { color: currentTheme.colors.textSecondary }]}>
              Loading integration status...
            </Text>
          </View>
        ) : (
          <>
            {currentStep === 'overview' && renderOverview()}
            {currentStep === 'qr' && renderQRCode()}
            {currentStep === 'success' && renderSuccess()}
          </>
        )}
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
  },
  closeButton: {
    padding: 4,
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
  },
  header: {
    padding: 24,
    alignItems: 'center',
    margin: 20,
    borderRadius: 16,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: 'white',
    marginTop: 12,
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 22,
  },
  statusCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 16,
    borderWidth: 1,
    overflow: 'hidden',
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
  },
  statusIcon: {
    marginRight: 16,
  },
  statusInfo: {
    flex: 1,
  },
  statusTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  statusSubtitle: {
    fontSize: 14,
    lineHeight: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    borderTopWidth: 1,
    paddingTop: 16,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
  section: {
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 16,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
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
  stepIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  stepDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  actionContainer: {
    padding: 20,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 8,
  },
  connectButton: {
    // backgroundColor set dynamically
  },
  refreshButton: {
    borderWidth: 2,
    backgroundColor: 'transparent',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  qrContainer: {
    padding: 20,
    alignItems: 'center',
  },
  qrTitle: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
    textAlign: 'center',
  },
  qrSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  qrCodeContainer: {
    padding: 20,
    borderRadius: 16,
    marginBottom: 24,
  },
  qrCodeImage: {
    width: 200,
    height: 200,
  },
  qrInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 32,
    gap: 8,
  },
  qrInfoText: {
    fontSize: 14,
  },
  successContainer: {
    padding: 20,
    alignItems: 'center',
  },
  successIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  successTitle: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  successSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  successStats: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 20,
    marginBottom: 32,
    width: '100%',
  },
  successStatItem: {
    flex: 1,
    alignItems: 'center',
  },
  successStatValue: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 4,
  },
  successStatLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
}); 