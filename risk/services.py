"""
Service layer — all business logic lives here, not in the views.
"""
from datetime import timedelta

from django.db.models import Avg, OuterRef, Subquery
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Incident, Pipeline, PipelineSegment, RiskAssessment


# ---------------------------------------------------------------------------
# AI Risk Engine interface
# ---------------------------------------------------------------------------
def get_risk_assessment(segment: PipelineSegment, environmental_data: dict,
                         incident_history: list) -> dict:
    """
    Calls the AI risk engine and returns its raw output.

    This is a stub. Swap the body of this function for the real call to
    the AI model once it's available. The contract below is what the
    rest of the service layer expects back:

        {
            "risk_score": int,            # 0-100
            "risk_level": str,            # "Low" | "Medium" | "High"
            "explanation": str,
            "contributing_factors": list[str],
            "recommendation": str,
        }
    """
    # --- STUBBED RESPONSE (replace with real AI engine call) ---
    factors = []
    if str(environmental_data.get('flood_risk', '')).lower() == 'high':
        factors.append('elevated flood risk')
    if environmental_data.get('elevation') is not None and environmental_data['elevation'] < 20:
        factors.append('low elevation')
    if incident_history:
        factors.append(f"{len(incident_history)} recorded incident(s)")
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
            f'segment {segment.full_code}.'
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
    resolve pipeline+segment -> save incident history -> prepare AI input
    -> call AI engine -> save RiskAssessment -> return response dict.
    """
    pipeline, _ = Pipeline.objects.get_or_create(
        code=validated_data['pipeline_id'],
        defaults={
            'name': validated_data['pipeline_id'],
            'location': 'Unknown',
            'status': 'active',
        },
    )

    segment, _ = PipelineSegment.objects.get_or_create(
        pipeline=pipeline,
        segment_code=validated_data['segment_code'],
        defaults={
            'latitude': validated_data.get('latitude', 0.0),
            'longitude': validated_data.get('longitude', 0.0),
        },
    )

    environmental_data = validated_data.get('environmental_data') or {}
    if environmental_data:
        segment.environmental_data = environmental_data
        segment.save(update_fields=['environmental_data'])
    else:
        environmental_data = segment.environmental_data

    for item in validated_data.get('incident_history', []):
        Incident.objects.get_or_create(
            segment=segment,
            incident_type=item['type'],
            date=item['date'],
        )
    incident_history = list(
        segment.incidents.values('incident_type', 'date', 'severity')
    )

    ai_output = get_risk_assessment(segment, environmental_data, incident_history)

    assessment = RiskAssessment.objects.create(
        segment=segment,
        risk_score=ai_output['risk_score'],
        risk_level=ai_output['risk_level'],
        explanation=ai_output['explanation'],
        recommendation=ai_output['recommendation'],
    )

    return {
        'segment_id': segment.full_code,
        'risk_score': assessment.risk_score,
        'risk_level': assessment.risk_level,
        'explanation': assessment.explanation,
        'contributing_factors': ai_output['contributing_factors'],
        'recommendation': assessment.recommendation,
    }


# ---------------------------------------------------------------------------
# /segments — list with latest risk level annotated, search + filter
# ---------------------------------------------------------------------------
def get_segment_queryset(search: str = '', risk_level: str = ''):
    latest_ra = RiskAssessment.objects.filter(segment=OuterRef('pk')).order_by('-created_at')
    qs = PipelineSegment.objects.select_related('pipeline').annotate(
        latest_risk_level=Subquery(latest_ra.values('risk_level')[:1]),
        latest_risk_score=Subquery(latest_ra.values('risk_score')[:1]),
        latest_updated_at=Subquery(latest_ra.values('created_at')[:1]),
    )
    if search:
        qs = qs.filter(segment_code__icontains=search) | qs.filter(
            pipeline__name__icontains=search
        ) | qs.filter(pipeline__code__icontains=search)
    if risk_level:
        qs = qs.filter(latest_risk_level__iexact=risk_level)
    return qs.order_by('pipeline__code', 'segment_code')


# ---------------------------------------------------------------------------
# /dashboard
# ---------------------------------------------------------------------------
def get_dashboard_summary() -> dict:
    """Aggregates summary data for the dashboard: counts, trend, recent alerts."""
    latest_ra = RiskAssessment.objects.filter(segment=OuterRef('pk')).order_by('-created_at')
    segments = PipelineSegment.objects.annotate(
        latest_risk_level=Subquery(latest_ra.values('risk_level')[:1]),
    )

    since = timezone.now() - timedelta(days=14)
    trend_qs = (
        RiskAssessment.objects.filter(created_at__gte=since)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(average_risk_score=Avg('risk_score'))
        .order_by('day')
    )

    recent_alerts = (
        RiskAssessment.objects.select_related('segment', 'segment__pipeline')
        .exclude(risk_level__iexact='Low')
        .order_by('-created_at')[:5]
    )

    return {
        'total_pipelines': Pipeline.objects.count(),
        'total_segments': PipelineSegment.objects.count(),
        'high_risk_count': segments.filter(latest_risk_level__iexact='High').count(),
        'medium_risk_count': segments.filter(latest_risk_level__iexact='Medium').count(),
        'low_risk_count': segments.filter(latest_risk_level__iexact='Low').count(),
        'risk_trend': [
            {
                'date': str(row['day']),
                'average_risk_score': round(row['average_risk_score'] or 0, 1),
            }
            for row in trend_qs
        ],
        'recent_alerts': [
            {
                'segment_id': a.segment.full_code,
                'risk_level': a.risk_level,
                'created_at': a.created_at,
            }
            for a in recent_alerts
        ],
    }
