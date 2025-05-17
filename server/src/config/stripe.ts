import Stripe from 'stripe';
import dotenv from 'dotenv';

dotenv.config();

const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;
const STRIPE_WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET;
const STRIPE_PREMIUM_PRICE_ID = process.env.STRIPE_PREMIUM_PRICE_ID;
const CLIENT_URL = process.env.CLIENT_URL || 'http://localhost:8081';

if (!STRIPE_SECRET_KEY) {
  console.error('Stripe secret key not found in environment variables');
  process.exit(1);
}

if (!STRIPE_WEBHOOK_SECRET) {
  console.error('Stripe webhook secret not found in environment variables');
  process.exit(1);
}

if (!STRIPE_PREMIUM_PRICE_ID) {
  console.error('Stripe premium price ID not found in environment variables');
  process.exit(1);
}

// Initialize Stripe client
const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2025-04-30.basil', // Use latest stable API version
});

export default stripe;
export {
  STRIPE_WEBHOOK_SECRET,
  STRIPE_PREMIUM_PRICE_ID,
  CLIENT_URL
}; 