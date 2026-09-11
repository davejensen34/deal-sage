import logging, uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.auth.routes import router as auth_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.seed import seed_database

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
settings=get_settings(); app=FastAPI(title="DealSage API",version="0.1.0",description="Evidence-backed ownership transition research")
app.add_middleware(SessionMiddleware,secret_key=settings.session_secret,session_cookie="dealsage_session",same_site="lax",https_only=settings.session_cookie_secure,max_age=60*60*12)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.middleware("http")
async def request_context(request:Request,call_next):
    request_id=request.headers.get("x-request-id",str(uuid.uuid4())); response=await call_next(request); response.headers["x-request-id"]=request_id
    logging.info("request_id=%s method=%s path=%s status=%s",request_id,request.method,request.url.path,response.status_code); return response


@app.middleware("http")
async def same_origin_mutation_signal(request: Request, call_next):
    """Require a non-form custom header on cookie-authenticated mutations."""
    if (
        settings.auth_mode == "oidc"
        and request.url.path.startswith("/api/")
        and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and request.headers.get("x-dealsage-csrf") != "1"
    ):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Missing same-origin mutation signal"}, status_code=403)
    return await call_next(request)

@app.on_event("startup")
def startup():
    if settings.auth_mode == "oidc" and (settings.session_secret == "development-only-change-me" or not settings.google_client_id or not settings.google_client_secret):
        raise RuntimeError("OIDC mode requires a unique SESSION_SECRET and Google client credentials")
    if settings.demo_mode:
        with SessionLocal() as db: seed_database(db)

app.include_router(router)
app.include_router(auth_router)
