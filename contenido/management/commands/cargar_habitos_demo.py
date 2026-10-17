"""
Carga el contenido de la sección Hábitos.

    python manage.py cargar_habitos_demo

- Las 4 disciplinas (Levantar pesas, Correr, Alimentación balanceada, Descanso activo)
  con su descripción.
- 3 consejos por disciplina y 1 artículo por disciplina (+1 general sobre hábitos),
  todos con su fuente científica enlazada.
- El rastreador de hábitos en PDF como recurso descargable.
- Relaciona los productos de demostración con su disciplina.

Se puede ejecutar varias veces: actualiza en lugar de duplicar.
Los textos son divulgación redactada por Bexceptional a partir de las fuentes citadas;
no sustituyen el consejo de un profesional sanitario.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogo.models import Disciplina, Producto
from contenido.models import Articulo, Consejo, FuenteArticulo, Recurso

# ── Fuentes (todas comprobadas) ─────────────────────────────────
OMS_ACTIVIDAD = ("OMS (2020). Directrices sobre actividad física y hábitos sedentarios",
                 "https://www.who.int/publications/i/item/9789240015128")
OMS_DIETA = ("OMS. Alimentación sana (nota descriptiva)",
             "https://www.who.int/news-room/fact-sheets/detail/healthy-diet")
SCHOENFELD = ("Schoenfeld, Ogborn y Krieger (2017). J Sports Sci",
              "https://pubmed.ncbi.nlm.nih.gov/27433992/")
ACSM = ("ACSM (2009). Progression models in resistance training",
        "https://pubmed.ncbi.nlm.nih.gov/19204579/")
ISSN_PROTEINA = ("Jäger et al. (2017). ISSN: proteína y ejercicio",
                 "https://pubmed.ncbi.nlm.nih.gov/28642676/")
SEILER = ("Seiler (2010). Int J Sports Physiol Perform",
          "https://pubmed.ncbi.nlm.nih.gov/20861519/")
NIELSEN = ("Nielsen et al. (2014). J Orthop Sports Phys Ther",
           "https://doi.org/10.2519/jospt.2014.5164")
LAUERSEN = ("Lauersen, Bertelsen y Andersen (2014). Br J Sports Med",
            "https://bjsm.bmj.com/content/48/11/871")
GSSI_BEBIDA = ("GSSI. Beber planificado o beber según la sed (2018)",
               "https://www.gssiweb.org/en/sports-science-exchange/article/"
               "fluid-intake-strategies-for-optimal-hydration-and-performance-planned-drinking-vs.-drinking-to-thirst")
WATSON = ("Watson et al. (2015). Consenso AASM/SRS sobre horas de sueño",
          "https://pubmed.ncbi.nlm.nih.gov/25979105/")
HUBERMAN = ("Huberman Lab. Toolkit for Sleep",
            "https://www.hubermanlab.com/newsletter/toolkit-for-sleep")
MAH = ("Mah et al. (2011). Sleep (baloncesto universitario)",
       "https://pmc.ncbi.nlm.nih.gov/articles/PMC3119836/")
LALLY = ("Lally et al. (2010). How are habits formed? (resumen de UCL)",
         "https://www.ucl.ac.uk/news/2009/aug/how-long-does-it-take-form-habit")

DISCIPLINAS = {
    "levantar-pesas": {
        "nombre": "Levantar pesas",
        "orden": 1,
        "descripcion": "Entrenar la fuerza construye músculo, protege tus articulaciones y te hace más "
                       "resistente a las lesiones. La clave no es entrenar al límite, sino progresar poco a poco.",
        "productos": ["camiseta-sin-mangas-training", "straps-algodon", "straps-acolchados",
                      "ganchos-levantamiento", "mini-rinonera-gym", "calcetines-media-cana-training"],
        "consejos": [
            ("Fuerza, al menos 2 días por semana",
             "La OMS recomienda a los adultos trabajar los grandes grupos musculares dos o más días a la "
             "semana, además de la actividad aeróbica.", OMS_ACTIVIDAD),
            ("Unas 10 series por músculo a la semana",
             "Un metaanálisis encontró más crecimiento muscular con 10 o más series semanales por grupo "
             "muscular que con menos de 5. Más no siempre es mejor: sube el volumen de forma gradual.", SCHOENFELD),
            ("Progresa poco a poco",
             "Aumentar de forma gradual el peso, las repeticiones o las series (sobrecarga progresiva) es el "
             "principio básico para seguir mejorando sin estancarte.", ACSM),
        ],
        "articulo": {
            "titulo": "Fuerza: lo esencial para empezar con buen pie",
            "slug": "fuerza-lo-esencial",
            "resumen": "Cuántos días entrenar, cuántas series hacer y cómo progresar sin lesionarte.",
            "cuerpo": (
                "Entrenar la fuerza no es solo para culturistas. La Organización Mundial de la Salud recomienda "
                "a todos los adultos ejercicios de fortalecimiento muscular al menos dos días por semana, porque "
                "mejoran la salud ósea, el metabolismo y la autonomía con los años.\n"
                "Para ganar músculo, el volumen semanal importa. El metaanálisis de Schoenfeld y colaboradores "
                "(2017) observó una relación dosis-respuesta: quienes hacían 10 o más series semanales por grupo "
                "muscular ganaban más masa muscular que quienes hacían menos de 5. Si estás empezando, de 6 a 10 "
                "series bien hechas por músculo son un punto de partida razonable.\n"
                "El motor del progreso es la sobrecarga progresiva: aumentar poco a poco el peso, las repeticiones "
                "o las series. El Colegio Americano de Medicina del Deporte (ACSM) recomienda subir la carga de "
                "forma gradual cuando puedas completar con buena técnica las repeticiones previstas.\n"
                "Tres hábitos que marcan la diferencia: anota tus entrenamientos para saber cuándo subir el peso, "
                "prioriza la técnica antes que la carga y deja al menos un día entre sesiones intensas del mismo "
                "grupo muscular.\n"
                "Recuerda que el músculo se construye fuera del gimnasio: la proteína suficiente y el sueño son "
                "parte del entrenamiento. Encontrarás más en las secciones de Alimentación balanceada y Descanso activo."
            ),
            "fuentes": [OMS_ACTIVIDAD, SCHOENFELD, ACSM],
        },
    },
    "correr": {
        "nombre": "Correr",
        "orden": 2,
        "descripcion": "Correr mejora tu corazón y tu cabeza. Para disfrutarlo durante años, la mayoría "
                       "de los kilómetros deben ser suaves y el volumen debe crecer con paciencia.",
        "productos": ["camiseta-arete", "rinonera-running", "calcetines-tobilleros-running",
                      "gorra-running-ligera", "visera-training"],
        "consejos": [
            ("La mayoría de tus kilómetros, suaves",
             "Los corredores de resistencia de élite hacen en torno al 80 % de su entrenamiento a baja "
             "intensidad y reservan el resto para trabajo intenso.", SEILER),
            ("Aumenta la distancia con paciencia",
             "En corredores principiantes, subir más de un 30 % la distancia semanal en dos semanas se "
             "asoció con más lesiones relacionadas con la distancia.", NIELSEN),
            ("La fuerza también es para corredores",
             "Una revisión con más de 26 000 deportistas encontró que el entrenamiento de fuerza redujo las "
             "lesiones deportivas a menos de un tercio.", LAUERSEN),
        ],
        "articulo": {
            "titulo": "Correr más y lesionarte menos",
            "slug": "correr-mas-lesionarte-menos",
            "resumen": "La regla del 80/20, cómo subir el kilometraje y por qué el gimnasio protege tus piernas.",
            "cuerpo": (
                "La mayoría de las lesiones al correr no llegan por un mal día, sino por hacer demasiado "
                "demasiado pronto. Por eso las tres ideas de este artículo tienen que ver con la paciencia.\n"
                "Primera: corre suave casi siempre. Stephen Seiler, uno de los investigadores de referencia en "
                "deportes de resistencia, describió que los atletas de élite hacen alrededor del 80 % de su "
                "entrenamiento a baja intensidad, a un ritmo en el que podrías mantener una conversación. El 20 % "
                "restante es el trabajo de calidad: series, cambios de ritmo o cuestas.\n"
                "Segunda: sube el volumen poco a poco. En un estudio con corredores principiantes, quienes "
                "aumentaron su distancia semanal más de un 30 % en dos semanas tuvieron más lesiones relacionadas "
                "con la distancia que quienes progresaron con más calma. Planifica semanas de subida y, cada "
                "cierto tiempo, una semana más ligera.\n"
                "Tercera: entrena la fuerza. Una revisión con más de 26 000 deportistas concluyó que el "
                "entrenamiento de fuerza redujo las lesiones deportivas a menos de un tercio. Dos sesiones "
                "semanales de sentadillas, zancadas, peso muerto y gemelos son una gran inversión.\n"
                "Y un detalle práctico: en tiradas largas o con calor, lleva agua y piensa en cuánto vas a beber "
                "antes de salir. Lo verás en Alimentación balanceada."
            ),
            "fuentes": [SEILER, NIELSEN, LAUERSEN],
        },
    },
    "alimentacion-balanceada": {
        "nombre": "Alimentación balanceada",
        "orden": 3,
        "descripcion": "Comer bien no es seguir una dieta perfecta: es repetir cada día unas pocas "
                       "decisiones sencillas que sostienen tu energía, tu recuperación y tu salud.",
        "productos": ["rinonera-cruzada-urban", "calcetines-pack-crew"],
        "consejos": [
            ("400 g de fruta y verdura al día",
             "La OMS recomienda al menos 400 gramos diarios de frutas y verduras, y limitar los azúcares "
             "libres a menos del 10 % de la energía y la sal a menos de 5 g al día.", OMS_DIETA),
            ("Proteína suficiente y repartida",
             "Para personas que entrenan, la ISSN recomienda entre 1,4 y 2,0 g de proteína por kilo de peso "
             "al día, repartida en varias comidas a lo largo del día.", ISSN_PROTEINA),
            ("Planifica la bebida en sesiones largas",
             "Pesarte antes y después de entrenar te dice cuánto líquido pierdes. En sesiones largas o con "
             "calor, un plan de hidratación es más fiable que esperar a tener sed.", GSSI_BEBIDA),
        ],
        "articulo": {
            "titulo": "Comer para rendir: tres pilares sin complicaciones",
            "slug": "comer-para-rendir",
            "resumen": "Fruta y verdura, proteína suficiente e hidratación: lo que dice la evidencia y cómo aplicarlo.",
            "cuerpo": (
                "No necesitas contar cada caloría para comer bien. Basta con cuidar tres pilares y repetirlos "
                "hasta que se vuelvan automáticos.\n"
                "Pilar 1, la base: fruta, verdura y alimentos poco procesados. La OMS recomienda al menos 400 "
                "gramos de frutas y verduras al día (unas cinco raciones), limitar los azúcares libres a menos "
                "del 10 % de la energía diaria y la sal a menos de 5 gramos. Un truco sencillo: que la mitad de "
                "tu plato sean verduras.\n"
                "Pilar 2, la proteína. Si entrenas, tus necesidades son algo mayores. La Sociedad Internacional "
                "de Nutrición Deportiva (ISSN) recomienda entre 1,4 y 2,0 gramos de proteína por kilo de peso al "
                "día, repartidos en varias comidas, de forma que cada una aporte una buena ración (por ejemplo, "
                "huevos, legumbres, lácteos, pescado o carne).\n"
                "Pilar 3, la hidratación. En el día a día, bebe con regularidad. En sesiones largas o con calor, "
                "el Gatorade Sports Science Institute (GSSI) explica que planificar cuánto beber, a partir de lo "
                "que sudas, es más fiable que esperar a tener sed. Pésate antes y después de entrenar: la "
                "diferencia te da una idea de lo que has perdido.\n"
                "Si tienes una condición médica o un objetivo concreto, consulta con un dietista-nutricionista: "
                "estas son recomendaciones generales."
            ),
            "fuentes": [OMS_DIETA, ISSN_PROTEINA, GSSI_BEBIDA],
        },
    },
    "descanso-activo": {
        "nombre": "Descanso activo",
        "orden": 4,
        "descripcion": "Descansar también es entrenar. El sueño y la recuperación son el momento en el "
                       "que tu cuerpo convierte el esfuerzo en progreso.",
        "productos": ["camiseta-fenix-oversize", "gorra-baseball-curva"],
        "consejos": [
            ("Duerme 7 horas o más",
             "El consenso de la Academia Americana de Medicina del Sueño recomienda a los adultos dormir "
             "7 horas o más cada noche de forma habitual.", WATSON),
            ("Luz natural por la mañana",
             "Salir a la luz natural en los primeros 30-60 minutos tras despertar ayuda a ajustar tu reloj "
             "interno; unos 10 minutos en días despejados y más si está nublado.", HUBERMAN),
            ("Dormir más mejora el rendimiento",
             "En un estudio con jugadores de baloncesto universitario, alargar el sueño varias semanas "
             "mejoró su velocidad en sprint y su precisión en el tiro.", MAH),
        ],
        "articulo": {
            "titulo": "Descanso activo: el entrenamiento que no se ve",
            "slug": "descanso-activo-el-entrenamiento-que-no-se-ve",
            "resumen": "Cuánto dormir, cómo mejorar tu sueño con la luz y la cafeína y por qué el descanso te hace más rápido.",
            "cuerpo": (
                "Entrenar genera el estímulo; descansar permite que tu cuerpo se adapte. Sin descanso suficiente, "
                "el esfuerzo se queda a medias.\n"
                "Empieza por las horas. El consenso de la Academia Americana de Medicina del Sueño y la Sleep "
                "Research Society recomienda a los adultos dormir 7 horas o más por noche de forma habitual. "
                "Dormir menos se asocia con peor salud y peor rendimiento.\n"
                "Cuida tu reloj interno. El neurocientífico Andrew Huberman (Universidad de Stanford) resume en su "
                "guía de sueño algunas herramientas sencillas: salir a la luz natural en los primeros 30-60 "
                "minutos tras despertar, levantarte a una hora parecida cada día y evitar la cafeína en las 8-10 "
                "horas previas a acostarte.\n"
                "El sueño también se nota en la pista. En un estudio de la Universidad de Stanford, jugadores de "
                "baloncesto que alargaron su sueño durante varias semanas mejoraron su velocidad en sprint y su "
                "precisión en tiros libres y triples.\n"
                "Descanso activo no significa no moverse: en tus días libres, un paseo, movilidad suave o una "
                "bici tranquila ayudan a recuperarte sin sumar fatiga. Apúntalo en tu rastreador de hábitos."
            ),
            "fuentes": [WATSON, HUBERMAN, MAH],
        },
    },
}

ARTICULO_GENERAL = {
    "titulo": "¿Cuánto se tarda en crear un hábito?",
    "slug": "cuanto-se-tarda-en-crear-un-habito",
    "resumen": "Ni 21 días ni fuerza de voluntad infinita: lo que encontró la investigación y cómo usar el rastreador.",
    "cuerpo": (
        "Seguramente has oído que un hábito se crea en 21 días. La investigación dice otra cosa.\n"
        "En un estudio del University College London, Phillippa Lally y su equipo siguieron a personas que "
        "querían incorporar un hábito saludable, como beber agua con la comida o salir a correr. De media, la "
        "conducta tardó 66 días en volverse automática, con mucha variación entre personas: de 18 a 254 días.\n"
        "La buena noticia: fallar un día no echó por tierra el proceso. Lo importante fue la constancia a lo largo "
        "del tiempo, no la perfección.\n"
        "Por eso hemos diseñado el rastreador de hábitos de Bexceptional: marcar cada día lo que haces convierte "
        "un propósito difuso en algo visible. Elige un hábito pequeño, átalo a algo que ya haces (por ejemplo, "
        "estiramientos después de lavarte los dientes) y regístralo.\n"
        "Rise above the ordinary no va de un gran día, sino de muchos días normales bien hechos."
    ),
    "fuentes": [LALLY],
}


class Command(BaseCommand):
    help = "Carga disciplinas, consejos, artículos y el rastreador de la sección Hábitos."

    @transaction.atomic
    def handle(self, *args, **opciones):
        for slug, datos in DISCIPLINAS.items():
            disciplina = self.disciplina(slug, datos)

            for orden, (titulo, texto, (fuente, url)) in enumerate(datos["consejos"], start=1):
                Consejo.objects.update_or_create(
                    titulo=titulo,
                    defaults={"texto": texto, "disciplina": disciplina, "fuente_nombre": fuente,
                              "fuente_url": url, "orden": orden, "activo": True},
                )

            self.articulo(datos["articulo"], disciplina)

            productos = Producto.objects.filter(slug__in=datos["productos"])
            for producto in productos:
                producto.disciplinas.add(disciplina)
            self.stdout.write(f"{disciplina.nombre}: 3 consejos, 1 artículo, {productos.count()} productos.")

        self.articulo(ARTICULO_GENERAL, None)
        self.recurso()
        self.stdout.write(self.style.SUCCESS("Sección Hábitos lista."))

    def disciplina(self, slug, datos):
        """Busca por slug o por nombre (para respetar las que ya creaste en el panel)."""
        disciplina = (Disciplina.objects.filter(slug=slug).first()
                      or Disciplina.objects.filter(nombre__iexact=datos["nombre"]).first())
        if disciplina is None:
            disciplina = Disciplina(slug=slug, nombre=datos["nombre"])
        disciplina.descripcion = datos["descripcion"]
        disciplina.orden = datos["orden"]
        disciplina.activa = True
        disciplina.save()
        return disciplina

    def articulo(self, datos, disciplina):
        articulo, _ = Articulo.objects.update_or_create(
            slug=datos["slug"],
            defaults={"titulo": datos["titulo"], "resumen": datos["resumen"], "cuerpo": datos["cuerpo"],
                      "disciplina": disciplina, "estado": Articulo.Estado.PUBLICADO},
        )
        articulo.fuentes.all().delete()
        FuenteArticulo.objects.bulk_create(
            FuenteArticulo(articulo=articulo, nombre=nombre, url=url) for nombre, url in datos["fuentes"]
        )
        return articulo

    def recurso(self):
        pdf = Path(settings.BASE_DIR) / "docs" / "recursos" / "Bexceptional_Rastreador_de_Habitos.pdf"
        previa = Path(settings.BASE_DIR) / "demo" / "habitos" / "rastreador-previa.webp"
        if Recurso.objects.exists():
            # Si ya lo subiste desde el panel, solo le añadimos la vista previa si no la tiene
            for recurso in Recurso.objects.filter(imagen_previa="", tipo=Recurso.Tipo.RASTREADOR):
                if previa.exists():
                    with previa.open("rb") as imagen:
                        recurso.imagen_previa.save(previa.name, File(imagen))
            self.stdout.write("Ya hay recursos descargables: se conservan.")
            return
        if not pdf.exists():
            self.stdout.write(self.style.WARNING(f"No encuentro {pdf}: súbelo desde el panel."))
            return
        recurso = Recurso(
            titulo="Rastreador de hábitos",
            slug="rastreador-de-habitos",
            descripcion="PDF editable de 3 páginas: rueda mensual, seguimiento diario y diseño de hábitos.",
            tipo=Recurso.Tipo.RASTREADOR,
        )
        with pdf.open("rb") as archivo:
            recurso.archivo.save(pdf.name, File(archivo), save=False)
        if previa.exists():
            with previa.open("rb") as imagen:
                recurso.imagen_previa.save(previa.name, File(imagen), save=False)
        recurso.save()
        self.stdout.write("Rastreador de hábitos añadido a los descargables.")
