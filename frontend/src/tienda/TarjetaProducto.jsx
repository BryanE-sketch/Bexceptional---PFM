// Tarjeta de un producto. Al pasar por encima de un color, cambia la foto a ese color.
import { useState } from "react";
import { formatearPrecio } from "./formato.js";

export default function TarjetaProducto({ producto }) {
  const [colorActivo, setColorActivo] = useState(null);
  const imagen = (colorActivo && producto.imagenes_por_color[colorActivo]) || producto.imagen;
  // Si el usuario eligió un color, la ficha se abre directamente en ese color
  const enlace = colorActivo ? `${producto.url}?color=${colorActivo}` : producto.url;

  return (
    <article className="group">
      <a href={enlace} className="block focus-visible:outline-none">
        <div className="relative aspect-3/4 overflow-hidden rounded-xl bg-claro-2 ring-negro ring-offset-2 group-focus-within:ring-2">
          {imagen ? (
            <img src={imagen} alt="" loading="lazy" decoding="async"
                 className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]" />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-linea">Sin imagen</div>
          )}
          {producto.agotado && (
            <span className="absolute left-3 top-3 rounded-full bg-negro px-3 py-1 text-xs font-bold text-crema">Agotado</span>
          )}
        </div>
        <h2 className="mt-3 text-sm font-bold text-negro">{producto.nombre}</h2>
      </a>
      <p className="text-sm text-linea">{producto.categoria.nombre}</p>
      <p className="mt-1 text-sm font-bold text-negro">{formatearPrecio(producto.precio)}</p>

      {producto.colores.length > 1 && (
        <ul className="mt-2 flex gap-2" aria-label="Colores disponibles">
          {producto.colores.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                title={c.nombre}
                aria-label={`Ver en ${c.nombre}`}
                aria-pressed={colorActivo === c.id}
                onMouseEnter={() => setColorActivo(c.id)}
                onFocus={() => setColorActivo(c.id)}
                onClick={() => setColorActivo(c.id)}
                className={`h-5 w-5 rounded-full border border-black/20 ${colorActivo === c.id ? "ring-2 ring-negro ring-offset-1" : ""}`}
                style={{ backgroundColor: c.codigo_hex }}
              />
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
