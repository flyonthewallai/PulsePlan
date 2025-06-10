/**
 * content.js - AI-powered Canvas LMS assignment scraper using Gemini
 * This script uses AI to intelligently extract assignment data from Canvas pages
 */

// Immediate loading confirmation
console.log("🎯 PulsePlan Content Script Loaded!");
console.log(
  "PulsePlan: Check out the repo! https://github.com/flyonthewalldev/pulseplan"
);
console.log("📍 Loading on:", window.location.href);
console.log("🕒 Load time:", new Date().toISOString());

// Configuration
const API_BASE_URL = "http://localhost:5000";
const SCRAPING_COOLDOWN = 5000; // 5 seconds between AI requests
const MAX_HTML_SIZE = 50000; // Limit HTML size for AI processing

// State management
let isProcessing = false;
let lastScrapeTime = 0;
let cachedResults = new Map();

/**
 * Main entry point - intelligently extract assignments using Gemini AI
 */
async function extractAssignmentsWithAI() {
  if (isProcessing) {
    console.log("🔄 PulsePlan: AI extraction already in progress...");
    return [];
  }

  const now = Date.now();
  if (now - lastScrapeTime < SCRAPING_COOLDOWN) {
    console.log("⏳ PulsePlan: Waiting for cooldown period...");
    return [];
  }

  isProcessing = true;
  lastScrapeTime = now;

  try {
    console.log("🤖 PulsePlan: Starting AI-powered assignment extraction...");

    // Get page context and HTML
    const pageData = await capturePageData();

    // Check cache first
    const cacheKey = generateCacheKey(pageData);
    if (cachedResults.has(cacheKey)) {
      console.log("💾 PulsePlan: Using cached results");
      return cachedResults.get(cacheKey);
    }

    // Send to AI extraction service
    const extractedData = await sendToGeminiService(pageData);

    if (extractedData && extractedData.events) {
      const assignments = processAIResults(extractedData);

      // Cache results
      cachedResults.set(cacheKey, assignments);

      console.log(
        `🎯 PulsePlan: AI extracted ${assignments.length} assignments`
      );
      return assignments;
    }

    return [];
  } catch (error) {
    console.error("❌ PulsePlan: AI extraction failed:", error);
    return [];
  } finally {
    isProcessing = false;
  }
}

/**
 * Capture relevant page data for AI processing
 */
async function capturePageData() {
  const pageData = {
    url: window.location.href,
    title: document.title,
    html: "",
    screenshot: null,
    context: determinePageContext(),
  };

  // Get cleaned HTML content
  const contentAreas = getRelevantContentAreas();
  let combinedHTML = contentAreas.map((area) => area.outerHTML).join("\n");

  // Limit HTML size for API efficiency
  if (combinedHTML.length > MAX_HTML_SIZE) {
    combinedHTML =
      combinedHTML.substring(0, MAX_HTML_SIZE) +
      "\n<!-- Content truncated for AI processing -->";
  }

  pageData.html = combinedHTML;

  // Optionally capture screenshot for vision analysis
  if (shouldUseVision()) {
    pageData.screenshot = await captureScreenshot();
  }

  return pageData;
}

/**
 * Determine the type of Canvas page we're on
 */
function determinePageContext() {
  const url = window.location.href.toLowerCase();
  const pathname = window.location.pathname.toLowerCase();

  if (url.includes("/courses/") && url.includes("/assignments")) {
    return "course_assignments";
  } else if (pathname.includes("/dashboard") || pathname === "/") {
    return "dashboard";
  } else if (url.includes("/calendar")) {
    return "calendar";
  } else if (url.includes("/courses/") && url.includes("/modules")) {
    return "course_modules";
  } else if (url.includes("/courses/")) {
    return "course_home";
  } else if (url.includes("/grades")) {
    return "grades";
  }

  return "unknown";
}

/**
 * Get relevant content areas that likely contain assignment data
 */
function getRelevantContentAreas() {
  const context = determinePageContext();

  // Context-specific selectors for better extraction
  const contextSelectors = {
    dashboard: [
      ".ic-DashboardCard",
      ".ic-DashboardCard__header",
      ".ic-DashboardCard__header-title",
      ".ic-DashboardCard__box",
      ".todo-list",
      ".todo-list-item",
      ".coming-up",
      ".coming-up-item",
      ".recent-feedback",
      ".recent-feedback-item",
      ".planner",
      ".planner-item",
      ".right-side-wrapper",
    ],
    course_assignments: [
      "#assignment-list",
      ".assignment-list",
      ".assignment_list",
      ".ig-list",
      ".ig-row",
      ".ig-header",
      ".ig-details",
      ".assignment-title",
      ".due-date",
      ".points",
      ".assignment-row",
      ".assignment-item",
      ".content-box",
    ],
    course_modules: [
      ".context_modules",
      ".context_module",
      ".context_module_item",
      ".module-item",
      ".module-item-title",
      ".item-group-container",
      ".ig-row",
    ],
    calendar: [
      ".calendar",
      ".calendar-event",
      ".fc-event",
      ".fc-event-title",
      ".agenda-date",
      ".agenda-event",
      ".mini_calendar",
      "#calendar-app",
    ],
    course_home: [
      ".course-home-sub-navigation",
      ".ic-app-course-menu",
      ".recent-activity",
      ".module-sequence",
      ".home-content",
      ".syllabus",
      ".announcement",
    ],
  };

  // Get context-specific selectors, fallback to general ones
  const primarySelectors = contextSelectors[context] || [
    "#content",
    ".content",
    "main",
    '[role="main"]',
  ];

  // Always include these general assignment-related selectors
  const generalSelectors = [
    '[class*="assignment"]',
    '[id*="assignment"]',
    '[class*="due"]',
    '[class*="todo"]',
    "[data-event-type]",
    ".student-planner",
    ".planner-app",
  ];

  const allSelectors = [...primarySelectors, ...generalSelectors];
  const foundElements = [];

  for (const selector of allSelectors) {
    try {
      const elements = document.querySelectorAll(selector);
      elements.forEach((element) => {
        // Skip if element is empty or just whitespace
        if (!element.textContent.trim()) return;

        // Skip navigation and header elements
        if (element.closest("nav, header, footer, .navigation, .header"))
          return;

        // Avoid duplicates by checking if element is already included
        if (
          !foundElements.some(
            (existing) =>
              existing.contains(element) || element.contains(existing)
          )
        ) {
          foundElements.push(element);
        }
      });
    } catch (error) {
      console.warn(`Selector failed: ${selector}`, error);
    }
  }

  // Enhanced fallback with text content analysis
  if (foundElements.length === 0) {
    console.log("🔍 No specific content found, using intelligent fallback");

    // Look for text that indicates assignments
    const assignmentKeywords = [
      "assignment",
      "due",
      "quiz",
      "exam",
      "project",
      "homework",
      "discussion",
      "points",
      "pts",
    ];
    const textElements = document.querySelectorAll("*");

    for (const element of textElements) {
      const text = element.textContent.toLowerCase();
      const hasAssignmentKeywords = assignmentKeywords.some((keyword) =>
        text.includes(keyword)
      );

      if (hasAssignmentKeywords && text.length > 10 && text.length < 500) {
        // Check if this element or its parent seems relevant
        const relevantParent = element.closest(
          '[class*="content"], [class*="main"], [class*="body"]'
        );
        if (relevantParent && !foundElements.includes(relevantParent)) {
          foundElements.push(relevantParent);
        }
      }
    }

    // Ultimate fallback
    if (foundElements.length === 0) {
      const fallbackSelectors = ["#content", "main", ".main-content", "body"];
      for (const selector of fallbackSelectors) {
        const element = document.querySelector(selector);
        if (element) {
          foundElements.push(element);
          break;
        }
      }
    }
  }

  console.log(
    `📄 Found ${foundElements.length} content areas for ${context} context`
  );
  return foundElements;
}

/**
 * Determine if we should use vision analysis
 */
function shouldUseVision() {
  // Use vision for complex layouts or when pattern recognition might be needed
  const context = determinePageContext();
  return ["dashboard", "calendar", "unknown"].includes(context);
}

/**
 * Capture screenshot for vision analysis
 */
async function captureScreenshot() {
  try {
    // Since content scripts can't directly capture screenshots,
    // we'll use a placeholder for now. In a full implementation,
    // this would communicate with the background script
    return null;
  } catch (error) {
    console.warn("Screenshot capture failed:", error);
    return null;
  }
}

/**
 * Generate cache key for results
 */
function generateCacheKey(pageData) {
  const keyData = {
    url: pageData.url,
    htmlHash: simpleHash(pageData.html),
    context: pageData.context,
  };
  return JSON.stringify(keyData);
}

/**
 * Simple hash function for cache key generation
 */
function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash.toString();
}

/**
 * Send data to Gemini service for AI extraction
 */
async function sendToGeminiService(pageData) {
  try {
    const request = {
      html: pageData.html,
      screenshot: pageData.screenshot,
      extractionType: "canvas_assignments",
      context: `Canvas LMS page - ${pageData.context}. URL: ${pageData.url}. Page title: ${pageData.title}`,
    };

    const response = await fetch(`${API_BASE_URL}/scraping/extract-html`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`AI service error: ${response.status}`);
    }

    const result = await response.json();
    return result.data;
  } catch (error) {
    console.error("Failed to call Gemini service:", error);

    // Fallback to basic extraction if AI service fails
    return await basicFallbackExtraction(pageData);
  }
}

/**
 * Process AI extraction results into assignment format
 */
function processAIResults(extractedData) {
  const assignments = [];

  if (!extractedData.events || !Array.isArray(extractedData.events)) {
    return assignments;
  }

  for (const event of extractedData.events) {
    // Validate and clean AI-extracted data
    if (!event.title || event.title.trim().length === 0) {
      continue;
    }

    const assignment = {
      id: generateAssignmentId(event),
      title: cleanTitle(event.title),
      course: event.course || extractCourseFromContext(),
      description: event.description || "",
      dueDate: parseAIDate(event.dueDate),
      url: validateURL(event.url) || window.location.href,
      priority: mapPriority(event.priority),
      estimatedMinutes: parseEstimatedTime(event.estimatedTime),
      type: event.type || "assignment",
      status: mapStatus(event.status),
      confidence: event.confidence || 0.8,
      extractionMethod: extractedData.metadata?.extractionMethod || "ai",
      scraped: new Date().toISOString(),
    };

    assignments.push(assignment);
  }

  return assignments;
}

/**
 * Generate unique assignment ID
 */
function generateAssignmentId(event) {
  const uniqueString = `${event.title}_${event.course}_${
    event.dueDate
  }_${Date.now()}`;
  return `canvas_ai_${simpleHash(uniqueString)}`;
}

/**
 * Clean and normalize assignment title
 */
function cleanTitle(title) {
  return title
    .trim()
    .replace(/\s+/g, " ")
    .replace(/^(Assignment|Task|Homework|HW|Quiz|Exam|Test):\s*/i, "")
    .substring(0, 200); // Limit length
}

/**
 * Extract course name from page context
 */
function extractCourseFromContext() {
  // Try various selectors to find course name
  const selectors = [
    ".ic-DashboardCard__header-title",
    ".context-course-info h1",
    ".course-title",
    "[data-course-name]",
    "h1",
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim()) {
      return element.textContent.trim();
    }
  }

  // Extract from URL if possible
  const urlMatch = window.location.pathname.match(/\/courses\/\d+/);
  if (urlMatch) {
    return `Course ${urlMatch[0].split("/").pop()}`;
  }

  return "Unknown Course";
}

/**
 * Parse AI-provided date string
 */
function parseAIDate(dateString) {
  if (!dateString) return null;

  try {
    const date = new Date(dateString);
    if (!isNaN(date.getTime())) {
      return date.toISOString();
    }
  } catch (error) {
    console.warn("Failed to parse AI date:", dateString);
  }

  return null;
}

/**
 * Validate URL from AI extraction
 */
function validateURL(url) {
  if (!url) return null;

  try {
    new URL(url);
    return url;
  } catch {
    // Try to construct relative URL
    if (url.startsWith("/")) {
      return window.location.origin + url;
    }
    return null;
  }
}

/**
 * Map AI priority to our system
 */
function mapPriority(aiPriority) {
  if (!aiPriority) return "medium";

  const priority = aiPriority.toLowerCase();
  if (["high", "urgent", "critical"].includes(priority)) return "high";
  if (["low", "optional"].includes(priority)) return "low";
  return "medium";
}

/**
 * Parse estimated time from AI
 */
function parseEstimatedTime(timeString) {
  if (!timeString) return null;

  const match = timeString.match(/(\d+)\s*(hour|hr|minute|min)/i);
  if (match) {
    const value = parseInt(match[1]);
    const unit = match[2].toLowerCase();

    if (unit.startsWith("hour") || unit === "hr") {
      return value * 60;
    } else {
      return value;
    }
  }

  return null;
}

/**
 * Map AI status to our system
 */
function mapStatus(aiStatus) {
  if (!aiStatus) return "pending";

  const status = aiStatus.toLowerCase();
  if (["completed", "done", "submitted"].includes(status)) return "completed";
  if (["in progress", "started", "working"].includes(status))
    return "in_progress";
  return "pending";
}

/**
 * Basic fallback extraction when AI service fails
 */
async function basicFallbackExtraction(pageData) {
  console.log("🔄 PulsePlan: Using fallback extraction...");

  // Simple pattern-based extraction as fallback
  const assignments = [];
  const elements = document.querySelectorAll(
    ".todo-list-item, .ig-row, .assignment"
  );

  elements.forEach((element) => {
    const titleElement = element.querySelector(
      '[class*="title"], [class*="Title"], a, h3, h4'
    );
    if (titleElement && titleElement.textContent.trim()) {
      assignments.push({
        id: `canvas_fallback_${Date.now()}_${Math.random()}`,
        title: titleElement.textContent.trim(),
        course: extractCourseFromContext(),
        url: titleElement.href || window.location.href,
        extractionMethod: "fallback",
        confidence: 0.6,
        scraped: new Date().toISOString(),
      });
    }
  });

  return { events: assignments };
}

/**
 * Store assignments in extension storage with enhanced feedback
 */
function storeAssignments(assignments) {
  if (assignments.length === 0) return;

  chrome.storage.local.get(
    ["canvas_assignments", "unsynced_count"],
    function (result) {
      const existingAssignments = result.canvas_assignments || [];
      const newAssignments = assignments.filter(
        (newAssignment) =>
          !existingAssignments.some(
            (existing) =>
              existing.title === newAssignment.title &&
              existing.course === newAssignment.course
          )
      );

      if (newAssignments.length > 0) {
        const updatedAssignments = [...existingAssignments, ...newAssignments];
        const newUnsyncedCount =
          (result.unsynced_count || 0) + newAssignments.length;

        // Calculate average AI confidence
        const aiConfidence =
          newAssignments.reduce(
            (sum, assignment) => sum + (assignment.confidence || 0.8),
            0
          ) / newAssignments.length;

        chrome.storage.local.set({
          canvas_assignments: updatedAssignments,
          unsynced_count: newUnsyncedCount,
          last_scan: new Date().toISOString(),
          ai_confidence: aiConfidence,
          extraction_status: "success",
        });

        console.log(
          `💾 PulsePlan: Stored ${newAssignments.length} new assignments`
        );

        // Notify popup of extraction completion
        notifyPopup("complete", newAssignments.length);
      }
    }
  );
}

/**
 * Notify popup of extraction status updates
 */
function notifyPopup(status, count = 0) {
  try {
    chrome.runtime.sendMessage({
      action: "extractionUpdate",
      status: status,
      count: count,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    // Popup might not be open, that's okay
    console.log("Could not notify popup:", error.message);
  }
}

// Rate limiting to prevent duplicate extractions
let lastExtractionTime = 0;
let isExtracting = false;

/**
 * Main execution function with enhanced status reporting and rate limiting
 */
async function runAIExtraction() {
  // Rate limiting: prevent extractions within 10 seconds of each other
  const now = Date.now();
  if (isExtracting) {
    console.log("⏳ PulsePlan: Extraction already in progress, skipping");
    return;
  }

  if (now - lastExtractionTime < 10000) {
    console.log("⏱️ PulsePlan: Rate limited, skipping extraction");
    return;
  }

  try {
    isExtracting = true;
    lastExtractionTime = now;

    console.log("🚀 PulsePlan: Starting AI-powered Canvas extraction...");
    console.log("📍 Current URL:", window.location.href);
    console.log("📄 Page context:", determinePageContext());

    // Update extraction status
    chrome.storage.local.set({ extraction_status: "extracting" });
    notifyPopup("extracting");

    const assignments = await extractAssignmentsWithAI();

    if (assignments.length > 0) {
      console.log(
        `✅ PulsePlan: Successfully extracted ${assignments.length} assignments`
      );
      console.log("📋 Assignments:", assignments);
      storeAssignments(assignments);
    } else {
      console.log("ℹ️ PulsePlan: No assignments found on this page");
      chrome.storage.local.set({
        extraction_status: "success",
        last_scan: new Date().toISOString(),
      });
      notifyPopup("complete", 0);
    }
  } catch (error) {
    console.error("❌ PulsePlan: Extraction failed:", error);
    chrome.storage.local.set({ extraction_status: "error" });
    notifyPopup("error");
  } finally {
    isExtracting = false;
  }
}

/**
 * Check if current page is relevant for assignment extraction
 */
function isRelevantPage() {
  const url = window.location.href.toLowerCase();
  const relevantPaths = [
    "/dashboard",
    "/courses/",
    "/assignments",
    "/calendar",
    "/grades",
  ];

  return relevantPaths.some((path) => url.includes(path));
}

/**
 * Smart page change detection
 */
function setupPageChangeDetection() {
  let currentUrl = window.location.href;

  // Monitor for URL changes (SPA navigation)
  setInterval(() => {
    if (window.location.href !== currentUrl) {
      currentUrl = window.location.href;
      if (isRelevantPage()) {
        setTimeout(runAIExtraction, 2000); // Delay to let page load
      }
    }
  }, 1000);

  // Monitor for significant DOM changes
  const observer = new MutationObserver((mutations) => {
    let shouldRun = false;

    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length > 0) {
        // Check if relevant content was added
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const element = node;
            if (
              element.classList &&
              (element.classList.contains("todo-list-item") ||
                element.classList.contains("ig-row") ||
                element.classList.contains("ic-DashboardCard") ||
                (element.querySelector &&
                  element.querySelector('[class*="assignment"]')))
            ) {
              shouldRun = true;
            }
          }
        });
      }
    });

    if (shouldRun && isRelevantPage()) {
      setTimeout(runAIExtraction, 1000);
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

/**
 * Enhanced initialization with multiple triggers
 */
function initializePulsePlan() {
  console.log("🚀 PulsePlan: Initializing Canvas extension...");
  console.log(
    "PulsePlan: Check out the repo! https://github.com/flyonthewalldev/pulseplan"
  );
  console.log("📍 Current URL:", window.location.href);
  console.log("📄 Document ready state:", document.readyState);

  if (isRelevantPage()) {
    console.log("✅ PulsePlan: Relevant Canvas page detected");

    // Run extraction with progressive delays to catch different loading states
    setTimeout(() => runAIExtraction(), 1000); // Quick load
    setTimeout(() => runAIExtraction(), 3000); // Normal load
    setTimeout(() => runAIExtraction(), 5000); // Slow load

    setupPageChangeDetection();
  } else {
    console.log(
      "ℹ️ PulsePlan: Not a relevant Canvas page, skipping extraction"
    );
  }
}

// Multiple initialization triggers for reliability
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializePulsePlan);
} else {
  initializePulsePlan();
}

// Additional trigger for Canvas SPA navigation
window.addEventListener("load", () => {
  if (isRelevantPage()) {
    setTimeout(runAIExtraction, 2000);
  }
});

// Canvas-specific navigation detection (they use pushState)
const originalPushState = history.pushState;
history.pushState = function () {
  originalPushState.apply(history, arguments);
  setTimeout(() => {
    if (isRelevantPage()) {
      console.log(
        "🔄 PulsePlan: Canvas navigation detected, running extraction"
      );
      runAIExtraction();
    }
  }, 1500);
};

// Also detect popstate (back/forward navigation)
window.addEventListener("popstate", () => {
  setTimeout(() => {
    if (isRelevantPage()) {
      console.log(
        "⬅️ PulsePlan: Browser navigation detected, running extraction"
      );
      runAIExtraction();
    }
  }, 1500);
});

// Clear cache periodically to prevent memory issues
setInterval(() => {
  if (cachedResults.size > 10) {
    cachedResults.clear();
    console.log("🧹 PulsePlan: Cleared extraction cache");
  }
}, 300000); // Every 5 minutes
