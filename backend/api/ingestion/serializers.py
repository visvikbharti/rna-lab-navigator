"""
Serializers for document ingestion API.
"""

from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from ..models import Document, Figure


class DocumentMetadataSerializer(serializers.Serializer):
    """Serializer for document metadata."""
    title = serializers.CharField(max_length=255, required=True)
    author = serializers.CharField(max_length=255, required=False, allow_blank=True)
    year = serializers.IntegerField(min_value=1900, max_value=2100, required=False)
    doc_type = serializers.ChoiceField(
        choices=['paper', 'thesis', 'protocol', 'inventory'],
        default='paper'
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    abstract = serializers.CharField(required=False, allow_blank=True)
    

class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload."""
    file = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'docx', 'pptx', 'txt', 'md']
            )
        ]
    )
    metadata = DocumentMetadataSerializer()
    options = serializers.DictField(required=False, default=dict)
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size
        max_size = 200 * 1024 * 1024  # 200MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of 200MB"
            )
        return value


class BatchUploadSerializer(serializers.Serializer):
    """Serializer for batch document upload."""
    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        max_length=20
    )
    metadata_list = serializers.ListField(
        child=DocumentMetadataSerializer(),
        min_length=1,
        max_length=20
    )
    options = serializers.DictField(required=False, default=dict)
    
    def validate(self, data):
        """Validate that files and metadata lists have same length."""
        if len(data['files']) != len(data['metadata_list']):
            raise serializers.ValidationError(
                "Number of files must match number of metadata entries"
            )
        return data


class ProcessingOptionsSerializer(serializers.Serializer):
    """Serializer for processing options."""
    enable_ocr = serializers.BooleanField(default=True)
    extract_figures = serializers.BooleanField(default=True)
    chunk_size = serializers.IntegerField(min_value=100, max_value=1000, default=400)
    chunk_overlap = serializers.IntegerField(min_value=0, max_value=200, default=100)
    language = serializers.ChoiceField(
        choices=['en', 'es', 'fr', 'de'],
        default='en'
    )


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    figures_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'doc_type', 'author', 'year',
            'created_at', 'updated_at', 'figures_count'
        ]
    
    def get_figures_count(self, obj):
        return obj.figures.count()


class FigureSerializer(serializers.ModelSerializer):
    """Serializer for Figure model."""
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = Figure
        fields = [
            'id', 'figure_id', 'figure_type', 'caption',
            'page_number', 'file', 'document', 'document_title',
            'created_at'
        ]


class ProcessingStatusSerializer(serializers.Serializer):
    """Serializer for processing status."""
    processing_id = serializers.CharField()
    status = serializers.ChoiceField(
        choices=['pending', 'processing', 'completed', 'failed']
    )
    total_pages = serializers.IntegerField()
    processed_pages = serializers.IntegerField()
    total_chunks = serializers.IntegerField()
    processed_chunks = serializers.IntegerField()
    current_stage = serializers.CharField()
    percentage = serializers.FloatField()
    elapsed_time = serializers.FloatField()
    errors = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField())


class ValidationResultSerializer(serializers.Serializer):
    """Serializer for validation results."""
    valid = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField())
    suggestions = serializers.ListField(child=serializers.CharField())


class DocumentPreviewSerializer(serializers.Serializer):
    """Serializer for document preview."""
    title = serializers.CharField()
    page_count = serializers.IntegerField()
    text_preview = serializers.CharField()
    metadata = serializers.DictField()
    figures_found = serializers.IntegerField()