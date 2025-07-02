import { Request, Response } from 'express';
import { Client } from '@microsoft/microsoft-graph-client';
import { getAuthUrl, exchangeCodeForTokens, SCOPES } from '../config/microsoft';
import supabase from '../config/supabase';
import { tokenService } from '../services/tokenService';

/**
 * Initiates the Microsoft OAuth flow
 */
export const initiateMicrosoftAuth = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: 'Supabase is not configured on the server.' });
  }

  try {
    const { userId } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Store userId in state parameter to retrieve it in callback
    const state = Buffer.from(JSON.stringify({ userId })).toString('base64');
    
    // Generate auth URL
    const authUrl = await getAuthUrl(state);
    
    res.redirect(authUrl);
  } catch (error) {
    console.error('Error initiating Microsoft auth:', error);
    res.status(500).json({ error: 'Failed to initiate Microsoft authentication' });
  }
};

/**
 * Handles the Microsoft OAuth callback
 */
export const handleMicrosoftCallback = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: 'Supabase is not configured on the server.' });
  }

  const { code, state, error: authError, error_description } = req.query;
  
  // Handle authentication errors
  if (authError) {
    console.error(`Authentication error: ${authError}, ${error_description}`);
    return res.status(400).json({ error: authError, description: error_description });
  }
  
  if (!code || !state) {
    return res.status(400).json({ error: 'Authorization code or state is missing' });
  }
  
  try {
    // Get userId from state
    const { userId } = JSON.parse(Buffer.from(state as string, 'base64').toString());
    
    // Exchange authorization code for tokens
    const tokenResponse = await exchangeCodeForTokens(code as string);
    
    if (!tokenResponse) {
      throw new Error('Failed to exchange code for tokens');
    }
    
    const accessToken = tokenResponse.accessToken;
    const refreshToken = (tokenResponse as any).refreshToken || (tokenResponse as any).refresh_token;
    const expiresOn = tokenResponse.expiresOn;
    
    if (!refreshToken) {
      console.warn('No refresh token received from Microsoft.');
    }
    
    // Get user info
    const graphClient = Client.init({
      authProvider: (done) => {
        done(null, accessToken);
      }
    });
    
    const userInfo = await graphClient
      .api('/me')
      .select('displayName,mail,userPrincipalName')
      .get();
    
    // Store tokens using token service (with encryption)
    try {
      await tokenService.storeUserTokens(userId, 'microsoft', {
        access_token: accessToken,
        refresh_token: refreshToken,
        expires_at: expiresOn ? new Date(expiresOn).toISOString() : undefined,
        scopes: SCOPES,
        email: userInfo.mail || userInfo.userPrincipalName
      });
    } catch (error) {
      console.error('Error storing tokens:', error);
      return res.status(500).json({ error: 'Failed to store connection' });
    }
    
    // Redirect to app with success message
    const clientUrl = process.env.CLIENT_URL || 'http://localhost:8081';
    res.redirect(`${clientUrl}/settings?status=connected&provider=microsoft`);
    
  } catch (error) {
    console.error('OAuth error:', error);
    res.status(500).json({ error: 'Authentication failed' });
  }
};

/**
 * Disconnects Microsoft Calendar
 */
export const disconnectMicrosoft = async (req: Request, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: 'Supabase is not configured on the server.' });
  }

  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Remove tokens using token service
    try {
      await tokenService.removeUserTokens(userId, 'microsoft');
    } catch (error) {
      console.error('Error removing tokens:', error);
      return res.status(500).json({ error: 'Failed to remove connection' });
    }
    
    res.json({ success: true, message: 'Microsoft Calendar disconnected successfully' });
    
  } catch (error) {
    console.error('Error disconnecting calendar:', error);
    res.status(500).json({ error: 'Failed to disconnect calendar' });
  }
}; 