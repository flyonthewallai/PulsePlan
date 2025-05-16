import { Request, Response } from 'express';
import stripe, { STRIPE_PREMIUM_PRICE_ID, STRIPE_WEBHOOK_SECRET, CLIENT_URL } from '../config/stripe';
import supabase from '../config/supabase';

/**
 * Create a checkout session for premium subscription
 */
export const createCheckoutSession = async (req: Request, res: Response) => {
  try {
    const { userId } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    // Retrieve user data to be included in checkout metadata
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('email')
      .eq('id', userId)
      .single();

    if (userError) {
      console.error('Error retrieving user data:', userError);
      return res.status(500).json({ error: 'Error retrieving user data' });
    }

    // Create Stripe checkout session
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price: STRIPE_PREMIUM_PRICE_ID,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: `${CLIENT_URL}/settings?payment=success`,
      cancel_url: `${CLIENT_URL}/settings?payment=canceled`,
      metadata: {
        userId,
      },
      customer_email: userData.email,
    });

    res.json({ url: session.url });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    res.status(500).json({ error: 'Failed to create checkout session' });
  }
};

/**
 * Handle Stripe webhook events
 */
export const handleWebhook = async (req: Request, res: Response) => {
  const signature = req.headers['stripe-signature'] as string;

  if (!signature) {
    return res.status(400).json({ error: 'Stripe signature is missing' });
  }

  let event;

  try {
    // Use raw body for webhook signature verification
    const payload = req.body;
    
    // Verify the webhook signature
    event = stripe.webhooks.constructEvent(
      payload,
      signature,
      STRIPE_WEBHOOK_SECRET
    );
  } catch (err: any) {
    console.error(`Webhook signature verification failed: ${err.message}`);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  // Handle different event types
  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as any;
        const userId = session.metadata?.userId;
        
        if (userId) {
          // Update user metadata with premium plan
          const { error } = await supabase
            .from('users')
            .update({ 
              subscription_status: 'premium',
              stripe_customer_id: session.customer,
              subscription_id: session.subscription,
              updated_at: new Date().toISOString()
            })
            .eq('id', userId);

          if (error) {
            console.error('Error updating user subscription status:', error);
            return res.status(500).json({ error: 'Failed to update user subscription status' });
          }
        }
        break;
      }
      
      case 'customer.subscription.deleted': {
        const subscription = event.data.object as any;
        
        // Find user with this subscription ID
        const { data, error } = await supabase
          .from('users')
          .select('id')
          .eq('subscription_id', subscription.id)
          .single();
        
        if (!error && data) {
          // Downgrade user to free plan
          await supabase
            .from('users')
            .update({ 
              subscription_status: 'free',
              updated_at: new Date().toISOString()
            })
            .eq('id', data.id);
        }
        break;
      }
    }

    res.json({ received: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(400).json({ error: 'Webhook error' });
  }
};

/**
 * Get user subscription status
 */
export const getSubscriptionStatus = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Get user subscription status
    const { data, error } = await supabase
      .from('users')
      .select('subscription_status')
      .eq('id', userId)
      .single();
    
    if (error) {
      return res.status(500).json({ error: 'Failed to get subscription status' });
    }
    
    res.json({ 
      status: data?.subscription_status || 'free'
    });
    
  } catch (error) {
    console.error('Error checking subscription status:', error);
    res.status(500).json({ error: 'Failed to check subscription status' });
  }
}; 