import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { ChevronLeft, Users, Check } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { ContactsService } from '@/services/contactsService';

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

interface ConnectionStatus {
  connected: boolean;
  providers: Array<{
    provider: 'google' | 'apple';
    email: string;
    connectedAt: string;
    expiresAt?: string;
    isActive: boolean;
  }>;
}

export default function ContactsIntegrationScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const { user } = useAuth();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnecting, setIsConnecting] = useState<{ google?: boolean; apple?: boolean }>({});

  // Load connection status on component mount and when screen comes into focus
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
      const status = await ContactsService.getConnectionStatus(user.id);
      setConnectionStatus(status);
    } catch (error) {
      console.error('Error loading connection status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleConnect = async () => {
    if (!user?.id) {
      Alert.alert('Error', 'Please sign in to connect your Google account');
      return;
    }

    try {
      setIsConnecting({ ...isConnecting, google: true });
      await ContactsService.connectGoogle(user.id);
      // Connection status will be updated when user returns from OAuth flow
    } catch (error) {
      console.error('Error connecting Google:', error);
      Alert.alert('Error', 'Failed to connect Google account. Please try again.');
    } finally {
      setIsConnecting({ ...isConnecting, google: false });
    }
  };

  const handleAppleConnect = async () => {
    if (!user?.id) {
      Alert.alert('Error', 'Please sign in to connect your Apple account');
      return;
    }

    try {
      setIsConnecting({ ...isConnecting, apple: true });
      // TODO: Implement Apple Contacts integration
      Alert.alert('Coming Soon', 'Apple Contacts integration is coming soon!');
    } catch (error) {
      console.error('Error connecting Apple:', error);
      Alert.alert('Error', 'Failed to connect Apple account. Please try again.');
    } finally {
      setIsConnecting({ ...isConnecting, apple: false });
    }
  };

  // Check if a provider is connected
  const isProviderConnected = (provider: 'google' | 'apple'): boolean => {
    return connectionStatus?.providers?.some(p => p.provider === provider && p.isActive) || false;
  };

  // Get provider email if connected
  const getProviderEmail = (provider: 'google' | 'apple'): string | undefined => {
    return connectionStatus?.providers?.find(p => p.provider === provider && p.isActive)?.email;
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Contacts</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={[styles.promoSection, { backgroundColor: currentTheme.colors.surface }]}>
          <View style={[styles.promoIconContainer, { backgroundColor: currentTheme.colors.background }]}>
            <Users size={32} color={currentTheme.colors.textPrimary} />
          </View>
          <Text style={[styles.promoTitle, { color: currentTheme.colors.textPrimary }]}>Connect your contacts</Text>
          <Text style={[styles.promoDescription, { color: currentTheme.colors.textSecondary }]}>
            Connect your Google and Apple contacts to let PulsePlan access your address book. This enables AI-powered contact management, smart messaging, and seamless communication.
          </Text>
        </View>

        <View style={styles.sectionContainer}>
          <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>SIGN IN WITH YOUR PROVIDER</Text>
          <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface }]}>
              <SettingsRow 
                icon={<Image source={require('@/assets/images/applecontacts.webp')} style={styles.providerIcon} />} 
                title="Add Apple Contacts" 
                onPress={handleAppleConnect}
                isConnected={isProviderConnected('apple')}
                isLoading={isConnecting.apple || isLoading}
              />
            <SettingsRow 
              icon={<Image source={require('@/assets/images/googlecontacts.webp')} style={styles.providerIcon} />} 
              title="Add Google Contacts" 
              onPress={handleGoogleConnect}
              isConnected={isProviderConnected('google')}
              isLoading={isConnecting.google || isLoading}
            />
            <View style={[styles.separator, { backgroundColor: currentTheme.colors.border }]} />
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
    paddingHorizontal: 16,
    paddingVertical: 12,
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
}); 