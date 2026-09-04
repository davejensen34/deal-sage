import logging, uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.services.seed import seed_database

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
settings=get_settings(); app=FastAPI(title="DealSage API",version="0.1.0",description="Evidence-backed ownership transition research")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.middleware("http")
async def request_context(request:Request,call_next):
    request_id=request.headers.get("x-request-id",str(uuid.uuid4())); response=await call_next(request); response.headers["x-request-id"]=request_id
    logging.info("request_id=%s method=%s path=%s status=%s",request_id,request.method,request.url.path,response.status_code); return response

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    if settings.demo_mode:
        with SessionLocal() as db: seed_database(db)

app.include_router(router)
