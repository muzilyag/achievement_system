from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from src.database import Base

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    target_value = Column(String, nullable=False)
    reward_id = Column(String, nullable=False)


class PlayerProgress(Base):
    __tablename__ = "player_progress"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String, nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    current_value = Column(Integer, default=0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
