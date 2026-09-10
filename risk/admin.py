from django.contrib import admin

from .models import Incident, Pipeline, PipelineSegment, RiskAssessment

admin.site.register(Pipeline)
admin.site.register(PipelineSegment)
admin.site.register(Incident)
admin.site.register(RiskAssessment)
