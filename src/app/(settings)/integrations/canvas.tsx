import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Image, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { ChevronLeft, Check, BookOpen } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { CanvasService, CanvasIntegrationStatus } from '@/services/canvasService';
import CanvasAPIConnectionModal from '@/components/CanvasAPIConnectionModal';

// Simple SettingsRow component matching the design
const SettingsRow = ({
  icon,
  title,
  onPress,
  isConnected,
  isLoading,
}: {
  icon: React.ReactNode;
  title: string;
  onPress?: () => void;
  isConnected?: boolean;
  isLoading?: boolean;
}) => {
  const { currentTheme } = useTheme();
  return (
    <TouchableOpacity style={styles.row} onPress={onPress} disabled={isLoading}>
      <View style={styles.rowLeft}>
        {icon}
        <Text style={[styles.rowTitle, { color: currentTheme.colors.textPrimary }]}>{title}</Text>
      </View>
      <View style={styles.rowRight}>
        {isLoading ? (
          <Text style={[styles.statusText, { color: currentTheme.colors.textSecondary }]}>Loading...</Text>
        ) : isConnected ? (
          <Check size={20} color="#10B981" />
        ) : (
          <ChevronLeft color={currentTheme.colors.textSecondary} size={20} style={{ transform: [{ rotate: '180deg' }] }} />
        )}
      </View>
    </TouchableOpacity>
  );
};

export default function CanvasIntegrationScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const { user, session } = useAuth();
  
  const [integrationStatus, setIntegrationStatus] = useState<CanvasIntegrationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAPIModal, setShowAPIModal] = useState(false);

  // Load connection status on component mount and when screen comes into focus
  useEffect(() => {
    loadIntegrationStatus();
  }, [user]);

  // Refresh connection status when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      if (user?.id && session?.access_token) {
        loadIntegrationStatus();
      }
    }, [user?.id, session?.access_token])
  );

  const loadIntegrationStatus = async () => {
    if (!session?.access_token) return;
    
    try {
      setIsLoading(true);
      const status = await CanvasService.getIntegrationStatus(session.access_token);
      setIntegrationStatus(status);
    } catch (error) {
      console.error('Error loading Canvas integration status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAPIConnect = () => {
    setShowAPIModal(true);
  };

  const handleAPISuccess = () => {
    setShowAPIModal(false);
    loadIntegrationStatus(); // Refresh status after successful connection
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
      <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Canvas</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={[styles.promoSection, { backgroundColor: currentTheme.colors.surface }]}>
          <View style={[styles.promoIconContainer, { backgroundColor: currentTheme.colors.background }]}>
            <BookOpen size={32} color={currentTheme.colors.textPrimary} />
          </View>
          <Text style={[styles.promoTitle, { color: currentTheme.colors.textPrimary }]}>Connect your Canvas</Text>
          <Text style={[styles.promoDescription, { color: currentTheme.colors.textSecondary }]}>
            Connect your Canvas account to automatically sync assignments and due dates to PulsePlan. Stay on top of your coursework with intelligent scheduling.
          </Text>
        </View>

        <View style={styles.sectionContainer}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>CONNECTION METHODS</Text>
          <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface }]}>
            <SettingsRow 
              icon={<Image source={require('@/assets/images/canvas.png')} style={styles.providerIcon} />} 
              title="Connect with API Key" 
              onPress={handleAPIConnect}
              isConnected={integrationStatus?.connected}
              isLoading={isLoading}
            />
            <View style={[styles.separator, { backgroundColor: currentTheme.colors.border }]} />
          </View>
        </View>

        {integrationStatus?.connected && (
          <View style={styles.sectionContainer}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>SYNC STATUS</Text>
            <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.statusRow}>
                <Text style={[styles.statusLabel, { color: currentTheme.colors.textPrimary }]}>Assignments Synced</Text>
                <Text style={[styles.statusValue, { color: currentTheme.colors.primary }]}>
                  {integrationStatus.totalCanvasTasks}
                </Text>
              </View>
              <View style={[styles.separator, { backgroundColor: currentTheme.colors.border }]} />
              <View style={styles.statusRow}>
                <Text style={[styles.statusLabel, { color: currentTheme.colors.textPrimary }]}>Last Sync</Text>
                <Text style={[styles.statusValue, { color: currentTheme.colors.textSecondary }]}>
                  {CanvasService.formatLastSync(integrationStatus.lastSync)}
                </Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>

      <CanvasAPIConnectionModal
        visible={showAPIModal}
        onClose={() => setShowAPIModal(false)}
        onSuccess={handleAPISuccess}
      />
    </SafeAreaView>
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
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  scrollContent: {
    paddingVertical: 24,
  },
  promoSection: {
    marginHorizontal: 16,
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 32,
  },
  promoIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  promoTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  promoDescription: {
    fontSize: 15,
    lineHeight: 20,
    textAlign: 'center',
  },
  sectionContainer: {
    marginHorizontal: 16,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '400',
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  sectionBody: {
    borderRadius: 10,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  rowRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  rowTitle: {
    fontSize: 17,
    fontWeight: '400',
  },
  statusText: {
    fontSize: 15,
  },
  providerIcon: {
    width: 24,
    height: 24,
  },
  separator: {
    height: 1,
    marginLeft: 52,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  statusLabel: {
    fontSize: 16,
    fontWeight: '400',
  },
  statusValue: {
    fontSize: 16,
    fontWeight: '500',
  },
});