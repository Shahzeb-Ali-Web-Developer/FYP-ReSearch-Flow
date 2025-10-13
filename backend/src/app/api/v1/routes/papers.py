from fastapi import APIRouter

router = APIRouter()

@router.get("/papers")
async def get_papers():
    return {"message": "Papers endpoint"}

# Add more endpoints here