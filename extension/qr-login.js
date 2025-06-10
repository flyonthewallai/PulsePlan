/**
 * QR Code Login Implementation for PulsePlan Canvas Extension
 */

// QR Login Session Management
let qrLoginSession = null;
let qrPollingInterval = null;

/**
 * Generate UUID for session ID
 */
function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c == "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Initialize QR code login
 */
async function initializeQRLogin() {
  try {
    console.log("🎯 Initializing QR code login...");

    // Generate unique session ID
    qrLoginSession = {
      sessionId: generateUUID(),
      timestamp: Date.now(),
      expiresAt: Date.now() + 10 * 60 * 1000, // 10 minutes
    };

    // Initialize session with server
    const initResponse = await fetch("http://localhost:5000/auth/qr-init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId: qrLoginSession.sessionId,
        extensionId: chrome.runtime.id,
      }),
    });

    if (!initResponse.ok) {
      throw new Error(`Server initialization failed: ${initResponse.status}`);
    }

    const initData = await initResponse.json();
    console.log("✅ QR session initialized:", initData);

    // QR code data for mobile app
    const qrData = {
      type: "pulseplan_extension_login",
      sessionId: qrLoginSession.sessionId,
      extensionId: chrome.runtime.id,
      timestamp: qrLoginSession.timestamp,
      serverUrl: "http://localhost:5000",
    };

    // Generate QR code using qrserver.com API
    const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(
      JSON.stringify(qrData)
    )}`;

    // Display QR code
    displayQRCode(qrCodeUrl);

    // Start polling for authentication
    startQRPolling();

    // Set up auto-refresh timer
    setupQRRefreshTimer();
  } catch (error) {
    console.error("❌ QR initialization failed:", error);
    showQRError("Failed to initialize QR login. Please try again.");
  }
}

/**
 * Display QR code in the popup
 */
function displayQRCode(qrCodeUrl) {
  const qrContainer = document.getElementById("qrContainer");
  const qrExpiry = document.getElementById("qrExpiry");

  if (!qrContainer) {
    console.error("QR container not found");
    return;
  }

  const expiryTime = new Date(qrLoginSession.expiresAt).toLocaleTimeString();

  qrContainer.innerHTML = `
    <img src="${qrCodeUrl}" alt="QR Code for Login" width="160" height="160">
  `;

  if (qrExpiry) {
    qrExpiry.textContent = `Expires at ${expiryTime}`;
  }
}

/**
 * Start polling for QR authentication
 */
function startQRPolling() {
  if (qrPollingInterval) {
    clearInterval(qrPollingInterval);
  }

  qrPollingInterval = setInterval(async () => {
    await checkQRAuthStatus();
  }, 2000); // Poll every 2 seconds

  console.log("🔄 Started QR polling");
}

/**
 * Check QR authentication status
 */
async function checkQRAuthStatus() {
  if (!qrLoginSession || Date.now() > qrLoginSession.expiresAt) {
    stopQRPolling();
    const qrContainer = document.getElementById("qrContainer");
    if (qrContainer) {
      qrContainer.innerHTML = "<p>QR code expired. Please refresh.</p>";
    }
    showQRError("QR code expired. Please refresh.");
    return;
  }

  try {
    const response = await fetch(
      `http://localhost:5000/auth/qr-status/${qrLoginSession.sessionId}`
    );
    const data = await response.json();

    if (data.authenticated) {
      // Success! Store the token
      await chrome.storage.local.set({
        pulseplan_jwt: data.token,
        auth_source: "qr_code",
        auth_timestamp: Date.now(),
        user_id: data.userId,
      });

      console.log("✅ QR authentication successful!");
      stopQRPolling();
      showQRSuccess();

      // Update main popup UI
      if (typeof showConnectedState === "function") {
        showConnectedState();
      }

      // Hide QR section
      setTimeout(() => {
        const qrSection = document.getElementById("qrSection");
        if (qrSection) qrSection.style.display = "none";
      }, 2000);

      return;
    }

    if (data.error && data.error.includes("expired")) {
      stopQRPolling();
      showQRError("QR code expired. Please refresh.");
    }
  } catch (error) {
    console.error("QR polling error:", error);
    // Don't stop polling for network errors, just log them
  }
}

/**
 * Stop QR polling
 */
function stopQRPolling() {
  if (qrPollingInterval) {
    clearInterval(qrPollingInterval);
    qrPollingInterval = null;
  }
}

/**
 * Setup auto-refresh timer for QR code
 */
function setupQRRefreshTimer() {
  const refreshTime = qrLoginSession.expiresAt - Date.now() - 30000; // 30 seconds before expiry

  if (refreshTime > 0) {
    setTimeout(() => {
      if (qrLoginSession && !qrLoginSession.authenticated) {
        console.log("🔄 Auto-refreshing QR code...");
        refreshQRCode();
      }
    }, refreshTime);
  }
}

/**
 * Refresh QR code
 */
function refreshQRCode() {
  stopQRPolling();
  initializeQRLogin();
}

/**
 * Show QR success message
 */
function showQRSuccess() {
  const statusElement = document.getElementById("qrStatus");
  if (statusElement) {
    statusElement.className = "qr-status success";
    statusElement.innerHTML = "<span>✅ Login successful!</span>";
  }
}

/**
 * Show QR error message
 */
function showQRError(message) {
  const statusElement = document.getElementById("qrStatus");
  if (statusElement) {
    statusElement.className = "qr-status error";
    statusElement.innerHTML = `<span>❌ ${message}</span>`;
  }
}

/**
 * Show QR login section
 */
function showQRLogin() {
  const qrSection = document.getElementById("qrSection");
  if (qrSection) {
    qrSection.style.display = "block";
    initializeQRLogin();
  }
}

/**
 * Hide QR login section
 */
function hideQRLogin() {
  const qrSection = document.getElementById("qrSection");
  if (qrSection) {
    qrSection.style.display = "none";
  }
  stopQRPolling();
}

// Set up event listeners when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  const refreshButton = document.getElementById("refreshQRButton");
  const closeButton = document.getElementById("closeQRButton");

  if (refreshButton) {
    refreshButton.addEventListener("click", refreshQRCode);
  }

  if (closeButton) {
    closeButton.addEventListener("click", hideQRLogin);
  }
});

// Export functions for use in popup.js
window.QRLogin = {
  initialize: initializeQRLogin,
  show: showQRLogin,
  hide: hideQRLogin,
  refresh: refreshQRCode,
};
