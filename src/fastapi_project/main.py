"""Course app with Alembic-managed database migrations."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .database import engine
from .routers import auth, post, user, vote


app = FastAPI(title="FastAPI Course - Posts API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)


@app.get("/health", tags=["Health"])
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"Hello": "How are you doing"}


@app.get("/items/{item_id}", tags=["Initial examples"])
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
