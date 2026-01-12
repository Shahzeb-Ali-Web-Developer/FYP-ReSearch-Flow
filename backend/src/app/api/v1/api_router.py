from fastapi import APIRouter
from src.app.api.v1.routes.search import router as search_router
from src.app.api.v1.routes.papers import router as papers_router
from src.app.api.v1.routes.citation import router as citation_router
from src.app.api.v1.routes.arxiv import router as arxiv_router
from src.app.api.v1.routes.core import router as core_router
from src.app.api.v1.routes.pmc import router as pmc_router
from src.app.api.v1.routes.semantic_scholar import router as semantic_scholar_router
from src.app.api.v1.routes.google_scholar import router as google_scholar_router


api_router = APIRouter()

api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(papers_router, prefix="/papers", tags=["Papers"])
api_router.include_router(citation_router, prefix="/citation", tags=["Citation Network"])
api_router.include_router(arxiv_router, prefix="/arxiv", tags=["arXiv Search & Summarization"])
api_router.include_router(core_router, prefix="/core", tags=["CORE Search & Summarization"])
api_router.include_router(pmc_router, prefix="/pmc", tags=["PMC Search & Summarization"])
api_router.include_router(semantic_scholar_router, prefix="/semantic-scholar", tags=["Semantic Scholar Search & Summarization"])
api_router.include_router(google_scholar_router, prefix="/google-scholar", tags=["Google Scholar Search & Summarization"])
