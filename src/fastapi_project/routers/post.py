from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/posts", tags=["Posts"])
Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[models.User, Depends(oauth2.get_current_user)]


def posts_with_votes():
    # LEFT JOIN includes posts with no votes; COUNT ignores the null vote row.
    return (
        select(models.Post, func.count(models.Vote.post_id).label("votes"))
        .outerjoin(models.Vote, models.Vote.post_id == models.Post.id)
        .group_by(models.Post.id)
    )


@router.get("/", response_model=list[schemas.PostOut])
def get_posts(
    db: Database, current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    skip: Annotated[int, Query(ge=0)] = 0,
    search: str = "",
):
    # The final course app lets authenticated users read everyone's posts.
    query = posts_with_votes().where(models.Post.title.contains(search, autoescape=True))
    rows = db.execute(query.order_by(models.Post.id).limit(limit).offset(skip)).all()
    return [{"Post": post, "votes": votes} for post, votes in rows]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_post(post: schemas.PostCreate, db: Database, current_user: CurrentUser):
    new_post = models.Post(owner_id=current_user.id, **post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/{id}", response_model=schemas.PostOut)
def get_post(id: int, db: Database, current_user: CurrentUser):
    row = db.execute(posts_with_votes().where(models.Post.id == id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Post with id {id} does not exist")
    return {"Post": row[0], "votes": row[1]}


def own_post(id: int, db: Session, user: models.User) -> models.Post:
    post = db.get(models.Post, id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post with id {id} does not exist")
    if post.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform requested action")
    return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Database, current_user: CurrentUser):
    db.delete(own_post(id, db, current_user))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Database, current_user: CurrentUser):
    post = own_post(id, db, current_user)
    for field, value in updated_post.model_dump().items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post
