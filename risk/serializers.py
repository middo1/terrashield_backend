from rest_framework import serializers

from .models import Incident, Pipeline, PipelineSegment, RiskAssessment


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = ['id', 'code', 'name', 'location', 'status']


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
    """
    Used for GET /segments — summary view for the Pipeline Map / Segment
    List screen. Includes the latest risk level/score/timestamp so the
    frontend doesn't need a separate call per row.
    """
    segment_code = serializers.SerializerMethodField()
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    risk_level = serializers.CharField(source='latest_risk_level', read_only=True, allow_null=True)
    risk_score = serializers.IntegerField(source='latest_risk_score', read_only=True, allow_null=True)
    last_assessed_at = serializers.DateTimeField(source='latest_updated_at', read_only=True, allow_null=True)

    class Meta:
        model = PipelineSegment
        fields = [
            'id', 'segment_code', 'pipeline_name', 'latitude', 'longitude',
            'status', 'risk_level', 'risk_score', 'last_assessed_at',
        ]

    def get_segment_code(self, obj):
        return obj.full_code


class PipelineSegmentDetailSerializer(serializers.ModelSerializer):
    """Used for GET /segments/{id} — full detail view."""
    segment_code = serializers.SerializerMethodField()
    pipeline = PipelineSerializer(read_only=True)
    incidents = IncidentSerializer(many=True, read_only=True)
    risk_assessments = RiskAssessmentSerializer(many=True, read_only=True)

    class Meta:
        model = PipelineSegment
        fields = [
            'id', 'segment_code', 'pipeline', 'latitude', 'longitude',
            'status', 'environmental_data', 'inspection_history',
            'incidents', 'risk_assessments',
        ]

    def get_segment_code(self, obj):
        return obj.full_code


class IncidentHistoryItemSerializer(serializers.Serializer):
    """One entry in the /risk-assess request's `incident_history` array."""
    type = serializers.CharField(max_length=100)
    date = serializers.DateField()


class RiskAssessRequestSerializer(serializers.Serializer):
    """
    Validates POST /risk-assess. Shape matches the frontend's payload
    exactly: pipeline_id + segment_code are separate short codes
    (e.g. "PL-05" + "SG-12"), not the combined display id.
    """
    pipeline_id = serializers.CharField(max_length=50)
    segment_code = serializers.CharField(max_length=100)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    environmental_data = serializers.JSONField(required=False, default=dict)
    incident_history = IncidentHistoryItemSerializer(many=True, required=False, default=list)


class RiskAssessResponseSerializer(serializers.Serializer):
    """Shapes the outgoing response from POST /risk-assess."""
    segment_id = serializers.CharField()
    risk_score = serializers.IntegerField()
    risk_level = serializers.CharField()
    explanation = serializers.CharField()
    contributing_factors = serializers.ListField(child=serializers.CharField())
    recommendation = serializers.CharField()
