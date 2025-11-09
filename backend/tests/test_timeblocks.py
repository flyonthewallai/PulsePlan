"""
Integration tests for unified timeblocks endpoint.
Tests the v_timeblocks VIEW, RPC function, and /v1/timeblocks API endpoint.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4


@pytest.fixture
def test_user_id():
    """Generate a test user ID"""
    return str(uuid4())


@pytest.fixture
def week_range():
    """Generate a week date range"""
    now = datetime.now(timezone.utc)
    from_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
    to_dt = from_dt + timedelta(days=7)
    return from_dt, to_dt


class TestTimeblocksEndpoint:
    """Test /v1/timeblocks endpoint"""

    def test_invalid_timestamps(self, client, auth_headers):
        """Test that invalid ISO timestamps return 400"""
        response = client.get(
            "/v1/timeblocks",
            params={"from": "invalid", "to": "2025-10-08T00:00:00Z"},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_reversed_timestamps(self, client, auth_headers):
        """Test that from >= to returns 400"""
        response = client.get(
            "/v1/timeblocks",
            params={
                "from": "2025-10-08T00:00:00Z",
                "to": "2025-10-01T00:00:00Z"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "before" in response.json()["detail"].lower()

    def test_missing_auth(self, client):
        """Test that missing auth returns 401"""
        response = client.get(
            "/v1/timeblocks",
            params={
                "from": "2025-10-01T00:00:00Z",
                "to": "2025-10-08T00:00:00Z"
            }
        )
        assert response.status_code == 401

    def test_empty_window(self, client, auth_headers, week_range):
        """Test that empty window returns empty items array"""
        from_dt, to_dt = week_range
        response = client.get(
            "/v1/timeblocks",
            params={
                "from": from_dt.isoformat(),
                "to": to_dt.isoformat()
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_response_structure(self, client, auth_headers, week_range):
        """Test that response has correct structure"""
        from_dt, to_dt = week_range
        response = client.get(
            "/v1/timeblocks",
            params={
                "from": from_dt.isoformat(),
                "to": to_dt.isoformat()
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "items" in data
        assert isinstance(data["items"], list)

        # If items exist, check structure
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "source" in item
            assert item["source"] in ["task", "calendar", "busy"]
            assert "title" in item
            assert "start" in item
            assert "end" in item
            assert "isAllDay" in item
            assert "readonly" in item


class TestTimeblocksWithData:
    """Test timeblocks with actual data (requires database setup)"""

    @pytest.mark.asyncio
    async def test_scheduled_task_appears(self, test_db, test_user_id, week_range):
        """Test that scheduled task appears in timeblocks"""
        from app.config.database.supabase import get_supabase_client

        supabase = get_supabase_client()
        from_dt, to_dt = week_range

        # Create a scheduled task
        task_id = str(uuid4())
        start = from_dt + timedelta(hours=10)
        end = start + timedelta(hours=2)

        await supabase.table("tasks").insert({
            "id": task_id,
            "user_id": test_user_id,
            "title": "Test Study Session",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "all_day": False,
            "status": "scheduled"
        }).execute()

        # Fetch timeblocks
        from app.database.timeblocks_repository import get_timeblocks_repository
        repo = get_timeblocks_repository()
        blocks = await repo.fetch_timeblocks(test_user_id, from_dt, to_dt)

        # Verify task appears
        task_blocks = [b for b in blocks if b["source"] == "task" and b["task_id"] == task_id]
        assert len(task_blocks) == 1
        assert task_blocks[0]["title"] == "Test Study Session"
        assert task_blocks[0]["readonly"] is False

        # Cleanup
        await supabase.table("tasks").delete().eq("id", task_id).execute()

    @pytest.mark.asyncio
    async def test_unscheduled_task_excluded(self, test_db, test_user_id, week_range):
        """Test that tasks without start/end dates are excluded"""
        from app.config.database.supabase import get_supabase_client

        supabase = get_supabase_client()
        from_dt, to_dt = week_range

        # Create unscheduled task
        task_id = str(uuid4())
        await supabase.table("tasks").insert({
            "id": task_id,
            "user_id": test_user_id,
            "title": "Unscheduled Task",
            "status": "pending",
            # No start_date or end_date
        }).execute()

        # Fetch timeblocks
        from app.database.timeblocks_repository import get_timeblocks_repository
        repo = get_timeblocks_repository()
        blocks = await repo.fetch_timeblocks(test_user_id, from_dt, to_dt)

        # Verify task does not appear
        task_blocks = [b for b in blocks if b.get("task_id") == task_id]
        assert len(task_blocks) == 0

        # Cleanup
        await supabase.table("tasks").delete().eq("id", task_id).execute()

    @pytest.mark.asyncio
    async def test_cancelled_event_excluded(self, test_db, test_user_id, week_range):
        """Test that cancelled calendar events are excluded"""
        from app.config.database.supabase import get_supabase_client

        supabase = get_supabase_client()
        from_dt, to_dt = week_range

        # Create cancelled event
        event_id = str(uuid4())
        start = from_dt + timedelta(hours=14)
        end = start + timedelta(hours=1)

        await supabase.table("calendar_events").insert({
            "id": event_id,
            "user_id": test_user_id,
            "provider": "google",
            "external_id": "test-event-123",
            "calendar_id": "primary",
            "title": "Cancelled Meeting",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "is_cancelled": True
        }).execute()

        # Fetch timeblocks
        from app.database.timeblocks_repository import get_timeblocks_repository
        repo = get_timeblocks_repository()
        blocks = await repo.fetch_timeblocks(test_user_id, from_dt, to_dt)

        # Verify cancelled event does not appear
        event_blocks = [b for b in blocks if b["block_id"] == event_id]
        assert len(event_blocks) == 0

        # Cleanup
        await supabase.table("calendar_events").delete().eq("id", event_id).execute()

    @pytest.mark.asyncio
    async def test_window_filtering(self, test_db, test_user_id):
        """Test that only overlapping blocks are returned"""
        from app.config.database.supabase import get_supabase_client

        supabase = get_supabase_client()

        # Create tasks outside window
        now = datetime.now(timezone.utc)
        window_start = now
        window_end = now + timedelta(days=7)

        # Task before window
        task1_id = str(uuid4())
        await supabase.table("tasks").insert({
            "id": task1_id,
            "user_id": test_user_id,
            "title": "Before Window",
            "start_date": (window_start - timedelta(days=2)).isoformat(),
            "end_date": (window_start - timedelta(days=1)).isoformat(),
        }).execute()

        # Task in window
        task2_id = str(uuid4())
        await supabase.table("tasks").insert({
            "id": task2_id,
            "user_id": test_user_id,
            "title": "In Window",
            "start_date": (window_start + timedelta(days=1)).isoformat(),
            "end_date": (window_start + timedelta(days=2)).isoformat(),
        }).execute()

        # Task after window
        task3_id = str(uuid4())
        await supabase.table("tasks").insert({
            "id": task3_id,
            "user_id": test_user_id,
            "title": "After Window",
            "start_date": (window_end + timedelta(days=1)).isoformat(),
            "end_date": (window_end + timedelta(days=2)).isoformat(),
        }).execute()

        # Fetch timeblocks for window
        from app.database.timeblocks_repository import get_timeblocks_repository
        repo = get_timeblocks_repository()
        blocks = await repo.fetch_timeblocks(test_user_id, window_start, window_end)

        # Verify only task2 appears
        task_ids = [b.get("task_id") for b in blocks if b.get("task_id")]
        assert task2_id in task_ids
        assert task1_id not in task_ids
        assert task3_id not in task_ids

        # Cleanup
        for task_id in [task1_id, task2_id, task3_id]:
            await supabase.table("tasks").delete().eq("id", task_id).execute()


class TestTimeblocksReadonly:
    """Test readonly logic for different scenarios"""

    @pytest.mark.asyncio
    async def test_task_not_readonly(self, test_db, test_user_id, week_range):
        """Test that tasks are never readonly"""
        from app.config.database.supabase import get_supabase_client

        supabase = get_supabase_client()
        from_dt, to_dt = week_range

        # Create task
        task_id = str(uuid4())
        start = from_dt + timedelta(hours=10)
        end = start + timedelta(hours=2)

        await supabase.table("tasks").insert({
            "id": task_id,
            "user_id": test_user_id,
            "title": "Test Task",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }).execute()

        # Fetch via repository
        from app.database.timeblocks_repository import get_timeblocks_repository
        repo = get_timeblocks_repository()
        blocks = await repo.fetch_timeblocks(test_user_id, from_dt, to_dt)

        task_blocks = [b for b in blocks if b.get("task_id") == task_id]
        assert len(task_blocks) == 1
        assert task_blocks[0]["readonly"] is False

        # Cleanup
        await supabase.table("tasks").delete().eq("id", task_id).execute()

    @pytest.mark.asyncio
    async def test_external_event_readonly(self, test_db, test_user_id, week_range):
        """Test that external calendar events are readonly (by default)"""
        from app.config.database.supabase import get_supabase_client

        supabase = get_supabase_client()
        from_dt, to_dt = week_range

        # Create external event
        event_id = str(uuid4())
        start = from_dt + timedelta(hours=14)
        end = start + timedelta(hours=1)

        await supabase.table("calendar_events").insert({
            "id": event_id,
            "user_id": test_user_id,
            "provider": "google",
            "external_id": "ext-123",
            "calendar_id": "primary",
            "title": "External Meeting",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }).execute()

        # Fetch via repository
        from app.database.timeblocks_repository import get_timeblocks_repository
        repo = get_timeblocks_repository()
        blocks = await repo.fetch_timeblocks(test_user_id, from_dt, to_dt)

        event_blocks = [b for b in blocks if b["block_id"] == event_id]
        assert len(event_blocks) == 1
        assert event_blocks[0]["readonly"] is True

        # Cleanup
        await supabase.table("calendar_events").delete().eq("id", event_id).execute()


@pytest.mark.skipif(
    True,  # Skip by default (requires Supabase connection)
    reason="Requires live Supabase database connection"
)
class TestPerformance:
    """Performance tests for timeblocks queries"""

    @pytest.mark.asyncio
    async def test_query_performance(self, test_db, test_user_id):
        """Test that weekly query completes in reasonable time"""
        import time
        from app.database.timeblocks_repository import get_timeblocks_repository

        repo = get_timeblocks_repository()

        # Query this week
        now = datetime.now(timezone.utc)
        from_dt = now
        to_dt = now + timedelta(days=7)

        start_time = time.time()
        blocks = await repo.fetch_timeblocks(test_user_id, from_dt, to_dt)
        elapsed = time.time() - start_time

        # Should complete in <100ms (adjust based on data volume)
        assert elapsed < 0.1, f"Query took {elapsed:.3f}s (expected <0.1s)"

        print(f"Fetched {len(blocks)} blocks in {elapsed:.3f}s")
