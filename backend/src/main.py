import json
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.auth import AuthService
from src.job_queue import JobQueue
from src.routes.v1 import auth as auth_routes, fields, regions, simulations
from src.store import Store

with open("config.json", "r") as f:
    config = json.load(f)

cors_allow_origins = config.get("cors-allow-origins", ["*"])
if isinstance(cors_allow_origins, str):
    cors_allow_origins = [cors_allow_origins]

store = Store(config["store-type"])
queue = JobQueue(
    os.getenv("TRANS4NUM_ENGINE_JOB_QUEUE_TYPE", config.get("engine-job-queue-type")),
    os.getenv("TRANS4NUM_ENGINE_JOB_QUEUE_URL", config.get("engine-job-queue-url")),
)
auth = AuthService(config)

app = FastAPI(openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}

app.include_router(auth_routes.get_router(auth), prefix="/api/v1")


app.include_router(
    regions.get_router(store),
    prefix="/api/v1",
    dependencies=[Depends(auth.verify_token)],
)
app.include_router(
    fields.get_router(store),
    prefix="/api/v1",
    dependencies=[Depends(auth.verify_token)],
)
app.include_router(
    simulations.get_router(store, queue),
    prefix="/api/v1",
    dependencies=[Depends(auth.verify_token)],
)

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
