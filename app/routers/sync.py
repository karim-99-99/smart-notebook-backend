"""
Sync API endpoints for Week 7 - Cloud Sync functionality
Handles uploading/downloading folders, notes, and images
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Folder, Note, User
from app.utils.security import get_current_user, get_db
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import uuid
import shutil
import logging
import platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])

# Cloud storage configuration
CLOUD_STORAGE_BASE_URL = os.getenv("CLOUD_STORAGE_BASE_URL", "http://localhost:8000/api/storage")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# Normalize paths for Windows compatibility
UPLOAD_FOLDER = os.path.normpath(UPLOAD_FOLDER)
if platform.system() == 'Windows':
    UPLOAD_FOLDER = UPLOAD_FOLDER.replace('/', '\\')
CLOUD_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, "cloud_images")
CLOUD_IMAGES_FOLDER = os.path.normpath(CLOUD_IMAGES_FOLDER)
if platform.system() == 'Windows':
    CLOUD_IMAGES_FOLDER = CLOUD_IMAGES_FOLDER.replace('/', '\\')
os.makedirs(CLOUD_IMAGES_FOLDER, exist_ok=True)


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class FolderSyncRequest(BaseModel):
    """Folder data from mobile app"""
    id: Optional[int] = None  # Local SQLite ID
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    created_at: Optional[int] = None  # Unix timestamp


class NoteSyncRequest(BaseModel):
    """Note data from mobile app"""
    id: Optional[int] = None  # Local SQLite ID
    folder_id: Optional[int] = None
    title: Optional[str] = None
    raw_text: str
    corrected_text: str
    line_count: int = 0
    average_confidence: Optional[str] = None
    lines: Optional[str] = None  # JSON string
    timestamp: Optional[int] = None
    image_url: Optional[str] = None  # If already uploaded


class SyncFoldersRequest(BaseModel):
    """Bulk folder sync request"""
    folders: List[FolderSyncRequest]


class SyncNotesRequest(BaseModel):
    """Bulk note sync request"""
    notes: List[NoteSyncRequest]


class SyncResponse(BaseModel):
    """Response after syncing"""
    success: bool
    message: str
    synced_count: int
    failed_count: int = 0


class DownloadSyncResponse(BaseModel):
    """Complete sync data for download"""
    folders: List[dict]
    notes: List[dict]


# ============================================================================
# Image Upload Endpoint
# ============================================================================

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image to cloud storage.
    Returns the image URL for use in notes.
    
    This is a simple file-based storage. For production, replace with:
    - Supabase Storage
    - AWS S3
    - Google Cloud Storage
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (jpg, png, etc.)"
            )
        
        # Generate unique filename with user ID prefix
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename or 'image.jpg')[1] or '.jpg'
        filename = f"{current_user.id}_{file_id}{file_ext}"
        file_path = os.path.join(CLOUD_IMAGES_FOLDER, filename)
        # Normalize path for Windows compatibility
        file_path = os.path.normpath(file_path)
        if platform.system() == 'Windows':
            file_path = file_path.replace('/', '\\')
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generate public URL
        # In production, this would be your cloud storage URL
        image_url = f"{CLOUD_STORAGE_BASE_URL}/images/{filename}"
        
        logger.info(f"Image uploaded: {filename} for user {current_user.id}")
        
        return {
            "success": True,
            "image_url": image_url,
            "filename": filename,
            "size": os.path.getsize(file_path)
        }
        
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )


# ============================================================================
# Folder Sync Endpoints
# ============================================================================

@router.post("/folders", response_model=SyncResponse)
async def sync_folders(
    request: SyncFoldersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload/sync folders from mobile app to cloud.
    
    This endpoint:
    1. Creates new folders if they don't exist
    2. Updates existing folders if they match by name
    3. Returns sync status
    """
    try:
        synced_count = 0
        failed_count = 0
        
        for folder_data in request.folders:
            try:
                # Check if folder already exists for this user
                existing_folder = db.query(Folder).filter(
                    and_(
                        Folder.user_id == current_user.id,
                        Folder.name == folder_data.name
                    )
                ).first()
                
                if existing_folder:
                    # Update existing folder
                    existing_folder.color = folder_data.color
                    existing_folder.icon = folder_data.icon
                    existing_folder.updated_at = datetime.utcnow()
                    synced_count += 1
                else:
                    # Create new folder
                    new_folder = Folder(
                        user_id=current_user.id,
                        name=folder_data.name,
                        color=folder_data.color,
                        icon=folder_data.icon
                    )
                    db.add(new_folder)
                    synced_count += 1
                
            except Exception as e:
                logger.error(f"Error syncing folder {folder_data.name}: {str(e)}")
                failed_count += 1
        
        db.commit()
        
        return SyncResponse(
            success=True,
            message=f"Synced {synced_count} folders",
            synced_count=synced_count,
            failed_count=failed_count
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in sync_folders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync folders: {str(e)}"
        )


# ============================================================================
# Note Sync Endpoints
# ============================================================================

@router.post("/notes", response_model=SyncResponse)
async def sync_notes(
    request: SyncNotesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload/sync notes from mobile app to cloud.
    
    This endpoint:
    1. Creates new notes
    2. Updates existing notes if they match
    3. Links notes to folders
    4. Stores raw_text and corrected_text for training data
    """
    try:
        synced_count = 0
        failed_count = 0
        
        for note_data in request.notes:
            try:
                # Find folder if folder_id is provided
                folder = None
                if note_data.folder_id:
                    folder = db.query(Folder).filter(
                        and_(
                            Folder.id == note_data.folder_id,
                            Folder.user_id == current_user.id
                        )
                    ).first()
                
                # Check if note already exists (by title + user_id)
                existing_note = None
                if note_data.title:
                    existing_note = db.query(Note).filter(
                        and_(
                            Note.user_id == current_user.id,
                            Note.title == note_data.title,
                            Note.folder_id == (note_data.folder_id if note_data.folder_id else None)
                        )
                    ).first()
                
                if existing_note:
                    # Update existing note
                    existing_note.raw_text = note_data.raw_text
                    existing_note.corrected_text = note_data.corrected_text
                    existing_note.text = note_data.corrected_text  # Legacy field
                    existing_note.folder_id = folder.id if folder else None
                    existing_note.line_count = note_data.line_count
                    existing_note.average_confidence = note_data.average_confidence
                    existing_note.lines = note_data.lines
                    existing_note.image_url = note_data.image_url
                    existing_note.timestamp = note_data.timestamp
                    existing_note.updated_at = datetime.utcnow()
                    existing_note.synced_at = datetime.utcnow()
                    synced_count += 1
                else:
                    # Create new note
                    new_note = Note(
                        user_id=current_user.id,
                        folder_id=folder.id if folder else None,
                        title=note_data.title or "Untitled Note",
                        raw_text=note_data.raw_text,
                        corrected_text=note_data.corrected_text,
                        text=note_data.corrected_text,  # Legacy field
                        line_count=note_data.line_count,
                        average_confidence=note_data.average_confidence,
                        lines=note_data.lines,
                        image_url=note_data.image_url,
                        timestamp=note_data.timestamp,
                        synced_at=datetime.utcnow()
                    )
                    db.add(new_note)
                    synced_count += 1
                
            except Exception as e:
                logger.error(f"Error syncing note: {str(e)}")
                failed_count += 1
        
        db.commit()
        
        return SyncResponse(
            success=True,
            message=f"Synced {synced_count} notes",
            synced_count=synced_count,
            failed_count=failed_count
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in sync_notes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync notes: {str(e)}"
        )


# ============================================================================
# Download Sync Endpoint
# ============================================================================

@router.get("/download", response_model=DownloadSyncResponse)
async def download_sync(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download all user's folders and notes from cloud.
    
    This is used when:
    - User logs in on a new device
    - User wants to sync across devices
    - App needs to restore from cloud
    """
    try:
        # Get all folders for user
        folders = db.query(Folder).filter(
            Folder.user_id == current_user.id
        ).all()
        
        folders_data = [
            {
                "id": folder.id,
                "name": folder.name,
                "color": folder.color,
                "icon": folder.icon,
                "created_at": folder.created_at.isoformat() if folder.created_at else None,
                "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
            }
            for folder in folders
        ]
        
        # Get all notes for user
        notes = db.query(Note).filter(
            Note.user_id == current_user.id
        ).all()
        
        notes_data = [
            {
                "id": note.id,
                "folder_id": note.folder_id,
                "title": note.title,
                "raw_text": note.raw_text,
                "corrected_text": note.corrected_text,
                "text": note.text or note.corrected_text,  # Legacy compatibility
                "line_count": note.line_count,
                "average_confidence": note.average_confidence,
                "lines": note.lines,
                "image_url": note.image_url,
                "timestamp": note.timestamp,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None,
                "synced_at": note.synced_at.isoformat() if note.synced_at else None,
            }
            for note in notes
        ]
        
        logger.info(f"Downloaded {len(folders_data)} folders and {len(notes_data)} notes for user {current_user.id}")
        
        return DownloadSyncResponse(
            folders=folders_data,
            notes=notes_data
        )
        
    except Exception as e:
        logger.error(f"Error downloading sync data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download sync data: {str(e)}"
        )


# ============================================================================
# Health Check for Sync
# ============================================================================

@router.get("/health")
async def sync_health():
    """Health check for sync service"""
    return {
        "status": "ok",
        "service": "sync",
        "storage": "file-based",  # Will be "supabase" or "s3" in production
        "message": "Sync service is running"
    }

