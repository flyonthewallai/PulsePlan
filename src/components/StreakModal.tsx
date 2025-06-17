import React from 'react';
import { Modal, View, Text, StyleSheet, Pressable, Dimensions } from 'react-native';
import { BlurView } from 'expo-blur';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Animated, { 
  FadeIn, 
  FadeOut, 
  SlideInDown, 
  SlideOutDown,
  withSpring 
} from 'react-native-reanimated';
import { useTheme } from '../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';

interface StreakModalProps {
  visible: boolean;
  onClose: () => void;
  streakCount: number;
  isNewRecord?: boolean;
}

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export const StreakModal: React.FC<StreakModalProps> = ({
  visible,
  onClose,
  streakCount,
  isNewRecord = false,
}) => {
  const { currentTheme } = useTheme();

  const getStreakMessage = () => {
    if (isNewRecord) {
      return "New Personal Record! 🎉";
    }
    if (streakCount >= 30) {
      return "Incredible Dedication! 🌟";
    }
    if (streakCount >= 14) {
      return "You're On Fire! 🔥";
    }
    if (streakCount >= 7) {
      return "Fantastic Progress! ⭐";
    }
    return "Keep Going Strong! 💪";
  };

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Animated.View 
        entering={FadeIn}
        exiting={FadeOut}
        style={styles.overlay}
      >
        <BlurView intensity={20} style={StyleSheet.absoluteFill} />
        
        <Animated.View
          entering={SlideInDown.springify().damping(15)}
          exiting={SlideOutDown}
          style={[styles.modalContainer, { backgroundColor: currentTheme.colors.surface }]}
        >
          <LinearGradient
            colors={[currentTheme.colors.primary + '20', 'transparent']}
            style={styles.gradientOverlay}
          />
          
          <View style={styles.content}>
            <MaterialCommunityIcons
              name="fire"
              size={64}
              color={currentTheme.colors.primary}
              style={styles.icon}
            />
            
            <Text style={[styles.streakCount, { color: currentTheme.colors.textPrimary }]}>
              {streakCount} Day{streakCount !== 1 ? 's' : ''}
            </Text>
            
            <Text style={[styles.streakMessage, { color: currentTheme.colors.textSecondary }]}>
              {getStreakMessage()}
            </Text>
            
            <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
              You've been consistently crushing your goals. Keep up the amazing work!
            </Text>
          </View>

          <Pressable
            style={[styles.button, { backgroundColor: currentTheme.colors.primary }]}
            onPress={onClose}
          >
            <Text style={[styles.buttonText, { color: '#FFFFFF' }]}>
              Keep Going
            </Text>
          </Pressable>
        </Animated.View>
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  modalContainer: {
    width: SCREEN_WIDTH * 0.85,
    borderRadius: 24,
    overflow: 'hidden',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
  },
  gradientOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 200,
  },
  content: {
    padding: 24,
    alignItems: 'center',
  },
  icon: {
    marginBottom: 16,
  },
  streakCount: {
    fontSize: 48,
    fontWeight: '700',
    marginBottom: 8,
  },
  streakMessage: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 8,
    paddingHorizontal: 16,
  },
  button: {
    marginHorizontal: 24,
    marginBottom: 24,
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
}); 