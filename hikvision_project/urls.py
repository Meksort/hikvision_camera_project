"""
URL configuration for Hikvision Camera Integration Project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from camera_events.web_views import add_employees_page, export_employees_excel

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("camera_events.urls")),
    path(
        "excel/",
        TemplateView.as_view(template_name="excel.html"),
        name="excel",
    ),
    path(
        "report/",
        TemplateView.as_view(template_name="report.html"),
        name="report",
    ),
    path("addemployees/", add_employees_page, name="addemployees"),
    path("addemployees/export/", export_employees_excel, name="addemployees-export"),
]

