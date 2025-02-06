from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.auth import UserSignUp, UserLogin, Token, VerifyEmailResponse
from app.db.session import get_db
from app.core.config import get_settings
from app.models.user import User
from app.models.user_verification import UserVerification
from app.services.email_service import send_verification_email
import bcrypt
from datetime import datetime, timedelta
import pytz
from jose import JWTError, jwt

router = APIRouter()
settings = get_settings()

def get_utc_now() -> datetime:
    """Get current UTC datetime with timezone information"""
    return datetime.now(pytz.UTC)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Password verification error: {str(e)}")
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = get_utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/signup", response_model=dict)
async def signup(user_data: UserSignUp, db: Session = Depends(get_db)):
    try:
        if not user_data.password:
            raise HTTPException(status_code=400, detail="Password is required")

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the password
        hashed_password = hash_password(user_data.password)

        # Create new user
        new_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=False
        )
        
        db.add(new_user)
        db.flush()  # Get the user ID without committing

        # Create verification record
        verification_token = create_access_token(
            {"email": user_data.email, "type": "verification"}
        )
        verification = UserVerification(
            user_id=new_user.id,
            verification_token=verification_token,
            expires_at=get_utc_now() + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)
        )
        
        db.add(verification)
        db.commit()
        db.refresh(new_user)

        # Send verification email
        try:
            send_verification_email(
                user_email=user_data.email,
                user_name=user_data.full_name,
                verification_token=verification_token
            )
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")
            # Don't raise here, let the user be created even if email fails
        
        return {
            "message": "User created successfully. Please check your email for verification.",
            "user_id": new_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        if not user_data.password:
            raise HTTPException(status_code=400, detail="Password is required")

        # Get user from database
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Verify password first
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Check if user is active and verified
        if not user.is_active:
            verification = db.query(UserVerification).filter(
                UserVerification.user_id == user.id
            ).first()
            
            if not verification or not verification.is_verified:
                # If verification record exists and not expired, tell user to check email
                current_time = get_utc_now()
                if verification and verification.expires_at > current_time:
                    raise HTTPException(
                        status_code=400,
                        detail="Please verify your email before logging in. Check your inbox for the verification link."
                    )
                # If no verification record or expired, create new one and send email
                else:
                    verification_token = create_access_token(
                        {"email": user.email, "type": "verification"}
                    )
                    if verification:
                        verification.verification_token = verification_token
                        verification.expires_at = current_time + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)
                    else:
                        verification = UserVerification(
                            user_id=user.id,
                            verification_token=verification_token,
                            expires_at=current_time + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)
                        )
                        db.add(verification)
                    
                    db.commit()
                    
                    try:
                        send_verification_email(
                            user_email=user.email,
                            user_name=user.full_name,
                            verification_token=verification_token
                        )
                    except Exception as e:
                        print(f"Failed to send verification email: {str(e)}")
                    
                    raise HTTPException(
                        status_code=400,
                        detail="Email verification required. A new verification link has been sent to your email."
                    )

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
            
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        # Decode token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        email = payload.get("email")
        token_type = payload.get("type")

        if not email or token_type != "verification":
            raise HTTPException(status_code=400, detail="Invalid verification token")

        # Get user and verification
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        verification = db.query(UserVerification).filter(
            UserVerification.user_id == user.id,
            UserVerification.verification_token == token
        ).first()

        if not verification:
            raise HTTPException(status_code=400, detail="Invalid verification token")

        if verification.is_verified:
            # Create access token even if already verified
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )
            return VerifyEmailResponse(
                message="Email already verified",
                user=user,
                access_token=access_token
            )

        current_time = get_utc_now()
        if verification.expires_at < current_time:
            # Create new verification token and send email
            new_token = create_access_token(
                {"email": user.email, "type": "verification"}
            )
            verification.verification_token = new_token
            verification.expires_at = current_time + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)
            db.commit()
            
            try:
                send_verification_email(
                    user_email=user.email,
                    user_name=user.full_name,
                    verification_token=new_token
                )
            except Exception as e:
                print(f"Failed to send new verification email: {str(e)}")
            
            raise HTTPException(
                status_code=400,
                detail="Verification token has expired. A new verification link has been sent to your email."
            )

        # Update verification
        verification.is_verified = True
        verification.verified_at = current_time
        
        # Activate the user
        user.is_active = True
        
        db.commit()
        db.refresh(user)  # Refresh to get updated user data

        # Create access token for the verified user
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return VerifyEmailResponse(
            message="Email verified successfully",
            user=user,
            access_token=access_token
        )
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 