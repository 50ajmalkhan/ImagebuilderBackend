import os
import base64
import time
from runwayml import RunwayML
from app.core.config import get_settings
from datetime import datetime
from supabase import create_client
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
import json
import asyncio
from typing import Optional
import requests

settings = get_settings()

# Create admin client for storage operations
admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

class RunwayMLService:
    def __init__(self):
        try:
            self.client = RunwayML(api_key=settings.RUNWAY_API_KEY)
            print(f"Initialized RunwayML client with API key: {settings.RUNWAY_API_KEY[:10]}...")
        except Exception as e:
            print(f"Error initializing RunwayML client: {str(e)}")
            raise

    async def generate_video(
        self, 
        prompt: str, 
        user_id: str, 
        reference_image: Optional[UploadFile] = None,
        duration: int = 4,
        fps: int = 30
    ):
        """Generate video from image and prompt."""
        try:
            if not reference_image:
                raise HTTPException(status_code=400, detail="Reference image is required")
            
            if not reference_image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed")
            
            print(f"Processing image: {reference_image.filename} ({reference_image.content_type})")
            
            # Read image content
            content = await reference_image.read()
            print(f"Read image content: {len(content)} bytes")
            
            # Convert to base64
            base64_string = base64.b64encode(content).decode('utf-8')
            print(f"Converted to base64 (first 50 chars): {base64_string[:50]}...")
            
            # Create data URI
            image_data_uri = f"data:{reference_image.content_type};base64,{base64_string}"
            
            try:
                print("Creating image-to-video task...")
                # Create a new image-to-video task
                task = self.client.image_to_video.create(
                    model='gen3a_turbo',
                    prompt_image=image_data_uri,
                    prompt_text=prompt
                )
                
                task_id = task.id
                print(f"Task created with ID: {task_id}")
                
                # Poll the task until it's complete
                print("Polling for task completion...")
                while True:
                    # Wait for ten seconds before polling
                    await asyncio.sleep(10)
                    
                    task = self.client.tasks.retrieve(task_id)
                    print(f"Task status: {task.status}")
                    
                    if task.status == 'FAILED':
                        raise HTTPException(status_code=500, detail=f"Task failed: {task.error}")
                    elif task.status == 'SUCCEEDED':
                        break
                
                print(f"Task completed successfully: {task}")
                
                # Get video URL from task output
                if not task.output or not task.output[0]:
                    raise HTTPException(status_code=500, detail="No video URL in task result")
                
                video_url = task.output[0]  # Get first URL from the list
                print(f"Video URL from Runway: {video_url}")
                
                # Download video
                print("Downloading video...")
                video_response = requests.get(video_url)
                if video_response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Failed to download generated video")
                
                # Upload to Supabase
                print("Uploading video to Supabase...")
                file_name = f"generated/{user_id}/{datetime.now().timestamp()}.mp4"
                try:
                    storage_response = admin_supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                        file_name,
                        video_response.content
                    )
                    print(f"Video upload response: {storage_response}")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")
                
                public_url = admin_supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_name)
                
                # Log generation
                print("Logging generation...")
                generation_id = str(uuid.uuid4())
                log_data = {
                    "id": generation_id,
                    "user_id": user_id,
                    "prompt": prompt,
                    "type": "video",
                    "url": public_url,
                    "status": "success",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                try:
                    admin_supabase.table("generations").insert(log_data).execute()
                except Exception as e:
                    print(f"Warning: Failed to log generation: {str(e)}")
                
                return {
                    "video_url": public_url,
                    "status": "success",
                    "task_id": task_id
                }
                
            except Exception as e:
                print(f"Error during video generation: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Video generation error: {str(e)}")
                
        except HTTPException as he:
            print(f"HTTP Exception: {str(he)}")
            raise
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

runway_service = RunwayMLService() 