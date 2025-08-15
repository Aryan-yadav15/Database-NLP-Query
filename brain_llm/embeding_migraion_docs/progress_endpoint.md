# Progress Tracking WebSocket Endpoint

## Real-time Progress Tracking for PDF Uploads

This file contains the WebSocket implementation for tracking PDF upload and processing progress in real-time.

**Status**: 📋 **DOCUMENTATION ONLY** - Not yet implemented

## WebSocket Endpoint Implementation

```python
# app/api/v1/endpoints/dq_chroma_genration/progress_endpoint.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Optional, Set
import asyncio
import json
import logging
from datetime import datetime, timedelta
import uuid

from app.services.dq_rule_manager import DQRuleManager
from app.api.v1.deps import get_dq_rule_manager
from .schemas import ProgressUpdate, UploadStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dq-rules", tags=["DQ Rules Progress Tracking"])

class ProgressTracker:
    """Manages progress tracking for multiple upload operations."""
    
    def __init__(self):
        # Store active WebSocket connections by upload_id
        self.connections: Dict[str, Set[WebSocket]] = {}
        
        # Store progress data
        self.progress_data: Dict[str, ProgressUpdate] = {}
        
        # Track upload metadata
        self.upload_metadata: Dict[str, Dict] = {}
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def add_connection(self, upload_id: str, websocket: WebSocket):
        """Add a WebSocket connection for an upload ID."""
        if upload_id not in self.connections:
            self.connections[upload_id] = set()
        
        self.connections[upload_id].add(websocket)
        logger.info(f"Added WebSocket connection for upload {upload_id}. Total connections: {len(self.connections[upload_id])}")
        
        # Send current progress if available
        if upload_id in self.progress_data:
            try:
                await websocket.send_text(self.progress_data[upload_id].json())
            except Exception as e:
                logger.warning(f"Failed to send initial progress: {e}")
    
    async def remove_connection(self, upload_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if upload_id in self.connections:
            self.connections[upload_id].discard(websocket)
            
            # Clean up if no more connections
            if not self.connections[upload_id]:
                del self.connections[upload_id]
                logger.info(f"Removed all connections for upload {upload_id}")
    
    async def broadcast_progress(self, upload_id: str, progress: ProgressUpdate):
        """Broadcast progress update to all connected clients for an upload."""
        # Store the progress
        self.progress_data[upload_id] = progress
        
        if upload_id not in self.connections:
            return
        
        # Get all connections for this upload
        connections = list(self.connections[upload_id])
        
        # Send to all connections
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_text(progress.json())
            except Exception as e:
                logger.warning(f"Failed to send progress to client: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            await self.remove_connection(upload_id, websocket)
    
    async def set_upload_metadata(self, upload_id: str, metadata: Dict):
        """Set metadata for an upload operation."""
        self.upload_metadata[upload_id] = {
            **metadata,
            'started_at': datetime.now(),
            'last_update': datetime.now()
        }
    
    async def cleanup_old_data(self):
        """Periodically clean up old progress data and metadata."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                # Clean up old progress data
                expired_uploads = [
                    upload_id for upload_id, metadata in self.upload_metadata.items()
                    if metadata.get('last_update', datetime.now()) < cutoff_time
                ]
                
                for upload_id in expired_uploads:
                    # Remove from all tracking structures
                    self.progress_data.pop(upload_id, None)
                    self.upload_metadata.pop(upload_id, None)
                    self.connections.pop(upload_id, None)
                    
                    logger.info(f"Cleaned up expired upload data for {upload_id}")
                
                if expired_uploads:
                    logger.info(f"Cleaned up {len(expired_uploads)} expired uploads")
                    
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    def start_cleanup_task(self):
        """Start the background cleanup task."""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self.cleanup_old_data())
    
    def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

# Global progress tracker instance
progress_tracker = ProgressTracker()

@router.on_event("startup")
async def start_progress_tracker():
    """Start the progress tracker on application startup."""
    progress_tracker.start_cleanup_task()
    logger.info("Progress tracker started")

@router.on_event("shutdown") 
async def stop_progress_tracker():
    """Stop the progress tracker on application shutdown."""
    progress_tracker.stop_cleanup_task()
    logger.info("Progress tracker stopped")

@router.websocket("/upload-progress/{upload_id}")
async def track_upload_progress(websocket: WebSocket, upload_id: str):
    """
    WebSocket endpoint for real-time upload progress tracking.
    
    **Connection Flow:**
    1. Client connects with upload_id
    2. Server sends current progress (if available)
    3. Server streams progress updates as they occur
    4. Connection closes when upload completes or client disconnects
    
    **Message Format:**
    ```json
    {
        "upload_id": "upload_123456789",
        "stage": "Generating embeddings",
        "progress_percentage": 67.5,
        "current_item": "Rule batch 3 of 5", 
        "estimated_time_remaining": 8.2,
        "status": "processing"
    }
    ```
    """
    await websocket.accept()
    
    try:
        # Add this connection to tracking
        await progress_tracker.add_connection(upload_id, websocket)
        
        logger.info(f"WebSocket connected for upload {upload_id}")
        
        # Keep the connection alive
        while True:
            try:
                # Wait for client messages (ping/pong)
                message = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=30.0
                )
                
                # Handle client messages
                try:
                    data = json.loads(message)
                    if data.get('type') == 'ping':
                        await websocket.send_text(json.dumps({'type': 'pong'}))
                except json.JSONDecodeError:
                    # Ignore malformed messages
                    pass
                    
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.ping()
                except:
                    # Connection is broken
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for upload {upload_id}")
    except Exception as e:
        logger.error(f"WebSocket error for upload {upload_id}: {str(e)}")
    finally:
        # Clean up connection
        await progress_tracker.remove_connection(upload_id, websocket)

@router.get(
    "/upload-progress/{upload_id}/current",
    summary="Get Current Progress",
    description="Get the current progress of an upload operation without WebSocket."
)
async def get_current_progress(upload_id: str):
    """Get the current progress state for an upload."""
    
    if upload_id not in progress_tracker.progress_data:
        return {
            "upload_id": upload_id,
            "status": "not_found",
            "message": "No progress data found for this upload ID"
        }
    
    progress = progress_tracker.progress_data[upload_id]
    metadata = progress_tracker.upload_metadata.get(upload_id, {})
    
    return {
        "upload_id": upload_id,
        "progress": progress.dict(),
        "metadata": {
            "started_at": metadata.get('started_at'),
            "last_update": metadata.get('last_update'),
            "filename": metadata.get('filename')
        }
    }

@router.get(
    "/active-uploads",
    summary="List Active Uploads",
    description="Get a list of all currently active upload operations."
)
async def list_active_uploads():
    """List all active upload operations."""
    
    active_uploads = []
    
    for upload_id, metadata in progress_tracker.upload_metadata.items():
        progress = progress_tracker.progress_data.get(upload_id)
        
        upload_info = {
            "upload_id": upload_id,
            "filename": metadata.get('filename', 'Unknown'),
            "started_at": metadata.get('started_at'),
            "last_update": metadata.get('last_update'),
            "connected_clients": len(progress_tracker.connections.get(upload_id, [])),
            "status": progress.status if progress else "unknown",
            "progress_percentage": progress.progress_percentage if progress else 0
        }
        
        active_uploads.append(upload_info)
    
    return {
        "active_uploads": active_uploads,
        "total_count": len(active_uploads)
    }

# Helper functions for use by upload processing logic

async def update_progress(
    upload_id: str,
    stage: str,
    progress_percentage: float,
    current_item: Optional[str] = None,
    estimated_time_remaining: Optional[float] = None,
    status: UploadStatus = UploadStatus.PROCESSING
):
    """
    Helper function to update progress for an upload.
    This is called by the PDF processing logic.
    """
    progress = ProgressUpdate(
        upload_id=upload_id,
        stage=stage,
        progress_percentage=progress_percentage,
        current_item=current_item,
        estimated_time_remaining=estimated_time_remaining,
        status=status
    )
    
    # Update metadata
    if upload_id in progress_tracker.upload_metadata:
        progress_tracker.upload_metadata[upload_id]['last_update'] = datetime.now()
    
    # Broadcast to all connected clients
    await progress_tracker.broadcast_progress(upload_id, progress)

async def set_upload_metadata(upload_id: str, filename: str, **kwargs):
    """Set metadata for an upload operation."""
    metadata = {
        'filename': filename,
        **kwargs
    }
    await progress_tracker.set_upload_metadata(upload_id, metadata)

# Integration with upload processing

class ProgressAwareUploadProcessor:
    """
    Example of how the upload processing logic would integrate
    with the progress tracking system.
    """
    
    def __init__(self, upload_id: str):
        self.upload_id = upload_id
        self.start_time = datetime.now()
    
    async def process_with_progress(
        self,
        pdf_content: bytes,
        filename: str,
        domain: str,
        sap_module: str,
        batch_size: int
    ):
        """Process PDF with progress updates."""
        try:
            # Set initial metadata
            await set_upload_metadata(
                self.upload_id, 
                filename, 
                domain=domain,
                sap_module=sap_module,
                batch_size=batch_size
            )
            
            # Step 1: Text extraction
            await update_progress(
                self.upload_id,
                "Extracting text from PDF",
                5.0,
                f"Processing {filename}"
            )
            
            # Simulate text extraction
            await asyncio.sleep(2)
            extracted_text = "Sample extracted text..."
            
            # Step 2: Rule parsing  
            await update_progress(
                self.upload_id,
                "Parsing rules from text",
                25.0,
                "Analyzing document structure",
                estimated_time_remaining=45.0
            )
            
            # Simulate rule parsing
            await asyncio.sleep(3)
            rules = [{"rule_id": f"rule_{i}", "description": f"Description {i}"} for i in range(50)]
            
            # Step 3: Batch processing
            total_batches = len(rules) // batch_size + (1 if len(rules) % batch_size else 0)
            
            for batch_num in range(total_batches):
                batch_progress = 30 + (batch_num / total_batches) * 60
                remaining_batches = total_batches - batch_num - 1
                estimated_time = remaining_batches * 5.0  # 5 seconds per batch
                
                await update_progress(
                    self.upload_id,
                    f"Processing batch {batch_num + 1} of {total_batches}",
                    batch_progress,
                    f"Generating embeddings for rules {batch_num * batch_size + 1}-{min((batch_num + 1) * batch_size, len(rules))}",
                    estimated_time_remaining=estimated_time
                )
                
                # Simulate batch processing
                await asyncio.sleep(2)
            
            # Step 4: Completion
            await update_progress(
                self.upload_id,
                "Upload completed successfully",
                100.0,
                f"Processed {len(rules)} rules",
                status=UploadStatus.SUCCESS
            )
            
            return {
                "success": True,
                "rules_processed": len(rules),
                "processing_time": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            await update_progress(
                self.upload_id,
                f"Error: {str(e)}",
                0.0,
                "Processing failed",
                status=UploadStatus.ERROR
            )
            raise

# Export for use in other modules
__all__ = [
    'progress_tracker',
    'update_progress', 
    'set_upload_metadata',
    'ProgressAwareUploadProcessor',
    'router'
]
```

## WebSocket Client Examples

### JavaScript Client
```javascript
// progress-client.js

class UploadProgressTracker {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.websocket = null;
        this.uploadId = null;
    }
    
    connect(uploadId, callbacks = {}) {
        this.uploadId = uploadId;
        const wsUrl = `ws://${this.baseUrl}/dq-rules/upload-progress/${uploadId}`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log(`Connected to progress tracking for upload ${uploadId}`);
            if (callbacks.onConnect) callbacks.onConnect();
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const progress = JSON.parse(event.data);
                if (callbacks.onProgress) callbacks.onProgress(progress);
                
                // Auto-disconnect on completion
                if (progress.status === 'success' || progress.status === 'error') {
                    setTimeout(() => this.disconnect(), 2000);
                }
            } catch (e) {
                console.error('Failed to parse progress message:', e);
            }
        };
        
        this.websocket.onclose = () => {
            console.log('Progress tracking disconnected');
            if (callbacks.onDisconnect) callbacks.onDisconnect();
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (callbacks.onError) callbacks.onError(error);
        };
        
        // Send periodic pings
        this.pingInterval = setInterval(() => {
            if (this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({type: 'ping'}));
            }
        }, 25000);
    }
    
    disconnect() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }
        
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
    
    async getCurrentProgress() {
        if (!this.uploadId) return null;
        
        const response = await fetch(
            `${this.baseUrl}/dq-rules/upload-progress/${this.uploadId}/current`
        );
        
        if (response.ok) {
            return await response.json();
        }
        
        throw new Error(`Failed to get progress: ${response.statusText}`);
    }
}

// Usage example
const tracker = new UploadProgressTracker('localhost:8000/api/v1');

tracker.connect('upload_123456789', {
    onConnect: () => {
        console.log('Connected to progress tracking');
    },
    
    onProgress: (progress) => {
        console.log(`${progress.stage}: ${progress.progress_percentage}%`);
        
        // Update UI
        document.getElementById('progress-bar').value = progress.progress_percentage;
        document.getElementById('status-text').textContent = progress.stage;
        
        if (progress.current_item) {
            document.getElementById('current-item').textContent = progress.current_item;
        }
        
        if (progress.estimated_time_remaining) {
            const minutes = Math.floor(progress.estimated_time_remaining / 60);
            const seconds = Math.floor(progress.estimated_time_remaining % 60);
            document.getElementById('time-remaining').textContent = 
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    },
    
    onError: (error) => {
        console.error('Progress tracking error:', error);
        document.getElementById('status-text').textContent = 'Connection error';
    },
    
    onDisconnect: () => {
        console.log('Progress tracking completed');
    }
});
```

### Python Client
```python
# progress_client.py

import asyncio
import websockets
import json
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class UploadProgressClient:
    """Python client for tracking upload progress via WebSocket."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.replace('http://', '').replace('https://', '')
        self.websocket = None
        self.upload_id = None
        
    async def connect(
        self,
        upload_id: str,
        on_progress: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_complete: Optional[Callable] = None
    ):
        """Connect to progress tracking for an upload."""
        self.upload_id = upload_id
        uri = f"ws://{self.base_url}/api/v1/dq-rules/upload-progress/{upload_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                logger.info(f"Connected to progress tracking for upload {upload_id}")
                
                # Send periodic pings
                ping_task = asyncio.create_task(self._send_pings())
                
                try:
                    async for message in websocket:
                        try:
                            progress = json.loads(message)
                            
                            if on_progress:
                                on_progress(progress)
                            
                            # Check for completion
                            if progress.get('status') in ['success', 'error', 'cancelled']:
                                if on_complete:
                                    on_complete(progress)
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse message: {e}")
                            
                finally:
                    ping_task.cancel()
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            if on_error:
                on_error(e)
    
    async def _send_pings(self):
        """Send periodic ping messages to keep connection alive."""
        while True:
            try:
                await asyncio.sleep(25)
                if self.websocket:
                    await self.websocket.send(json.dumps({'type': 'ping'}))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Failed to send ping: {e}")
                break

# Usage example
async def track_upload(upload_id: str):
    client = UploadProgressClient('localhost:8000')
    
    def on_progress(progress):
        print(f"Progress: {progress['stage']} - {progress['progress_percentage']}%")
        if progress.get('current_item'):
            print(f"  Current: {progress['current_item']}")
        if progress.get('estimated_time_remaining'):
            print(f"  ETA: {progress['estimated_time_remaining']:.1f}s")
    
    def on_complete(final_status):
        print(f"Upload completed with status: {final_status['status']}")
    
    def on_error(error):
        print(f"Error: {error}")
    
    await client.connect(upload_id, on_progress, on_error, on_complete)

# Run the client
if __name__ == "__main__":
    upload_id = "upload_123456789"
    asyncio.run(track_upload(upload_id))
```

## Integration Notes

### Backend Integration
1. **Import Progress Functions**: Import `update_progress` and `set_upload_metadata` in upload processing logic
2. **Call at Key Points**: Update progress at major processing stages
3. **Error Handling**: Always update progress on errors with appropriate status
4. **Cleanup**: Progress data auto-expires after 24 hours

### Frontend Integration
1. **Connect Early**: Connect WebSocket immediately after starting upload
2. **Handle Disconnections**: Implement reconnection logic for network issues
3. **UI Updates**: Update progress bars, status text, and ETA displays
4. **Error Display**: Show meaningful error messages to users

### Performance Considerations
1. **Connection Limits**: Monitor concurrent WebSocket connections
2. **Memory Usage**: Progress data is cleaned up automatically
3. **Network Efficiency**: Pings sent every 25 seconds only
4. **Graceful Degradation**: Fallback to polling if WebSocket fails

**Note**: This is a planned implementation that depends on the core PDF upload endpoint being implemented first.
