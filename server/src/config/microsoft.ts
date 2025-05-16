// @ts-ignore
import { ConfidentialClientApplication } from 'msal-node';
import dotenv from 'dotenv';

dotenv.config();

const CLIENT_ID = process.env.MICROSOFT_CLIENT_ID || '';
const CLIENT_SECRET = process.env.MICROSOFT_CLIENT_SECRET || '';
const REDIRECT_URI = process.env.MICROSOFT_REDIRECT_URL || '';
const TENANT_ID = process.env.MICROSOFT_TENANT_ID || 'common'; // 'common' for multi-tenant apps

if (!CLIENT_ID || !CLIENT_SECRET || !REDIRECT_URI) {
  console.error('Microsoft OAuth credentials not found in environment variables');
  process.exit(1);
}

// Define Microsoft Graph API scopes
export const SCOPES = [
  'Calendars.Read',
  'Calendars.ReadWrite',
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
      logLevel: "Info"
    }
  }
};

// Create confidential client application
export const msalClient = new ConfidentialClientApplication(msalConfig);

// Helper function to get auth URL
export function getAuthUrl(state: string) {
  const authCodeUrlParameters = {
    scopes: SCOPES,
    redirectUri: REDIRECT_URI,
    state: state
  };

  return msalClient.getAuthCodeUrl(authCodeUrlParameters);
}

// Helper function to exchange code for tokens
export async function exchangeCodeForTokens(code: string) {
  const tokenRequest = {
    code,
    scopes: SCOPES,
    redirectUri: REDIRECT_URI
  };

  return msalClient.acquireTokenByCode(tokenRequest);
}

// Helper function to get access token with refresh token
export async function getAccessTokenWithRefreshToken(refreshToken: string) {
  const tokenRequest = {
    refreshToken,
    scopes: SCOPES
  };

  return msalClient.acquireTokenByRefreshToken(tokenRequest);
} 