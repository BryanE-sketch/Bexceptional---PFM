from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import salud

urlpatterns = [
    path("admin/", admin.site.urls),
    # Comprobación de estado para monitorización
    path("salud/", salud, name="salud"),
    # API REST
    path('api/', include('catalogo.api_urls')),
    path('api/esquema/', SpectacularAPIView.as_view(), name='esquema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='esquema'), name='docs'),
    # URLs de la web
    path("", include("catalogo.urls")),
    path("", include("contenido.urls")),
    path("", include("carrito.urls")),
    path("", include("cuentas.urls")),
    path("", include("pedidos.urls")),
]

# Solo en desarrollo: Django sirve las imágenes subidas
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)