"""
Carga el catálogo de demostración de Bexceptional.

    python manage.py cargar_catalogo_demo
    python manage.py cargar_catalogo_demo --retirar-color "#A9A9A9" --reemplazar-imagenes --retirar-incompletos

- 6 productos (3 camisetas y 3 riñoneras) en negro y blanco, con foto delantera y trasera.
- --retirar-incompletos borra los 9 productos de demostración antiguos que no tienen
  sus 4 fotos y desactiva las categorías que se quedan vacías.
- Todas las tallas con stock entre 11 y 25 unidades.
- En cada categoría, UNA variante elegida al azar queda agotada (stock 0) como demostración.
- Se puede ejecutar varias veces: actualiza en lugar de duplicar.
"""
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogo.models import Categoria, Color, Disciplina, ImagenProducto, Producto, Talla, Variante

CARPETA_IMAGENES = Path(settings.BASE_DIR) / "demo" / "catalogo"

# nombre, código hexadecimal, abreviatura para el SKU
COLORES = {
    "negro": ("Negro", "#121214", "NEG"),
    "blanco": ("Blanco", "#FFFFFF", "BLA"),
}

# Cada color lleva dos fotos: delante (fénix) y detrás (BEXCEPTIONAL + mensaje)
VISTAS = [("frente", "vista delantera"), ("espalda", "vista trasera")]

# nombre de la talla → orden en que se muestra
TALLAS = {
    "XS": 1, "S": 2, "M": 3, "L": 4, "XL": 5, "XXL": 6,
    "35-38": 10, "39-42": 11, "43-46": 12,
    "Única": 20,
}
ROPA = ["XS", "S", "M", "L", "XL", "XXL"]
PIES = ["35-38", "39-42", "43-46"]
UNICA = ["Única"]

# slug de la categoría → (nombre, slug del padre, tallas, abreviatura SKU)
CATEGORIAS = {
    "camisetas": ("Camisetas", "ropa", ROPA, "CAM"),
    "rinoneras": ("Riñoneras", "accesorios", UNICA, "RIN"),
}

# Productos de demostración antiguos que se quedaron sin sus 4 fotos (2 colores × delante/detrás).
# Se retiran con --retirar-incompletos; sus categorías se desactivan si se quedan vacías.
PRODUCTOS_RETIRADOS = [
    "calcetines-tobilleros-running", "calcetines-media-cana-training", "calcetines-pack-crew",
    "gorra-running-ligera", "gorra-baseball-curva", "visera-training",
    "straps-algodon", "straps-acolchados", "ganchos-levantamiento",
]
CATEGORIAS_RETIRADAS = ["calcetines", "gorras", "agarraderas"]

PRODUCTOS = [
    # slug, nombre, categoría, precio, público, disciplinas, descripción
    ("camiseta-arete", "Camiseta Areté", "camisetas", "29.95", "unisex", ["gimnasio", "running"],
     "Corte ajustado y tejido técnico que expulsa el sudor. Costuras planas para que no roce "
     "y el fénix pequeño en el pecho. Para entrenar todos los días."),
    ("camiseta-fenix-oversize", "Camiseta Fénix Oversize", "camisetas", "34.95", "unisex", ["gimnasio"],
     "Algodón grueso, hombro caído y corte amplio. El fénix grande en el pecho recuerda la idea de la marca: "
     "levantarse una vez más."),
    ("camiseta-sin-mangas-training", "Camiseta sin mangas Training", "camisetas", "24.95", "unisex", ["gimnasio"],
     "Sisa amplia para moverse sin límites en los días de hombro y espalda. Tejido ligero y transpirable."),
    ("rinonera-running", "Riñonera Running", "rinoneras", "22.95", "unisex", ["running"],
     "Cinturón elástico de perfil bajo que no rebota al correr. Cabe el móvil, las llaves y un gel."),
    ("rinonera-cruzada-urban", "Riñonera Cruzada Urban", "rinoneras", "39.95", "unisex", [],
     "Bandolera compacta de nailon resistente al agua, con correa ajustable. Del gimnasio a la calle."),
    ("mini-rinonera-gym", "Mini riñonera Gym", "rinoneras", "19.95", "unisex", ["gimnasio"],
     "Formato mini para lo imprescindible: tarjeta del gimnasio, auriculares y llaves."),
]


class Command(BaseCommand):
    help = "Carga 6 productos de demostración con variantes, stock e imágenes."

    def add_arguments(self, parser):
        parser.add_argument("--semilla", type=int, default=2026,
                            help="Semilla del azar: con la misma semilla se agotan siempre las mismas variantes.")
        parser.add_argument("--retirar-color", metavar="NOMBRE_O_HEX", action="append", default=[],
                            help="Borra las variantes y fotos de ese color en TODO el catálogo y después el color. "
                                 "Acepta el nombre (Magenta) o el código (#A9A9A9). Se puede repetir.")
        parser.add_argument("--reemplazar-imagenes", action="store_true",
                            help="Borra las fotos actuales de los productos de demostración y carga las nuevas.")
        parser.add_argument("--retirar-incompletos", action="store_true",
                            help="Borra los productos de demostración antiguos sin fotos completas "
                                 "y desactiva las categorías que se quedan vacías.")

    @transaction.atomic
    def handle(self, *args, **opciones):
        if not CARPETA_IMAGENES.is_dir():
            raise CommandError(f"No encuentro la carpeta de imágenes: {CARPETA_IMAGENES}")
        azar = random.Random(opciones["semilla"])

        if opciones["retirar_incompletos"]:
            self.retirar_incompletos()
        for color in opciones["retirar_color"]:
            self.retirar_color(color)
        if opciones["reemplazar_imagenes"]:
            borradas, _ = ImagenProducto.objects.filter(producto__slug__in=[p[0] for p in PRODUCTOS]).delete()
            self.stdout.write(f"Fotos anteriores retiradas: {borradas}. (Para borrar los archivos: limpiar_media --borrar)")

        colores = {clave: self.color(*datos[:2]) for clave, datos in COLORES.items()}
        tallas = {nombre: Talla.objects.update_or_create(nombre=nombre, defaults={"orden": orden})[0]
                  for nombre, orden in TALLAS.items()}
        categorias = {slug: self.categoria(slug, nombre, padre)
                      for slug, (nombre, padre, _, _) in CATEGORIAS.items()}

        # 1) Elegimos al azar qué variante se agota en cada categoría
        agotadas = set()
        for slug_cat, (_, _, tallas_cat, _) in CATEGORIAS.items():
            productos_cat = [p[0] for p in PRODUCTOS if p[2] == slug_cat]
            if not productos_cat:
                continue
            agotadas.add((azar.choice(productos_cat), azar.choice(list(COLORES)), azar.choice(tallas_cat)))

        # 2) Productos, variantes e imágenes
        for orden, (slug, nombre, slug_cat, precio, publico, disciplinas, descripcion) in enumerate(PRODUCTOS):
            _, _, tallas_cat, abrev_cat = CATEGORIAS[slug_cat]
            producto, creado = Producto.objects.update_or_create(
                slug=slug,
                defaults={
                    "nombre": nombre, "descripcion": descripcion, "precio": Decimal(precio),
                    "categoria": categorias[slug_cat], "publico": publico, "activo": True,
                },
            )
            producto.disciplinas.set(Disciplina.objects.filter(slug__in=disciplinas))

            for clave_color, (_, _, abrev_color) in COLORES.items():
                for nombre_talla in tallas_cat:
                    agotada = (slug, clave_color, nombre_talla) in agotadas
                    sku = f"BX-{abrev_cat}{orden + 1:02d}-{abrev_color}-{self.abreviar(nombre_talla)}"
                    Variante.objects.update_or_create(
                        producto=producto, talla=tallas[nombre_talla], color=colores[clave_color],
                        defaults={"sku": sku, "stock": 0 if agotada else azar.randint(11, 25)},
                    )
                    if agotada:
                        self.stdout.write(self.style.WARNING(
                            f"  Agotada (demo): {nombre} · {COLORES[clave_color][0]} · {nombre_talla}"))
                self.imagen(producto, colores[clave_color], clave_color)

            self.stdout.write(f"{'Creado' if creado else 'Actualizado'}: {nombre}")

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {len(PRODUCTOS)} productos, {Variante.objects.filter(producto__slug__in=[p[0] for p in PRODUCTOS]).count()} variantes."))

    # ── Ayudantes ──────────────────────────────────────────────

    def color(self, nombre, codigo_hex):
        """Reutiliza el color si ya existe con ese código (aunque se llame distinto, p. ej. 'Gris oscuro')."""
        existente = Color.objects.filter(codigo_hex__iexact=codigo_hex).first()
        if existente:
            return existente
        return Color.objects.get_or_create(nombre=nombre, defaults={"codigo_hex": codigo_hex})[0]

    def categoria(self, slug, nombre, slug_padre):
        """Busca la categoría por slug o por nombre; si no existe la crea bajo su padre."""
        padre = Categoria.objects.filter(slug=slug_padre).first()
        if padre is None:
            padre = Categoria.objects.create(nombre=slug_padre.capitalize(), slug=slug_padre)
        categoria = (Categoria.objects.filter(slug=slug).first()
                     or Categoria.objects.filter(nombre__iexact=nombre).first())
        if categoria is None:
            return Categoria.objects.create(nombre=nombre, slug=slug, padre=padre)
        if categoria.padre_id != padre.pk:
            self.stdout.write(self.style.WARNING(
                f"  Aviso: '{categoria}' no cuelga de '{padre.nombre}'. Revísalo en el panel."))
        return categoria

    def imagen(self, producto, color, clave_color):
        """
        Dos fotos por color (delante y detrás). Si aún no existen las nuevas,
        usa la foto única antigua ({slug}-{color}.webp). Nunca duplica.
        """
        if ImagenProducto.objects.filter(producto=producto, color=color).exists():
            return
        rutas = [(CARPETA_IMAGENES / f"{producto.slug}-{clave_color}-{vista}.webp", texto) for vista, texto in VISTAS]
        rutas = [(ruta, texto) for ruta, texto in rutas if ruta.exists()]
        if not rutas:
            antigua = CARPETA_IMAGENES / f"{producto.slug}-{clave_color}.webp"
            rutas = [(antigua, "vista delantera")] if antigua.exists() else []
        if not rutas:
            self.stdout.write(self.style.WARNING(f"  Faltan las fotos de {producto.slug} en {clave_color}"))
            return
        for orden, (ruta, texto) in enumerate(rutas):
            with ruta.open("rb") as archivo:
                ImagenProducto.objects.create(
                    producto=producto, color=color, orden=orden,
                    imagen=File(archivo, name=ruta.name),
                    texto_alternativo=f"{producto.nombre} en color {color.nombre.lower()}, {texto}",
                )

    def retirar_incompletos(self):
        """
        Borra los productos antiguos. En cascada se van sus variantes, fotos, favoritos,
        líneas de carrito y reseñas; los pedidos NO se pierden porque cada línea de pedido
        guarda una copia del nombre y el precio (y su variante pasa a NULL).
        """
        borrados = 0
        for producto in Producto.objects.filter(slug__in=PRODUCTOS_RETIRADOS):
            self.stdout.write(self.style.WARNING(f"  Retirado: {producto.nombre}"))
            producto.delete()
            borrados += 1
        # Una categoría vacía no se borra (otros datos podrían apuntar a ella): se desactiva,
        # y así desaparece de la tienda, de los menús y de los filtros de la API.
        desactivadas = (Categoria.objects.filter(slug__in=CATEGORIAS_RETIRADAS, activa=True)
                        .exclude(productos__isnull=False).update(activa=False))
        self.stdout.write(f"Productos incompletos retirados: {borrados}. Categorías desactivadas: {desactivadas}.")

    def retirar_color(self, nombre):
        if nombre.startswith("#"):
            color = Color.objects.filter(codigo_hex__iexact=nombre).first()
        else:
            color = Color.objects.filter(nombre__iexact=nombre).first()
        if color is None:
            self.stdout.write(f"El color '{nombre}' no existe; nada que retirar.")
            return
        variantes, _ = Variante.objects.filter(color=color).delete()
        imagenes, _ = ImagenProducto.objects.filter(color=color).delete()
        color.delete()
        self.stdout.write(self.style.WARNING(
            f"Color '{nombre}' retirado: {variantes} objetos de variantes y {imagenes} de imágenes borrados."))

    @staticmethod
    def abreviar(talla):
        return {"Única": "U"}.get(talla, talla.replace("-", ""))
