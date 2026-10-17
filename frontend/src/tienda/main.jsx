// Punto de entrada: monta la tienda de React dentro de <div id="tienda"> de la plantilla de Django.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Tienda from "./Tienda.jsx";

const raiz = document.getElementById("tienda");

if (raiz) {
  // Django nos pasa las URLs de la API con atributos data-* (así no se escriben a mano en JS)
  const { urlProductos, urlFiltros } = raiz.dataset;
  createRoot(raiz).render(
    <StrictMode>
      <Tienda urlProductos={urlProductos} urlFiltros={urlFiltros} />
    </StrictMode>,
  );
}
