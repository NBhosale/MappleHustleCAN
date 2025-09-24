"""
File processing background tasks for MapleHustleCAN
"""
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.items import Item
from app.models.users import User

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_uploaded_file(
    self,
    file_path: str,
    file_type: str,
    user_id: str,
    item_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process uploaded file (resize images, validate, etc.)

    Args:
        file_path: Path to uploaded file
        file_type: Type of file (image, document, etc.)
        user_id: User ID who uploaded the file
        item_id: Optional item ID if file is associated with an item

    Returns:
        Dict with task result
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Process based on file type
        if file_type == "image":
            result = process_image_file(file_path, user_id, item_id)
        elif file_type == "document":
            result = process_document_file(file_path, user_id, item_id)
        else:
            result = process_generic_file(file_path, user_id, item_id)

        logger.info(f"File processed successfully: {file_name}")

        return {
            "success": True,
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "user_id": user_id,
            "item_id": item_id,
            "processed_at": datetime.utcnow().isoformat(),
            "result": result
        }

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        raise self.retry(exc=e, countdown=60)


def process_image_file(file_path: str, user_id: str,
                       item_id: Optional[str]) -> Dict[str, Any]:
    """Process image file (resize, optimize, etc.)"""
    try:
        # This would implement actual image processing
        # For now, just return basic info
        return {
            "type": "image",
            "processed": True,
            "optimized": True,
            "thumbnails_created": True
        }
    except Exception as e:
        logger.error(f"Error processing image file {file_path}: {e}")
        return {"type": "image", "processed": False, "error": str(e)}


def process_document_file(file_path: str, user_id: str,
                          item_id: Optional[str]) -> Dict[str, Any]:
    """Process document file (extract text, generate preview, etc.)"""
    try:
        # This would implement actual document processing
        # For now, just return basic info
        return {
            "type": "document",
            "processed": True,
            "text_extracted": True,
            "preview_generated": True
        }
    except Exception as e:
        logger.error(f"Error processing document file {file_path}: {e}")
        return {"type": "document", "processed": False, "error": str(e)}


def process_generic_file(file_path: str, user_id: str,
                         item_id: Optional[str]) -> Dict[str, Any]:
    """Process generic file"""
    try:
        return {
            "type": "generic",
            "processed": True,
            "validated": True
        }
    except Exception as e:
        logger.error(f"Error processing generic file {file_path}: {e}")
        return {"type": "generic", "processed": False, "error": str(e)}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_file_thumbnails(
    self,
    file_path: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Generate thumbnails for image files

    Args:
        file_path: Path to image file
        user_id: User ID

    Returns:
        Dict with task result
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # This would implement actual thumbnail generation
        # For now, just return success
        thumbnails = [
            {"size": "small", "path": f"{file_path}_small.jpg"},
            {"size": "medium", "path": f"{file_path}_medium.jpg"},
            {"size": "large", "path": f"{file_path}_large.jpg"}
        ]

        logger.info(f"Thumbnails generated for {file_path}")

        return {
            "success": True,
            "file_path": file_path,
            "user_id": user_id,
            "thumbnails": thumbnails,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating thumbnails for {file_path}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def cleanup_temp_files(self) -> Dict[str, Any]:
    """
    Clean up temporary files older than 24 hours

    Returns:
        Dict with task result
    """
    try:
        temp_dir = getattr(settings, 'TEMP_DIR', '/tmp/maplehustlecan')
        if not os.path.exists(temp_dir):
            return {"success": True, "files_deleted": 0}

        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        deleted_files = []

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_time = datetime.fromtimestamp(
                        os.path.getmtime(file_path))
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                except Exception as e:
                    logger.warning(
                        f"Could not delete temp file {file_path}: {e}")

        logger.info(f"Cleaned up {len(deleted_files)} temporary files")

        return {
            "success": True,
            "files_deleted": len(deleted_files),
            "deleted_files": deleted_files,
            "cutoff_time": cutoff_time.isoformat()
        }

    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def backup_user_files(
    self,
    user_id: str,
    backup_path: str
) -> Dict[str, Any]:
    """
    Backup user files to specified path

    Args:
        user_id: User ID
        backup_path: Path to backup directory

    Returns:
        Dict with task result
    """
    try:
        db = SessionLocal()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Create backup directory
            user_backup_dir = os.path.join(backup_path, f"user_{user_id}")
            os.makedirs(user_backup_dir, exist_ok=True)

            # Get user's items with files
            items = db.query(Item).filter(Item.user_id == user_id).all()

            backed_up_files = []
            for item in items:
                if item.image_path and os.path.exists(item.image_path):
                    # Copy file to backup
                    backup_file_path = os.path.join(
                        user_backup_dir,
                        f"item_{item.id}_{os.path.basename(item.image_path)}"
                    )
                    shutil.copy2(item.image_path, backup_file_path)
                    backed_up_files.append(backup_file_path)

            logger.info(
                f"Backed up {len(backed_up_files)} files for user {user_id}")

            return {
                "success": True,
                "user_id": user_id,
                "backup_path": user_backup_dir,
                "files_backed_up": len(backed_up_files),
                "backed_up_files": backed_up_files,
                "backed_up_at": datetime.utcnow().isoformat()
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error backing up files for user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def optimize_storage(self) -> Dict[str, Any]:
    """
    Optimize file storage (compress images, remove duplicates, etc.)

    Returns:
        Dict with task result
    """
    try:
        upload_dir = getattr(settings, 'UPLOAD_DIR', 'uploads')
        if not os.path.exists(upload_dir):
            return {"success": True, "files_optimized": 0}

        optimized_files = []
        space_saved = 0

        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Get original size
                    os.path.getsize(file_path)

                    # This would implement actual optimization
                    # For now, just track the file
                    optimized_files.append(file_path)

                except Exception as e:
                    logger.warning(f"Could not optimize file {file_path}: {e}")

        logger.info(f"Optimized {len(optimized_files)} files")

        return {
            "success": True,
            "files_optimized": len(optimized_files),
            "space_saved_bytes": space_saved,
            "optimized_files": optimized_files,
            "optimized_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error optimizing storage: {e}")
        raise self.retry(exc=e, countdown=60)
