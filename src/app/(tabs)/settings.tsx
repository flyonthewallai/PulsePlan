import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, Linking, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { 
  ChevronRight,
  LogOut,
  Trash2,
  Calendar, 
  Mails,
  BookText,
  GraduationCap,
  Info,
  Shield,
  FileText,
  HelpCircle,
  LifeBuoy,
  User,
  Palette,
  Clock,
  Star,
  School,
  Bell,
} from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { signOut } from '@/lib/supabase-rn';
import SubscriptionModal from '@/components/SubscriptionModal';

const SettingsSection = ({ title, children }: { title: string; children: React.ReactNode }) => {
    const { currentTheme } = useTheme();
    return (
        <View style={styles.sectionContainer}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>{title.toUpperCase()}</Text>
            <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface }]}>{children}</View>
        </View>
    );
};

const SettingsRow = ({
  icon,
  title,
  value,
  onPress,
  isDestructive = false,
  isLastItem = false,
}: {
  icon: React.ReactNode;
  title: string;
  value?: string;
  onPress?: () => void;
  isDestructive?: boolean;
  isLastItem?: boolean;
}) => {
  const { currentTheme } = useTheme();
  const titleColor = isDestructive ? currentTheme.colors.error : currentTheme.colors.textPrimary;

  return (
    <View>
      <TouchableOpacity style={styles.row} onPress={onPress}>
        <View style={styles.rowLeft}>
          {icon}
          <Text style={[styles.rowTitle, { color: titleColor }]}>{title}</Text>
        </View>
        <View style={styles.rowRight}>
          {value && <Text style={[styles.rowValue, { color: currentTheme.colors.textSecondary }]}>{value}</Text>}
          {onPress && !isDestructive && <ChevronRight color={currentTheme.colors.textSecondary} size={20} />}
        </View>
      </TouchableOpacity>
      {!isLastItem && (
        <View style={[styles.divider, { backgroundColor: currentTheme.colors.border }]} />
      )}
    </View>
  );
};

export default function SettingsScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const { user, refreshAuth, subscriptionPlan } = useAuth();
  const [isSubscriptionModalVisible, setIsSubscriptionModalVisible] = useState(false);

  const handleLogout = async () => {
    try {
      await signOut();
      await refreshAuth();
      router.replace('/auth');
    } catch (error) {
      Alert.alert('Logout Failed', (error as Error).message);
    }
  };

  const confirmLogout = () => {
    Alert.alert('Log Out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log Out', style: 'destructive', onPress: handleLogout },
    ]);
  };

  const confirmDeleteAccount = () => {
        Alert.alert(
      'Delete Account',
      'This action is irreversible. Are you sure you want to permanently delete your account?',
          [
            { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: () => Alert.alert("Coming soon.") },
      ]
    );
  };


  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Account</Text>
      </View>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
      >
        <SettingsSection title="Profile">
          <SettingsRow 
            icon={<User color={currentTheme.colors.textSecondary} size={24} />} 
            title="Profile" 
            value={user?.user_metadata?.full_name || user?.email}
            onPress={() => router.push('/(settings)/profile')} 
            isLastItem
          />
        </SettingsSection>
          
        <SettingsSection title="Preferences">
          <SettingsRow icon={<Bell color={currentTheme.colors.textSecondary} size={24} />} title="Reminders" onPress={() => router.push('/(settings)/reminders')} />
          <SettingsRow icon={<Palette color={currentTheme.colors.textSecondary} size={24} />} title="Appearance" onPress={() => router.push('/(settings)/appearance')} />
          <SettingsRow icon={<Clock color={currentTheme.colors.textSecondary} size={24} />} title="Study Times" onPress={() => router.push('/(settings)/study')} />
          <SettingsRow icon={<GraduationCap color={currentTheme.colors.textSecondary} size={24} />} title="Subjects" onPress={() => router.push('/(settings)/subjects')} isLastItem />
        </SettingsSection>
        
        <SettingsSection title="Integrations">
          <SettingsRow 
            icon={<Image source={require('@/assets/images/applecalendar.png')} style={{ width: 24, height: 24 }} />} 
            title="Calendar" 
            value="Not Connected" 
            onPress={() => router.push('/(settings)/integrations/calendar')} 
          />
          <SettingsRow 
            icon={<Image source={require('@/assets/images/gmail.png')} style={{ width: 24, height: 24 }} />} 
            title="Mail" 
            value="Not Connected" 
            onPress={() => router.push('/(settings)/integrations/mail')} 
          />
          <SettingsRow 
            icon={<Image source={require('@/assets/images/applecontacts.webp')} style={{ width: 24, height: 24 }} />} 
            title="Contacts" 
            value="Not Connected" 
            onPress={() => router.push('/(settings)/integrations/contacts')} 
          />
          <SettingsRow 
            icon={<Image source={require('@/assets/images/canvas.png')} style={{ width: 24, height: 24 }} />} 
            title="Canvas" 
            value="Not Connected" 
            onPress={() => router.push('/(settings)/integrations/canvas')} 
          />
          <SettingsRow 
            icon={<Image source={require('@/assets/images/notion.png')} style={{ width: 24, height: 24 }} />} 
            title="Notes" 
            value="Not Connected" 
            onPress={() => router.push('/(settings)/integrations/notes')} 
            isLastItem 
          />
        </SettingsSection>

        <SettingsSection title="About">
            {subscriptionPlan === 'free' && (
              <SettingsRow 
                icon={<Star color={currentTheme.colors.textSecondary} size={24} />} 
                title="Premium" 
                onPress={() => setIsSubscriptionModalVisible(true)} 
              />
            )}
            <SettingsRow icon={<LifeBuoy color={currentTheme.colors.textSecondary} size={24} />} title="Help Center" onPress={() => {}} />
            <SettingsRow 
              icon={<Shield color={currentTheme.colors.textSecondary} size={24} />} 
              title="Privacy Policy" 
              onPress={() => Linking.openURL('https://pulseplan.app/privacy')} 
            />
            <SettingsRow 
              icon={<FileText color={currentTheme.colors.textSecondary} size={24} />} 
              title="Terms of Service" 
              onPress={() => Linking.openURL('https://pulseplan.app/terms')} 
            />
            <SettingsRow 
              icon={<Info color={currentTheme.colors.textSecondary} size={24} />} 
              title="Contact Us" 
              onPress={() => Linking.openURL('mailto:hello@pulseplan.app')} 
              isLastItem={subscriptionPlan !== 'free'} 
            />
        </SettingsSection>
        
        <SettingsSection title="">
            <SettingsRow icon={<LogOut color={currentTheme.colors.textSecondary} size={24} />} title="Log Out" onPress={confirmLogout} />
            <SettingsRow icon={<Trash2 color={currentTheme.colors.error} size={24} />} title="Delete Account" onPress={confirmDeleteAccount} isDestructive isLastItem />
        </SettingsSection>
      </ScrollView>
      <SubscriptionModal 
        visible={isSubscriptionModalVisible}
        onClose={() => setIsSubscriptionModalVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  header: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    paddingTop: 20,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  sectionContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '400',
    marginLeft: 16,
    marginBottom: 8,
  },
  sectionBody: {
    borderRadius: 10,
    marginHorizontal: 16,
    overflow: 'hidden',
    borderWidth: 1,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  rowRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  rowTitle: {
    fontSize: 17,
  },
  rowValue: {
    fontSize: 17,
  },
  divider: {
    height: 1,
    marginLeft: 56, // This aligns with the text (icon width + gap)
    marginRight: 16,
    opacity: 1,
  },
});
 