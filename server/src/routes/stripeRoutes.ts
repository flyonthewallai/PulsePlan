import express from 'express';
import { 
  createCheckoutSession,
  handleWebhook,
  getSubscriptionStatus
} from '../controllers/stripeController';
import { requirePremium } from '../middleware/requirePremium';

const router = express.Router();

/**
 * @route   POST /stripe/create-checkout-session
 * @desc    Create a Stripe Checkout Session for premium subscription
 * @access  Public
 */
router.post('/create-checkout-session', createCheckoutSession);

/**
 * @route   POST /stripe/webhook
 * @desc    Handle Stripe webhooks
 * @access  Public
 * @note    Raw body parsing is handled at the app level
 */
router.post('/webhook', handleWebhook);

/**
 * @route   GET /stripe/subscription-status/:userId
 * @desc    Get user's subscription status
 * @access  Public
 */
router.get('/subscription-status/:userId', getSubscriptionStatus);

/**
 * @route   GET /stripe/premium-check/:userId
 * @desc    Check if user has premium subscription
 * @access  Public (for testing the middleware)
 */
router.get('/premium-check/:userId', requirePremium, (req, res) => {
  res.json({ 
    status: 'premium',
    message: 'User has premium subscription' 
  });
});

export default router; 