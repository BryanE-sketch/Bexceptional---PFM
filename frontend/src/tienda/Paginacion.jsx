// Paginación numerada: « Anterior 1 2 3 Siguiente »
export default function Paginacion({ actual, total, alCambiar }) {
  if (total <= 1) return null;
  const paginas = Array.from({ length: total }, (_, i) => i + 1);
  const boton = "flex h-11 min-w-11 items-center justify-center rounded-full px-4 text-sm font-semibold";

  return (
    <nav aria-label="Paginación" className="mt-12 flex flex-wrap items-center justify-center gap-2">
      <button type="button" className={`${boton} border border-black/15 disabled:opacity-40`}
              disabled={actual <= 1} onClick={() => alCambiar(actual - 1)}>
        Anterior
      </button>
      {paginas.map((n) => (
        <button key={n} type="button" aria-current={n === actual ? "page" : undefined} onClick={() => alCambiar(n)}
                className={`${boton} ${n === actual ? "bg-negro text-crema" : "hover:bg-claro-2"}`}>
          {n}
        </button>
      ))}
      <button type="button" className={`${boton} border border-black/15 disabled:opacity-40`}
              disabled={actual >= total} onClick={() => alCambiar(actual + 1)}>
        Siguiente
      </button>
    </nav>
  );
}
