"""
URL configuration for Hikvision Camera Integration Project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("camera_events.urls")),
    path("report/", TemplateView.as_view(template_name="report.html"), name="report"),
    path("excel/", TemplateView.as_view(template_name="excel.html"), name="excel"),
]

