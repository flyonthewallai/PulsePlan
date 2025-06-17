import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Mail as MailIcon } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';

const SettingsRow = ({
  icon,
  title,
  onPress,
}: {
  icon: React.ReactNode;
  title: string;
  onPress?: () => void;
}) => {
  const { currentTheme } = useTheme();
  return (
    <TouchableOpacity style={styles.row} onPress={onPress}>
      <View style={styles.rowLeft}>
        {icon}
        <Text style={[styles.rowTitle, { color: currentTheme.colors.textPrimary }]}>{title}</Text>
      </View>
      <ChevronLeft color={currentTheme.colors.textSecondary} size={20} style={{ transform: [{ rotate: '180deg' }] }} />
    </TouchableOpacity>
  );
};

export default function MailIntegrationScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();

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
          <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
            <SettingsRow 
              icon={<Image source={{ uri: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Gmail_Icon_%282020%29.svg/2560px-Gmail_Icon_%282020%29.svg.png' }} style={styles.providerIcon} />} 
              title="Add Google Account" 
              onPress={() => {}} 
            />
            <SettingsRow 
              icon={<Image source={{ uri: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Apple_Mail_icon.svg/2048px-Apple_Mail_icon.svg.png' }} style={styles.providerIcon} />} 
              title="Add iCloud Account" 
              onPress={() => {}} 
            />
            <SettingsRow 
              icon={<Image source={{ uri: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Microsoft_Outlook_2019-present.svg/2048px-Microsoft_Outlook_2019-present.svg.png' }} style={styles.providerIcon} />} 
              title="Add Outlook Account" 
              onPress={() => {}} 
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
    borderBottomWidth: 1,
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
    borderWidth: 1,
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
  providerIcon: {
    width: 28,
    height: 28,
    borderRadius: 4,
  }
}); 
 
 
 