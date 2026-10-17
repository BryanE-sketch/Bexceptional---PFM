// Hook: los filtros viven en la URL (?publico=mujer&color=1,3...).
// Ventajas: se puede compartir el enlace, el botón "atrás" funciona y los menús de Django ya enlazan así.
import { useCallback, useEffect, useState } from "react";

const leer = () => new URLSearchParams(window.location.search);

export function useParametrosURL() {
  const [parametros, setParametros] = useState(leer);

  // Botones atrás/adelante del navegador: volvemos a leer la URL
  useEffect(() => {
    const alNavegar = () => setParametros(leer());
    window.addEventListener("popstate", alNavegar);
    return () => window.removeEventListener("popstate", alNavegar);
  }, []);

  /**
   * Cambia uno o varios parámetros. Un valor vacío ([] , "" o null) lo elimina.
   * Si cambia cualquier filtro, volvemos a la página 1.
   */
  const actualizar = useCallback((cambios, { reemplazar = false } = {}) => {
    const nuevos = leer();
    for (const [clave, valor] of Object.entries(cambios)) {
      const vacio = valor === null || valor === undefined || valor === "" || (Array.isArray(valor) && valor.length === 0);
      if (vacio) nuevos.delete(clave);
      else nuevos.set(clave, Array.isArray(valor) ? valor.join(",") : String(valor));
    }
    if (!("pagina" in cambios)) nuevos.delete("pagina");

    const consulta = nuevos.toString();
    const url = window.location.pathname + (consulta ? `?${consulta}` : "");
    window.history[reemplazar ? "replaceState" : "pushState"](null, "", url);
    setParametros(nuevos);
  }, []);

  return [parametros, actualizar];
}

/** "1,3" → ["1", "3"] */
export function lista(parametros, clave) {
  return (parametros.get(clave) || "").split(",").filter(Boolean);
}

/** Quita todos los filtros (y la búsqueda) de la URL. */
export function limpiarTodo(actualizar) {
  actualizar({ publico: null, categoria: null, disciplina: null, color: null, talla: null,
    precio_min: null, precio_max: null, en_stock: null, q: null });
}
