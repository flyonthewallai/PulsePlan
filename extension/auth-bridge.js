/**
 * auth-bridge.js - Content script that runs on pulseplan.app
 * Detects user authentication and transfers JWT to extension
 */

console.log("🔗 PulsePlan Auth Bridge: Content script loaded");

// Listen for authentication events from the website
function detectAuthentication() {
  // Method 1: Check for JWT in localStorage/sessionStorage
  const checkStorageAuth = () => {
    const possibleTokenKeys = [
      "pulseplan_token",
      "auth_token",
      "jwt_token",
      "supabase.auth.token",
      "sb-", // Supabase session keys start with this
    ];

    for (const key of possibleTokenKeys) {
      const token = localStorage.getItem(key) || sessionStorage.getItem(key);
      if (token) {
        try {
          // Try to parse if it's a Supabase session object
          const parsed = JSON.parse(token);
          if (parsed.access_token) {
            return parsed.access_token;
          }
          // Otherwise assume it's a direct JWT
          return token;
        } catch {
          // If not JSON, assume it's a direct JWT
          if (token.includes(".")) {
            // JWT format check
            return token;
          }
        }
      }
    }

    // Check all localStorage keys for Supabase format
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith("sb-")) {
        try {
          const value = localStorage.getItem(key);
          const parsed = JSON.parse(value);
          if (parsed.access_token) {
            return parsed.access_token;
          }
        } catch {
          // Ignore parsing errors
        }
      }
    }

    return null;
  };

  // Method 2: Listen for custom auth events
  const token = checkStorageAuth();
  if (token) {
    console.log("🎉 Auth Bridge: JWT token detected");
    sendTokenToExtension(token);
  }
}

// Send JWT token to extension
function sendTokenToExtension(token) {
  try {
    // Send to extension background script
    chrome.runtime.sendMessage(
      {
        action: "AUTH_TOKEN_DETECTED",
        token: token,
        source: "pulseplan_web",
        timestamp: new Date().toISOString(),
      },
      (response) => {
        if (chrome.runtime.lastError) {
          console.log(
            "Auth Bridge: Extension not responding (normal if extension disabled)"
          );
        } else if (response?.success) {
          console.log("✅ Auth Bridge: Successfully sent token to extension");

          // Show success notification
          showAuthSuccessNotification();
        }
      }
    );
  } catch (error) {
    console.log(
      "Auth Bridge: Could not communicate with extension:",
      error.message
    );
  }
}

// Show success notification on the webpage
function showAuthSuccessNotification() {
  // Only show if we haven't shown it recently
  const lastShown = sessionStorage.getItem("pulseplan_auth_notification");
  const now = Date.now();

  if (!lastShown || now - parseInt(lastShown) > 30000) {
    // 30 seconds cooldown
    sessionStorage.setItem("pulseplan_auth_notification", now.toString());

    // Create and show notification
    const notification = document.createElement("div");
    notification.innerHTML = `
      <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: 500;
        max-width: 300px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        animation: slideInRight 0.3s ease-out;
      ">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 16px;">🚀</span>
          <span>Extension Connected!</span>
        </div>
        <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">
          Canvas extension is now authenticated and ready to sync assignments.
        </div>
      </div>
      <style>
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      </style>
    `;

    document.body.appendChild(notification);

    // Remove notification after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.style.animation = "slideInRight 0.3s ease-out reverse";
        setTimeout(() => notification.remove(), 300);
      }
    }, 5000);
  }
}

// Listen for storage changes (real-time auth detection)
function setupStorageListener() {
  let lastAuthCheck = "";

  const checkAuth = () => {
    const authData = JSON.stringify({
      localStorage: Object.keys(localStorage)
        .filter(
          (k) =>
            k.includes("auth") || k.includes("token") || k.startsWith("sb-")
        )
        .map((k) => k + ":" + (localStorage.getItem(k) || "").substring(0, 50)),
      sessionStorage: Object.keys(sessionStorage)
        .filter((k) => k.includes("auth") || k.includes("token"))
        .map(
          (k) => k + ":" + (sessionStorage.getItem(k) || "").substring(0, 50)
        ),
    });

    if (authData !== lastAuthCheck) {
      lastAuthCheck = authData;
      detectAuthentication();
    }
  };

  // Listen to storage events
  window.addEventListener("storage", checkAuth);

  // Also poll every 2 seconds for sessionStorage changes (which don't trigger storage events)
  setInterval(checkAuth, 2000);
}

// Listen for page navigation and auth state changes
function setupPageListener() {
  // Check auth immediately
  setTimeout(detectAuthentication, 1000);

  // Listen for URL changes (SPA navigation)
  let currentUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== currentUrl) {
      currentUrl = location.href;
      setTimeout(detectAuthentication, 1000); // Check auth after navigation
    }
  }).observe(document, { subtree: true, childList: true });

  // Listen for focus events (user might have logged in in another tab)
  window.addEventListener("focus", () => {
    setTimeout(detectAuthentication, 500);
  });
}

// Custom event listener for explicit auth events
function setupCustomEventListener() {
  // Allow the website to explicitly notify the extension
  window.addEventListener("pulseplan:auth", (event) => {
    const { token } = event.detail || {};
    if (token) {
      console.log("🎯 Auth Bridge: Received explicit auth event");
      sendTokenToExtension(token);
    }
  });

  // Expose function for website to call directly
  window.pulsePlanExtensionAuth = (token) => {
    if (token) {
      sendTokenToExtension(token);
    }
  };
}

// Initialize all listeners
function initialize() {
  console.log("🚀 Auth Bridge: Initializing on", location.hostname);

  setupStorageListener();
  setupPageListener();
  setupCustomEventListener();

  // Initial auth check
  detectAuthentication();
}

// Start when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initialize);
} else {
  initialize();
}
