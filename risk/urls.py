from django.urls import path

from . import views

urlpatterns = [
    path('login', views.LoginView.as_view(), name='login'),
    path('dashboard', views.DashboardView.as_view(), name='dashboard'),
    path('segments', views.SegmentListView.as_view(), name='segment-list'),
    path('segments/<int:pk>', views.SegmentDetailView.as_view(), name='segment-detail'),
    path('risk-assess', views.RiskAssessView.as_view(), name='risk-assess'),
    path('debug-info', views.DebugInfoView.as_view(), name='debug-info'),
]
