from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models import User
from app.schemas import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token/{username}", response_model=TokenResponse)
def token_for_seeded_user(username: str, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=404, detail="Seeded user not found")
    return TokenResponse(access_token=create_access_token(str(user.id)))
