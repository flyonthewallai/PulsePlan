/**
 * upload.js - Handles uploading assignments to the PulsePlan API
 * This is a background service worker that processes messages from the popup
 */

// API endpoints for Canvas data sync
const API_ENDPOINT = "http://localhost:5000/canvas/upload-data";
const SYNC_ENDPOINT = "http://localhost:5000/canvas/sync-assignments";

// Listen for messages from the popup and content scripts
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

  // Handle auth token from pulseplan.app
  if (message.action === "AUTH_TOKEN_DETECTED") {
    handleWebAuthToken(message, sender, sendResponse);
    return true; // Async response
  }
});

// Extension startup initialization
chrome.runtime.onStartup.addListener(() => {
  console.log("🚀 PulsePlan Extension Started");
  console.log(
    "PulsePlan: Check out the repo! https://github.com/flyonthewalldev/pulseplan"
  );
});

chrome.runtime.onInstalled.addListener(() => {
  console.log("🎉 PulsePlan Extension Installed/Updated");
  console.log(
    "PulsePlan: Check out the repo! https://github.com/flyonthewalldev/pulseplan"
  );
});

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

    // Send data to sync API
    const response = await fetchWithTimeout(SYNC_ENDPOINT, {
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
 * Handle authentication token received from pulseplan.app
 */
async function handleWebAuthToken(message, sender, sendResponse) {
  try {
    const { token, source, timestamp } = message;

    console.log("🔐 Auth Bridge: Received token from", source);

    // Validate token format (basic JWT check)
    if (!token || typeof token !== "string" || !token.includes(".")) {
      throw new Error("Invalid token format");
    }

    // Store the JWT token
    await saveToStorage({
      pulseplan_jwt: token,
      auth_source: source,
      auth_timestamp: timestamp,
      auth_method: "web_bridge",
    });

    console.log("✅ Auth Bridge: Token stored successfully");

    // Update extension badge to show connected status
    chrome.action.setBadgeText({ text: "✓" });
    chrome.action.setBadgeBackgroundColor({ color: "#10b981" });

    // Clear badge after 3 seconds
    setTimeout(() => {
      chrome.action.setBadgeText({ text: "" });
    }, 3000);

    // Notify all open popups of successful auth
    notifyPopupsOfAuth();

    sendResponse({
      success: true,
      message: "Authentication successful",
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("❌ Auth Bridge: Token storage failed:", error);
    sendResponse({
      success: false,
      error: error.message,
    });
  }
}

/**
 * Notify all open extension popups of successful authentication
 */
function notifyPopupsOfAuth() {
  // Send message to content scripts that might forward to popups
  chrome.tabs.query({ url: "*://*.instructure.com/*" }, (tabs) => {
    tabs.forEach((tab) => {
      chrome.tabs
        .sendMessage(tab.id, {
          action: "AUTH_STATUS_CHANGED",
          authenticated: true,
          source: "web_login",
        })
        .catch(() => {
          // Ignore errors for tabs without content script
        });
    });
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
