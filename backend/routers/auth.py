"""
routers/auth.py — Authentication endpoints: register, login, refresh, me.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from core.database import get_users_collection
from core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    TokenResponse,
)
from models.user import UserRegister, UserLogin, UserProfile

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister):
    """Register a new user, agent, or admin account."""
    users = get_users_collection()

    # Check email uniqueness
    existing = await users.find_one({"email": body.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    now = datetime.now(timezone.utc)
    user_doc = {
        "user_id": str(uuid.uuid4()),
        "name": body.name,
        "email": body.email,
        "password_hash": get_password_hash(body.password),
        "role": body.role,
        "tier": body.tier,
        "skills": body.skills or [],
        "current_load": 0,
        "max_load": 10,
        "avg_resolution_time": None,
        "tickets_resolved_total": 0,
        "approval_rate": None,
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }

    await users.insert_one(user_doc)
    logger.info(f"New user registered: {body.email} (role={body.role})")

    return UserProfile(**{k: v for k, v in user_doc.items() if k != "password_hash"})


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    """Authenticate user and return JWT access token."""
    users = get_users_collection()

    user = await users.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    # Update last_login timestamp
    await users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )

    access_token = create_access_token(
        data={
            "sub": user["user_id"],
            "email": user["email"],
            "role": user["role"],
        }
    )

    from core.config import settings
    logger.info(f"User logged in: {body.email}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get the authenticated user's profile."""
    return UserProfile(**current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh the JWT access token (returns new token with fresh expiry)."""
    access_token = create_access_token(
        data={
            "sub": current_user["user_id"],
            "email": current_user["email"],
            "role": current_user["role"],
        }
    )
    from core.config import settings
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
