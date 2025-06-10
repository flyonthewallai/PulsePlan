/**
 * popup.js - Enhanced UI interactions and sync handling for AI-powered Canvas extension
 */

document.addEventListener("DOMContentLoaded", function () {
  // UI Elements
  const assignmentCountElement = document.getElementById("assignmentCount");
  const lastScanElement = document.getElementById("lastScan");
  const unsyncedCountElement = document.getElementById("unsyncedCount");
  const extractionStatusElement = document.getElementById("extractionStatus");
  const aiConfidenceElement = document.getElementById("aiConfidence");
  const syncButton = document.getElementById("syncButton");
  const syncButtonText = document.getElementById("syncButtonText");
  const messageElement = document.getElementById("message");
  const loginSection = document.getElementById("loginSection");
  const connectionSection = document.getElementById("connectionSection");
  const scanQRButton = document.getElementById("scanQRButton");

  // Initialize UI
  initializeUI();

  // Add event listeners
  syncButton.addEventListener("click", handleSync);
  scanQRButton.addEventListener("click", handleQRScan);

  // Auto-refresh stats every 30 seconds
  setInterval(updateStats, 30000);

  // Listen for auth status changes from background script
  setupAuthStatusListener();

  /**
   * Initialize the popup UI with current data
   */
  function initializeUI() {
    showMessage("", "info");

    // Check if user is logged in
    chrome.storage.local.get(["pulseplan_jwt"], function (result) {
      if (!result.pulseplan_jwt) {
        syncButton.disabled = true;
        loginSection.style.display = "block";
        connectionSection.style.display = "block";
        updateExtractionStatus("login_required", "Login Required");
      } else {
        loginSection.style.display = "none";
        connectionSection.style.display = "none";
      }
    });

    // Load and display current stats
    updateStats();
  }

  /**
   * Update statistics display
   */
  function updateStats() {
    chrome.storage.local.get(
      [
        "canvas_assignments",
        "last_scan",
        "unsynced_count",
        "ai_confidence",
        "extraction_status",
      ],
      function (result) {
        const assignments = result.canvas_assignments || [];
        const lastScan = result.last_scan;
        const unsyncedCount = result.unsynced_count || assignments.length;
        const aiConfidence = result.ai_confidence;
        const extractionStatus = result.extraction_status;

        // Update assignment count with animation
        updateCountWithAnimation(assignmentCountElement, assignments.length);
        updateCountWithAnimation(unsyncedCountElement, unsyncedCount);

        // Update last scan time
        if (lastScan) {
          const lastScanDate = new Date(lastScan);
          lastScanElement.textContent = formatRelativeTime(lastScanDate);
        } else {
          lastScanElement.textContent = "Never";
        }

        // Update AI confidence
        if (aiConfidence !== undefined) {
          aiConfidenceElement.textContent = `${Math.round(
            aiConfidence * 100
          )}%`;
          aiConfidenceElement.className = `status-value ${
            aiConfidence > 0.8 ? "success" : aiConfidence > 0.6 ? "warning" : ""
          }`;
        } else {
          aiConfidenceElement.textContent = "-";
          aiConfidenceElement.className = "status-value";
        }

        // Update extraction status
        updateExtractionStatus(extractionStatus || "ready", "Ready");

        // Update sync button state
        updateSyncButtonState(unsyncedCount > 0);
      }
    );
  }

  /**
   * Update count with smooth animation
   */
  function updateCountWithAnimation(element, newValue) {
    const currentValue = parseInt(element.textContent) || 0;
    if (currentValue !== newValue) {
      // Simple counting animation
      const duration = 500;
      const steps = 20;
      const increment = (newValue - currentValue) / steps;
      let current = currentValue;
      let step = 0;

      const animate = () => {
        if (step < steps) {
          current += increment;
          element.textContent = Math.round(current);
          step++;
          setTimeout(animate, duration / steps);
        } else {
          element.textContent = newValue;
        }
      };

      animate();
    }
  }

  /**
   * Update extraction status with appropriate styling
   */
  function updateExtractionStatus(status, displayText) {
    extractionStatusElement.textContent = displayText;
    extractionStatusElement.className = "status-value";

    switch (status) {
      case "extracting":
        extractionStatusElement.className += " warning";
        break;
      case "success":
        extractionStatusElement.className += " success";
        break;
      case "error":
        extractionStatusElement.className += " error";
        break;
      case "login_required":
        extractionStatusElement.className += " warning";
        break;
      default:
        extractionStatusElement.className += " success";
    }
  }

  /**
   * Update sync button state and appearance
   */
  function updateSyncButtonState(hasUnsyncedItems) {
    if (hasUnsyncedItems) {
      syncButton.disabled = false;
      syncButtonText.textContent = "🚀 Sync to PulsePlan";
      clearMessage();
    } else {
      syncButton.disabled = true;
      syncButtonText.textContent = "✅ All Synced";
      showMessage("No new assignments to sync", "info");
    }
  }

  /**
   * Handle sync button click with enhanced UI feedback
   */
  function handleSync() {
    // Update button state
    syncButton.disabled = true;
    syncButtonText.innerHTML = '<span class="loading"></span>Syncing...';
    clearMessage();
    updateExtractionStatus("syncing", "Syncing...");

    // Send sync message to background script
    chrome.runtime.sendMessage(
      { action: "syncAssignments" },
      function (response) {
        if (response && response.success) {
          // Success state
          syncButtonText.innerHTML = "✅ Sync Complete!";
          showMessage(
            `Successfully synced ${response.count} assignments`,
            "success"
          );
          updateExtractionStatus("success", "Synced");

          // Update unsynced count
          unsyncedCountElement.textContent = "0";

          // Store success state
          chrome.storage.local.set({
            unsynced_count: 0,
            last_sync: new Date().toISOString(),
          });

          // Reset button after delay
          setTimeout(() => {
            updateSyncButtonState(false);
            updateExtractionStatus("ready", "Ready");
          }, 3000);
        } else {
          // Error state
          const errorMessage =
            response?.error || "Sync failed. Please try again.";
          syncButtonText.textContent = "🚀 Sync to PulsePlan";
          syncButton.disabled = false;
          showMessage(errorMessage, "error");
          updateExtractionStatus("error", "Sync Failed");

          // Auto-retry after delay if it's a network error
          if (
            errorMessage.toLowerCase().includes("network") ||
            errorMessage.toLowerCase().includes("timeout")
          ) {
            setTimeout(() => {
              showMessage("Retrying sync...", "info");
              handleSync();
            }, 5000);
          }
        }
      }
    );
  }

  /**
   * Handle QR code scanning with improved UX
   */
  async function handleQRScan() {
    try {
      showMessage("Generating QR code...", "info");
      scanQRButton.disabled = true;

      // Show QR code section
      const qrSection = document.getElementById("qrSection");
      if (qrSection) {
        qrSection.style.display = "block";
        // Initialize QR code if the function is available
        if (window.QRLogin && window.QRLogin.initialize) {
          await window.QRLogin.initialize();
        }
      }

      clearMessage();
    } catch (error) {
      console.error("QR scanning error:", error);
      showMessage("Failed to generate QR code. Please try again.", "error");
    } finally {
      scanQRButton.disabled = false;
    }
  }

  /**
   * Handle detected QR code with better validation
   */
  async function handleQRCodeDetected(qrData) {
    try {
      showMessage("Processing connection...", "info");

      // Extract connection code from various formats
      let connectionCode = extractConnectionCode(qrData);

      if (!connectionCode) {
        throw new Error("Invalid connection data format");
      }

      await connectWithCode(connectionCode);
    } catch (error) {
      console.error("QR code processing error:", error);
      showMessage(
        "Invalid connection data. Please check the QR code or URL.",
        "error"
      );
    }
  }

  /**
   * Extract connection code from various input formats
   */
  function extractConnectionCode(input) {
    // Handle URL format
    try {
      const url = new URL(input);
      const code =
        url.searchParams.get("code") || url.searchParams.get("connectionCode");
      if (code) return code;
    } catch {
      // Not a valid URL, continue
    }

    // Handle direct code format
    if (/^[a-zA-Z0-9]{6,}$/.test(input)) {
      return input;
    }

    // Handle other formats
    const codeMatch = input.match(/(?:code[=:]|connect[=:])\s*([a-zA-Z0-9]+)/i);
    return codeMatch ? codeMatch[1] : null;
  }

  /**
   * Connect using connection code with enhanced error handling
   */
  async function connectWithCode(connectionCode) {
    try {
      showMessage("Connecting to PulsePlan...", "info");

      const response = await fetch(
        "http://localhost:5000/canvas/connect-extension",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ connectionCode }),
          timeout: 10000, // 10 second timeout
        }
      );

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(
          errorData.error || `Connection failed (${response.status})`
        );
      }

      const result = await response.json();

      // Store connection info
      chrome.storage.local.set({
        canvas_connected: true,
        connected_at: new Date().toISOString(),
        connection_message: result.message,
      });

      showMessage(
        result.message || "Successfully connected to PulsePlan!",
        "success"
      );

      // Hide connection section
      connectionSection.style.display = "none";

      // Check if user is now logged in
      setTimeout(initializeUI, 1000);
    } catch (error) {
      console.error("Connection error:", error);
      let errorMessage = "Connection failed";

      if (
        error.message.includes("timeout") ||
        error.message.includes("network")
      ) {
        errorMessage =
          "Connection timeout. Please check your internet connection.";
      } else if (error.message.includes("404")) {
        errorMessage = "Invalid connection code. Please try again.";
      } else if (error.message) {
        errorMessage = error.message;
      }

      showMessage(errorMessage, "error");
    }
  }

  /**
   * Show message with enhanced styling and auto-hide
   */
  function showMessage(text, type = "info") {
    if (!text) {
      clearMessage();
      return;
    }

    messageElement.textContent = text;
    messageElement.className = `message ${type}`;
    messageElement.style.display = "flex";

    // Auto-hide success messages after 5 seconds
    if (type === "success") {
      setTimeout(() => {
        if (messageElement.classList.contains("success")) {
          clearMessage();
        }
      }, 5000);
    }
  }

  /**
   * Clear message display
   */
  function clearMessage() {
    messageElement.textContent = "";
    messageElement.className = "message";
    messageElement.style.display = "none";
  }

  /**
   * Format relative time for last scan display
   */
  function formatRelativeTime(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    // Format as date for older scans
    return date.toLocaleDateString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  /**
   * Handle window focus to refresh stats
   */
  window.addEventListener("focus", () => {
    updateStats();
  });

  /**
   * Set up authentication status listeners
   */
  function setupAuthStatusListener() {
    // Listen for storage changes (auth token updates)
    chrome.storage.onChanged.addListener((changes, namespace) => {
      if (namespace === "local" && changes.pulseplan_jwt) {
        const newToken = changes.pulseplan_jwt.newValue;
        const oldToken = changes.pulseplan_jwt.oldValue;

        // If token was added/changed
        if (newToken && newToken !== oldToken) {
          showMessage("🔐 Logged in via PulsePlan website!", "success");
          setTimeout(() => {
            initializeUI();
            clearMessage();
          }, 2000);
        }

        // If token was removed
        if (!newToken && oldToken) {
          showMessage("🔒 Logged out", "warning");
          setTimeout(initializeUI, 1000);
        }
      }
    });
  }

  // Initialize auth listener
  setupAuthStatusListener();

  /**
   * Listen for messages from content script
   */
  chrome.runtime.onMessage?.addListener((message, sender, sendResponse) => {
    if (message.action === "extractionUpdate") {
      updateStats();

      if (message.status === "extracting") {
        updateExtractionStatus("extracting", "AI Extracting...");
        showMessage("AI is analyzing the page...", "info");
      } else if (message.status === "complete") {
        updateExtractionStatus("success", "Extraction Complete");
        showMessage(`Found ${message.count || 0} new assignments`, "success");
      }
    }

    // Handle auth status changes from background script
    if (message.action === "AUTH_STATUS_CHANGED" && message.authenticated) {
      showMessage("✅ Authenticated via website!", "success");
      setTimeout(() => {
        initializeUI();
        clearMessage();
      }, 2000);
      sendResponse({ received: true });
    }
  });
});
