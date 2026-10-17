"""Formulario de «Finalizar compra»: dirección de envío + método de pago (simulado)."""
import re
from datetime import date

from django import forms
from django.core.validators import RegexValidator

from .models import Pago

CODIGO_POSTAL = RegexValidator(r"^\d{5}$", "El código postal debe tener 5 cifras.")
TELEFONO = RegexValidator(r"^\+?[\d\s]{9,15}$", "Introduce un teléfono válido.")


def luhn_valido(numero):
    """
    Algoritmo de Luhn: la comprobación que hacen todas las tiendas para detectar
    errores al teclear una tarjeta (no dice si tiene saldo, solo si el número es posible).
    """
    digitos = [int(d) for d in numero][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digitos))
    return total % 10 == 0


class CheckoutForm(forms.Form):
    # ── 1. Envío ──
    nombre_destinatario = forms.CharField(label="Nombre y apellidos", max_length=120)
    direccion = forms.CharField(label="Dirección", max_length=200,
                                widget=forms.TextInput(attrs={"autocomplete": "street-address"}))
    codigo_postal = forms.CharField(label="Código postal", max_length=5, validators=[CODIGO_POSTAL],
                                    widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "postal-code"}))
    ciudad = forms.CharField(label="Ciudad", max_length=80)
    provincia = forms.CharField(label="Provincia", max_length=80)
    telefono = forms.CharField(label="Teléfono", max_length=20, validators=[TELEFONO],
                               widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}))
    guardar_direccion = forms.BooleanField(label="Guardar como mi dirección predeterminada", required=False)

    # ── 2. Pago (simulado) ──
    metodo = forms.ChoiceField(label="Método de pago", choices=Pago.Metodo.choices, initial=Pago.Metodo.TARJETA,
                               widget=forms.RadioSelect)
    titular = forms.CharField(label="Titular de la tarjeta", max_length=100, required=False,
                              widget=forms.TextInput(attrs={"autocomplete": "cc-name"}))
    numero_tarjeta = forms.CharField(label="Número de tarjeta", max_length=23, required=False,
                                     widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "cc-number",
                                                                   "placeholder": "4242 4242 4242 4242"}))
    caducidad = forms.CharField(label="Caducidad (MM/AA)", max_length=5, required=False,
                                widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "cc-exp",
                                                              "placeholder": "12/28"}))
    cvc = forms.CharField(label="CVC", max_length=4, required=False,
                          widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "cc-csc", "placeholder": "123"}))

    def clean_numero_tarjeta(self):
        return re.sub(r"[\s-]", "", self.cleaned_data["numero_tarjeta"])

    def clean(self):
        datos = super().clean()
        # Los datos de tarjeta solo son obligatorios si se paga con tarjeta
        if datos.get("metodo") != Pago.Metodo.TARJETA:
            return datos

        if not datos.get("titular"):
            self.add_error("titular", "Indica el titular de la tarjeta.")
        numero = datos.get("numero_tarjeta", "")
        if not re.fullmatch(r"\d{13,19}", numero) or not luhn_valido(numero):
            self.add_error("numero_tarjeta", "El número de tarjeta no es válido.")
        caducidad = datos.get("caducidad", "")
        coincidencia = re.fullmatch(r"(0[1-9]|1[0-2])/(\d{2})", caducidad)
        if not coincidencia:
            self.add_error("caducidad", "Usa el formato MM/AA.")
        else:
            mes, anio = int(coincidencia[1]), 2000 + int(coincidencia[2])
            hoy = date.today()
            if (anio, mes) < (hoy.year, hoy.month):
                self.add_error("caducidad", "La tarjeta está caducada.")
        if not re.fullmatch(r"\d{3,4}", datos.get("cvc", "")):
            self.add_error("cvc", "El CVC son 3 o 4 cifras.")
        return datos

    def datos_envio(self):
        campos = ["nombre_destinatario", "direccion", "ciudad", "codigo_postal", "provincia", "telefono"]
        return {campo: self.cleaned_data[campo] for campo in campos}
