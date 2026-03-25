from pydantic import BaseModel


class EventPayload(BaseModel):
    player_id: str
    action_type: str
    value: int


class AchievementCreate(BaseModel):
    id: int
    goal: int 
    reward_type: str
