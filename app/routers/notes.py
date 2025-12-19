from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.models import Note, User
from app.utils.security import get_current_user, get_db
import httpx
import os
import uuid
import shutil
from typing import Optional
import logging
import platform
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from datetime import datetime
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["notes"])

# OCR Service URL - use environment variable or default
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://ocr-service:9000")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# Normalize upload folder path for Windows compatibility
UPLOAD_FOLDER = os.path.normpath(UPLOAD_FOLDER)
if platform.system() == 'Windows':
    UPLOAD_FOLDER = UPLOAD_FOLDER.replace('/', '\\')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Pydantic models for request validation
class WordExportRequest(BaseModel):
    text: str
    title: str = "Smart Notebook Export"


async def call_ocr_service(image_path: str) -> dict:
    """
    Call OCR service to extract text from image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with OCR results (text, lines, etc.)
    """
    try:
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            async with httpx.AsyncClient(timeout=180.0) as client:  # Increased to 3 minutes for large images
                response = await client.post(
                    f"{OCR_SERVICE_URL}/ocr",
                    files=files
                )
                response.raise_for_status()
                return response.json()
    except httpx.TimeoutException:
        logger.error(f"OCR service timeout for image: {image_path}")
        raise HTTPException(
            status_code=504,
            detail="OCR service timeout. Please try again."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"OCR service error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"OCR service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error calling OCR service: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image with OCR: {str(e)}"
        )


@router.post("/ocr", response_model=dict)
async def process_image_with_ocr(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image, extract text using OCR service, and save to database.
    
    Returns:
        {
            "id": note_id,
            "text": "extracted text",
            "lines": ["line1", "line2"],
            "image_path": "path/to/image",
            "user_id": user_id
        }
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (jpg, png, etc.)"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename or 'image.jpg')[1] or '.jpg'
        filename = f"{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # Normalize path for Windows compatibility
        file_path = os.path.normpath(file_path)
        if platform.system() == 'Windows':
            file_path = file_path.replace('/', '\\')
        
        # Save uploaded file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Call OCR service
            logger.info(f"Calling OCR service for image: {filename}")
            ocr_result = await call_ocr_service(file_path)
            
            # Create note in database
            note = Note(
                user_id=current_user.id,
                text=ocr_result.get("full_text", ocr_result.get("text", "")),
                image_path=file_path,
                title=file.filename or "Untitled Note"
            )
            db.add(note)
            db.commit()
            db.refresh(note)
            
            return {
                "id": note.id,
                "text": note.text,
                "lines": ocr_result.get("lines", []),
                "full_text": ocr_result.get("full_text", note.text),
                "image_path": note.image_path,
                "user_id": note.user_id,
                "title": note.title,
                "created_at": note.created_at.isoformat() if note.created_at else None
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions (from OCR service)
            raise
        except Exception as e:
            # Clean up uploaded file on error
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process image: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in OCR endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/", response_model=list)
async def get_notes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notes for the current user."""
    notes = db.query(Note).filter(
        Note.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": note.id,
            "title": note.title,
            "text": note.text,
            "image_path": note.image_path,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None
        }
        for note in notes
    ]


@router.get("/{note_id}", response_model=dict)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific note by ID."""
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {
        "id": note.id,
        "title": note.title,
        "text": note.text,
        "image_path": note.image_path,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None
    }


@router.delete("/{note_id}", response_model=dict)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a note by ID."""
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Delete image file if it exists
    if note.image_path and os.path.exists(note.image_path):
        try:
            os.remove(note.image_path)
        except Exception as e:
            logger.warning(f"Failed to delete image file {note.image_path}: {str(e)}")
    
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully", "id": note_id}


@router.post("/export/word")
async def export_to_word(
    request: WordExportRequest
):
    """
    Export OCR text to a Word document.
    
    Request body:
        {
            "text": "OCR text content",
            "title": "Document title (optional)"
        }
    
    Returns:
        Word document file for download
    """
    try:
        text = request.text
        title = request.title
        # Create a new Document
        doc = Document()
        
        # Add title
        title_paragraph = doc.add_paragraph()
        title_run = title_paragraph.add_run(title)
        title_run.font.size = Pt(18)
        title_run.bold = True
        title_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Add spacing
        doc.add_paragraph()
        
        # Add metadata
        date_paragraph = doc.add_paragraph()
        date_run = date_paragraph.add_run(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        date_run.font.size = Pt(10)
        date_run.italic = True
        date_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        
        doc.add_paragraph()
        doc.add_paragraph("─" * 50)
        doc.add_paragraph()
        
        # Add OCR text content
        # Split by lines to preserve formatting
        lines = text.split('\n')
        for line in lines:
            if line.strip():  # Only add non-empty lines
                p = doc.add_paragraph(line)
                p.style = 'Normal'
                for run in p.runs:
                    run.font.size = Pt(12)
            else:
                doc.add_paragraph()  # Empty line for spacing
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"smart_notebook_{timestamp}.docx"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # Normalize path for Windows compatibility
        file_path = os.path.normpath(file_path)
        if platform.system() == 'Windows':
            file_path = file_path.replace('/', '\\')
        
        # Save document
        doc.save(file_path)
        
        logger.info(f"Word document created: {filename}")
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error creating Word document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Word document: {str(e)}"
        )


class NoteContent(BaseModel):
    title: str
    text: str

class BulkExportRequest(BaseModel):
    notes: list[NoteContent]  # Accept note content directly
    title: str = "Smart Notebook - Multiple Notes"
    format: str = "word"  # "word" or "pdf"


@router.post("/export/bulk")
async def export_bulk_notes(
    request: BulkExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export multiple notes as a single Word or PDF document.
    
    Request body:
        {
            "notes": [
                {"title": "Note 1", "text": "Content..."},
                {"title": "Note 2", "text": "Content..."}
            ],
            "title": "My Notes Collection",
            "format": "word" or "pdf"
        }
    
    Returns:
        Combined document file for download
    """
    try:
        if not request.notes or len(request.notes) == 0:
            raise HTTPException(status_code=400, detail="No notes provided")
        
        # Combine all note text
        combined_text = ""
        for i, note in enumerate(request.notes, 1):
            combined_text += f"\n\n{'='*50}\n"
            combined_text += f"Note {i}: {note.title or 'Untitled'}\n"
            combined_text += f"{'='*50}\n\n"
            combined_text += note.text
            combined_text += "\n\n"
        
        if request.format == "pdf":
            # Export as PDF
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"smart_notebook_bulk_{timestamp}.pdf"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            # Normalize path for Windows compatibility
            file_path = os.path.normpath(file_path)
            if platform.system() == 'Windows':
                file_path = file_path.replace('/', '\\')
            
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor='#000000',
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            story.append(Paragraph(request.title, title_style))
            story.append(Spacer(1, 20))
            
            body_style = ParagraphStyle(
                'BodyStyle',
                parent=styles['Normal'],
                fontSize=12,
                leading=16,
                textColor='#000000',
                fontName='Helvetica'
            )
            
            lines = combined_text.split('\n')
            for line in lines:
                if line.strip():
                    safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(safe_line, body_style))
                    story.append(Spacer(1, 6))
                else:
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Export as Word (default)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"smart_notebook_bulk_{timestamp}.docx"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            # Normalize path for Windows compatibility
            file_path = os.path.normpath(file_path)
            if platform.system() == 'Windows':
                file_path = file_path.replace('/', '\\')
            
            doc = Document()
            
            # Add title
            title_paragraph = doc.add_paragraph()
            title_run = title_paragraph.add_run(request.title)
            title_run.font.size = Pt(18)
            title_run.bold = True
            title_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            doc.add_paragraph()
            
            # Add combined content
            lines = combined_text.split('\n')
            for line in lines:
                if line.strip():
                    p = doc.add_paragraph(line)
                    for run in p.runs:
                        run.font.size = Pt(12)
                else:
                    doc.add_paragraph()
            
            doc.save(file_path)
            
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk export: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create bulk export: {str(e)}"
        )


@router.post("/export/pdf")
async def export_to_pdf(
    request: WordExportRequest  # Reuse same request model
):
    """
    Export OCR text to a PDF document.
    
    Request body:
        {
            "text": "OCR text content",
            "title": "Document title (optional)"
        }
    
    Returns:
        PDF document file for download
    """
    try:
        text = request.text
        title = request.title
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"smart_notebook_{timestamp}.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # Normalize path for Windows compatibility
        file_path = os.path.normpath(file_path)
        if platform.system() == 'Windows':
            file_path = file_path.replace('/', '\\')
        
        # Create PDF document
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#000000',
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#666666',
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Oblique'
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            textColor='#000000',
            fontName='Helvetica'
        )
        
        # Add title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Add metadata
        date_text = f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(date_text, date_style))
        story.append(Spacer(1, 12))
        
        # Add separator line
        story.append(Paragraph("─" * 80, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Add OCR text content
        # Split by lines and preserve formatting
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                # Escape special characters for reportlab
                safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(safe_line, body_style))
                story.append(Spacer(1, 6))
            else:
                story.append(Spacer(1, 12))  # Empty line for spacing
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF document created: {filename}")
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error creating PDF document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create PDF document: {str(e)}"
        )
