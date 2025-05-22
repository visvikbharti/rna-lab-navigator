"""
Admin interface for the enhanced feedback system.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db.models import Count, Avg, F, Q
import json
import datetime

from .models import (
    EnhancedFeedback,
    FeedbackCategory,
    FeedbackTheme,
    FeedbackAnalysis,
    FeedbackThemeMapping
)


class EnhancedFeedbackAdmin(admin.ModelAdmin):
    """Admin interface for enhanced feedback"""
    
    list_display = ('id', 'rating_display', 'category', 'status', 'query_text_short', 'created_at')
    list_filter = ('rating', 'category', 'status', 'created_at')
    search_fields = ('comment', 'query_history__query_text', 'review_notes')
    readonly_fields = ('created_at', 'reviewed_at', 'system_response_date')
    raw_id_fields = ('query_history', 'user', 'reviewed_by')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('query_history', 'user', 'rating', 'category', 'status', 'created_at')
        }),
        ('Feedback Details', {
            'fields': ('comment', 'specific_issues')
        }),
        ('Detailed Ratings', {
            'fields': ('relevance_rating', 'accuracy_rating', 'completeness_rating',
                      'clarity_rating', 'citation_rating')
        }),
        ('Learning Information', {
            'fields': ('incorrect_sections', 'suggested_answer', 'source_quality_issues')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('System Response', {
            'fields': ('system_response', 'improvement_actions', 'system_response_date')
        }),
    )
    
    def query_text_short(self, obj):
        """Truncate query text for display"""
        return obj.query_history.query_text[:50] + '...' if len(obj.query_history.query_text) > 50 else obj.query_history.query_text
    query_text_short.short_description = 'Query'
    
    def rating_display(self, obj):
        """Display rating with visual indicator"""
        if obj.rating == 'thumbs_up':
            return format_html('<span style="color: green;">👍 Positive</span>')
        elif obj.rating == 'thumbs_down':
            return format_html('<span style="color: red;">👎 Negative</span>')
        return format_html('<span style="color: gray;">⚖️ Neutral</span>')
    rating_display.short_description = 'Rating'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('query_history', 'user', 'reviewed_by')


class FeedbackCategoryAdmin(admin.ModelAdmin):
    """Admin interface for feedback categories"""
    
    list_display = ('name', 'type', 'parent', 'is_active', 'display_order')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'display_order')
    ordering = ('display_order', 'name')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('parent')


class FeedbackThemeMappingInline(admin.TabularInline):
    """Inline admin for feedback theme mappings"""
    
    model = FeedbackThemeMapping
    extra = 0
    readonly_fields = ('mapped_at',)
    raw_id_fields = ('feedback', 'mapped_by')
    

class FeedbackThemeAdmin(admin.ModelAdmin):
    """Admin interface for feedback themes"""
    
    list_display = ('title', 'status', 'priority', 'feedback_count_display', 'assigned_to', 'last_reported')
    list_filter = ('status', 'priority', 'assigned_to')
    search_fields = ('title', 'description', 'solution_notes')
    readonly_fields = ('first_reported', 'last_reported', 'feedback_count')
    inlines = [FeedbackThemeMappingInline]
    date_hierarchy = 'last_reported'
    
    actions = ['mark_investigating', 'mark_implementing', 'mark_resolved']
    
    def feedback_count_display(self, obj):
        """Display feedback count with link to view mappings"""
        url = reverse('admin:api_feedbackthememapping_changelist') + f'?theme__id__exact={obj.id}'
        return format_html('<a href="{}">{} items</a>', url, obj.feedback_count)
    feedback_count_display.short_description = 'Feedback Items'
    
    def mark_investigating(self, request, queryset):
        """Mark selected themes as investigating"""
        queryset.update(status='investigating')
        self.message_user(request, f"{queryset.count()} themes marked as investigating")
    mark_investigating.short_description = "Mark selected themes as investigating"
    
    def mark_implementing(self, request, queryset):
        """Mark selected themes as implementing solution"""
        queryset.update(status='implementing')
        self.message_user(request, f"{queryset.count()} themes marked as implementing")
    mark_implementing.short_description = "Mark selected themes as implementing solution"
    
    def mark_resolved(self, request, queryset):
        """Mark selected themes as resolved"""
        queryset.update(status='resolved', resolution_date=timezone.now())
        self.message_user(request, f"{queryset.count()} themes marked as resolved")
    mark_resolved.short_description = "Mark selected themes as resolved"


class FeedbackAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for feedback analysis"""
    
    list_display = ('analysis_id', 'analysis_date', 'date_range_display', 
                   'total_feedback_analyzed', 'implemented_status')
    list_filter = ('analysis_date', 'implementation_date')
    search_fields = ('analysis_id',)
    readonly_fields = ('analysis_id', 'analysis_date')
    
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis_id', 'date_range_start', 'date_range_end', 'analysis_date',
                      'total_feedback_analyzed', 'positive_feedback_count', 
                      'negative_feedback_count', 'neutral_feedback_count')
        }),
        ('Analysis Results', {
            'fields': ('top_issues', 'category_distribution', 'improvement_opportunities',
                       'trend_analysis', 'recommended_actions', 'priority_areas')
        }),
        ('Implementation', {
            'fields': ('actions_implemented', 'implementation_date', 'implemented_by',
                       'effectiveness_metrics')
        }),
    )
    
    def date_range_display(self, obj):
        """Display date range for analysis"""
        start = obj.date_range_start.strftime('%Y-%m-%d')
        end = obj.date_range_end.strftime('%Y-%m-%d')
        return f"{start} to {end}"
    date_range_display.short_description = 'Date Range'
    
    def implemented_status(self, obj):
        """Display implementation status"""
        if obj.implementation_date:
            return format_html(
                '<span style="color: green;">Implemented on {}</span>',
                obj.implementation_date.strftime('%Y-%m-%d')
            )
        return format_html('<span style="color: orange;">Pending implementation</span>')
    implemented_status.short_description = 'Implementation Status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('implemented_by')


class FeedbackThemeMappingAdmin(admin.ModelAdmin):
    """Admin interface for feedback theme mappings"""
    
    list_display = ('id', 'theme_title', 'feedback_summary', 'relevance_score', 'mapped_at')
    list_filter = ('theme', 'mapped_at')
    search_fields = ('notes', 'feedback__comment', 'theme__title')
    readonly_fields = ('mapped_at',)
    raw_id_fields = ('feedback', 'theme', 'mapped_by')
    
    def theme_title(self, obj):
        """Display theme title with link"""
        url = reverse('admin:api_feedbacktheme_change', args=[obj.theme.id])
        return format_html('<a href="{}">{}</a>', url, obj.theme.title)
    theme_title.short_description = 'Theme'
    
    def feedback_summary(self, obj):
        """Display feedback summary with link"""
        url = reverse('admin:api_enhancedfeedback_change', args=[obj.feedback.id])
        rating = '👍' if obj.feedback.rating == 'thumbs_up' else '👎' if obj.feedback.rating == 'thumbs_down' else '⚖️'
        query = obj.feedback.query_history.query_text[:40] + '...' if len(obj.feedback.query_history.query_text) > 40 else obj.feedback.query_history.query_text
        return format_html('<a href="{}">{} {}</a>', url, rating, query)
    feedback_summary.short_description = 'Feedback'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'feedback', 'theme', 'mapped_by', 'feedback__query_history'
        )


# Register models with the admin site
admin.site.register(EnhancedFeedback, EnhancedFeedbackAdmin)
admin.site.register(FeedbackCategory, FeedbackCategoryAdmin)
admin.site.register(FeedbackTheme, FeedbackThemeAdmin)
admin.site.register(FeedbackAnalysis, FeedbackAnalysisAdmin)
admin.site.register(FeedbackThemeMapping, FeedbackThemeMappingAdmin)