// Core data structures for web scraping and AI processing

export interface ScrapingConfig {
  url: string;
  selectors?: CustomSelectors;
  authHeaders?: Record<string, string>;
  waitForElements?: string[];
  scrollToBottom?: boolean;
  maxRetries?: number;
  timeout?: number;
}

export interface CustomSelectors {
  events?: string[];
  assignments?: string[];
  dates?: string[];
  titles?: string[];
  descriptions?: string[];
  courses?: string[];
}

export interface ScrapedContent {
  html: string;
  screenshot?: string;
  url: string;
  timestamp: Date;
  metadata: {
    title: string;
    domain: string;
    contentLength: number;
  };
}

export interface ExtractedEvent {
  title: string;
  description?: string;
  dueDate?: string;
  course?: string;
  priority?: 'low' | 'medium' | 'high';
  estimatedDuration?: number; // in minutes
  type: 'assignment' | 'exam' | 'project' | 'reading' | 'lecture' | 'other';
  confidence: number; // 0-1 score
  sourceElement?: string; // CSS selector or description
}

export interface ExtractedData {
  events: ExtractedEvent[];
  metadata: WebsiteMetadata;
  overallConfidence: number;
  extractionMethod: 'pattern' | 'ai' | 'hybrid';
  processingTime: number; // milliseconds
}

export interface WebsiteMetadata {
  url: string;
  websiteType: 'lms' | 'calendar' | 'university' | 'generic' | 'unknown';
  platform?: 'canvas' | 'blackboard' | 'moodle' | 'brightspace' | 'other';
  extractionRules?: ExtractionRule[];
  lastUpdated: Date;
  supportLevel: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface ExtractionRule {
  id: string;
  name: string;
  selectors: string[];
  dataType: 'event' | 'date' | 'title' | 'description' | 'course';
  priority: number;
  confidence: number;
}

export interface PageStructure {
  hasEvents: boolean;
  hasCalendar: boolean;
  hasAssignments: boolean;
  hasTables: boolean;
  hasLists: boolean;
  detectedPlatform?: string;
  commonPatterns: string[];
  semanticElements: string[];
}

export interface PatternData {
  events: PatternEvent[];
  confidence: number;
  extractionMethod: string;
}

export interface PatternEvent {
  title: string;
  rawDate?: string;
  parsedDate?: Date;
  description?: string;
  selector: string;
  confidence: number;
}

export interface AIExtractedData {
  events: ExtractedEvent[];
  metadata: {
    extractionMethod: string;
    overallConfidence: number;
    processingNotes: string[];
  };
}

export interface ConsolidatedTask {
  id?: string;
  title: string;
  description?: string;
  dueDate?: Date;
  course?: string;
  priority: 'low' | 'medium' | 'high';
  estimatedDuration?: number;
  type: 'assignment' | 'exam' | 'project' | 'reading' | 'lecture' | 'other';
  source: 'scraped' | 'calendar' | 'manual';
  sourceUrl?: string;
  confidence: number;
  tags?: string[];
}

export interface CacheEntry {
  data: ExtractedData;
  timestamp: Date;
  ttl: number; // seconds
  url: string;
  hash: string;
}

export interface ScrapingResult {
  success: boolean;
  data?: ExtractedData;
  error?: string;
  cached: boolean;
  processingTime: number;
}

// Security and validation types
export interface SecurityValidation {
  isValidUrl: boolean;
  isDomainAllowed: boolean;
  hasSSL: boolean;
  riskLevel: 'low' | 'medium' | 'high';
  warnings: string[];
}

export interface RateLimitInfo {
  remainingRequests: number;
  resetTime: Date;
  totalRequests: number;
}

// Gemini AI specific types
export interface GeminiRequest {
  html: string;
  screenshot?: string;
  context: string;
  extractionType: 'schedule' | 'assignment' | 'event' | 'general';
}

export interface GeminiResponse {
  events: ExtractedEvent[];
  confidence: number;
  reasoning: string[];
  suggestions: string[];
}

// Website analyzer types
export interface WebsiteAnalysis {
  structure: PageStructure;
  supportLevel: 'excellent' | 'good' | 'fair' | 'poor';
  recommendedStrategy: 'pattern' | 'ai' | 'hybrid';
  estimatedAccuracy: number;
  requiredAuthentication: boolean;
  dynamicContent: boolean;
}

export interface ExtractionStrategy {
  primary: 'pattern' | 'ai' | 'hybrid';
  fallback?: 'pattern' | 'ai';
  confidence: number;
  reasoning: string;
} 