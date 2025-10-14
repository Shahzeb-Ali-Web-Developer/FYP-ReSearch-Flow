from fastapi import APIRouter
from src.app.api.v1.routes.search import router as search_router

from src.app.api.v1.routes.search import router as papers_router


api_router = APIRouter()

api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(papers_router, prefix="/papers", tags=["Papers"])
