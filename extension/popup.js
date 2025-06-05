/**
 * popup.js - Handles popup UI interactions and sync triggering
 */

document.addEventListener("DOMContentLoaded", function () {
  const assignmentCountElement = document.getElementById("assignmentCount");
  const lastScanElement = document.getElementById("lastScan");
  const unsyncedCountElement = document.getElementById("unsyncedCount");
  const syncButton = document.getElementById("syncButton");
  const messageElement = document.getElementById("message");
  const loginSection = document.getElementById("loginSection");
  const connectionSection = document.getElementById("connectionSection");
  const scanQRButton = document.getElementById("scanQRButton");

  // Initialize UI
  initializeUI();

  // Add event listeners
  syncButton.addEventListener("click", handleSync);
  scanQRButton.addEventListener("click", handleQRScan);

  // Function to initialize the popup UI
  function initializeUI() {
    // Check if user is logged in
    chrome.storage.local.get(["pulseplan_jwt"], function (result) {
      if (!result.pulseplan_jwt) {
        syncButton.disabled = true;
        loginSection.style.display = "block";
        connectionSection.style.display = "block";
      }
    });

    // Get and display assignment stats
    chrome.storage.local.get(
      ["canvas_assignments", "last_scan", "unsynced_count"],
      function (result) {
        const assignments = result.canvas_assignments || [];
        const lastScan = result.last_scan;
        const unsyncedCount = result.unsynced_count || assignments.length;

        // Update UI
        assignmentCountElement.textContent = assignments.length;

        if (lastScan) {
          const lastScanDate = new Date(lastScan);
          lastScanElement.textContent = formatDate(lastScanDate);
        }

        unsyncedCountElement.textContent = unsyncedCount;

        // Disable sync button if no unsynced assignments
        if (unsyncedCount === 0) {
          syncButton.disabled = true;
          messageElement.textContent = "No new assignments to sync.";
        }
      }
    );
  }

  // Function to handle sync button click
  function handleSync() {
    // Disable the button to prevent multiple clicks
    syncButton.disabled = true;
    syncButton.textContent = "Syncing...";
    messageElement.textContent = "";
    messageElement.classList.remove("success", "error");

    // Send a message to the background script to start the sync
    chrome.runtime.sendMessage(
      { action: "syncAssignments" },
      function (response) {
        if (response.success) {
          // Update UI with success message
          syncButton.textContent = "Sync Complete!";
          messageElement.textContent = `Successfully synced ${response.count} assignments.`;
          messageElement.classList.add("success");

          // Update unsynced count
          unsyncedCountElement.textContent = "0";

          // Re-enable button after a delay
          setTimeout(() => {
            syncButton.textContent = "Sync to PulsePlan";
            syncButton.disabled = true;
          }, 3000);
        } else {
          // Handle errors
          syncButton.textContent = "Sync to PulsePlan";
          syncButton.disabled = false;
          messageElement.textContent = `Error: ${
            response.error || "Unknown error occurred."
          }`;
          messageElement.classList.add("error");
        }
      }
    );
  }

  // Function to handle QR code scanning
  async function handleQRScan() {
    try {
      messageElement.textContent = "Opening QR scanner...";
      messageElement.className = "message";

      // For demo purposes, we'll use a simple prompt
      // In a real implementation, you'd integrate a QR code library
      const qrData = prompt("Paste the connection URL from PulsePlan app:");

      if (qrData) {
        await handleQRCodeDetected(qrData);
      }
    } catch (error) {
      console.error("QR scanning error:", error);
      messageElement.textContent = "QR scanning failed. Please try again.";
      messageElement.className = "message error";
    }
  }

  // Function to handle detected QR code
  async function handleQRCodeDetected(qrData) {
    try {
      // Extract connection code from QR data
      let connectionCode;

      if (qrData.includes("code=")) {
        const url = new URL(qrData);
        connectionCode = url.searchParams.get("code");
      } else {
        // Assume the input is the connection code itself
        connectionCode = qrData.trim();
      }

      if (!connectionCode) {
        throw new Error("Invalid connection data");
      }

      await connectWithCode(connectionCode);
    } catch (error) {
      console.error("QR code processing error:", error);
      messageElement.textContent = "Invalid connection data. Please try again.";
      messageElement.className = "message error";
    }
  }

  // Function to connect using connection code
  async function connectWithCode(connectionCode) {
    try {
      messageElement.textContent = "Connecting to PulsePlan...";
      messageElement.className = "message";

      // Send connection request to PulsePlan API
      const response = await fetch(
        "https://api.pulseplan.flyonthewalldev.com/canvas/connect-extension",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ connectionCode }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Connection failed");
      }

      const result = await response.json();

      // Store connection info (we'll get JWT from login)
      chrome.storage.local.set({
        canvas_connected: true,
        connected_at: new Date().toISOString(),
        connection_message: result.message,
      });

      messageElement.textContent =
        result.message || "Successfully connected to PulsePlan!";
      messageElement.className = "message success";

      // Hide connection section
      connectionSection.style.display = "none";

      // User still needs to log in to get JWT for syncing
      if (!syncButton.disabled) {
        loginSection.style.display = "none";
      }
    } catch (error) {
      console.error("Connection error:", error);
      messageElement.textContent = `Connection failed: ${error.message}`;
      messageElement.className = "message error";
    }
  }

  // Helper function to format date
  function formatDate(date) {
    // Simple date/time formatting
    const now = new Date();
    const isToday = now.toDateString() === date.toDateString();

    if (isToday) {
      return `Today at ${date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })}`;
    } else {
      return date.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }
  }
});
