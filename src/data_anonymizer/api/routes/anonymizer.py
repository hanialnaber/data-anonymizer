"""Anonymizer API routes with enhanced security."""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ...core.anonymizer import run_anonymization_job
from ...core.config import Config
from ...core.security import DataValidator, security_manager

router = APIRouter()
config = Config()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file for processing with enhanced security validation.

    Args:
        file: The uploaded file

    Returns:
        JSON response with upload status and filename
    """
    try:
        # Validate file security
        temp_path = Path("temp") / file.filename
        temp_path.parent.mkdir(exist_ok=True)

        # Save file temporarily for validation
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file security
        validation_result = security_manager.validate_file_security(
            str(temp_path), max_size_mb=config.MAX_FILE_SIZE
        )

        if not validation_result["valid"]:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"File validation failed: {'; '.join(validation_result['issues'])}",
            )

        # Sanitize filename
        sanitized_filename = security_manager.sanitize_filename(file.filename)

        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)

        # Move file to uploads directory with sanitized name
        final_path = uploads_dir / sanitized_filename
        shutil.move(str(temp_path), str(final_path))

        # Register for cleanup
        security_manager.register_temp_file(str(final_path))

        # Generate audit log
        audit_log = security_manager.generate_audit_log(
            "file_upload",
            {
                "original_filename": file.filename,
                "sanitized_filename": sanitized_filename,
                "file_size_mb": validation_result["size_mb"],
                "warnings": validation_result["warnings"],
            },
        )

        return JSONResponse(
            content={
                "status": "success",
                "filename": sanitized_filename,
                "message": f"File {sanitized_filename} uploaded successfully",
                "file_size_mb": validation_result["size_mb"],
                "warnings": validation_result["warnings"],
                "audit_id": audit_log["hash"],
            }
        )

    except Exception as e:
        # Clean up any temp files
        if "temp_path" in locals():
            temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.post("/anonymize")
async def anonymize_data(
    background_tasks: BackgroundTasks,
    filename: str = Form(...),
    output_format: str = Form(...),
    masking_config: str = Form(...),
    selected_sheet: Optional[str] = Form(None),
):
    """
    Anonymize data in a file with enhanced security and validation.

    Args:
        background_tasks: FastAPI background tasks
        filename: Name of the input file
        output_format: Desired output format (will be inferred from filename)
        masking_config: JSON string containing masking configuration
        selected_sheet: Optional sheet name for Excel files

    Returns:
        JSON response with processing status and result file name
    """
    try:
        # Validate and parse masking configuration
        try:
            config_dict = json.loads(masking_config)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid masking configuration JSON"
            )

        # Validate anonymization configuration
        validation_issues = DataValidator.validate_anonymization_config(config_dict)
        if validation_issues:
            raise HTTPException(
                status_code=400,
                detail=f"Configuration validation failed: {'; '.join(validation_issues)}",
            )

        # Sanitize filename
        sanitized_filename = security_manager.sanitize_filename(filename)

        # Look for file in uploads directory first, then samples
        uploads_path = Path("uploads") / sanitized_filename
        samples_path = Path("samples") / sanitized_filename

        if uploads_path.exists():
            input_path = uploads_path
        elif samples_path.exists():
            input_path = samples_path
        else:
            raise HTTPException(
                status_code=404, detail=f"File not found: {sanitized_filename}"
            )

        # Additional security validation on input file
        validation_result = security_manager.validate_file_security(str(input_path))
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Input file validation failed: {'; '.join(validation_result['issues'])}",
            )

        # Generate secure output filename
        ext = input_path.suffix.lower()
        output_filename = (
            f"anonymized_{security_manager.generate_session_id()[:8]}_{input_path.name}"
        )
        output_filename = security_manager.sanitize_filename(output_filename)
        output_path = Path("uploads") / output_filename

        # Register output file for cleanup
        security_manager.register_temp_file(str(output_path))

        # Generate audit log
        audit_log = security_manager.generate_audit_log(
            "anonymization_started",
            {
                "input_file": sanitized_filename,
                "output_file": output_filename,
                "config": config_dict,
                "selected_sheet": selected_sheet,
            },
        )

        # Add background task for anonymization
        background_tasks.add_task(
            run_anonymization_job,
            str(input_path),
            str(output_path),
            ext.replace(".", ""),
            masking_config,
            selected_sheet,
        )

        return JSONResponse(
            content={
                "status": "processing",
                "message": "Anonymization job started",
                "result_file": output_filename,
                "audit_id": audit_log["hash"],
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """Get API status with security information."""
    return {
        "status": "running",
        "version": config.APP_VERSION,
        "samples_dir": config.get_samples_dir(),
        "security_features": {
            "file_validation": True,
            "auto_cleanup": config.AUTO_CLEANUP_ENABLED,
            "max_file_size_mb": config.MAX_FILE_SIZE,
            "supported_algorithms": ["sha256", "sha512"],
            "privacy_methods": [
                "hash",
                "mask",
                "pseudonymize",
                "substitute",
                "shuffle",
                "perturb",
                "generalize_numeric",
                "generalize_date",
                "anonymize_email",
                "anonymize_phone",
                "anonymize_ssn",
                "k_anonymity",
                "differential_privacy",
            ],
        },
    }


@router.post("/cleanup")
async def cleanup_temp_files():
    """Clean up temporary files (admin endpoint)."""
    try:
        cleaned_files = security_manager.cleanup_temp_files(
            config.TEMP_FILE_RETENTION_HOURS
        )
        return JSONResponse(
            content={
                "status": "success",
                "message": f"Cleaned up {len(cleaned_files)} temporary files",
                "cleaned_files": cleaned_files,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")


@router.get("/samples")
async def list_samples():
    """List available sample files."""
    try:
        samples_dir = Path("samples")
        if not samples_dir.exists():
            return []

        files = []
        for file_path in samples_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".csv", ".xlsx"]:
                files.append(file_path.name)

        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing samples: {str(e)}")


@router.post("/generate-samples")
async def generate_samples():
    """Generate sample data files."""
    try:
        from ...utils.data_generator import generate_sample_data

        results = generate_sample_data()
        return JSONResponse(
            content={
                "status": "success",
                "message": "Sample files generated successfully",
                "files": list(results.keys()),
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating samples: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a file from the uploads directory.

    Args:
        filename: Name of the file to download

    Returns:
        File response with the requested file
    """
    # Look for file in uploads directory first, then samples
    uploads_path = Path("uploads") / filename
    samples_path = Path("samples") / filename

    if uploads_path.exists():
        file_path = uploads_path
    elif samples_path.exists():
        file_path = samples_path
    else:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    return FileResponse(
        path=str(file_path), filename=filename, media_type="application/octet-stream"
    )
