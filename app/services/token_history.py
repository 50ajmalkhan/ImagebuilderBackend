from sqlalchemy.orm import Session
from app.models.token_history import TokenHistory, TokenActionType
from typing import Dict, Optional, List
from app.services.storage_service import storage_service
import os

class TokenHistoryService:
    def create_token_history(
        self,
        db: Session,
        user_id: int,
        tokens: int,
        action_type: TokenActionType,
        description: str,
        extra_data: Optional[Dict] = None,
        generation_url: Optional[str] = None
    ) -> TokenHistory:
        """Create a new token history record"""
        if extra_data is None:
            extra_data = {}
            
        if generation_url:
            extra_data["generation_url"] = generation_url
            
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

    def get_user_token_history(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[TokenHistory]:
        """Get token history for a user with signed URLs"""
        histories = db.query(TokenHistory).filter(
            TokenHistory.user_id == user_id
        ).order_by(
            TokenHistory.created_at.desc()
        ).offset(skip).limit(limit).all()

        # Add signed URLs for generation URLs in extra_data
        for history in histories:
            if "generation_url" in history.extra_data:
                file_path = history.extra_data["generation_url"]
                filename = os.path.basename(file_path)
                history.extra_data["generation_url"] = storage_service.get_signed_url(
                    file_path=file_path,
                    display_name=filename
                )

        return histories

token_history_service = TokenHistoryService() 