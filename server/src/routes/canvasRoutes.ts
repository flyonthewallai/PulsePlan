import express from 'express';
import { authenticate } from '../middleware/authenticate';
import { 
  uploadCanvasData,
  getCanvasIntegrationStatus,
  generateQRConnectionCode,
  completeExtensionConnection,
  testConnection
} from '../controllers/canvasController';

const router = express.Router();

// Canvas data upload endpoint (used by extension)
router.post('/upload-data', authenticate, uploadCanvasData);

// Get Canvas integration status
router.get('/status', authenticate, getCanvasIntegrationStatus);

// Generate QR code for extension connection
router.post('/generate-connection-code', authenticate, generateQRConnectionCode);

// Complete extension connection (via QR code/shortlink)
router.post('/connect-extension', authenticate, completeExtensionConnection);

// Test connection endpoint
router.get('/test-connection', testConnection);

// Assignment sync endpoint (for seamless Canvas → PulsePlan sync)
router.post('/sync-assignments', authenticate, async (req, res) => {
  try {
    const { assignments } = req.body;
    const userId = req.user?.id;
    
    if (!userId) {
      return res.status(401).json({ error: 'User not authenticated' });
    }
    
    if (!assignments || !Array.isArray(assignments)) {
      return res.status(400).json({ error: 'Invalid assignments data' });
    }
    
    console.log(`🔄 Syncing ${assignments.length} assignments for user ${userId}`);
    
    let syncedCount = 0;
    let updatedCount = 0;
    const errors: Array<{ assignment: string; error: string }> = [];
    
    // Import Supabase here to avoid circular dependencies
    const { createClient } = require('@supabase/supabase-js');
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL,
      process.env.SUPABASE_SERVICE_ROLE_KEY
    );
    
    for (const assignment of assignments) {
      try {
        // Check if assignment already exists by canvas_id
        const { data: existing, error: fetchError } = await supabase
          .from('assignments')
          .select('id, title, due_date')
          .eq('canvas_id', assignment.id)
          .eq('user_id', userId)
          .maybeSingle();
          
        if (fetchError && fetchError.code !== 'PGRST116') {
          throw fetchError;
        }
        
        const baseAssignmentData = {
          user_id: userId,
          title: assignment.title,
          description: assignment.description || '',
          due_date: assignment.dueDate,
          course_name: assignment.course,
          canvas_id: assignment.id,
          canvas_url: assignment.url,
          sync_source: 'canvas',
          confidence_score: assignment.confidence || 0.8,
          priority: assignment.priority || 'medium',
          estimated_minutes: assignment.estimatedMinutes || 60,
          status: 'pending',
          updated_at: new Date().toISOString()
        };
        
        if (existing) {
          // Update existing assignment
          const { error: updateError } = await supabase
            .from('assignments')
            .update(baseAssignmentData)
            .eq('id', existing.id);
            
          if (updateError) throw updateError;
          updatedCount++;
          console.log(`📝 Updated: ${assignment.title}`);
        } else {
          // Create new assignment
          const newAssignmentData = {
            ...baseAssignmentData,
            created_at: new Date().toISOString()
          };
          
          const { error: insertError } = await supabase
            .from('assignments')
            .insert(newAssignmentData);
            
          if (insertError) throw insertError;
          syncedCount++;
          console.log(`➕ Created: ${assignment.title}`);
        }
        
      } catch (error: any) {
        console.error(`❌ Error syncing ${assignment.title}:`, error);
        errors.push({ 
          assignment: assignment.title, 
          error: error?.message || 'Unknown error' 
        });
      }
    }
    
    // Log sync activity
    try {
      await supabase
        .from('canvas_sync_log')
        .insert({
          user_id: userId,
          assignments_synced: syncedCount,
          assignments_updated: updatedCount,
          sync_source: 'canvas_extension',
          status: errors.length === 0 ? 'success' : (syncedCount > 0 ? 'partial' : 'failed'),
          sync_timestamp: new Date().toISOString()
        });
    } catch (logError) {
      console.error('Failed to log sync activity:', logError);
    }
    
    const totalProcessed = syncedCount + updatedCount;
    const message = `Successfully synced ${totalProcessed} assignments (${syncedCount} new, ${updatedCount} updated)`;
    
    console.log(`✅ Sync complete: ${message}`);
    
    res.json({
      success: true,
      synced: syncedCount,
      updated: updatedCount,
      total: totalProcessed,
      errors: errors,
      message: message
    });
    
  } catch (error: any) {
    console.error('❌ Assignment sync failed:', error);
    res.status(500).json({ 
      error: 'Sync failed', 
      details: error?.message || 'Unknown error'
    });
  }
});

export default router; 