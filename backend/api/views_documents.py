"""
Views for document management and preview functionality.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import Document
from .serializers import DocumentPreviewSerializer
from .ingestion.embeddings_utils import get_weaviate_client


class DocumentPreviewView(APIView):
    """
    API view for retrieving document previews.
    Extracts relevant chunks from Weaviate to create a preview.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, document_id):
        """
        Get a preview of a document with relevant snippets.
        
        Args:
            document_id: ID of the document to preview
            
        Returns:
            Document metadata with preview text
        """
        # Get the document
        document = get_object_or_404(Document, id=document_id)
        
        # Get chunks from Weaviate
        client = get_weaviate_client()
        
        try:
            # Query weaviate for chunks from this document
            result = (
                client.query
                .get("Document", ["content", "chunk_id", "metadata"])
                .with_where({
                    "path": ["document_id"],
                    "operator": "Equal",
                    "valueString": str(document_id)
                })
                .with_limit(5)  # Get a few chunks for preview
                .do()
            )
            
            chunks = result.get("data", {}).get("Get", {}).get("Document", [])
            
            # Create preview text from chunks
            preview_text = ""
            if chunks:
                # Sort chunks by chunk_id to maintain order
                sorted_chunks = sorted(chunks, key=lambda x: x.get("chunk_id", 0))
                
                # Concatenate content with ellipses between chunks
                for i, chunk in enumerate(sorted_chunks):
                    if i > 0:
                        preview_text += "\n...\n"
                    preview_text += chunk.get("content", "")
                
                # Limit preview length
                if len(preview_text) > 1500:
                    preview_text = preview_text[:1500] + "..."
            else:
                preview_text = "No content available for preview."
            
            # Serialize and return
            serializer = DocumentPreviewSerializer(document)
            data = serializer.data
            data["preview_text"] = preview_text
            
            return Response(data)
            
        except Exception as e:
            return Response(
                {"error": f"Error retrieving document preview: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )