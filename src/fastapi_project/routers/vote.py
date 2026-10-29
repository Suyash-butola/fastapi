from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/vote", tags=["Vote"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(
    vote: schemas.Vote, db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(oauth2.get_current_user)],
):
    if db.get(models.Post, vote.post_id) is None:
        raise HTTPException(status_code=404, detail=f"Post with id {vote.post_id} does not exist")
    existing = db.get(models.Vote, (current_user.id, vote.post_id))
    if vote.dir == 1:
        if existing:
            raise HTTPException(status_code=409, detail="You have already voted on this post")
        db.add(models.Vote(user_id=current_user.id, post_id=vote.post_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Vote could not be added") from None
        return {"message": "Successfully added vote"}
    if existing is None:
        raise HTTPException(status_code=404, detail="Vote does not exist")
    db.delete(existing)
    db.commit()
    return {"message": "Successfully deleted vote"}
