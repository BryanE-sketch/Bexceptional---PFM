// Componente principal de la tienda: lee la URL, pide los datos a la API y reparte el trabajo.
import { useEffect, useMemo, useRef, useState } from "react";
import { limpiarTodo, lista, useParametrosURL } from "./useParametrosURL.js";
import PanelFiltros from "./PanelFiltros.jsx";
import FiltrosActivos from "./FiltrosActivos.jsx";
import TarjetaProducto from "./TarjetaProducto.jsx";
import Paginacion from "./Paginacion.jsx";

const ORDENES = [
  { valor: "", nombre: "Novedades" },
  { valor: "precio", nombre: "Precio: de menor a mayor" },
  { valor: "-precio", nombre: "Precio: de mayor a menor" },
  { valor: "nombre", nombre: "Nombre (A-Z)" },
];
const POR_PAGINA = 12;

export default function Tienda({ urlProductos, urlFiltros }) {
  const [parametros, actualizar] = useParametrosURL();
  const [opciones, setOpciones] = useState(null);      // lo que devuelve /api/filtros/
  const [resultado, setResultado] = useState(null);    // lo que devuelve /api/productos/
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [panelAbierto, setPanelAbierto] = useState(false);
  const [reintento, setReintento] = useState(0);
  const inicioResultados = useRef(null);

  const consulta = parametros.toString();

  // 1) Las opciones de los filtros se piden una sola vez
  useEffect(() => {
    fetch(urlFiltros)
      .then((r) => (r.ok ? r.json() : Promise.reject(r)))
      .then(setOpciones)
      .catch(() => setOpciones({ categorias: [], disciplinas: [], colores: [], tallas: [], publicos: [], precio: {} }));
  }, [urlFiltros]);

  // 2) Los productos se piden cada vez que cambia la URL
  useEffect(() => {
    // AbortController: si el usuario cambia de filtro rápido, cancelamos la petición anterior
    // para que una respuesta vieja no pise a la nueva.
    const control = new AbortController();
    setCargando(true);
    setError(null);
    fetch(`${urlProductos}?${consulta}`, { signal: control.signal, headers: { Accept: "application/json" } })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`Error ${r.status}`))))
      .then((datos) => {
        setResultado(datos);
        setCargando(false);
      })
      .catch((e) => {
        if (e.name === "AbortError") return;
        setError("No hemos podido cargar los productos.");
        setCargando(false);
      });
    return () => control.abort();
  }, [urlProductos, consulta, reintento]);

  const titulo = useMemo(() => tituloDePagina(parametros, opciones), [parametros, opciones]);
  useEffect(() => {
    document.title = `${titulo} · Bexceptional`;
  }, [titulo]);

  const cambiarPagina = (pagina) => {
    actualizar({ pagina: pagina > 1 ? pagina : null });
    inicioResultados.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const totalPaginas = resultado ? Math.max(1, Math.ceil(resultado.count / POR_PAGINA)) : 1;
  const paginaActual = Number(parametros.get("pagina") || 1);
  const numFiltros = ["publico", "categoria", "disciplina", "color", "talla", "precio_min", "precio_max", "en_stock"]
    .reduce((n, clave) => n + (clave === "disciplina" || clave === "color" || clave === "talla"
      ? lista(parametros, clave).length : parametros.get(clave) ? 1 : 0), 0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8 lg:py-12">
      <header className="flex flex-col gap-6 border-b border-black/10 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="bx-eyebrow text-linea">Tienda</p>
          <h1 className="mt-2 text-3xl font-extrabold text-negro lg:text-4xl">{titulo}</h1>
          <p className="mt-2 text-sm text-linea" aria-live="polite">
            {resultado && !cargando ? `${resultado.count} producto${resultado.count === 1 ? "" : "s"}` : "Cargando…"}
          </p>
        </div>
        <Buscador valorInicial={parametros.get("q") || ""} alBuscar={(q) => actualizar({ q }, { reemplazar: true })} />
      </header>

      <div className="mt-6 flex items-center justify-between gap-3">
        <button
          type="button"
          className="btn whitespace-nowrap border border-black/15 text-negro lg:hidden"
          aria-expanded={panelAbierto}
          aria-controls="panel-filtros"
          onClick={() => setPanelAbierto((a) => !a)}
        >
          Filtros{numFiltros ? ` (${numFiltros})` : ""}
        </button>
        <label className="ml-auto flex items-center gap-2 text-sm font-semibold text-negro">
          <span className="hidden sm:inline">Ordenar por</span>
          <select
            className="h-11 rounded-full border border-black/15 bg-white px-4 text-sm font-semibold focus:border-negro focus:outline-none"
            value={parametros.get("orden") || ""}
            onChange={(e) => actualizar({ orden: e.target.value })}
          >
            {ORDENES.map((o) => (
              <option key={o.valor} value={o.valor}>{o.nombre}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-6 grid gap-8 lg:grid-cols-[260px_1fr]">
        <PanelFiltros
          id="panel-filtros"
          abierto={panelAbierto}
          opciones={opciones}
          parametros={parametros}
          actualizar={actualizar}
          alCerrar={() => setPanelAbierto(false)}
        />

        <section ref={inicioResultados} aria-label="Productos" className="scroll-mt-6">
          <FiltrosActivos opciones={opciones} parametros={parametros} actualizar={actualizar} />

          {error ? (
            <div className="rounded-2xl bg-claro-2 p-8 text-center">
              <p className="font-semibold text-negro">{error}</p>
              <button type="button" className="btn btn-oscuro mt-4" onClick={() => setReintento((n) => n + 1)}>
                Reintentar
              </button>
            </div>
          ) : !resultado ? (
            <Esqueleto />
          ) : resultado.results.length === 0 ? (
            <div className="rounded-2xl bg-claro-2 p-10 text-center">
              <p className="text-lg font-bold text-negro">No hay productos con estos filtros.</p>
              <p className="mt-2 text-sm text-linea">Prueba a quitar alguno o vuelve a ver toda la tienda.</p>
              <button type="button" className="btn btn-oscuro mt-6" onClick={() => limpiarTodo(actualizar)}>
                Ver todos los productos
              </button>
            </div>
          ) : (
            <>
              <ul className={`grid grid-cols-2 gap-x-4 gap-y-8 md:grid-cols-3 transition-opacity ${cargando ? "opacity-50" : ""}`}>
                {resultado.results.map((producto) => (
                  <li key={producto.id}>
                    <TarjetaProducto producto={producto} />
                  </li>
                ))}
              </ul>
              <Paginacion actual={paginaActual} total={totalPaginas} alCambiar={cambiarPagina} />
            </>
          )}
        </section>
      </div>
    </div>
  );
}

/** Caja de búsqueda: espera unos ms después de la última tecla antes de buscar (debounce). */
function Buscador({ valorInicial, alBuscar }) {
  const [texto, setTexto] = useState(valorInicial);

  // Si la URL cambia desde fuera (p. ej. "Quitar todos los filtros"), actualizamos la caja
  useEffect(() => setTexto(valorInicial), [valorInicial]);

  useEffect(() => {
    if (texto.trim() === valorInicial) return;          // nada nuevo que buscar
    const espera = setTimeout(() => alBuscar(texto.trim()), 350);
    return () => clearTimeout(espera);                  // si sigue escribiendo, se cancela
  }, [texto]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <form role="search" className="w-full md:w-80" onSubmit={(e) => { e.preventDefault(); alBuscar(texto.trim()); }}>
      <label htmlFor="buscar" className="sr-only">Buscar productos</label>
      <input
        id="buscar"
        type="search"
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        placeholder="Buscar camisetas, gorras…"
        autoComplete="off"
        className="h-12 w-full rounded-full border border-black/15 bg-white px-5 text-sm text-negro placeholder:text-linea focus:border-negro focus:outline-none"
      />
    </form>
  );
}

function Esqueleto() {
  return (
    <ul className="grid grid-cols-2 gap-x-4 gap-y-8 md:grid-cols-3" aria-hidden="true">
      {Array.from({ length: 6 }, (_, i) => (
        <li key={i} className="animate-pulse">
          <div className="aspect-3/4 rounded-xl bg-claro-2" />
          <div className="mt-3 h-4 w-3/4 rounded bg-claro-2" />
          <div className="mt-2 h-4 w-1/3 rounded bg-claro-2" />
        </li>
      ))}
    </ul>
  );
}

/** Título según los filtros: "Mujeres", "Accesorios", "Resultados de «gorra»"... */
function tituloDePagina(parametros, opciones) {
  const q = parametros.get("q");
  if (q) return `Resultados de «${q}»`;
  const slug = parametros.get("categoria");
  if (slug && opciones) {
    for (const raiz of opciones.categorias) {
      if (raiz.slug === slug) return raiz.nombre;
      const hija = raiz.subcategorias.find((s) => s.slug === slug);
      if (hija) return hija.nombre;
    }
  }
  const publico = parametros.get("publico");
  if (publico === "mujer") return "Mujeres";
  if (publico === "hombre") return "Hombres";
  if (publico === "unisex") return "Unisex";
  return "Toda la tienda";
}
