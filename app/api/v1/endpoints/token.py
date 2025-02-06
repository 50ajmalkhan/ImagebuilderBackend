from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.services.token_history import token_history_service
from app.models.user import User
from app.schemas.token_history import TokenHistoryResponse

router = APIRouter()

@router.get("/balance")
def get_token_balance(
    current_user: User = Depends(get_current_user)
):
    """Get current token balance for the user"""
    return {"tokens": current_user.tokens}

@router.get("/history", response_model=List[TokenHistoryResponse])
def get_token_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get token history for current user"""
    return token_history_service.get_user_token_history(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    ) 