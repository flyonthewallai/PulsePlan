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
  Switch,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  X,
  Calendar,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  ExternalLink,
  Clock,
  Users,
  Sync,
  Unlink,
} from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { CalendarService, ConnectionStatus, SyncStatus } from '../services/calendarService';

interface CalendarIntegrationModalProps {
  visible: boolean;
  onClose: () => void;
}

interface ProviderCardProps {
  provider: 'google' | 'microsoft';
  title: string;
  description: string;
  icon: React.ReactNode;
  connected: boolean;
  email?: string;
  connectedAt?: string;
  isActive?: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onSync: () => void;
  isLoading: boolean;
  isSyncing: boolean;
}

const ProviderCard: React.FC<ProviderCardProps> = ({
  provider,
  title,
  description,
  icon,
  connected,
  email,
  connectedAt,
  isActive,
  onConnect,
  onDisconnect,
  onSync,
  isLoading,
  isSyncing,
}) => {
  const { currentTheme } = useTheme();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <View style={[styles.providerCard, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
      <View style={styles.providerHeader}>
        <View style={styles.providerInfo}>
          <View style={[styles.providerIcon, { backgroundColor: currentTheme.colors.card }]}>
            {icon}
          </View>
          <View style={styles.providerDetails}>
            <Text style={[styles.providerTitle, { color: currentTheme.colors.textPrimary }]}>
              {title}
            </Text>
            <Text style={[styles.providerDescription, { color: currentTheme.colors.textSecondary }]}>
              {description}
            </Text>
          </View>
        </View>
        
        <View style={styles.providerStatus}>
          {connected ? (
            <View style={styles.connectedBadge}>
              <CheckCircle size={16} color={currentTheme.colors.success} />
              <Text style={[styles.statusText, { color: currentTheme.colors.success }]}>
                Connected
              </Text>
            </View>
          ) : (
            <View style={styles.disconnectedBadge}>
              <AlertCircle size={16} color={currentTheme.colors.textSecondary} />
              <Text style={[styles.statusText, { color: currentTheme.colors.textSecondary }]}>
                Not Connected
              </Text>
            </View>
          )}
        </View>
      </View>

      {connected && email && (
        <View style={[styles.connectionDetails, { backgroundColor: currentTheme.colors.card }]}>
          <View style={styles.connectionInfo}>
            <Text style={[styles.connectionEmail, { color: currentTheme.colors.textPrimary }]}>
              {email}
            </Text>
            {connectedAt && (
              <Text style={[styles.connectionDate, { color: currentTheme.colors.textSecondary }]}>
                Connected on {formatDate(connectedAt)}
              </Text>
            )}
            {!isActive && (
              <Text style={[styles.expiredText, { color: currentTheme.colors.error }]}>
                Connection expired - please reconnect
              </Text>
            )}
          </View>
        </View>
      )}

      <View style={styles.providerActions}>
        {connected ? (
          <>
            <TouchableOpacity
              style={[
                styles.actionButton,
                styles.syncButton,
                { backgroundColor: currentTheme.colors.primary },
                isSyncing && styles.disabledButton,
              ]}
              onPress={onSync}
              disabled={isSyncing || !isActive}
            >
              {isSyncing ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Sync size={16} color="white" />
              )}
              <Text style={[styles.actionButtonText, { color: 'white' }]}>
                {isSyncing ? 'Syncing...' : 'Sync Now'}
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[
                styles.actionButton,
                styles.disconnectButton,
                { borderColor: currentTheme.colors.error },
                isLoading && styles.disabledButton,
              ]}
              onPress={onDisconnect}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color={currentTheme.colors.error} />
              ) : (
                <Unlink size={16} color={currentTheme.colors.error} />
              )}
              <Text style={[styles.actionButtonText, { color: currentTheme.colors.error }]}>
                Disconnect
              </Text>
            </TouchableOpacity>
          </>
        ) : (
          <TouchableOpacity
            style={[
              styles.actionButton,
              styles.connectButton,
              { backgroundColor: currentTheme.colors.primary },
              isLoading && styles.disabledButton,
            ]}
            onPress={onConnect}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <ExternalLink size={16} color="white" />
            )}
            <Text style={[styles.actionButtonText, { color: 'white' }]}>
              Connect {title}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

export default function CalendarIntegrationModal({ visible, onClose }: CalendarIntegrationModalProps) {
  const { currentTheme } = useTheme();
  const { user } = useAuth();
  
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStates, setLoadingStates] = useState({
    google: false,
    microsoft: false,
  });
  const [syncingStates, setSyncingStates] = useState({
    google: false,
    microsoft: false,
  });
  const [autoSync, setAutoSync] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (visible && user?.id) {
      loadConnectionStatus();
      loadSyncStatus();
    }
  }, [visible, user?.id]);

  const loadConnectionStatus = async () => {
    if (!user?.id) return;
    
    try {
      setIsLoading(true);
      const status = await CalendarService.getConnectionStatus(user.id);
      setConnectionStatus(status);
    } catch (error) {
      console.error('Error loading connection status:', error);
      
      // Provide default empty status if server is not available
      setConnectionStatus({
        connected: false,
        providers: []
      });
      
      // Show a more user-friendly error message
      Alert.alert(
        'Connection Error', 
        'Unable to check calendar connection status. Please ensure the server is running and try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const loadSyncStatus = async () => {
    if (!user?.id) return;
    
    try {
      const status = await CalendarService.getSyncStatus(user.id);
      setSyncStatus(status);
    } catch (error) {
      console.error('Error loading sync status:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([loadConnectionStatus(), loadSyncStatus()]);
    setRefreshing(false);
  };

  const handleConnect = async (provider: 'google' | 'microsoft') => {
    if (!user?.id) return;

    try {
      setLoadingStates(prev => ({ ...prev, [provider]: true }));
      
      if (provider === 'google') {
        await CalendarService.connectGoogle(user.id);
      } else {
        await CalendarService.connectMicrosoft(user.id);
      }
    } catch (error) {
      console.error(`Error connecting ${provider}:`, error);
      Alert.alert('Connection Error', `Failed to connect ${provider === 'google' ? 'Google Calendar' : 'Outlook Calendar'}`);
    } finally {
      setLoadingStates(prev => ({ ...prev, [provider]: false }));
    }
  };

  const handleDisconnect = async (provider: 'google' | 'microsoft') => {
    if (!user?.id) return;

    Alert.alert(
      'Disconnect Calendar',
      `Are you sure you want to disconnect ${provider === 'google' ? 'Google Calendar' : 'Outlook Calendar'}? This will stop syncing your events.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Disconnect',
          style: 'destructive',
          onPress: async () => {
            try {
              setLoadingStates(prev => ({ ...prev, [provider]: true }));
              
              if (provider === 'google') {
                await CalendarService.disconnectGoogle(user.id);
              } else {
                await CalendarService.disconnectMicrosoft(user.id);
              }
              
              await loadConnectionStatus();
              Alert.alert('Success', `${provider === 'google' ? 'Google Calendar' : 'Outlook Calendar'} disconnected successfully`);
            } catch (error) {
              console.error(`Error disconnecting ${provider}:`, error);
              Alert.alert('Error', `Failed to disconnect ${provider === 'google' ? 'Google Calendar' : 'Outlook Calendar'}`);
            } finally {
              setLoadingStates(prev => ({ ...prev, [provider]: false }));
            }
          },
        },
      ]
    );
  };

  const handleSync = async (provider: 'google' | 'microsoft') => {
    if (!user?.id) return;

    try {
      setSyncingStates(prev => ({ ...prev, [provider]: true }));
      
      const result = await CalendarService.syncAllCalendars(user.id, {
        providers: [provider],
        syncPeriodDays: 30,
        includeAllCalendars: true,
      });

      if (result.success) {
        Alert.alert(
          'Sync Complete',
          `Successfully synced ${result.syncedEvents} events from ${provider === 'google' ? 'Google Calendar' : 'Outlook Calendar'}`
        );
        await loadSyncStatus();
      } else {
        Alert.alert(
          'Sync Issues',
          `Sync completed with some issues. ${result.syncedEvents} events synced. ${result.errors.length} errors occurred.`
        );
      }
    } catch (error) {
      console.error(`Error syncing ${provider}:`, error);
      Alert.alert('Sync Error', `Failed to sync ${provider === 'google' ? 'Google Calendar' : 'Outlook Calendar'}`);
    } finally {
      setSyncingStates(prev => ({ ...prev, [provider]: false }));
    }
  };

  const handleSyncAll = async () => {
    if (!user?.id) return;

    const connectedProviders = connectionStatus?.providers
      .filter(p => p.isActive)
      .map(p => p.provider) || [];

    if (connectedProviders.length === 0) {
      Alert.alert('No Connections', 'Please connect at least one calendar service to sync');
      return;
    }

    try {
      setSyncingStates({ google: true, microsoft: true });
      
      const result = await CalendarService.syncAllCalendars(user.id, {
        providers: connectedProviders,
        syncPeriodDays: 30,
        includeAllCalendars: true,
      });

      if (result.success) {
        Alert.alert(
          'Sync Complete',
          `Successfully synced ${result.syncedEvents} events from all connected calendars`
        );
      } else {
        Alert.alert(
          'Sync Issues',
          `Sync completed with some issues. ${result.syncedEvents} events synced. ${result.errors.length} errors occurred.`
        );
      }
      
      await loadSyncStatus();
    } catch (error) {
      console.error('Error syncing all calendars:', error);
      Alert.alert('Sync Error', 'Failed to sync calendars');
    } finally {
      setSyncingStates({ google: false, microsoft: false });
    }
  };

  const getProviderConnection = (provider: 'google' | 'microsoft') => {
    return connectionStatus?.providers.find(p => p.provider === provider);
  };

  const formatLastSync = (lastSyncAt: string | null) => {
    if (!lastSyncAt) return 'Never synced';
    
    const date = new Date(lastSyncAt);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    return `${diffDays} days ago`;
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <LinearGradient
          colors={[currentTheme.colors.primary + '20', currentTheme.colors.background]}
          style={styles.header}
        >
          <View style={styles.headerContent}>
            <View style={styles.headerLeft}>
              <Calendar size={24} color={currentTheme.colors.primary} />
              <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
                Calendar Integration
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color={currentTheme.colors.textSecondary} />
            </TouchableOpacity>
          </View>
        </LinearGradient>

        <ScrollView
          style={styles.content}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor="#FFFFFF"
            />
          }
        >
          <Text style={[styles.sectionDescription, { color: currentTheme.colors.textSecondary }]}>
            Connect your calendar services to automatically sync events with PulsePlan. 
            Your events will be imported and kept up to date.
          </Text>

          {/* Sync Status Section */}
          {syncStatus && (
            <View style={[styles.syncStatusCard, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
              <View style={styles.syncStatusHeader}>
                <Clock size={20} color={currentTheme.colors.textPrimary} />
                <Text style={[styles.syncStatusTitle, { color: currentTheme.colors.textPrimary }]}>
                  Sync Status
                </Text>
              </View>
              
              <View style={styles.syncStatusContent}>
                <View style={styles.syncStatusRow}>
                  <Text style={[styles.syncStatusLabel, { color: currentTheme.colors.textSecondary }]}>
                    Last Sync:
                  </Text>
                  <Text style={[styles.syncStatusValue, { color: currentTheme.colors.textPrimary }]}>
                    {formatLastSync(syncStatus.last_sync_at)}
                  </Text>
                </View>
                
                <View style={styles.syncStatusRow}>
                  <Text style={[styles.syncStatusLabel, { color: currentTheme.colors.textSecondary }]}>
                    Total Events:
                  </Text>
                  <Text style={[styles.syncStatusValue, { color: currentTheme.colors.textPrimary }]}>
                    {syncStatus.synced_events_count}
                  </Text>
                </View>
                
                <View style={styles.syncStatusRow}>
                  <Text style={[styles.syncStatusLabel, { color: currentTheme.colors.textSecondary }]}>
                    Google Events:
                  </Text>
                  <Text style={[styles.syncStatusValue, { color: currentTheme.colors.textPrimary }]}>
                    {syncStatus.google_events}
                  </Text>
                </View>
                
                <View style={styles.syncStatusRow}>
                  <Text style={[styles.syncStatusLabel, { color: currentTheme.colors.textSecondary }]}>
                    Outlook Events:
                  </Text>
                  <Text style={[styles.syncStatusValue, { color: currentTheme.colors.textPrimary }]}>
                    {syncStatus.microsoft_events}
                  </Text>
                </View>
              </View>

              <TouchableOpacity
                style={[styles.syncAllButton, { backgroundColor: currentTheme.colors.primary }]}
                onPress={handleSyncAll}
                disabled={syncingStates.google || syncingStates.microsoft}
              >
                {(syncingStates.google || syncingStates.microsoft) ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <RefreshCw size={16} color="white" />
                )}
                <Text style={[styles.syncAllButtonText, { color: 'white' }]}>
                  {(syncingStates.google || syncingStates.microsoft) ? 'Syncing...' : 'Sync All Calendars'}
                </Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Google Calendar Provider */}
          <ProviderCard
            provider="google"
            title="Google Calendar"
            description="Sync events from your Google Calendar"
            icon={<Calendar size={20} color="#4285F4" />}
            connected={!!getProviderConnection('google')}
            email={getProviderConnection('google')?.email}
            connectedAt={getProviderConnection('google')?.connectedAt}
            isActive={getProviderConnection('google')?.isActive}
            onConnect={() => handleConnect('google')}
            onDisconnect={() => handleDisconnect('google')}
            onSync={() => handleSync('google')}
            isLoading={loadingStates.google}
            isSyncing={syncingStates.google}
          />

          {/* Microsoft Calendar Provider */}
          <ProviderCard
            provider="microsoft"
            title="Outlook Calendar"
            description="Sync events from your Outlook/Microsoft Calendar"
            icon={<Calendar size={20} color="#0078D4" />}
            connected={!!getProviderConnection('microsoft')}
            email={getProviderConnection('microsoft')?.email}
            connectedAt={getProviderConnection('microsoft')?.connectedAt}
            isActive={getProviderConnection('microsoft')?.isActive}
            onConnect={() => handleConnect('microsoft')}
            onDisconnect={() => handleDisconnect('microsoft')}
            onSync={() => handleSync('microsoft')}
            isLoading={loadingStates.microsoft}
            isSyncing={syncingStates.microsoft}
          />

          {/* Settings Section */}
          <View style={[styles.settingsCard, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
            <View style={styles.settingsHeader}>
              <Settings size={20} color={currentTheme.colors.textPrimary} />
              <Text style={[styles.settingsTitle, { color: currentTheme.colors.textPrimary }]}>
                Sync Settings
              </Text>
            </View>
            
            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={[styles.settingLabel, { color: currentTheme.colors.textPrimary }]}>
                  Auto Sync
                </Text>
                <Text style={[styles.settingDescription, { color: currentTheme.colors.textSecondary }]}>
                  Automatically sync calendars in the background
                </Text>
              </View>
              <Switch
                value={autoSync}
                onValueChange={setAutoSync}
                trackColor={{ false: currentTheme.colors.border, true: currentTheme.colors.primary + '40' }}
                thumbColor={autoSync ? currentTheme.colors.primary : currentTheme.colors.textSecondary}
              />
            </View>
          </View>

          {/* Help Section */}
          <View style={[styles.helpCard, { backgroundColor: currentTheme.colors.card }]}>
            <Text style={[styles.helpTitle, { color: currentTheme.colors.textPrimary }]}>
              How it works
            </Text>
            <Text style={[styles.helpText, { color: currentTheme.colors.textSecondary }]}>
              • Connect your calendar services using secure OAuth authentication{'\n'}
              • Your events are automatically imported and kept in sync{'\n'}
              • PulsePlan can create events in your external calendars{'\n'}
              • All data is encrypted and stored securely
            </Text>
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
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginLeft: 12,
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  sectionDescription: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 24,
  },
  syncStatusCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 20,
  },
  syncStatusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  syncStatusTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 8,
  },
  syncStatusContent: {
    marginBottom: 16,
  },
  syncStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  syncStatusLabel: {
    fontSize: 14,
  },
  syncStatusValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  syncAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  syncAllButtonText: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  providerCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  providerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  providerInfo: {
    flexDirection: 'row',
    flex: 1,
  },
  providerIcon: {
    width: 40,
    height: 40,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  providerDetails: {
    flex: 1,
  },
  providerTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  providerDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  providerStatus: {
    marginLeft: 12,
  },
  connectedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  disconnectedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  connectionDetails: {
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  connectionInfo: {
    flex: 1,
  },
  connectionEmail: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
  },
  connectionDate: {
    fontSize: 12,
  },
  expiredText: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 4,
  },
  providerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  connectButton: {
    // backgroundColor set dynamically
  },
  syncButton: {
    // backgroundColor set dynamically
  },
  disconnectButton: {
    borderWidth: 1,
    backgroundColor: 'transparent',
  },
  disabledButton: {
    opacity: 0.6,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  settingsCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 20,
  },
  settingsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  settingsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 8,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  helpCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  helpTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  helpText: {
    fontSize: 14,
    lineHeight: 22,
  },
}); 