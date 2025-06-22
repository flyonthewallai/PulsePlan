// @ts-ignore
import { ConfidentialClientApplication } from '@azure/msal-node';
import dotenv from 'dotenv';

dotenv.config();

const CLIENT_ID = process.env.MICROSOFT_CLIENT_ID || '';
const CLIENT_SECRET = process.env.MICROSOFT_CLIENT_SECRET || '';
const REDIRECT_URI = process.env.MICROSOFT_REDIRECT_URL || '';
const TENANT_ID = process.env.MICROSOFT_TENANT_ID || 'common'; // 'common' for multi-tenant apps

// Only warn in development, don't exit
if (!CLIENT_ID || !CLIENT_SECRET || !REDIRECT_URI) {
  console.warn('Microsoft OAuth credentials not found in environment variables. Microsoft Calendar features will be disabled.');
}

// Define Microsoft Graph API scopes for full integration
export const SCOPES = [
  'Calendars.Read',
  'Calendars.ReadWrite',
  'Mail.Read',
  'Mail.ReadWrite',
  'User.Read',
  'offline_access'
];

// MSAL configuration
const msalConfig = {
  auth: {
    clientId: CLIENT_ID,
    authority: `https://login.microsoftonline.com/${TENANT_ID}`,
    clientSecret: CLIENT_SECRET
  },
  system: {
    loggerOptions: {
      loggerCallback(loglevel, message) {
        console.log(message);
      },
      piiLoggingEnabled: false,
      logLevel: ("Info" as any)
    }
  }
};

// Create confidential client application only if credentials are available
export const msalClient = CLIENT_ID && CLIENT_SECRET && REDIRECT_URI
  ? new ConfidentialClientApplication(msalConfig)
  : null;

// Helper function to get auth URL
export function getAuthUrl(state: string) {
  if (!msalClient) { throw new Error("Microsoft OAuth credentials not configured."); }
  const authCodeUrlParameters = {
    scopes: SCOPES,
    redirectUri: REDIRECT_URI,
    state: state
  };

  return msalClient.getAuthCodeUrl(authCodeUrlParameters);
}

// Helper function to exchange code for tokens
export async function exchangeCodeForTokens(code: string) {
  if (!msalClient) { throw new Error("Microsoft OAuth credentials not configured."); }
  const tokenRequest = {
    code,
    scopes: SCOPES,
    redirectUri: REDIRECT_URI
  };

  return msalClient.acquireTokenByCode(tokenRequest);
}

// Helper function to get access token with refresh token
export async function getAccessTokenWithRefreshToken(refreshToken: string) {
  if (!msalClient) { throw new Error("Microsoft OAuth credentials not configured."); }
  const tokenRequest = {
    refreshToken,
    scopes: SCOPES
  };

  return msalClient.acquireTokenByRefreshToken(tokenRequest);
} 