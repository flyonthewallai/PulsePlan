/**
 * upload.js - Handles uploading assignments to the Rhythm API
 * This is a background service worker that processes messages from the popup
 */

// API endpoint for Canvas data upload
const API_ENDPOINT =
  "https://api.rhythm.flyonthewalldev.com/upload_canvas_data";

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "syncAssignments") {
    // Start the sync process
    syncAssignmentsToRhythm()
      .then((result) => {
        sendResponse(result);
      })
      .catch((error) => {
        sendResponse({ success: false, error: error.message });
      });

    // Return true to indicate we'll respond asynchronously
    return true;
  }
});

/**
 * Main function to sync assignments to Rhythm
 * Gets assignments from storage, authenticates, and sends to the API
 */
async function syncAssignmentsToRhythm() {
  try {
    // Get the auth token and assignments from storage
    const { rhythm_jwt, canvas_assignments } = await getFromStorage([
      "rhythm_jwt",
      "canvas_assignments",
    ]);

    // Check if user is logged in
    if (!rhythm_jwt) {
      throw new Error("Not logged in. Please log in to Rhythm first.");
    }

    // Check if we have assignments to sync
    if (!canvas_assignments || canvas_assignments.length === 0) {
      return { success: true, count: 0, message: "No assignments to sync" };
    }

    // Filter to get only unsynced assignments
    const unsyncedAssignments = canvas_assignments.filter(
      (assignment) => !assignment.synced
    );

    if (unsyncedAssignments.length === 0) {
      return { success: true, count: 0, message: "No new assignments to sync" };
    }

    // Prepare the payload
    const payload = {
      assignments: unsyncedAssignments,
      source: "canvas_extension",
      version: chrome.runtime.getManifest().version,
    };

    // Send data to API
    const response = await fetchWithTimeout(API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${rhythm_jwt}`,
      },
      body: JSON.stringify(payload),
      // Add timeout to prevent hanging requests
      timeout: 15000,
    });

    // Handle non-200 responses
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error (${response.status}): ${errorText}`);
    }

    // Parse the response
    const data = await response.json();

    // Mark assignments as synced in storage
    await markAssignmentsAsSynced(unsyncedAssignments);

    // Return success result
    return {
      success: true,
      count: unsyncedAssignments.length,
      message: data.message || "Assignments successfully synced",
    };
  } catch (error) {
    console.error("Sync error:", error);
    throw error;
  }
}

/**
 * Mark assignments as synced in storage
 */
async function markAssignmentsAsSynced(syncedAssignments) {
  // Get current assignments
  const { canvas_assignments } = await getFromStorage(["canvas_assignments"]);

  if (!canvas_assignments) return;

  // Create a set of synced IDs for faster lookup
  const syncedIds = new Set(syncedAssignments.map((a) => a.id));

  // Update the synced flag for each assignment
  const updatedAssignments = canvas_assignments.map((assignment) => {
    if (syncedIds.has(assignment.id)) {
      return {
        ...assignment,
        synced: true,
        syncedAt: new Date().toISOString(),
      };
    }
    return assignment;
  });

  // Save back to storage
  await saveToStorage({
    canvas_assignments: updatedAssignments,
    unsynced_count: 0,
  });
}

/**
 * Promise-based wrapper for chrome.storage.local.get
 */
function getFromStorage(keys) {
  return new Promise((resolve) => {
    chrome.storage.local.get(keys, (result) => {
      resolve(result);
    });
  });
}

/**
 * Promise-based wrapper for chrome.storage.local.set
 */
function saveToStorage(items) {
  return new Promise((resolve) => {
    chrome.storage.local.set(items, () => {
      resolve();
    });
  });
}

/**
 * Fetch with timeout to prevent hanging requests
 */
async function fetchWithTimeout(url, options = {}) {
  const { timeout = 8000, ...fetchOptions } = options;

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    if (error.name === "AbortError") {
      throw new Error("Request timed out");
    }
    throw error;
  }
}
