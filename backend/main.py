from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    from backend.watchers.watcher_manager import stop_all

    stop_all()


app = FastAPI(title="CV Tracker & Smart ATS Matcher", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "CV Tracker API"}


from backend.routers import auth, cv_files, export, folders, job_descriptions, matching, websocket

app.include_router(auth.router)
app.include_router(job_descriptions.router)
app.include_router(folders.router)
app.include_router(cv_files.router)
app.include_router(matching.router)
app.include_router(export.router)
app.include_router(websocket.router)
