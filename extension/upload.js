/**
 * upload.js - Handles uploading assignments to the PulsePlan API
 * This is a background service worker that processes messages from the popup
 */

// API endpoint for Canvas data upload
const API_ENDPOINT =
  "https://api.pulseplan.flyonthewalldev.com/canvas/upload-data";

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "syncAssignments") {
    // Start the sync process
    syncAssignmentsToPulsePlan()
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

// Auto-sync logic: Check for new assignments periodically
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "autoSync") {
    console.log("🔄 Auto-sync triggered");
    performAutoSync();
  }
});

// Set up auto-sync alarm when extension starts
chrome.runtime.onStartup.addListener(() => {
  setupAutoSync();
});

chrome.runtime.onInstalled.addListener(() => {
  setupAutoSync();
});

function setupAutoSync() {
  // Create alarm for weekly auto-sync
  chrome.alarms.create("autoSync", {
    delayInMinutes: 60, // First sync after 1 hour
    periodInMinutes: 10080, // Then every week (7 days * 24 hours * 60 minutes)
  });
  console.log("📅 Auto-sync scheduled for weekly intervals");
}

async function performAutoSync() {
  try {
    // Check if user is logged in
    const { pulseplan_jwt } = await getFromStorage(["pulseplan_jwt"]);

    if (!pulseplan_jwt) {
      console.log("⚠️ Auto-sync skipped: User not logged in");
      return;
    }

    // Check if there are unsynced assignments
    const { canvas_assignments } = await getFromStorage(["canvas_assignments"]);
    const unsyncedAssignments = (canvas_assignments || []).filter(
      (a) => !a.synced
    );

    if (unsyncedAssignments.length === 0) {
      console.log("✅ Auto-sync: No new assignments to sync");
      return;
    }

    // Perform sync
    const result = await syncAssignmentsToPulsePlan();
    console.log(`🎉 Auto-sync completed: ${result.count} assignments synced`);

    // Update badge to show sync status
    chrome.action.setBadgeText({ text: "" });
    chrome.action.setBadgeBackgroundColor({ color: "#4CAF50" });
  } catch (error) {
    console.error("❌ Auto-sync failed:", error);
    // Show error badge
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "#F44336" });
  }
}

/**
 * Main function to sync assignments to PulsePlan
 * Gets assignments from storage, authenticates, and sends to the API
 */
async function syncAssignmentsToPulsePlan() {
  try {
    // Get the auth token and assignments from storage
    const { pulseplan_jwt, canvas_assignments } = await getFromStorage([
      "pulseplan_jwt",
      "canvas_assignments",
    ]);

    // Check if user is logged in
    if (!pulseplan_jwt) {
      throw new Error("Not logged in. Please log in to PulsePlan first.");
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
        Authorization: `Bearer ${pulseplan_jwt}`,
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
