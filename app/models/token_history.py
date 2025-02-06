from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base_class import Base, TimestampMixin
import enum

class TokenActionType(str, enum.Enum):
    CONSUMED = "consumed"
    ADDED = "added"

class TokenHistory(Base, TimestampMixin):
    __tablename__ = "token_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    tokens = Column(Integer, nullable=False)  # can be positive (added) or negative (consumed)
    action_type = Column(String, nullable=False)  # Will store "consumed" or "added"
    description = Column(String, nullable=False)  # e.g., "Subscription purchase", "Competitor search"
    extra_data = Column(JSONB, nullable=False, server_default='{}')  # store additional info like search query
    
    user = relationship("User", back_populates="token_history")

    def __repr__(self):
        return f"<TokenHistory user_id={self.user_id} tokens={self.tokens} action={self.action_type}>" 