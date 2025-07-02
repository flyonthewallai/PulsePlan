export interface ConnectedAccount {
  id: string;
  user_id: string;
  provider: 'google' | 'microsoft' | 'canvas' | 'notion';
  access_token: string;
  refresh_token?: string;
  expires_at?: string;
  scopes: string[];
  email?: string;
  created_at: string;
  updated_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token?: string;
  expires_at?: string;
  scopes: string[];
}

export interface UserTokens {
  userId: string;
  google?: TokenPair;
  microsoft?: TokenPair;
  canvas?: TokenPair;
  notion?: TokenPair;
}

export interface AgentPayloadWithTokens {
  userId: string;
  userEmail?: string;
  userName?: string;
  isPremium?: boolean;
  city?: string;
  timezone?: string;
  source: 'agent' | 'user' | 'scheduler';
  tool?: string;
  // Connected account tokens
  connectedAccounts?: {
    google?: {
      access_token: string;
      refresh_token?: string;
      expires_at?: string;
      scopes: string[];
      email?: string;
    };
    microsoft?: {
      access_token: string;
      refresh_token?: string;
      expires_at?: string;
      scopes: string[];
      email?: string;
    };
    canvas?: {
      access_token: string;
      refresh_token?: string;
      expires_at?: string;
      scopes: string[];
    };
    notion?: {
      access_token: string;
      refresh_token?: string;
      expires_at?: string;
      scopes: string[];
    };
  };
  [key: string]: any;
}

export interface TokenRefreshResult {
  success: boolean;
  tokens?: TokenPair;
  error?: string;
}

export interface TokenValidationResult {
  isValid: boolean;
  needsRefresh: boolean;
  error?: string;
} 