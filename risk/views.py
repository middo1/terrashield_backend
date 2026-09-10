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
