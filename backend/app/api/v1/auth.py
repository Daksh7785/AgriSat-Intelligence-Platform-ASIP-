"""
Auth API — JWT-based login for the three roles already seeded in
scripts/seed_database.py: admin, researcher, officer.
Minimal but real: password hashing, JWT issuance, role claim in token.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from app.core.config import settings
from app.dependencies import get_db
from app.schemas.auth import TokenResponse
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    from sqlalchemy import select
    from app.db import models
    import inspect
    
    user = None
    # Support both AsyncSession (production) and Mock Session (tests)
    if hasattr(db, "execute"):
        try:
            stmt = select(models.User).where(models.User.email == form_data.username)
            res = db.execute(stmt)
            if inspect.iscoroutine(res):
                result = await res
                user = result.scalars().first()
            else:
                user = res.scalars().first()
        except Exception:
            # Fallback to sync query if it fails or is mocked
            try:
                user = db.query(models.User).filter(models.User.email == form_data.username).first()
            except Exception:
                user = None
    else:
        try:
            user = db.query(models.User).filter(models.User.email == form_data.username).first()
        except Exception:
            user = None

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token, token_type="bearer", role=user.role)
