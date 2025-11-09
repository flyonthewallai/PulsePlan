import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X, CheckCircle2, ShieldCheck } from 'lucide-react-native';
import { BlurView } from 'expo-blur';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

type SubscriptionModalProps = {
  visible: boolean;
  onClose: () => void;
};

const features = [
  'Unlimited AI assistant messages',
  'Intelligent schedule optimization',
  'Long-term memory & personalization',
  'Proactive task suggestions',
  'Advanced progress tracking & insights',
  'Early access to new features',
];

export default function SubscriptionModal({ visible, onClose }: SubscriptionModalProps) {
  const theme = {
    background: '#0D0D0D',
    text: '#FFFFFF',
    textSecondary: '#A1A1A1',
    primary: '#D4AF37',
    card: '#1A1A1A',
    cardBorder: '#2C2C2C',
    button: '#F0F0F0',
    buttonText: '#0D0D0D',
  };

  return (
    <Modal
      animationType="slide"
      presentationStyle="pageSheet"
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <SafeAreaView style={styles.safeArea} edges={['top']}>
          <View style={styles.header}>
            <TouchableOpacity style={styles.headerButton}>
              <Text style={[styles.headerButtonText, { color: theme.text }]}>Restore</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color={theme.text} />
            </TouchableOpacity>
          </View>

          <ScrollView 
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
          >
            <View style={styles.brandingSection}>
              <View style={[styles.logoContainer, { borderColor: theme.primary }]}>
                <ShieldCheck size={32} color={theme.primary} />
              </View>
              <Text style={[styles.mainTitle, { color: theme.text }]}>
                Get unlimited usage with
              </Text>
              <Text style={[styles.appName, { color: theme.text }]}>
                PulsePlan <Text style={{ color: theme.primary }}>Premium</Text>
              </Text>
            </View>

            <View style={styles.featuresSection}>
              {features.map((feature, index) => (
                <View key={index} style={styles.featureItem}>
                  <CheckCircle2 size={16} color={theme.primary} />
                  <Text style={[styles.featureText, { color: theme.text }]}>{feature}</Text>
                </View>
              ))}
            </View>
            
            <View style={styles.planSection}>
              <Text style={[styles.planTitle, { color: theme.text }]}>Unlock Your Potential</Text>
              <Text style={[styles.planSubtitle, { color: theme.textSecondary }]}>
                Cancel anytime. 7 day free-trial.
              </Text>
            </View>

            <View style={[styles.priceCard, { backgroundColor: theme.card, borderColor: theme.primary }]}>
              <View>
                <Text style={[styles.planName, { color: theme.text }]}>Premium</Text>
                <Text style={[styles.price, { color: theme.text }]}>$6.99</Text>
                <Text style={[styles.billingCycle, { color: theme.textSecondary }]}>Billed Monthly</Text>
              </View>
              <View style={styles.radioSelected}>
                <View style={styles.radioInner} />
              </View>
            </View>
          </ScrollView>

          <View style={[styles.footer, { borderTopColor: theme.cardBorder }]}>
            <TouchableOpacity style={[styles.ctaButton, { backgroundColor: theme.button }]}>
              <Text style={[styles.ctaButtonText, { color: theme.buttonText }]}>
                Start 7-day free trial
              </Text>
            </TouchableOpacity>
            <View style={styles.legalLinks}>
              <TouchableOpacity onPress={() => Linking.openURL('https://pulseplan.app/terms')}>
                <Text style={[styles.legalText, { color: theme.textSecondary }]}>Terms of Use</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => Linking.openURL('https://pulseplan.app/privacy')}>
                <Text style={[styles.legalText, { color: theme.textSecondary }]}>Privacy Policy</Text>
              </TouchableOpacity>
            </View>
          </View>
        </SafeAreaView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  headerButton: {
    width: 70,
    height: 40,
    justifyContent: 'center',
  },
  headerButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingBottom: 24,
  },
  brandingSection: {
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 24,
  },
  logoContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  mainTitle: {
    fontSize: 20,
    fontWeight: '500',
    textAlign: 'center',
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 4,
  },
  featuresSection: {
    marginTop: 12,
    marginBottom: 24,
    gap: 12,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  featureText: {
    fontSize: 15,
    lineHeight: 20,
    flex: 1,
  },
  planSection: {
    marginBottom: 16,
    alignItems: 'center',
  },
  planTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  planSubtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  priceCard: {
    borderWidth: 2,
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  planName: {
    fontSize: 16,
    fontWeight: '600',
  },
  price: {
    fontSize: 24,
    fontWeight: 'bold',
    marginVertical: 4,
  },
  billingCycle: {
    fontSize: 14,
  },
  radioSelected: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FFFFFF',
  },
  footer: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 32,
    borderTopWidth: 1,
  },
  ctaButton: {
    paddingVertical: 16,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  ctaButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  legalLinks: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 24,
    marginTop: 16,
  },
  legalText: {
    fontSize: 13,
    textDecorationLine: 'underline',
  },
}); 