from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, oauth2, schemas, utils
from ..database import get_db

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=schemas.Token)
def login(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.scalar(select(models.User).where(models.User.email == credentials.username))
    if user is None or not utils.verify(credentials.password, user.password):
        raise HTTPException(status_code=403, detail="Invalid credentials")
    return {"access_token": oauth2.create_access_token({"user_id": user.id}), "token_type": "bearer"}
