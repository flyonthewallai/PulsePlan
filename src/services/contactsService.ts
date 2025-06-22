import { API_BASE_URL } from '@/config/api';

export interface Contact {
  resourceName: string;
  displayName: string;
  emailAddresses?: Array<{
    value: string;
    type?: string;
    formattedType?: string;
  }>;
  phoneNumbers?: Array<{
    value: string;
    type?: string;
    formattedType?: string;
  }>;
  organizations?: Array<{
    name: string;
    title?: string;
  }>;
  photos?: Array<{
    url: string;
  }>;
}

export interface ContactsResponse {
  contacts: Contact[];
  totalCount: number;
  nextPageToken?: string;
}

export interface ConnectionStatus {
  connected: boolean;
  providers: Array<{
    provider: 'google' | 'apple';
    email: string;
    connectedAt: string;
    expiresAt?: string;
    isActive: boolean;
  }>;
}

class ContactsServiceClass {
  private baseUrl = `${API_BASE_URL}/contacts`;

  /**
   * Connect Google Contacts
   */
  async connectGoogle(userId: string): Promise<void> {
    const authUrl = `${this.baseUrl}/auth?userId=${encodeURIComponent(userId)}`;
    window.location.href = authUrl;
  }

  /**
   * Disconnect Google Contacts
   */
  async disconnectGoogle(userId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/disconnect/${userId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to disconnect Google Contacts');
    }
  }

  /**
   * Get connection status
   */
  async getConnectionStatus(userId: string): Promise<ConnectionStatus> {
    const response = await fetch(`${this.baseUrl}/status/${userId}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get connection status');
    }

    return response.json();
  }

  /**
   * Get all contacts
   */
  async getContacts(userId: string, pageSize: number = 100, pageToken?: string): Promise<ContactsResponse> {
    const params = new URLSearchParams({
      userId,
      pageSize: pageSize.toString(),
    });

    if (pageToken) {
      params.append('pageToken', pageToken);
    }

    const response = await fetch(`${this.baseUrl}/list?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch contacts');
    }

    return response.json();
  }

  /**
   * Search contacts
   */
  async searchContacts(userId: string, query: string, pageSize: number = 50): Promise<ContactsResponse> {
    const params = new URLSearchParams({
      userId,
      query,
      pageSize: pageSize.toString(),
    });

    const response = await fetch(`${this.baseUrl}/search?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to search contacts');
    }

    return response.json();
  }

  /**
   * Get a specific contact
   */
  async getContact(userId: string, resourceName: string): Promise<Contact> {
    const params = new URLSearchParams({
      userId,
      resourceName,
    });

    const response = await fetch(`${this.baseUrl}/get?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch contact');
    }

    return response.json();
  }

  /**
   * Get contacts with email addresses
   */
  async getContactsWithEmails(userId: string): Promise<Contact[]> {
    const params = new URLSearchParams({
      userId,
      filter: 'emails',
    });

    const response = await fetch(`${this.baseUrl}/filter?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch contacts with emails');
    }

    const data = await response.json();
    return data.contacts || [];
  }

  /**
   * Get contacts with phone numbers
   */
  async getContactsWithPhones(userId: string): Promise<Contact[]> {
    const params = new URLSearchParams({
      userId,
      filter: 'phones',
    });

    const response = await fetch(`${this.baseUrl}/filter?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch contacts with phones');
    }

    const data = await response.json();
    return data.contacts || [];
  }

  /**
   * Find contact by email
   */
  async findContactByEmail(userId: string, email: string): Promise<Contact | null> {
    const params = new URLSearchParams({
      userId,
      email,
    });

    const response = await fetch(`${this.baseUrl}/find-by-email?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error('Failed to find contact by email');
    }

    return response.json();
  }

  /**
   * Get contact groups
   */
  async getContactGroups(userId: string): Promise<any[]> {
    const params = new URLSearchParams({
      userId,
    });

    const response = await fetch(`${this.baseUrl}/groups?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch contact groups');
    }

    const data = await response.json();
    return data.groups || [];
  }
}

export const ContactsService = new ContactsServiceClass(); 