from django.db import models


class Pipeline(models.Model):
    # Short human-readable identifier used by the frontend, e.g. "PL-05".
    # Distinct from `name`, which is a display label.
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='active')

    def __str__(self):
        return f'{self.code} — {self.name}'


class PipelineSegment(models.Model):
    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE, related_name='segments'
    )
    # Short code scoped to the pipeline, e.g. "SG-12" (combines with the
    # pipeline's code to form the full display id "PL-05-SG-12" — see
    # `full_code` below).
    segment_code = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    environmental_data = models.JSONField(default=dict, blank=True)
    inspection_history = models.JSONField(default=dict, blank=True)
    # Free-text status shown on the segment detail screen, e.g.
    # "Active", "Active — flagged", "Inactive".
    status = models.CharField(max_length=100, default='Active')

    class Meta:
        unique_together = [('pipeline', 'segment_code')]

    def __str__(self):
        return self.full_code

    @property
    def full_code(self):
        """The combined display id used everywhere in the frontend, e.g. 'PL-05-SG-12'."""
        return f'{self.pipeline.code}-{self.segment_code}'


class Incident(models.Model):
    segment = models.ForeignKey(
        PipelineSegment, on_delete=models.CASCADE, related_name='incidents'
    )
    incident_type = models.CharField(max_length=100)
    date = models.DateField()
    # Optional: the frontend's /risk-assess payload doesn't send severity,
    # only type + date, so this can't be required.
    severity = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        unique_together = [('segment', 'incident_type', 'date')]

    def __str__(self):
        return f'{self.incident_type} ({self.segment.full_code})'


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
        return f'{self.segment.full_code} — {self.risk_level} ({self.risk_score})'
