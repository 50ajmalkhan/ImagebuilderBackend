from sqlalchemy.orm import Session
from app.models.token_history import TokenHistory, TokenActionType
from typing import Dict, Optional

class TokenHistoryService:
    def create_token_history(
        self,
        db: Session,
        user_id: int,
        tokens: int,
        action_type: TokenActionType,
        description: str,
        extra_data: Optional[Dict] = None
    ) -> TokenHistory:
        """Create a new token history record"""
        if extra_data is None:
            extra_data = {}
            
        token_history = TokenHistory(
            user_id=user_id,
            tokens=tokens,
            action_type=action_type,
            description=description,
            extra_data=extra_data
        )
        
        db.add(token_history)
        db.commit()
        db.refresh(token_history)
        
        return token_history

token_history_service = TokenHistoryService() 