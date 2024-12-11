from openai import OpenAI
from app.core.config import get_settings
import requests
from datetime import datetime
from supabase import create_client
import uuid

settings = get_settings()
print(f"Initializing OpenAI client with key: {settings.AI_MODEL_KEY[:8]}...")
client = OpenAI(api_key=settings.AI_MODEL_KEY)

# Create admin client for storage operations
admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

async def generate_image(prompt: str, user_id: str):
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
            
            # Upload to Supabase storage using admin client
            file_name = f"generated/{user_id}/{datetime.now().timestamp()}.png"
            storage_response = admin_supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                file_name,
                image_data
            )
            print(f"Storage response: {storage_response}")
            
            # Get public URL using admin client
            public_url = admin_supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_name)
            print(f"Public URL: {public_url}")
            
            try:
                # Log generation using admin client
                generation_id = str(uuid.uuid4())
                log_data = {
                    "id": generation_id,
                    "user_id": user_id,
                    "prompt": prompt,
                    "type": "image",
                    "url": public_url,
                    "status": "success",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                print(f"Inserting generation data: {log_data}")
                
                log_response = admin_supabase.table("generations").insert(log_data).execute()
                print(f"Generation log response: {log_response}")
                
                return public_url
            except Exception as log_error:
                print(f"Error logging generation: {str(log_error)}")
                # Even if logging fails, return the URL if we have it
                return public_url
                
        except Exception as storage_error:
            print(f"Error in storage operations: {str(storage_error)}")
            raise Exception(f"Failed to store generated image: {str(storage_error)}")
            
    except Exception as e:
        print(f"Error in generate_image: {str(e)}")
        raise Exception(f"Failed to generate image: {str(e)}") 