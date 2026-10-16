from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("catalogo.urls")),
    path("", include("contenido.urls")),
    path("", include("carrito.urls")),
    path("", include("cuentas.urls")),
]

# Solo en desarrollo: Django sirve las imágenes subidas
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)