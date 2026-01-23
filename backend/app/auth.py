import os
from supabase import create_client, Client
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

# 1. Load Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 2. Initialize Supabase Client Safely (Lazy/Conditional)
# We default to None so the app can start even if credentials are missing.
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Supabase Init Failed: {e}")
else:
    print("⚠️ CRITICAL: SUPABASE_URL or SUPABASE_KEY missing. Auth will fail.")

# 3. Define OAuth2 Scheme
# auto_error=False allows us to handle the error manually in the function
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the JWT token with Supabase and returns the user ID.
    If Supabase is not configured, it raises a 503 error.
    """
    # FAIL SAFE: Check if client exists before using it
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured (Missing Credentials)"
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify the token with Supabase Auth
        user_response = supabase.auth.get_user(token)

        if user_response and user_response.user:
            return user_response.user.id

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except Exception as e:
        print(f"Auth Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )