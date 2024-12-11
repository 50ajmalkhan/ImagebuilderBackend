import requests
from app.core.config import get_settings
from datetime import datetime
from supabase import create_client
import uuid
import os
import aiofiles
from fastapi import UploadFile
import json
import asyncio

settings = get_settings()

# Create admin client for storage operations
admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

class RunwayMLService:
    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        self.api_url = "https://api.runwayml.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _poll_task(self, task_id: str) -> dict:
        """Poll the task until it's complete."""
        while True:
            response = requests.get(
                f"{self.api_url}/tasks/{task_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get task status: {response.text}")
            
            task_data = response.json()
            status = task_data.get("status")
            
            print(f"Task status: {status}")
            
            if status == "SUCCEEDED":
                return task_data
            elif status == "FAILED":
                raise Exception(f"Task failed: {task_data.get('error', 'Unknown error')}")
            
            # Wait for 10 seconds before polling again
            await asyncio.sleep(10)

    async def generate_video(self, prompt: str, user_id: str, reference_image: UploadFile = None):
        try:
            print(f"Attempting to generate video with prompt: {prompt}")
            
            if not reference_image:
                raise Exception("Reference image is required for gen3a_turbo model")
            
            try:
                # Create a temporary directory if it doesn't exist
                os.makedirs("temp", exist_ok=True)
                
                # Save the uploaded file temporarily
                temp_path = f"temp/{reference_image.filename}"
                async with aiofiles.open(temp_path, 'wb') as out_file:
                    content = await reference_image.read()
                    await out_file.write(content)
                
                # Upload reference image to Supabase
                ref_file_name = f"references/{user_id}/{datetime.now().timestamp()}_{reference_image.filename}"
                with open(temp_path, 'rb') as f:
                    ref_response = admin_supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                        ref_file_name,
                        f
                    )
                print(f"Reference image upload response: {ref_response}")
                
                # Clean up temporary file
                os.remove(temp_path)
                
                ref_url = admin_supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(ref_file_name)
                print(f"Reference image URL: {ref_url}")
                
                # Initialize task with gen3a_turbo model
                generation_input = {
                    "model": "gen3a_turbo",
                    "promptImage": ref_url,
                    "promptText": prompt
                }
                
                print("Creating image-to-video task...")
                print(f"Generation input: {json.dumps(generation_input, indent=2)}")
                
                # Create the task
                response = requests.post(
                    f"{self.api_url}/image-to-video",
                    headers=self.headers,
                    json=generation_input
                )
                
                print(f"Task creation response status: {response.status_code}")
                print(f"Task creation response: {response.text}")
                
                if response.status_code != 200:
                    raise Exception(f"Failed to create task: {response.text}")
                
                task_data = response.json()
                task_id = task_data.get("id")
                
                if not task_id:
                    raise Exception("No task ID in response")
                
                print(f"Task created with ID: {task_id}")
                
                # Poll until task is complete
                result = await self._poll_task(task_id)
                
                if not result.get("output") or not result["output"].get("video_url"):
                    raise Exception("No video URL in task result")
                
                video_url = result["output"]["video_url"]
                print(f"Received video URL from Runway: {video_url}")
                
                # Download the video
                print("Downloading video from Runway...")
                video_response = requests.get(video_url)
                if video_response.status_code != 200:
                    raise Exception("Failed to download video from Runway")
                
                video_data = video_response.content
                
                # Upload to Supabase storage
                file_name = f"generated/{user_id}/{datetime.now().timestamp()}.mp4"
                storage_response = admin_supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                    file_name,
                    video_data
                )
                print(f"Video upload response: {storage_response}")
                
                # Get public URL
                public_url = admin_supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_name)
                print(f"Video public URL: {public_url}")
                
                # Log generation
                generation_id = str(uuid.uuid4())
                log_data = {
                    "id": generation_id,
                    "user_id": user_id,
                    "prompt": prompt,
                    "type": "video",
                    "url": public_url,
                    "reference_image_url": ref_url,
                    "status": "success",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                print(f"Inserting generation data: {log_data}")
                
                log_response = admin_supabase.table("generations").insert(log_data).execute()
                print(f"Generation log response: {log_response}")
                
                return public_url
                
            except Exception as e:
                print(f"Error in processing: {str(e)}")
                raise
                
        except Exception as e:
            print(f"Error in generate_video: {str(e)}")
            raise Exception(f"Failed to generate video: {str(e)}")
        finally:
            # Clean up temp directory if it exists
            if os.path.exists("temp"):
                try:
                    for file in os.listdir("temp"):
                        os.remove(os.path.join("temp", file))
                except Exception as e:
                    print(f"Error cleaning up temp files: {str(e)}")

runway_service = RunwayMLService() 