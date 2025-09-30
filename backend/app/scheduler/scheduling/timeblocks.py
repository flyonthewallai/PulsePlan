"""
Unified timeblock representation for calendar parity.

Provides a standardized timeblock format that ensures consistency
between internal scheduler blocks and external calendar systems.
"""

import logging
from typing import List, Dict, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

from ..core.domain import ScheduleBlock, Task, BusyEvent
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class BlockType(Enum):
    """Types of unified time blocks."""
    SCHEDULED_TASK = "scheduled_task"    # Internal scheduled task
    BUSY_EVENT = "busy_event"           # External calendar event
    BREAK = "break"                     # Break/buffer time
    TRAVEL = "travel"                   # Travel/transition time
    BLOCKED = "blocked"                 # Unavailable time


class BlockSource(Enum):
    """Source of time blocks."""
    PULSE_SCHEDULER = "pulse_scheduler"  # Internal scheduler
    GOOGLE_CALENDAR = "google_calendar"  # Google Calendar
    OUTLOOK_CALENDAR = "outlook_calendar" # Microsoft Outlook
    APPLE_CALENDAR = "apple_calendar"    # Apple Calendar
    CANVAS_LMS = "canvas_lms"           # Canvas assignments
    MANUAL = "manual"                   # User-created


class SyncStatus(Enum):
    """Synchronization status with external calendars."""
    SYNCED = "synced"                   # Successfully synchronized
    PENDING = "pending"                 # Pending synchronization
    FAILED = "failed"                   # Synchronization failed
    CONFLICTED = "conflicted"           # Has conflicts with external
    DISABLED = "disabled"               # Sync disabled for this block


@dataclass
class UnifiedTimeBlock:
    """
    Unified representation of time blocks across all systems.

    This provides a standard format that can be used internally by the
    scheduler and synchronized with external calendar systems.
    """

    # Time and duration (required fields first)
    start: datetime
    end: datetime
    title: str

    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    external_id: Optional[str] = None              # ID in external system
    parent_task_id: Optional[str] = None           # Associated task ID

    # Time metadata
    timezone: str = "UTC"
    all_day: bool = False

    # Content and metadata
    description: Optional[str] = None
    location: Optional[str] = None
    block_type: BlockType = BlockType.SCHEDULED_TASK
    source: BlockSource = BlockSource.PULSE_SCHEDULER

    # Calendar integration
    calendar_id: Optional[str] = None              # External calendar ID
    sync_status: SyncStatus = SyncStatus.PENDING
    last_sync: Optional[datetime] = None
    sync_errors: List[str] = field(default_factory=list)

    # Scheduling properties
    priority: int = 1                              # 1-5 priority scale
    color: Optional[str] = None                    # Display color
    tags: List[str] = field(default_factory=list)
    locked: bool = False                           # Prevent modifications
    flexible: bool = False                         # Can be rescheduled

    # Collaboration and sharing
    attendees: List[str] = field(default_factory=list)
    organizer: Optional[str] = None
    visibility: str = "default"                    # public, private, default

    # Tracking
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())
    version: int = 1                               # For conflict resolution

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_minutes(self) -> int:
        """Get block duration in minutes."""
        return int((self.end - self.start).total_seconds() / 60)

    @property
    def is_past(self) -> bool:
        """Check if block is in the past."""
        tz_manager = get_timezone_manager()
        now = tz_manager.ensure_timezone_aware(datetime.now())
        block_end = tz_manager.ensure_timezone_aware(self.end)
        return block_end < now

    @property
    def is_current(self) -> bool:
        """Check if block is currently active."""
        tz_manager = get_timezone_manager()
        now = tz_manager.ensure_timezone_aware(datetime.now())
        block_start = tz_manager.ensure_timezone_aware(self.start)
        block_end = tz_manager.ensure_timezone_aware(self.end)
        return block_start <= now <= block_end

    @property
    def is_future(self) -> bool:
        """Check if block is in the future."""
        tz_manager = get_timezone_manager()
        now = tz_manager.ensure_timezone_aware(datetime.now())
        block_start = tz_manager.ensure_timezone_aware(self.start)
        return block_start > now

    def overlaps_with(self, other: 'UnifiedTimeBlock') -> bool:
        """Check if this block overlaps with another block."""
        tz_manager = get_timezone_manager()

        # Normalize timezones for comparison
        self_start, other_start = tz_manager.normalize_datetime_comparison(
            self.start, other.start
        )
        self_end, other_end = tz_manager.normalize_datetime_comparison(
            self.end, other.end
        )

        return (self_start < other_end) and (other_start < self_end)

    def gap_to(self, other: 'UnifiedTimeBlock') -> Optional[timedelta]:
        """Calculate gap between this block and another block."""
        if self.overlaps_with(other):
            return timedelta(0)  # No gap if overlapping

        tz_manager = get_timezone_manager()
        self_end, other_start = tz_manager.normalize_datetime_comparison(
            self.end, other.start
        )

        if self_end <= other_start:
            return other_start - self_end
        else:
            # Other block comes first
            other_end, self_start = tz_manager.normalize_datetime_comparison(
                other.end, self.start
            )
            return self_start - other_end

    def can_merge_with(self, other: 'UnifiedTimeBlock') -> bool:
        """Check if this block can be merged with another block."""
        # Must be same task and adjacent or overlapping
        if (self.parent_task_id != other.parent_task_id or
            self.parent_task_id is None or
            other.parent_task_id is None):
            return False

        # Must be same type and source
        if self.block_type != other.block_type or self.source != other.source:
            return False

        # Check if adjacent or overlapping (within 30 minutes)
        gap = self.gap_to(other)
        return gap is not None and gap <= timedelta(minutes=30)

    def merge_with(self, other: 'UnifiedTimeBlock') -> 'UnifiedTimeBlock':
        """Merge this block with another block."""
        if not self.can_merge_with(other):
            raise ValueError("Blocks cannot be merged")

        tz_manager = get_timezone_manager()

        # Determine combined time range
        self_start, other_start = tz_manager.normalize_datetime_comparison(
            self.start, other.start
        )
        self_end, other_end = tz_manager.normalize_datetime_comparison(
            self.end, other.end
        )

        merged_start = min(self_start, other_start)
        merged_end = max(self_end, other_end)

        # Create merged block (prefer this block's properties)
        merged = UnifiedTimeBlock(
            id=self.id,  # Keep this block's ID
            external_id=self.external_id,
            parent_task_id=self.parent_task_id,
            start=merged_start.replace(tzinfo=self.start.tzinfo),
            end=merged_end.replace(tzinfo=self.end.tzinfo),
            timezone=self.timezone,
            title=self.title,
            description=self.description,
            location=self.location,
            block_type=self.block_type,
            source=self.source,
            calendar_id=self.calendar_id,
            sync_status=SyncStatus.PENDING,  # Need to re-sync merged block
            priority=max(self.priority, other.priority),
            color=self.color,
            tags=sorted(list(set(self.tags + other.tags))),
            locked=self.locked or other.locked,
            flexible=self.flexible and other.flexible,
            attendees=sorted(list(set(self.attendees + other.attendees))),
            organizer=self.organizer,
            visibility=self.visibility,
            updated_at=get_timezone_manager().ensure_timezone_aware(datetime.now()),
            version=max(self.version, other.version) + 1,
            metadata={**other.metadata, **self.metadata}  # This block's metadata takes priority
        )

        return merged

    def split_at(self, split_time: datetime) -> Tuple['UnifiedTimeBlock', 'UnifiedTimeBlock']:
        """Split block at specified time."""
        tz_manager = get_timezone_manager()
        split_time_aware = tz_manager.ensure_timezone_aware(split_time)
        start_aware = tz_manager.ensure_timezone_aware(self.start)
        end_aware = tz_manager.ensure_timezone_aware(self.end)

        if split_time_aware <= start_aware or split_time_aware >= end_aware:
            raise ValueError("Split time must be within block duration")

        # Create first part
        first_block = UnifiedTimeBlock(
            id=str(uuid.uuid4()),
            external_id=None,  # New block needs new external ID
            parent_task_id=self.parent_task_id,
            start=self.start,
            end=split_time_aware.replace(tzinfo=self.end.tzinfo),
            timezone=self.timezone,
            title=f"{self.title} (Part 1)",
            description=self.description,
            location=self.location,
            block_type=self.block_type,
            source=self.source,
            sync_status=SyncStatus.PENDING,
            priority=self.priority,
            color=self.color,
            tags=self.tags.copy(),
            locked=self.locked,
            flexible=self.flexible,
            attendees=self.attendees.copy(),
            organizer=self.organizer,
            visibility=self.visibility,
            version=1,
            metadata=self.metadata.copy()
        )

        # Create second part
        second_block = UnifiedTimeBlock(
            id=str(uuid.uuid4()),
            external_id=None,  # New block needs new external ID
            parent_task_id=self.parent_task_id,
            start=split_time_aware.replace(tzinfo=self.start.tzinfo),
            end=self.end,
            timezone=self.timezone,
            title=f"{self.title} (Part 2)",
            description=self.description,
            location=self.location,
            block_type=self.block_type,
            source=self.source,
            sync_status=SyncStatus.PENDING,
            priority=self.priority,
            color=self.color,
            tags=self.tags.copy(),
            locked=self.locked,
            flexible=self.flexible,
            attendees=self.attendees.copy(),
            organizer=self.organizer,
            visibility=self.visibility,
            version=1,
            metadata=self.metadata.copy()
        )

        return first_block, second_block

    def to_calendar_event(self, calendar_format: str = "google") -> Dict[str, Any]:
        """Convert to external calendar event format."""
        tz_manager = get_timezone_manager()

        # Convert to timezone-aware format
        start_aware = tz_manager.ensure_timezone_aware(self.start)
        end_aware = tz_manager.ensure_timezone_aware(self.end)

        if calendar_format.lower() == "google":
            return {
                "id": self.external_id,
                "summary": self.title,
                "description": self.description or "",
                "location": self.location or "",
                "start": {
                    "dateTime": start_aware.isoformat(),
                    "timeZone": self.timezone
                },
                "end": {
                    "dateTime": end_aware.isoformat(),
                    "timeZone": self.timezone
                },
                "attendees": [{"email": email} for email in self.attendees],
                "organizer": {"email": self.organizer} if self.organizer else None,
                "visibility": self.visibility,
                "colorId": self.color,
                "source": {
                    "title": "PulsePlan",
                    "url": f"https://pulseplan.ai/tasks/{self.parent_task_id}"
                },
                "extendedProperties": {
                    "private": {
                        "pulseplan_block_id": self.id,
                        "pulseplan_task_id": self.parent_task_id or "",
                        "pulseplan_priority": str(self.priority),
                        "pulseplan_flexible": str(self.flexible),
                        "pulseplan_tags": ",".join(self.tags)
                    }
                }
            }

        elif calendar_format.lower() == "outlook":
            return {
                "id": self.external_id,
                "subject": self.title,
                "body": {
                    "contentType": "text",
                    "content": self.description or ""
                },
                "location": {
                    "displayName": self.location or ""
                },
                "start": {
                    "dateTime": start_aware.isoformat(),
                    "timeZone": self.timezone
                },
                "end": {
                    "dateTime": end_aware.isoformat(),
                    "timeZone": self.timezone
                },
                "attendees": [
                    {"emailAddress": {"address": email}}
                    for email in self.attendees
                ],
                "organizer": {
                    "emailAddress": {"address": self.organizer}
                } if self.organizer else None,
                "sensitivity": "normal" if self.visibility == "default" else self.visibility,
                "categories": self.tags,
                "singleValueExtendedProperties": [
                    {"id": "String {66f5a359-4659-4830-9070-00047ec6ac6e} Name pulseplan_block_id",
                     "value": self.id},
                    {"id": "String {66f5a359-4659-4830-9070-00047ec6ac6e} Name pulseplan_task_id",
                     "value": self.parent_task_id or ""},
                    {"id": "String {66f5a359-4659-4830-9070-00047ec6ac6e} Name pulseplan_priority",
                     "value": str(self.priority)},
                ]
            }

        else:
            raise ValueError(f"Unsupported calendar format: {calendar_format}")

    def to_schedule_block(self) -> ScheduleBlock:
        """Convert to internal ScheduleBlock format."""
        return ScheduleBlock(
            task_id=self.parent_task_id or self.id,
            start=self.start,
            end=self.end,
            utility_score=float(self.priority),
            estimated_completion_probability=0.8,  # Default probability
            penalties_applied=self.metadata.get("penalties", {}),
            alternatives=[]
        )

    def to_busy_event(self) -> BusyEvent:
        """Convert to BusyEvent format."""
        return BusyEvent(
            id=self.external_id or self.id,
            source=self.source.value,
            start=self.start,
            end=self.end,
            title=self.title,
            hard=not self.flexible,
            location=self.location,
            attendees=self.attendees
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "parent_task_id": self.parent_task_id,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "timezone": self.timezone,
            "all_day": self.all_day,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "block_type": self.block_type.value,
            "source": self.source.value,
            "calendar_id": self.calendar_id,
            "sync_status": self.sync_status.value,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_errors": self.sync_errors,
            "priority": self.priority,
            "color": self.color,
            "tags": self.tags,
            "locked": self.locked,
            "flexible": self.flexible,
            "attendees": self.attendees,
            "organizer": self.organizer,
            "visibility": self.visibility,
            "duration_minutes": self.duration_minutes,
            "is_past": self.is_past,
            "is_current": self.is_current,
            "is_future": self.is_future,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata
        }

    @classmethod
    def from_schedule_block(
        cls,
        block: ScheduleBlock,
        task: Optional[Task] = None
    ) -> 'UnifiedTimeBlock':
        """Create UnifiedTimeBlock from ScheduleBlock."""
        return cls(
            id=str(uuid.uuid4()),
            parent_task_id=block.task_id,
            start=block.start,
            end=block.end,
            title=task.title if task else f"Task {block.task_id}",
            description=task.description if task else None,
            block_type=BlockType.SCHEDULED_TASK,
            source=BlockSource.PULSE_SCHEDULER,
            priority=int(block.utility_score) if block.utility_score else 3,
            flexible=True,  # Scheduled tasks are flexible by default
            metadata={
                "utility_score": block.utility_score,
                "completion_probability": block.estimated_completion_probability,
                "penalties": block.penalties_applied
            }
        )

    @classmethod
    def from_busy_event(cls, event: BusyEvent) -> 'UnifiedTimeBlock':
        """Create UnifiedTimeBlock from BusyEvent."""
        # Map source to appropriate enum
        source_map = {
            "google": BlockSource.GOOGLE_CALENDAR,
            "microsoft": BlockSource.OUTLOOK_CALENDAR,
            "outlook": BlockSource.OUTLOOK_CALENDAR,
            "canvas": BlockSource.CANVAS_LMS,
            "manual": BlockSource.MANUAL
        }

        source = source_map.get(event.source.lower(), BlockSource.GOOGLE_CALENDAR)

        return cls(
            id=str(uuid.uuid4()),
            external_id=event.id,
            start=event.start,
            end=event.end,
            title=event.title,
            location=event.location,
            block_type=BlockType.BUSY_EVENT,
            source=source,
            sync_status=SyncStatus.SYNCED,
            locked=event.hard,
            flexible=not event.hard,
            attendees=event.attendees or [],
            metadata={
                "original_source": event.source
            }
        )

    @classmethod
    def from_calendar_event(
        cls,
        event: Dict[str, Any],
        calendar_format: str = "google"
    ) -> 'UnifiedTimeBlock':
        """Create UnifiedTimeBlock from external calendar event."""
        if calendar_format.lower() == "google":
            # Extract PulsePlan metadata if present
            extended_props = event.get("extendedProperties", {}).get("private", {})
            task_id = extended_props.get("pulseplan_task_id")
            priority = int(extended_props.get("pulseplan_priority", "3"))
            flexible = extended_props.get("pulseplan_flexible", "true").lower() == "true"
            tags = [tag.strip() for tag in extended_props.get("pulseplan_tags", "").split(",") if tag.strip()]

            return cls(
                id=extended_props.get("pulseplan_block_id", str(uuid.uuid4())),
                external_id=event.get("id"),
                parent_task_id=task_id if task_id else None,
                start=datetime.fromisoformat(event["start"]["dateTime"].replace('Z', '+00:00')),
                end=datetime.fromisoformat(event["end"]["dateTime"].replace('Z', '+00:00')),
                timezone=event["start"].get("timeZone", "UTC"),
                title=event.get("summary", "Untitled Event"),
                description=event.get("description"),
                location=event.get("location"),
                block_type=BlockType.SCHEDULED_TASK if task_id else BlockType.BUSY_EVENT,
                source=BlockSource.GOOGLE_CALENDAR,
                sync_status=SyncStatus.SYNCED,
                priority=priority,
                color=event.get("colorId"),
                tags=tags,
                flexible=flexible,
                attendees=[a.get("email", "") for a in event.get("attendees", [])],
                organizer=event.get("organizer", {}).get("email"),
                visibility=event.get("visibility", "default")
            )

        elif calendar_format.lower() == "outlook":
            # Extract PulsePlan metadata from extended properties
            ext_props = event.get("singleValueExtendedProperties", [])
            ext_props_dict = {
                prop["id"].split(" Name ")[-1]: prop["value"]
                for prop in ext_props
                if " Name " in prop["id"]
            }

            task_id = ext_props_dict.get("pulseplan_task_id")
            priority = int(ext_props_dict.get("pulseplan_priority", "3"))

            return cls(
                id=ext_props_dict.get("pulseplan_block_id", str(uuid.uuid4())),
                external_id=event.get("id"),
                parent_task_id=task_id if task_id else None,
                start=datetime.fromisoformat(event["start"]["dateTime"].replace('Z', '+00:00')),
                end=datetime.fromisoformat(event["end"]["dateTime"].replace('Z', '+00:00')),
                timezone=event["start"].get("timeZone", "UTC"),
                title=event.get("subject", "Untitled Event"),
                description=event.get("body", {}).get("content"),
                location=event.get("location", {}).get("displayName"),
                block_type=BlockType.SCHEDULED_TASK if task_id else BlockType.BUSY_EVENT,
                source=BlockSource.OUTLOOK_CALENDAR,
                sync_status=SyncStatus.SYNCED,
                priority=priority,
                tags=event.get("categories", []),
                attendees=[a.get("emailAddress", {}).get("address", "") for a in event.get("attendees", [])],
                organizer=event.get("organizer", {}).get("emailAddress", {}).get("address"),
                visibility=event.get("sensitivity", "default")
            )

        else:
            raise ValueError(f"Unsupported calendar format: {calendar_format}")


class TimeBlockManager:
    """
    Manager for unified timeblock operations and calendar synchronization.

    Handles conversion between different block formats and manages
    synchronization with external calendar systems.
    """

    def __init__(self):
        """Initialize timeblock manager."""
        self.tz_manager = get_timezone_manager()

    def merge_overlapping_blocks(
        self,
        blocks: List[UnifiedTimeBlock]
    ) -> List[UnifiedTimeBlock]:
        """Merge overlapping blocks from the same task."""
        if not blocks:
            return blocks

        # Group by task ID
        task_blocks = {}
        other_blocks = []

        for block in blocks:
            if block.parent_task_id and block.block_type == BlockType.SCHEDULED_TASK:
                if block.parent_task_id not in task_blocks:
                    task_blocks[block.parent_task_id] = []
                task_blocks[block.parent_task_id].append(block)
            else:
                other_blocks.append(block)

        # Merge blocks for each task
        merged_blocks = other_blocks.copy()

        for task_id, task_block_list in task_blocks.items():
            task_block_list.sort(key=lambda b: b.start)

            merged_task_blocks = []
            current_block = task_block_list[0]

            for next_block in task_block_list[1:]:
                if current_block.can_merge_with(next_block):
                    current_block = current_block.merge_with(next_block)
                else:
                    merged_task_blocks.append(current_block)
                    current_block = next_block

            merged_task_blocks.append(current_block)
            merged_blocks.extend(merged_task_blocks)

        # Sort final result by start time
        merged_blocks.sort(key=lambda b: b.start)
        return merged_blocks

    def detect_conflicts(
        self,
        blocks: List[UnifiedTimeBlock]
    ) -> List[Tuple[UnifiedTimeBlock, UnifiedTimeBlock]]:
        """Detect conflicting blocks."""
        conflicts = []

        # Sort blocks by start time
        sorted_blocks = sorted(blocks, key=lambda b: b.start)

        for i in range(len(sorted_blocks)):
            for j in range(i + 1, len(sorted_blocks)):
                block1, block2 = sorted_blocks[i], sorted_blocks[j]

                if block1.overlaps_with(block2):
                    # Skip conflicts between blocks from same task
                    if (block1.parent_task_id and
                        block1.parent_task_id == block2.parent_task_id):
                        continue

                    conflicts.append((block1, block2))

        return conflicts

    def resolve_conflicts(
        self,
        blocks: List[UnifiedTimeBlock],
        resolution_strategy: str = "priority"
    ) -> List[UnifiedTimeBlock]:
        """Resolve conflicts between blocks using specified strategy."""
        conflicts = self.detect_conflicts(blocks)

        if not conflicts:
            return blocks

        resolved_blocks = blocks.copy()
        blocks_to_remove = set()

        for block1, block2 in conflicts:
            if block1.id in blocks_to_remove or block2.id in blocks_to_remove:
                continue

            if resolution_strategy == "priority":
                # Keep higher priority block
                if block1.priority > block2.priority:
                    blocks_to_remove.add(block2.id)
                elif block2.priority > block1.priority:
                    blocks_to_remove.add(block1.id)
                elif block1.locked and not block2.locked:
                    blocks_to_remove.add(block2.id)
                elif block2.locked and not block1.locked:
                    blocks_to_remove.add(block1.id)
                else:
                    # Keep earlier block
                    if block1.start <= block2.start:
                        blocks_to_remove.add(block2.id)
                    else:
                        blocks_to_remove.add(block1.id)

            elif resolution_strategy == "locked":
                # Locked blocks always win
                if block1.locked and not block2.locked:
                    blocks_to_remove.add(block2.id)
                elif block2.locked and not block1.locked:
                    blocks_to_remove.add(block1.id)
                else:
                    # Fall back to priority
                    if block1.priority >= block2.priority:
                        blocks_to_remove.add(block2.id)
                    else:
                        blocks_to_remove.add(block1.id)

        # Remove conflicted blocks
        resolved_blocks = [
            block for block in resolved_blocks
            if block.id not in blocks_to_remove
        ]

        return resolved_blocks

    def convert_schedule_blocks(
        self,
        schedule_blocks: List[ScheduleBlock],
        tasks: Optional[List[Task]] = None
    ) -> List[UnifiedTimeBlock]:
        """Convert ScheduleBlocks to UnifiedTimeBlocks."""
        task_map = {task.id: task for task in (tasks or [])}

        unified_blocks = []
        for block in schedule_blocks:
            task = task_map.get(block.task_id)
            unified_block = UnifiedTimeBlock.from_schedule_block(block, task)
            unified_blocks.append(unified_block)

        return unified_blocks

    def convert_to_schedule_blocks(
        self,
        unified_blocks: List[UnifiedTimeBlock]
    ) -> List[ScheduleBlock]:
        """Convert UnifiedTimeBlocks to ScheduleBlocks."""
        schedule_blocks = []

        for block in unified_blocks:
            if block.block_type == BlockType.SCHEDULED_TASK and block.parent_task_id:
                schedule_block = block.to_schedule_block()
                schedule_blocks.append(schedule_block)

        return schedule_blocks

    def convert_busy_events(
        self,
        busy_events: List[BusyEvent]
    ) -> List[UnifiedTimeBlock]:
        """Convert BusyEvents to UnifiedTimeBlocks."""
        return [
            UnifiedTimeBlock.from_busy_event(event)
            for event in busy_events
        ]

    def get_sync_summary(
        self,
        blocks: List[UnifiedTimeBlock]
    ) -> Dict[str, Any]:
        """Get synchronization summary for blocks."""
        status_counts = {}
        source_counts = {}
        sync_errors = []

        for block in blocks:
            # Count by sync status
            status = block.sync_status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by source
            source = block.source.value
            source_counts[source] = source_counts.get(source, 0) + 1

            # Collect sync errors
            if block.sync_errors:
                sync_errors.extend([
                    {"block_id": block.id, "error": error}
                    for error in block.sync_errors
                ])

        return {
            "total_blocks": len(blocks),
            "sync_status_counts": status_counts,
            "source_counts": source_counts,
            "sync_errors": sync_errors,
            "conflicts_count": len(self.detect_conflicts(blocks)),
            "last_updated": datetime.now().isoformat()
        }


# Global timeblock manager instance
_timeblock_manager = None

def get_timeblock_manager() -> TimeBlockManager:
    """Get global timeblock manager instance."""
    global _timeblock_manager
    if _timeblock_manager is None:
        _timeblock_manager = TimeBlockManager()
    return _timeblock_manager

