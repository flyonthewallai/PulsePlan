import express from 'express';
// @ts-ignore - Rate limiting package will be installed
import rateLimit from 'express-rate-limit';
import { UniversalWebScraper } from '../services/universalScraper';
import { WebsiteAnalyzer } from '../services/websiteAnalyzer';
import { GeminiService } from '../services/geminiService';
import { ScrapingConfig } from '../types/scraping';

const router = express.Router();

// Initialize services
const scraper = new UniversalWebScraper();
const analyzer = new WebsiteAnalyzer();
const gemini = new GeminiService();

// Rate limiting for scraping endpoints
const scrapingLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // 10 requests per hour per IP
  message: {
    error: 'Rate limit exceeded',
    message: 'Too many scraping requests. Please try again later.',
    retryAfter: '1 hour'
  },
  standardHeaders: true,
  legacyHeaders: false
});

// Apply rate limiting to all scraping routes
router.use(scrapingLimiter);

/**
 * POST /api/scraping/analyze-url
 * Analyze a website's structure and compatibility
 */
router.post('/analyze-url', async (req, res) => {
  try {
    const { url } = req.body;

    if (!url || typeof url !== 'string') {
      return res.status(400).json({
        error: 'URL is required',
        message: 'Please provide a valid URL to analyze'
      });
    }

    // Initialize browser for content scraping
    await scraper.initializeBrowser();

    // Scrape basic content for analysis
    const config: ScrapingConfig = {
      url,
      timeout: 15000 // Shorter timeout for analysis
    };

    const scrapingResult = await scraper.scrapeWebsite(config);

    if (!scrapingResult.success || !scrapingResult.data) {
      return res.status(400).json({
        error: 'Failed to analyze website',
        message: scrapingResult.error || 'Could not access the website',
        suggestions: [
          'Check if the URL is accessible',
          'Ensure the website doesn\'t require authentication',
          'Try a direct link to the assignments/schedule page'
        ]
      });
    }

    // Perform detailed analysis
    const analysis = await analyzer.analyzeWebsite(
      scrapingResult.data.events.length > 0 ? 'Has content' : 'Limited content',
      url
    );

    res.json({
      success: true,
      analysis: {
        url,
        supportLevel: analysis.supportLevel,
        recommendedStrategy: analysis.recommendedStrategy,
        estimatedAccuracy: analysis.estimatedAccuracy,
        requiresAuthentication: analysis.requiredAuthentication,
        hasDynamicContent: analysis.dynamicContent,
        detectedPlatform: analysis.structure.detectedPlatform,
        hasScheduleData: analysis.structure.hasEvents || analysis.structure.hasAssignments,
        confidence: scrapingResult.data.overallConfidence
      },
      extractionPreview: {
        eventsFound: scrapingResult.data.events.length,
        sampleEvents: scrapingResult.data.events.slice(0, 3).map(event => ({
          title: event.title,
          type: event.type,
          confidence: event.confidence
        }))
      },
      processingTime: scrapingResult.processingTime
    });

  } catch (error) {
    console.error('URL analysis error:', error);
    res.status(500).json({
      error: 'Analysis failed',
      message: 'An error occurred while analyzing the website',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/scraping/extract-html
 * Extract schedule data directly from HTML content (for extensions)
 */
router.post('/extract-html', async (req, res) => {
  try {
    const { html, screenshot, extractionType, context } = req.body;

    if (!html || typeof html !== 'string') {
      return res.status(400).json({
        error: 'HTML content is required',
        message: 'Please provide HTML content to extract data from'
      });
    }

    // Use Gemini service directly for HTML content
    const geminiRequest = {
      html: html.substring(0, 50000), // Limit size for API efficiency
      screenshot,
      extractionType: extractionType || 'canvas_assignments',
      context: context || 'Canvas LMS page'
    };

    const aiData = await gemini.extractScheduleData(geminiRequest);

    res.json({
      success: true,
      data: {
        extractedAt: new Date().toISOString(),
        events: aiData.events,
        metadata: aiData.metadata,
        extraction: {
          method: aiData.metadata.extractionMethod,
          confidence: aiData.metadata.overallConfidence,
          eventsFound: aiData.events.length
        }
      }
    });

  } catch (error) {
    console.error('HTML extraction error:', error);
    res.status(500).json({
      error: 'Extraction failed',
      message: 'An error occurred while extracting data from HTML',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/scraping/extract-data
 * Extract schedule data from a website
 */
router.post('/extract-data', async (req, res) => {
  try {
    const { url, options = {} } = req.body;

    if (!url || typeof url !== 'string') {
      return res.status(400).json({
        error: 'URL is required',
        message: 'Please provide a valid URL to extract data from'
      });
    }

    // Configure scraping based on options
    const config: ScrapingConfig = {
      url,
      timeout: options.timeout || 30000,
      scrollToBottom: options.scrollToBottom || false,
      waitForElements: options.waitForElements || [],
      authHeaders: options.authHeaders || undefined,
      maxRetries: options.maxRetries || 1
    };

    await scraper.initializeBrowser();
    const result = await scraper.scrapeWebsite(config);

    if (!result.success || !result.data) {
      return res.status(400).json({
        error: 'Extraction failed',
        message: result.error || 'Could not extract data from the website',
        suggestions: [
          'Verify the URL contains schedule/assignment data',
          'Check if authentication is required',
          'Try enabling scroll-to-bottom option for dynamic content'
        ]
      });
    }

    // Enhance extracted data with AI
    const enhancedEvents = await gemini.enhanceTasks(
      result.data.events.map(event => ({
        title: event.title,
        description: event.description,
        dueDate: event.dueDate ? new Date(event.dueDate) : undefined,
        course: event.course,
        priority: event.priority || 'medium',
        estimatedDuration: event.estimatedDuration,
        type: event.type,
        source: 'scraped' as const,
        sourceUrl: url,
        confidence: event.confidence
      }))
    );

    res.json({
      success: true,
      data: {
        url,
        extractedAt: new Date().toISOString(),
        events: enhancedEvents,
        metadata: result.data.metadata,
        extraction: {
          method: result.data.extractionMethod,
          confidence: result.data.overallConfidence,
          processingTime: result.processingTime,
          eventsFound: enhancedEvents.length
        }
      }
    });

  } catch (error) {
    console.error('Data extraction error:', error);
    res.status(500).json({
      error: 'Extraction failed',
      message: 'An error occurred while extracting data',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * GET /api/scraping/supported-types
 * Get information about supported website types
 */
router.get('/supported-types', async (req, res) => {
  try {
    const supportedTypes = {
      excellentSupport: [
        {
          platform: 'Canvas LMS',
          domains: ['instructure.com', '*.edu (Canvas instances)'],
          features: ['Assignments', 'Due dates', 'Course information', 'Descriptions'],
          accuracy: '90-95%'
        },
        {
          platform: 'Blackboard Learn',
          domains: ['blackboard.com', '*.edu (Blackboard instances)'],
          features: ['Assignments', 'Due dates', 'Course content', 'Grades'],
          accuracy: '85-90%'
        },
        {
          platform: 'Moodle',
          domains: ['moodle sites', '*.edu (Moodle instances)'],
          features: ['Activities', 'Deadlines', 'Course structure'],
          accuracy: '80-90%'
        }
      ],
      goodSupport: [
        {
          platform: 'University Websites',
          domains: ['*.edu domains'],
          features: ['Academic calendars', 'Event listings', 'Course schedules'],
          accuracy: '70-85%'
        },
        {
          platform: 'Google Calendar',
          domains: ['calendar.google.com'],
          features: ['Events', 'Recurring schedules', 'Descriptions'],
          accuracy: '85-95%'
        }
      ],
      fairSupport: [
        {
          platform: 'Generic Academic Sites',
          domains: ['Various educational websites'],
          features: ['Basic event extraction', 'Date parsing'],
          accuracy: '50-70%'
        }
      ],
      limitations: [
        'Websites requiring complex authentication may need manual login',
        'Heavy JavaScript sites may require special handling',
        'Private/internal sites may not be accessible',
        'Rate limiting applies to prevent abuse'
      ],
      tips: [
        'Use direct links to assignment/schedule pages for best results',
        'Ensure you have necessary permissions to access the content',
        'For LMS platforms, try the main assignments or calendar page',
        'Enable scroll-to-bottom for sites with lazy loading'
      ]
    };

    res.json({
      success: true,
      supportedTypes,
      lastUpdated: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error getting supported types:', error);
    res.status(500).json({
      error: 'Failed to get supported types',
      message: 'An error occurred while retrieving information'
    });
  }
});

/**
 * POST /api/scraping/test-connection
 * Test connection to scraping services
 */
router.post('/test-connection', async (req, res) => {
  try {
    const tests = {
      browser: false,
      gemini: false,
      analyzer: false
    };

    // Test browser initialization
    try {
      await scraper.initializeBrowser();
      tests.browser = true;
    } catch (error) {
      console.error('Browser test failed:', error);
    }

    // Test Gemini connection
    try {
      tests.gemini = await gemini.testConnection();
    } catch (error) {
      console.error('Gemini test failed:', error);
    }

    // Test analyzer
    try {
      const testHtml = '<html><body><div class="assignment">Test Assignment</div></body></html>';
      await analyzer.analyzeWebsite(testHtml, 'https://example.com');
      tests.analyzer = true;
    } catch (error) {
      console.error('Analyzer test failed:', error);
    }

    const allPassed = Object.values(tests).every(Boolean);

    res.json({
      success: allPassed,
      tests,
      message: allPassed 
        ? 'All scraping services are operational' 
        : 'Some services are not functioning properly',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Connection test error:', error);
    res.status(500).json({
      error: 'Test failed',
      message: 'An error occurred while testing connections'
    });
  }
});

/**
 * POST /api/scraping/batch-extract
 * Extract data from multiple URLs
 */
router.post('/batch-extract', async (req, res) => {
  try {
    const { urls, options = {} } = req.body;

    if (!Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({
        error: 'URLs array is required',
        message: 'Please provide an array of URLs to extract data from'
      });
    }

    if (urls.length > 5) {
      return res.status(400).json({
        error: 'Too many URLs',
        message: 'Maximum 5 URLs allowed per batch request'
      });
    }

    await scraper.initializeBrowser();

    interface BatchResult {
      url: string;
      success: boolean;
      eventsFound: number;
      confidence?: number;
      events?: any[];
      error?: string;
    }

    const results: BatchResult[] = [];
    let totalEvents = 0;

    for (const url of urls) {
      try {
        const config: ScrapingConfig = {
          url,
          timeout: options.timeout || 20000,
          scrollToBottom: options.scrollToBottom || false
        };

        const result = await scraper.scrapeWebsite(config);
        
        if (result.success && result.data) {
          totalEvents += result.data.events.length;
          results.push({
            url,
            success: true,
            eventsFound: result.data.events.length,
            confidence: result.data.overallConfidence,
            events: result.data.events
          });
        } else {
          results.push({
            url,
            success: false,
            error: result.error || 'Extraction failed',
            eventsFound: 0
          });
        }
      } catch (error) {
        results.push({
          url,
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
          eventsFound: 0
        });
      }
    }

    const successCount = results.filter(r => r.success).length;

    res.json({
      success: successCount > 0,
      summary: {
        totalUrls: urls.length,
        successfulExtractions: successCount,
        totalEventsFound: totalEvents,
                 averageConfidence: results
           .filter(r => r.success && r.confidence)
           .reduce((acc: number, r) => acc + (r.confidence || 0), 0) / Math.max(successCount, 1)
      },
      results
    });

  } catch (error) {
    console.error('Batch extraction error:', error);
    res.status(500).json({
      error: 'Batch extraction failed',
      message: 'An error occurred during batch processing'
    });
  }
});

// Cleanup resources on process exit
process.on('SIGINT', async () => {
  console.log('Cleaning up scraping resources...');
  await scraper.cleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Cleaning up scraping resources...');
  await scraper.cleanup();
  process.exit(0);
});

export default router; 