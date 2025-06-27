import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X } from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';

const { width } = Dimensions.get('window');

interface SubjectColorPickerProps {
  visible: boolean;
  onClose: () => void;
  onSelectColor: (color: string) => void;
  currentColor: string;
  subjectName: string;
}

// Grouped by color families - darker, blue-tinted rainbow spectrum
const sleekColors = [
  '#B91C1C', '#DC2626', '#BE185D', '#EC4899',  // Reds & Pinks
  '#D97706', '#F59E0B', '#CA8A04', '#A3A3A3',  // Oranges & Yellows  
  '#166534', '#059669', '#0D9488', '#0F766E',  // Greens & Teals
  '#0369A1', '#1E40AF', '#3730A3', '#6B21A8',  // Blues & Purples
];

export default function SubjectColorPicker({ 
  visible, 
  onClose, 
  onSelectColor, 
  currentColor, 
  subjectName 
}: SubjectColorPickerProps) {
  const { currentTheme } = useTheme();
  const [previewColor, setPreviewColor] = React.useState(currentColor);

  // Reset preview color when modal opens or current color changes
  React.useEffect(() => {
    setPreviewColor(currentColor);
  }, [currentColor, visible]);

  const handleColorSelect = (color: string) => {
    onSelectColor(color);
    onClose();
  };

  const handleColorPressIn = (color: string) => {
    setPreviewColor(color);
  };

  const handleColorPressOut = () => {
    setPreviewColor(currentColor);
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
          <View style={styles.headerContent}>
            <Text style={[styles.title, { color: currentTheme.colors.textPrimary }]}>
              Choose Color
            </Text>
            <Text style={[styles.subtitle, { color: currentTheme.colors.textSecondary }]}>
              {subjectName}
            </Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color={currentTheme.colors.textSecondary} />
          </TouchableOpacity>
        </View>

        <View style={styles.colorGrid}>
          {sleekColors.map((color, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.colorOption,
                { backgroundColor: color },
                currentColor === color && [styles.selectedColor, { 
                  borderColor: currentTheme.colors.textPrimary,
                  shadowColor: color 
                }]
              ]}
              onPress={() => handleColorSelect(color)}
              onPressIn={() => handleColorPressIn(color)}
              onPressOut={handleColorPressOut}
              activeOpacity={0.8}
            >
              {currentColor === color && (
                <View style={styles.checkmark}>
                  <Text style={styles.checkmarkText}>✓</Text>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.previewSection}>
          <Text style={[styles.previewLabel, { color: currentTheme.colors.textSecondary }]}>
            Preview
          </Text>
          <View style={[styles.previewCard, { backgroundColor: currentTheme.colors.surface }]}>
            <View style={[styles.previewColorDot, { backgroundColor: previewColor }]} />
            <Text style={[styles.previewText, { color: currentTheme.colors.textPrimary }]}>
              {subjectName}
            </Text>
          </View>
        </View>
      </SafeAreaView>
    </Modal>
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
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  headerContent: {
    flex: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 14,
  },
  closeButton: {
    padding: 8,
  },
  colorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 20,
    paddingTop: 32,
    gap: 16,
  },
  colorOption: {
    width: (width - 40 - (3 * 16)) / 4,
    height: (width - 40 - (3 * 16)) / 4,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  selectedColor: {
    borderWidth: 3,
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
    transform: [{ scale: 1.05 }],
  },
  checkmark: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 12,
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmarkText: {
    color: '#000',
    fontSize: 14,
    fontWeight: '600',
  },
  previewSection: {
    paddingHorizontal: 20,
    paddingTop: 40,
  },
  previewLabel: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  previewCard: {
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  previewColorDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    marginRight: 16,
  },
  previewText: {
    fontSize: 17,
    fontWeight: '600',
  },
}); 