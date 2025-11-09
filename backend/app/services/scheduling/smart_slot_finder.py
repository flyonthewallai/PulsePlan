"""
Smart Slot Finder Service

Fast, rule-based single-event scheduling with optional LLM fallback.
Part of PulsePlan's two-tier scheduling architecture.

This service handles:
- Quick scheduling/rescheduling of individual events (≤1 day ahead)
- Conflict detection and resolution
- Heuristic-based optimal slot selection
- LLM fallback for complex scenarios

For bulk scheduling or multi-day optimization (>1 day ahead), use the
main constraint-based scheduler (backend/app/scheduler/).

Author: PulsePlan Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pytz

logger = logging.getLogger(__name__)


@dataclass
class TimeBlock:
    """Represents a time block (event, task, or free slot)."""

    id: str
    title: str
    start_time: datetime
    end_time: datetime
    type: str  # "event", "task", "timeblock", "free"
    readonly: bool = False
    priority: Optional[str] = None

    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def overlaps_with(self, other: 'TimeBlock') -> bool:
        """Check if this block overlaps with another."""
        return (self.start_time < other.end_time and
                self.end_time > other.start_time)


@dataclass
class SlotCandidate:
    """A candidate time slot with scoring metadata."""

    start_time: datetime
    end_time: datetime
    score: float
    reasoning: str
    conflicts: List[TimeBlock]
    method: str  # "exact_match", "heuristic", "llm"


@dataclass
class SchedulingResult:
    """Result of a scheduling operation."""

    success: bool
    chosen_slot: Optional[SlotCandidate]
    message: str
    rationale: str
    method: str  # "rule_based", "heuristic", "llm"
    confidence: float
    alternatives: List[SlotCandidate] = None
    moved_events: List[Dict[str, Any]] = None


class SmartSlotFinder:
    """
    Smart Slot Finder - Fast single-event scheduling service.

    Part of PulsePlan's two-tier scheduling architecture:
    - Tier 1 (this): Fast heuristic scheduling for ≤1 day ahead
    - Tier 2: Constraint-based optimization for >1 day or bulk operations

    Decision Flow:
    1. Check if preferred time is free → Use it (exact match)
    2. If conflict, score nearby alternative slots (heuristic)
    3. If complex (multiple conflicts, shifting needed), use LLM fallback
    4. Validate and return best slot with rationale
    """

    def __init__(self):
        """Initialize the smart slot finder."""
        self.max_shift_minutes = 120  # Max time to shift from preferred time
        self.candidate_window_hours = 6  # Window to search for alternatives

    async def find_optimal_slot(
        self,
        preferred_time: datetime,
        duration_minutes: int,
        user_id: str,
        event_title: str,
        user_timezone: str = "UTC",
        constraints: Optional[Dict[str, Any]] = None
    ) -> SchedulingResult:
        """
        Find the optimal time slot for an event.

        Args:
            preferred_time: User's preferred start time (timezone-aware)
            duration_minutes: Event duration in minutes
            user_id: User identifier
            event_title: Name of event being scheduled
            user_timezone: User's timezone
            constraints: Optional constraints (working hours, preferences, etc.)

        Returns:
            SchedulingResult with chosen slot, rationale, and alternatives

        Example:
            >>> result = await finder.find_optimal_slot(
            ...     preferred_time=datetime(2025, 10, 31, 14, 0, tzinfo=pytz.UTC),
            ...     duration_minutes=60,
            ...     user_id="user123",
            ...     event_title="Bio Study Session"
            ... )
            >>> print(result.message)
            "Scheduled Bio Study Session for Oct 31 at 2:00 PM"
            >>> print(result.rationale)
            "Exact match - preferred time was available"
        """
        try:
            logger.info(
                f"[SmartSlotFinder] Finding slot for '{event_title}' at {preferred_time}, "
                f"duration={duration_minutes}min, user={user_id}"
            )

            # Step 1: Load user's existing schedule
            busy_blocks = await self._load_busy_blocks(user_id, preferred_time)

            # Step 2: Check if preferred time is free (fast path)
            conflict = self._check_conflict(preferred_time, duration_minutes, busy_blocks)

            if not conflict:
                # Exact match - preferred time is free!
                logger.info("[SmartSlotFinder] Exact match - preferred time is free")
                return SchedulingResult(
                    success=True,
                    chosen_slot=SlotCandidate(
                        start_time=preferred_time,
                        end_time=preferred_time + timedelta(minutes=duration_minutes),
                        score=1.0,
                        reasoning="Exact match - preferred time was available",
                        conflicts=[],
                        method="exact_match"
                    ),
                    message=self._format_time(preferred_time, user_timezone),
                    rationale="Exact match - preferred time was available",
                    method="rule_based",
                    confidence=1.0
                )

            # Step 3: Find alternative slots using heuristics
            logger.info(f"[SmartSlotFinder] Conflict detected: {conflict.title}, finding alternatives")

            candidates = await self._find_candidate_slots(
                preferred_time=preferred_time,
                duration_minutes=duration_minutes,
                busy_blocks=busy_blocks,
                constraints=constraints or {},
                user_timezone=user_timezone
            )

            if not candidates:
                # Step 4: LLM fallback for complex scenarios
                logger.info("[SmartSlotFinder] No candidates found, using LLM fallback")
                return await self._llm_fallback_scheduling(
                    preferred_time=preferred_time,
                    duration_minutes=duration_minutes,
                    event_title=event_title,
                    busy_blocks=busy_blocks,
                    constraints=constraints or {},
                    user_timezone=user_timezone
                )

            # Choose best candidate
            best_slot = max(candidates, key=lambda c: c.score)

            logger.info(
                f"[SmartSlotFinder] Found best slot: {best_slot.start_time}, "
                f"score={best_slot.score:.2f}, method={best_slot.method}"
            )

            return SchedulingResult(
                success=True,
                chosen_slot=best_slot,
                message=self._format_time(best_slot.start_time, user_timezone),
                rationale=best_slot.reasoning,
                method="heuristic",
                confidence=best_slot.score,
                alternatives=candidates[1:4] if len(candidates) > 1 else None  # Top 3 alternatives
            )

        except Exception as e:
            logger.error(f"[SmartSlotFinder] Error finding slot: {e}", exc_info=True)
            return SchedulingResult(
                success=False,
                chosen_slot=None,
                message=f"Failed to find available slot: {str(e)}",
                rationale=f"Error: {str(e)}",
                method="error",
                confidence=0.0
            )

    async def _load_busy_blocks(
        self,
        user_id: str,
        around_time: datetime
    ) -> List[TimeBlock]:
        """
        Load user's busy blocks (events, tasks, timeblocks) around a given time.

        Args:
            user_id: User identifier
            around_time: Center time to search around

        Returns:
            List of TimeBlock objects representing busy periods
        """
        from app.database.repositories.calendar_repositories import get_timeblocks_repository

        # Search window: 12 hours before/after preferred time
        start_window = around_time - timedelta(hours=12)
        end_window = around_time + timedelta(hours=12)

        timeblocks_repo = get_timeblocks_repository()

        # Fetch timeblocks from database
        raw_blocks = await timeblocks_repo.get_timeblocks_for_user(
            user_id=user_id,
            start_date=start_window,
            end_date=end_window
        )

        # Convert to TimeBlock objects
        busy_blocks = []
        for block in raw_blocks:
            try:
                start_time = datetime.fromisoformat(block["start_at"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(block["end_at"].replace('Z', '+00:00'))

                busy_blocks.append(TimeBlock(
                    id=block["id"],
                    title=block["title"],
                    start_time=start_time,
                    end_time=end_time,
                    type=block.get("type", "external"),
                    readonly=block.get("readonly", False),
                    priority=block.get("metadata", {}).get("priority")
                ))
            except Exception as e:
                logger.warning(f"[SmartSlotFinder] Failed to parse timeblock {block.get('id')}: {e}")
                continue

        logger.info(f"[SmartSlotFinder] Loaded {len(busy_blocks)} busy blocks for user {user_id}")
        return busy_blocks

    def _check_conflict(
        self,
        start_time: datetime,
        duration_minutes: int,
        busy_blocks: List[TimeBlock]
    ) -> Optional[TimeBlock]:
        """
        Check if a time slot conflicts with existing blocks.

        Args:
            start_time: Proposed start time
            duration_minutes: Event duration
            busy_blocks: List of existing busy blocks

        Returns:
            Conflicting TimeBlock if found, None if slot is free
        """
        proposed_end = start_time + timedelta(minutes=duration_minutes)
        proposed_block = TimeBlock(
            id="proposed",
            title="Proposed Event",
            start_time=start_time,
            end_time=proposed_end,
            type="proposed"
        )

        for block in busy_blocks:
            if proposed_block.overlaps_with(block):
                return block

        return None

    async def _find_candidate_slots(
        self,
        preferred_time: datetime,
        duration_minutes: int,
        busy_blocks: List[TimeBlock],
        constraints: Dict[str, Any],
        user_timezone: str
    ) -> List[SlotCandidate]:
        """
        Find and score candidate time slots near the preferred time.

        Scoring Factors:
        - Proximity to preferred time (closer = higher score)
        - Alignment with user's productivity patterns (constraints)
        - Distance from other study blocks (avoid clustering)
        - Time of day preferences (morning/afternoon/evening)

        Args:
            preferred_time: User's preferred start time
            duration_minutes: Event duration
            busy_blocks: List of existing busy blocks
            constraints: User preferences and constraints
            user_timezone: User's timezone

        Returns:
            List of SlotCandidate objects sorted by score (descending)
        """
        candidates = []

        # Generate time slots to check (every 30 minutes)
        search_start = preferred_time - timedelta(hours=self.candidate_window_hours)
        search_end = preferred_time + timedelta(hours=self.candidate_window_hours)

        current_time = search_start
        while current_time < search_end:
            # Check if slot is free
            conflict = self._check_conflict(current_time, duration_minutes, busy_blocks)

            if not conflict:
                # Score this slot
                score = self._score_slot(
                    slot_time=current_time,
                    preferred_time=preferred_time,
                    duration_minutes=duration_minutes,
                    busy_blocks=busy_blocks,
                    constraints=constraints,
                    user_timezone=user_timezone
                )

                reasoning = self._generate_slot_reasoning(
                    slot_time=current_time,
                    preferred_time=preferred_time,
                    score=score,
                    constraints=constraints
                )

                candidates.append(SlotCandidate(
                    start_time=current_time,
                    end_time=current_time + timedelta(minutes=duration_minutes),
                    score=score,
                    reasoning=reasoning,
                    conflicts=[],
                    method="heuristic"
                ))

            # Move to next slot (30-minute intervals)
            current_time += timedelta(minutes=30)

        # Sort by score (descending)
        candidates.sort(key=lambda c: c.score, reverse=True)

        logger.info(f"[SmartSlotFinder] Found {len(candidates)} candidate slots")
        return candidates

    def _score_slot(
        self,
        slot_time: datetime,
        preferred_time: datetime,
        duration_minutes: int,
        busy_blocks: List[TimeBlock],
        constraints: Dict[str, Any],
        user_timezone: str
    ) -> float:
        """
        Score a time slot based on multiple factors.

        Scoring Formula:
        score = w1 * proximity_score +
                w2 * productivity_score +
                w3 * spacing_score -
                w4 * conflict_penalty

        Args:
            slot_time: Candidate slot start time
            preferred_time: User's preferred time
            duration_minutes: Event duration
            busy_blocks: Existing busy blocks
            constraints: User preferences
            user_timezone: User's timezone

        Returns:
            Score between 0.0 and 1.0 (higher is better)
        """
        # Weights for scoring factors
        w_proximity = 0.4
        w_productivity = 0.3
        w_spacing = 0.2
        w_time_of_day = 0.1

        # Factor 1: Proximity to preferred time (exponential decay)
        time_diff_minutes = abs((slot_time - preferred_time).total_seconds() / 60)
        proximity_score = max(0, 1 - (time_diff_minutes / self.max_shift_minutes))

        # Factor 2: Productivity pattern match
        # (prefer afternoon for study, morning for admin, etc.)
        productivity_score = self._score_productivity_match(
            slot_time, constraints, user_timezone
        )

        # Factor 3: Spacing from other blocks
        # (avoid clustering, prefer gaps between events)
        spacing_score = self._score_spacing(slot_time, duration_minutes, busy_blocks)

        # Factor 4: Time of day preference
        time_of_day_score = self._score_time_of_day(slot_time, constraints, user_timezone)

        # Combined score
        total_score = (
            w_proximity * proximity_score +
            w_productivity * productivity_score +
            w_spacing * spacing_score +
            w_time_of_day * time_of_day_score
        )

        return min(1.0, max(0.0, total_score))

    def _score_productivity_match(
        self,
        slot_time: datetime,
        constraints: Dict[str, Any],
        user_timezone: str
    ) -> float:
        """Score based on user's productivity patterns."""
        # TODO: Load user's actual productivity patterns from database
        # For now, use simple heuristics

        from app.core.utils.timezone_utils import get_timezone_manager
        local_time = get_timezone_manager().convert_to_user_timezone(slot_time, user_timezone)
        hour = local_time.hour

        # Default productivity curve (peak 9am-5pm)
        if 9 <= hour < 17:
            return 1.0
        elif 8 <= hour < 9 or 17 <= hour < 19:
            return 0.7
        else:
            return 0.3

    def _score_spacing(
        self,
        slot_time: datetime,
        duration_minutes: int,
        busy_blocks: List[TimeBlock]
    ) -> float:
        """Score based on spacing from other events (prefer buffer time)."""
        slot_end = slot_time + timedelta(minutes=duration_minutes)

        # Find nearest blocks before and after
        min_gap_before = float('inf')
        min_gap_after = float('inf')

        for block in busy_blocks:
            if block.end_time <= slot_time:
                gap = (slot_time - block.end_time).total_seconds() / 60
                min_gap_before = min(min_gap_before, gap)
            elif block.start_time >= slot_end:
                gap = (block.start_time - slot_end).total_seconds() / 60
                min_gap_after = min(min_gap_after, gap)

        # Prefer 30+ minute gaps
        desired_gap = 30
        avg_gap = (
            min(min_gap_before, desired_gap) +
            min(min_gap_after, desired_gap)
        ) / (2 * desired_gap)

        return avg_gap

    def _score_time_of_day(
        self,
        slot_time: datetime,
        constraints: Dict[str, Any],
        user_timezone: str
    ) -> float:
        """Score based on time-of-day preferences."""
        from app.core.utils.timezone_utils import get_timezone_manager
        local_time = get_timezone_manager().convert_to_user_timezone(slot_time, user_timezone)
        hour = local_time.hour

        prefer_afternoon = constraints.get("prefer_afternoon", False)
        prefer_morning = constraints.get("prefer_morning", False)

        if prefer_afternoon and 13 <= hour < 17:
            return 1.0
        elif prefer_morning and 8 <= hour < 12:
            return 1.0
        else:
            return 0.5

    def _generate_slot_reasoning(
        self,
        slot_time: datetime,
        preferred_time: datetime,
        score: float,
        constraints: Dict[str, Any]
    ) -> str:
        """Generate human-readable reasoning for slot choice."""
        time_diff = (slot_time - preferred_time).total_seconds() / 60

        if abs(time_diff) < 15:
            return "Very close to your preferred time"
        elif abs(time_diff) < 60:
            return f"Shifted {int(abs(time_diff))} minutes to avoid conflicts"
        elif time_diff > 0:
            return f"Moved {int(time_diff / 60)} hours later to find free slot"
        else:
            return f"Moved {int(abs(time_diff) / 60)} hours earlier to find free slot"

    async def _llm_fallback_scheduling(
        self,
        preferred_time: datetime,
        duration_minutes: int,
        event_title: str,
        busy_blocks: List[TimeBlock],
        constraints: Dict[str, Any],
        user_timezone: str
    ) -> SchedulingResult:
        """
        LLM-based fallback for complex scheduling scenarios.

        Used when:
        - No free slots found in heuristic search
        - Complex conflicts requiring event shifting
        - Multiple overlapping flexible events

        Args:
            preferred_time: User's preferred time
            duration_minutes: Event duration
            event_title: Name of event
            busy_blocks: Existing busy blocks
            constraints: User preferences
            user_timezone: User's timezone

        Returns:
            SchedulingResult with LLM-chosen slot and reasoning
        """
        logger.info("[SmartSlotFinder] Using LLM fallback for complex scheduling")

        try:
            from openai import OpenAI
            import os
            import json

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Prepare context for LLM
            busy_slots_info = []
            for block in busy_blocks:
                from app.core.utils.timezone_utils import get_timezone_manager
                tz_mgr = get_timezone_manager()
                local_start = tz_mgr.convert_to_user_timezone(block.start_time, user_timezone)
                local_end = tz_mgr.convert_to_user_timezone(block.end_time, user_timezone)
                busy_slots_info.append({
                    "title": block.title,
                    "start": local_start.strftime("%Y-%m-%d %H:%M"),
                    "end": local_end.strftime("%Y-%m-%d %H:%M"),
                    "readonly": block.readonly,
                    "type": block.type
                })

            from app.core.utils.timezone_utils import get_timezone_manager
            local_preferred = get_timezone_manager().convert_to_user_timezone(preferred_time, user_timezone)

            system_prompt = """You are a scheduling assistant. Find the best alternative time for an event given busy periods and constraints.

Your task:
1. Analyze the busy schedule and constraints
2. Find the most natural alternative time
3. Optionally propose shifting flexible events by ≤30 minutes if needed
4. Provide clear reasoning for your choice

Return JSON with:
{
  "new_start": "YYYY-MM-DD HH:MM",
  "moved_event": null or event title,
  "shift_minutes": 0 or shift amount,
  "reasoning": "explanation"
}"""

            user_prompt = f"""Find the best time for this event:

Target Event: "{event_title}"
Requested Time: {local_preferred.strftime("%Y-%m-%d %H:%M")}
Duration: {duration_minutes} minutes

Busy Schedule:
{json.dumps(busy_slots_info, indent=2)}

Constraints:
- Working hours: {constraints.get('earliest_start', '08:00')} - {constraints.get('latest_end', '22:00')}
- Prefer afternoon: {constraints.get('prefer_afternoon', False)}
- Max shift from preferred: {self.max_shift_minutes} minutes

Find the best alternative time."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Parse LLM response
            new_start_str = result.get("new_start")
            reasoning = result.get("reasoning", "LLM-suggested alternative")

            # Convert to datetime
            from app.core.utils.timezone_utils import get_timezone_manager
            tz_mgr = get_timezone_manager()
            naive_local = datetime.strptime(new_start_str, "%Y-%m-%d %H:%M")
            new_start_local = tz_mgr.ensure_timezone_aware(naive_local, user_timezone)
            new_start_utc = new_start_local.astimezone(tz_mgr._default_timezone)
            new_end_utc = new_start_utc + timedelta(minutes=duration_minutes)

            return SchedulingResult(
                success=True,
                chosen_slot=SlotCandidate(
                    start_time=new_start_utc,
                    end_time=new_end_utc,
                    score=0.85,  # LLM confidence
                    reasoning=reasoning,
                    conflicts=[],
                    method="llm"
                ),
                message=self._format_time(new_start_utc, user_timezone),
                rationale=reasoning,
                method="llm",
                confidence=0.85,
                moved_events=[result] if result.get("moved_event") else None
            )

        except Exception as e:
            logger.error(f"[SmartSlotFinder] LLM fallback failed: {e}", exc_info=True)
            return SchedulingResult(
                success=False,
                chosen_slot=None,
                message="Could not find available time slot",
                rationale=f"No free slots found and LLM fallback failed: {str(e)}",
                method="error",
                confidence=0.0
            )

    def _format_time(self, dt: datetime, user_timezone: str) -> str:
        """Format datetime for user display."""
        from app.core.utils.timezone_utils import get_timezone_manager
        local_time = get_timezone_manager().convert_to_user_timezone(dt, user_timezone)
        return local_time.strftime("%b %d at %I:%M %p")


# Global singleton instance
_smart_slot_finder = None


def get_smart_slot_finder() -> SmartSlotFinder:
    """Get or create the global SmartSlotFinder instance."""
    global _smart_slot_finder
    if _smart_slot_finder is None:
        _smart_slot_finder = SmartSlotFinder()
    return _smart_slot_finder
