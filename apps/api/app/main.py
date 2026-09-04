import logging, uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.auth.routes import router as auth_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.services.seed import seed_database
from sqlalchemy import inspect, text

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
settings=get_settings(); app=FastAPI(title="DealSage API",version="0.1.0",description="Evidence-backed ownership transition research")
app.add_middleware(SessionMiddleware,secret_key=settings.session_secret,session_cookie="dealsage_session",same_site="lax",https_only=settings.session_cookie_secure,max_age=60*60*12)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.middleware("http")
async def request_context(request:Request,call_next):
    request_id=request.headers.get("x-request-id",str(uuid.uuid4())); response=await call_next(request); response.headers["x-request-id"]=request_id
    logging.info("request_id=%s method=%s path=%s status=%s",request_id,request.method,request.url.path,response.status_code); return response

@app.on_event("startup")
def startup():
    if settings.auth_mode == "oidc" and (settings.session_secret == "development-only-change-me" or not settings.google_client_id or not settings.google_client_secret):
        raise RuntimeError("OIDC mode requires a unique SESSION_SECRET and Google client credentials")
    Base.metadata.create_all(engine)
    # Early demo releases created schemas without Alembic versioning. Preserve
    # those local volumes while formal migrations remain the deployment path.
    audit_columns = {column["name"] for column in inspect(engine).get_columns("audit_events")}
    if "user_id" not in audit_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE audit_events ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_events_user_id ON audit_events (user_id)"))
    if settings.demo_mode:
        with SessionLocal() as db: seed_database(db)

app.include_router(router)
app.include_router(auth_router)
