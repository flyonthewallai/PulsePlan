// @ts-ignore - Package will be installed during setup
import * as puppeteer from 'puppeteer';
// @ts-ignore - Package will be installed during setup
import * as cheerio from 'cheerio';
// @ts-ignore - Cheerio types compatibility
const CheerioElement = cheerio;
import { 
  ScrapingConfig, 
  ScrapedContent, 
  ExtractedData, 
  ExtractedEvent,
  PatternData,
  PatternEvent,
  ScrapingResult,
  SecurityValidation,
  CustomSelectors
} from '../types/scraping';
import { GeminiService } from './geminiService';
import { WebsiteAnalyzer } from './websiteAnalyzer';

export class UniversalWebScraper {
  private browser?: puppeteer.Browser;
  private gemini: GeminiService;
  private analyzer: WebsiteAnalyzer;

  constructor() {
    this.gemini = new GeminiService();
    this.analyzer = new WebsiteAnalyzer();
  }

  /**
   * Initialize browser instance for scraping
   */
  async initializeBrowser(): Promise<void> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--disable-software-rasterizer'
        ]
      });
    }
  }

  /**
   * Main scraping method - extracts data from any website
   */
  async scrapeWebsite(config: ScrapingConfig): Promise<ScrapingResult> {
    const startTime = Date.now();
    
    try {
      // Step 1: Security validation
      const security = this.validateSecurity(config.url);
      if (!security.isValidUrl || !security.isDomainAllowed) {
        return {
          success: false,
          error: `Security validation failed: ${security.warnings.join(', ')}`,
          cached: false,
          processingTime: Date.now() - startTime
        };
      }

      // Step 2: Initialize browser if needed
      await this.initializeBrowser();

      // Step 3: Scrape content from website
      const scrapedContent = await this.scrapeContent(config);

      // Step 4: Analyze website structure and strategy
      const analysis = await this.analyzer.analyzeWebsite(
        scrapedContent.html, 
        config.url, 
        scrapedContent.screenshot
      );

      // Step 5: Extract data using recommended strategy
      const extractedData = await this.extractData(scrapedContent, analysis);

      return {
        success: true,
        data: extractedData,
        cached: false,
        processingTime: Date.now() - startTime
      };
    } catch (error) {
      console.error('Scraping error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown scraping error',
        cached: false,
        processingTime: Date.now() - startTime
      };
    }
  }

  /**
   * Scrape content from website with browser automation
   */
  private async scrapeContent(config: ScrapingConfig): Promise<ScrapedContent> {
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }

    const page = await this.browser.newPage();
    
    try {
      // Set user agent to appear more like a real browser
      await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      );

      // Set additional headers if provided
      if (config.authHeaders) {
        await page.setExtraHTTPHeaders(config.authHeaders);
      }

      // Navigate to the page
      await page.goto(config.url, { 
        waitUntil: 'networkidle2',
        timeout: config.timeout || 30000
      });

      // Wait for specific elements if configured
      if (config.waitForElements) {
        for (const selector of config.waitForElements) {
          try {
            await page.waitForSelector(selector, { timeout: 5000 });
          } catch (e) {
            console.warn(`Element ${selector} not found within timeout`);
          }
        }
      }

      // Scroll to bottom if configured (useful for lazy-loaded content)
      if (config.scrollToBottom) {
        await this.autoScroll(page);
      }

      // Extract content
      const html = await page.content();
      const title = await page.title();
      
      // Take screenshot for AI analysis
      const screenshot = await page.screenshot({ 
        encoding: 'base64',
        fullPage: false // Just viewport for performance
      });

      const url = new URL(config.url);
      
      return {
        html,
        screenshot: screenshot as string,
        url: config.url,
        timestamp: new Date(),
        metadata: {
          title,
          domain: url.hostname,
          contentLength: html.length
        }
      };
    } finally {
      await page.close();
    }
  }

  /**
   * Extract data using the appropriate strategy
   */
  private async extractData(
    content: ScrapedContent,
    analysis: any
  ): Promise<ExtractedData> {
    const strategy = analysis.recommendedStrategy || 'hybrid';
    
    let extractedEvents: ExtractedEvent[] = [];
    let extractionMethod: 'pattern' | 'ai' | 'hybrid' = strategy;
    let overallConfidence = 0;

    if (strategy === 'pattern' || strategy === 'hybrid') {
      const patternData = await this.extractWithPatterns(content);
      extractedEvents = this.convertPatternToEvents(patternData.events);
      overallConfidence = patternData.confidence;
    }

    if (strategy === 'ai' || strategy === 'hybrid') {
      const aiData = await this.gemini.extractScheduleData({
        html: content.html.substring(0, 20000), // Limit for API
        screenshot: content.screenshot,
        context: 'academic_schedule',
        extractionType: 'schedule'
      });
      
      if (strategy === 'hybrid') {
        extractedEvents = this.mergeResults(extractedEvents, aiData.events);
        overallConfidence = (overallConfidence + aiData.metadata.overallConfidence) / 2;
      } else {
        extractedEvents = aiData.events;
        overallConfidence = aiData.metadata.overallConfidence;
      }
    }

    return {
      events: extractedEvents,
      metadata: {
        url: content.url,
        websiteType: this.determineWebsiteType(analysis),
        platform: analysis.structure.detectedPlatform,
        lastUpdated: new Date(),
        supportLevel: analysis.supportLevel || 'fair'
      },
      overallConfidence,
      extractionMethod,
      processingTime: Date.now() - content.timestamp.getTime()
    };
  }

  /**
   * Pattern-based extraction using CSS selectors and common patterns
   */
  private async extractWithPatterns(
    content: ScrapedContent
  ): Promise<PatternData> {
    const $ = cheerio.load(content.html);
    const events: PatternEvent[] = [];
    
    // Default selectors for common academic content
    const defaultSelectors = {
      events: [
        '.event', '.assignment', '.due-date', '.deadline',
        '.assignment-item', '.course-event', '.task-item',
        '.homework', '.project', '.exam'
      ],
      dates: [
        'time[datetime]', '.date', '.due-date', '.deadline',
        '[data-date]', 'span:contains("Due:")', '*:contains("Due Date")'
      ],
      titles: [
        '.title', '.assignment-title', '.event-title', '.name',
        'h1', 'h2', 'h3', 'h4', '.subject', '.task-name'
      ],
      descriptions: [
        '.description', '.details', '.content', '.summary',
        '.assignment-description', '.event-description'
      ]
    };

    // Merge custom selectors with defaults
    const selectors = {
      events: [...defaultSelectors.events],
      dates: [...defaultSelectors.dates],
      titles: [...defaultSelectors.titles],
      descriptions: [...defaultSelectors.descriptions]
    };

    // Extract events using selectors
    selectors.events.forEach(selector => {
      $(selector).each((index, element) => {
        const $element = $(element);
        
        // Extract basic information
        const title = this.extractTitle($element, selectors.titles);
        const dateInfo = this.extractDate($element, selectors.dates);
        const description = this.extractDescription($element, selectors.descriptions);
        
        if (title && title.trim().length > 0) {
          events.push({
            title: title.trim(),
            rawDate: dateInfo.raw,
            parsedDate: dateInfo.parsed,
            description: description?.trim(),
            selector,
            confidence: this.calculatePatternConfidence($element, title, dateInfo.parsed)
          });
        }
      });
    });

    // Calculate overall confidence
    const avgConfidence = events.length > 0 
      ? events.reduce((sum, event) => sum + event.confidence, 0) / events.length
      : 0;

    return {
      events: this.deduplicatePatternEvents(events),
      confidence: avgConfidence,
      extractionMethod: 'pattern'
    };
  }

  /**
   * Extract title from element using multiple strategies
   */
  private extractTitle($element: any, titleSelectors: string[]): string {
    // Try direct text content first
    let title = $element.text().trim();
    if (title && title.length > 5) return title;

    // Try title selectors within the element
    for (const selector of titleSelectors) {
      const found = $element.find(selector).first().text().trim();
      if (found && found.length > 5) return found;
    }

    // Try data attributes
    title = $element.attr('title') || $element.attr('data-title') || '';
    if (title && title.length > 5) return title;

    // Try aria-label
    title = $element.attr('aria-label') || '';
    if (title && title.length > 5) return title;

    return $element.text().trim();
  }

  /**
   * Extract date information from element
   */
  private extractDate(
    $element: any, 
    dateSelectors: string[]
  ): { raw?: string; parsed?: Date } {
    // Try datetime attribute first
    const datetime = $element.find('time[datetime]').attr('datetime') ||
                    $element.attr('datetime');
    if (datetime) {
      return {
        raw: datetime,
        parsed: new Date(datetime)
      };
    }

    // Try date selectors
    for (const selector of dateSelectors) {
      const dateText = $element.find(selector).first().text().trim();
      if (dateText) {
        const parsed = this.parseDate(dateText);
        if (parsed) {
          return {
            raw: dateText,
            parsed
          };
        }
      }
    }

    // Try text content for date patterns
    const text = $element.text();
    const dateMatch = text.match(/(?:due|deadline|on)\s*:?\s*([^,\n]+)/i);
    if (dateMatch) {
      const parsed = this.parseDate(dateMatch[1]);
      return {
        raw: dateMatch[1],
        parsed
      };
    }

    return {};
  }

  /**
   * Extract description from element
   */
  private extractDescription(
    $element: any, 
    descSelectors: string[]
  ): string | undefined {
    for (const selector of descSelectors) {
      const desc = $element.find(selector).first().text().trim();
      if (desc && desc.length > 10) return desc;
    }
    return undefined;
  }

  /**
   * Parse date string into Date object
   */
  private parseDate(dateStr: string): Date | undefined {
    try {
      // Clean the date string
      const cleaned = dateStr.replace(/^\s*due\s*:?\s*/i, '').trim();
      
      // Try parsing as ISO date first
      const isoDate = new Date(cleaned);
      if (!isNaN(isoDate.getTime())) return isoDate;

      // Try common date formats
      const formats = [
        /(\d{1,2})\/(\d{1,2})\/(\d{4})/,  // MM/DD/YYYY
        /(\d{4})-(\d{2})-(\d{2})/,        // YYYY-MM-DD
        /(\w+)\s+(\d{1,2}),?\s+(\d{4})/   // Month DD, YYYY
      ];

      for (const format of formats) {
        const match = cleaned.match(format);
        if (match) {
          const parsed = new Date(cleaned);
          if (!isNaN(parsed.getTime())) return parsed;
        }
      }
    } catch (error) {
      console.warn('Date parsing failed:', dateStr, error);
    }
    return undefined;
  }

  /**
   * Calculate confidence score for pattern extraction
   */
  private calculatePatternConfidence(
    $element: any,
    title: string,
    parsedDate?: Date
  ): number {
    let confidence = 0.3; // Base confidence

    // Title quality
    if (title.length > 10) confidence += 0.2;
    if (title.toLowerCase().includes('assignment')) confidence += 0.1;
    if (title.toLowerCase().includes('homework')) confidence += 0.1;
    if (title.toLowerCase().includes('project')) confidence += 0.1;
    if (title.toLowerCase().includes('exam')) confidence += 0.1;

    // Date presence
    if (parsedDate) confidence += 0.2;

    // Element context
    if ($element.hasClass('assignment')) confidence += 0.1;
    if ($element.hasClass('event')) confidence += 0.1;
    if ($element.find('time').length > 0) confidence += 0.1;

    return Math.min(confidence, 0.9);
  }

  /**
   * Convert pattern events to standard event format
   */
  private convertPatternToEvents(patterns: PatternEvent[]): ExtractedEvent[] {
    return patterns.map(pattern => ({
      title: pattern.title,
      description: pattern.description,
      dueDate: pattern.parsedDate?.toISOString(),
      type: this.inferEventType(pattern.title),
      confidence: pattern.confidence,
      sourceElement: pattern.selector,
      priority: this.inferPriority(pattern.title)
    }));
  }

  /**
   * Infer event type from title
   */
  private inferEventType(title: string): ExtractedEvent['type'] {
    const lower = title.toLowerCase();
    if (lower.includes('exam') || lower.includes('test') || lower.includes('quiz')) return 'exam';
    if (lower.includes('project')) return 'project';
    if (lower.includes('reading') || lower.includes('read')) return 'reading';
    if (lower.includes('lecture') || lower.includes('class')) return 'lecture';
    if (lower.includes('assignment') || lower.includes('homework')) return 'assignment';
    return 'other';
  }

  /**
   * Infer priority from title and context
   */
  private inferPriority(title: string): 'low' | 'medium' | 'high' {
    const lower = title.toLowerCase();
    if (lower.includes('final') || lower.includes('exam')) return 'high';
    if (lower.includes('project') || lower.includes('midterm')) return 'high';
    if (lower.includes('assignment')) return 'medium';
    return 'low';
  }

  /**
   * Merge results from pattern and AI extraction
   */
  private mergeResults(
    patternEvents: ExtractedEvent[],
    aiEvents: ExtractedEvent[]
  ): ExtractedEvent[] {
    const merged: ExtractedEvent[] = [...patternEvents];
    
    // Add AI events that don't seem to be duplicates
    for (const aiEvent of aiEvents) {
      const isDuplicate = patternEvents.some(pattern => 
        this.areEventsSimilar(pattern, aiEvent)
      );
      
      if (!isDuplicate) {
        merged.push(aiEvent);
      }
    }

    return merged;
  }

  /**
   * Check if two events are likely duplicates
   */
  private areEventsSimilar(event1: ExtractedEvent, event2: ExtractedEvent): boolean {
    // Simple similarity check based on title
    const title1 = event1.title.toLowerCase().trim();
    const title2 = event2.title.toLowerCase().trim();
    
    // Exact match
    if (title1 === title2) return true;
    
    // High similarity (>80% character overlap)
    const similarity = this.calculateStringSimilarity(title1, title2);
    return similarity > 0.8;
  }

  /**
   * Calculate string similarity (simple implementation)
   */
  private calculateStringSimilarity(str1: string, str2: string): number {
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;
    
    if (longer.length === 0) return 1.0;
    
    const editDistance = this.levenshteinDistance(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  private levenshteinDistance(str1: string, str2: string): number {
    const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null));
    
    for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
    for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;
    
    for (let j = 1; j <= str2.length; j++) {
      for (let i = 1; i <= str1.length; i++) {
        const substitutionCost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1, // deletion
          matrix[j - 1][i] + 1, // insertion
          matrix[j - 1][i - 1] + substitutionCost // substitution
        );
      }
    }
    
    return matrix[str2.length][str1.length];
  }

  /**
   * Remove duplicate pattern events
   */
  private deduplicatePatternEvents(events: PatternEvent[]): PatternEvent[] {
    const unique: PatternEvent[] = [];
    
    for (const event of events) {
      const isDuplicate = unique.some(existing => 
        existing.title.toLowerCase() === event.title.toLowerCase()
      );
      
      if (!isDuplicate) {
        unique.push(event);
      }
    }
    
    return unique;
  }

  /**
   * Auto-scroll page to load dynamic content
   */
  private async autoScroll(page: puppeteer.Page): Promise<void> {
    await page.evaluate(async () => {
      await new Promise((resolve) => {
        let totalHeight = 0;
        const distance = 100;
        const timer = setInterval(() => {
          const scrollHeight = document.body.scrollHeight;
          window.scrollBy(0, distance);
          totalHeight += distance;

          if (totalHeight >= scrollHeight) {
            clearInterval(timer);
            resolve(undefined);
          }
        }, 100);
      });
    });
  }

  /**
   * Validate URL security
   */
  private validateSecurity(url: string): SecurityValidation {
    try {
      const parsed = new URL(url);
      const warnings: string[] = [];
      
      // Check protocol
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return {
          isValidUrl: false,
          isDomainAllowed: false,
          hasSSL: false,
          riskLevel: 'high',
          warnings: ['Invalid protocol - only HTTP and HTTPS are allowed']
        };
      }

      // Check for localhost/internal IPs
      const hostname = parsed.hostname.toLowerCase();
      const blockedHosts = ['localhost', '127.0.0.1', '0.0.0.0', '10.', '192.168.', '172.'];
      const isBlocked = blockedHosts.some(blocked => hostname.includes(blocked));
      
      if (isBlocked) {
        warnings.push('Local/internal network access not allowed');
      }

      // Check SSL
      const hasSSL = parsed.protocol === 'https:';
      if (!hasSSL) {
        warnings.push('Non-HTTPS URLs have higher security risk');
      }

      return {
        isValidUrl: true,
        isDomainAllowed: !isBlocked,
        hasSSL,
        riskLevel: warnings.length > 0 ? 'medium' : 'low',
        warnings
      };
    } catch (error) {
      return {
        isValidUrl: false,
        isDomainAllowed: false,
        hasSSL: false,
        riskLevel: 'high',
        warnings: ['Invalid URL format']
      };
    }
  }

  /**
   * Determine website type from analysis
   */
  private determineWebsiteType(analysis: any): 'lms' | 'calendar' | 'university' | 'generic' | 'unknown' {
    const platform = analysis.structure.detectedPlatform;
    
    if (['canvas', 'blackboard', 'moodle', 'brightspace'].includes(platform)) return 'lms';
    if (['google_calendar', 'outlook'].includes(platform)) return 'calendar';
    if (platform === 'university') return 'university';
    if (platform === 'unknown') return 'unknown';
    
    return 'generic';
  }

  /**
   * Clean up browser resources
   */
  async cleanup(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = undefined;
    }
  }
} 