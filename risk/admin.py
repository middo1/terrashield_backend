from django.contrib import admin

from .models import Incident, Pipeline, PipelineSegment, RiskAssessment


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'location', 'status']
    search_fields = ['code', 'name']


@admin.register(PipelineSegment)
class PipelineSegmentAdmin(admin.ModelAdmin):
    list_display = ['full_code', 'pipeline', 'status', 'latitude', 'longitude']
    search_fields = ['segment_code', 'pipeline__code', 'pipeline__name']
    list_filter = ['status']


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['segment', 'incident_type', 'date', 'severity']
    list_filter = ['incident_type']


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ['segment', 'risk_level', 'risk_score', 'created_at']
    list_filter = ['risk_level']
    readonly_fields = ['created_at']
