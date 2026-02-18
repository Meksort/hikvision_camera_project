"""
Views for reports module.
"""
from django.shortcuts import render


def excel_view(request):
    """
    View to render the Excel export form page.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered excel.html template
    """
    return render(request, 'excel.html')


