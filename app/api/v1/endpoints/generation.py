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
from typing import List, Optional
from fastapi.openapi.models import Response
from fastapi import Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.generation import Generation, GenerationType
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()

@router.post("/generate-image", response_model=GenerationResponse)
async def create_image(
    request: ImageGenerationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an image using DALL-E model.
    """
    try:
        image_url = await generate_image(request.prompt, current_user.id, db)
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        video_url = await runway_service.generate_video(
            prompt,
            current_user.id,
            reference_image,
            db
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
    description="Retrieve the history of all your image and video generations. Use the 'type' parameter to filter by content type (image/video)",
    response_description="List of all generations ordered by creation date"
)
async def get_generation_history(
    current_user: dict = Depends(get_current_user),
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Generation).filter(Generation.user_id == current_user.id)
        
        # Add type filter if specified
        if type:
            if type not in ["image", "video"]:
                raise HTTPException(status_code=400, detail="Type must be either 'image' or 'video'")
            query = query.filter(Generation.type == type)
        
        # Execute query with ordering
        generations = query.order_by(Generation.created_at.desc()).all()
        return generations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 