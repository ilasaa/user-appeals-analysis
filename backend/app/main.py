from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    analytics,
    appeals,
    categories,
)

app = FastAPI(
    title="Appeals Analysis API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appeals.router)
app.include_router(categories.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"message": "Appeals Analysis API is running"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
