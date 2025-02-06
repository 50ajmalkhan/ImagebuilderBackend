from app.core.config import get_settings
from app.db.session import s3_client
from datetime import timedelta
import os
import urllib.parse
from fastapi import HTTPException

settings = get_settings()

class StorageService:
    def __init__(self):
        self.s3_client = s3_client
        self.bucket_name = settings.S3_BUCKET_NAME
        self.project_id = settings.S3_ENDPOINT.split('/')[2].split('.')[0]

    def get_signed_url(self, file_path: str, display_name: str = None, expiration: int = 3600) -> str:
        """Generate a signed URL with content disposition"""
        try:
            params = {
                "Bucket": self.bucket_name,
                "Key": file_path,
            }

            if display_name:
                encoded_display_name = urllib.parse.quote(display_name, encoding="utf-8")
                params["ResponseContentDisposition"] = f"attachment; filename={encoded_display_name}"

            url = self.s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params=params,
                ExpiresIn=expiration
            )

            if not url:
                raise HTTPException(status_code=500, detail="Failed to generate signed URL")

            url = url.replace(
                settings.S3_ENDPOINT,
                f"https://{self.project_id}.supabase.co/storage/v1/s3"
            )

            return url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {str(e)}")

    def upload_file(self, file_data: bytes, file_path: str, content_type: str = "application/octet-stream") -> str:
        """Upload a file to storage and return its path"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_data,
                ContentType=content_type
            )
            return file_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

storage_service = StorageService() 