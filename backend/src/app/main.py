from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.api.v1.api_router import api_router



app = FastAPI(
    title="ReSearch Flow API",
    description="Research paper search and management API",
    version="1.0.0"
)

# CORS middleware - IMPORTANT for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fyp-researchflow.vercel.app",
        "http://localhost:5173",  # Vite default
    
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "ReSearch Flow API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
