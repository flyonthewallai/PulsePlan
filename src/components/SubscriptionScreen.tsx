import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { usePremium } from '../contexts/PremiumContext';

interface SubscriptionScreenProps {
  onClose: () => void;
}

const SubscriptionScreen: React.FC<SubscriptionScreenProps> = ({ onClose }) => {
  const { theme } = useTheme();
  const { 
    isPremium, 
    isLoading, 
    initiateSubscription, 
    manageSubscription, 
    checkSubscriptionStatus 
  } = usePremium();
  const [processingSubscription, setProcessingSubscription] = useState(false);

  // Features included in premium
  const premiumFeatures = [
    { 
      title: 'Premium Themes', 
      description: 'Access to exclusive premium themes and color options', 
      icon: 'color-palette-outline' 
    },
    { 
      title: 'Advanced Analytics', 
      description: 'Detailed insights into your productivity and habits', 
      icon: 'bar-chart-outline' 
    },
    { 
      title: 'Unlimited Schedules', 
      description: 'Create and save as many schedules as you need', 
      icon: 'calendar-outline' 
    },
    { 
      title: 'Priority Support', 
      description: 'Get help faster with dedicated premium support', 
      icon: 'help-buoy-outline' 
    },
    { 
      title: 'Calendar Sync', 
      description: 'Sync with Google, Outlook and Apple calendars', 
      icon: 'sync-outline' 
    },
  ];

  const handleSubscribe = async () => {
    setProcessingSubscription(true);
    try {
      await initiateSubscription();
    } finally {
      setProcessingSubscription(false);
    }
  };

  const handleManageSubscription = async () => {
    await manageSubscription();
  };

  const handleRefresh = async () => {
    setProcessingSubscription(true);
    try {
      await checkSubscriptionStatus();
    } finally {
      setProcessingSubscription(false);
    }
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={theme.colors.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
            Subscription
          </Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.loadingText, { color: theme.colors.text }]}>
            Checking subscription status...
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
          <Ionicons name="close" size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
          Rhythm Premium
        </Text>
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.planContainer}>
          <View style={[
            styles.planBadge, 
            { backgroundColor: isPremium ? theme.colors.primary : theme.colors.cardBackground }
          ]}>
            <Text style={[
              styles.planBadgeText,
              { color: isPremium ? '#FFFFFF' : theme.colors.text }
            ]}>
              {isPremium ? 'PREMIUM' : 'FREE PLAN'}
            </Text>
          </View>

          <Text style={[styles.statusText, { color: theme.colors.text }]}>
            {isPremium 
              ? 'You are currently on the Premium plan!' 
              : 'Upgrade to Premium to unlock all features'}
          </Text>

          <View style={[styles.pricingCard, { backgroundColor: theme.colors.cardBackground }]}>
            <Text style={[styles.pricingTitle, { color: theme.colors.text }]}>
              Premium Plan
            </Text>
            <Text style={[styles.price, { color: theme.colors.primary }]}>
              $4.99
              <Text style={[styles.pricePeriod, { color: theme.colors.text }]}>
                /month
              </Text>
            </Text>
            <Text style={[styles.billingInfo, { color: theme.colors.textSecondary }]}>
              or $49.99/year (save 17%)
            </Text>
          </View>
        </View>

        <View style={styles.featuresContainer}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Premium Features
          </Text>
          
          {premiumFeatures.map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <View style={[styles.featureIconContainer, { backgroundColor: theme.colors.primary + '20' }]}>
                <Ionicons name={feature.icon as any} size={22} color={theme.colors.primary} />
              </View>
              <View style={styles.featureTextContainer}>
                <Text style={[styles.featureTitle, { color: theme.colors.text }]}>
                  {feature.title}
                </Text>
                <Text style={[styles.featureDescription, { color: theme.colors.textSecondary }]}>
                  {feature.description}
                </Text>
              </View>
            </View>
          ))}
        </View>

        <TouchableOpacity 
          style={[
            styles.button, 
            { 
              backgroundColor: isPremium 
                ? theme.colors.cardBackground 
                : theme.colors.primary,
              borderWidth: isPremium ? 1 : 0,
              borderColor: isPremium ? theme.colors.border : 'transparent'
            }
          ]}
          onPress={isPremium ? handleManageSubscription : handleSubscribe}
          disabled={processingSubscription}
        >
          {processingSubscription ? (
            <ActivityIndicator size="small" color={isPremium ? theme.colors.primary : '#FFFFFF'} />
          ) : (
            <Text 
              style={[
                styles.buttonText, 
                { 
                  color: isPremium 
                    ? theme.colors.primary 
                    : '#FFFFFF' 
                }
              ]}
            >
              {isPremium ? 'Manage Subscription' : 'Upgrade to Premium'}
            </Text>
          )}
        </TouchableOpacity>

        {isPremium && (
          <TouchableOpacity 
            style={styles.refreshButton}
            onPress={handleRefresh}
            disabled={processingSubscription}
          >
            <Text style={[styles.refreshButtonText, { color: theme.colors.primary }]}>
              Refresh Subscription Status
            </Text>
          </TouchableOpacity>
        )}

        <Text style={[styles.termsText, { color: theme.colors.textSecondary }]}>
          By subscribing, you agree to our Terms of Service and Privacy Policy. 
          Subscriptions automatically renew unless auto-renew is turned off at least 
          24 hours before the end of the current period.
        </Text>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
    marginRight: 40,
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  planContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  planBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 8,
  },
  planBadgeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  statusText: {
    fontSize: 16,
    marginBottom: 16,
    textAlign: 'center',
  },
  pricingCard: {
    width: '100%',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
  },
  pricingTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  price: {
    fontSize: 32,
    fontWeight: '700',
  },
  pricePeriod: {
    fontSize: 16,
    fontWeight: '400',
  },
  billingInfo: {
    fontSize: 14,
    marginTop: 4,
  },
  featuresContainer: {
    marginTop: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
  },
  featureItem: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'center',
  },
  featureIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  featureTextContainer: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  featureDescription: {
    fontSize: 14,
  },
  button: {
    borderRadius: 12,
    padding: 16,
    marginTop: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  refreshButton: {
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  refreshButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  termsText: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
});

export default SubscriptionScreen; 