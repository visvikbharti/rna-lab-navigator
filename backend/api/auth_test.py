"""
Simple auth test endpoint to debug CORS
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def auth_test(request):
    """Test endpoint to verify auth works"""
    # Handle preflight
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "3600"
        return response
    
    # Handle actual request
    response_data = {
        "status": "success",
        "message": "Auth test endpoint working",
        "method": request.method,
        "headers": dict(request.headers),
    }
    
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            response_data["received_data"] = body
        except:
            response_data["body"] = "Could not parse body"
    
    response = JsonResponse(response_data)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Credentials"] = "true"
    return response