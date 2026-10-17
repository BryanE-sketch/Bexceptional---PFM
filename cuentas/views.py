from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import AccesoForm, RegistroForm


class EntrarView(LoginView):
    """Inicio de sesión. LoginView ya gestiona ?next= de forma segura."""

    template_name = "cuentas/entrar.html"
    authentication_form = AccesoForm
    redirect_authenticated_user = True  # si ya has entrado, no tiene sentido ver el formulario


def registro(request):
    """Alta de cliente. Al terminar, inicia sesión y vuelve a donde estaba (p. ej. el carrito)."""
    if request.user.is_authenticated:
        return redirect("cuentas:perfil")

    siguiente = request.POST.get("next") or request.GET.get("next") or ""
    if not url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        siguiente = ""  # evita redirecciones a webs externas

    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        # login() dispara la señal user_logged_in: se registra el acceso y se fusiona el carrito
        login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, f"¡Bienvenido/a, {usuario.first_name}! Tu cuenta está lista.")
        return redirect(siguiente or "cuentas:perfil")
    return render(request, "cuentas/registro.html", {"form": form, "next": siguiente})


@login_required
def perfil(request):
    """Mi cuenta: datos básicos y últimos pedidos."""
    pedidos = request.user.pedidos.order_by("-creado")[:10]
    return render(request, "cuentas/perfil.html", {"pedidos": pedidos})
