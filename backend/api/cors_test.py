"""
Simple CORS test endpoint
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def cors_test(request):
    """Test endpoint to verify CORS is working"""
    return JsonResponse({
        "status": "success",
        "message": "CORS is working!",
        "method": request.method,
        "headers": dict(request.headers),
        "origin": request.headers.get('Origin', 'No origin header')
    })