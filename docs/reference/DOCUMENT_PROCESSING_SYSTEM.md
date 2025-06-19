# Robust Document Processing System

## Overview

I've built a comprehensive document processing system for the RNA Lab Navigator that handles large, complex documents with streaming processing, OCR capabilities, and real-time progress tracking.

## Key Features

### 1. Advanced Document Processor (`backend/api/ingestion/advanced_processor.py`)

- **Streaming Processing**: Handles large PDFs (200+ pages) without memory issues
- **OCR Support**: Automatic text extraction from scanned documents using pytesseract
- **Multiple Formats**: Supports PDF, DOCX, PPTX, TXT, and MD files
- **Figure Extraction**: Extracts figures and tables with captions
- **Progress Tracking**: Real-time progress updates via WebSocket
- **Error Recovery**: Graceful handling of partial failures

### 2. WebSocket Integration (`backend/api/ingestion/consumers.py`)

- **Real-time Updates**: Live progress tracking during processing
- **Document Validation**: Pre-upload validation with instant feedback
- **Preview Generation**: Quick document preview before full processing
- **Batch Monitoring**: Track multiple document processing simultaneously

### 3. Robust Task System (`backend/api/ingestion/tasks.py`)

- **Retry Logic**: Automatic retry with exponential backoff
- **Partial Recovery**: Batch processing continues despite individual failures
- **Time Limits**: Prevents stuck processes (30min for single, 2hr for batch)
- **Health Monitoring**: Tracks processing health and alerts on issues
- **Cleanup**: Automatic cleanup of temporary files and old data

### 4. REST API (`backend/api/ingestion/views.py`)

- **Single Upload**: `/api/ingestion/upload/`
- **Batch Upload**: `/api/ingestion/batch-upload/`
- **Validation**: `/api/ingestion/validate/`
- **Preview**: `/api/ingestion/preview/`
- **Status Tracking**: `/api/ingestion/status/{processing_id}/`
- **Document Management**: Full CRUD operations on documents

### 5. Frontend Components

#### Document Uploader (`frontend/src/components/DocumentUploader.jsx`)
- Drag-and-drop interface
- Multiple file support
- Real-time validation
- Progress bars for each document
- Error and warning display
- Preview generation

#### Batch Processing Manager (`frontend/src/components/BatchProcessingManager.jsx`)
- Dashboard with statistics
- Active job monitoring
- Processing history
- Cancel and retry functionality
- Detailed progress tracking

## Processing Flow

1. **Upload & Validation**
   - File is uploaded and validated
   - Size, type, and content checks
   - OCR detection for scanned documents

2. **Processing**
   - Document is processed page by page
   - Text extraction with OCR fallback
   - Figure and table extraction
   - Chunking based on document type

3. **Vector Storage**
   - Chunks are embedded and stored in Weaviate
   - Metadata preserved for retrieval
   - Figures indexed separately

4. **Progress Updates**
   - Real-time updates via WebSocket
   - Persistent status in Redis cache
   - Error tracking and recovery

## Configuration

### Backend Requirements
```txt
PyMuPDF==1.23.8          # PDF processing
pytesseract==0.3.10      # OCR support
python-docx==1.1.0       # Word documents
python-pptx==0.6.23      # PowerPoint
python-magic==0.4.27     # File type detection
opencv-python==4.8.1.78  # Image processing
aiofiles==23.2.1         # Async file operations
```

### Environment Setup
```bash
# Install system dependencies
sudo apt-get install tesseract-ocr tesseract-ocr-eng
sudo apt-get install libmagic1

# Install Python packages
pip install -r requirements.txt
```

## Usage Examples

### Single Document Upload
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('metadata', JSON.stringify({
  title: 'RNA Protocol',
  author: 'Dr. Smith',
  doc_type: 'protocol',
  year: 2024
}));
formData.append('options', JSON.stringify({
  enable_ocr: true,
  extract_figures: true
}));

const response = await uploadDocument(formData);
// Connect to WebSocket for progress
const ws = createProcessingWebSocket(response.processing_id, {
  onMessage: (data) => console.log('Progress:', data)
});
```

### Batch Processing
```javascript
const formData = new FormData();
files.forEach(file => formData.append('files', file));
formData.append('metadata_list', JSON.stringify(metadataArray));
formData.append('options', JSON.stringify({
  max_concurrent: 3,
  enable_ocr: true
}));

const response = await uploadBatch(formData);
```

## Error Handling

1. **File-level Errors**: Individual file failures don't stop batch processing
2. **Retry Mechanism**: Failed documents retry up to 3 times
3. **Partial Success**: Batch completes with summary of successes/failures
4. **User Notification**: Real-time error updates via WebSocket

## Performance Optimizations

1. **Streaming**: Large files processed in chunks to avoid memory issues
2. **Concurrent Processing**: Batch files processed in parallel (configurable)
3. **Caching**: Processing status cached for quick retrieval
4. **Async Operations**: Non-blocking file I/O and processing

## Monitoring

- **Health Checks**: Periodic monitoring of processing queue
- **Stuck Detection**: Alerts for processes with no updates
- **Failure Tracking**: Metrics on failure rates and causes
- **Performance Metrics**: Processing times and throughput

## Security

- **File Validation**: Type and size restrictions
- **Virus Scanning**: Optional integration point
- **Access Control**: User authentication required
- **Temporary File Cleanup**: Automatic removal of uploaded files

## Future Enhancements

1. **Additional Formats**: Support for more document types
2. **Language Detection**: Multi-language OCR support
3. **Smart Chunking**: ML-based optimal chunk boundaries
4. **Duplicate Detection**: Prevent re-ingestion of same content
5. **Version Control**: Track document versions and updates