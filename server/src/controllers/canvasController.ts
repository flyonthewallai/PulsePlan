import { Response } from 'express';
import supabase from '../config/supabase';
import { AuthenticatedRequest } from '../middleware/authenticate';
import crypto from 'crypto';

interface CanvasAssignment {
  id: string;
  title: string;
  course: string;
  dueDate?: string;
  url?: string;
  grade?: string;
  points?: number;
  maxPoints?: number;
  status?: string;
  scraped: string;
}

interface CanvasUploadPayload {
  assignments: CanvasAssignment[];
  source: string;
  version: string;
}

// POST /canvas/upload-data
export const uploadCanvasData = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  const userId = req.user?.id;
  const { assignments, source, version }: CanvasUploadPayload = req.body;

  if (!assignments || !Array.isArray(assignments)) {
    return res.status(400).json({ error: 'Invalid assignments data' });
  }

  try {
    console.log(`📚 Processing ${assignments.length} Canvas assignments for user ${userId}`);

    // Convert Canvas assignments to PulsePlan tasks
    const tasks = assignments.map(assignment => ({
      user_id: userId,
      title: assignment.title,
      description: `Canvas Assignment from ${assignment.course}${assignment.url ? `\n\nLink: ${assignment.url}` : ''}`,
      subject: assignment.course,
      due_date: assignment.dueDate || null,
      estimated_minutes: 60, // Default estimate
      status: assignment.status === 'completed' ? 'completed' : 'pending',
      priority: 'medium',
      source: 'canvas',
      canvas_id: assignment.id,
      canvas_url: assignment.url,
      canvas_grade: assignment.grade,
      canvas_points: assignment.points,
      canvas_max_points: assignment.maxPoints,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }));

    // Batch insert/upsert tasks
    const { data, error } = await supabase
      .from('tasks')
      .upsert(tasks, { 
        onConflict: 'canvas_id',
        ignoreDuplicates: false 
      })
      .select();

    if (error) {
      console.error('Error inserting Canvas tasks:', error);
      return res.status(500).json({ error: error.message });
    }

    // Update Canvas integration status
    await supabase
      .from('canvas_integrations')
      .upsert({
        user_id: userId,
        last_sync: new Date().toISOString(),
        assignments_synced: assignments.length,
        extension_version: version,
        sync_source: source,
        is_active: true
      }, { onConflict: 'user_id' });

    console.log(`✅ Successfully synced ${assignments.length} Canvas assignments`);

    res.json({
      success: true,
      count: assignments.length,
      message: `Successfully synced ${assignments.length} assignments from Canvas`
    });

  } catch (error) {
    console.error('Canvas upload error:', error);
    res.status(500).json({ error: 'Failed to process Canvas data' });
  }
};

// GET /canvas/status
export const getCanvasIntegrationStatus = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  const userId = req.user?.id;

  try {
    const { data, error } = await supabase
      .from('canvas_integrations')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error && error.code !== 'PGRST116') { // PGRST116 = not found
      return res.status(500).json({ error: error.message });
    }

    // Get count of Canvas-sourced tasks
    const { count: canvasTasksCount } = await supabase
      .from('tasks')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId)
      .eq('source', 'canvas');

    res.json({
      connected: !!data?.is_active,
      lastSync: data?.last_sync || null,
      assignmentsSynced: data?.assignments_synced || 0,
      extensionVersion: data?.extension_version || null,
      totalCanvasTasks: canvasTasksCount || 0,
      connectionCode: data?.connection_code || null,
      connectionCodeExpiry: data?.connection_code_expiry || null
    });

  } catch (error) {
    console.error('Canvas status error:', error);
    res.status(500).json({ error: 'Failed to get Canvas integration status' });
  }
};

// POST /canvas/generate-connection-code
export const generateQRConnectionCode = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  const userId = req.user?.id;

  try {
    // Generate a secure connection code
    const connectionCode = crypto.randomBytes(32).toString('hex');
    const expiryTime = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes

    // Store connection code in database
    const { error } = await supabase
      .from('canvas_integrations')
      .upsert({
        user_id: userId,
        connection_code: connectionCode,
        connection_code_expiry: expiryTime.toISOString(),
        is_active: false // Will be activated when extension connects
      }, { onConflict: 'user_id' });

    if (error) {
      return res.status(500).json({ error: error.message });
    }

    // Generate QR code URL (using a QR code service or return data for client-side generation)
    const connectUrl = `${process.env.CLIENT_URL || 'http://localhost:19006'}/connect-canvas?code=${connectionCode}`;
    const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(connectUrl)}`;

    res.json({
      connectionCode,
      connectUrl,
      qrCodeUrl,
      expiresAt: expiryTime.toISOString()
    });

  } catch (error) {
    console.error('QR code generation error:', error);
    res.status(500).json({ error: 'Failed to generate connection code' });
  }
};

// POST /canvas/connect-extension
export const completeExtensionConnection = async (req: AuthenticatedRequest, res: Response) => {
  if (!supabase) {
    return res.status(500).json({ error: "Supabase is not configured on the server." });
  }

  const userId = req.user?.id;
  const { connectionCode } = req.body;

  if (!connectionCode) {
    return res.status(400).json({ error: 'Connection code is required' });
  }

  try {
    // Verify connection code
    const { data: integration, error } = await supabase
      .from('canvas_integrations')
      .select('*')
      .eq('user_id', userId)
      .eq('connection_code', connectionCode)
      .single();

    if (error || !integration) {
      return res.status(400).json({ error: 'Invalid connection code' });
    }

    // Check if code has expired
    if (new Date() > new Date(integration.connection_code_expiry)) {
      return res.status(400).json({ error: 'Connection code has expired' });
    }

    // Activate the connection
    const { error: updateError } = await supabase
      .from('canvas_integrations')
      .update({
        is_active: true,
        connected_at: new Date().toISOString(),
        connection_code: null, // Clear the code after use
        connection_code_expiry: null
      })
      .eq('user_id', userId);

    if (updateError) {
      return res.status(500).json({ error: updateError.message });
    }

    res.json({
      success: true,
      message: 'Canvas extension successfully connected!',
      connectedAt: new Date().toISOString()
    });

  } catch (error) {
    console.error('Extension connection error:', error);
    res.status(500).json({ error: 'Failed to connect extension' });
  }
};

// GET /canvas/test-connection
export const testConnection = async (req: any, res: Response) => {
  res.json({
    success: true,
    message: 'Canvas API is working',
    timestamp: new Date().toISOString()
  });
}; 