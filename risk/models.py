from django.db import models


class Pipeline(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class PipelineSegment(models.Model):
    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE, related_name='segments'
    )
    segment_code = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    environmental_data = models.JSONField(default=dict, blank=True)
    inspection_history = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.segment_code


class Incident(models.Model):
    segment = models.ForeignKey(
        PipelineSegment, on_delete=models.CASCADE, related_name='incidents'
    )
    incident_type = models.CharField(max_length=100)
    date = models.DateField()
    severity = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.incident_type} ({self.segment.segment_code})'


class RiskAssessment(models.Model):
    segment = models.ForeignKey(
        PipelineSegment, on_delete=models.CASCADE, related_name='risk_assessments'
    )
    risk_score = models.IntegerField()
    risk_level = models.CharField(max_length=50)
    explanation = models.TextField()
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.segment.segment_code} — {self.risk_level} ({self.risk_score})'
