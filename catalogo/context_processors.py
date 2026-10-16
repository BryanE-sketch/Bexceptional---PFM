"""Datos que necesitan TODAS las páginas de la tienda (menú y contador del carrito)."""

from django.db.models import Prefetch

from carrito.services import cantidad_en_carrito

from .models import Categoria, Disciplina

SLUG_ACCESORIOS = "accesorios"  # la categoría raíz con este slug forma el menú «Accesorios»


def navegacion(request):
    if request.path.startswith("/admin/"):
        return {}  # el panel no necesita el menú de la tienda

    raices = list(
        Categoria.objects.filter(activa=True, padre__isnull=True).prefetch_related(
            Prefetch("subcategorias", queryset=Categoria.objects.filter(activa=True))
        )
    )
    return {
        "nav_categorias": [c for c in raices if c.slug != SLUG_ACCESORIOS],
        "nav_accesorios": next((c for c in raices if c.slug == SLUG_ACCESORIOS), None),
        "nav_disciplinas": Disciplina.objects.filter(activa=True),
        "carrito_cantidad": cantidad_en_carrito(request),
    }