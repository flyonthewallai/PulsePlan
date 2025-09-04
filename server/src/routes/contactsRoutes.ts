import express from 'express';
import { 
  initiateGoogleAuth,
  handleGoogleCallback,
  disconnectGoogle
} from '../controllers/googleAuthController';

const router = express.Router();

/**
 * Google Contacts OAuth Routes
 * These use the same Google OAuth infrastructure but are specifically for Contacts access
 */

/**
 * @route   GET /contacts/auth
 * @desc    Initiate Google OAuth flow specifically for Contacts
 * @access  Public
 */
router.get('/auth', (req, res) => {
  // Add a source parameter to track that this is from Contacts settings
  req.query.source = 'contacts';
  initiateGoogleAuth(req, res);
});

/**
 * @route   GET /contacts/auth/callback
 * @desc    Handle Google OAuth callback for Contacts
 * @access  Public
 */
router.get('/auth/callback', handleGoogleCallback);

/**
 * @route   DELETE /contacts/disconnect/:userId
 * @desc    Disconnect Google Contacts integration
 * @access  Private
 */
router.delete('/disconnect/:userId', disconnectGoogle);

/**
 * @route   GET /contacts/status/:userId
 * @desc    Get Google Contacts connection status
 * @access  Private
 */
router.get('/status/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    
    // Use the same connection status logic as calendar
    const baseUrl = process.env.NODE_ENV === 'production' 
      ? 'https://api.pulseplan.app' 
      : `http://localhost:${process.env.PORT || 5000}`;
    const response = await fetch(`${baseUrl}/calendar/status/${userId}`);
    const status = await response.json();
    
    // Filter to only show Google connections and add Contacts-specific messaging
    const contactsStatus = {
      connected: status.providers?.some((p: any) => p.provider === 'google' && p.isActive) || false,
      providers: status.providers?.filter((p: any) => p.provider === 'google') || []
    };
    
    res.json(contactsStatus);
  } catch (error) {
    console.error('Error getting Google Contacts status:', error);
    res.status(500).json({ error: 'Failed to get Google Contacts connection status' });
  }
});

/**
 * @route   GET /contacts/list
 * @desc    Get all contacts for a user
 * @access  Private
 */
router.get('/list', async (req, res) => {
  try {
    const { userId, pageSize = '100', pageToken } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    const { googleContactsService } = await import('../services/googleContactsService.js');
    const result = await googleContactsService.getContacts(
      userId as string,
      parseInt(pageSize as string),
      pageToken as string
    );
    
    res.json(result);
  } catch (error) {
    console.error('Error fetching contacts:', error);
    res.status(500).json({ error: 'Failed to fetch contacts' });
  }
});

/**
 * @route   GET /contacts/search
 * @desc    Search contacts by query
 * @access  Private
 */
router.get('/search', async (req, res) => {
  try {
    const { userId, query, pageSize = '50' } = req.query;
    
    if (!userId || !query) {
      return res.status(400).json({ error: 'User ID and query are required' });
    }

    const { googleContactsService } = await import('../services/googleContactsService.js');
    const result = await googleContactsService.searchContacts(
      userId as string,
      query as string,
      parseInt(pageSize as string)
    );
    
    res.json(result);
  } catch (error) {
    console.error('Error searching contacts:', error);
    res.status(500).json({ error: 'Failed to search contacts' });
  }
});

/**
 * @route   GET /contacts/get
 * @desc    Get a specific contact by resource name
 * @access  Private
 */
router.get('/get', async (req, res) => {
  try {
    const { userId, resourceName } = req.query;
    
    if (!userId || !resourceName) {
      return res.status(400).json({ error: 'User ID and resource name are required' });
    }

    const { googleContactsService } = await import('../services/googleContactsService.js');
    const contact = await googleContactsService.getContact(
      userId as string,
      resourceName as string
    );
    
    res.json(contact);
  } catch (error) {
    console.error('Error fetching contact:', error);
    res.status(500).json({ error: 'Failed to fetch contact' });
  }
});

/**
 * @route   GET /contacts/filter
 * @desc    Get contacts filtered by type (emails, phones)
 * @access  Private
 */
router.get('/filter', async (req, res) => {
  try {
    const { userId, filter } = req.query;
    
    if (!userId || !filter) {
      return res.status(400).json({ error: 'User ID and filter are required' });
    }

    const { googleContactsService } = await import('../services/googleContactsService.js');
    
    let contacts;
    if (filter === 'emails') {
      contacts = await googleContactsService.getContactsWithEmails(userId as string);
    } else if (filter === 'phones') {
      contacts = await googleContactsService.getContactsWithPhones(userId as string);
    } else {
      return res.status(400).json({ error: 'Invalid filter. Use "emails" or "phones"' });
    }
    
    res.json({ contacts });
  } catch (error) {
    console.error('Error filtering contacts:', error);
    res.status(500).json({ error: 'Failed to filter contacts' });
  }
});

/**
 * @route   GET /contacts/find-by-email
 * @desc    Find contact by email address
 * @access  Private
 */
router.get('/find-by-email', async (req, res) => {
  try {
    const { userId, email } = req.query;
    
    if (!userId || !email) {
      return res.status(400).json({ error: 'User ID and email are required' });
    }

    const { googleContactsService } = await import('../services/googleContactsService.js');
    const contact = await googleContactsService.findContactByEmail(
      userId as string,
      email as string
    );
    
    if (!contact) {
      return res.status(404).json({ error: 'Contact not found' });
    }
    
    res.json(contact);
  } catch (error) {
    console.error('Error finding contact by email:', error);
    res.status(500).json({ error: 'Failed to find contact by email' });
  }
});

/**
 * @route   GET /contacts/groups
 * @desc    Get contact groups
 * @access  Private
 */
router.get('/groups', async (req, res) => {
  try {
    const { userId } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    const { googleContactsService } = await import('../services/googleContactsService.js');
    const groups = await googleContactsService.getContactGroups(userId as string);
    
    res.json({ groups });
  } catch (error) {
    console.error('Error fetching contact groups:', error);
    res.status(500).json({ error: 'Failed to fetch contact groups' });
  }
});

export default router; 