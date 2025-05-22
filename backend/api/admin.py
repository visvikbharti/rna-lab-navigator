"""
Admin interface for the API app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from .models import (
    Document, 
    QueryHistory, 
    Feedback, 
    QueryCache,
    EvaluationSet,
    ReferenceQuestion,
    EvaluationRun,
    QuestionResult,
    Figure
)
from .security.verification import get_verifier


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'author', 'year', 'created_at')
    list_filter = ('doc_type', 'year')
    search_fields = ('title', 'author')
    date_hierarchy = 'created_at'


@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    list_display = ('query_text_short', 'confidence_score', 'created_at')
    search_fields = ('query_text', 'answer')
    date_hierarchy = 'created_at'
    readonly_fields = ('query_text', 'answer', 'confidence_score', 'sources', 'created_at')
    
    def query_text_short(self, obj):
        if len(obj.query_text) > 50:
            return obj.query_text[:50] + "..."
        return obj.query_text
    query_text_short.short_description = "Query"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('rating', 'query_text_short', 'created_at')
    list_filter = ('rating',)
    search_fields = ('comment', 'query_history__query_text')
    date_hierarchy = 'created_at'
    
    def query_text_short(self, obj):
        if len(obj.query_history.query_text) > 50:
            return obj.query_history.query_text[:50] + "..."
        return obj.query_history.query_text
    query_text_short.short_description = "Query"


@admin.register(QueryCache)
class QueryCacheAdmin(admin.ModelAdmin):
    list_display = ('query_text_short', 'hit_count', 'last_accessed')
    list_filter = ('doc_type',)
    search_fields = ('query_text',)
    readonly_fields = ('query_hash', 'hit_count', 'created_at', 'last_accessed')
    
    def query_text_short(self, obj):
        if len(obj.query_text) > 50:
            return obj.query_text[:50] + "..."
        return obj.query_text
    query_text_short.short_description = "Query"


@admin.register(EvaluationSet)
class EvaluationSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'question_count', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Questions"


@admin.register(ReferenceQuestion)
class ReferenceQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'evaluation_set', 'question_type', 'difficulty')
    list_filter = ('question_type', 'difficulty', 'evaluation_set')
    search_fields = ('question_text', 'expected_answer')
    
    def question_text_short(self, obj):
        if len(obj.question_text) > 50:
            return obj.question_text[:50] + "..."
        return obj.question_text
    question_text_short.short_description = "Question"


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = ('evaluation_set', 'run_date', 'status', 'success_rate', 'average_score')
    list_filter = ('status', 'evaluation_set')
    date_hierarchy = 'run_date'
    
    def success_rate(self, obj):
        if obj.total_questions > 0:
            rate = (obj.success_count / obj.total_questions) * 100
            return f"{rate:.1f}%"
        return "N/A"
    success_rate.short_description = "Success Rate"


@admin.register(QuestionResult)
class QuestionResultAdmin(admin.ModelAdmin):
    list_display = ('reference_question_text', 'evaluation_run', 'confidence_score')
    list_filter = ('evaluation_run',)
    
    def reference_question_text(self, obj):
        if len(obj.reference_question.question_text) > 50:
            return obj.reference_question.question_text[:50] + "..."
        return obj.reference_question.question_text
    reference_question_text.short_description = "Question"


@admin.register(Figure)
class FigureAdmin(admin.ModelAdmin):
    list_display = ('figure_preview', 'figure_type', 'document', 'page_number')
    list_filter = ('figure_type', 'document')
    search_fields = ('caption', 'document__title')
    
    def figure_preview(self, obj):
        if obj.file:
            return format_html('<img src="{}" height="50" />', obj.file.url)
        return "No preview"
    figure_preview.short_description = "Preview"


class SecurityAdmin(admin.ModelAdmin):
    """Admin interface for security settings and verification"""
    
    change_list_template = 'admin/security_change_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('security/', self.admin_site.admin_view(self.security_dashboard_view), name='security-dashboard'),
            path('security/verify/', self.admin_site.admin_view(self.verify_security_view), name='verify-security'),
            path('security/settings/', self.admin_site.admin_view(self.security_settings_view), name='security-settings'),
        ]
        return custom_urls + urls
    
    @method_decorator(staff_member_required)
    def security_dashboard_view(self, request):
        """Security dashboard view"""
        context = {
            'title': 'Security Dashboard',
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, 'admin/security_dashboard.html', context)
    
    @method_decorator(staff_member_required)
    def verify_security_view(self, request):
        """Run security verification"""
        verifier = get_verifier()
        report = verifier.generate_report(include_details=True)
        return JsonResponse(report)
    
    @method_decorator(staff_member_required)
    def security_settings_view(self, request):
        """View or update security settings"""
        # Only handle GET for now
        if request.method == 'GET':
            from django.conf import settings
            
            # Get security-related settings
            security_settings = {
                'DEBUG': getattr(settings, 'DEBUG', False),
                'ENABLE_CONNECTION_TIMEOUT': getattr(settings, 'ENABLE_CONNECTION_TIMEOUT', False),
                'CONNECTION_TIMEOUT_SECONDS': getattr(settings, 'CONNECTION_TIMEOUT_SECONDS', 1800),
                'SCAN_REQUESTS_FOR_PII': getattr(settings, 'SCAN_REQUESTS_FOR_PII', True),
                'SCAN_RESPONSES_FOR_PII': getattr(settings, 'SCAN_RESPONSES_FOR_PII', False),
                'AUTO_REDACT_PII': getattr(settings, 'AUTO_REDACT_PII', False),
                'ENABLE_DP_EMBEDDING_PROTECTION': getattr(settings, 'ENABLE_DP_EMBEDDING_PROTECTION', True),
                'DP_EPSILON': getattr(settings, 'DP_EPSILON', 0.1),
                'SECURITY_HEADERS_MONITORING': getattr(settings, 'SECURITY_HEADERS_MONITORING', True),
            }
            
            return JsonResponse(security_settings)
        
        # POST would be handled here to update settings
        return JsonResponse({'error': 'Method not allowed'}, status=405)


# Register the security admin without a model
# Commented out for demo purposes as register_view is not supported
# admin.site.register_view('security', SecurityAdmin.as_view('security'))