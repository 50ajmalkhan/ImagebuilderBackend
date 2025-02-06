from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.generation import Generation, GenerationType
from app.services.dalle_service import generate_image
from app.services.runway_service import runway_service
from app.services.storage_service import storage_service
from app.schemas.generation import (
    ImageGenerationRequest,
    GenerationResponse,
    GenerationLog
)
from datetime import datetime
from app.core.config import get_settings
import os

settings = get_settings()
router = APIRouter()

@router.post("/generate-image", response_model=GenerationResponse)
async def create_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an image using DALL-E model.
    """
    try:
        file_path = await generate_image(request.prompt, current_user.id, db)
        # Get filename from path for content disposition
        filename = os.path.basename(file_path)
        return {
            "url": storage_service.get_signed_url(file_path, display_name=filename),
            "status": "success",
            "generated_at": datetime.now()
        }
    
    except HTTPException as http_error:
        # Re-raise HTTP exceptions with their original status code and detail
        raise http_error
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        file_path = await runway_service.generate_video(
            prompt,
            current_user.id,
            reference_image,
            db
        )
        # Get filename from path for content disposition
        filename = os.path.basename(file_path)
        return {
            "url": storage_service.get_signed_url(file_path, display_name=filename),
            "status": "success",
            "generated_at": datetime.now()
        }
    except HTTPException as http_error:
        # Re-raise HTTP exceptions with their original status code and detail
        raise http_error
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/history",
    response_model=List[GenerationLog],
    summary="Get generation history",
    description="Retrieve the history of all your image and video generations"
)
async def get_generation_history(
    current_user: User = Depends(get_current_user),
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
        
        # Generate signed URLs for all media
        for gen in generations:
            filename = os.path.basename(gen.url)
            gen.url = storage_service.get_signed_url(gen.url, display_name=filename)
            if gen.reference_image_url:
                ref_filename = os.path.basename(gen.reference_image_url)
                gen.reference_image_url = storage_service.get_signed_url(
                    gen.reference_image_url,
                    display_name=ref_filename
                )
        
        return generations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 