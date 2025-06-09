# Web Scraping Service Implementation Plan

## Core Architecture

### 2.1 Universal Web Scraper (`webScrapingService.ts`)

```typescript
interface ScrapingConfig {
  url: string;
  selectors?: CustomSelectors;
  authHeaders?: Record<string, string>;
  waitForElements?: string[];
  scrollToBottom?: boolean;
  maxRetries?: number;
}

interface ExtractedData {
  events: ScheduleEvent[];
  assignments: Assignment[];
  deadlines: Deadline[];
  metadata: WebsiteMetadata;
  confidence: number;
}

class UniversalWebScraper {
  // Multi-stage scraping pipeline
  async scrapeWebsite(config: ScrapingConfig): Promise<ExtractedData>
  
  // Intelligent element detection
  async analyzePageStructure(url: string): Promise<PageStructure>
  
  // Custom extraction rules
  async applyExtractionRules(html: string, rules: ExtractionRule[]): Promise<RawData>
  
  // AI-powered data interpretation
  async interpretScrapedData(rawData: RawData): Promise<ExtractedData>
}
```

### 2.2 Website Analysis Engine

The system will use a multi-layered approach to handle any website:

**Layer 1: Pattern Recognition**
- Common LMS patterns (Canvas, Blackboard, Moodle, etc.)
- University website structures
- Calendar application layouts
- Generic schedule/event patterns

**Layer 2: Dynamic Analysis**
- DOM structure analysis
- ARIA labels and semantic HTML detection
- Table/list pattern recognition
- Date/time pattern matching

**Layer 3: AI-Powered Extraction**
- Gemini Vision API for visual layout analysis
- Content understanding through Gemini text processing
- Context-aware data extraction
- Confidence scoring for extracted data

### 2.3 Implementation Strategy

#### Backend Service Structure:

```typescript
// server/src/services/webScrapingService.ts
import puppeteer from 'puppeteer';
import cheerio from 'cheerio';
import { GeminiService } from './geminiService';

export class WebScrapingService {
  private gemini: GeminiService;
  private browser: Browser;

  async initializeBrowser(): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  }

  async scrapeWithAuthentication(
    url: string, 
    credentials?: AuthCredentials
  ): Promise<ScrapedContent> {
    const page = await this.browser.newPage();
    
    // Handle authentication if needed
    if (credentials) {
      await this.handleAuthentication(page, credentials);
    }
    
    // Navigate and wait for content
    await page.goto(url, { waitUntil: 'networkidle2' });
    
    // Smart waiting for dynamic content
    await this.waitForContentLoad(page);
    
    // Extract HTML and screenshots for AI analysis
    const html = await page.content();
    const screenshot = await page.screenshot({ encoding: 'base64' });
    
    return { html, screenshot, url };
  }

  async extractScheduleData(content: ScrapedContent): Promise<ExtractedData> {
    // Stage 1: Pattern-based extraction
    const patternData = await this.extractWithPatterns(content.html);
    
    // Stage 2: AI-powered extraction
    const aiData = await this.gemini.extractScheduleData({
      html: content.html,
      screenshot: content.screenshot,
      context: 'academic_schedule'
    });
    
    // Stage 3: Merge and validate
    return this.mergeAndValidateData(patternData, aiData);
  }

  private async extractWithPatterns(html: string): Promise<PatternData> {
    const $ = cheerio.load(html);
    
    // Common patterns for schedule data
    const patterns = {
      events: [
        '.event', '.assignment', '.due-date',
        '[data-event]', '[data-assignment]',
        'tr:has(td:contains("Due"))',
        'li:has(time)', '.calendar-event'
      ],
      dates: [
        'time[datetime]', '.date', '.due-date',
        '[data-date]', 'span:contains("Due:")'
      ],
      titles: [
        '.title', '.assignment-title', '.event-title',
        'h1, h2, h3, h4', '.name', '[data-title]'
      ]
    };
    
    return this.extractByPatterns($, patterns);
  }
}
```

### 2.4 Gemini Integration for Data Extraction

```typescript
// server/src/services/geminiService.ts
import { GoogleGenerativeAI } from '@google/generative-ai';

export class GeminiService {
  private genAI: GoogleGenerativeAI;
  private model: any;

  constructor() {
    this.genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-1.5-pro' });
  }

  async extractScheduleData(input: {
    html: string;
    screenshot?: string;
    context: string;
  }): Promise<AIExtractedData> {
    const prompt = this.buildExtractionPrompt(input.context);
    
    const result = await this.model.generateContent([
      prompt,
      { text: input.html },
      ...(input.screenshot ? [{ 
        inlineData: { 
          mimeType: 'image/png', 
          data: input.screenshot 
        } 
      }] : [])
    ]);

    return this.parseAIResponse(result.response.text());
  }

  async optimizeSchedule(input: {
    tasks: Task[];
    availability: TimeSlot[];
    preferences: SchedulingPreferences;
    constraints: Constraint[];
  }): Promise<OptimizedSchedule> {
    const prompt = this.buildOptimizationPrompt();
    
    const context = {
      tasks: input.tasks,
      availability: input.availability,
      preferences: input.preferences,
      constraints: input.constraints
    };

    const result = await this.model.generateContent([
      prompt,
      { text: JSON.stringify(context) }
    ]);

    return this.parseScheduleResponse(result.response.text());
  }

  private buildExtractionPrompt(context: string): string {
    return `
You are an expert at extracting schedule and assignment data from academic websites.

Context: ${context}

Extract the following information from the provided HTML and/or screenshot:
1. Events/assignments with titles
2. Due dates and times
3. Descriptions or details
4. Course/subject information
5. Priority or importance indicators
6. Recurring patterns

Return a JSON object with this structure:
{
  "events": [
    {
      "title": "string",
      "description": "string",
      "dueDate": "ISO 8601 date string",
      "course": "string",
      "priority": "low|medium|high",
      "estimatedDuration": "number (minutes)",
      "type": "assignment|exam|project|reading",
      "confidence": "number (0-1)"
    }
  ],
  "metadata": {
    "websiteType": "string",
    "extractionMethod": "string",
    "overallConfidence": "number (0-1)"
  }
}

Focus on accuracy and include confidence scores for each extracted item.
`;
  }

  private buildOptimizationPrompt(): string {
    return `
You are an AI scheduling assistant specialized in creating optimal academic schedules.

Analyze the provided tasks, availability, preferences, and constraints to create the most effective weekly schedule.

Consider:
1. Task priorities and deadlines
2. User's energy levels throughout the day
3. Break times and cognitive load management
4. Deadline proximity and urgency
5. Task dependencies and logical ordering
6. User preferences for study times
7. Buffer time for unexpected changes

Return a JSON object with optimized time blocks:
{
  "schedule": [
    {
      "day": "string (Monday-Sunday)",
      "timeSlots": [
        {
          "startTime": "HH:MM",
          "endTime": "HH:MM",
          "taskId": "string",
          "activity": "string",
          "priority": "low|medium|high",
          "reasoning": "string"
        }
      ]
    }
  ],
  "insights": [
    "string array of scheduling insights"
  ],
  "optimization_score": "number (0-100)"
}
`;
  }
}
```

## Phase 3: Enhanced Onboarding Implementation

### 3.1 Smart Onboarding Flow

The new onboarding will be a multi-step process that maximizes automation:

```typescript
// src/app/onboarding/websites.tsx
export default function WebsitesScreen() {
  const [urls, setUrls] = useState<string[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [extractedData, setExtractedData] = useState<ExtractedData[]>([]);

  const handleUrlSubmit = async (url: string) => {
    setAnalyzing(true);
    try {
      // Step 1: Analyze website compatibility
      const analysis = await scrapingService.analyzeWebsite(url);
      
      // Step 2: Extract data
      const data = await scrapingService.extractData(url);
      
      // Step 3: Process with AI
      const processedData = await geminiService.processExtractedData(data);
      
      setExtractedData(prev => [...prev, processedData]);
    } catch (error) {
      // Handle extraction errors gracefully
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <ScrollView>
      <Text className="text-2xl font-bold mb-4">
        Add Your Academic Websites
      </Text>
      
      <WebsiteUrlInput onSubmit={handleUrlSubmit} />
      
      {analyzing && <ExtractionProgress />}
      
      {extractedData.map((data, index) => (
        <DataExtractionPreview 
          key={index} 
          data={data}
          onEdit={(editedData) => updateExtractedData(index, editedData)}
        />
      ))}
      
      <CalendarSyncSection />
      
      <SchedulingPreferences />
    </ScrollView>
  );
}
```

### 3.2 Calendar Integration Enhancement

```typescript
// server/src/services/calendarIntegrationService.ts
export class CalendarIntegrationService {
  async syncAllCalendars(userId: string): Promise<CalendarData> {
    const integrations = await this.getUserIntegrations(userId);
    
    const calendarData = await Promise.all([
      this.syncGoogleCalendar(integrations.google),
      this.syncOutlookCalendar(integrations.outlook),
      this.syncAppleCalendar(integrations.apple)
    ]);

    return this.mergeCalendarData(calendarData);
  }

  async extractAvailabilityWindows(
    calendarData: CalendarData,
    preferences: UserPreferences
  ): Promise<AvailabilityWindow[]> {
    // AI-powered availability analysis
    return this.gemini.analyzeAvailability({
      existingEvents: calendarData.events,
      preferences: preferences,
      workingHours: preferences.workingHours,
      breakPreferences: preferences.breaks
    });
  }
}
```

## Phase 4: Schedule Optimization Engine

### 4.1 AI-Powered Schedule Generator

```typescript
// server/src/services/scheduleOptimizer.ts
export class ScheduleOptimizerService {
  async generateOptimalSchedule(input: {
    tasks: Task[];
    availability: AvailabilityWindow[];
    preferences: SchedulingPreferences;
    existingSchedule?: ScheduleBlock[];
  }): Promise<OptimizedSchedule> {
    
    // Step 1: Preprocess and analyze
    const analysis = await this.analyzeSchedulingContext(input);
    
    // Step 2: Generate multiple schedule options
    const scheduleOptions = await this.generateScheduleVariants(
      input,
      analysis
    );
    
    // Step 3: Use Gemini to evaluate and optimize
    const optimized = await this.gemini.optimizeSchedule({
      options: scheduleOptions,
      criteria: this.buildOptimizationCriteria(input.preferences),
      context: analysis
    });
    
    // Step 4: Validate and adjust
    return this.validateAndAdjustSchedule(optimized, input);
  }

  private async analyzeSchedulingContext(
    input: SchedulingInput
  ): Promise<SchedulingAnalysis> {
    return {
      taskComplexity: this.analyzeTaskComplexity(input.tasks),
      timeConstraints: this.analyzeTimeConstraints(input.availability),
      workloadDistribution: this.analyzeWorkloadDistribution(input.tasks),
      deadlinePressure: this.analyzeDeadlinePressure(input.tasks),
      userPatterns: await this.analyzeUserPatterns(input.preferences)
    };
  }

  private buildOptimizationCriteria(
    preferences: SchedulingPreferences
  ): OptimizationCriteria {
    return {
      prioritizeDeadlines: preferences.deadlineFocus,
      balanceWorkload: preferences.workloadBalance,
      respectEnergyLevels: preferences.energyAware,
      minimizeContext: preferences.minimizeContextSwitching,
      allowFlexibility: preferences.flexibilityTolerance,
      bufferTime: preferences.bufferTimePercentage
    };
  }
}
```

### 4.2 Advanced Data Processing Pipeline

```typescript
// server/src/services/dataProcessor.ts
export class DataProcessorService {
  async processOnboardingData(data: {
    scrapedData: ExtractedData[];
    calendarData: CalendarData;
    manualTasks: Task[];
    preferences: UserPreferences;
  }): Promise<ProcessedOnboardingData> {
    
    // Step 1: Consolidate all data sources
    const consolidatedTasks = await this.consolidateTaskData(data);
    
    // Step 2: Detect conflicts and duplicates
    const deduplicatedTasks = await this.deduplicateAndResolveConflicts(
      consolidatedTasks
    );
    
    // Step 3: AI-powered task enhancement
    const enhancedTasks = await this.gemini.enhanceTasks({
      tasks: deduplicatedTasks,
      context: data.preferences,
      calendarContext: data.calendarData
    });
    
    // Step 4: Generate initial schedule
    const initialSchedule = await this.scheduleOptimizer.generateOptimalSchedule({
      tasks: enhancedTasks,
      availability: data.calendarData.availability,
      preferences: data.preferences
    });
    
    return {
      tasks: enhancedTasks,
      schedule: initialSchedule,
      insights: await this.generateOnboardingInsights(data),
      recommendations: await this.generateRecommendations(data)
    };
  }

  private async consolidateTaskData(
    data: OnboardingData
  ): Promise<ConsolidatedTask[]> {
    const allTasks: ConsolidatedTask[] = [];
    
    // Process scraped data
    data.scrapedData.forEach(scraped => {
      scraped.events.forEach(event => {
        allTasks.push({
          ...event,
          source: 'scraped',
          sourceUrl: scraped.metadata.url,
          confidence: event.confidence
        });
      });
    });
    
    // Process calendar data
    data.calendarData.events.forEach(event => {
      if (this.isAcademicEvent(event)) {
        allTasks.push({
          ...this.convertCalendarEventToTask(event),
          source: 'calendar',
          confidence: 1.0
        });
      }
    });
    
    // Process manual tasks
    data.manualTasks.forEach(task => {
      allTasks.push({
        ...task,
        source: 'manual',
        confidence: 1.0
      });
    });
    
    return allTasks;
  }
}
```

## Phase 5: Security & Performance Considerations

### 5.1 Security Implementation

```typescript
// server/src/middleware/scrapingAuth.ts
export const scrapingAuthMiddleware = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  // Validate URL safety
  const url = req.body.url;
  if (!isValidUrl(url) || isBlacklistedDomain(url)) {
    return res.status(400).json({ error: 'Invalid or prohibited URL' });
  }
  
  // Rate limiting for scraping requests
  const rateLimitKey = `scraping:${req.user.id}`;
  const requestCount = await redis.incr(rateLimitKey);
  
  if (requestCount === 1) {
    await redis.expire(rateLimitKey, 3600); // 1 hour window
  }
  
  if (requestCount > 10) { // 10 requests per hour
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }
  
  next();
};

// URL validation and safety checks
function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

function isBlacklistedDomain(url: string): boolean {
  const blacklist = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    // Add internal network ranges
  ];
  
  const domain = new URL(url).hostname;
  return blacklist.some(blocked => domain.includes(blocked));
}
```

### 5.2 Performance Optimization

```typescript
// server/src/services/cacheService.ts
export class CacheService {
  private redis: Redis;
  
  async cacheScrapingResult(
    url: string,
    data: ExtractedData,
    ttl: number = 3600
  ): Promise<void> {
    const key = this.generateScrapingKey(url);
    await this.redis.setex(key, ttl, JSON.stringify(data));
  }
  
  async getCachedScrapingResult(url: string): Promise<ExtractedData | null> {
    const key = this.generateScrapingKey(url);
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }
  
  async cacheScheduleOptimization(
    userId: string,
    input: SchedulingInput,
    result: OptimizedSchedule
  ): Promise<void> {
    const key = this.generateScheduleKey(userId, input);
    await this.redis.setex(key, 1800, JSON.stringify(result)); // 30 min cache
  }
  
  private generateScrapingKey(url: string): string {
    const hash = crypto.createHash('sha256').update(url).digest('hex');
    return `scraping:${hash}`;
  }
}
```

## Phase 6: Implementation Timeline

### Week 1-2: Foundation
- Set up Gemini API integration
- Create basic web scraping service
- Implement universal data extraction patterns

### Week 3-4: Core Scraping
- Build advanced scraping capabilities
- Implement AI-powered data extraction
- Create website analysis engine

### Week 5-6: Onboarding Enhancement
- Redesign onboarding flow
- Implement URL processing
- Build data preview and editing interfaces

### Week 7-8: Schedule Optimization
- Implement Gemini-powered schedule optimization
- Build advanced scheduling algorithms
- Create schedule insights and analytics

### Week 9-10: Integration & Testing
- Integrate all components
- Implement security measures
- Performance optimization and testing

### Week 11-12: UI/UX Polish
- Enhance user interfaces
- Add advanced visualizations
- User testing and refinement

This comprehensive plan transforms PulsePlan into a powerful, AI-driven schedule management platform that can extract and optimize data from any academic website, providing users with unprecedented automation and intelligence in their academic planning. 