import express from 'express';
import { 
  getSubscriptionStatus,
  updateSubscriptionFromApplePay,
  verifyApplePayReceipt,
  cancelSubscription
} from '../controllers/applePayController';
import { authenticate } from '../middleware/authenticate';
import { invalidateUserSubscriptionCache } from '../middleware/cacheInvalidation';

const router = express.Router();

/**
 * @route   GET /apple-pay/subscription-status/:userId
 * @desc    Get user's subscription status
 * @access  Public
 */
router.get('/subscription-status/:userId', getSubscriptionStatus);

/**
 * @route   POST /apple-pay/update-subscription
 * @desc    Update subscription status from Apple Pay transaction
 * @access  Private
 */
router.post('/update-subscription', authenticate, invalidateUserSubscriptionCache, updateSubscriptionFromApplePay);

/**
 * @route   POST /apple-pay/verify-receipt
 * @desc    Verify Apple Pay receipt and update subscription
 * @access  Private
 */
router.post('/verify-receipt', authenticate, invalidateUserSubscriptionCache, verifyApplePayReceipt);

/**
 * @route   POST /apple-pay/cancel-subscription
 * @desc    Cancel user subscription
 * @access  Private
 */
router.post('/cancel-subscription', authenticate, invalidateUserSubscriptionCache, cancelSubscription);

export default router; 