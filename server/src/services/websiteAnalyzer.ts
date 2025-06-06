// @ts-ignore - Package will be installed during setup
import * as cheerio from 'cheerio';
import { 
  PageStructure, 
  WebsiteAnalysis, 
  ExtractionStrategy, 
  WebsiteMetadata 
} from '../types/scraping';
import { GeminiService } from './geminiService';

export class WebsiteAnalyzer {
  private gemini: GeminiService;

  constructor() {
    this.gemini = new GeminiService();
  }

  /**
   * Analyze website structure and determine extraction strategy
   */
  async analyzeWebsite(
    html: string, 
    url: string, 
    screenshot?: string
  ): Promise<WebsiteAnalysis> {
    const startTime = Date.now();
    
    try {
      // Step 1: Basic structure analysis
      const structure = this.analyzePageStructure(html);
      
      // Step 2: Platform detection
      const platform = this.detectPlatform(html, url);
      
      // Step 3: AI-powered analysis (with fallback)
      let aiAnalysis;
      try {
        aiAnalysis = await this.gemini.analyzeWebsiteStructure(html, screenshot);
      } catch (error) {
        console.warn('AI analysis failed, using fallback:', error instanceof Error ? error.message : 'Unknown error');
        aiAnalysis = {
          platform: platform || 'unknown',
          confidence: 0.5,
          strategy: 'pattern',
          reasoning: ['AI analysis unavailable, using pattern-based detection']
        };
      }
      
      // Step 4: Determine support level and strategy
      const supportLevel = this.determineSupportLevel(structure, platform, aiAnalysis);
      const strategy = this.determineExtractionStrategy(structure, platform, aiAnalysis);
      
      return {
        structure,
        supportLevel,
        recommendedStrategy: strategy.primary,
        estimatedAccuracy: this.estimateAccuracy(structure, platform, strategy),
        requiredAuthentication: this.requiresAuthentication(html),
        dynamicContent: this.hasDynamicContent(html)
      };
    } catch (error) {
      console.error('Website analysis error:', error);
      return this.getDefaultAnalysis();
    }
  }

  /**
   * Analyze page structure for schedule-related elements
   */
  private analyzePageStructure(html: string): PageStructure {
    const $ = cheerio.load(html);
    
    // Common selectors for academic content
    const eventSelectors = [
      '.event', '.assignment', '.due-date', '.deadline',
      '[data-event]', '[data-assignment]', '.calendar-event',
      '.assignment-item', '.course-event', '.task-item'
    ];
    
    const calendarSelectors = [
      '.calendar', '.schedule', '.agenda', '.timeline',
      '[data-calendar]', '.month-view', '.week-view', '.day-view'
    ];
    
    const assignmentSelectors = [
      '.assignment', '.homework', '.project', '.exam',
      '.due', '.submitted', '.graded', '.pending'
    ];
    
    const tableSelectors = ['table', '.table', '.data-table', '.grid'];
    const listSelectors = ['ul', 'ol', '.list', '.items'];
    
    // Check for presence of these elements
    const hasEvents = eventSelectors.some(selector => $(selector).length > 0);
    const hasCalendar = calendarSelectors.some(selector => $(selector).length > 0);
    const hasAssignments = assignmentSelectors.some(selector => $(selector).length > 0);
    const hasTables = tableSelectors.some(selector => $(selector).length > 0);
    const hasLists = listSelectors.some(selector => $(selector).length > 0);
    
    // Detect common patterns
    const commonPatterns = this.detectCommonPatterns($);
    
    // Analyze semantic elements
    const semanticElements = this.analyzeSemanticElements($);
    
    // Detect platform from DOM structure
    const detectedPlatform = this.detectPlatformFromDOM($);
    
    return {
      hasEvents,
      hasCalendar,
      hasAssignments,
      hasTables,
      hasLists,
      detectedPlatform,
      commonPatterns,
      semanticElements
    };
  }

  /**
   * Detect platform from URL and content
   */
  private detectPlatform(html: string, url: string): string {
    const domain = new URL(url).hostname.toLowerCase();
    const content = html.toLowerCase();
    
    // URL-based detection
    if (domain.includes('instructure.com') || content.includes('canvas')) return 'canvas';
    if (domain.includes('blackboard.com') || content.includes('blackboard')) return 'blackboard';
    if (domain.includes('moodle') || content.includes('moodle')) return 'moodle';
    if (domain.includes('brightspace') || content.includes('brightspace')) return 'brightspace';
    if (domain.includes('schoology') || content.includes('schoology')) return 'schoology';
    if (domain.includes('google.com/calendar')) return 'google_calendar';
    if (domain.includes('outlook.live.com') || domain.includes('office.com')) return 'outlook';
    
    // Content-based detection
    if (content.includes('canvas lms') || content.includes('instructure')) return 'canvas';
    if (content.includes('blackboard learn')) return 'blackboard';
    if (content.includes('moodle site')) return 'moodle';
    
    // University-specific patterns
    if (domain.includes('.edu')) return 'university';
    
    return 'unknown';
  }

  /**
   * Detect platform from DOM structure
   */
  private detectPlatformFromDOM($: any): string | undefined {
    // Canvas-specific elements
    if ($('#application').length || $('.ic-app').length || $('[data-component="Canvas"]').length) {
      return 'canvas';
    }
    
    // Blackboard-specific elements
    if ($('#blackboard').length || $('.bb-learn').length || $('[data-bb-component]').length) {
      return 'blackboard';
    }
    
    // Moodle-specific elements
    if ($('#page-wrapper').length || $('.moodle-page').length || $('[data-region="main"]').length) {
      return 'moodle';
    }
    
    // Brightspace-specific elements
    if ($('.d2l-page').length || $('[data-location="brightspace"]').length) {
      return 'brightspace';
    }
    
    return undefined;
  }

  /**
   * Detect common academic content patterns
   */
  private detectCommonPatterns($: any): string[] {
    const patterns: string[] = [];
    
    // Date patterns
    if ($('time').length > 0) patterns.push('semantic_time');
    if ($('[datetime]').length > 0) patterns.push('datetime_attributes');
    if ($('*:contains("Due:")').length > 0) patterns.push('due_date_labels');
    
    // Assignment patterns
    if ($('*:contains("Assignment")').length > 0) patterns.push('assignment_content');
    if ($('*:contains("Homework")').length > 0) patterns.push('homework_content');
    if ($('*:contains("Project")').length > 0) patterns.push('project_content');
    
    // Status patterns
    if ($('*:contains("Submitted")').length > 0) patterns.push('submission_status');
    if ($('*:contains("Graded")').length > 0) patterns.push('grading_status');
    if ($('*:contains("Pending")').length > 0) patterns.push('pending_status');
    
    // Course patterns
    if ($('*:contains("Course")').length > 0) patterns.push('course_content');
    if ($('.course').length > 0) patterns.push('course_classes');
    
    return patterns;
  }

  /**
   * Analyze semantic HTML elements
   */
  private analyzeSemanticElements($: any): string[] {
    const elements: string[] = [];
    
    if ($('article').length > 0) elements.push('article');
    if ($('section').length > 0) elements.push('section');
    if ($('time').length > 0) elements.push('time');
    if ($('main').length > 0) elements.push('main');
    if ($('header').length > 0) elements.push('header');
    if ($('nav').length > 0) elements.push('nav');
    if ($('[role]').length > 0) elements.push('aria_roles');
    if ($('[aria-label]').length > 0) elements.push('aria_labels');
    
    return elements;
  }

  /**
   * Determine support level based on analysis
   */
  private determineSupportLevel(
    structure: PageStructure,
    platform: string,
    aiAnalysis: any
  ): 'excellent' | 'good' | 'fair' | 'poor' {
    let score = 0;
    
    // Platform-specific scoring
    if (['canvas', 'blackboard', 'moodle'].includes(platform)) score += 30;
    else if (platform === 'university') score += 20;
    else if (platform === 'unknown') score += 0;
    
    // Structure scoring
    if (structure.hasEvents) score += 20;
    if (structure.hasAssignments) score += 20;
    if (structure.hasCalendar) score += 15;
    if (structure.hasTables) score += 10;
    if (structure.semanticElements.length > 3) score += 10;
    
    // AI confidence scoring
    if (aiAnalysis.confidence > 0.8) score += 15;
    else if (aiAnalysis.confidence > 0.6) score += 10;
    else if (aiAnalysis.confidence > 0.4) score += 5;
    
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
  }

  /**
   * Determine best extraction strategy
   */
  private determineExtractionStrategy(
    structure: PageStructure,
    platform: string,
    aiAnalysis: any
  ): ExtractionStrategy {
    // Well-known platforms with good structure
    if (['canvas', 'blackboard', 'moodle'].includes(platform) && 
        structure.semanticElements.length > 2) {
      return {
        primary: 'hybrid',
        fallback: 'ai',
        confidence: 0.8,
        reasoning: 'Known platform with good semantic structure'
      };
    }
    
    // Good structure but unknown platform
    if (structure.hasEvents && structure.semanticElements.length > 3) {
      return {
        primary: 'hybrid',
        fallback: 'ai',
        confidence: 0.7,
        reasoning: 'Good semantic structure detected'
      };
    }
    
    // Poor structure or complex layout
    if (aiAnalysis.confidence > 0.6) {
      return {
        primary: 'ai',
        fallback: 'pattern',
        confidence: aiAnalysis.confidence,
        reasoning: 'AI analysis shows good extraction potential'
      };
    }
    
    // Fallback to pattern matching
    return {
      primary: 'pattern',
      fallback: 'ai',
      confidence: 0.5,
      reasoning: 'Limited structure, using pattern-based extraction'
    };
  }

  /**
   * Estimate extraction accuracy
   */
  private estimateAccuracy(
    structure: PageStructure,
    platform: string,
    strategy: ExtractionStrategy
  ): number {
    let accuracy = 0.5; // Base accuracy
    
    // Platform bonus
    if (['canvas', 'blackboard', 'moodle'].includes(platform)) accuracy += 0.3;
    else if (platform === 'university') accuracy += 0.2;
    
    // Structure bonus
    if (structure.hasEvents) accuracy += 0.15;
    if (structure.hasAssignments) accuracy += 0.15;
    if (structure.semanticElements.length > 3) accuracy += 0.1;
    
    // Strategy adjustment
    if (strategy.primary === 'hybrid') accuracy += 0.1;
    else if (strategy.primary === 'ai') accuracy += 0.05;
    
    return Math.min(accuracy, 0.95); // Cap at 95%
  }

  /**
   * Check if authentication is required
   */
  private requiresAuthentication(html: string): boolean {
    const content = html.toLowerCase();
    const authIndicators = [
      'login', 'sign in', 'authenticate', 'please log in',
      'session expired', 'unauthorized', 'access denied'
    ];
    
    return authIndicators.some(indicator => content.includes(indicator));
  }

  /**
   * Check for dynamic content loading
   */
  private hasDynamicContent(html: string): boolean {
    const content = html.toLowerCase();
    const dynamicIndicators = [
      'loading...', 'please wait', 'data-loading',
      'react-', 'vue-', 'angular-', 'spa-'
    ];
    
    return dynamicIndicators.some(indicator => content.includes(indicator));
  }

  /**
   * Get default analysis for error cases
   */
  private getDefaultAnalysis(): WebsiteAnalysis {
    return {
      structure: {
        hasEvents: false,
        hasCalendar: false,
        hasAssignments: false,
        hasTables: false,
        hasLists: false,
        commonPatterns: [],
        semanticElements: []
      },
      supportLevel: 'poor',
      recommendedStrategy: 'ai',
      estimatedAccuracy: 0.3,
      requiredAuthentication: false,
      dynamicContent: false
    };
  }
} 