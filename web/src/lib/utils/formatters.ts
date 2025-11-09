/**
 * Shared formatting utilities for PulsePlan
 * 
 * This module contains reusable formatting functions to prevent code duplication.
 */

/**
 * Formats a course code by extracting text and first 3-4 digit numbers.
 * 
 * @example
 * formatCourseCode('CSCI1200') => 'CSCI 1200'
 * formatCourseCode('MATH120') => 'MATH 120'
 * formatCourseCode('CS 4641') => 'CS 4641'
 * 
 * @param courseCode - The course code to format
 * @returns Formatted course code with space between letters and numbers
 */
export function formatCourseCode(courseCode: string): string {
  // Try to match 4-digit course number first (e.g., "CSCI1200")
  const match4 = courseCode.match(/^([A-Za-z]+)\s*(\d{4})/)
  if (match4) {
    return `${match4[1]} ${match4[2]}`
  }
  
  // Try to match 3-digit course number (e.g., "MATH120")
  const match3 = courseCode.match(/^([A-Za-z]+)\s*(\d{3})/)
  if (match3) {
    return `${match3[1]} ${match3[2]}`
  }
  
  // Return as-is if no pattern matches
  return courseCode
}

/**
 * Formats a date string to a human-readable format.
 * 
 * @param dateString - ISO date string or Date object
 * @returns Formatted date string (e.g., "Jan 15, 2025")
 */
export function formatDate(dateString: string | Date): string {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Formats a time string to 12-hour format.
 * 
 * @param dateString - ISO date string or Date object
 * @returns Formatted time string (e.g., "3:00 PM")
 */
export function formatTime(dateString: string | Date): string {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}


