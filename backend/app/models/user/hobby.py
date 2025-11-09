"""
Hobby Models
Pydantic models for hobby parsing and storage
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, validator


class DurationRange(BaseModel):
    """Duration range for flexible hobby scheduling"""
    min: int = Field(ge=5, le=480, description="Minimum duration in minutes")
    max: int = Field(ge=5, le=480, description="Maximum duration in minutes")

    @validator('max')
    def validate_max_greater_than_min(cls, v, values):
        if 'min' in values and v < values['min']:
            raise ValueError('max must be greater than or equal to min')
        return v


class SpecificTime(BaseModel):
    """Specific time window for precise scheduling"""
    start: str = Field(
        description="Start time in HH:MM format (24-hour)",
        pattern=r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    )
    end: str = Field(
        description="End time in HH:MM format (24-hour)",
        pattern=r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    )


class HobbyParseRequest(BaseModel):
    """Request to parse hobby description from natural language"""
    description: str = Field(
        min_length=5,
        max_length=1000,
        description="Natural language description of the hobby"
    )


class ParsedHobby(BaseModel):
    """Structured hobby data extracted from natural language"""
    name: str = Field(description="Hobby name (e.g., 'Gym', 'Piano Practice')")
    preferred_time: Literal['morning', 'afternoon', 'evening', 'night', 'any'] = Field(
        description="Preferred time of day"
    )
    specific_time: Optional[SpecificTime] = Field(
        None,
        description="Specific time window if user mentions exact times (e.g., '8 AM')"
    )
    days: List[Literal['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']] = Field(
        default_factory=lambda: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        description="Days of the week for this hobby"
    )
    duration: DurationRange = Field(
        description="Duration range in minutes"
    )
    flexibility: Literal['low', 'medium', 'high'] = Field(
        default='medium',
        description="Scheduling flexibility (low=strict timing, high=very flexible)"
    )
    notes: str = Field(
        default='',
        max_length=500,
        description="Additional context or preferences"
    )
    icon: Literal['Music', 'Camera', 'Book', 'Gamepad2', 'Palette', 'Target', 'MountainSnow', 'Heart', 'Bike', 'Dumbbell', 'Mountain'] = Field(
        default='Target',
        description="Icon representing the hobby"
    )

    @validator('days')
    def validate_days_not_empty(cls, v):
        if not v:
            raise ValueError('At least one day must be selected')
        return v


class HobbyParseResponse(BaseModel):
    """Response from hobby parsing endpoint"""
    success: bool = Field(description="Whether parsing was successful")
    hobby: Optional[ParsedHobby] = Field(
        None,
        description="Parsed hobby data if successful"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if parsing failed"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the parsing"
    )
