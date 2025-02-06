from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.token_history import TokenHistory, TokenActionType
from app.services.stripe_service import stripe_service
from app.services.token_history import token_history_service
from app.core.config import get_settings
from app.schemas.subscription import SubscriptionResponse, CreateCheckoutSession

router = APIRouter()
settings = get_settings()

async def process_webhook_payment(
    session: Dict,
    db: Session,
) -> bool:
    """Process payment from webhook with metadata validation"""
    # Verify application slug
    metadata = session.get("metadata", {})
    if metadata.get("application_slug") != "vidgen":
        return True
    
    return await create_subscription(session, db)

async def create_subscription(
    session: Dict,
    db: Session,
) -> bool:
    """Create subscription record if not exists"""
    # Check if this payment was already processed
    existing_subscription = db.query(Subscription).filter(
        Subscription.transaction_id == session["id"]
    ).first()
    
    if existing_subscription:
        return False
        
    try:
        # Get user_id from client_reference_id and tokens from metadata
        client_reference_id = session.get("client_reference_id")
        metadata = session.get("metadata", {})
        tokens_str = metadata.get("tokens")
        
        if not client_reference_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing client_reference_id"
            )
            
        if not tokens_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing tokens in metadata"
            )
            
        try:
            user_id = int(client_reference_id)
            tokens = int(tokens_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client_reference_id or tokens format"
            )
        
        if not user_id or not tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zero values not allowed for user_id or tokens"
            )
        
        # Create subscription record
        subscription = Subscription(
            user_id=user_id,
            tokens_purchased=tokens,
            amount_paid=session["amount_total"] / 100,  # Convert from cents
            payment_status=session["payment_status"],
            payment_method="stripe",
            transaction_id=session["id"]
        )
        db.add(subscription)
        
        # Only add tokens and create history if payment is successful
        if session["payment_status"] == "paid":
            # Create token history record
            token_history_service.create_token_history(
                db=db,
                user_id=user_id,
                tokens=tokens,  # positive value for tokens added
                action_type=TokenActionType.ADDED,
                description="Subscription purchase",
                extra_data={
                    "subscription_id": session["id"],
                    "payment_method": "stripe",
                    "amount_paid": session["amount_total"] / 100
                }
            )
            
            # Update user's token balance
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found with ID: {user_id}"
                )
                
            user.tokens += tokens
            db.add(user)
        
        db.commit()
        return True
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment: {str(e)}"
        )

@router.post("/create-checkout-session")
async def create_checkout(
    data: CreateCheckoutSession,
    current_user: User = Depends(get_current_user)
):
    """Create a Stripe checkout session for token purchase"""
    try:
        session_id = await stripe_service.create_checkout_session(
            user_id=current_user.id,
            tokens=data.tokens,
            amount=data.amount
        )
        return {"session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events for payment notifications"""
    try:
        payload = await request.body()        
        sig_header = request.headers.get("stripe-signature")
        
        event = await stripe_service.verify_payment_signature(payload, sig_header)
        
        # Handle successful payment completion
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            await process_webhook_payment(session, db)
        
        # Always return 200 to acknowledge receipt of the webhook
        return Response(status_code=200)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/verify/{session_id}")
async def verify_payment(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify payment status and process if needed"""
    try:
        # Get session from Stripe
        session = await stripe_service.get_session(session_id)
        
        # Only process completed payments
        if session["payment_status"] == "paid":
            # Try to process the payment (will be ignored if already processed)
            was_processed = await create_subscription(session, db)
            return {
                "status": "success",
                "message": "Payment processed successfully" if was_processed else "Payment was already processed"
            }
        
        return {
            "status": session["payment_status"],
            "message": "Payment is not complete"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/history", response_model=List[SubscriptionResponse])
def get_subscription_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subscription history for current user"""
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(
        Subscription.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return subscriptions 