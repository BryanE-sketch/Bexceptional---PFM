// Panel lateral de filtros. En móvil se abre como un cajón; en escritorio está siempre visible.
import { useEffect, useState } from "react";
import { limpiarTodo, lista } from "./useParametrosURL.js";

const PUBLICOS = [
  { valor: "", nombre: "Todos" },
  { valor: "mujer", nombre: "Mujer" },
  { valor: "hombre", nombre: "Hombre" },
];

export default function PanelFiltros({ id, abierto, opciones, parametros, actualizar, alCerrar }) {
  // Añade o quita un valor de un filtro múltiple (?color=1,3)
  const alternar = (clave, valor) => {
    const actuales = lista(parametros, clave);
    const nuevos = actuales.includes(valor) ? actuales.filter((v) => v !== valor) : [...actuales, valor];
    actualizar({ [clave]: nuevos });
  };

  return (
    <aside
      id={id}
      aria-label="Filtros"
      className={`${abierto ? "fixed inset-0 z-50 overflow-y-auto bg-claro p-6" : "hidden"} lg:static lg:block lg:bg-transparent lg:p-0`}
    >
      <div className="mb-6 flex items-center justify-between lg:hidden">
        <p className="text-xl font-extrabold text-negro">Filtros</p>
        <button type="button" className="btn btn-oscuro" onClick={alCerrar}>Ver productos</button>
      </div>

      {!opciones ? (
        <p className="text-sm text-linea">Cargando filtros…</p>
      ) : (
        <div className="space-y-8">
          <Grupo titulo="Público">
            <div className="flex flex-wrap gap-2">
              {PUBLICOS.map((p) => (
                <Chip key={p.valor} activo={(parametros.get("publico") || "") === p.valor}
                      onClick={() => actualizar({ publico: p.valor })}>
                  {p.nombre}
                </Chip>
              ))}
            </div>
          </Grupo>

          <Grupo titulo="Categoría">
            <ul className="space-y-1 text-sm">
              <li>
                <OpcionCategoria activa={!parametros.get("categoria")} onClick={() => actualizar({ categoria: null })}>
                  Todas
                </OpcionCategoria>
              </li>
              {opciones.categorias.map((raiz) => (
                <li key={raiz.slug}>
                  <OpcionCategoria activa={parametros.get("categoria") === raiz.slug}
                                   onClick={() => actualizar({ categoria: raiz.slug })} negrita>
                    {raiz.nombre}
                  </OpcionCategoria>
                  <ul className="ml-4 border-l border-black/10 pl-3">
                    {raiz.subcategorias.map((sub) => (
                      <li key={sub.slug}>
                        <OpcionCategoria activa={parametros.get("categoria") === sub.slug}
                                         onClick={() => actualizar({ categoria: sub.slug })}>
                          {sub.nombre}
                        </OpcionCategoria>
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </Grupo>

          {opciones.colores.length > 0 && (
            <Grupo titulo="Color">
              <div className="flex flex-wrap gap-3">
                {opciones.colores.map((c) => {
                  const activo = lista(parametros, "color").includes(String(c.id));
                  return (
                    <button
                      key={c.id}
                      type="button"
                      aria-pressed={activo}
                      title={c.nombre}
                      onClick={() => alternar("color", String(c.id))}
                      className={`h-10 w-10 rounded-full border border-black/15 ring-offset-2 ring-offset-claro transition
                                  ${activo ? "ring-2 ring-negro" : "hover:ring-2 hover:ring-linea"}`}
                      style={{ backgroundColor: c.codigo_hex }}
                    >
                      <span className="sr-only">{c.nombre}</span>
                    </button>
                  );
                })}
              </div>
            </Grupo>
          )}

          {opciones.tallas.length > 0 && (
            <Grupo titulo="Talla">
              <div className="flex flex-wrap gap-2">
                {opciones.tallas.map((t) => (
                  <Chip key={t.id} activo={lista(parametros, "talla").includes(String(t.id))}
                        onClick={() => alternar("talla", String(t.id))}>
                    {t.nombre}
                  </Chip>
                ))}
              </div>
            </Grupo>
          )}

          {opciones.disciplinas.length > 0 && (
            <Grupo titulo="Actividad">
              <div className="flex flex-wrap gap-2">
                {opciones.disciplinas.map((d) => (
                  <Chip key={d.slug} activo={lista(parametros, "disciplina").includes(d.slug)}
                        onClick={() => alternar("disciplina", d.slug)}>
                    {d.nombre}
                  </Chip>
                ))}
              </div>
            </Grupo>
          )}

          <Grupo titulo="Precio (€)">
            <RangoPrecio parametros={parametros} actualizar={actualizar} limites={opciones.precio} />
          </Grupo>

          <Grupo titulo="Disponibilidad">
            <label className="flex cursor-pointer items-center gap-3 text-sm font-semibold text-negro">
              <input
                type="checkbox"
                className="h-5 w-5 accent-negro"
                checked={parametros.get("en_stock") === "true"}
                onChange={(e) => actualizar({ en_stock: e.target.checked ? "true" : null })}
              />
              Solo productos con stock
            </label>
          </Grupo>

          <button type="button" className="text-sm font-semibold text-linea underline hover:text-negro"
                  onClick={() => limpiarTodo(actualizar)}>
            Quitar todos los filtros
          </button>
        </div>
      )}
    </aside>
  );
}

function Grupo({ titulo, children }) {
  return (
    <fieldset>
      <legend className="mb-3 text-sm font-bold text-negro">{titulo}</legend>
      {children}
    </fieldset>
  );
}

function Chip({ activo, onClick, children }) {
  return (
    <button
      type="button"
      aria-pressed={activo}
      onClick={onClick}
      className={`min-h-10 rounded-full border px-4 text-sm font-semibold transition
                  ${activo ? "border-negro bg-negro text-crema" : "border-black/15 text-negro hover:border-negro"}`}
    >
      {children}
    </button>
  );
}

function OpcionCategoria({ activa, onClick, negrita, children }) {
  return (
    <button
      type="button"
      aria-current={activa ? "true" : undefined}
      onClick={onClick}
      className={`block w-full rounded-lg px-2 py-1.5 text-left transition hover:bg-claro-2
                  ${activa ? "bg-claro-2 font-bold text-negro" : negrita ? "font-semibold text-negro" : "text-tinta"}`}
    >
      {children}
    </button>
  );
}

/** Mínimo y máximo: se aplican al pulsar "Aplicar" o Enter, no en cada tecla. */
function RangoPrecio({ parametros, actualizar, limites }) {
  const [minimo, setMinimo] = useState(parametros.get("precio_min") || "");
  const [maximo, setMaximo] = useState(parametros.get("precio_max") || "");

  useEffect(() => {
    setMinimo(parametros.get("precio_min") || "");
    setMaximo(parametros.get("precio_max") || "");
  }, [parametros]);

  const aplicar = (e) => {
    e.preventDefault();
    actualizar({ precio_min: minimo, precio_max: maximo });
  };

  const campo = "h-11 w-full rounded-lg border border-black/15 bg-white px-3 text-sm focus:border-negro focus:outline-none";
  return (
    <form className="flex items-end gap-2" onSubmit={aplicar}>
      <label className="flex-1 text-xs text-linea">
        Desde
        <input type="number" min="0" step="1" inputMode="decimal" className={campo} value={minimo}
               placeholder={limites?.minimo ? Math.floor(limites.minimo) : ""} onChange={(e) => setMinimo(e.target.value)} />
      </label>
      <label className="flex-1 text-xs text-linea">
        Hasta
        <input type="number" min="0" step="1" inputMode="decimal" className={campo} value={maximo}
               placeholder={limites?.maximo ? Math.ceil(limites.maximo) : ""} onChange={(e) => setMaximo(e.target.value)} />
      </label>
      <button type="submit" className="h-11 rounded-lg bg-negro px-3 text-sm font-semibold text-crema">OK</button>
    </form>
  );
}
