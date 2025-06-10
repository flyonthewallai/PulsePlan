// @ts-ignore - Package will be installed during setup
import { GoogleGenerativeAI } from '@google/generative-ai';
import { 
  GeminiRequest, 
  GeminiResponse, 
  ExtractedEvent, 
  AIExtractedData,
  ConsolidatedTask 
} from '../types/scraping';

export class GeminiService {
  private genAI: GoogleGenerativeAI;
  private textModel: any;
  private visionModel: any;

  constructor() {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error('GEMINI_API_KEY environment variable is required');
    }

    this.genAI = new GoogleGenerativeAI(apiKey);
    this.textModel = this.genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
    this.visionModel = this.genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
  }

  /**
   * Extract schedule data from HTML content and optional screenshot
   */
  async extractScheduleData(request: GeminiRequest): Promise<AIExtractedData> {
    const startTime = Date.now();
    
    try {
      const prompt = this.buildExtractionPrompt(request.extractionType, request.context);
      
      let result;
      
      // Use vision model if screenshot is provided
      if (request.screenshot) {
                 result = await this.visionModel.generateContent([
           prompt,
           { text: `HTML Content:\n${request.html}` },
           {
             inlineData: {
               mimeType: 'image/png',
               data: request.screenshot
             }
           } as any
         ]);
      } else {
        // Use text-only model
        result = await this.textModel.generateContent([
          prompt,
          { text: `HTML Content to analyze:\n${request.html}` }
        ]);
      }

      const responseText = result.response.text();
      const parsedResponse = this.parseExtractionResponse(responseText);
      
      return {
        events: parsedResponse.events,
        metadata: {
          extractionMethod: request.screenshot ? 'ai_vision' : 'ai_text',
          overallConfidence: parsedResponse.confidence,
          processingNotes: parsedResponse.reasoning || []
        }
      };
    } catch (error) {
      console.error('Gemini extraction error:', error);
      return {
        events: [],
        metadata: {
          extractionMethod: 'ai_failed',
          overallConfidence: 0,
          processingNotes: [`Error: ${error instanceof Error ? error.message : 'Unknown error'}`]
        }
      };
    }
  }

  /**
   * Enhance and process extracted tasks with AI
   */
  async enhanceTasks(tasks: ConsolidatedTask[]): Promise<ConsolidatedTask[]> {
    if (tasks.length === 0) return tasks;

    try {
      const prompt = this.buildTaskEnhancementPrompt();
      const taskData = JSON.stringify(tasks, null, 2);

      const result = await this.textModel.generateContent([
        prompt,
        { text: `Tasks to enhance:\n${taskData}` }
      ]);

      const responseText = result.response.text();
      const enhancedTasks = this.parseTaskEnhancementResponse(responseText);
      
      return enhancedTasks.length > 0 ? enhancedTasks : tasks;
    } catch (error) {
      console.error('Task enhancement error:', error);
      return tasks; // Return original tasks if enhancement fails
    }
  }

  /**
   * Analyze website content to determine extraction strategy
   */
  async analyzeWebsiteStructure(html: string, screenshot?: string): Promise<{
    platform: string;
    confidence: number;
    strategy: 'pattern' | 'ai' | 'hybrid';
    reasoning: string[];
  }> {
    try {
      const prompt = `
Analyze this website content and determine:
1. What type of academic platform this is (Canvas, Blackboard, Moodle, university site, etc.)
2. How suitable it is for schedule/assignment data extraction
3. The best extraction strategy (pattern-based, AI-based, or hybrid)
4. Confidence level (0-1) in the analysis

Return a JSON response with this structure:
{
  "platform": "platform_name or 'unknown'",
  "confidence": 0.8,
  "strategy": "ai",
  "reasoning": ["reason1", "reason2"],
  "hasScheduleData": true,
  "extractionDifficulty": "medium"
}
`;

      const parts = [
        prompt,
        { text: `HTML to analyze:\n${html.substring(0, 10000)}` } // Limit HTML size
      ];

             if (screenshot) {
         parts.push({
           inlineData: {
             mimeType: 'image/png',
             data: screenshot
           }
         } as any);
       }

      const result = await (screenshot ? this.visionModel : this.textModel)
        .generateContent(parts);

      const responseText = result.response.text();
      return this.parseAnalysisResponse(responseText);
    } catch (error) {
      console.error('Website analysis error:', error);
      return {
        platform: 'unknown',
        confidence: 0,
        strategy: 'ai',
        reasoning: ['Analysis failed']
      };
    }
  }

  /**
   * Build extraction prompt based on type and context
   */
  private buildExtractionPrompt(extractionType: string, context: string): string {
    // Enhanced prompt for Canvas LMS specifically
    const canvasPrompt = `
You are an expert at extracting assignment and academic data from Canvas LMS websites.

Context: ${context}
Extraction Type: ${extractionType}

CANVAS LMS SPECIFIC INSTRUCTIONS:
You are analyzing a Canvas Learning Management System page. Focus on these HTML patterns and extract assignments systematically:

HTML STRUCTURE PATTERNS TO LOOK FOR:
1. **Module Items**: Look for li class="context_module_item" elements containing assignment titles
2. **Assignment Links**: Text patterns ending with "Assignment" (e.g., "Research Article Assignment")
3. **Quiz Items**: Elements with classes containing "lti-quiz" or "also_assignment"
4. **Todo Lists**: Elements with class "todo-list" containing assignment summaries
5. **Due Date Indicators**: Text containing "Jun 29", "at 11:59pm", or similar date patterns
6. **Point Values**: Text containing "points", "pts", or score indicators

SPECIFIC CANVAS PATTERNS TO EXTRACT:
- Assignment titles that end with "Assignment", "Quiz", "Discussion", "Project"
- Due dates in format "Jun 29 at 11:59pm" or similar
- Point values like "7 points" or "10 pts"
- Course context from page titles or navigation

EXTRACTION STRATEGY:
1. Scan for any text containing "Assignment" followed by course/title information
2. Look for associated due dates within the same HTML element or nearby
3. Extract point values from the same context
4. Use page title for course information if not found in individual items

DATE PARSING RULES:
- "Jun 29" → Convert to 2025-06-29T23:59:00Z (default to end of day)
- "Jun 29 at 11:59pm" → Convert to 2025-06-29T23:59:00Z
- Current context: ${new Date().toISOString()}
- If year is missing, assume current year (2025)

EXAMPLE EXTRACTION FROM YOUR HTML:
If you see text like "Cite Research Articles Assignment...7 points Jun 29 at 11:59pm"
Extract this as:
{
  "title": "Cite Research Articles Assignment",
  "course": "CU SPUR Literature Research Summer 2025",
  "dueDate": "2025-06-29T23:59:00Z",
  "points": 7,
  "type": "assignment",
  "confidence": 0.9
}

CONFIDENCE SCORING:
- 0.9-1.0: Clear assignment title + due date + points
- 0.7-0.8: Assignment title + either due date OR points  
- 0.5-0.6: Assignment title only
- 0.1-0.4: Weak assignment indicators
- 0.0: No academic content found

CRITICAL: Look specifically for text patterns like:
- "What are Research Articles? Assignment"
- "Cite Research Articles Assignment" 
- "Find a Research Article Assignment"
- "Research Data Management Assignment"
These are clear assignment titles that should be extracted with high confidence.

Return ONLY a valid JSON object with this exact structure:
{
  "events": [
    {
      "title": "Assignment Name",
      "description": "Assignment description or details",
      "dueDate": "2024-01-15T23:59:00Z",
      "course": "Course Code - Course Name",
      "priority": "medium",
      "estimatedDuration": 120,
      "type": "assignment",
      "confidence": 0.9,
      "points": 25,
      "status": "not_submitted",
      "sourceElement": "assignment-item or similar"
    }
  ],
  "confidence": 0.85,
  "reasoning": ["Found 3 assignment items with clear due dates", "Extracted from Canvas dashboard view"]
}

CRITICAL: If you find NO assignments, still return the JSON structure with an empty events array and explain why in the reasoning field.
Do not include any text outside the JSON object.
`;

    return canvasPrompt;
  }

  /**
   * Build task enhancement prompt
   */
  private buildTaskEnhancementPrompt(): string {
    return `
You are an AI assistant that enhances academic task data to make it more useful for scheduling.

Analyze the provided tasks and enhance them by:
1. Improving titles to be more descriptive and consistent
2. Estimating realistic completion times based on task type and complexity
3. Assigning appropriate priority levels
4. Adding relevant tags or categories
5. Filling in missing information where reasonable
6. Standardizing course names and formats

Return a JSON array of enhanced tasks with the same structure but improved data:
{
  "enhancedTasks": [
    {
      "title": "Enhanced title",
      "description": "Enhanced description",
      "dueDate": "ISO date",
      "course": "Standardized course name",
      "priority": "low|medium|high",
      "estimatedDuration": 90,
      "type": "assignment",
      "tags": ["category", "topic"],
      "confidence": 0.95
    }
  ]
}

Only enhance existing information, do not create new tasks.
`;
  }

  /**
   * Parse Gemini extraction response
   */
  private parseExtractionResponse(responseText: string): GeminiResponse {
    try {
      // Clean the response text to extract JSON
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in response');
      }

      const parsed = JSON.parse(jsonMatch[0]);
      
      return {
        events: parsed.events || [],
        confidence: parsed.confidence || 0,
        reasoning: parsed.reasoning || [],
        suggestions: parsed.suggestions || []
      };
    } catch (error) {
      console.error('Failed to parse Gemini response:', error);
      return {
        events: [],
        confidence: 0,
        reasoning: ['Failed to parse AI response'],
        suggestions: []
      };
    }
  }

  /**
   * Parse task enhancement response
   */
  private parseTaskEnhancementResponse(responseText: string): ConsolidatedTask[] {
    try {
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in enhancement response');
      }

      const parsed = JSON.parse(jsonMatch[0]);
      return parsed.enhancedTasks || [];
    } catch (error) {
      console.error('Failed to parse task enhancement response:', error);
      return [];
    }
  }

  /**
   * Parse website analysis response
   */
  private parseAnalysisResponse(responseText: string): any {
    try {
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in analysis response');
      }

      return JSON.parse(jsonMatch[0]);
    } catch (error) {
      console.error('Failed to parse analysis response:', error);
      return {
        platform: 'unknown',
        confidence: 0,
        strategy: 'ai',
        reasoning: ['Failed to parse analysis']
      };
    }
  }

  /**
   * Test Gemini API connection
   */
  async testConnection(): Promise<boolean> {
    try {
      const result = await this.textModel.generateContent(['Say "Hello" if you can understand this message.']);
      const response = result.response.text();
      return response.toLowerCase().includes('hello');
    } catch (error) {
      console.error('Gemini connection test failed:', error);
      return false;
    }
  }
} 