from django.http import HttpResponse

def test_view(request):
    """Simple test view that bypasses middleware"""
    return HttpResponse("RNA Lab Navigator is running!", content_type="text/plain")