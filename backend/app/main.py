from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api

app = FastAPI(title="Slop API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Slop API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 