import { google } from 'googleapis';
import dotenv from 'dotenv';

dotenv.config();

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || '';
const GOOGLE_REDIRECT_URL = process.env.GOOGLE_REDIRECT_URL || '';

if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET || !GOOGLE_REDIRECT_URL) {
  console.error('Google OAuth credentials not found in environment variables');
  process.exit(1);
}

// Define Google Calendar API scopes
export const SCOPES = [
  'https://www.googleapis.com/auth/calendar.readonly',
  'https://www.googleapis.com/auth/userinfo.email',
  'https://www.googleapis.com/auth/userinfo.profile'
];

// Create OAuth2 client
export const oauth2Client = new google.auth.OAuth2(
  GOOGLE_CLIENT_ID,
  GOOGLE_CLIENT_SECRET,
  GOOGLE_REDIRECT_URL
);

// Helper function to get a new OAuth2 client instance
export function getOAuth2Client() {
  return new google.auth.OAuth2(
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URL
  );
} 