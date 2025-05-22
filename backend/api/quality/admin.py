"""
Admin configurations for quality improvement models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Count

from .models import (
    QualityAnalysis,
    QualityImprovement,
    ImprovedPrompt,
    RetrievalConfiguration
)


@admin.register(QualityAnalysis)
class QualityAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for QualityAnalysis."""
    
    list_display = (
        'name', 
        'analysis_type', 
        'status',
        'feedback_count', 
        'quality_score_display',
        'date_range', 
        'created_at'
    )
    list_filter = ('status', 'analysis_type')
    search_fields = ('name', 'description', 'summary')
    readonly_fields = (
        'analysis_id', 
        'created_at', 
        'started_at', 
        'completed_at',
        'feedback_count',
        'issues_summary',
        'recommendations_list'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'analysis_id', 'name', 'description', 'analysis_type', 
                'status', 'created_at', 'started_at', 'completed_at'
            )
        }),
        ('Analysis Parameters', {
            'fields': (
                'date_range_start', 'date_range_end', 'feedback_count', 
                'feedback_filter'
            )
        }),
        ('Analysis Results', {
            'fields': (
                'summary', 'quality_score', 'identified_issues', 
                'issue_frequencies', 'primary_issues', 'topic_clusters',
                'difficulty_assessment', 'issues_summary', 'recommendations_list'
            )
        }),
    )
    
    def date_range(self, obj):
        """Display date range in a readable format."""
        return f"{obj.date_range_start.date()} to {obj.date_range_end.date()}"
    date_range.short_description = 'Date Range'
    
    def quality_score_display(self, obj):
        """Display quality score with color coding."""
        if obj.quality_score is None:
            return '-'
        
        score = obj.quality_score
        if score >= 0.8:
            color = 'green'
        elif score >= 0.6:
            color = 'orange'
        else:
            color = 'red'
            
        return format_html(
            '<span style="color: {};">{:.2f}</span>',
            color, score
        )
    quality_score_display.short_description = 'Quality Score'
    
    def issues_summary(self, obj):
        """Display a summary of the top issues."""
        if not obj.primary_issues:
            return '-'
        
        html = '<ul>'
        for issue in obj.primary_issues[:5]:
            html += f'<li>{issue}</li>'
        html += '</ul>'
        
        return format_html(html)
    issues_summary.short_description = 'Top Issues'
    
    def recommendations_list(self, obj):
        """Display related improvement recommendations."""
        recommendations = obj.improvement_recommendations.all()
        if not recommendations:
            return '-'
        
        html = '<ul>'
        for rec in recommendations:
            url = reverse('admin:api_qualityimprovement_change', args=[rec.improvement_id])
            html += f'<li><a href="{url}">{rec.title}</a> ({rec.get_status_display()})</li>'
        html += '</ul>'
        
        return format_html(html)
    recommendations_list.short_description = 'Recommendations'


@admin.register(QualityImprovement)
class QualityImprovementAdmin(admin.ModelAdmin):
    """Admin interface for QualityImprovement."""
    
    list_display = (
        'title',
        'improvement_type',
        'priority',
        'status',
        'created_at', 
        'approval_status',
        'implementation_status'
    )
    list_filter = ('status', 'improvement_type', 'priority')
    search_fields = ('title', 'description', 'expected_impact')
    readonly_fields = (
        'improvement_id', 
        'created_at', 
        'approved_at',
        'implemented_at'
    )
    
    actions = ['approve_improvements', 'implement_improvements']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'improvement_id', 'title', 'description', 'improvement_type',
                'priority', 'status'
            )
        }),
        ('Timing', {
            'fields': (
                'created_at', 'approved_at', 'implemented_at'
            )
        }),
        ('Implementation Details', {
            'fields': (
                'expected_impact', 'implementation_effort', 'impact_score',
                'implementation_details', 'target_issues'
            )
        }),
        ('Results', {
            'fields': (
                'actual_impact', 'impact_metrics', 'before_metrics', 'after_metrics'
            )
        }),
        ('Relations', {
            'fields': (
                'source_analysis', 'created_by', 'approved_by'
            )
        }),
    )
    
    def approval_status(self, obj):
        """Display approval status with details."""
        if obj.status == 'approved' or obj.status == 'implemented' or obj.status == 'reverted':
            return format_html(
                '<span style="color: green;">✓</span> {}'.format(
                    obj.approved_at.strftime('%Y-%m-%d') if obj.approved_at else ''
                )
            )
        elif obj.status == 'rejected':
            return format_html('<span style="color: red;">✗</span>')
        else:
            return format_html('<span style="color: gray;">-</span>')
    approval_status.short_description = 'Approved'
    
    def implementation_status(self, obj):
        """Display implementation status with details."""
        if obj.status == 'implemented':
            return format_html(
                '<span style="color: green;">✓</span> {}'.format(
                    obj.implemented_at.strftime('%Y-%m-%d') if obj.implemented_at else ''
                )
            )
        elif obj.status == 'reverted':
            return format_html('<span style="color: red;">✗ Reverted</span>')
        else:
            return format_html('<span style="color: gray;">-</span>')
    implementation_status.short_description = 'Implemented'
    
    def approve_improvements(self, request, queryset):
        """Action to approve selected improvements."""
        from .services import QualityImprovementService
        
        service = QualityImprovementService()
        count = 0
        
        for improvement in queryset.filter(status='proposed'):
            service.approve_improvement(improvement.improvement_id, request.user)
            count += 1
            
        self.message_user(
            request, 
            f'{count} improvements were successfully approved.'
        )
    approve_improvements.short_description = 'Approve selected improvements'
    
    def implement_improvements(self, request, queryset):
        """Action to implement selected improvements."""
        from .services import QualityImprovementService
        
        service = QualityImprovementService()
        count = 0
        errors = 0
        
        for improvement in queryset.filter(status='approved'):
            try:
                service.implement_improvement(improvement.improvement_id)
                count += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f'Error implementing improvement {improvement.title}: {str(e)}',
                    level='ERROR'
                )
                
        self.message_user(
            request, 
            f'{count} improvements were successfully implemented. {errors} failed.'
        )
    implement_improvements.short_description = 'Implement selected improvements'


@admin.register(ImprovedPrompt)
class ImprovedPromptAdmin(admin.ModelAdmin):
    """Admin interface for ImprovedPrompt."""
    
    list_display = (
        'name',
        'prompt_type',
        'status',
        'version',
        'created_at',
        'avg_quality_score_display',
        'usage_count'
    )
    list_filter = ('status', 'prompt_type')
    search_fields = ('name', 'description', 'prompt_text')
    readonly_fields = (
        'prompt_id', 
        'created_at', 
        'activated_at',
        'usage_count',
        'avg_quality_score',
        'previous_version_link'
    )
    
    actions = ['activate_prompts']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'prompt_id', 'name', 'description', 'prompt_type',
                'status', 'version'
            )
        }),
        ('Prompt Content', {
            'fields': ('prompt_text',)
        }),
        ('Timing', {
            'fields': (
                'created_at', 'activated_at'
            )
        }),
        ('Relations', {
            'fields': (
                'previous_version', 'previous_version_link', 'source_improvement'
            )
        }),
        ('Performance', {
            'fields': (
                'usage_count', 'avg_quality_score', 'performance_metrics',
                'topic_applicability'
            )
        }),
    )
    
    def avg_quality_score_display(self, obj):
        """Display average quality score with color coding."""
        if obj.avg_quality_score is None:
            return '-'
        
        score = obj.avg_quality_score
        if score >= 0.8:
            color = 'green'
        elif score >= 0.6:
            color = 'orange'
        else:
            color = 'red'
            
        return format_html(
            '<span style="color: {};">{:.2f}</span>',
            color, score
        )
    avg_quality_score_display.short_description = 'Quality Score'
    
    def previous_version_link(self, obj):
        """Link to previous version of the prompt."""
        if not obj.previous_version:
            return '-'
        
        url = reverse('admin:api_improvedprompt_change', args=[obj.previous_version.prompt_id])
        return format_html(
            '<a href="{}">{}</a>',
            url, f"{obj.previous_version.name} v{obj.previous_version.version}"
        )
    previous_version_link.short_description = 'Previous Version'
    
    def activate_prompts(self, request, queryset):
        """Action to activate selected prompts."""
        # Group by prompt_type to ensure only one is active per type
        prompt_types = set(queryset.values_list('prompt_type', flat=True))
        
        for prompt_type in prompt_types:
            # Get the most recent prompt of this type from the selection
            latest = queryset.filter(
                prompt_type=prompt_type, 
                status='draft'
            ).order_by('-version').first()
            
            if latest:
                latest.activate()
                
        self.message_user(
            request, 
            f'Activated the latest prompt for each type: {", ".join(prompt_types)}.'
        )
    activate_prompts.short_description = 'Activate selected prompts'


@admin.register(RetrievalConfiguration)
class RetrievalConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for RetrievalConfiguration."""
    
    list_display = (
        'name',
        'status',
        'version',
        'created_at',
        'avg_quality_score_display',
        'usage_count'
    )
    list_filter = ('status',)
    search_fields = ('name', 'description')
    readonly_fields = (
        'config_id', 
        'created_at', 
        'activated_at',
        'usage_count',
        'avg_quality_score',
        'previous_version_link'
    )
    
    actions = ['activate_configurations']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'config_id', 'name', 'description', 'status', 'version'
            )
        }),
        ('Configuration', {
            'fields': ('parameters',)
        }),
        ('Timing', {
            'fields': (
                'created_at', 'activated_at'
            )
        }),
        ('Relations', {
            'fields': (
                'previous_version', 'previous_version_link', 'source_improvement'
            )
        }),
        ('Performance', {
            'fields': (
                'usage_count', 'avg_quality_score', 'performance_metrics',
                'topic_applicability'
            )
        }),
    )
    
    def avg_quality_score_display(self, obj):
        """Display average quality score with color coding."""
        if obj.avg_quality_score is None:
            return '-'
        
        score = obj.avg_quality_score
        if score >= 0.8:
            color = 'green'
        elif score >= 0.6:
            color = 'orange'
        else:
            color = 'red'
            
        return format_html(
            '<span style="color: {};">{:.2f}</span>',
            color, score
        )
    avg_quality_score_display.short_description = 'Quality Score'
    
    def previous_version_link(self, obj):
        """Link to previous version of the configuration."""
        if not obj.previous_version:
            return '-'
        
        url = reverse('admin:api_retrievalconfiguration_change', args=[obj.previous_version.config_id])
        return format_html(
            '<a href="{}">{}</a>',
            url, f"{obj.previous_version.name} v{obj.previous_version.version}"
        )
    previous_version_link.short_description = 'Previous Version'
    
    def activate_configurations(self, request, queryset):
        """Action to activate a selected configuration."""
        # Only activate the most recent configuration
        latest = queryset.filter(status='draft').order_by('-version').first()
        
        if latest:
            latest.activate()
            self.message_user(
                request, 
                f'Activated configuration: {latest.name} v{latest.version}.'
            )
        else:
            self.message_user(
                request,
                'No draft configurations selected.',
                level='WARNING'
            )
    activate_configurations.short_description = 'Activate selected configuration'