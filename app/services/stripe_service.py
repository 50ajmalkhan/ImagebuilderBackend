import stripe
from app.core.config import get_settings
from fastapi import HTTPException, status

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    async def verify_payment_signature(self, payload: bytes, sig_header: str) -> dict:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def get_session(self, session_id: str) -> dict:
        """Get Stripe session details"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def create_checkout_session(self, user_id: int, tokens: int, amount: float) -> str:
        """Create a Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'{tokens} VidGen Tokens',
                            'description': f'Purchase {tokens} tokens for video generation'
                        },
                        'unit_amount': int(amount * 100)  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                client_reference_id=str(user_id),
                metadata={
                    'tokens': str(tokens),
                    'application_slug': 'vidgen'
                },
                success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/payment/cancel"
            )
            return session.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

stripe_service = StripeService() 