"""
Storage API endpoint for serving uploaded images
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import logging
import platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storage", tags=["storage"])

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# Normalize paths for Windows compatibility
UPLOAD_FOLDER = os.path.normpath(UPLOAD_FOLDER)
if platform.system() == 'Windows':
    UPLOAD_FOLDER = UPLOAD_FOLDER.replace('/', '\\')
CLOUD_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, "cloud_images")
CLOUD_IMAGES_FOLDER = os.path.normpath(CLOUD_IMAGES_FOLDER)
if platform.system() == 'Windows':
    CLOUD_IMAGES_FOLDER = CLOUD_IMAGES_FOLDER.replace('/', '\\')


@router.get("/images/{filename}")
async def get_image(filename: str):
    """
    Serve uploaded images from cloud storage.
    
    In production with Supabase/S3, this would redirect to the cloud URL.
    For now, serves files from local storage.
    """
    try:
        file_path = os.path.join(CLOUD_IMAGES_FOLDER, filename)
        # Normalize path for Windows compatibility
        file_path = os.path.normpath(file_path)
        if platform.system() == 'Windows':
            file_path = file_path.replace('/', '\\')
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Determine content type from extension
        ext = os.path.splitext(filename)[1].lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        media_type = content_type_map.get(ext, 'image/jpeg')
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve image: {str(e)}"
        )

