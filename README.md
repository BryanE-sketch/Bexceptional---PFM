<p align="center">
  <img src="docs/marca/logo-simbolo.png" alt="Bexceptional" width="120">
</p>

<h1 align="center">BEXCEPTIONAL</h1>
<p align="center"><em>Rise above the ordinary.</em></p>

<p align="center">
  <a href="https://github.com/BryanE-sketch/Bexceptional---PFM/actions/workflows/tests.yml">
    <img src="https://github.com/BryanE-sketch/Bexceptional---PFM/actions/workflows/tests.yml/badge.svg" alt="Tests">
  </a>
</p>

---

Proyecto Final del **Máster en Desarrollo Full Stack**.

**Demo:** [bexceptional.onrender.com](https://bexceptional.onrender.com) · Alojada en el plan gratuito de Render: en horario laboral se mantiene activa; fuera de él, la primera visita puede tardar hasta un minuto.

**Bexceptional** es una tienda online de ropa deportiva y una comunidad que
promueve la disciplina, la constancia y la superación personal, inspirada en
el concepto estoico de _areté_: la excelencia que se practica cada día.

## Funcionalidades

- **Tienda** en React con filtros (público, categoría, color, talla, actividad, precio, stock),
  búsqueda, orden y paginación. El estado de los filtros vive en la URL.
- **API REST pública** de solo lectura, documentada con OpenAPI en `/api/docs/`.
- **Carrito** con HTMX (cantidades y borrado sin recargar la página).
- **Cuentas**: registro, acceso con bloqueo tras 5 intentos fallidos, perfil y pedidos.
- **Pago simulado** con tarjeta (validación Luhn), PayPal y Apple Pay. No se guardan datos de tarjeta.
- **Favoritos** con HTMX.
- **Hábitos**: consejos, artículos con fuentes y un rastreador descargable para 4 disciplinas.

## Tecnologías

| Capa                    | Tecnología                                                       |
| ----------------------- | ---------------------------------------------------------------- |
| Backend                 | Python 3.13 · Django 5.2 · Django REST Framework · django-filter |
| Base de datos           | PostgreSQL (Neon en producción)                                  |
| Frontend                | Plantillas de Django · HTMX · Tailwind CSS 4 · React 19 (Vite)   |
| Imágenes                | Pillow · Cloudinary (django-cloudinary-storage)                  |
| Documentación de la API | drf-spectacular (Swagger)                                        |
| Despliegue              | Render · gunicorn · WhiteNoise · GitHub Actions                  |

## Puesta en marcha en local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install
cp .env.example .env            # y rellena tus datos
python manage.py migrate
python manage.py cargar_catalogo_demo
python manage.py cargar_habitos_demo
npm run css:build && npm run htmx:copiar && npm run build
python manage.py runserver
```

Tests: `python manage.py test`

## Despliegue

| Servicio       | Uso                                  | Plan                     |
| -------------- | ------------------------------------ | ------------------------ |
| Render         | Servidor web (gunicorn + WhiteNoise) | Gratuito                 |
| Neon           | PostgreSQL                           | Gratuito                 |
| Cloudinary     | Imágenes y archivos subidos          | Gratuito                 |
| GitHub Actions | Tests en cada push y servidor activo | Gratuito                 |
|                | en horario laboral                   |                          |
| Dominio propio | —                                    | Único coste del proyecto |

`render.yaml` describe el servicio y `build.sh` los pasos de cada despliegue
(dependencias, compilación del frontend, estáticos, migraciones y datos iniciales).
Los secretos solo existen como variables de entorno en Render; nunca en el repositorio.

## Documentación

- [Propuesta del proyecto](docs/propuesta/Propuesta_Bexceptional_Brayan_Echeverri.pdf)

## Autor

**Brayan Echeverri Medina** · echeverry28brayan@gmail.com
