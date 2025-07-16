"""Anonymizer API routes."""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ...core.anonymizer import run_anonymization_job
from ...core.config import Config

router = APIRouter()
config = Config()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file for processing.

    Args:
        file: The uploaded file

    Returns:
        JSON response with upload status and filename
    """
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)

        # Save file to uploads directory
        file_path = uploads_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse(
            content={
                "status": "success",
                "filename": file.filename,
                "message": f"File {file.filename} uploaded successfully",
            }
        )

    except Exception as e:
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
    Anonymize data in a file.

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
        # Parse masking configuration
        try:
            config_dict = json.loads(masking_config)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid masking configuration JSON"
            )

        # Parse anonymization configuration
        if not config_dict:
            raise HTTPException(
                status_code=400, detail="Empty configuration provided"
            )

        # Look for file in uploads directory first, then samples
        uploads_path = Path("uploads") / filename
        samples_path = Path("samples") / filename

        if uploads_path.exists():
            input_path = uploads_path
        elif samples_path.exists():
            input_path = samples_path
        else:
            raise HTTPException(
                status_code=404, detail=f"File not found: {filename}"
            )

        # Generate output filename
        ext = input_path.suffix.lower()
        output_filename = f"anonymized_{input_path.name}"
        output_path = Path("uploads") / output_filename

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
                "input_file": filename,
                "result_file": output_filename,
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
    """Get API status."""
    return {
        "status": "running",
        "version": config.APP_VERSION,
        "samples_dir": config.get_samples_dir(),
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
    }


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
