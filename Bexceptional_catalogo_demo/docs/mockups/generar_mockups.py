"""Genera los 45 mockups del catálogo demo (15 productos × 3 colores) en SVG."""
BIRD = __import__('re').search(r' d="([^"]+)"', open('static/img/fenix-oscuro.svg').read()).group(1)
BW, BH = 602, 749
W, H = 900, 1200
FONDO = "#F4F1EC"
COLORES = {  # slug: (color de la prenda, color del fénix)
    "negro": ("#1C1C1F", "#FFFFFF"),
    "blanco": ("#FCFCFB", "#121214"),
    "gris": ("#A9A9A9", "#121214"),
}

def fenix(cx, cy, alto, color, rot=0):
    s = alto / BH
    return (f'<g transform="rotate({rot} {cx} {cy})"><path transform="translate({cx - BW*s/2:.1f} {cy - alto/2:.1f}) scale({s:.4f})" '
            f'fill="{color}" fill-rule="evenodd" d="{BIRD}"/></g>')

def lienzo(contenido):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <filter id="sombra" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#3a2f25" flood-opacity="0.20"/></filter>
  <linearGradient id="luz" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.18"/><stop offset="0.5" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.12"/></linearGradient>
  <linearGradient id="metal" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6d6d70"/><stop offset="0.45" stop-color="#d9d9dc"/><stop offset="1" stop-color="#5a5a5d"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="{FONDO}"/>
{contenido}
</svg>'''

def pieza(d, base, sombra=True):
    """Una superficie con sombra, luz y un perfil fino (para que el blanco se distinga del fondo)."""
    f = ' filter="url(#sombra)"' if sombra else ''
    return (f'<g{f}><path d="{d}" fill="{base}" stroke="#000" stroke-opacity="0.10" stroke-width="2" stroke-linejoin="round"/></g>'
            f'<path d="{d}" fill="url(#luz)"/>')

def oscuro(d, op=0.12):
    return f'<path d="{d}" fill="#000" fill-opacity="{op}"/>'

def costuras(d, base):
    claro = base != "#FCFCFB"
    return (f'<g fill="none" stroke="#000" stroke-opacity="0.20" stroke-width="2.5" stroke-linecap="round"><path d="{d}"/></g>'
            + (f'<g fill="none" stroke="#fff" stroke-opacity="0.20" stroke-width="2" stroke-dasharray="5 6"><path d="{d}"/></g>' if claro else
               f'<g fill="none" stroke="#000" stroke-opacity="0.12" stroke-width="2" stroke-dasharray="5 6"><path d="{d}"/></g>'))

def mirror(pts):
    return pts + [(W - x, y) for x, y in reversed(pts)]

def poly(pts):
    return "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + " Z"

# ───────────── CAMISETAS ─────────────
def camiseta_arete(b, l):
    d = poly(mirror([(400, 250), (300, 280), (190, 400), (245, 470), (310, 415), (318, 640), (300, 900)]))
    return (pieza(d, b) + '<path d="M400,252 Q450,300 500,252" fill="none" stroke="#000" stroke-opacity="0.35" stroke-width="10"/>'
            + costuras('M400,254 L310,415 M500,254 L590,415 M190,400 L245,470 M710,400 L655,470 M300,890 Q450,902 600,890', b)
            + fenix(548, 370, 62, l))

def camiseta_oversize(b, l):
    d = poly(mirror([(385, 250), (245, 275), (100, 430), (185, 530), (250, 480), (240, 950)]))
    return (pieza(d, b) + '<path d="M385,240 Q450,300 515,240" fill="none" stroke="#000" stroke-opacity="0.3" stroke-width="14"/>'
            + costuras('M245,268 Q252,380 250,480 M655,268 Q648,380 650,480 M100,425 L185,530 M800,425 L715,530 M240,940 L660,940', b)
            + fenix(450, 470, 150, l))

def camiseta_tirantes(b, l):
    d = ('M385,230 L322,236 Q330,430 268,480 L282,950 L618,950 L632,480 Q570,430 578,236 L515,230 Q450,320 385,230 Z')
    return (pieza(d, b) + '<path d="M388,232 Q450,318 512,232" fill="none" stroke="#000" stroke-opacity="0.3" stroke-width="9"/>'
            + costuras('M322,240 Q330,430 270,482 M578,240 Q570,430 630,482 M282,940 L618,940', b)
            + fenix(540, 420, 60, l))

# ───────────── RIÑONERAS ─────────────
def rinonera_running(b, l):
    cinta = 'M70,560 Q450,520 830,560 L830,616 Q450,576 70,616 Z'
    bolsa = 'M255,520 Q450,490 645,520 Q675,610 645,700 Q450,730 255,700 Q225,610 255,520 Z'
    hebilla = '<rect x="760" y="548" width="44" height="64" rx="10" fill="#121214" fill-opacity="0.85"/><rect x="772" y="562" width="20" height="36" rx="4" fill="#fff" fill-opacity="0.25"/>'
    return (pieza(cinta, b) + oscuro(cinta, 0.10) + hebilla + pieza(bolsa, b)
            + '<path d="M275,548 Q450,522 625,548" fill="none" stroke="#000" stroke-opacity="0.45" stroke-width="5"/>'
            + '<rect x="600" y="528" width="14" height="30" rx="4" fill="#121214" fill-opacity="0.8"/>'
            + costuras('M262,690 Q450,718 638,690', b) + fenix(450, 625, 95, l))

def rinonera_cruzada(b, l):
    correa = '<path d="M250,600 C180,380 300,190 450,190 C600,190 720,380 650,600" fill="none" stroke="#000" stroke-opacity="0.10" stroke-width="50" stroke-linecap="round"/>' \
             f'<path d="M250,600 C180,380 300,190 450,190 C600,190 720,380 650,600" fill="none" stroke="{b}" stroke-width="44" stroke-linecap="round"/>' \
             '<path d="M250,600 C180,380 300,190 450,190 C600,190 720,380 650,600" fill="none" stroke="#000" stroke-opacity="0.12" stroke-width="44" stroke-linecap="round"/>' \
             '<rect x="196" y="380" width="40" height="70" rx="8" fill="#121214" fill-opacity="0.85" transform="rotate(-12 216 415)"/>'
    cuerpo = 'M210,640 Q200,560 300,545 L600,545 Q700,560 690,640 Q700,800 560,850 L340,850 Q200,800 210,640 Z'
    return (correa + pieza(cuerpo, b)
            + '<path d="M245,600 Q450,575 655,600" fill="none" stroke="#000" stroke-opacity="0.45" stroke-width="5"/>'
            + '<rect x="620" y="585" width="14" height="34" rx="4" fill="#121214" fill-opacity="0.8"/>'
            + costuras('M230,700 Q450,730 670,700 M340,842 L560,842', b) + fenix(450, 750, 110, l))

def rinonera_mini(b, l):
    cinta = 'M60,600 Q450,570 840,600 L840,644 Q450,614 60,644 Z'
    bolsa = 'M330,540 Q450,520 570,540 Q600,630 570,730 Q450,750 330,730 Q300,630 330,540 Z'
    return (pieza(cinta, b) + oscuro(cinta, 0.12)
            + '<rect x="110" y="592" width="40" height="56" rx="9" fill="#121214" fill-opacity="0.85"/>'
            + pieza(bolsa, b)
            + '<path d="M345,565 Q450,548 555,565" fill="none" stroke="#000" stroke-opacity="0.45" stroke-width="4"/>'
            + costuras('M338,720 Q450,738 562,720', b) + fenix(450, 645, 80, l))

# ───────────── CALCETINES ─────────────
def calcetin(x, y, pierna, b, l, logo=True):
    L = pierna
    d = (f'M{x},{y} L{x+150},{y} L{x+150},{y+L} Q{x+152},{y+L+40} {x+195},{y+L+52} L{x+300},{y+L+66} '
         f'Q{x+345},{y+L+80} {x+338},{y+L+128} Q{x+330},{y+L+172} {x+285},{y+L+172} L{x+70},{y+L+172} Q{x-4},{y+L+172} {x},{y+L+96} Z')
    puno = f'<path d="M{x},{y} L{x+150},{y} L{x+150},{y+38} L{x},{y+38} Z" fill="#000" fill-opacity="0.12"/>'
    canale = ''.join(f'<line x1="{x+i}" y1="{y+4}" x2="{x+i}" y2="{y+34}" stroke="#000" stroke-opacity="0.12" stroke-width="2"/>' for i in range(14, 150, 14))
    talon = f'<path d="M{x},{y+L+96} Q{x-4},{y+L+172} {x+70},{y+L+172} L{x+70},{y+L+120} Q{x+20},{y+L+110} {x+4},{y+L+60} Z" fill="#000" fill-opacity="0.10"/>'
    punta = f'<path d="M{x+285},{y+L+66} Q{x+345},{y+L+80} {x+338},{y+L+128} Q{x+330},{y+L+172} {x+285},{y+L+172} Z" fill="#000" fill-opacity="0.10"/>'
    f = fenix(x + 75, y + 38 + min(L - 38, 260) / 2 + 6, min(70, max(46, (L - 38) * 0.6)), l) if logo else ''
    return pieza(d, b) + puno + canale + talon + punta + f

def calcetines_tobilleros(b, l):
    return calcetin(230, 430, 110, b, l) + calcetin(330, 520, 110, b, l)

def calcetines_media_cana(b, l):
    return calcetin(210, 170, 470, b, l) + calcetin(330, 250, 470, b, l)

def calcetines_pack(b, l):
    return calcetin(150, 260, 330, b, l) + calcetin(280, 310, 330, b, l) + calcetin(410, 360, 330, b, l)

# ───────────── GORRAS ─────────────
def gorra(b, l, alta=True, perforada=False):
    """Vista de perfil 3/4: copa a la izquierda y visera hacia la derecha."""
    top = 390 if alta else 450
    copa = f'M170,720 Q150,{top+60} 400,{top} Q610,{top+10} 650,700 Q420,760 170,720 Z'
    visera = 'M470,705 Q690,640 860,700 Q885,745 835,778 Q690,822 530,785 Q470,750 470,705 Z'
    bajo_visera = 'M530,785 Q690,822 835,778 Q790,812 700,826 Q600,830 530,805 Z'
    paneles = costuras(f'M400,{top+2} Q300,{top+120} 290,728 M400,{top+2} Q520,{top+110} 540,722 M175,712 Q420,752 645,694', b)
    boton = f'<ellipse cx="400" cy="{top+2}" rx="22" ry="9" fill="{b}" stroke="#000" stroke-opacity="0.25" stroke-width="2"/>'
    cierre = '<path d="M172,650 Q190,640 205,655 L205,705 Q190,712 175,705 Z" fill="#000" fill-opacity="0.25"/>'
    agujeros = ''
    if perforada:
        agujeros = ''.join(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#000" fill-opacity="0.22"/>'
                           for cx in (235, 345) for cy in range(top + 140, 690, 26))
    return (pieza(copa, b) + oscuro('M400,' + str(top) + ' Q610,' + str(top+10) + ' 650,700 Q600,715 545,722 Q520,' + str(top+110) + ' 400,' + str(top) + ' Z', 0.06)
            + paneles + agujeros + boton + cierre
            + pieza(visera, b) + oscuro(bajo_visera, 0.30) + costuras('M490,712 Q690,656 845,712', b)
            + fenix(440, (top + 720) / 2 + 20, 120 if alta else 95, l))

def _zoom(g):
    return f'<g transform="translate(450 600) scale(1.18) translate(-500 -620)">{g}</g>'

def gorra_running(b, l):
    return _zoom(gorra(b, l, alta=False, perforada=True))

def gorra_baseball(b, l):
    return _zoom(gorra(b, l, alta=True))

def visera(b, l):
    """Visera: banda de cabeza (anillo) + ala delantera."""
    tras = f'<ellipse cx="400" cy="640" rx="250" ry="95" fill="none" stroke="{b}" stroke-width="40"/><ellipse cx="400" cy="640" rx="250" ry="95" fill="none" stroke="#000" stroke-opacity="0.22" stroke-width="40"/>'
    frente = 'M150,640 Q170,735 400,742 Q600,738 650,640 L650,700 Q600,798 400,802 Q170,795 150,700 Z'
    ala = 'M470,745 Q690,680 860,740 Q885,785 835,818 Q690,862 530,825 Q470,790 470,745 Z'
    return (tras + pieza(frente, b) + costuras('M155,652 Q175,747 400,754 Q600,750 645,652 M155,690 Q175,785 400,792 Q600,788 645,690', b)
            + pieza(ala, b) + oscuro('M530,825 Q690,862 835,818 Q790,852 700,866 Q600,870 530,845 Z', 0.30)
            + costuras('M490,752 Q690,696 845,752', b)
            + fenix(330, 722, 58, l))

# ───────────── AGARRADERAS ─────────────
def strap(x, y, largo, b, l, rot=0, acolchado=False, gancho=False):
    w = 70
    partes = []
    if not gancho:
        cuerpo = f'M{x},{y+120} L{x+w},{y+120} L{x+w},{y+largo} Q{x+w/2},{y+largo+24} {x},{y+largo} Z'
        partes.append(pieza(cuerpo, b))
        partes.append(costuras(f'M{x+8},{y+130} L{x+8},{y+largo-6} M{x+w-8},{y+130} L{x+w-8},{y+largo-6}', b))
    lazo = f'<path d="M{x+w/2},{y+150} C{x-60},{y+100} {x-30},{y-20} {x+w/2},{y} C{x+w+30},{y-20} {x+w+60},{y+100} {x+w/2},{y+150}" fill="none" stroke="{b}" stroke-width="56"/>' \
           f'<path d="M{x+w/2},{y+150} C{x-60},{y+100} {x-30},{y-20} {x+w/2},{y} C{x+w+30},{y-20} {x+w+60},{y+100} {x+w/2},{y+150}" fill="none" stroke="#000" stroke-opacity="0.12" stroke-width="56"/>'
    partes.insert(0, lazo)
    if acolchado or gancho:
        pad = f'M{x-26},{y+70} L{x+w+26},{y+70} Q{x+w+40},{y+160} {x+w+26},{y+250} L{x-26},{y+250} Q{x-40},{y+160} {x-26},{y+70} Z'
        partes.append(pieza(pad, b) + oscuro(pad, 0.10) + costuras(f'M{x-16},{y+82} L{x+w+16},{y+82} M{x-16},{y+238} L{x+w+16},{y+238}', b))
    if gancho:
        cx = x + w / 2
        partes.append(f'<rect x="{cx-30}" y="{y+250}" width="60" height="70" rx="6" fill="url(#metal)"/>'
                      f'<path d="M{cx},{y+318} L{cx},{y+520} Q{cx},{y+600} {cx+70},{y+600} Q{cx+130},{y+600} {cx+130},{y+530} L{cx+130},{y+500}" fill="none" stroke="url(#metal)" stroke-width="30" stroke-linecap="round"/>'
                      f'<path d="M{cx},{y+318} L{cx},{y+520} Q{cx},{y+600} {cx+70},{y+600} Q{cx+130},{y+600} {cx+130},{y+530} L{cx+130},{y+500}" fill="none" stroke="#000" stroke-opacity="0.15" stroke-width="4" stroke-linecap="round"/>')
        partes.append(fenix(cx, y + 160, 80, l))
    else:
        partes.append(fenix(x + w / 2, y + largo - 120 if not acolchado else y + 160, 56 if not acolchado else 80, l))
    return f'<g transform="rotate({rot} {x+w/2} {y+largo/2})">' + ''.join(partes) + '</g>'

def straps_algodon(b, l):
    return strap(320, 200, 820, b, l, rot=-5) + strap(500, 230, 820, b, l, rot=5)

def straps_acolchados(b, l):
    return strap(320, 200, 820, b, l, rot=-5, acolchado=True) + strap(500, 230, 820, b, l, rot=5, acolchado=True)

def ganchos(b, l):
    return strap(250, 260, 600, b, l, rot=-4, gancho=True) + strap(500, 300, 600, b, l, rot=4, gancho=True)

PRODUCTOS = {
    "camiseta-arete": camiseta_arete,
    "camiseta-fenix-oversize": camiseta_oversize,
    "camiseta-sin-mangas-training": camiseta_tirantes,
    "rinonera-running": rinonera_running,
    "rinonera-cruzada-urban": rinonera_cruzada,
    "mini-rinonera-gym": rinonera_mini,
    "calcetines-tobilleros-running": calcetines_tobilleros,
    "calcetines-media-cana-training": calcetines_media_cana,
    "calcetines-pack-crew": calcetines_pack,
    "gorra-running-ligera": gorra_running,
    "gorra-baseball-curva": gorra_baseball,
    "visera-training": lambda b, l: _zoom(visera(b, l)),
    "straps-algodon": straps_algodon,
    "straps-acolchados": straps_acolchados,
    "ganchos-levantamiento": ganchos,
}

if __name__ == "__main__":
    import pathlib
    out = pathlib.Path("svg"); out.mkdir(exist_ok=True)
    for slug, fn in PRODUCTOS.items():
        for color, (base, logo) in COLORES.items():
            (out / f"{slug}-{color}.svg").write_text(lienzo(fn(base, logo)))
    print(len(list(out.glob("*.svg"))), "svg")
