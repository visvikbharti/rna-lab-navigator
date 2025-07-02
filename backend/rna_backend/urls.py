from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.health import health_check, health_detailed, ready_check
from api.cors_test import cors_test
from api.auth_test import auth_test
from api.test_view import test_view

urlpatterns = [
    path("", test_view, name="root_test"),  # Root path test
    path("health", health_check, name="health_check_no_slash"),  # Without trailing slash
    path("health/", health_check, name="health_check"),  # With trailing slash
    path("api/health", health_check, name="api_health_no_slash"),  # API path without slash
    path("api/health/", health_check, name="api_health"),  # API path with slash
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("health/detailed/", health_detailed, name="health_detailed"),
    path("cors-test/", cors_test, name="cors_test"),
    path("auth-test/", auth_test, name="auth_test"),
    path("ready/", ready_check, name="ready_check"),
    # The following URLs are already included in api.urls and don't need to be duplicated here
    # path("api/quality/", include("api.quality.urls")),
    # path("api/feedback/", include("api.feedback.urls")),
]

# Add media serving capability in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)