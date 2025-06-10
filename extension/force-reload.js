/**
 * Force Extension Reload Helper
 * This script helps clear Chrome extension cache and force a complete reload
 */

console.log("🔄 PulsePlan Extension Force Reload Helper");
console.log(
  "PulsePlan: Check out the repo! https://github.com/flyonthewalldev/pulseplan"
);

// Instructions for manual reload
console.log(`
🚀 To completely reload the PulsePlan extension:

1. **Go to chrome://extensions/**
2. **Find "PulsePlan Canvas Sync - AI Powered"**
3. **Click the "Remove" button** (this clears all cache)
4. **Click "Load unpacked"** 
5. **Select the extension folder** again

OR try the automated method below:
`);

async function forceReloadExtension() {
  try {
    // Get all extensions
    const extensions = await chrome.management.getAll();

    // Find PulsePlan extension
    const pulsePlanExtension = extensions.find(
      (ext) =>
        ext.name.toLowerCase().includes("pulseplan") ||
        ext.name.toLowerCase().includes("canvas")
    );

    if (pulsePlanExtension) {
      console.log(`✅ Found extension: ${pulsePlanExtension.name}`);
      console.log(`📋 Extension ID: ${pulsePlanExtension.id}`);

      // Disable the extension first
      console.log("🔄 Disabling extension...");
      await chrome.management.setEnabled(pulsePlanExtension.id, false);

      // Wait a moment
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Re-enable the extension
      console.log("✅ Re-enabling extension...");
      await chrome.management.setEnabled(pulsePlanExtension.id, true);

      console.log("🎉 Extension force-reloaded successfully!");
      console.log("💡 Now navigate to a Canvas page to test");
    } else {
      console.log("❌ PulsePlan extension not found");
      console.log("💡 Try the manual reload steps above");
    }
  } catch (error) {
    console.error("❌ Force reload failed:", error);
    console.log("💡 Please try the manual reload steps above");
  }
}

// Manual service worker restart (if possible)
function restartServiceWorker() {
  console.log("🔧 Attempting to restart service worker...");

  // This might help clear service worker cache
  if (typeof chrome !== "undefined" && chrome.runtime) {
    chrome.runtime.getBackgroundPage((backgroundPage) => {
      if (backgroundPage) {
        backgroundPage.location.reload();
        console.log("✅ Background page reloaded");
      } else {
        console.log("⚠️ No background page found (normal for Manifest V3)");
      }
    });
  }
}

// Auto-run helpers
console.log("💡 Available commands:");
console.log("  - forceReloadExtension() - Try automated reload");
console.log("  - restartServiceWorker() - Try service worker restart");
console.log("");
console.log("🚨 If still getting alarms error, use MANUAL RELOAD steps above");
