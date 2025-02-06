from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base, TimestampMixin
import uuid

class UserVerification(Base, TimestampMixin):
    __tablename__ = "user_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    verification_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    user = relationship("User", back_populates="verification")

    def __repr__(self):
        return f"<UserVerification user_id={self.user_id}>" 