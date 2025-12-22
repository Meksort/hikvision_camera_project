"""
URL маршруты для приложения camera_events.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CameraEventViewSet, EntryExitViewSet, DepartmentViewSet, AttendanceStatsViewSet

router = DefaultRouter()
router.register(r"camera-events", CameraEventViewSet, basename="camera-events")
router.register(r"entries-exits", EntryExitViewSet, basename="entries-exits")
router.register(r"departments", DepartmentViewSet, basename="departments")
router.register(r"attendance-stats", AttendanceStatsViewSet, basename="attendance-stats")

urlpatterns = [
    path("", include(router.urls)),
]

