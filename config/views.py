from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def salud(request):
    """Comprobación de estado: confirma que el servidor responde, sin consultar la base de datos."""
    return HttpResponse("ok", content_type="text/plain")