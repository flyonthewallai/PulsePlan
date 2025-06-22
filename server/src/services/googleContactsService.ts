import { google } from 'googleapis';
import { getOAuth2Client } from '../config/google';
import supabase from '../config/supabase';

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

class GoogleContactsService {
  private async getAuthenticatedClient(userId: string) {
    if (!supabase) {
      throw new Error('Supabase not configured');
    }

    // Get user's Google tokens from database
    const { data, error } = await supabase
      .from('calendar_connections')
      .select('access_token, refresh_token, expires_at')
      .eq('user_id', userId)
      .eq('provider', 'google')
      .single();

    if (error || !data) {
      throw new Error('Google account not connected');
    }

    const oauth2Client = getOAuth2Client();
    oauth2Client.setCredentials({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expiry_date: data.expires_at ? new Date(data.expires_at).getTime() : undefined,
    });

    return oauth2Client;
  }

  /**
   * Get all contacts for a user
   */
  async getContacts(userId: string, pageSize: number = 100, pageToken?: string): Promise<ContactsResponse> {
    try {
      const auth = await this.getAuthenticatedClient(userId);
      const people = google.people({ version: 'v1', auth });

      const response = await people.people.connections.list({
        resourceName: 'people/me',
        pageSize,
        pageToken,
        personFields: 'names,emailAddresses,phoneNumbers,organizations,photos',
        sortOrder: 'LAST_MODIFIED_DESCENDING',
      });

      const contacts: Contact[] = (response.data.connections || []).map(person => ({
        resourceName: person.resourceName || '',
        displayName: person.names?.[0]?.displayName || 'Unknown',
        emailAddresses: person.emailAddresses?.map(email => ({
          value: email.value || '',
          type: email.type || undefined,
          formattedType: email.formattedType || undefined,
        })),
        phoneNumbers: person.phoneNumbers?.map(phone => ({
          value: phone.value || '',
          type: phone.type || undefined,
          formattedType: phone.formattedType || undefined,
        })),
        organizations: person.organizations?.map(org => ({
          name: org.name || '',
          title: org.title || undefined,
        })),
        photos: person.photos?.map(photo => ({
          url: photo.url || '',
        })),
      }));

      return {
        contacts,
        totalCount: response.data.totalItems || contacts.length,
        nextPageToken: response.data.nextPageToken || undefined,
      };
    } catch (error) {
      console.error('Error fetching Google contacts:', error);
      throw new Error('Failed to fetch contacts');
    }
  }

  /**
   * Search contacts by query
   */
  async searchContacts(userId: string, query: string, pageSize: number = 50): Promise<ContactsResponse> {
    try {
      const auth = await this.getAuthenticatedClient(userId);
      const people = google.people({ version: 'v1', auth });

      const response = await people.people.searchContacts({
        query,
        pageSize,
        readMask: 'names,emailAddresses,phoneNumbers,organizations,photos',
      });

      const contacts: Contact[] = (response.data.results || []).map(result => {
        const person = result.person;
        return {
          resourceName: person?.resourceName || '',
          displayName: person?.names?.[0]?.displayName || 'Unknown',
          emailAddresses: person?.emailAddresses?.map(email => ({
            value: email.value || '',
            type: email.type || undefined,
            formattedType: email.formattedType || undefined,
          })),
          phoneNumbers: person?.phoneNumbers?.map(phone => ({
            value: phone.value || '',
            type: phone.type || undefined,
            formattedType: phone.formattedType || undefined,
          })),
          organizations: person?.organizations?.map(org => ({
            name: org.name || '',
            title: org.title || undefined,
          })),
          photos: person?.photos?.map(photo => ({
            url: photo.url || '',
          })),
        };
      });

      return {
        contacts,
        totalCount: contacts.length,
      };
    } catch (error) {
      console.error('Error searching Google contacts:', error);
      throw new Error('Failed to search contacts');
    }
  }

  /**
   * Get a specific contact by resource name
   */
  async getContact(userId: string, resourceName: string): Promise<Contact> {
    try {
      const auth = await this.getAuthenticatedClient(userId);
      const people = google.people({ version: 'v1', auth });

      const response = await people.people.get({
        resourceName,
        personFields: 'names,emailAddresses,phoneNumbers,organizations,photos,addresses,birthdays',
      });

      const person = response.data;
      return {
        resourceName: person.resourceName || '',
        displayName: person.names?.[0]?.displayName || 'Unknown',
        emailAddresses: person.emailAddresses?.map(email => ({
          value: email.value || '',
          type: email.type || undefined,
          formattedType: email.formattedType || undefined,
        })),
        phoneNumbers: person.phoneNumbers?.map(phone => ({
          value: phone.value || '',
          type: phone.type || undefined,
          formattedType: phone.formattedType || undefined,
        })),
        organizations: person.organizations?.map(org => ({
          name: org.name || '',
          title: org.title || undefined,
        })),
        photos: person.photos?.map(photo => ({
          url: photo.url || '',
        })),
      };
    } catch (error) {
      console.error('Error fetching Google contact:', error);
      throw new Error('Failed to fetch contact');
    }
  }

  /**
   * Get contacts with email addresses only
   */
  async getContactsWithEmails(userId: string): Promise<Contact[]> {
    try {
      const response = await this.getContacts(userId, 1000); // Get more contacts for email filtering
      return response.contacts.filter(contact => 
        contact.emailAddresses && contact.emailAddresses.length > 0
      );
    } catch (error) {
      console.error('Error fetching contacts with emails:', error);
      throw new Error('Failed to fetch contacts with emails');
    }
  }

  /**
   * Get contacts with phone numbers only
   */
  async getContactsWithPhones(userId: string): Promise<Contact[]> {
    try {
      const response = await this.getContacts(userId, 1000); // Get more contacts for phone filtering
      return response.contacts.filter(contact => 
        contact.phoneNumbers && contact.phoneNumbers.length > 0
      );
    } catch (error) {
      console.error('Error fetching contacts with phones:', error);
      throw new Error('Failed to fetch contacts with phone numbers');
    }
  }

  /**
   * Find contact by email address
   */
  async findContactByEmail(userId: string, email: string): Promise<Contact | null> {
    try {
      const contacts = await this.getContactsWithEmails(userId);
      return contacts.find(contact => 
        contact.emailAddresses?.some(emailAddr => 
          emailAddr.value.toLowerCase() === email.toLowerCase()
        )
      ) || null;
    } catch (error) {
      console.error('Error finding contact by email:', error);
      throw new Error('Failed to find contact by email');
    }
  }

  /**
   * Get contact groups
   */
  async getContactGroups(userId: string): Promise<any[]> {
    try {
      const auth = await this.getAuthenticatedClient(userId);
      const people = google.people({ version: 'v1', auth });

      const response = await people.contactGroups.list({
        groupFields: 'name,groupType,memberCount',
      });

      return response.data.contactGroups || [];
    } catch (error) {
      console.error('Error fetching contact groups:', error);
      throw new Error('Failed to fetch contact groups');
    }
  }
}

export const googleContactsService = new GoogleContactsService(); 