from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import PipelineSegment
from .serializers import (
    PipelineSegmentDetailSerializer,
    PipelineSegmentListSerializer,
    RiskAssessRequestSerializer,
    RiskAssessResponseSerializer,
)


class LoginView(APIView):
    """POST /login — authenticate user, return an auth token."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'error': {
                    'code': 'authentication_failed',
                    'message': 'Invalid username or password.',
                }},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)


class DashboardView(APIView):
    """GET /dashboard — dashboard summary data."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.get_dashboard_summary()
        return Response(data, status=status.HTTP_200_OK)


class SegmentListView(APIView):
    """GET /segments — list pipeline segments."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        segments = PipelineSegment.objects.select_related('pipeline').all()
        serializer = PipelineSegmentListSerializer(segments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SegmentDetailView(APIView):
    """GET /segments/{id} — segment details."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        segment = get_object_or_404(PipelineSegment, pk=pk)
        serializer = PipelineSegmentDetailSerializer(segment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RiskAssessView(APIView):
    """
    POST /risk-assess — generate an AI risk assessment for a segment.

    View stays thin: validate -> delegate to service layer -> return result.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_serializer = RiskAssessRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        result = services.run_risk_assessment(request_serializer.validated_data)

        response_serializer = RiskAssessResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DebugInfoView(APIView):
    """
    GET /debug-info — TEMPORARY diagnostic endpoint.

    Shows what host/protocol the server actually sees on this request
    versus what it's configured to accept, so a "Bad Request" caused by
    an ALLOWED_HOSTS or CSRF/proxy mismatch can be pinpointed in one
    request instead of guessing from empty logs.

    No secrets are exposed here (no SECRET_KEY, no DB credentials) — but
    remove this view/route once the deployment issue is resolved, since
    it's still more configuration detail than a public app should expose.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from django.conf import settings as dj_settings
        from django.contrib.auth.models import User

        db_config = dj_settings.DATABASES.get('default', {})

        db_check = {'ok': True, 'user_count': None, 'error': None}
        try:
            db_check['user_count'] = User.objects.count()
        except Exception as exc:
            db_check['ok'] = False
            db_check['error'] = f'{exc.__class__.__name__}: {exc}'

        return Response({
            'request_host_header': request.META.get('HTTP_HOST'),
            'request_get_host_result': request.get_host(),
            'x_forwarded_proto': request.META.get('HTTP_X_FORWARDED_PROTO'),
            'x_forwarded_host': request.META.get('HTTP_X_FORWARDED_HOST'),
            'is_secure': request.is_secure(),
            'configured_allowed_hosts': dj_settings.ALLOWED_HOSTS,
            'configured_csrf_trusted_origins': dj_settings.CSRF_TRUSTED_ORIGINS,
            'configured_cors_allowed_origins': dj_settings.CORS_ALLOWED_ORIGINS,
            'debug_mode': dj_settings.DEBUG,
            'database_engine': db_config.get('ENGINE'),
            'database_name': str(db_config.get('NAME', ''))[:60],
            'database_host': db_config.get('HOST') or None,
            'database_check': db_check,
        })
