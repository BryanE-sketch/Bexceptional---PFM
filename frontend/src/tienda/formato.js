const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });

/** "29.95" → "29,95 €" */
export const formatearPrecio = (precio) => euros.format(Number(precio));
