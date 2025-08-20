import { Platform, Linking } from 'react-native';
import { API_BASE_URL } from '@/config/api';

export interface GmailMessage {
  id: string;
  threadId: string;
  labelIds: string[];
  snippet: string;
  payload: {
    partId?: string;
    mimeType: string;
    filename?: string;
    headers: Array<{
      name: string;
      value: string;
    }>;
    body?: {
      attachmentId?: string;
      size: number;
      data?: string;
    };
    parts?: any[];
  };
  sizeEstimate: number;
  historyId: string;
  internalDate: string;
}

export interface GmailThread {
  id: string;
  historyId: string;
  messages: GmailMessage[];
}

export interface GmailLabel {
  id: string;
  name: string;
  messageListVisibility: string;
  labelListVisibility: string;
  type: string;
  messagesTotal?: number;
  messagesUnread?: number;
  threadsTotal?: number;
  threadsUnread?: number;
  color?: {
    textColor: string;
    backgroundColor: string;
  };
}

export interface GmailSearchOptions {
  query?: string;
  labelIds?: string[];
  maxResults?: number;
  pageToken?: string;
  includeSpamTrash?: boolean;
}

export interface ParsedGmailMessage {
  id: string;
  threadId: string;
  subject: string;
  from: string;
  to: string[];
  cc?: string[];
  bcc?: string[];
  date: string;
  snippet: string;
  body: string;
  isUnread: boolean;
  isImportant: boolean;
  labels: string[];
  attachments: Array<{
    filename: string;
    mimeType: string;
    size: number;
    attachmentId: string;
  }>;
}

/**
 * Gmail Service
 * Handles Gmail API operations using connected Google account tokens
 */
export class GmailService {
  private static baseUrl = API_BASE_URL;

  /**
   * Get Gmail messages
   */
  static async getMessages(
    userId: string,
    options: GmailSearchOptions = {}
  ): Promise<{ messages: ParsedGmailMessage[]; nextPageToken?: string; totalResults: number }> {
    const params = new URLSearchParams();
    
    if (options.query) params.append('q', options.query);
    if (options.labelIds?.length) params.append('labelIds', options.labelIds.join(','));
    if (options.maxResults) params.append('maxResults', options.maxResults.toString());
    if (options.pageToken) params.append('pageToken', options.pageToken);
    if (options.includeSpamTrash) params.append('includeSpamTrash', 'true');

    const response = await fetch(`${this.baseUrl}/gmail/messages/${userId}?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch Gmail messages: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get unread messages
   */
  static async getUnreadMessages(
    userId: string,
    maxResults: number = 10
  ): Promise<ParsedGmailMessage[]> {
    const result = await this.getMessages(userId, {
      query: 'is:unread',
      maxResults,
    });
    
    return result.messages;
  }

  /**
   * Get messages from today
   */
  static async getTodaysMessages(
    userId: string,
    maxResults: number = 20
  ): Promise<ParsedGmailMessage[]> {
    const today = new Date().toISOString().split('T')[0];
    const result = await this.getMessages(userId, {
      query: `after:${today}`,
      maxResults,
    });
    
    return result.messages;
  }

  /**
   * Get messages from a specific sender
   */
  static async getMessagesFromSender(
    userId: string,
    senderEmail: string,
    maxResults: number = 10
  ): Promise<ParsedGmailMessage[]> {
    const result = await this.getMessages(userId, {
      query: `from:${senderEmail}`,
      maxResults,
    });
    
    return result.messages;
  }

  /**
   * Get messages with specific subject
   */
  static async getMessagesBySubject(
    userId: string,
    subject: string,
    maxResults: number = 10
  ): Promise<ParsedGmailMessage[]> {
    const result = await this.getMessages(userId, {
      query: `subject:"${subject}"`,
      maxResults,
    });
    
    return result.messages;
  }

  /**
   * Get a specific message by ID
   */
  static async getMessage(
    userId: string,
    messageId: string
  ): Promise<ParsedGmailMessage> {
    const response = await fetch(`${this.baseUrl}/gmail/message/${userId}/${messageId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch Gmail message: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Mark message as read
   */
  static async markAsRead(
    userId: string,
    messageId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/gmail/message/${userId}/${messageId}/read`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to mark message as read: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Mark message as unread
   */
  static async markAsUnread(
    userId: string,
    messageId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/gmail/message/${userId}/${messageId}/unread`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to mark message as unread: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Add label to message
   */
  static async addLabel(
    userId: string,
    messageId: string,
    labelId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/gmail/message/${userId}/${messageId}/label`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ labelId, action: 'add' }),
    });

    if (!response.ok) {
      throw new Error(`Failed to add label to message: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Remove label from message
   */
  static async removeLabel(
    userId: string,
    messageId: string,
    labelId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/gmail/message/${userId}/${messageId}/label`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ labelId, action: 'remove' }),
    });

    if (!response.ok) {
      throw new Error(`Failed to remove label from message: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get Gmail labels
   */
  static async getLabels(userId: string): Promise<GmailLabel[]> {
    const response = await fetch(`${this.baseUrl}/gmail/labels/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch Gmail labels: ${response.status}`);
    }

    const data = await response.json();
    return data.labels;
  }

  /**
   * Send email
   */
  static async sendEmail(
    userId: string,
    email: {
      to: string[];
      cc?: string[];
      bcc?: string[];
      subject: string;
      body: string;
      isHtml?: boolean;
      attachments?: Array<{
        filename: string;
        content: string;
        mimeType: string;
      }>;
    }
  ): Promise<{ success: boolean; messageId: string }> {
    const response = await fetch(`${this.baseUrl}/gmail/send/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(email),
    });

    if (!response.ok) {
      throw new Error(`Failed to send email: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Reply to email
   */
  static async replyToEmail(
    userId: string,
    messageId: string,
    threadId: string,
    reply: {
      body: string;
      isHtml?: boolean;
      attachments?: Array<{
        filename: string;
        content: string;
        mimeType: string;
      }>;
    }
  ): Promise<{ success: boolean; messageId: string }> {
    const response = await fetch(`${this.baseUrl}/gmail/reply/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messageId,
        threadId,
        ...reply,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to reply to email: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get email threads
   */
  static async getThreads(
    userId: string,
    options: GmailSearchOptions = {}
  ): Promise<{ threads: GmailThread[]; nextPageToken?: string; totalResults: number }> {
    const params = new URLSearchParams();
    
    if (options.query) params.append('q', options.query);
    if (options.labelIds?.length) params.append('labelIds', options.labelIds.join(','));
    if (options.maxResults) params.append('maxResults', options.maxResults.toString());
    if (options.pageToken) params.append('pageToken', options.pageToken);
    if (options.includeSpamTrash) params.append('includeSpamTrash', 'true');

    const response = await fetch(`${this.baseUrl}/gmail/threads/${userId}?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch Gmail threads: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Search emails
   */
  static async searchEmails(
    userId: string,
    searchQuery: string,
    maxResults: number = 10
  ): Promise<ParsedGmailMessage[]> {
    const result = await this.getMessages(userId, {
      query: searchQuery,
      maxResults,
    });
    
    return result.messages;
  }

  /**
   * Get email summary for AI processing
   */
  static async getEmailSummary(
    userId: string,
    timeframe: 'today' | 'yesterday' | 'week' = 'today',
    maxResults: number = 20
  ): Promise<{
    totalMessages: number;
    unreadCount: number;
    messages: ParsedGmailMessage[];
    summary: string;
  }> {
    let query = '';
    switch (timeframe) {
      case 'today':
        query = `after:${new Date().toISOString().split('T')[0]}`;
        break;
      case 'yesterday':
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        query = `after:${yesterday.toISOString().split('T')[0]} before:${new Date().toISOString().split('T')[0]}`;
        break;
      case 'week':
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        query = `after:${weekAgo.toISOString().split('T')[0]}`;
        break;
    }

    const result = await this.getMessages(userId, {
      query,
      maxResults,
    });

    const unreadResult = await this.getMessages(userId, {
      query: `${query} is:unread`,
      maxResults: 100,
    });

    return {
      totalMessages: result.totalResults,
      unreadCount: unreadResult.totalResults,
      messages: result.messages,
      summary: `Found ${result.totalResults} messages (${unreadResult.totalResults} unread) from ${timeframe}`,
    };
  }

  /**
   * Utility method to format message for display
   */
  static formatMessageForDisplay(message: ParsedGmailMessage): {
    title: string;
    subtitle: string;
    preview: string;
    timestamp: Date;
    isUnread: boolean;
    sender: string;
  } {
    const timestamp = new Date(message.date);
    
    return {
      title: message.subject || '(No Subject)',
      subtitle: message.from,
      preview: message.snippet,
      timestamp,
      isUnread: message.isUnread,
      sender: message.from,
    };
  }
} 