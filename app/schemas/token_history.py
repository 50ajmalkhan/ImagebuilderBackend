from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

class TokenHistoryResponse(BaseModel):
    id: int
    user_id: int
    tokens: int
    action_type: str
    description: str
    extra_data: Dict
    created_at: datetime
    updated_at: datetime
    generation_url: Optional[str] = None  # For storing signed URLs

    class Config:
        from_attributes = True 