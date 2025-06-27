import { Request, Response } from 'express';
import supabase from '../config/supabase';
import { invalidateCache } from '../middleware/cacheInvalidation';

/**
 * Get user subscription status
 */
export const getSubscriptionStatus = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Get user subscription status
    const { data, error } = await supabase
      .from('users')
      .select('subscription_status, apple_transaction_id, subscription_expires_at')
      .eq('id', userId)
      .single();
    
    if (error) {
      return res.status(500).json({ error: 'Failed to get subscription status' });
    }
    
    res.json({ 
      status: data?.subscription_status || 'free',
      appleTransactionId: data?.apple_transaction_id,
      expiresAt: data?.subscription_expires_at
    });
    
  } catch (error) {
    console.error('Error checking subscription status:', error);
    res.status(500).json({ error: 'Failed to check subscription status' });
  }
};

/**
 * Update subscription status from Apple Pay transaction
 */
export const updateSubscriptionFromApplePay = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  try {
    const { 
      userId, 
      appleTransactionId, 
      subscriptionStatus, 
      expiresAt 
    } = req.body;
    
    if (!userId || !appleTransactionId || !subscriptionStatus) {
      return res.status(400).json({ 
        error: 'userId, appleTransactionId, and subscriptionStatus are required' 
      });
    }

    // Update user subscription status
    const { error } = await supabase
      .from('users')
      .update({ 
        subscription_status: subscriptionStatus,
        apple_transaction_id: appleTransactionId,
        subscription_expires_at: expiresAt,
        subscription_updated_at: new Date().toISOString()
      })
      .eq('id', userId);

    if (error) {
      console.error('Error updating subscription status:', error);
      return res.status(500).json({ error: 'Failed to update subscription status' });
    }

    // Invalidate user cache to reflect subscription change
    await invalidateCache.userInfo(userId);
    await invalidateCache.userSubscription(userId);
    
    console.log(`🔄 Invalidated cache for user ${userId} after Apple Pay subscription ${subscriptionStatus}`);

    res.json({ 
      success: true,
      message: 'Subscription status updated successfully',
      status: subscriptionStatus
    });
  } catch (error) {
    console.error('Error updating Apple Pay subscription:', error);
    res.status(500).json({ error: 'Failed to update subscription' });
  }
};

/**
 * Verify Apple Pay receipt and update subscription
 */
export const verifyApplePayReceipt = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  try {
    const { userId, receiptData, isProduction = false } = req.body;
    
    if (!userId || !receiptData) {
      return res.status(400).json({ 
        error: 'userId and receiptData are required' 
      });
    }

    // Apple's receipt verification endpoints
    const verificationUrl = isProduction 
      ? 'https://buy.itunes.apple.com/verifyReceipt'
      : 'https://sandbox.itunes.apple.com/verifyReceipt';

    // Verify receipt with Apple
    const appleResponse = await fetch(verificationUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        'receipt-data': receiptData,
        'password': process.env.APPLE_SHARED_SECRET, // Your App Store Connect shared secret
        'exclude-old-transactions': true
      })
    });

    const appleData = await appleResponse.json();

    if (appleData.status !== 0) {
      console.error('Apple receipt verification failed:', appleData);
      return res.status(400).json({ 
        error: 'Invalid receipt',
        appleStatus: appleData.status
      });
    }

    // Extract subscription info from Apple response
    const latestReceiptInfo = appleData.latest_receipt_info?.[0];
    if (!latestReceiptInfo) {
      return res.status(400).json({ error: 'No subscription found in receipt' });
    }

    const expiresDate = new Date(parseInt(latestReceiptInfo.expires_date_ms));
    const isActive = expiresDate > new Date();
    const transactionId = latestReceiptInfo.transaction_id;

    // Update subscription in database
    const { error } = await supabase
      .from('users')
      .update({
        subscription_status: isActive ? 'premium' : 'free',
        apple_transaction_id: transactionId,
        subscription_expires_at: expiresDate.toISOString(),
        subscription_updated_at: new Date().toISOString()
      })
      .eq('id', userId);

    if (error) {
      console.error('Error updating subscription from Apple receipt:', error);
      return res.status(500).json({ error: 'Failed to update subscription' });
    }

    // Invalidate user cache
    await invalidateCache.userInfo(userId);
    await invalidateCache.userSubscription(userId);
    
    console.log(`🔄 Invalidated cache for user ${userId} after Apple Pay receipt verification`);

    res.json({
      success: true,
      subscription: {
        status: isActive ? 'premium' : 'free',
        transactionId,
        expiresAt: expiresDate.toISOString(),
        isActive
      }
    });

  } catch (error) {
    console.error('Error verifying Apple Pay receipt:', error);
    res.status(500).json({ error: 'Failed to verify receipt' });
  }
};

/**
 * Handle subscription cancellation
 */
export const cancelSubscription = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  try {
    const { userId } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    // Update subscription status to cancelled
    const { error } = await supabase
      .from('users')
      .update({
        subscription_status: 'free',
        subscription_updated_at: new Date().toISOString()
      })
      .eq('id', userId);

    if (error) {
      console.error('Error cancelling subscription:', error);
      return res.status(500).json({ error: 'Failed to cancel subscription' });
    }

    // Invalidate user cache
    await invalidateCache.userInfo(userId);
    await invalidateCache.userSubscription(userId);
    
    console.log(`🔄 Invalidated cache for user ${userId} after subscription cancellation`);

    res.json({
      success: true,
      message: 'Subscription cancelled successfully'
    });

  } catch (error) {
    console.error('Error cancelling subscription:', error);
    res.status(500).json({ error: 'Failed to cancel subscription' });
  }
}; 