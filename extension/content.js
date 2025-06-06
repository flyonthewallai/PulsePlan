/**
 * content.js - Scrapes assignment data from Canvas LMS pages
 * This script runs on Canvas pages, detects assignments, and stores them for syncing
 */

// Cached assignments to avoid duplicates
let cachedAssignments = [];

// Check if we're on a Canvas page with assignments
function isAssignmentPage() {
  // Dashboard pages
  const dashboardItems = document.querySelectorAll(
    ".ic-DashboardCard, .todo-list-item"
  );
  // Course assignment pages
  const assignmentItems = document.querySelectorAll(".ig-row");
  // Assignment index pages
  const assignmentListItems = document.querySelectorAll(
    ".assignment-list .assignment, .assignment_list .assignment, " +
      "[data-view='assignments'] .assignment, .assignments .assignment, " +
      ".assignment-group-list .assignment, .assignment-group .assignment"
  );
  // Generic assignment selectors
  const genericAssignments = document.querySelectorAll(
    "[id*='assignment'], [class*='assignment'], [data-id*='assignment']"
  );

  return (
    dashboardItems.length > 0 ||
    assignmentItems.length > 0 ||
    assignmentListItems.length > 0 ||
    genericAssignments.length > 0
  );
}

// Parse assignments from dashboard cards and todo items
function scrapeAssignmentsFromDashboard() {
  const assignments = [];

  // Process dashboard todo items (most direct assignment references)
  document.querySelectorAll(".todo-list-item").forEach((item) => {
    const titleElement = item.querySelector(".todo-details__Title");
    const courseElement = item.querySelector(".todo-details__CourseTitle");
    const dateElement = item.querySelector(".todo-details__Info");
    const gradeElement = item.querySelector(".todo-details__Grade, .points");

    if (titleElement) {
      const assignment = {
        id: "canvas_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
        title: titleElement.textContent.trim(),
        course: courseElement
          ? courseElement.textContent.trim()
          : "Unknown Course",
        dueDate: dateElement ? extractDate(dateElement.textContent) : null,
        url: titleElement.closest("a") ? titleElement.closest("a").href : null,
        grade: gradeElement ? extractGrade(gradeElement.textContent) : null,
        status: determineAssignmentStatus(item),
        scraped: new Date().toISOString(),
      };

      assignments.push(assignment);
    }
  });

  // Process dashboard cards with assignments
  document.querySelectorAll(".ic-DashboardCard").forEach((card) => {
    const courseName = card.querySelector(".ic-DashboardCard__header-title");

    card
      .querySelectorAll(".ic-DashboardCard__action-container a")
      .forEach((link) => {
        if (
          link.textContent.includes("Assignment") ||
          link.getAttribute("aria-label")?.includes("Assignment")
        ) {
          // For cards, we might only have partial info, so we get what we can
          const assignment = {
            id: "canvas_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
            title: link.getAttribute("aria-label") || link.textContent.trim(),
            course: courseName
              ? courseName.textContent.trim()
              : "Unknown Course",
            url: link.href,
            scraped: new Date().toISOString(),
          };

          assignments.push(assignment);
        }
      });
  });

  return assignments;
}

// Parse assignments from a course assignments page
function scrapeAssignmentsFromCoursePage() {
  const assignments = [];
  const courseTitle = document.querySelector(".context-course-info h1");

  document.querySelectorAll(".ig-row").forEach((row) => {
    const titleElement = row.querySelector(".ig-title");
    const dateElement = row.querySelector(".date-due");
    const gradeElement = row.querySelector(".grade, .points, .score");
    const statusElement = row.querySelector(".submission-status, .status");

    if (titleElement) {
      const assignment = {
        id: "canvas_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
        title: titleElement.textContent.trim(),
        course: courseTitle ? courseTitle.textContent.trim() : "Unknown Course",
        dueDate: dateElement ? extractDate(dateElement.textContent) : null,
        url: titleElement.closest("a")
          ? titleElement.closest("a").href
          : window.location.href,
        grade: gradeElement ? extractGrade(gradeElement.textContent) : null,
        status: statusElement
          ? extractStatus(statusElement.textContent)
          : "pending",
        scraped: new Date().toISOString(),
      };

      assignments.push(assignment);
    }
  });

  return assignments;
}

// Parse assignments from assignment index/list pages
function scrapeAssignmentsFromIndexPage() {
  const assignments = [];
  const courseTitle =
    document.querySelector(
      "h1, .course-title, [class*='course'], .context-course-info h1"
    ) || document.querySelector("title");
  const courseName = courseTitle
    ? courseTitle.textContent.trim()
    : "Unknown Course";

  // Try multiple selectors for assignment items
  const selectors = [
    ".assignment", // Generic assignment class
    "[id*='assignment']", // Elements with assignment in ID
    ".assignment-list li", // Assignment list items
    ".assignment-group .assignment", // Assignment group items
    ".content-box", // Canvas content boxes
    ".assignment_list_item", // Alternative assignment list
    ".context_module_item", // Module items
    "tr", // Table rows that might contain assignments
  ];

  let foundAssignments = false;

  selectors.forEach((selector) => {
    if (foundAssignments) return; // Skip if we already found assignments

    const elements = document.querySelectorAll(selector);
    if (elements.length === 0) return;

    elements.forEach((element) => {
      // Look for title in various ways
      const titleElement =
        element.querySelector(
          "a[title], .title, .assignment-title, .ig-title, h3, h4"
        ) ||
        element.querySelector("a") ||
        element;

      if (!titleElement) return;

      const titleText =
        titleElement.getAttribute("title") || titleElement.textContent.trim();

      // Skip if it doesn't look like an assignment
      if (!titleText || titleText.length < 3) return;
      if (
        titleText.toLowerCase().includes("calendar") ||
        titleText.toLowerCase().includes("people") ||
        titleText.toLowerCase().includes("files")
      )
        return;

      // Look for due date information
      const dateElement = element.querySelector(
        ".date-due, .due-date, .due_date, .date_due, " +
          "[class*='due'], [class*='date'], .datetime"
      );

      // Look for grade information
      const gradeElement = element.querySelector(
        ".grade, .points, .score, .percentage, " +
          "[class*='grade'], [class*='points'], [class*='score']"
      );

      // Get the assignment URL
      const linkElement =
        titleElement.tagName === "A"
          ? titleElement
          : element.querySelector("a");
      const assignmentUrl = linkElement
        ? linkElement.href
        : window.location.href;

      const assignment = {
        id: "canvas_" + Date.now() + "_" + Math.floor(Math.random() * 10000),
        title: titleText,
        course: courseName,
        dueDate: dateElement ? extractDate(dateElement.textContent) : null,
        url: assignmentUrl,
        grade: gradeElement ? extractGrade(gradeElement.textContent) : null,
        status: determineAssignmentStatus(element),
        scraped: new Date().toISOString(),
      };

      assignments.push(assignment);
      foundAssignments = true;
    });
  });

  return assignments;
}

// Helper function to extract and standardize dates from text
function extractDate(text) {
  if (!text) return null;

  text = text.trim();

  // Try to extract date information from various formats
  if (text.toLowerCase().includes("due:")) {
    text = text.split("Due:")[1].trim();
  }

  // Handle "Due Jun 15 at 11:59pm" format
  const dateMatch = text.match(/(\w+)\s+(\d+)(?:\s+at\s+(\d+):(\d+)([ap]m))?/i);
  if (dateMatch) {
    const monthNames = [
      "jan",
      "feb",
      "mar",
      "apr",
      "may",
      "jun",
      "jul",
      "aug",
      "sep",
      "oct",
      "nov",
      "dec",
    ];
    const month = monthNames.findIndex(
      (m) => m === dateMatch[1].toLowerCase().substring(0, 3)
    );

    if (month !== -1) {
      const now = new Date();
      const year = now.getFullYear();
      let day = parseInt(dateMatch[2]);

      // Simple time parsing if available
      let hours = 23;
      let minutes = 59;
      if (dateMatch[3] && dateMatch[4]) {
        hours = parseInt(dateMatch[3]);
        minutes = parseInt(dateMatch[4]);
        if (dateMatch[5]?.toLowerCase() === "pm" && hours < 12) {
          hours += 12;
        }
      }

      // Create the date string in ISO format
      return `${year}-${(month + 1).toString().padStart(2, "0")}-${day
        .toString()
        .padStart(2, "0")}T${hours.toString().padStart(2, "0")}:${minutes
        .toString()
        .padStart(2, "0")}:00`;
    }
  }

  return null;
}

// Helper function to extract grades from text
function extractGrade(text) {
  if (!text) return null;

  text = text.trim();

  // Look for patterns like "85/100", "A-", "95%", "8.5/10"
  const gradePatterns = [
    /(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/, // "85/100" or "8.5/10"
    /(\d+(?:\.\d+)?)%/, // "95%"
    /([A-F][+-]?)/, // "A-", "B+", etc.
    /(\d+(?:\.\d+)?)\s*pts?/i, // "85 pts"
  ];

  for (const pattern of gradePatterns) {
    const match = text.match(pattern);
    if (match) {
      if (pattern === gradePatterns[0]) {
        // Points format: calculate percentage
        const earned = parseFloat(match[1]);
        const total = parseFloat(match[2]);
        return {
          points: earned,
          maxPoints: total,
          percentage: total > 0 ? Math.round((earned / total) * 100) : null,
          display: text,
        };
      } else if (pattern === gradePatterns[1]) {
        // Percentage format
        return {
          percentage: parseFloat(match[1]),
          display: text,
        };
      } else if (pattern === gradePatterns[2]) {
        // Letter grade
        return {
          letterGrade: match[1],
          display: text,
        };
      } else if (pattern === gradePatterns[3]) {
        // Points only
        return {
          points: parseFloat(match[1]),
          display: text,
        };
      }
    }
  }

  return { display: text };
}

// Helper function to determine assignment status
function determineAssignmentStatus(element) {
  const text = element.textContent.toLowerCase();

  if (text.includes("submitted") || text.includes("complete")) {
    return "completed";
  } else if (text.includes("graded") || text.includes("scored")) {
    return "graded";
  } else if (text.includes("overdue") || text.includes("late")) {
    return "overdue";
  } else if (text.includes("missing")) {
    return "missing";
  }

  return "pending";
}

// Helper function to extract status from text
function extractStatus(text) {
  if (!text) return "pending";

  text = text.toLowerCase().trim();

  if (text.includes("submitted") || text.includes("complete")) {
    return "completed";
  } else if (text.includes("graded") || text.includes("scored")) {
    return "graded";
  } else if (text.includes("overdue") || text.includes("late")) {
    return "overdue";
  } else if (text.includes("missing")) {
    return "missing";
  }

  return "pending";
}

// Main function to collect assignments
function collectAssignments() {
  if (!isAssignmentPage()) return [];

  // Get assignments from all potential sources
  const dashboardAssignments = scrapeAssignmentsFromDashboard();
  const courseAssignments = scrapeAssignmentsFromCoursePage();
  const indexAssignments = scrapeAssignmentsFromIndexPage();

  // Combine results
  const allAssignments = [
    ...dashboardAssignments,
    ...courseAssignments,
    ...indexAssignments,
  ];

  // Filter out duplicates (based on title and course)
  const uniqueAssignments = allAssignments.filter((assignment) => {
    const isDuplicate = cachedAssignments.some(
      (cached) =>
        cached.title === assignment.title && cached.course === assignment.course
    );
    return !isDuplicate;
  });

  // Update our cache
  cachedAssignments = [...cachedAssignments, ...uniqueAssignments];

  // Keep cache size reasonable
  if (cachedAssignments.length > 100) {
    cachedAssignments = cachedAssignments.slice(-100);
  }

  return uniqueAssignments;
}

// Store assignments in chrome.storage
function storeAssignments(assignments) {
  if (assignments.length === 0) return;

  chrome.storage.local.get(["canvas_assignments"], function (result) {
    const storedAssignments = result.canvas_assignments || [];

    // Add new assignments, avoiding duplicates
    const updatedAssignments = [...storedAssignments];

    assignments.forEach((newAssignment) => {
      const isDuplicate = storedAssignments.some(
        (stored) =>
          stored.title === newAssignment.title &&
          stored.course === newAssignment.course
      );

      if (!isDuplicate) {
        updatedAssignments.push(newAssignment);
      }
    });

    // Store the updated list
    chrome.storage.local.set({
      canvas_assignments: updatedAssignments,
      last_scan: new Date().toISOString(),
    });

    // Also store unsyncedCount for the badge
    const unsyncedCount = updatedAssignments.filter((a) => !a.synced).length;
    chrome.storage.local.set({ unsynced_count: unsyncedCount });

    console.log(
      `PulsePlan extension: Stored ${assignments.length} new assignments`
    );
  });
}

// Run the collection process
function runCollection() {
  console.log("🔍 PulsePlan: Starting assignment collection...");
  console.log("📍 Current URL:", window.location.href);

  const assignments = collectAssignments();
  console.log(`📚 PulsePlan: Found ${assignments.length} assignments`);

  if (assignments.length > 0) {
    console.log("📋 Assignments found:", assignments);
  } else {
    console.log("🔍 Debug: Checking page elements...");
    console.log(
      "- Dashboard items:",
      document.querySelectorAll(".ic-DashboardCard, .todo-list-item").length
    );
    console.log("- IG rows:", document.querySelectorAll(".ig-row").length);
    console.log(
      "- Generic assignments:",
      document.querySelectorAll("[id*='assignment'], [class*='assignment']")
        .length
    );
    console.log("- Table rows:", document.querySelectorAll("tr").length);
    console.log("- Links:", document.querySelectorAll("a").length);
  }

  storeAssignments(assignments);
}

// Run on page load
runCollection();

// Also run when the page content changes significantly
const observer = new MutationObserver(function (mutations) {
  let shouldRun = false;

  mutations.forEach(function (mutation) {
    // Only run if relevant DOM elements were added
    if (
      mutation.addedNodes.length &&
      (mutation.addedNodes[0].classList?.contains("ic-DashboardCard") ||
        mutation.addedNodes[0].classList?.contains("todo-list-item") ||
        mutation.addedNodes[0].classList?.contains("ig-row"))
    ) {
      shouldRun = true;
    }
  });

  if (shouldRun) {
    runCollection();
  }
});

observer.observe(document.body, { childList: true, subtree: true });
