"""
Hobby Parser Service
Uses LLM to parse natural language hobby descriptions into structured data
"""
import logging
from typing import Optional
from openai import AsyncOpenAI

from app.config.core.settings import get_settings
from app.models.user.hobby import ParsedHobby, HobbyParseRequest, HobbyParseResponse

logger = logging.getLogger(__name__)


class HobbyParserService:
    """Service for parsing hobby descriptions using LLM with structured output"""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)

    async def parse_hobby_description(
        self,
        request: HobbyParseRequest
    ) -> HobbyParseResponse:
        """
        Parse natural language hobby description into structured data

        Args:
            request: Hobby parse request with description

        Returns:
            HobbyParseResponse with parsed hobby data or error
        """
        try:
            # Use structured output with JSON mode
            completion = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": request.description
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for more consistent parsing
            )

            # Extract and parse JSON response
            response_text = completion.choices[0].message.content
            if not response_text:
                return HobbyParseResponse(
                    success=False,
                    error="Empty response from LLM",
                    confidence=0.0
                )

            # Parse JSON and validate with Pydantic
            import json
            response_data = json.loads(response_text)
            parsed_hobby = ParsedHobby(**response_data)

            # Calculate confidence based on finish_reason
            confidence = 1.0 if completion.choices[0].finish_reason == "stop" else 0.7

            return HobbyParseResponse(
                success=True,
                hobby=parsed_hobby,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Error parsing hobby description: {str(e)}", exc_info=True)
            return HobbyParseResponse(
                success=False,
                error=f"Failed to parse hobby: {str(e)}",
                confidence=0.0
            )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for hobby parsing"""
        return """You are a hobby extraction assistant for PulsePlan, an academic planning system.

Your task is to parse natural language descriptions of hobbies and extract structured information.

IMPORTANT: You must respond with valid JSON matching this exact schema:
{
  "name": "string",
  "preferred_time": "morning|afternoon|evening|night|any",
  "specific_time": {"start": "HH:MM", "end": "HH:MM"} | null,
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  "duration": {"min": number, "max": number},
  "flexibility": "low|medium|high",
  "notes": "string",
  "icon": "Music|Camera|Book|Gamepad2|Palette|Target|MountainSnow|Heart|Bike|Dumbbell|Mountain"
}

Guidelines:
1. **Name**: Extract a clear, concise hobby name (e.g., "Gym", "Piano Practice", "Photography")
2. **Preferred Time**: Determine when they like to do it:
   - morning: 5am-11am
   - afternoon: 12pm-4pm
   - evening: 5pm-8pm
   - night: 9pm-12am
   - any: no specific preference mentioned
3. **Specific Time**: Extract exact time windows for precise scheduling:
   - If user mentions a specific time (e.g., "8 AM", "at 6:30 PM"), set specific_time
   - Start time: the mentioned time
   - End time: start + duration
   - For "sharp" or "always at X": use a tight 15-minute window (e.g., 08:00-08:15)
   - For "around X" or "usually X": use a 30-45 minute window (e.g., 08:00-08:30)
   - If only general period mentioned (e.g., "in the morning"), leave specific_time as null
   - Use 24-hour format (HH:MM)
4. **Days**: Extract which days they mentioned. Default to all 7 days if not specified.
5. **Duration**: Extract min and max duration in minutes
   - If only one duration mentioned, use it for both min and max
   - If range mentioned (e.g., "45-60 minutes"), extract both
   - If vague (e.g., "about an hour"), use reasonable range like 45-75
6. **Flexibility**: Infer scheduling flexibility:
   - low: strict timing mentioned (e.g., "must be at 6am", "always at noon", "sharp")
   - medium: some preference but flexible (default if unclear)
   - high: very flexible (e.g., "whenever I have time", "anytime works")
7. **Notes**: Capture additional context like:
   - Location preferences (e.g., "outdoor photography")
   - Conditions (e.g., "only if weather is good")
   - Specific constraints (e.g., "not after dinner", "before work")
8. **Icon**: Choose the most appropriate icon:
   - Music: musical activities (guitar, piano, singing, etc.)
   - Camera: photography, videography
   - Book: reading, writing, journaling
   - Gamepad2: gaming, video games
   - Palette: art, drawing, painting
   - MountainSnow: winter sports (skiing, snowboarding, ice skating)
   - Heart: cardio activities (running, jogging, aerobics, dancing, general fitness)
   - Bike: cycling, biking, spinning
   - Dumbbell: strength training, weightlifting, CrossFit, gym workouts
   - Mountain: outdoor activities (hiking, climbing, mountaineering, trail running)
   - Target: general sports, yoga, other activities (default)

Examples:

Input: "I like to go to the gym in the morning, Monday-Friday, usually 45-60 minutes"
Output JSON:
{
  "name": "Gym",
  "preferred_time": "morning",
  "specific_time": null,
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "duration": {"min": 45, "max": 60},
  "flexibility": "medium",
  "notes": "",
  "icon": "Dumbbell"
}

Input: "I always lift at 8 AM sharp for an hour, Monday to Friday"
Output JSON:
{
  "name": "Gym",
  "preferred_time": "morning",
  "specific_time": {"start": "08:00", "end": "09:00"},
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "duration": {"min": 60, "max": 60},
  "flexibility": "low",
  "notes": "",
  "icon": "Dumbbell"
}

Input: "I play guitar for about an hour in the evening, 3-4 times a week"
Output JSON:
{
  "name": "Guitar Practice",
  "preferred_time": "evening",
  "specific_time": null,
  "days": ["Mon", "Tue", "Wed", "Thu"],
  "duration": {"min": 45, "max": 75},
  "flexibility": "medium",
  "notes": "",
  "icon": "Music"
}

Input: "I enjoy photography on weekends, usually afternoon for 1-2 hours when weather is good"
Output JSON:
{
  "name": "Photography",
  "preferred_time": "afternoon",
  "specific_time": null,
  "days": ["Sat", "Sun"],
  "duration": {"min": 60, "max": 120},
  "flexibility": "high",
  "notes": "Outdoor photography, weather dependent",
  "icon": "Camera"
}

Input: "I run around 6:30 AM every weekday for 30 minutes"
Output JSON:
{
  "name": "Running",
  "preferred_time": "morning",
  "specific_time": {"start": "06:30", "end": "07:00"},
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "duration": {"min": 30, "max": 30},
  "flexibility": "medium",
  "notes": "",
  "icon": "Heart"
}

Be intelligent about inferring information while staying faithful to what the user said. Always respond with valid JSON only.
"""


# Singleton instance
_hobby_parser_service: Optional[HobbyParserService] = None


def get_hobby_parser_service() -> HobbyParserService:
    """Get or create the hobby parser service singleton"""
    global _hobby_parser_service
    if _hobby_parser_service is None:
        _hobby_parser_service = HobbyParserService()
    return _hobby_parser_service
