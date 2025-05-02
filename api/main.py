from fastapi import FastAPI
import uvicorn

from api.database.connection import engine
from api.models.models import Base
from api.routers import auth, users, clubs, events, event_participation

# Create tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="UniVibe API",
    description="API for university club management",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clubs.router)
app.include_router(events.router)
app.include_router(event_participation.router)

@app.get("/")
async def root():
    return {"message": "Welcome to UniVibe API! See /docs for documentation."}

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True) 