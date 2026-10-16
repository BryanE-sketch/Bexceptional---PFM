"""
Carga el catálogo de demostración de Bexceptional.

    python manage.py cargar_catalogo_demo
    python manage.py cargar_catalogo_demo --retirar-color Magenta

- 15 productos (3 por categoría) en negro, blanco y gris.
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
    "gris": ("Gris", "#A9A9A9", "GRI"),
}

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
    "calcetines": ("Calcetines", "accesorios", PIES, "CAL"),
    "gorras": ("Gorras", "accesorios", UNICA, "GOR"),
    "agarraderas": ("Agarraderas", "accesorios", UNICA, "AGA"),
}

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
    ("calcetines-tobilleros-running", "Calcetines tobilleros Running", "calcetines", "12.95", "unisex", ["running"],
     "Corte bajo, zona acolchada en talón y puntera y tejido que seca rápido. Se venden por pares."),
    ("calcetines-media-cana-training", "Calcetines media caña Training", "calcetines", "14.95", "unisex", ["gimnasio"],
     "Protegen la espinilla en el peso muerto y sujetan el tobillo. Puño acanalado que no se cae."),
    ("calcetines-pack-crew", "Pack de 3 calcetines Crew", "calcetines", "24.95", "unisex", [],
     "Tres pares de algodón peinado para el día a día. El básico que siempre falta."),
    ("gorra-running-ligera", "Gorra Running ligera", "gorras", "24.95", "unisex", ["running"],
     "Copa baja y paneles perforados para ventilar. Pesa muy poco y se lava a mano."),
    ("gorra-baseball-curva", "Gorra Baseball curva", "gorras", "27.95", "unisex", [],
     "Seis paneles estructurados, visera curva y cierre ajustable. El fénix bordado al frente."),
    ("visera-training", "Visera Training", "gorras", "19.95", "unisex", ["running"],
     "Protege del sol sin dar calor en la cabeza. Banda interior que absorbe el sudor."),
    ("straps-algodon", "Straps de algodón", "agarraderas", "14.95", "unisex", ["gimnasio"],
     "Correas de algodón resistente para que el agarre no limite tus tirones pesados. Se venden por pares."),
    ("straps-acolchados", "Straps acolchados", "agarraderas", "19.95", "unisex", ["gimnasio"],
     "Como los de algodón, pero con almohadilla de neopreno en la muñeca para series largas."),
    ("ganchos-levantamiento", "Ganchos de levantamiento", "agarraderas", "29.95", "unisex", ["gimnasio"],
     "Gancho de acero con muñequera acolchada. Para series de remo y peso muerto donde el agarre falla antes que la espalda."),
]


class Command(BaseCommand):
    help = "Carga 15 productos de demostración con variantes, stock e imágenes."

    def add_arguments(self, parser):
        parser.add_argument("--semilla", type=int, default=2026,
                            help="Semilla del azar: con la misma semilla se agotan siempre las mismas variantes.")
        parser.add_argument("--retirar-color", metavar="NOMBRE",
                            help="Borra las variantes y fotos de ese color en TODO el catálogo y después el color.")

    @transaction.atomic
    def handle(self, *args, **opciones):
        if not CARPETA_IMAGENES.is_dir():
            raise CommandError(f"No encuentro la carpeta de imágenes: {CARPETA_IMAGENES}")
        azar = random.Random(opciones["semilla"])

        if opciones["retirar_color"]:
            self.retirar_color(opciones["retirar_color"])

        colores = {clave: self.color(*datos[:2]) for clave, datos in COLORES.items()}
        tallas = {nombre: Talla.objects.update_or_create(nombre=nombre, defaults={"orden": orden})[0]
                  for nombre, orden in TALLAS.items()}
        categorias = {slug: self.categoria(slug, nombre, padre)
                      for slug, (nombre, padre, _, _) in CATEGORIAS.items()}

        # 1) Elegimos al azar qué variante se agota en cada categoría
        agotadas = set()
        for slug_cat, (_, _, tallas_cat, _) in CATEGORIAS.items():
            productos_cat = [p[0] for p in PRODUCTOS if p[2] == slug_cat]
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
        """Una foto por color. Si ya existe, no la duplica."""
        if ImagenProducto.objects.filter(producto=producto, color=color).exists():
            return
        ruta = CARPETA_IMAGENES / f"{producto.slug}-{clave_color}.webp"
        if not ruta.exists():
            self.stdout.write(self.style.WARNING(f"  Falta la imagen {ruta.name}"))
            return
        with ruta.open("rb") as archivo:
            ImagenProducto.objects.create(
                producto=producto, color=color, orden=0,
                imagen=File(archivo, name=ruta.name),
                texto_alternativo=f"{producto.nombre} en color {color.nombre.lower()}",
            )

    def retirar_color(self, nombre):
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
