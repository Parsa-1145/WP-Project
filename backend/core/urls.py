from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from . import settings
from cases.views import FrontModulesGetView

def health_check(request):
    return HttpResponse("OK", status=200)


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path('api/auth/', include("accounts.urls")),
    path('api/evidence/', include("evidence.urls")),
    path('api/cases/', include("cases.urls")),
    path("api/front-modules/", FrontModulesGetView.as_view(), name="front-modules-get"),
    path('api/submission/', include("submissions.urls")),
    path('api/payments/', include("payments.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
