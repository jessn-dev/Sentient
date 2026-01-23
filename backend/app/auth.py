import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

# Initialize Supabase Client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # Use the ANON key here

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Supabase Credentials Missing! Auth will fail.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the JWT token sent in the Authorization header.
    Returns the user_id (UUID) if valid, otherwise raises 401.
    """
    token = credentials.credentials

    try:
        # Ask Supabase: "Is this token valid?"
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return response.user.id

    except Exception as e:
        # print(f"Auth Error: {e}") # Debugging
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )