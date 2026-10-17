// Fila de "etiquetas" con los filtros aplicados; cada una se quita con un clic.
import { limpiarTodo, lista } from "./useParametrosURL.js";

export default function FiltrosActivos({ opciones, parametros, actualizar }) {
  if (!opciones) return null;

  const nombreCategoria = (slug) => {
    for (const raiz of opciones.categorias) {
      if (raiz.slug === slug) return raiz.nombre;
      const hija = raiz.subcategorias.find((s) => s.slug === slug);
      if (hija) return hija.nombre;
    }
    return slug;
  };
  const quitarDeLista = (clave, valor) =>
    actualizar({ [clave]: lista(parametros, clave).filter((v) => v !== valor) });

  const etiquetas = [];
  const publico = parametros.get("publico");
  if (publico) etiquetas.push({ texto: publico === "mujer" ? "Mujer" : publico === "hombre" ? "Hombre" : "Unisex", quitar: () => actualizar({ publico: null }) });
  const categoria = parametros.get("categoria");
  if (categoria) etiquetas.push({ texto: nombreCategoria(categoria), quitar: () => actualizar({ categoria: null }) });
  for (const id of lista(parametros, "color")) {
    const color = opciones.colores.find((c) => String(c.id) === id);
    etiquetas.push({ texto: color ? color.nombre : `Color ${id}`, quitar: () => quitarDeLista("color", id) });
  }
  for (const id of lista(parametros, "talla")) {
    const talla = opciones.tallas.find((t) => String(t.id) === id);
    etiquetas.push({ texto: `Talla ${talla ? talla.nombre : id}`, quitar: () => quitarDeLista("talla", id) });
  }
  for (const slug of lista(parametros, "disciplina")) {
    const d = opciones.disciplinas.find((x) => x.slug === slug);
    etiquetas.push({ texto: d ? d.nombre : slug, quitar: () => quitarDeLista("disciplina", slug) });
  }
  if (parametros.get("precio_min")) etiquetas.push({ texto: `Desde ${parametros.get("precio_min")} €`, quitar: () => actualizar({ precio_min: null }) });
  if (parametros.get("precio_max")) etiquetas.push({ texto: `Hasta ${parametros.get("precio_max")} €`, quitar: () => actualizar({ precio_max: null }) });
  if (parametros.get("en_stock") === "true") etiquetas.push({ texto: "Con stock", quitar: () => actualizar({ en_stock: null }) });

  if (!etiquetas.length) return null;

  return (
    <div className="mb-6 flex flex-wrap items-center gap-2">
      {etiquetas.map((e) => (
        <button key={e.texto} type="button" onClick={e.quitar}
                className="inline-flex min-h-9 items-center gap-2 rounded-full bg-negro px-4 text-xs font-semibold text-crema hover:bg-tinta">
          {e.texto}
          <span aria-hidden="true">×</span>
          <span className="sr-only">(quitar filtro)</span>
        </button>
      ))}
      <button type="button" onClick={() => limpiarTodo(actualizar)}
              className="ml-1 text-xs font-semibold text-linea underline hover:text-negro">
        Quitar todo
      </button>
    </div>
  );
}
