from sqlalchemy import String, ForeignKey, Integer, Boolean, JSON, DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_id: Mapped[str] = mapped_column(String, nullable=False)


class PlayerProgress(Base):
    __tablename__ = "player_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    achievement_id: Mapped[int] = mapped_column(Integer, ForeignKey("achievements.id"), nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def increment(self, value: int) -> None:
        if not self.is_completed:
            self.current_value += value

    def check_completion(self, target_value: int) -> bool:
        if self.is_completed:
            return False

        if self.current_value >= target_value:
            self.is_completed = True
            self.current_value = target_value
            return True

        return False


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    error_message: Mapped[str] = mapped_column(String, nullable=True)
