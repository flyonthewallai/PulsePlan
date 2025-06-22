import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Check, Lock, Star } from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import SubscriptionModal from '@/components/SubscriptionModal';
import { Theme } from '@/contexts/ThemeContext';

export default function AppearanceScreen() {
  const router = useRouter();
  const { currentTheme, allThemes, setTheme } = useTheme();
  const { subscriptionPlan } = useAuth();
  const [isSubscriptionModalVisible, setIsSubscriptionModalVisible] = useState(false);

  const handleThemeChange = async (theme: Theme) => {
    try {
      if (theme.premium && subscriptionPlan !== 'premium') {
        setIsSubscriptionModalVisible(true);
        return;
      }
      await setTheme(theme.id);
    } catch (error) {
      console.error('Error changing theme:', error);
      Alert.alert('Error', 'Failed to change theme. Please try again.');
    }
  };

  const renderThemeCard = (theme: Theme) => {
    const isSelected = currentTheme.id === theme.id;
    const isLocked = theme.premium && subscriptionPlan !== 'premium';

    return (
      <TouchableOpacity
        key={theme.id}
        style={[
          styles.cardContainer,
          { backgroundColor: currentTheme.colors.surface }
        ]}
        onPress={() => handleThemeChange(theme)}
        activeOpacity={0.7}
      >
        <LinearGradient
          colors={[theme.colors.primary, theme.colors.accent]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.themePreview}
        />
        <View style={styles.themeInfo}>
          <Text style={[styles.themeName, { color: currentTheme.colors.textPrimary }]}>
            {theme.name}
          </Text>
          {theme.premium && (
             <View style={[styles.premiumBadge, { backgroundColor: theme.colors.accent }]}>
              <Star size={12} color="#FFFFFF" fill="#FFFFFF" />
            </View>
          )}
        </View>
        <View style={styles.selectionIndicator}>
          {isLocked ? (
            <Lock size={20} color={currentTheme.colors.textSecondary} />
          ) : isSelected ? (
            <View style={[styles.checkBadge, { backgroundColor: currentTheme.colors.primary }]}>
              <Check size={16} color="#FFFFFF" />
            </View>
          ) : (
            <View style={[styles.emptyCircle, { borderColor: currentTheme.colors.border }]} />
          )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Appearance</Text>
        <View style={{ width: 24 }} />
      </View>
      
      <ScrollView 
        contentContainerStyle={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
      >
        <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
          CHOOSE A THEME
        </Text>
        <View style={styles.listContainer}>
          {allThemes.map(renderThemeCard)}
        </View>
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
  scrollContainer: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 12,
    marginLeft: 8,
    textTransform: 'uppercase',
  },
  listContainer: {
    gap: 12,
  },
  cardContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    height: 80,
  },
  themePreview: {
    width: 48,
    height: 48,
    borderRadius: 8,
    marginRight: 16,
  },
  themeInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  themeName: {
    fontSize: 17,
    fontWeight: '500',
  },
  premiumBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectionIndicator: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
  },
}); 
 
 
 