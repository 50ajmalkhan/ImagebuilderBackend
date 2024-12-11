from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from app.schemas.generation import (
    ImageGenerationRequest,
    GenerationResponse,
    GenerationLog
)
from app.services.dalle_service import generate_image
from app.services.runway_service import runway_service
from app.core.dependencies import get_current_user
from datetime import datetime
from typing import List
from fastapi.openapi.models import Response
from fastapi import Body
from supabase import create_client
from app.core.config import get_settings

settings = get_settings()
admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

router = APIRouter()

@router.post("/generate-image", response_model=GenerationResponse)
async def create_image(
    request: ImageGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an image using DALL-E model.
    """
    try:
        image_url = await generate_image(request.prompt, current_user.id)
        return {
            "url": image_url,
            "status": "success",
            "generated_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/generate-video",
    response_model=GenerationResponse,
    summary="Generate a video from image",
    response_description="Returns the URL of the generated video"
)
async def create_video(
    prompt: str = Form(..., description=""),
    reference_image: UploadFile = File(..., description=""),
    current_user: dict = Depends(get_current_user)
):
    try:
        video_url = await runway_service.generate_video(
            prompt,
            current_user.id,
            reference_image
        )
        return {
            "url": video_url,
            "status": "success",
            "generated_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/history",
    response_model=List[GenerationLog],
    summary="Get generation history",
    description="Retrieve the history of all your image and video generations",
    response_description="List of all generations ordered by creation date"
)
async def get_generation_history(current_user: dict = Depends(get_current_user)):
    try:
        response = admin_supabase.table("generations")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .order("created_at", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 