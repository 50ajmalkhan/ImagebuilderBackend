from openai import OpenAI
from app.core.config import get_settings
import requests
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app.models.generation import Generation, GenerationType
from app.db.session import s3_client

settings = get_settings()
print(f"Initializing OpenAI client with key: {settings.AI_MODEL_KEY[:8]}...")
client = OpenAI(api_key=settings.AI_MODEL_KEY)

async def generate_image(prompt: str, user_id: int, db: Session):
    try:
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
            
            # Upload to S3
            file_name = f"generated/{user_id}/{datetime.now().timestamp()}.png"
            s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=file_name,
                Body=image_data,
                ContentType="image/png"
            )
            print(f"File uploaded to S3: {file_name}")
            
            # Get public URL
            public_url = f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET_NAME}/{file_name}"
            print(f"Public URL: {public_url}")
            
            try:
                # Log generation to database
                generation = Generation(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    prompt=prompt,
                    type=GenerationType.IMAGE,
                    url=public_url,
                    status="success"
                )
                db.add(generation)
                db.commit()
                
                return public_url
            except Exception as log_error:
                print(f"Error logging generation: {str(log_error)}")
                db.rollback()
                # Even if logging fails, return the URL if we have it
                return public_url
                
        except Exception as storage_error:
            print(f"Error in storage operations: {str(storage_error)}")
            raise Exception(f"Failed to store generated image: {str(storage_error)}")
            
    except Exception as e:
        print(f"Error in generate_image: {str(e)}")
        raise Exception(f"Failed to generate image: {str(e)}") 