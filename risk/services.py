"""
Service layer — all business logic lives here, not in the views.

The views' job is to: authenticate the request, hand off to a service
function, and return whatever the service returns. Nothing more.
"""
from django.db.models import Avg, Count

from .models import Pipeline, PipelineSegment, RiskAssessment


# ---------------------------------------------------------------------------
# AI Risk Engine interface
# ---------------------------------------------------------------------------
def get_risk_assessment(segment: PipelineSegment, environmental_data: dict,
                         incident_history: list) -> dict:
    """
    Calls the AI risk engine and returns its raw output.

    This is a stub. Swap the body of this function for the real call to
    the AI model (e.g. an HTTP request to the risk-scoring service, or an
    Anthropic API call) once it's available. The contract below is what
    the rest of the service layer expects back:

        {
            "risk_score": int,            # 0-100
            "risk_level": str,            # e.g. "Low" | "Medium" | "High"
            "explanation": str,
            "contributing_factors": list[str],
            "recommendation": str,
        }
    """
    # --- STUBBED RESPONSE (replace with real AI engine call) ---
    factors = []
    if environmental_data.get('corrosion_risk'):
        factors.append('corrosion')
    if environmental_data.get('soil_moisture'):
        factors.append('soil_moisture')
    if incident_history:
        factors.append('past_incident')
    if not factors:
        factors.append('baseline_conditions')

    score = min(95, 30 + len(incident_history) * 15 + len(factors) * 10)
    level = 'High' if score >= 70 else 'Medium' if score >= 40 else 'Low'

    return {
        'risk_score': score,
        'risk_level': level,
        'explanation': (
            f'Assessment based on {len(factors)} contributing factor(s) '
            f'and {len(incident_history)} recorded incident(s) for '
            f'segment {segment.segment_code}.'
        ),
        'contributing_factors': factors,
        'recommendation': (
            'Schedule inspection within 7 days.' if level == 'High'
            else 'Schedule inspection within 30 days.' if level == 'Medium'
            else 'Continue routine monitoring.'
        ),
    }


# ---------------------------------------------------------------------------
# /risk-assess
# ---------------------------------------------------------------------------
def run_risk_assessment(validated_data: dict) -> dict:
    """
    Orchestrates the full /risk-assess flow:
    prepare AI input -> call AI engine -> save RiskAssessment -> return response dict.
    """
    segment_code = validated_data['segment_code']
    segment, _ = PipelineSegment.objects.get_or_create(
        segment_code=segment_code,
        defaults={
            'pipeline': Pipeline.objects.first() or Pipeline.objects.create(
                name='Default Pipeline', location='Unknown', status='active'
            ),
            'latitude': validated_data.get('latitude', 0.0),
            'longitude': validated_data.get('longitude', 0.0),
        },
    )

    environmental_data = validated_data.get('environmental_data') or segment.environmental_data
    incident_history = list(segment.incidents.values(
        'incident_type', 'date', 'severity'
    ))

    ai_output = get_risk_assessment(segment, environmental_data, incident_history)

    assessment = RiskAssessment.objects.create(
        segment=segment,
        risk_score=ai_output['risk_score'],
        risk_level=ai_output['risk_level'],
        explanation=ai_output['explanation'],
        recommendation=ai_output['recommendation'],
    )

    return {
        'segment_id': segment.segment_code,
        'risk_score': assessment.risk_score,
        'risk_level': assessment.risk_level,
        'explanation': assessment.explanation,
        'contributing_factors': ai_output['contributing_factors'],
        'recommendation': assessment.recommendation,
    }


# ---------------------------------------------------------------------------
# /dashboard
# ---------------------------------------------------------------------------
def get_dashboard_summary() -> dict:
    """Aggregates summary data for the dashboard endpoint."""
    segment_count = PipelineSegment.objects.count()
    pipeline_count = Pipeline.objects.count()
    latest_assessments = RiskAssessment.objects.select_related('segment')[:5]

    return {
        'pipeline_count': pipeline_count,
        'segment_count': segment_count,
        'average_risk_score': RiskAssessment.objects.aggregate(
            avg=Avg('risk_score')
        )['avg'] or 0,
        'risk_level_breakdown': list(
            RiskAssessment.objects.values('risk_level').annotate(count=Count('id'))
        ),
        'latest_assessments': [
            {
                'segment_id': a.segment.segment_code,
                'risk_score': a.risk_score,
                'risk_level': a.risk_level,
                'created_at': a.created_at,
            }
            for a in latest_assessments
        ],
    }
