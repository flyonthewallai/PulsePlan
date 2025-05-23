// Platform-specific exports for Stripe functionality
import { Platform } from 'react-native';
import React from 'react';

// Import Stripe directly - this file will be replaced with an empty module on web
// by metro.config.js resolver
import * as Stripe from '@stripe/stripe-react-native';

// Re-export all Stripe components and hooks
export const { 
  StripeProvider, 
  CardField, 
  useStripe,
} = Stripe;

// Export types for convenience if needed
export type { 
  StripeProviderProps, 
  CardFieldProps 
} from '@stripe/stripe-react-native'; 