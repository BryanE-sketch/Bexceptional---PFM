from django import forms

from catalogo.models import Variante


class AnadirAlCarritoForm(forms.Form):
    """Valida lo que llega al pulsar «Añadir al carrito» (nunca nos fiamos del navegador)."""

    variante = forms.ModelChoiceField(
        queryset=Variante.objects.filter(producto__activo=True).select_related("producto", "talla", "color"),
        error_messages={
            "required": "Elige una talla.",
            "invalid_choice": "Esa talla ya no está disponible.",
        },
    )
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        error_messages={
            "min_value": "La cantidad mínima es 1.",
            "max_value": "Puedes añadir como máximo 10 unidades a la vez.",
        },
    )