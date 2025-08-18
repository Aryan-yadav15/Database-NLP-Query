# Future PDF Upload Endpoint Implementation

## Overview
This file contains the implementation plan for the PDF upload endpoint that will be used to dynamically add DQ rules to ChromaDB.

**Status**: 📋 **DOCUMENTATION ONLY** - Not yet implemented

## Planned Endpoint Implementation

```python
# app/api/v1/endpoints/dq_chroma_genration/upload_endpoint.py

from fastapi import (
    APIRouter, 
    UploadFile, 
    File, 
    Form, 
    Depends, 
    HTTPException,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
import asyncio
import logging
from datetime import datetime

from app.services.dq_rule_manager import DQRuleManager
from app.services.pdf_extraction_service import PDFExtractionService
from app.api.v1.deps import get_dq_rule_manager
from .schemas import (
    PDFUploadResponse, 
    PDFUploadErrorResponse,
    ProcessingStats,
    ProgressUpdate,
    UploadStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dq-rules", tags=["DQ Rules Management"])

# In-memory storage for tracking upload progress
upload_progress_store = {}

class PDFUploadManager:
    """Manages PDF upload operations and progress tracking."""
    
    def __init__(self):
        self.active_uploads = {}
        self.websocket_connections = {}
    
    async def process_pdf_async(
        self,
        upload_id: str,
        file_content: bytes,
        filename: str,
        domain: str,
        sap_module: str,
        batch_size: int,
        overwrite: bool,
        dq_manager: DQRuleManager
    ):
        """Process PDF in background and update progress."""
        try:
            # Update progress: Starting
            await self.update_progress(upload_id, "Starting PDF processing", 0)
            
            # Step 1: Extract text from PDF
            await self.update_progress(upload_id, "Extracting text from PDF", 10)
            pdf_service = PDFExtractionService()
            extracted_text = await pdf_service.extract_text_from_pdf_bytes(file_content)
            
            # Step 2: Parse rules from text
            await self.update_progress(upload_id, "Parsing rules from text", 30)
            rules = await pdf_service.parse_rules_from_text(
                extracted_text, domain, sap_module
            )
            
            # Step 3: Generate embeddings and store in batches
            total_rules = len(rules)
            successful_rules = 0
            duplicates_skipped = 0
            
            for i, batch in enumerate(self._create_batches(rules, batch_size)):
                progress = 40 + (i * 50 / len(list(self._create_batches(rules, batch_size))))
                await self.update_progress(
                    upload_id, 
                    f"Processing batch {i+1}", 
                    progress
                )
                
                batch_result = await dq_manager.batch_add_rules(batch, overwrite)
                successful_rules += batch_result['successful']
                duplicates_skipped += batch_result['duplicates']
            
            # Step 4: Complete
            await self.update_progress(upload_id, "Processing complete", 100)
            
            # Store final results
            final_stats = ProcessingStats(
                filename=filename,
                total_pages=pdf_service.get_page_count(),
                extracted_rules=total_rules,
                successfully_stored=successful_rules,
                duplicates_skipped=duplicates_skipped,
                processing_time_seconds=self._get_processing_time(upload_id),
                batch_count=len(list(self._create_batches(rules, batch_size))),
                collection_total_count=dq_manager.get_collection_count()
            )
            
            self.active_uploads[upload_id] = {
                'status': UploadStatus.SUCCESS,
                'stats': final_stats
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {upload_id}: {str(e)}")
            await self.update_progress(upload_id, f"Error: {str(e)}", 0, UploadStatus.ERROR)
            self.active_uploads[upload_id] = {
                'status': UploadStatus.ERROR,
                'error': str(e)
            }
    
    async def update_progress(
        self, 
        upload_id: str, 
        stage: str, 
        percentage: float, 
        status: UploadStatus = UploadStatus.PROCESSING
    ):
        """Update progress and notify WebSocket clients."""
        progress = ProgressUpdate(
            upload_id=upload_id,
            stage=stage,
            progress_percentage=percentage,
            status=status
        )
        
        # Store progress
        upload_progress_store[upload_id] = progress
        
        # Notify WebSocket clients
        if upload_id in self.websocket_connections:
            websocket = self.websocket_connections[upload_id]
            try:
                await websocket.send_text(progress.json())
            except:
                # Client disconnected
                del self.websocket_connections[upload_id]
    
    def _create_batches(self, rules, batch_size):
        """Create batches of rules for processing."""
        for i in range(0, len(rules), batch_size):
            yield rules[i:i + batch_size]
    
    def _get_processing_time(self, upload_id: str) -> float:
        """Calculate processing time for upload."""
        # Implementation would track start time
        return 0.0

# Global upload manager instance
upload_manager = PDFUploadManager()

@router.post(
    "/upload-pdf",
    response_model=PDFUploadResponse,
    responses={
        400: {"model": PDFUploadErrorResponse},
        500: {"model": PDFUploadErrorResponse}
    },
    summary="Upload PDF with DQ Rules",
    description="""
    Upload a PDF document containing data quality rules.
    The PDF will be processed asynchronously and rules will be extracted,
    validated, and stored in ChromaDB with embeddings.
    
    **Processing Steps:**
    1. Extract text from PDF pages
    2. Parse and validate rule structure
    3. Generate embeddings using nomic-embed-text
    4. Store in ChromaDB in batches
    5. Return processing statistics
    
    **Supported PDF Features:**
    - Text-based PDFs (not image/scanned)
    - Multi-page documents
    - Standard rule formats
    
    **WebSocket Progress Tracking:**
    Use `/upload-progress/{upload_id}` WebSocket endpoint to track real-time progress.
    """
)
async def upload_pdf_rules(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ..., 
        description="PDF file containing DQ rules (max 50MB)"
    ),
    domain: str = Form(
        "General", 
        description="Domain classification for rules"
    ),
    sap_module: str = Form(
        "General", 
        description="SAP module classification"
    ),
    batch_size: int = Form(
        32, 
        ge=1, 
        le=100, 
        description="Number of rules to process per batch"
    ),
    overwrite: bool = Form(
        False, 
        description="Whether to overwrite existing rules with same ID"
    ),
    dq_manager: DQRuleManager = Depends(get_dq_rule_manager)
):
    """Upload and process PDF containing DQ rules."""
    
    # Generate unique upload ID
    upload_id = str(uuid.uuid4())
    
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail="Only PDF files are supported"
            )
        
        # Check file size (50MB limit)
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 50MB limit"
            )
        
        # Initialize upload tracking
        upload_manager.active_uploads[upload_id] = {
            'status': UploadStatus.PROCESSING,
            'filename': file.filename,
            'started_at': datetime.now()
        }
        
        # Start background processing
        background_tasks.add_task(
            upload_manager.process_pdf_async,
            upload_id=upload_id,
            file_content=file_content,
            filename=file.filename,
            domain=domain,
            sap_module=sap_module,
            batch_size=batch_size,
            overwrite=overwrite,
            dq_manager=dq_manager
        )
        
        return PDFUploadResponse(
            status=UploadStatus.PROCESSING,
            message=f"PDF upload started. Use upload_id '{upload_id}' to track progress.",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during PDF upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get(
    "/upload-status/{upload_id}",
    response_model=PDFUploadResponse,
    summary="Get Upload Status",
    description="Retrieve the current status and results of a PDF upload operation."
)
async def get_upload_status(upload_id: str):
    """Get the status of a PDF upload operation."""
    
    if upload_id not in upload_manager.active_uploads:
        raise HTTPException(
            status_code=404,
            detail=f"Upload ID '{upload_id}' not found"
        )
    
    upload_data = upload_manager.active_uploads[upload_id]
    
    if upload_data['status'] == UploadStatus.SUCCESS:
        return PDFUploadResponse(
            status=UploadStatus.SUCCESS,
            message="PDF processed successfully",
            data=upload_data['stats']
        )
    elif upload_data['status'] == UploadStatus.ERROR:
        return PDFUploadResponse(
            status=UploadStatus.ERROR,
            message=f"Processing failed: {upload_data.get('error', 'Unknown error')}",
            data=None
        )
    else:
        return PDFUploadResponse(
            status=UploadStatus.PROCESSING,
            message="PDF is still being processed",
            data=None
        )

@router.websocket("/upload-progress/{upload_id}")
async def upload_progress_websocket(websocket: WebSocket, upload_id: str):
    """WebSocket endpoint for real-time upload progress tracking."""
    await websocket.accept()
    
    try:
        # Register WebSocket connection
        upload_manager.websocket_connections[upload_id] = websocket
        
        # Send initial progress if available
        if upload_id in upload_progress_store:
            progress = upload_progress_store[upload_id]
            await websocket.send_text(progress.json())
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.ping()
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for upload {upload_id}")
    except Exception as e:
        logger.error(f"WebSocket error for upload {upload_id}: {str(e)}")
    finally:
        # Clean up connection
        if upload_id in upload_manager.websocket_connections:
            del upload_manager.websocket_connections[upload_id]

@router.delete(
    "/upload/{upload_id}",
    summary="Cancel Upload",
    description="Cancel an ongoing PDF upload operation."
)
async def cancel_upload(upload_id: str):
    """Cancel an ongoing PDF upload operation."""
    
    if upload_id not in upload_manager.active_uploads:
        raise HTTPException(
            status_code=404,
            detail=f"Upload ID '{upload_id}' not found"
        )
    
    upload_data = upload_manager.active_uploads[upload_id]
    
    if upload_data['status'] != UploadStatus.PROCESSING:
        raise HTTPException(
            status_code=400,
            detail=f"Upload '{upload_id}' is not in progress and cannot be cancelled"
        )
    
    # Mark as cancelled
    upload_manager.active_uploads[upload_id]['status'] = UploadStatus.CANCELLED
    
    # Notify WebSocket clients
    await upload_manager.update_progress(
        upload_id, 
        "Upload cancelled by user", 
        0, 
        UploadStatus.CANCELLED
    )
    
    return {"message": f"Upload '{upload_id}' has been cancelled"}

# Additional utility endpoints

@router.get(
    "/collections/stats",
    summary="Get Collection Statistics",
    description="Get current statistics about the DQ rules ChromaDB collection."
)
async def get_collection_stats(
    dq_manager: DQRuleManager = Depends(get_dq_rule_manager)
):
    """Get statistics about the DQ rules collection."""
    
    stats = dq_manager.get_collection_statistics()
    return {
        "total_rules": stats['total_count'],
        "unique_domains": stats['unique_domains'],
        "unique_sap_modules": stats['unique_modules'],
        "last_updated": stats['last_updated'],
        "collection_name": stats['collection_name']
    }

@router.post(
    "/collections/rebuild",
    summary="Rebuild Collection",
    description="Rebuild the entire ChromaDB collection from the base CSV file."
)
async def rebuild_collection(
    background_tasks: BackgroundTasks,
    dq_manager: DQRuleManager = Depends(get_dq_rule_manager)
):
    """Rebuild the ChromaDB collection from scratch."""
    
    rebuild_id = str(uuid.uuid4())
    
    # Start background rebuild
    background_tasks.add_task(
        dq_manager.rebuild_collection_async,
        rebuild_id
    )
    
    return {
        "message": "Collection rebuild started",
        "rebuild_id": rebuild_id,
        "status": "processing"
    }
```

## Supporting Service Classes

### PDF Extraction Service (Future Implementation)
```python
# app/services/pdf_extraction_service.py

import PyPDF2
import pdfplumber
from typing import List, Dict, Any, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

logger = logging.getLogger(__name__)

class PDFExtractionService:
    """Service for extracting and parsing DQ rules from PDF documents."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.page_count = 0
    
    async def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._extract_text_sync,
            pdf_bytes
        )
    
    def _extract_text_sync(self, pdf_bytes: bytes) -> str:
        """Synchronous text extraction from PDF."""
        try:
            # Use pdfplumber for better text extraction
            import io
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                self.page_count = len(pdf.pages)
                extracted_text = ""
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n\n"
                
                return extracted_text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    async def parse_rules_from_text(
        self, 
        text: str, 
        domain: str, 
        sap_module: str
    ) -> List[Dict[str, Any]]:
        """Parse structured rules from extracted text using pattern matching and LLM."""
        
        # This would use the LLM service to intelligently parse rules
        # For now, showing the structure
        
        rules = []
        
        # Simple pattern-based parsing (would be enhanced with LLM)
        rule_patterns = [
            r"Rule\s+(\w+):\s*(.+?)(?=Rule\s+\w+:|$)",
            r"(\d+)\.\s*(.+?)(?=\d+\.|$)",
            # Add more patterns as needed
        ]
        
        for pattern in rule_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                rule_id = match.group(1).strip()
                description = match.group(2).strip()
                
                if len(description) > 10:  # Basic validation
                    rules.append({
                        "Rule_ID": rule_id,
                        "Description": description,
                        "Domain": domain,
                        "SAP_Module": sap_module,
                        "Quality_Dimension": "Completeness",  # Default
                        "Attribute_Group": "General",  # Default
                        "Data_Type": "Text"  # Default
                    })
        
        return rules
    
    def get_page_count(self) -> int:
        """Get the number of pages processed."""
        return self.page_count
```

## Client Integration Example

### JavaScript/TypeScript Client
```typescript
// client-example.ts

class DQRulesUploadClient {
    private baseUrl: string;
    private websocket: WebSocket | null = null;
    
    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }
    
    async uploadPDF(
        file: File,
        options: {
            domain?: string;
            sapModule?: string;
            batchSize?: number;
            overwrite?: boolean;
        } = {}
    ): Promise<{uploadId: string}> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('domain', options.domain || 'General');
        formData.append('sap_module', options.sapModule || 'General');
        formData.append('batch_size', String(options.batchSize || 32));
        formData.append('overwrite', String(options.overwrite || false));
        
        const response = await fetch(`${this.baseUrl}/dq-rules/upload-pdf`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        return { uploadId: result.upload_id };
    }
    
    connectToProgress(
        uploadId: string,
        onProgress: (progress: any) => void,
        onError: (error: string) => void
    ): void {
        const wsUrl = `ws://${this.baseUrl}/dq-rules/upload-progress/${uploadId}`;
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onmessage = (event) => {
            const progress = JSON.parse(event.data);
            onProgress(progress);
        };
        
        this.websocket.onerror = (error) => {
            onError(`WebSocket error: ${error}`);
        };
        
        this.websocket.onclose = () => {
            console.log('Progress tracking disconnected');
        };
    }
    
    async getUploadStatus(uploadId: string): Promise<any> {
        const response = await fetch(`${this.baseUrl}/dq-rules/upload-status/${uploadId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to get status: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    disconnect(): void {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
}

// Usage example
const client = new DQRulesUploadClient('http://localhost:8000/api/v1');

const fileInput = document.getElementById('pdf-file') as HTMLInputElement;
const progressBar = document.getElementById('progress') as HTMLProgressElement;

fileInput.addEventListener('change', async (event) => {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    
    try {
        // Start upload
        const { uploadId } = await client.uploadPDF(file, {
            domain: 'Finance',
            sapModule: 'FI-GL',
            batchSize: 32
        });
        
        // Track progress
        client.connectToProgress(
            uploadId,
            (progress) => {
                progressBar.value = progress.progress_percentage;
                console.log(`${progress.stage}: ${progress.progress_percentage}%`);
            },
            (error) => {
                console.error('Progress error:', error);
            }
        );
        
        // Poll for final status
        const checkStatus = async () => {
            const status = await client.getUploadStatus(uploadId);
            if (status.status === 'success') {
                console.log('Upload completed!', status.data);
                client.disconnect();
            } else if (status.status === 'error') {
                console.error('Upload failed:', status.message);
                client.disconnect();
            } else {
                // Still processing, check again in 2 seconds
                setTimeout(checkStatus, 2000);
            }
        };
        
        setTimeout(checkStatus, 5000); // Start checking after 5 seconds
        
    } catch (error) {
        console.error('Upload error:', error);
    }
});
```

## Implementation Timeline

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Set up PDF extraction service
- [ ] Implement basic upload endpoint
- [ ] Add progress tracking system
- [ ] Create Pydantic schemas

### Phase 2: Processing Logic (Week 3-4)
- [ ] Implement batch processing
- [ ] Add rule validation
- [ ] Integrate with existing DQ manager
- [ ] Add error handling

### Phase 3: Real-time Features (Week 5-6)
- [ ] WebSocket progress tracking
- [ ] Background task management
- [ ] Upload cancellation
- [ ] Status persistence

### Phase 4: Testing & Documentation (Week 7-8)
- [ ] Comprehensive testing
- [ ] API documentation
- [ ] Client examples
- [ ] Performance optimization

**Note**: This is a planned implementation and requires the migration to nomic-embed-text (Ollama) to be completed first.
