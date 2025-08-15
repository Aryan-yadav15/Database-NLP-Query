# PDF Upload Endpoint Schemas

## Request/Response Models for DQ Rules PDF Upload

This file defines the Pydantic schemas used by the PDF upload endpoints for data validation and API documentation.

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum

class UploadStatus(str, Enum):
    """Status enumeration for upload operations."""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    CANCELLED = "cancelled"

class PDFUploadRequest(BaseModel):
    """Schema for PDF upload request parameters."""
    domain: Optional[str] = Field(
        default="General",
        description="Domain classification for the rules",
        example="Finance"
    )
    sap_module: Optional[str] = Field(
        default="General", 
        description="SAP module classification",
        example="FI-GL"
    )
    batch_size: Optional[int] = Field(
        default=32,
        ge=1,
        le=100,
        description="Batch size for processing rules"
    )
    overwrite: Optional[bool] = Field(
        default=False,
        description="Whether to overwrite existing rules with same ID"
    )

    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Batch size must be between 1 and 100')
        return v

class ProcessingStats(BaseModel):
    """Statistics from PDF processing."""
    filename: str = Field(description="Name of the uploaded file")
    total_pages: int = Field(description="Total number of pages in PDF")
    extracted_rules: int = Field(description="Number of rules extracted from PDF")
    successfully_stored: int = Field(description="Number of rules successfully stored")
    duplicates_skipped: int = Field(description="Number of duplicate rules skipped")
    processing_time_seconds: float = Field(description="Total processing time")
    batch_count: int = Field(description="Number of batches processed")
    collection_total_count: int = Field(description="Total count in ChromaDB collection after upload")

class PDFUploadResponse(BaseModel):
    """Schema for PDF upload response."""
    status: UploadStatus
    message: str = Field(description="Human-readable status message")
    data: Optional[ProcessingStats] = Field(default=None)

class ErrorDetails(BaseModel):
    """Detailed error information."""
    error_type: str = Field(description="Type of error that occurred")
    description: str = Field(description="Detailed error description")
    suggestions: List[str] = Field(description="List of suggestions to fix the error")

class PDFUploadErrorResponse(BaseModel):
    """Schema for error responses."""
    status: UploadStatus = UploadStatus.ERROR
    message: str = Field(description="Error message")
    error_details: ErrorDetails

class ProgressUpdate(BaseModel):
    """Schema for progress updates via WebSocket."""
    upload_id: str = Field(description="Unique identifier for the upload")
    stage: str = Field(description="Current processing stage")
    progress_percentage: float = Field(ge=0, le=100, description="Progress percentage")
    current_item: Optional[str] = Field(default=None, description="Currently processing item")
    estimated_time_remaining: Optional[float] = Field(default=None, description="Estimated seconds remaining")
    status: UploadStatus

class RuleValidationResult(BaseModel):
    """Schema for individual rule validation."""
    rule_id: Optional[str]
    domain: str
    description: str
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)

class BatchProcessingResult(BaseModel):
    """Schema for batch processing results."""
    batch_number: int
    batch_size: int
    successful_rules: int
    failed_rules: int
    validation_results: List[RuleValidationResult]
    processing_time_seconds: float

# Example API documentation responses
EXAMPLE_SUCCESS_RESPONSE = {
    "status": "success",
    "message": "PDF processed successfully",
    "data": {
        "filename": "financial_dq_rules.pdf",
        "total_pages": 25,
        "extracted_rules": 147,
        "successfully_stored": 145,
        "duplicates_skipped": 2,
        "processing_time_seconds": 12.5,
        "batch_count": 5,
        "collection_total_count": 720
    }
}

EXAMPLE_ERROR_RESPONSE = {
    "status": "error",
    "message": "Failed to process PDF",
    "error_details": {
        "error_type": "PDFExtractionError", 
        "description": "Unable to extract text from PDF pages 5-7",
        "suggestions": [
            "Ensure PDF is not password protected",
            "Verify PDF contains extractable text (not just images)",
            "Try converting PDF to a newer format"
        ]
    }
}

EXAMPLE_PROGRESS_UPDATE = {
    "upload_id": "upload_123456789",
    "stage": "Generating embeddings",
    "progress_percentage": 67.5,
    "current_item": "Rule batch 3 of 5",
    "estimated_time_remaining": 8.2,
    "status": "processing"
}
```

## Usage Examples

### FastAPI Endpoint Usage
```python
from fastapi import APIRouter, UploadFile, File, Form, Depends
from .schemas import PDFUploadResponse, PDFUploadRequest, PDFUploadErrorResponse

@router.post("/upload-pdf", response_model=PDFUploadResponse, responses={
    400: {"model": PDFUploadErrorResponse},
    500: {"model": PDFUploadErrorResponse}
})
async def upload_pdf_rules(
    file: UploadFile = File(..., description="PDF file containing DQ rules"),
    domain: str = Form("General"),
    sap_module: str = Form("General"), 
    batch_size: int = Form(32),
    overwrite: bool = Form(False)
):
    # Implementation here
    pass
```

### WebSocket Progress Tracking
```python
@router.websocket("/upload-progress/{upload_id}")
async def upload_progress(websocket: WebSocket, upload_id: str):
    await websocket.accept()
    
    # Send progress updates
    progress = ProgressUpdate(
        upload_id=upload_id,
        stage="Extracting text from PDF",
        progress_percentage=25.0,
        status=UploadStatus.PROCESSING
    )
    
    await websocket.send_text(progress.json())
```

## Validation Rules

### File Validation
- **File Type**: Must be PDF (.pdf extension)
- **File Size**: Maximum 50MB
- **File Content**: Must contain extractable text
- **Password Protection**: Not supported

### Rule Validation
- **Rule ID**: Must be unique within domain
- **Description**: Minimum 10 characters
- **Domain**: Valid domain from predefined list
- **SAP Module**: Valid SAP module code

### Processing Constraints
- **Batch Size**: 1-100 rules per batch
- **Concurrent Uploads**: Maximum 3 per user
- **Processing Timeout**: 30 minutes maximum
- **Memory Limit**: 1GB per upload operation
