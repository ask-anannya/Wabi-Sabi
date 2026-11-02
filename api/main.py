import os
import sys

# The whole codebase uses flat imports (`from routers import ...`, `from
# services import ...`) that assume api/ itself is on sys.path — true when
# run via Docker (WORKDIR=/app=api/, uvicorn's CWD puts it there
# automatically) but not guaranteed by every runtime that might import this
# module directly (e.g. Vercel's Python runtime does not add it).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from routers import auth, health, llm, matches, profile, scan, tts
from utils.exception_handler import ExceptionBase 
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from webhooks import datadog_incident
from datadog_agent import datadog_agent
from contextlib import asynccontextmanager

from utils.cors import get_cors_origins



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application is starting...")
    yield
    print("Application is shutting down...")
    datadog_agent.close_socket()

app = FastAPI(title="WabiSabi LLM Backend with Datadog Observability", 
                version="1.0.0",
                openapi_url="",
                root_path="/api/v1",
                lifespan=lifespan
            )

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llm.router, prefix="/llm")
app.include_router(scan.router)
app.include_router(auth.router)
app.include_router(tts.router)
app.include_router(profile.router)
app.include_router(matches.router)
app.include_router(health.router, prefix="/health")
app.include_router(datadog_incident.router, prefix="/webhooks/datadog")

@app.exception_handler(ExceptionBase)
async def exception_handler(request: Request, exc: ExceptionBase):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message":exc.message},
    )