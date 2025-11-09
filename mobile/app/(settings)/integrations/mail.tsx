import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { ChevronLeft, Mail as MailIcon, Check } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { GmailService } from '@/services/gmailService';
import { getApiUrl } from '@/config/api';

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

interface ConnectionStatus {
  connected: boolean;
  providers: Array<{
    provider: 'google' | 'microsoft';
    email: string;
    connectedAt: string;
    expiresAt?: string;
    isActive: boolean;
  }>;
}

export default function MailIntegrationScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const { user } = useAuth();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnecting, setIsConnecting] = useState<{ google?: boolean; microsoft?: boolean }>({});

  // Load connection status on component mount
  useEffect(() => {
    loadConnectionStatus();
  }, [user]);

  // Refresh connection status when screen comes into focus (after OAuth flow)
  useFocusEffect(
    React.useCallback(() => {
      if (user?.id) {
        loadConnectionStatus();
      }
    }, [user?.id])
  );

  const loadConnectionStatus = async () => {
    if (!user?.id) return;
    
    try {
      setIsLoading(true);
      // Use the same connection status endpoint as calendar since they share the same OAuth tokens
      const response = await fetch(getApiUrl(`/calendar/status/${user.id}`));
      if (response.ok) {
        const status = await response.json();
        setConnectionStatus(status);
      }
    } catch (error) {
      console.error('Error loading connection status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGmailConnect = async () => {
    if (!user?.id) {
      Alert.alert('Error', 'Please sign in to connect your Gmail account');
      return;
    }

    try {
      setIsConnecting({ ...isConnecting, google: true });
      // Use the Gmail-specific OAuth endpoint
      const url = `${getApiUrl('/gmail/auth')}?userId=${encodeURIComponent(user.id)}`;
      
      // Open OAuth URL
      if (typeof window !== 'undefined' && window.location) {
        window.location.href = url;
      } else {
        // For React Native
        const { Linking } = require('react-native');
        await Linking.openURL(url);
      }
    } catch (error) {
      console.error('Error connecting Gmail:', error);
      Alert.alert('Error', 'Failed to connect Gmail account. Please try again.');
    } finally {
      setIsConnecting({ ...isConnecting, google: false });
    }
  };

  const handleOutlookConnect = async () => {
    if (!user?.id) {
      Alert.alert('Error', 'Please sign in to connect your Outlook account');
      return;
    }

    try {
      setIsConnecting({ ...isConnecting, microsoft: true });
      const url = `${getApiUrl('/auth/microsoft')}?userId=${encodeURIComponent(user.id)}`;
      
      // Open OAuth URL
      if (typeof window !== 'undefined' && window.location) {
        window.location.href = url;
      } else {
        // For React Native
        const { Linking } = require('react-native');
        await Linking.openURL(url);
      }
    } catch (error) {
      console.error('Error connecting Outlook:', error);
      Alert.alert('Error', 'Failed to connect Outlook account. Please try again.');
    } finally {
      setIsConnecting({ ...isConnecting, microsoft: false });
    }
  };

  // Check if a provider is connected
  const isProviderConnected = (provider: 'google' | 'microsoft'): boolean => {
    return connectionStatus?.providers?.some(p => p.provider === provider && p.isActive) || false;
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
      <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Mail</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={[styles.promoSection, { backgroundColor: currentTheme.colors.surface }]}>
          <View style={[styles.promoIconContainer, { backgroundColor: currentTheme.colors.background }]}>
            <MailIcon size={32} color={currentTheme.colors.textPrimary} />
          </View>
          <Text style={[styles.promoTitle, { color: currentTheme.colors.textPrimary }]}>Connect your email</Text>
          <Text style={[styles.promoDescription, { color: currentTheme.colors.textSecondary }]}>
            PulsePlan can draft, send, and manage emails on your behalf. It can also help you stay on top of your inbox and important conversations.
          </Text>
        </View>

        <View style={styles.sectionContainer}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>SIGN IN WITH YOUR PROVIDER</Text>
          <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface }]}>
            <SettingsRow 
              icon={<Image source={require('@/assets/images/gmail.png')} style={styles.providerIcon} />} 
              title="Add Google Account" 
              onPress={handleGmailConnect}
              isConnected={isProviderConnected('google')}
              isLoading={isConnecting.google || isLoading}
            />
            <View style={[styles.separator, { backgroundColor: currentTheme.colors.border }]} />
            <SettingsRow 
              icon={<Image source={require('@/assets/images/applecalendar.png')} style={styles.providerIcon} />} 
              title="Add iCloud Account" 
              onPress={() => Alert.alert('Coming Soon', 'iCloud Mail integration is coming soon!')}
              isConnected={false}
              isLoading={false}
            />
            <View style={[styles.separator, { backgroundColor: currentTheme.colors.border }]} />
            <SettingsRow 
              icon={<Image source={require('@/assets/images/applecalendar.png')} style={styles.providerIcon} />} 
              title="Add Outlook Account" 
              onPress={handleOutlookConnect}
              isConnected={isProviderConnected('microsoft')}
              isLoading={isConnecting.microsoft || isLoading}
            />
          </View>
        </View>
      </ScrollView>
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
    paddingVertical: 20,
    paddingHorizontal: 16,
  },
  promoSection: {
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 32,
  },
  promoIconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  promoTitle: {
    fontSize: 22,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
  },
  promoDescription: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
  },
  sectionContainer: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '400',
    marginBottom: 8,
    marginLeft: 4,
    textTransform: 'uppercase'
  },
  sectionBody: {
    borderRadius: 10,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'transparent'
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  rowTitle: {
    fontSize: 17,
  },
  rowRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  providerIcon: {
    width: 28,
    height: 28,
    borderRadius: 4,
  },
  separator: {
    height: 1,
    marginLeft: 60, // Align with text, accounting for icon + gap
  },
}); 
 
 
 