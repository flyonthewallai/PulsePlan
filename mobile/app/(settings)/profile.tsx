import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, User, Mail, School, Calendar } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabase-rn';

const SettingsSection = ({ title, children }: { title: string; children: React.ReactNode }) => {
  const { currentTheme } = useTheme();
  return (
    <View style={styles.sectionContainer}>
      <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>{title.toUpperCase()}</Text>
              <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface }]}>
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
          <View style={styles.fieldContent}>
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
              placeholder={editable ? `Enter ${label.toLowerCase()}` : ''}
              placeholderTextColor={currentTheme.colors.textSecondary}
              multiline={false}
              returnKeyType="done"
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
  const [fullName, setFullName] = useState('');
  const [school, setSchool] = useState('');
  const [academicYear, setAcademicYear] = useState('');
  const [loading, setLoading] = useState(false);

  // Load profile data from database
  useEffect(() => {
    const loadProfile = async () => {
      if (!user?.id) return;

      try {
        const { data, error } = await supabase
          .from('users')
          .select('name, school, academic_year')
          .eq('id', user.id)
          .single();

        if (error) {
          console.error('Error loading profile:', error);
          return;
        }

        if (data) {
          setFullName(data.name || '');
          setSchool(data.school || '');
          setAcademicYear(data.academic_year || '');
        }
      } catch (error) {
        console.error('Error loading profile:', error);
      }
    };

    loadProfile();
  }, [user?.id]);

  const handleSave = async () => {
    if (!user?.id) {
      Alert.alert('Error', 'User not found');
      return;
    }

    setLoading(true);
    try {
      const { error } = await supabase
        .from('users')
        .update({
          name: fullName,
          school: school,
          academic_year: academicYear,
        })
        .eq('id', user.id);

      if (error) {
        throw error;
      }

      // Close the page after successful save
      router.back();
    } catch (error) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Profile</Text>
        <TouchableOpacity onPress={handleSave} disabled={loading}>
          <Text style={[styles.saveButton, { color: loading ? currentTheme.colors.textSecondary : currentTheme.colors.primary }]}>
            {loading ? 'Saving...' : 'Save'}
          </Text>
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
            isLastItem
          />
        </SettingsSection>

        <SettingsSection title="Academic Information">
          <ProfileField
            icon={<School size={24} color={currentTheme.colors.textSecondary} />}
            label="School"
            value={school}
            onChangeText={setSchool}
          />
          <ProfileField
            icon={<Calendar size={24} color={currentTheme.colors.textSecondary} />}
            label="Academic Year"
            value={academicYear}
            onChangeText={setAcademicYear}
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
  fieldContent: {
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
    marginRight: 0, // Extend to the end of the card
    opacity: 1,
  },
}); 