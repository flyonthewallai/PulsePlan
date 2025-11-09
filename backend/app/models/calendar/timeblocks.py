"""
Timeblock models for unified calendar feed
Merges tasks, calendar events, and busy blocks into a single normalized feed
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

TimeblockSource = Literal["task", "calendar", "busy"]
TimeblockProvider = Optional[Literal["google", "outlook", "apple", "pulse"]]


class Timeblock(BaseModel):
    """
    Normalized timeblock representing a scheduled item from any source
    """
    id: str = Field(..., alias="block_id", description="Unique identifier for this block")
    source: TimeblockSource = Field(..., description="Source type: task, calendar, or busy")
    provider: TimeblockProvider = Field(None, description="Provider if from external calendar")
    title: str = Field(..., description="Display title")
    start: str = Field(..., description="Start time as ISO8601 UTC")
    end: str = Field(..., description="End time as ISO8601 UTC")
    is_all_day: bool = Field(False, alias="isAllDay", description="Whether this is an all-day event")
    readonly: bool = Field(True, description="Whether this block can be edited")
    link_id: Optional[str] = Field(None, alias="linkId", description="calendar_links.id if linked")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "source": "task",
                "provider": None,
                "title": "Study for CS 101 midterm",
                "start": "2025-10-03T14:00:00Z",
                "end": "2025-10-03T16:00:00Z",
                "isAllDay": False,
                "readonly": False,
                "linkId": None
            }
        }


class TimeblocksResponse(BaseModel):
    """Response containing list of timeblocks"""
    items: List[Timeblock] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "source": "task",
                        "provider": None,
                        "title": "Study for CS 101 midterm",
                        "start": "2025-10-03T14:00:00Z",
                        "end": "2025-10-03T16:00:00Z",
                        "isAllDay": False,
                        "readonly": False,
                        "linkId": None
                    }
                ]
            }
        }


class TimeblockQueryParams(BaseModel):
    """Query parameters for timeblock fetching"""
    from_iso: str = Field(..., alias="from", description="Start of window (ISO8601)")
    to_iso: str = Field(..., alias="to", description="End of window (ISO8601)")

    class Config:
        populate_by_name = True
