from fastapi import APIRouter, HTTPException, Depends
from app.schemas.auth import UserSignUp, UserLogin, Token
from app.db.session import supabase
from app.core.config import get_settings
import bcrypt

router = APIRouter()
settings = get_settings()

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

@router.post("/signup", response_model=dict)
async def signup(user_data: UserSignUp):
    try:
        if not user_data.password:
            raise HTTPException(status_code=400, detail="Password is required")

        # Hash the password first to ensure it works
        try:
            hashed_password = hash_password(user_data.password)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Password hashing failed: {str(e)}")

        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                }
            }
        })
        
        if auth_response.user is None:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Store user data in our table
        user_id = auth_response.user.id
        user_data = {
            "id": user_id,
            "full_name": user_data.full_name,
            "email": user_data.email,
            "hashed_password": hashed_password
        }
        
        # Insert user data
        result = supabase.table("users").insert(user_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to store user data")
        
        return {
            "message": "User created successfully. Please check your email for verification.",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    try:
        if not user_data.password:
            raise HTTPException(status_code=401, detail="Password is required")

        # Try to sign in with Supabase Auth first
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": user_data.email,
                "password": user_data.password
            })
            
            if auth_response.session is None:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            return {
                "access_token": auth_response.session.access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            error_msg = str(e)
            if "Email not confirmed" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Please verify your email before logging in. Check your inbox for the verification link."
                )
            elif "Invalid login credentials" in error_msg:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            else:
                print(f"Login error: {error_msg}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials") 