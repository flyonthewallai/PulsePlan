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

  // Initialize UI
  initializeUI();

  // Add event listener for the sync button
  syncButton.addEventListener("click", handleSync);

  // Function to initialize the popup UI
  function initializeUI() {
    // Check if user is logged in
    chrome.storage.local.get(["rhythm_jwt"], function (result) {
      if (!result.rhythm_jwt) {
        syncButton.disabled = true;
        loginSection.style.display = "block";
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
            syncButton.textContent = "Sync to Rhythm";
            syncButton.disabled = true;
          }, 3000);
        } else {
          // Handle errors
          syncButton.textContent = "Sync to Rhythm";
          syncButton.disabled = false;
          messageElement.textContent = `Error: ${
            response.error || "Unknown error occurred."
          }`;
          messageElement.classList.add("error");
        }
      }
    );
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
