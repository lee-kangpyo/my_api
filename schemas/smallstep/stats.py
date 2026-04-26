from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StatsOverview(BaseModel):
    total_goals: int
    completed_goals: int
    completed_phases_count: int
    current_level: int
    experience_points: int
    xp_to_next_level: int
    completed_tasks_count: int
    current_streak: int
    longest_streak: int

class WeeklyStats(BaseModel):
    week_start_date: datetime
    week_end_date: datetime
    tasks_completed: int
    tasks_skipped: int
    completion_rate: int  # percentage
    xp_earned: int

class StreakInfo(BaseModel):
    current_streak: int
    longest_streak: int
    streak_start_date: Optional[datetime] = None
    is_streak_active_today: bool
    last_activity_date: Optional[datetime] = None
    streak_history: List[dict] = []  # List of {date: str, completed: bool}
