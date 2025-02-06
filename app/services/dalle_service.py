from openai import OpenAI
from app.core.config import get_settings
import requests
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app.models.generation import Generation, GenerationType
from app.services.storage_service import storage_service
from app.services.token_history import token_history_service, TokenActionType
from app.models.user import User
from fastapi import HTTPException

settings = get_settings()
print(f"Initializing OpenAI client with key: {settings.AI_MODEL_KEY[:8]}...")
client = OpenAI(api_key=settings.AI_MODEL_KEY)

async def generate_image(prompt: str, user_id: int, db: Session):
    try:
        # Check if user has enough tokens
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        required_tokens = 15  # Cost for image generation
        if user.tokens < required_tokens:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient tokens. You need {required_tokens} tokens to generate an image, but you only have {user.tokens} tokens."
            )

        print(f"Attempting to generate image with prompt: {prompt}")
        # Generate image using DALL-E
        response = client.images.generate(
            model="dall-e-3",  # Explicitly specify the model
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        print("Image generation response received")
        
        image_url = response.data[0].url
        print(f"Generated image URL: {image_url}")
        
        try:
            # Download the image
            image_response = requests.get(image_url)
            image_data = image_response.content
            
            # Generate file path
            file_path = f"generated/{user_id}/{datetime.now().timestamp()}.png"
            
            # Upload to storage
            storage_url = storage_service.upload_file(
                file_data=image_data,
                file_path=file_path,
                content_type="image/png"
            )
            print(f"File uploaded: {file_path}")
            
            try:
                # Log generation to database
                generation = Generation(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    prompt=prompt,
                    type=GenerationType.IMAGE,
                    url=file_path,
                    status="success"
                )
                db.add(generation)
                
                # Deduct tokens and log token history
                user.tokens -= required_tokens
                token_history_service.create_token_history(
                    db=db,
                    user_id=user_id,
                    tokens=-required_tokens,  # Negative value for consumption
                    action_type=TokenActionType.CONSUMED,
                    description="Image generation",
                    extra_data={"prompt": prompt},
                    generation_url=file_path
                )
                
                db.commit()
                return file_path
                
            except Exception as log_error:
                print(f"Error logging generation: {str(log_error)}")
                db.rollback()
                raise Exception(f"Failed to log generation: {str(log_error)}")
                
        except Exception as storage_error:
            print(f"Error in storage operations: {str(storage_error)}")
            raise Exception(f"Failed to store generated image: {str(storage_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_image: {str(e)}")
        raise Exception(f"Failed to generate image: {str(e)}") 