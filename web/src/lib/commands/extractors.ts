/**
 * Parameter Extraction Utilities
 * Rule-based parsers for extracting parameters from command text
 */

import * as chrono from 'chrono-node';
import type { ExtractedParameter } from '@/lib/commands/types';

/**
 * Extract date/time from text using chrono-node
 */
export function extractDateTime(text: string): ExtractedParameter | null {
  const results = chrono.parse(text);
  
  if (results.length === 0) return null;
  
  const result = results[0];
  const date = result.start.date();
  
  return {
    name: 'datetime',
    value: date.toISOString(),
    confidence: 0.9,
    rawText: result.text,
    startIndex: result.index,
    endIndex: result.index + result.text.length,
  };
}

/**
 * Extract priority from text
 */
export function extractPriority(text: string): ExtractedParameter | null {
  const priorityRegex = /\b(low|medium|high|urgent)\s*(priority)?\b/i;
  const match = text.match(priorityRegex);
  
  if (!match) return null;
  
  let priority = match[1].toLowerCase();
  if (priority === 'urgent') priority = 'high';
  
  return {
    name: 'priority',
    value: priority,
    confidence: 0.95,
    rawText: match[0],
    startIndex: match.index!,
    endIndex: match.index! + match[0].length,
  };
}

/**
 * Extract tags from text (e.g., #study, #work)
 */
export function extractTags(text: string): ExtractedParameter | null {
  const tagRegex = /#(\w+)/g;
  const matches = [...text.matchAll(tagRegex)];
  
  if (matches.length === 0) return null;
  
  const tags = matches.map(m => m[1]);
  const fullText = matches.map(m => m[0]).join(' ');
  
  return {
    name: 'tags',
    value: tags,
    confidence: 0.98,
    rawText: fullText,
    startIndex: matches[0].index!,
    endIndex: matches[matches.length - 1].index! + matches[matches.length - 1][0].length,
  };
}

/**
 * Extract duration from text (e.g., "30 minutes", "1.5 hours", "2h")
 */
export function extractDuration(text: string): ExtractedParameter | null {
  // Match patterns like: "30 min", "1 hour", "90 minutes", "1.5h", "2 hrs"
  const durationRegex = /\b(\d+(?:\.\d+)?)\s*(min|mins|minute|minutes|h|hr|hrs|hour|hours)\b/i;
  const match = text.match(durationRegex);
  
  if (!match) return null;
  
  const value = parseFloat(match[1]);
  const unit = match[2].toLowerCase();
  
  // Convert to minutes
  let minutes = value;
  if (unit.startsWith('h')) {
    minutes = value * 60;
  }
  
  return {
    name: 'duration',
    value: Math.round(minutes),
    confidence: 0.9,
    rawText: match[0],
    startIndex: match.index!,
    endIndex: match.index! + match[0].length,
  };
}

/**
 * Extract location from text (heuristic: words after "at" or "in")
 */
export function extractLocation(text: string): ExtractedParameter | null {
  const locationRegex = /\b(?:at|in)\s+([A-Z][a-zA-Z\s]+?)(?:\s+(?:on|at|for|with|$))/;
  const match = text.match(locationRegex);
  
  if (!match) return null;
  
  return {
    name: 'location',
    value: match[1].trim(),
    confidence: 0.7,
    rawText: match[0],
    startIndex: match.index!,
    endIndex: match.index! + match[0].length,
  };
}

/**
 * Extract title (remaining text after removing all other parameters)
 */
export function extractTitle(
  text: string,
  extractedParams: ExtractedParameter[]
): string {
  let title = text;
  
  // Remove all extracted parameter text
  const sortedParams = [...extractedParams].sort((a, b) => b.startIndex - a.startIndex);
  for (const param of sortedParams) {
    title = title.slice(0, param.startIndex) + title.slice(param.endIndex);
  }
  
  // Clean up extra whitespace
  title = title.replace(/\s+/g, ' ').trim();
  
  return title;
}

/**
 * Main extraction function - extracts all parameters from text
 */
export function extractParameters(
  text: string,
  commandId: string
): Record<string, any> {
  const extracted: ExtractedParameter[] = [];
  const parameters: Record<string, any> = {};
  
  // Extract based on command type
  const datetime = extractDateTime(text);
  if (datetime) {
    extracted.push(datetime);
    
    // Determine if this is start_time, due_date, or new_time based on command
    if (commandId === 'schedule') {
      parameters.start_time = datetime.value;
    } else if (commandId === 'todo') {
      parameters.due_date = datetime.value;
    } else if (commandId === 'reschedule') {
      parameters.new_time = datetime.value;
    }
  }
  
  const priority = extractPriority(text);
  if (priority) {
    extracted.push(priority);
    parameters.priority = priority.value;
  }
  
  const tags = extractTags(text);
  if (tags) {
    extracted.push(tags);
    parameters.tags = tags.value;
  }
  
  const duration = extractDuration(text);
  if (duration) {
    extracted.push(duration);
    parameters.duration = duration.value;
  }
  
  const location = extractLocation(text);
  if (location) {
    extracted.push(location);
    parameters.location = location.value;
  }
  
  // Extract title from remaining text
  const title = extractTitle(text, extracted);
  if (title) {
    if (commandId === 'reschedule') {
      parameters.task_identifier = title;
    } else if (commandId === 'focus') {
      parameters.task = title;
    } else {
      parameters.title = title;
    }
  }
  
  return parameters;
}

