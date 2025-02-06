from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Text description of the image you want to generate",
        example="A beautiful sunset over a mountain lake",
        min_length=1
    )

class GenerationResponse(BaseModel):
    url: str = Field(
        ...,
        description="Public URL of the generated content",
        example="https://example.com/storage/v1/object/public/images/generated/123/image.png"
    )
    status: str = Field(
        ...,
        description="Status of the generation",
        example="success"
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when the content was generated"
    )

class GenerationLog(BaseModel):
    id: UUID = Field(
        ...,
        description="Unique identifier for the generation",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    user_id: int = Field(
        ...,
        description="ID of the user who created this generation",
        example="user123"
    )
    prompt: str = Field(
        ...,
        description="The prompt used to generate the content",
        example="A beautiful sunset over a mountain lake"
    )
    type: str = Field(
        ...,
        description="Type of generated content (image or video)",
        example="image"
    )
    url: str = Field(
        ...,
        description="Public URL of the generated content",
        example="https://example.com/storage/v1/object/public/images/generated/123/image.png"
    )
    reference_image_url: Optional[str] = Field(
        None,
        description="URL of the reference image used for video generation",
        example="https://example.com/storage/v1/object/public/images/references/123/ref.png"
    )
    status: str = Field(
        ...,
        description="Status of the generation",
        example="success"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the record was created"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the record was last updated"
    )

    class Config:
        from_attributes = True 