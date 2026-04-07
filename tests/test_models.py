import pytest
from src.models import PlayerProgress

def test_increment_progress():
    progress = PlayerProgress(player_id="test_user", achievement_id=1, current_value=0, is_completed=False)
    progress.increment(5)
    
    assert progress.current_value == 5
    assert progress.is_completed is False

def test_check_completion_success():
    progress = PlayerProgress(player_id="test_user", achievement_id=1, current_value=8, is_completed=False)
    
    is_done = progress.check_completion(10)
    assert is_done is False
    assert progress.is_completed is False
    progress.increment(2)
    is_done_now = progress.check_completion(10)
    assert is_done_now is True
    assert progress.is_completed is True
    assert progress.current_value == 10

def test_check_completion_already_done():
    progress = PlayerProgress(player_id="test_user", achievement_id=1, current_value=10, is_completed=True)
    
    is_done = progress.check_completion(10)
    assert is_done is False
