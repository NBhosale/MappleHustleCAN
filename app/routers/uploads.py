"""
File upload endpoints for attachments, images, and documents
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
from pathlib import Path

from app.db import SessionLocal
from app.utils.deps import get_current_user
from app.utils.storage import save_file
from app.utils.validation import ValidationError

router = APIRouter(prefix="/uploads", tags=["File Uploads"])

# Allowed file types and their max sizes
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf", "text/plain", "application/msword"]
ALLOWED_ATTACHMENT_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5MB


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_file_type(file: UploadFile, allowed_types: List[str]) -> None:
    """Validate file type"""
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(allowed_types)}"
        )


def validate_file_size(file: UploadFile, max_size: int) -> None:
    """Validate file size"""
    # Read file content to check size
    content = file.file.read()
    file.file.seek(0)  # Reset file pointer
    
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB"
        )


# ============================================================================
# PROFILE IMAGE UPLOADS
# ============================================================================

@router.post("/profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """
    Upload profile image for current user
    """
    try:
        # Validate file type and size
        validate_file_type(file, ALLOWED_IMAGE_TYPES)
        validate_file_size(file, MAX_IMAGE_SIZE)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"profile_{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        
        # Save file
        file_path = await save_file(file, f"profiles/{unique_filename}")
        
        # Update user profile (this would be done in a service layer)
        # For now, just return the file path
        
        return {
            "message": "Profile image uploaded successfully",
            "file_path": file_path,
            "file_size": len(await file.read()),
            "content_type": file.content_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# ITEM IMAGE UPLOADS
# ============================================================================

@router.post("/item-images")
async def upload_item_images(
    files: List[UploadFile] = File(...),
    item_id: str = Form(...),
    current_user=Depends(get_current_user),
):
    """
    Upload multiple images for an item
    """
    try:
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 images allowed per item")
        
        uploaded_files = []
        
        for i, file in enumerate(files):
            # Validate file type and size
            validate_file_type(file, ALLOWED_IMAGE_TYPES)
            validate_file_size(file, MAX_IMAGE_SIZE)
            
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"item_{item_id}_{i}_{uuid.uuid4().hex}.{file_extension}"
            
            # Save file
            file_path = await save_file(file, f"items/{unique_filename}")
            
            uploaded_files.append({
                "filename": file.filename,
                "file_path": file_path,
                "file_size": len(await file.read()),
                "content_type": file.content_type,
                "order": i
            })
        
        return {
            "message": f"Successfully uploaded {len(files)} images",
            "item_id": item_id,
            "files": uploaded_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# MESSAGE ATTACHMENTS
# ============================================================================

@router.post("/message-attachments")
async def upload_message_attachments(
    files: List[UploadFile] = File(...),
    message_id: str = Form(...),
    current_user=Depends(get_current_user),
):
    """
    Upload attachments for a message
    """
    try:
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 attachments allowed per message")
        
        uploaded_files = []
        
        for file in files:
            # Validate file type and size
            validate_file_type(file, ALLOWED_ATTACHMENT_TYPES)
            validate_file_size(file, MAX_ATTACHMENT_SIZE)
            
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
            unique_filename = f"msg_{message_id}_{uuid.uuid4().hex}.{file_extension}"
            
            # Save file
            file_path = await save_file(file, f"attachments/{unique_filename}")
            
            uploaded_files.append({
                "filename": file.filename,
                "file_path": file_path,
                "file_size": len(await file.read()),
                "content_type": file.content_type
            })
        
        return {
            "message": f"Successfully uploaded {len(files)} attachments",
            "message_id": message_id,
            "files": uploaded_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# DOCUMENT UPLOADS (Provider Certifications, etc.)
# ============================================================================

@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),  # "certification", "id_verification", etc.
    current_user=Depends(get_current_user),
):
    """
    Upload documents (certifications, ID verification, etc.)
    """
    try:
        # Validate file type and size
        validate_file_type(file, ALLOWED_DOCUMENT_TYPES)
        validate_file_size(file, MAX_DOCUMENT_SIZE)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        unique_filename = f"{document_type}_{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        
        # Save file
        file_path = await save_file(file, f"documents/{document_type}/{unique_filename}")
        
        return {
            "message": "Document uploaded successfully",
            "file_path": file_path,
            "document_type": document_type,
            "file_size": len(await file.read()),
            "content_type": file.content_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# BULK UPLOAD OPERATIONS
# ============================================================================

@router.post("/bulk/items")
async def bulk_upload_item_images(
    files: List[UploadFile] = File(...),
    current_user=Depends(get_current_user),
):
    """
    Bulk upload images for multiple items
    """
    try:
        if len(files) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 files allowed in bulk upload")
        
        uploaded_files = []
        failed_uploads = []
        
        for i, file in enumerate(files):
            try:
                # Validate file type and size
                validate_file_type(file, ALLOWED_IMAGE_TYPES)
                validate_file_size(file, MAX_IMAGE_SIZE)
                
                # Generate unique filename
                file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
                unique_filename = f"bulk_{current_user.id}_{i}_{uuid.uuid4().hex}.{file_extension}"
                
                # Save file
                file_path = await save_file(file, f"bulk/items/{unique_filename}")
                
                uploaded_files.append({
                    "original_filename": file.filename,
                    "file_path": file_path,
                    "file_size": len(await file.read()),
                    "content_type": file.content_type
                })
                
            except Exception as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "message": f"Bulk upload completed. {len(uploaded_files)} successful, {len(failed_uploads)} failed",
            "uploaded_files": uploaded_files,
            "failed_uploads": failed_uploads
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


# ============================================================================
# FILE MANAGEMENT
# ============================================================================

@router.delete("/files/{file_path:path}")
async def delete_file(
    file_path: str,
    current_user=Depends(get_current_user),
):
    """
    Delete an uploaded file
    """
    try:
        # Security check: ensure user can only delete their own files
        if not file_path.startswith(f"profiles/{current_user.id}") and \
           not file_path.startswith(f"items/") and \
           not file_path.startswith(f"attachments/") and \
           not file_path.startswith(f"documents/"):
            raise HTTPException(status_code=403, detail="Not authorized to delete this file")
        
        # Delete file from storage
        full_path = Path(file_path)
        if full_path.exists():
            full_path.unlink()
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="File not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/files/{file_path:path}")
async def get_file_info(
    file_path: str,
    current_user=Depends(get_current_user),
):
    """
    Get file information
    """
    try:
        full_path = Path(file_path)
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        stat = full_path.stat()
        return {
            "file_path": file_path,
            "file_size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")
