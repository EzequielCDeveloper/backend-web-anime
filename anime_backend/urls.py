"""
URL configuration for anime_backend project (Anime Recommended).

Endpoints principales:
- Panel de Administración: /admin/
- API v1: /api/v1/
- Documentación Swagger UI: /swagger/
- Documentación ReDoc: /redoc/
- Esquema OpenAPI JSON/YAML: /swagger.json o /swagger.yaml
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Personalización del Admin de Django para Anime Recommended
admin.site.site_header = "Anime Recommended - Panel Administrativo"
admin.site.site_title = "Anime Recommended Portal"
admin.site.index_title = "Gestión del Sistema y Usuarios"

# Configuración del esquema de Swagger / OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Anime Recommended API",
        default_version='v1',
        description=(
            "Documentación interactiva de la API Backend para la plataforma "
            "de streaming y recomendaciones Anime Recommended.\n\n"
            "Incluye autenticación por JWT, gestión de usuarios con campos extendidos "
            "(teléfono), y registro público seguro."
        ),
        terms_of_service="https://www.animerecommended.local/terms/",
        contact=openapi.Contact(email="contacto@animerecommended.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),

    # Endpoints de la API v1
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('reviews.urls')),

    # Documentación interactiva
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
