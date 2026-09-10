from rest_framework import serializers

from .models import Incident, Pipeline, PipelineSegment, RiskAssessment


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'location', 'status']


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ['id', 'incident_type', 'date', 'severity']


class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = [
            'id', 'risk_score', 'risk_level', 'explanation',
            'recommendation', 'created_at',
        ]


class PipelineSegmentListSerializer(serializers.ModelSerializer):
    """Used for GET /segments — summary view."""
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)

    class Meta:
        model = PipelineSegment
        fields = ['id', 'segment_code', 'pipeline_name', 'latitude', 'longitude']


class PipelineSegmentDetailSerializer(serializers.ModelSerializer):
    """Used for GET /segments/{id} — full detail view."""
    pipeline = PipelineSerializer(read_only=True)
    incidents = IncidentSerializer(many=True, read_only=True)
    risk_assessments = RiskAssessmentSerializer(many=True, read_only=True)

    class Meta:
        model = PipelineSegment
        fields = [
            'id', 'segment_code', 'pipeline', 'latitude', 'longitude',
            'environmental_data', 'inspection_history',
            'incidents', 'risk_assessments',
        ]


class RiskAssessRequestSerializer(serializers.Serializer):
    """
    Validates the incoming payload to POST /risk-assess.
    Accepts either an existing segment_code, or a full segment dataset
    (with optional environmental_data / inspection_history) to score.
    """
    segment_code = serializers.CharField(max_length=100)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    environmental_data = serializers.JSONField(required=False, default=dict)
    inspection_history = serializers.JSONField(required=False, default=dict)


class RiskAssessResponseSerializer(serializers.Serializer):
    """Shapes the outgoing response from POST /risk-assess."""
    segment_id = serializers.CharField()
    risk_score = serializers.IntegerField()
    risk_level = serializers.CharField()
    explanation = serializers.CharField()
    contributing_factors = serializers.ListField(child=serializers.CharField())
    recommendation = serializers.CharField()
