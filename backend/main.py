from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import init_db
from backend.routers import accounts, parts, part_revisions, files, jobs, geometry, scenes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="3D Shape API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router, prefix="/api/v1")
app.include_router(parts.router, prefix="/api/v1")
app.include_router(part_revisions.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(geometry.router, prefix="/api/v1")
app.include_router(scenes.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
