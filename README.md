# FastAPI course project

Implementation through **Advanced FastAPI**, plus **Database Migration** with Alembic.
The downloaded English transcripts are in [transcripts/](transcripts/).
This is the final ORM-based app at that point in the course, rather than a
separate copy of every intermediate in-memory/raw-SQL version.

## Run locally

The app uses PostgreSQL, matching the course. PostgreSQL must be running and a
database named `fastapi` must exist.

PostgreSQL 18 is installed locally. The existing course tables have been checked
against the models and registered at Alembic revision `0001_initial_schema`.

1. Run `uv sync`.
2. Use the generated local `.env`, or copy `.env.example` to `.env` and set your
   PostgreSQL password and a random JWT secret.
3. Run `uv run python scripts/create_database.py` to create the course database
   (an existing database is left intact).
4. Run `uv run python scripts/migrate.py` to apply migrations. This also handles
   an existing, matching pre-Alembic course schema safely.
5. Run `uv run uvicorn main:app --reload`.
6. Open <http://127.0.0.1:8000/docs>.

Table creation and schema changes are now managed by Alembic. Starting the API
does not create or modify tables automatically.

For pgAdmin, register a local server using host `localhost`, port `5432`,
maintenance database `postgres`, and username `postgres`. Use the password
stored in your local `.env`. The application database is `fastapi`.

## Try the API

1. POST `/users/` with an email and password.
2. POST `/login` as form data: `username` is the email, plus `password`.
3. In Swagger, click **Authorize** and log in using those same credentials.
4. POST `/posts/` with `title`, `content`, and optional `published`.
5. GET `/posts/?limit=10&skip=0&search=beaches`.
6. POST `/vote/` with `{"post_id": 1, "dir": 1}`; use `dir: 0` to remove your vote.

GET post responses contain `{"Post": {...}, "votes": 0}`, including the owner's
public user details. Create/update responses return the post directly, as in
lesson 87. Passwords are hashed and excluded from all user responses.

Authenticated users can read all posts. Only a post's owner can update or
delete it. A user can vote on a post once; repeated votes return 409.

## Where to read the code

| Course topics | Files |
| --- | --- |
| Application entry point and automatic API docs | `main.py`, `src/fastapi_project/main.py` |
| Database engine and request sessions | `database.py` |
| Users, posts, foreign keys, relationships, composite vote key | `models.py` |
| Request validation and response models | `schemas.py` |
| Registration and user lookup | `routers/user.py` |
| Login, JWT creation, expiration, protected routes | `routers/auth.py`, `oauth2.py` |
| Password hashing | `utils.py` |
| CRUD, ownership, pagination, title search, joins and vote counts | `routers/post.py` |
| Like/unlike operations | `routers/vote.py` |
| Environment variables | `config.py`, `.env.example` |

Paths in the table, except the root entry point, are relative to
`src/fastapi_project/`. Your original greeting and item example remain available.

## Version adaptations

The course uses older library APIs. This implementation uses Pydantic v2
`model_dump()` and `from_attributes=True`, SQLAlchemy typed models and `select()`,
and `pydantic-settings`. JWT signing uses PyJWT; password hashing uses
`pwdlib` with Argon2, following the current
[FastAPI security tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).
Course-facing routes and behavior are retained. Small validation improvements
include restricting vote direction to 0/1, nonnegative pagination, and handling
duplicate registration.

## Database migrations

The initial revision creates users, posts, and votes, including defaults, unique
emails, foreign keys with cascading deletes, and the composite vote primary key.
It is a complete initial schema, rather than the instructor's intermediate
practice revisions. Database migrations change table structure; they do not
automatically insert sample users or posts.

For an empty database, run `uv run alembic upgrade head`. For the existing course
database, the one-time adoption has already been performed by `scripts/migrate.py`:
it compared the schema before stamping the initial revision, preserving data.

For later model changes:

1. Edit `src/fastapi_project/models.py`.
2. Run `uv run alembic revision --autogenerate -m "describe the change"`.
3. Read the generated file in `alembic/versions/`; check both `upgrade()` and
   `downgrade()` before applying it. Autogeneration needs human review, especially
   for renames and data transformations.
4. Run `uv run alembic upgrade head`.
5. Run `uv run alembic check` to check for model/schema drift.

Useful inspection commands are `uv run alembic current` and
`uv run alembic history`. To roll back one revision, use
`uv run alembic downgrade -1`. The initial revision's downgrade drops the
course tables and their data; only use it on a disposable database. No rollback
has been run on your existing course tables.

The connection comes from `.env`; `alembic.ini` contains no database credentials.
`scripts/create_tables.py` now delegates to the migration helper for compatibility.

## CORS

The API allows frontend origins on localhost and 127.0.0.1 at ports 3000 and
5173 by default. To use another frontend origin, set `CORS_ORIGINS` in `.env`
to a JSON list, for example:

```dotenv
CORS_ORIGINS=["http://localhost:8080"]
```

Restart the API after changing settings. Allowed methods are GET, POST, PUT,
DELETE, and OPTIONS; Authorization and Content-Type headers are permitted.

## Hosting FastAPI and PostgreSQL on Render

`render.yaml` defines a free Python web service and a free PostgreSQL 18
database in the same region. Render supplies the private database URL and
generates a fresh JWT signing secret; your local `.env` is not uploaded.
This starts with a separate empty cloud database, not a copy of your local rows.

To deploy from the Render dashboard:

1. Push this project's deployment files to the `main` branch on GitHub.
2. Choose **New > Blueprint**, connect your GitHub repository, and select
   `render.yaml`.
3. Review that both resources use the **Free** plan and apply the Blueprint.
4. Wait for deployment, then open the web service's URL followed by `/docs`.
5. Check `/health`; a successful response confirms database connectivity.

The build command is `uv sync --locked --no-dev`. The startup script applies
`alembic upgrade head` before running Uvicorn on Render's assigned port.
Free services do not have pre-deploy commands, so migrations run at each startup.
For a future multi-instance paid deployment, move migrations into a single
pre-deploy step instead.

`DATABASE_URL` overrides the individual local database settings. Standard
Render PostgreSQL URLs are converted to the installed Psycopg 3 driver.
External access to the hosted database is disabled in the Blueprint; the API
uses Render's private connection. No local database password is shared.

The hosted CORS list starts empty because no separate frontend is deployed.
Swagger at `/docs` works from the API's own origin. When you deploy a frontend,
set `CORS_ORIGINS` in Render to its exact origin as a JSON list.

**Free-plan limits:** Render's free PostgreSQL expires after 30 days. Free web
services sleep after 15 minutes without requests and take time to wake up.
See [Render's free plan documentation](https://render.com/docs/free).
The Blueprint does not choose paid resources or upgrade plans automatically.

Docker and CI/CD are not included.

## Verification

42 API checks passed using an isolated temporary database session override:
registration, duplicate emails, password hashing, login, invalid/expired tokens,
CRUD, cross-user ownership restrictions, query parameters, vote counts,
duplicate voting, unvoting, cascade deletion, and API docs.
The temporary verification did not use or change the configured database.
Migration verification uses real PostgreSQL in a randomly named temporary schema
inside a rolled-back transaction. Run it with:

`uv run python -m unittest discover -s tests -v`
