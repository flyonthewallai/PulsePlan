import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { Alert, Linking } from 'react-native';
import { supabase, getCurrentUser } from '../lib/supabase';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:3000';
const PUBLISHABLE_KEY = Constants.expoConfig?.extra?.stripePublishableKey;

// Define StripeProvider props type
interface StripeProviderProps {
  publishableKey?: string;
  merchantIdentifier?: string;
  children: React.ReactNode;
}

// Import Stripe only on native platforms
let StripeProvider: React.FC<StripeProviderProps> = ({ children }) => <>{children}</>;
if (Platform.OS !== 'web') {
  try {
    const StripeReactNative = require('@stripe/stripe-react-native');
    StripeProvider = StripeReactNative.StripeProvider;
  } catch (error) {
    console.warn('Stripe React Native not available:', error);
  }
}

interface PremiumContextType {
  isPremium: boolean;
  isLoading: boolean;
  subscriptionStatus: 'free' | 'premium' | 'loading';
  initiateTestPayment: () => Promise<void>;
  checkSubscriptionStatus: () => Promise<void>;
}

const PremiumContext = createContext<PremiumContextType | undefined>(undefined);

export const PremiumProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isPremium, setIsPremium] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [subscriptionStatus, setSubscriptionStatus] = useState<'free' | 'premium' | 'loading'>('loading');

  // Check subscription status on mount
  useEffect(() => {
    checkSubscriptionStatus();
  }, []);

  // Check subscription status from the server
  const checkSubscriptionStatus = async () => {
    setIsLoading(true);
    try {
      // Get current user using Supabase v1
      const { user, error: userError } = getCurrentUser();
      
      if (userError) {
        console.error('Auth error:', userError);
        setSubscriptionStatus('free');
        setIsPremium(false);
        return;
      }

      if (!user) {
        setSubscriptionStatus('free');
        setIsPremium(false);
        return;
      }

      // Get subscription status from Supabase
      const { data: subscriptions, error: subError } = await supabase
        .from('subscriptions')
        .select('status')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(1);

      if (subError) {
        console.error('Subscription check error:', subError);
        setSubscriptionStatus('free');
        setIsPremium(false);
        return;
      }

      // If no subscription exists, user is on free plan
      if (!subscriptions || subscriptions.length === 0) {
        setSubscriptionStatus('free');
        setIsPremium(false);
        return;
      }

      const status = subscriptions[0]?.status === 'active' ? 'premium' : 'free';
      setSubscriptionStatus(status);
      setIsPremium(status === 'premium');
      
      // Cache the status
      await AsyncStorage.setItem('subscriptionStatus', status);
    } catch (error) {
      console.error('Error checking subscription:', error);
      // Try to get cached status
      const cachedStatus = await AsyncStorage.getItem('subscriptionStatus') || 'free';
      setSubscriptionStatus(cachedStatus as 'free' | 'premium');
      setIsPremium(cachedStatus === 'premium');
    } finally {
      setIsLoading(false);
    }
  };

  // Initiate test payment
  const initiateTestPayment = async () => {
    try {
      // Get current user using Supabase v1
      const { user, error: userError } = getCurrentUser();
      
      if (userError) {
        throw new Error('Authentication error: Please log in again');
      }
      
      if (!user) {
        Alert.alert('Error', 'You must be logged in to test subscription.');
        return;
      }

      console.log('Initiating test payment for user:', user.id);

      // Create a test checkout session
      const requestBody = { userId: user.id };
      console.log('Sending request body:', requestBody);
      
      const { data, error: sessionError } = await supabase
        .functions.invoke('create-test-checkout-session', {
          body: JSON.stringify(requestBody)
        });

      console.log('Function response:', { data, error: sessionError });

      if (sessionError) {
        console.error('Session creation error:', sessionError);
        throw new Error('Failed to create checkout session. Please try again.');
      }

      if (!data || !data.url) {
        console.error('Invalid session response:', data);
        throw new Error('No checkout URL received from server');
      }

      // Open the checkout URL
      const canOpen = await Linking.canOpenURL(data.url);
      if (!canOpen) {
        throw new Error('Cannot open checkout URL');
      }

      await Linking.openURL(data.url);
    } catch (error) {
      console.error('Error initiating test payment:', error);
      Alert.alert(
        'Error',
        error instanceof Error 
          ? error.message 
          : 'Failed to initiate test payment. Please try again later.'
      );
    }
  };

  return (
    <StripeProvider
      publishableKey={PUBLISHABLE_KEY}
      merchantIdentifier="merchant.com.rhythm.app"
    >
      <PremiumContext.Provider 
        value={{ 
          isPremium, 
          isLoading,
          subscriptionStatus,
          initiateTestPayment,
          checkSubscriptionStatus
        }}
      >
        {children}
      </PremiumContext.Provider>
    </StripeProvider>
  );
};

export const usePremium = () => {
  const context = useContext(PremiumContext);
  if (context === undefined) {
    throw new Error('usePremium must be used within a PremiumProvider');
  }
  return context;
}; 