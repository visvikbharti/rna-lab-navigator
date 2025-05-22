"""
Health check endpoints for Railway deployment monitoring
"""
import os
import time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
import redis
import weaviate


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint for Railway
    Returns 200 OK if the service is running
    """
    return JsonResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "rna-lab-navigator-backend"
    })


@csrf_exempt
@require_http_methods(["GET"])
def health_detailed(request):
    """
    Detailed health check with dependency status
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "rna-lab-navigator-backend",
        "checks": {}
    }
    
    overall_healthy = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status["checks"]["database"] = {"status": "healthy", "message": "PostgreSQL connection OK"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
        overall_healthy = False
    
    # Redis check
    try:
        cache.set("health_check", "ok", timeout=10)
        if cache.get("health_check") == "ok":
            health_status["checks"]["redis"] = {"status": "healthy", "message": "Redis connection OK"}
        else:
            health_status["checks"]["redis"] = {"status": "unhealthy", "message": "Redis read/write failed"}
            overall_healthy = False
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "message": str(e)}
        overall_healthy = False
    
    # Weaviate check
    try:
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        client = weaviate.Client(weaviate_url)
        if client.is_ready():
            health_status["checks"]["weaviate"] = {"status": "healthy", "message": "Weaviate connection OK"}
        else:
            health_status["checks"]["weaviate"] = {"status": "unhealthy", "message": "Weaviate not ready"}
            overall_healthy = False
    except Exception as e:
        health_status["checks"]["weaviate"] = {"status": "unhealthy", "message": str(e)}
        overall_healthy = False
    
    # OpenAI API check (basic)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key and openai_api_key.startswith("sk-"):
        health_status["checks"]["openai"] = {"status": "healthy", "message": "OpenAI API key configured"}
    else:
        health_status["checks"]["openai"] = {"status": "unhealthy", "message": "OpenAI API key not configured"}
        overall_healthy = False
    
    # Overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    
    return JsonResponse(health_status, status=200 if overall_healthy else 503)


@csrf_exempt
@require_http_methods(["GET"])
def ready_check(request):
    """
    Readiness check for Railway health monitoring
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({"status": "ready"})
    except Exception:
        return JsonResponse({"status": "not ready"}, status=503)