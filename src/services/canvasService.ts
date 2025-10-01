import { API_BASE_URL } from '../config/api';

export interface CanvasIntegrationStatus {
  connected: boolean;
  lastSync: string | null;
  assignmentsSynced: number;
  extensionVersion: string | null;
  totalCanvasTasks: number;
  connectionCode: string | null;
  connectionCodeExpiry: string | null;
}

export interface QRConnectionData {
  connectionCode: string;
  connectUrl: string;
  qrCodeUrl: string;
  expiresAt: string;
}

export class CanvasService {
  private static baseUrl = API_BASE_URL;

  /**
   * Get Canvas integration status for the current user
   */
  static async getIntegrationStatus(authToken: string): Promise<CanvasIntegrationStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/canvas/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching Canvas integration status:', error);
      throw error;
    }
  }

  /**
   * Generate QR code for extension connection
   */
  static async generateConnectionCode(authToken: string): Promise<QRConnectionData> {
    try {
      const response = await fetch(`${this.baseUrl}/canvas/generate-connection-code`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating connection code:', error);
      throw error;
    }
  }

  /**
   * Complete extension connection using connection code
   */
  static async completeConnection(authToken: string, connectionCode: string): Promise<{ success: boolean; message: string; connectedAt: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/canvas/connect-extension`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ connectionCode }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error completing extension connection:', error);
      throw error;
    }
  }

  /**
   * Connect Canvas using API key
   */
  static async connectWithAPIKey(authToken: string, canvasUrl: string, apiToken: string): Promise<{ success: boolean; message: string; user_id: string; canvas_url: string; status: string; stored_at: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/canvas/connect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          canvas_url: canvasUrl,
          api_token: apiToken,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error connecting Canvas with API key:', error);
      throw error;
    }
  }

  /**
   * Test Canvas API connection
   */
  static async testConnection(): Promise<{ success: boolean; message: string; timestamp: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/canvas/test-connection`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error testing Canvas connection:', error);
      throw error;
    }
  }

  /**
   * Format last sync time for display
   */
  static formatLastSync(lastSync: string | null): string {
    if (!lastSync) return 'Never';
    
    const date = new Date(lastSync);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  }
} 