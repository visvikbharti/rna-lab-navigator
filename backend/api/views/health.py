from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

@csrf_exempt
def health_check(request):
    """Simple health check endpoint for Railway"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'rna-lab-navigator',
        'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')
    })