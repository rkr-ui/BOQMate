from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
import os
import uuid
import json
from datetime import datetime
from typing import List
from pathlib import Path

from auth import get_current_user
from services.openai_service import BOQGenerator
from services.excel_service import ExcelExporter
from database import db
from security import security_manager

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

@router.post("/api/generate-boq")
async def generate_boq(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    categories: str = None  # Comma-separated list of categories
):
    """
    Upload a file and generate BOQ using OpenAI GPT-4o
    """
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Create user-specific directory
        user_dir = UPLOADS_DIR / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = user_dir / f"{file_id}_{file.filename}"
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Generate file hash for integrity
        file_hash = db.get_file_hash(content)
        
        # Save file metadata to database securely
        if not db.insert_file(file_id, user_id, file.filename, str(file_path), file_hash, len(content)):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file metadata"
            )
        
        # Parse selected categories
        selected_categories = []
        if categories:
            selected_categories = [cat.strip() for cat in categories.split(',') if cat.strip()]
        
        # Generate BOQ using OpenAI
        boq_generator = BOQGenerator()
        boq_items = boq_generator.generate_boq(content, file.filename, selected_categories)
        
        # Validate BOQ data
        if not boq_generator.validate_boq_data(boq_items):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generated BOQ data is invalid"
            )
        
        # Update database with BOQ data securely
        if not db.update_file_boq(file_id, json.dumps(boq_items)):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save BOQ data"
            )
        
        return boq_items
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )

@router.get("/api/categories")
async def get_categories():
    """
    Get available construction categories for BOQ generation
    """
    try:
        boq_generator = BOQGenerator()
        return boq_generator.get_available_categories()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )

@router.get("/api/files")
async def list_files(user_id: str = Depends(get_current_user)):
    """
    List all files for the authenticated user
    """
    try:
        files_data = db.get_user_files(user_id)
        files = []
        for row in files_data:
            files.append({
                "id": row["id"],
                "filename": row["filename"],
                "uploaded_at": row["uploaded_at"],
                "boq_data": json.loads(row["boq_data"]) if row["boq_data"] else None
            })
        return files
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch files: {str(e)}"
        )

@router.get("/api/files/{file_id}/download")
async def download_file(file_id: str, user_id: str = Depends(get_current_user)):
    """
    Download a file (only if it belongs to the user)
    """
    try:
        file_data = db.get_file_by_id(file_id, user_id)
        
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        file_path = Path(file_data["filepath"])
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=file_data["filename"],
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.get("/api/files/{file_id}/boq")
async def download_boq(file_id: str, user_id: str = Depends(get_current_user)):
    """
    Download BOQ data as Excel file
    """
    try:
        file_data = db.get_file_by_id(file_id, user_id)
        
        if not file_data or not file_data["boq_data"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BOQ data not found"
            )
        
        # Parse BOQ data
        boq_data = json.loads(file_data["boq_data"])
        
        # Create Excel file
        excel_exporter = ExcelExporter()
        excel_content = excel_exporter.create_boq_excel(boq_data, file_data["filename"])
        
        # Create response with Excel file
        from fastapi.responses import Response
        
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={file_data['filename']}_BOQ.xlsx"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate BOQ: {str(e)}"
        ) 