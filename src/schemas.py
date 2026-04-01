from pydantic import BaseModel


class EventPayload(BaseModel):
    player_id: str
    action_type: str
    value: int


class AchievementCreate(BaseModel):
    name: str
    action_type: str
    target_value: int
    reward_id: str


class AchievementRead(AchievementCreate):
    id: int
    class Config:
        from_attributes = True
