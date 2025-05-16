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

  return dashboardItems.length > 0 || assignmentItems.length > 0;
}

// Parse assignments from dashboard cards and todo items
function scrapeAssignmentsFromDashboard() {
  const assignments = [];

  // Process dashboard todo items (most direct assignment references)
  document.querySelectorAll(".todo-list-item").forEach((item) => {
    const titleElement = item.querySelector(".todo-details__Title");
    const courseElement = item.querySelector(".todo-details__CourseTitle");
    const dateElement = item.querySelector(".todo-details__Info");

    if (titleElement) {
      const assignment = {
        id: "canvas_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
        title: titleElement.textContent.trim(),
        course: courseElement
          ? courseElement.textContent.trim()
          : "Unknown Course",
        dueDate: dateElement ? extractDate(dateElement.textContent) : null,
        url: titleElement.closest("a") ? titleElement.closest("a").href : null,
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

    if (titleElement) {
      const assignment = {
        id: "canvas_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
        title: titleElement.textContent.trim(),
        course: courseTitle ? courseTitle.textContent.trim() : "Unknown Course",
        dueDate: dateElement ? extractDate(dateElement.textContent) : null,
        url: titleElement.closest("a")
          ? titleElement.closest("a").href
          : window.location.href,
        scraped: new Date().toISOString(),
      };

      assignments.push(assignment);
    }
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

// Main function to collect assignments
function collectAssignments() {
  if (!isAssignmentPage()) return [];

  // Get assignments from both potential sources
  const dashboardAssignments = scrapeAssignmentsFromDashboard();
  const courseAssignments = scrapeAssignmentsFromCoursePage();

  // Combine results
  const allAssignments = [...dashboardAssignments, ...courseAssignments];

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
      `Rhythm extension: Stored ${assignments.length} new assignments`
    );
  });
}

// Run the collection process
function runCollection() {
  const assignments = collectAssignments();
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
