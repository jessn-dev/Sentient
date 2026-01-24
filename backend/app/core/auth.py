import os
import logging
from supabase import create_client, Client
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

# 1. Configure Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 2. Load Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")             # Anon/Public Key
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Admin/Service Role Key

# 3. Initialize Supabase Clients
supabase: Optional[Client] = None
supabase_admin: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ [AUTH] Standard Supabase Client Initialized")
    except Exception as e:
        logger.error(f"⚠️ [AUTH] Supabase Init Failed: {e}")
else:
    logger.critical("⚠️ [AUTH] CRITICAL: SUPABASE_URL or SUPABASE_KEY missing. Auth will fail.")

# Admin Client (for checking duplicates/managing users)
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ [AUTH] Admin Supabase Client Initialized (User Management Enabled)")
    except Exception as e:
        logger.warning(f"⚠️ [AUTH] Admin Client Init Failed: {e}")
else:
    logger.warning("ℹ️ [AUTH] SUPABASE_SERVICE_KEY not found. Duplicate checks will FAIL.")

# 4. Define OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def check_user_exists(email: str) -> bool:
    """
    Checks if a user already exists with the given email.
    Requires SUPABASE_SERVICE_KEY to be set.
    """
    # ✅ FAIL SECURE: If admin client is missing, we MUST NOT return False (Email Available).
    # We should raise an error to alert the developer that the system is misconfigured.
    if not supabase_admin:
        logger.critical("❌ [AUTH] SECURITY ALERT: check_user_exists called without SUPABASE_SERVICE_KEY.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: Cannot verify user existence."
        )

    try:
        # Supabase Admin List Users (filters by email)
        # Note: listing users and filtering in python is the most compatible way for older versions.
        users = supabase_admin.auth.admin.list_users()
        for user in users:
            if user.email == email:
                logger.info(f"🔍 [AUTH] Duplicate Found: {email} already exists.")
                return True
        return False
    except Exception as e:
        logger.error(f"❌ [AUTH] Failed to check user existence: {e}")
        # If the check crashes, we assume the user exists to prevent overwrite/duplicates
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying user status"
        )

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the JWT token with Supabase and returns the user ID.
    """
    # FAIL SAFE
    if not supabase:
        logger.error("❌ [AUTH] Auth Failed: Service not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured"
        )

    if not token:
        logger.warning("⚠️ [AUTH] Auth Failed: No token provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify the token
        user_response = supabase.auth.get_user(token)

        if user_response and user_response.user:
            return user_response.user.id

        logger.warning("⚠️ [AUTH] Auth Failed: Invalid Token Structure.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except Exception as e:
        logger.error(f"❌ [AUTH] Token Validation Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )