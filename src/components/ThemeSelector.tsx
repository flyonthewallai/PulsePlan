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

import { colors } from '../constants/theme';

interface Theme {
  id: string;
  name: string;
  primary: string;
  accent: string;
}

type ThemeSelectorProps = {
  themes: Theme[];
  selectedTheme: string;
  onSelectTheme: (themeId: string) => void;
};

export default function ThemeSelector({ 
  themes, 
  selectedTheme, 
  onSelectTheme 
}: ThemeSelectorProps) {
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
        >
          <LinearGradient
            colors={[theme.primary, theme.accent]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.themePreview}
          />
          <View style={styles.themeInfo}>
            <Text style={styles.themeName}>{theme.name}</Text>
            {selectedTheme === theme.id && (
              <View style={styles.selectedIndicator}>
                <Check size={12} color="#fff" />
              </View>
            )}
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
  themePreview: {
    width: 60,
    height: 60,
    borderRadius: 16,
    marginBottom: 8,
  },
  themeInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  themeName: {
    fontSize: 14,
    color: colors.textPrimary,
    marginRight: 4,
  },
  selectedIndicator: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: colors.primaryBlue,
    alignItems: 'center',
    justifyContent: 'center',
  },
});