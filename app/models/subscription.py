from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base, TimestampMixin

class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tokens_purchased = Column(Integer, nullable=False)
    amount_paid = Column(Float, nullable=False)
    payment_status = Column(String, nullable=False)  # 'pending', 'paid', 'failed'
    payment_method = Column(String, nullable=False)  # 'stripe'
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription user_id={self.user_id} tokens={self.tokens_purchased} status={self.payment_status}>" 