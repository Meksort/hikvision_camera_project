from __future__ import annotations

import os
import tempfile
from datetime import datetime
from typing import Optional

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from camera_events.import_employees import export_employees_to_excel, import_employees_from_excel
from camera_events.models import Department


def _is_xlsx_filename(filename: str) -> bool:
    return filename.lower().endswith(".xlsx")


def _write_uploaded_file_to_temp(uploaded_file) -> str:
    suffix = ".xlsx" if _is_xlsx_filename(getattr(uploaded_file, "name", "")) else ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
    finally:
        tmp.close()
    return tmp.name


def _safe_remove_file(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


@staff_member_required
@require_http_methods(["GET", "POST"])
def add_employees_page(request: HttpRequest) -> HttpResponse:
    """
    Web-страница для импорта/экспорта сотрудников через Excel.

    Доступ ограничен staff-пользователями (через admin login), чтобы не открывать
    критичные операции во внешний доступ.
    """
    departments = Department.objects.select_related("parent").all().order_by("name")

    context = {
        "departments": departments,
        "import_result": None,
        "import_error": None,
    }

    if request.method == "GET":
        return render(request, "addemployees.html", context)

    excel_file = request.FILES.get("excel_file")
    if not excel_file:
        context["import_error"] = "Выберите Excel файл (.xlsx) для импорта."
        return render(request, "addemployees.html", context, status=400)

    if not _is_xlsx_filename(excel_file.name):
        context["import_error"] = "Неверный формат файла. Нужен .xlsx."
        return render(request, "addemployees.html", context, status=400)

    tmp_path = _write_uploaded_file_to_temp(excel_file)
    try:
        context["import_result"] = import_employees_from_excel(tmp_path, update_existing=True)
        return render(request, "addemployees.html", context)
    except Exception as exc:
        context["import_error"] = f"Ошибка импорта: {exc}"
        return render(request, "addemployees.html", context, status=500)
    finally:
        _safe_remove_file(tmp_path)


@staff_member_required
@require_http_methods(["GET"])
def export_employees_excel(request: HttpRequest) -> HttpResponse:
    """
    Экспорт сотрудников в Excel и выдача файла на скачивание.
    Опционально: фильтр по подразделению через query-param `department_id`.
    """
    department_filter: Optional[Department] = None
    department_id = request.GET.get("department_id")

    if department_id:
        try:
            department_filter = Department.objects.get(pk=int(department_id))
        except (ValueError, Department.DoesNotExist):
            return HttpResponse("Подразделение не найдено.", status=404)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp_path = tmp.name
    tmp.close()

    try:
        export_employees_to_excel(tmp_path, department_filter=department_filter)
        with open(tmp_path, "rb") as f:
            content = f.read()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"employees_export_{timestamp}.xlsx"

        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-store"
        return response
    finally:
        _safe_remove_file(tmp_path)

