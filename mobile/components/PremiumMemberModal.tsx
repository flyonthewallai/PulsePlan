import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X, Star, Check } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';

interface PremiumMemberModalProps {
  visible: boolean;
  onClose: () => void;
}

const PremiumMemberModal: React.FC<PremiumMemberModalProps> = ({ visible, onClose }) => {
  const { currentTheme } = useTheme();

  const premiumPerks = [
    {
      title: 'Daily Briefings',
      description: 'Start each day with AI-powered schedule insights and smart suggestions'
    },
    {
      title: 'Weekly Pulse',
      description: 'Get comprehensive weekly recaps with productivity analytics and tips'
    },
    {
      title: 'Hobbies Integration',
      description: 'Balance work and play with intelligent hobby scheduling'
    },
    {
      title: 'Premium Themes',
      description: 'Access exclusive color schemes and visual customizations'
    },
    {
      title: 'Advanced AI Features',
      description: 'Enhanced scheduling intelligence and personalized recommendations'
    },
    {
      title: 'Priority Support',
      description: 'Get faster response times and dedicated customer support'
    }
  ];

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X color={currentTheme.colors.textSecondary} size={24} />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.heroSection}>
            <View style={[styles.starContainer, { backgroundColor: currentTheme.colors.primary + '20' }]}>
              <Star color={currentTheme.colors.primary} size={32} fill={currentTheme.colors.primary} />
            </View>
            <Text style={[styles.title, { color: currentTheme.colors.textPrimary }]}>
              Thank You for Being Premium!
            </Text>
            <Text style={[styles.subtitle, { color: currentTheme.colors.textSecondary }]}>
              You're unlocking the full potential of PulsePlan with these exclusive features:
            </Text>
          </View>

          <View style={styles.perksContainer}>
            {premiumPerks.map((perk, index) => (
              <View key={index} style={[styles.perkItem, { backgroundColor: currentTheme.colors.surface }]}>
                <View style={styles.perkHeader}>
                  <Check color={currentTheme.colors.primary} size={20} />
                  <Text style={[styles.perkTitle, { color: currentTheme.colors.textPrimary }]}>
                    {perk.title}
                  </Text>
                </View>
                <Text style={[styles.perkDescription, { color: currentTheme.colors.textSecondary }]}>
                  {perk.description}
                </Text>
              </View>
            ))}
          </View>

          <View style={[styles.thankYouCard, { backgroundColor: currentTheme.colors.surface }]}>
            <Text style={[styles.thankYouTitle, { color: currentTheme.colors.textPrimary }]}>
              Your Support Matters
            </Text>
            <Text style={[styles.thankYouText, { color: currentTheme.colors.textSecondary }]}>
              Your premium subscription helps us continue building amazing features and maintaining the best possible experience for all PulsePlan users.
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  heroSection: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  starContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 17,
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: 16,
  },
  perksContainer: {
    marginBottom: 32,
  },
  perkItem: {
    padding: 20,
    borderRadius: 12,
    marginBottom: 12,
  },
  perkHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  perkTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 12,
  },
  perkDescription: {
    fontSize: 15,
    lineHeight: 22,
    marginLeft: 32,
  },
  thankYouCard: {
    padding: 24,
    borderRadius: 16,
    marginBottom: 32,
  },
  thankYouTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  thankYouText: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
  },
});

export default PremiumMemberModal; 