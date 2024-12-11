from sqlalchemy import Column, String, UUID, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum
from .base import Base, TimestampMixin

class GenerationType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"

class Generation(Base, TimestampMixin):
    __tablename__ = "generations"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    type = Column(Enum(GenerationType), nullable=False)
    url = Column(String, nullable=False)
    reference_image_url = Column(String, nullable=True)
    status = Column(String, nullable=False, default="success")

    # Relationships
    user = relationship("User", back_populates="generations")

    def __repr__(self):
        return f"<Generation {self.id} - {self.type.value}>" 