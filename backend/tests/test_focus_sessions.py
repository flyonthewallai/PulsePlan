"""
Tests for Focus Session Tracking System
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.focus.focus_session_service import FocusSessionService


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    supabase = Mock()
    supabase.table = Mock(return_value=supabase)
    supabase.insert = Mock(return_value=supabase)
    supabase.update = Mock(return_value=supabase)
    supabase.select = Mock(return_value=supabase)
    supabase.eq = Mock(return_value=supabase)
    supabase.single = Mock(return_value=supabase)
    supabase.execute = Mock()
    return supabase


@pytest.fixture
def mock_cache():
    """Mock cache service"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def focus_service(mock_supabase, mock_cache):
    """Create FocusSessionService with mocks"""
    service = FocusSessionService()
    service.supabase = mock_supabase
    service.cache_service = mock_cache
    return service


class TestFocusSessionService:
    """Test suite for FocusSessionService"""
    
    @pytest.mark.asyncio
    async def test_start_session_success(self, focus_service, mock_supabase):
        """Test successfully starting a focus session"""
        # Mock the insert response
        mock_response = Mock()
        mock_response.data = [{
            'id': 'session-123',
            'user_id': 'user-456',
            'start_time': datetime.utcnow().isoformat(),
            'expected_duration': 25,
            'session_type': 'pomodoro'
        }]
        mock_supabase.execute.return_value = mock_response
        
        # Start session
        result = await focus_service.start_session(
            user_id='user-456',
            expected_duration=25,
            context='Test focus session'
        )
        
        assert result['success'] is True
        assert result['session_id'] == 'session-123'
        assert 'session' in result
        
        # Verify insert was called
        mock_supabase.table.assert_called_with('focus_sessions')
        mock_supabase.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_end_session_success(self, focus_service, mock_supabase):
        """Test successfully ending a focus session"""
        # Mock getting the session
        start_time = datetime.utcnow() - timedelta(minutes=25)
        mock_get_response = Mock()
        mock_get_response.data = {
            'id': 'session-123',
            'user_id': 'user-456',
            'start_time': start_time.isoformat(),
            'actual_start_time': start_time.isoformat(),
            'expected_duration': 25
        }
        
        # Mock update response
        mock_update_response = Mock()
        mock_update_response.data = [{
            **mock_get_response.data,
            'end_time': datetime.utcnow().isoformat(),
            'duration_minutes': 25,
            'was_completed': True
        }]
        
        mock_supabase.execute.side_effect = [mock_get_response, mock_update_response]
        
        # End session
        result = await focus_service.end_session(
            session_id='session-123',
            user_id='user-456',
            was_completed=True,
            focus_score=4
        )
        
        assert result['success'] is True
        assert 'session' in result
        assert result['actual_duration'] >= 24  # Should be close to 25 minutes
        
        # Verify update was called
        mock_supabase.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compute_user_profile_no_sessions(self, focus_service, mock_supabase):
        """Test computing profile with no sessions"""
        # Mock empty sessions response
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.execute.return_value = mock_response
        
        # Mock upsert for empty profile
        mock_upsert_response = Mock()
        mock_upsert_response.data = [{
            'user_id': 'user-456',
            'total_sessions_count': 0,
            'avg_focus_duration_minutes': 0
        }]
        mock_supabase.execute.side_effect = [mock_response, mock_upsert_response]
        
        profile = await focus_service.compute_user_profile('user-456')
        
        assert profile['total_sessions_count'] == 0
        assert profile['avg_focus_duration_minutes'] == 0
    
    @pytest.mark.asyncio
    async def test_compute_user_profile_with_sessions(self, focus_service, mock_supabase):
        """Test computing profile with actual sessions"""
        # Mock sessions data
        sessions = [
            {
                'id': 'sess-1',
                'user_id': 'user-456',
                'start_time': '2025-01-15T10:00:00Z',
                'duration_minutes': 25,
                'expected_duration': 25,
                'was_completed': True,
                'interruption_count': 0,
                'break_minutes': 5
            },
            {
                'id': 'sess-2',
                'user_id': 'user-456',
                'start_time': '2025-01-15T14:00:00Z',
                'duration_minutes': 30,
                'expected_duration': 25,
                'was_completed': True,
                'interruption_count': 1,
                'break_minutes': 5
            },
            {
                'id': 'sess-3',
                'user_id': 'user-456',
                'start_time': '2025-01-15T16:00:00Z',
                'duration_minutes': 20,
                'expected_duration': 25,
                'was_completed': False,
                'interruption_count': 2,
                'break_minutes': 5
            }
        ]
        
        mock_sessions_response = Mock()
        mock_sessions_response.data = sessions
        
        mock_upsert_response = Mock()
        mock_upsert_response.data = [{
            'user_id': 'user-456',
            'avg_focus_duration_minutes': 25,  # (25+30+20)/3
            'avg_break_duration_minutes': 5,
            'avg_interruption_count': 1.0,
            'total_sessions_count': 3,
            'completed_sessions_count': 2
        }]
        
        mock_supabase.execute.side_effect = [mock_sessions_response, mock_upsert_response]
        
        profile = await focus_service.compute_user_profile('user-456')
        
        assert profile['total_sessions_count'] == 3
        assert profile['completed_sessions_count'] == 2
        assert profile['avg_focus_duration_minutes'] == 25
        assert profile['avg_interruption_count'] == 1.0
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, focus_service, mock_supabase):
        """Test retrieving user's session history"""
        # Mock sessions response
        mock_response = Mock()
        mock_response.data = [
            {'id': 'sess-1', 'user_id': 'user-456', 'duration_minutes': 25},
            {'id': 'sess-2', 'user_id': 'user-456', 'duration_minutes': 30}
        ]
        mock_supabase.execute.return_value = mock_response
        
        result = await focus_service.get_user_sessions(
            user_id='user-456',
            limit=10
        )
        
        assert result['success'] is True
        assert len(result['sessions']) == 2
        assert result['count'] == 2
    
    @pytest.mark.asyncio
    async def test_get_active_session_from_cache(self, focus_service, mock_cache):
        """Test getting active session from cache"""
        # Mock cached session
        cached_session = {
            'id': 'session-123',
            'user_id': 'user-456',
            'start_time': datetime.utcnow().isoformat()
        }
        mock_cache.get.return_value = cached_session
        
        result = await focus_service.get_active_session('user-456')
        
        assert result == cached_session
        mock_cache.get.assert_called_with('focus:active:user-456')


class TestFocusProfileComputation:
    """Test suite for profile computation logic"""
    
    def test_peak_hours_calculation(self):
        """Test that peak hours are correctly identified"""
        sessions = [
            {'start_time': '2025-01-15T10:00:00Z'},  # Hour 10
            {'start_time': '2025-01-15T10:30:00Z'},  # Hour 10
            {'start_time': '2025-01-15T14:00:00Z'},  # Hour 14
            {'start_time': '2025-01-15T22:00:00Z'},  # Hour 22
            {'start_time': '2025-01-15T22:15:00Z'},  # Hour 22
            {'start_time': '2025-01-15T22:45:00Z'},  # Hour 22
        ]
        
        # Hour 22 should be the peak (3 sessions)
        # Hour 10 should be second (2 sessions)
        hour_counts = {}
        for session in sessions:
            start = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
            hour = start.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        assert peak_hours[0][0] == 22  # Hour 22 is #1
        assert peak_hours[0][1] == 3   # 3 sessions
        assert peak_hours[1][0] == 10  # Hour 10 is #2
        assert peak_hours[1][1] == 2   # 2 sessions
    
    def test_underestimation_calculation(self):
        """Test calculation of time estimation accuracy"""
        sessions = [
            {'expected_duration': 25, 'duration_minutes': 30},  # +20% overrun
            {'expected_duration': 25, 'duration_minutes': 25},  # 0% perfect
            {'expected_duration': 25, 'duration_minutes': 20},  # -20% underrun
        ]
        
        underestimations = []
        for session in sessions:
            actual = session['duration_minutes']
            expected = session['expected_duration']
            diff_pct = ((actual - expected) / expected) * 100
            underestimations.append(diff_pct)
        
        avg_underestimation = sum(underestimations) / len(underestimations)
        
        # Average should be 0% (20 + 0 + (-20)) / 3
        assert abs(avg_underestimation) < 0.01
    
    def test_completion_ratio(self):
        """Test completion ratio calculation"""
        sessions = [
            {'expected_duration': 25, 'duration_minutes': 25},  # 100%
            {'expected_duration': 25, 'duration_minutes': 20},  # 80%
            {'expected_duration': 25, 'duration_minutes': 15},  # 60%
        ]
        
        completion_ratios = [
            s['duration_minutes'] / s['expected_duration']
            for s in sessions
        ]
        avg_completion = sum(completion_ratios) / len(completion_ratios)
        
        # Average should be 80% (100 + 80 + 60) / 3
        assert abs(avg_completion - 0.8) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])








