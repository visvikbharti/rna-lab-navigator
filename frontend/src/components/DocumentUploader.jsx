import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Upload, File, X, AlertCircle, CheckCircle, Loader2, FileText, Image } from 'lucide-react';
import { uploadDocument, validateDocument, previewDocument } from '../api/ingestion';
import { useWebSocket } from '../hooks/useWebSocket';

const DocumentUploader = ({ onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [processingStatus, setProcessingStatus] = useState({});
  const fileInputRef = useRef(null);
  const dropZoneRef = useRef(null);

  // WebSocket connection for progress updates
  const { connected, subscribe, unsubscribe } = useWebSocket();

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, []);

  const handleFiles = async (fileList) => {
    const newFiles = Array.from(fileList).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
      errors: [],
      warnings: [],
      preview: null
    }));

    setFiles(prev => [...prev, ...newFiles]);

    // Validate files
    for (const fileObj of newFiles) {
      await validateFile(fileObj);
    }
  };

  const validateFile = async (fileObj) => {
    try {
      const formData = new FormData();
      formData.append('file', fileObj.file);

      const validation = await validateDocument(formData);
      
      setFiles(prev => prev.map(f => 
        f.id === fileObj.id 
          ? { 
              ...f, 
              validation,
              status: validation.valid ? 'validated' : 'invalid',
              errors: validation.errors,
              warnings: validation.warnings
            }
          : f
      ));

      // Generate preview if valid
      if (validation.valid) {
        await generatePreview(fileObj);
      }
    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === fileObj.id 
          ? { ...f, status: 'error', errors: [error.message] }
          : f
      ));
    }
  };

  const generatePreview = async (fileObj) => {
    try {
      const formData = new FormData();
      formData.append('file', fileObj.file);
      formData.append('preview_pages', '3');

      const preview = await previewDocument(formData);
      
      setFiles(prev => prev.map(f => 
        f.id === fileObj.id 
          ? { ...f, preview }
          : f
      ));
    } catch (error) {
      console.error('Preview generation failed:', error);
    }
  };

  const uploadFiles = async () => {
    setUploading(true);
    const validFiles = files.filter(f => f.status === 'validated');

    for (const fileObj of validFiles) {
      try {
        // Prepare metadata
        const metadata = {
          title: fileObj.name.replace(/\.[^/.]+$/, ''),
          author: '',
          doc_type: detectDocType(fileObj.name),
          year: new Date().getFullYear()
        };

        // Upload file
        const formData = new FormData();
        formData.append('file', fileObj.file);
        formData.append('metadata', JSON.stringify(metadata));
        formData.append('options', JSON.stringify({
          enable_ocr: true,
          extract_figures: true
        }));

        const response = await uploadDocument(formData);
        const { processing_id, websocket_url } = response;

        // Update file status
        setFiles(prev => prev.map(f => 
          f.id === fileObj.id 
            ? { ...f, status: 'processing', processingId: processing_id }
            : f
        ));

        // Subscribe to WebSocket updates
        if (connected) {
          subscribe(`processing_${processing_id}`, (data) => {
            handleProcessingUpdate(fileObj.id, data);
          });
        }
      } catch (error) {
        setFiles(prev => prev.map(f => 
          f.id === fileObj.id 
            ? { ...f, status: 'error', errors: [error.message] }
            : f
        ));
      }
    }

    setUploading(false);
  };

  const handleProcessingUpdate = (fileId, data) => {
    if (data.type === 'progress') {
      setFiles(prev => prev.map(f => 
        f.id === fileId 
          ? { 
              ...f, 
              progress: data.data.percentage,
              currentStage: data.data.current_stage
            }
          : f
      ));
    } else if (data.type === 'completed') {
      setFiles(prev => prev.map(f => 
        f.id === fileId 
          ? { 
              ...f, 
              status: 'completed',
              progress: 100,
              documentId: data.data.document_id
            }
          : f
      ));

      if (onUploadComplete) {
        onUploadComplete(data.data.document_id);
      }
    } else if (data.type === 'error') {
      setFiles(prev => prev.map(f => 
        f.id === fileId 
          ? { 
              ...f, 
              status: 'error',
              errors: [data.message]
            }
          : f
      ));
    }
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const detectDocType = (filename) => {
    const lower = filename.toLowerCase();
    if (lower.includes('thesis')) return 'thesis';
    if (lower.includes('protocol')) return 'protocol';
    if (lower.includes('inventory')) return 'inventory';
    return 'paper';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Drop Zone */}
      <div
        ref={dropZoneRef}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${dragActive 
            ? 'border-blue-500 bg-blue-50 scale-105' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.pptx,.txt,.md"
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />
        
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700">
          Drop documents here or click to browse
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Supports PDF, DOCX, PPTX, TXT, and MD files up to 200MB
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">
              Files ({files.length})
            </h3>
            {files.some(f => f.status === 'validated') && (
              <button
                onClick={uploadFiles}
                disabled={uploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    <span>Upload All Valid</span>
                  </>
                )}
              </button>
            )}
          </div>

          {files.map((file) => (
            <FileItem 
              key={file.id}
              file={file}
              onRemove={() => removeFile(file.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const FileItem = ({ file, onRemove }) => {
  const getStatusIcon = () => {
    switch (file.status) {
      case 'pending':
        return <File className="h-5 w-5 text-gray-400" />;
      case 'validated':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'invalid':
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      default:
        return null;
    }
  };

  const getFileIcon = () => {
    if (file.type.includes('image')) {
      return <Image className="h-8 w-8 text-gray-400" />;
    }
    return <FileText className="h-8 w-8 text-gray-400" />;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          {getFileIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <p className="text-sm font-medium text-gray-900 truncate">
                {file.name}
              </p>
              {getStatusIcon()}
            </div>
            
            <button
              onClick={onRemove}
              className="ml-4 text-gray-400 hover:text-gray-500"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <p className="text-sm text-gray-500">
            {formatFileSize(file.size)}
          </p>

          {/* Progress Bar */}
          {file.status === 'processing' && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>{file.currentStage || 'Processing'}</span>
                <span>{Math.round(file.progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${file.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Errors and Warnings */}
          {file.errors.length > 0 && (
            <div className="mt-2 text-sm text-red-600">
              {file.errors.map((error, idx) => (
                <p key={idx}>{error}</p>
              ))}
            </div>
          )}
          
          {file.warnings.length > 0 && (
            <div className="mt-2 text-sm text-yellow-600">
              {file.warnings.map((warning, idx) => (
                <p key={idx}>{warning}</p>
              ))}
            </div>
          )}

          {/* Preview */}
          {file.preview && (
            <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
              <p>Pages: {file.preview.page_count}</p>
              {file.preview.figures_found > 0 && (
                <p>Figures: {file.preview.figures_found}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default DocumentUploader;