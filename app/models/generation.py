from sqlalchemy import Column, String, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
import enum
from app.db.base_class import Base, TimestampMixin

class GenerationType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"

class Generation(Base, TimestampMixin):
    __tablename__ = "generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # Will store "image" or "video"
    url = Column(String, nullable=False)
    reference_image_url = Column(String, nullable=True)
    status = Column(String, nullable=False, default="success")

    # Relationships
    user = relationship("User", back_populates="generations")

    def __repr__(self):
        return f"<Generation {self.id} - {self.type}>" 