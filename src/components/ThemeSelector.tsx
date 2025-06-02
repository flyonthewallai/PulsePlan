import React from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Check } from 'lucide-react-native';
import { Crown } from 'lucide-react-native';

import { Theme, useTheme } from '../contexts/ThemeContext';

type ThemeSelectorProps = {
  themes: Theme[];
  selectedTheme: string;
  onSelectTheme: (themeId: string) => void;
  isPremium?: boolean;
};

export default function ThemeSelector({ 
  themes, 
  selectedTheme, 
  onSelectTheme,
  isPremium = false
}: ThemeSelectorProps) {
  const { currentTheme } = useTheme();
  
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {themes.map(theme => (
        <TouchableOpacity
          key={theme.id}
          style={styles.themeCard}
          onPress={() => onSelectTheme(theme.id)}
          disabled={theme.premium && !isPremium}
        >
          <View style={styles.themePreviewContainer}>
            <LinearGradient
              colors={[theme.colors.primary, theme.colors.accent]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={[
                styles.themePreview,
                selectedTheme === theme.id && [styles.selectedThemePreview, { borderColor: currentTheme.colors.primary }]
              ]}
            />
            {theme.premium && (
              <View style={[styles.premiumBadge, { backgroundColor: currentTheme.colors.primary }]}>
                <Crown size={10} color="#FFD700" />
              </View>
            )}
            {selectedTheme === theme.id && (
              <View style={styles.selectedOverlay}>
                <Check size={16} color="#fff" />
              </View>
            )}
          </View>
          <View style={styles.themeInfo}>
            <Text style={[
              styles.themeName,
              { color: currentTheme.colors.textPrimary },
              theme.premium && !isPremium && { color: currentTheme.colors.textSecondary }
            ]}>
              {theme.name}
            </Text>
          </View>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
  },
  themeCard: {
    width: 80,
    marginRight: 16,
    alignItems: 'center',
  },
  themePreviewContainer: {
    position: 'relative',
    marginBottom: 8,
  },
  themePreview: {
    width: 60,
    height: 60,
    borderRadius: 16,
  },
  selectedThemePreview: {
    borderWidth: 2,
  },
  premiumBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    borderRadius: 8,
    padding: 2,
  },
  selectedOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  themeInfo: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 20,
    width: '100%',
  },
  themeName: {
    fontSize: 14,
    textAlign: 'center',
  },
});