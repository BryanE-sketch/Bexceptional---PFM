from django.urls import path

from catalogo.views import proximamente

app_name = "pedidos"

urlpatterns = [
    # Provisional: el proceso de pago (CU-04) se construye en la siguiente entrega
    path("finalizar-compra/", proximamente, {"titulo": "Finalizar compra"}, name="checkout"),
]
