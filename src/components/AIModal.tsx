import React, { useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  Modal, 
  Animated,
  Dimensions
} from 'react-native';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

export const AIModal = ({ 
  isVisible, 
  onClose, 
  task, 
  darkMode,
  pulsing = false 
}) => {
  const translateY = new Animated.Value(SCREEN_HEIGHT);
  const opacity = new Animated.Value(0);

  useEffect(() => {
    if (isVisible) {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: SCREEN_HEIGHT,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [isVisible]);

  const handleClose = () => {
    onClose();
  };

  return (
    <Modal
      visible={isVisible}
      transparent
      animationType="none"
      onRequestClose={handleClose}
    >
      <TouchableOpacity 
        style={styles.overlay} 
        activeOpacity={1} 
        onPress={handleClose}
      >
        <Animated.View 
          style={[
            styles.modal,
            darkMode ? styles.darkModal : styles.lightModal,
            {
              transform: [{ translateY }],
              opacity,
            }
          ]}
        >
          <View style={styles.handle} />
          
          {/* AI Avatar */}
          <View style={styles.avatarContainer}>
            <Animated.View 
              style={[
                styles.avatar,
                pulsing && styles.pulsing
              ]}
            >
              <View style={styles.avatarInner}>
                <Text style={styles.avatarText}>AI</Text>
              </View>
            </Animated.View>
          </View>

          {/* Task Title */}
          <Text style={[styles.title, darkMode ? styles.darkText : styles.lightText]}>
            {task.title}
          </Text>

          {/* Content Sections */}
          <View style={styles.sections}>
            {/* Why this task? */}
            <View style={[styles.section, { backgroundColor: `${task.color}10` }]}>
              <Text style={[styles.sectionTitle, darkMode ? styles.darkText : styles.lightText]}>
                Why this task?
              </Text>
              <Text style={[styles.sectionText, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                Based on your study patterns and upcoming deadlines, this task is prioritized to help you maintain a balanced workload.
              </Text>
              <TouchableOpacity 
                style={[styles.actionButton, { backgroundColor: '#00AEEF' }]}
              >
                <Text style={styles.actionButtonText}>Adjust Priority</Text>
              </TouchableOpacity>
            </View>

            {/* Need more time? */}
            <View style={[styles.section, { backgroundColor: `${task.color}10` }]}>
              <Text style={[styles.sectionTitle, darkMode ? styles.darkText : styles.lightText]}>
                Need more time?
              </Text>
              <Text style={[styles.sectionText, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                I can help you reschedule this task to a better time slot that fits your schedule.
              </Text>
            </View>

            {/* What's next? */}
            <View style={[styles.section, { backgroundColor: `${task.color}10` }]}>
              <Text style={[styles.sectionTitle, darkMode ? styles.darkText : styles.lightText]}>
                What's next?
              </Text>
              <Text style={[styles.sectionText, darkMode ? styles.darkSubtext : styles.lightSubtext]}>
                After completing this task, I recommend reviewing your notes from last week's lecture to prepare for the upcoming quiz.
              </Text>
            </View>
          </View>

          {/* Close Button */}
          <TouchableOpacity 
            style={[
              styles.closeButton,
              darkMode ? styles.darkCloseButton : styles.lightCloseButton
            ]}
            onPress={handleClose}
          >
            <Text style={[
              styles.closeButtonText,
              darkMode ? styles.darkCloseButtonText : styles.lightCloseButtonText
            ]}>
              Got it
            </Text>
          </TouchableOpacity>
        </Animated.View>
      </TouchableOpacity>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
    justifyContent: 'flex-end',
  },
  modal: {
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 20,
    paddingBottom: 40,
    shadowColor: '#00AEEF',
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.15,
    shadowRadius: 24,
    elevation: 12,
    borderWidth: 1,
    borderColor: 'rgba(209, 213, 219, 0.2)',
  },
  darkModal: {
    backgroundColor: '#1F2937F0', // 94% opacity for frosted effect
  },
  lightModal: {
    backgroundColor: '#FFFFFFF0', // 94% opacity for frosted effect
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: 'rgba(209, 213, 219, 0.6)',
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 16,
  },
  avatarContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#00AEEF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulsing: {
    opacity: 0.7,
  },
  avatarInner: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  darkText: {
    color: '#FFFFFF',
  },
  lightText: {
    color: '#1F2937',
  },
  darkSubtext: {
    color: '#D1D5DB',
  },
  lightSubtext: {
    color: '#6B7280',
  },
  sections: {
    gap: 16,
  },
  section: {
    padding: 12,
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  actionButton: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
  },
  closeButton: {
    paddingVertical: 12,
    borderRadius: 12,
    marginTop: 24,
  },
  darkCloseButton: {
    backgroundColor: '#C9C9FF',
  },
  lightCloseButton: {
    backgroundColor: '#0D1B2A',
  },
  closeButtonText: {
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
  },
  darkCloseButtonText: {
    color: '#0D1B2A',
  },
  lightCloseButtonText: {
    color: '#FFFFFF',
  },
});