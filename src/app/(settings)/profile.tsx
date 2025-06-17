import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, User, Mail, Phone } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';

const SettingsSection = ({ title, children }: { title: string; children: React.ReactNode }) => {
  const { currentTheme } = useTheme();
  return (
    <View style={styles.sectionContainer}>
      <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>{title.toUpperCase()}</Text>
      <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
        {children}
      </View>
    </View>
  );
};

const ProfileField = ({
  icon,
  label,
  value,
  onChangeText,
  editable = true,
  isLastItem = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  onChangeText?: (text: string) => void;
  editable?: boolean;
  isLastItem?: boolean;
}) => {
  const { currentTheme } = useTheme();
  
  return (
    <View>
      <View style={styles.fieldContainer}>
        <View style={styles.fieldLeft}>
          {icon}
          <View>
            <Text style={[styles.fieldLabel, { color: currentTheme.colors.textSecondary }]}>{label}</Text>
            <TextInput
              value={value}
              onChangeText={onChangeText}
              style={[
                styles.fieldInput,
                { color: currentTheme.colors.textPrimary },
                !editable && { opacity: 0.5 }
              ]}
              editable={editable}
              placeholderTextColor={currentTheme.colors.textSecondary}
            />
          </View>
        </View>
      </View>
      {!isLastItem && (
        <View style={[styles.divider, { backgroundColor: currentTheme.colors.border }]} />
      )}
    </View>
  );
};

export default function ProfileScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.user_metadata?.full_name || '');
  const [phone, setPhone] = useState(user?.user_metadata?.phone || '');

  const handleSave = async () => {
    try {
      // TODO: Implement save functionality
      Alert.alert('Success', 'Profile updated successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to update profile');
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Profile</Text>
        <TouchableOpacity onPress={handleSave}>
          <Text style={[styles.saveButton, { color: currentTheme.colors.primary }]}>Save</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <SettingsSection title="Personal Information">
          <ProfileField
            icon={<User size={24} color={currentTheme.colors.textSecondary} />}
            label="Full Name"
            value={fullName}
            onChangeText={setFullName}
          />
          <ProfileField
            icon={<Mail size={24} color={currentTheme.colors.textSecondary} />}
            label="Email"
            value={user?.email || ''}
            editable={false}
          />
          <ProfileField
            icon={<Phone size={24} color={currentTheme.colors.textSecondary} />}
            label="Phone"
            value={phone}
            onChangeText={setPhone}
            isLastItem
          />
        </SettingsSection>
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
  saveButton: {
    fontSize: 17,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingVertical: 20,
  },
  sectionContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '400',
    marginBottom: 8,
    marginLeft: 16,
  },
  sectionBody: {
    borderRadius: 10,
    marginHorizontal: 16,
    overflow: 'hidden',
    borderWidth: 1,
  },
  fieldContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  fieldLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    flex: 1,
  },
  fieldLabel: {
    fontSize: 13,
    marginBottom: 4,
  },
  fieldInput: {
    fontSize: 17,
    padding: 0,
    margin: 0,
  },
  divider: {
    height: 1,
    marginLeft: 56,
    marginRight: 16,
    opacity: 1,
  },
}); 