from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.app.api.v1.api_router import api_router
from src.app.db.client_neo4j import neo4j_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    neo4j_client.connect()
    yield
    # Shutdown
    neo4j_client.disconnect()


app = FastAPI(
    title="ReSearch Flow API",
    description="Research paper search and management API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - IMPORTANT for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fyp-re-search-flow.vercel.app",
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
