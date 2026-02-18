"""
URL routes for the reports sub-application.
"""
from django.urls import path

from .views import excel_view

urlpatterns = [
    path("excel/", excel_view, name="excel"),
]



