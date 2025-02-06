from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CreateCheckoutSession(BaseModel):
    tokens: int = Field(..., gt=0, description="Number of tokens to purchase")
    amount: float = Field(..., gt=0, description="Amount to charge in USD")

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    tokens_purchased: int
    amount_paid: float
    payment_status: str
    payment_method: str
    transaction_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 