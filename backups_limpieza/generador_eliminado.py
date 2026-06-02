from PIL import Image, ImageDraw, ImageFont, ImageFilter
from groq import Groq
import os
import random
import json
from datetime import datetime

# ==========================
# CONFIG
# ==========================

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

ANCHO, ALTO = 1080, 1350

MORADO = (145, 60, 255)
NEGRO = (8, 8, 10)
BLANCO = (245, 245, 245)

EXTENSIONES = (".jpg", ".jpeg", ".png", ".webp")


def cargar_fuente(tamano):
    try:
        return ImageFont.truetype("arialbd.ttf", tamano)
    except:
        return ImageFont.load_default()


def dividir_texto(texto, fuente, max_ancho):
    palabras = texto.split()
    lineas = []
    linea = ""
    draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    for palabra in palabras:
        prueba = linea + " " + palabra if linea else palabra
        ancho = draw_temp.textbbox((0, 0), prueba, font=fuente)[2]

        if ancho <= max_ancho:
            linea = prueba
        else:
            lineas.append(linea)
            linea = palabra

    if linea:
        lineas.append(linea)

    return lineas


def analizar_noticia(texto):
    artistas = [
        nombre for nombre in os.listdir("fotos")
        if os.path.isdir(os.path.join("fotos", nombre))
    ]

    prompt = f"""
Eres editor creativo de Freshbloc, un medio chileno de música urbana.

Tu trabajo es convertir información cruda en titulares con energía para Instagram.

Devuelve SOLO JSON válido.

Artistas disponibles:
{artistas}

Categorías permitidas:
NOTICIA, LANZAMIENTO, TENDENCIA, EVENTO, RADAR, ENTREVISTA

Reglas:
- artista debe ser EXACTAMENTE una carpeta disponible.
- titulo debe ser solo el artista principal.
- gancho debe parecer titular de medio urbano.
- subtitulo debe complementar el titular.
- subtitulo máximo 10 palabras.
- Nunca repitas palabras del gancho.
- Nunca uses frases robóticas.
- No inventes datos.
- caption debe sonar humano, cercano y breve.
- hashtags debe ser una lista.
- subtitulo debe explicar por qué importa la noticia, no solo mencionar nombres.

PROHIBIDO:
"NUEVO TEMA"
"NUEVO MATERIAL"
"COLABORACIONES"
"PRÓXIMO LANZAMIENTO"
"SE VIENE ÁLBUM"
"LANZA CANCIÓN"

Prefiere frases como:
"PRENDIÓ LAS REDES"
"JUNTE PESADO"
"SE MUEVE LA ESCENA"
"CONFIRMÓ LA FECHA"
"YA ES OFICIAL"
"ALGO GRANDE VIENE"
"SORPRENDIÓ A SUS FANÁTICOS"
"MOVIÓ AL GÉNERO"
"DESTAPÓ EL PLAN"
"ROMPIÓ EL SILENCIO"

Formato:
{{
 "categoria": "",
 "artista": "",
 "titulo": "",
 "gancho": "",
 "dato": "",
 "caption": "",
 "hashtags": []
}}

Ejemplos:

Información:
Floyy Menor anuncia álbum colaborativo para junio.

Respuesta:
{{
 "categoria": "LANZAMIENTO",
 "artista": "floyymenor",
 "titulo": "FLOYYMENOR",
 "gancho": "JUNTE HISTÓRICO",
 "subtitulo": "Reunirá a figuras de la escena chilena",
 "caption": "FloyyMenor prepara un proyecto colaborativo que reuniría a varias figuras del género urbano chileno.",
 "hashtags": ["#FloyyMenor", "#GeneroUrbano", "#UrbanoChileno", "#Freshbloc"]
}}

Información:
Cris MJ y Juliano Sosa lanzan canción el 17 de junio.

Respuesta:
{{
 "categoria": "LANZAMIENTO",
 "artista": "cris_mj",
 "titulo": "CRIS MJ",
 "gancho": "SE VIENE EL JUNTE",
 "subtitulo": "Confirmaron estreno para este 17 de junio",
 "caption": "Cris MJ y Juliano Sosa encendieron a sus seguidores tras confirmar nuevo estreno para este 17 de junio.",
 "hashtags": ["#CrisMJ", "#JulianoSosa", "#UrbanoChileno", "#Freshbloc"]
}}

Información:
AK420 anuncia proyecto.

Respuesta:
{{
 "categoria": "LANZAMIENTO",
 "artista": "ak420",
 "titulo": "AK420",
 "gancho": "ALGO GRANDE VIENE",
 "subtitulo": "El artista comenzó a dejar pistas",
 "caption": "AK420 volvió a mover a sus seguidores con señales de nueva música.",
 "hashtags": ["#AK420", "#UrbanoChileno", "#Freshbloc"]
}}

Información:
{texto}
"""

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,
        response_format={"type": "json_object"}
    )

    return json.loads(respuesta.choices[0].message.content)


def elegir_foto(artista):
    carpeta = os.path.join("fotos", artista)

    imagenes = [
        archivo for archivo in os.listdir(carpeta)
        if archivo.lower().endswith(EXTENSIONES)
    ]

    if not imagenes:
        raise Exception(f"No hay fotos en {carpeta}")

    elegida = random.choice(imagenes)

    print(f"📸 {len(imagenes)} fotos encontradas")
    print(f"🎲 Foto seleccionada: {elegida}")

    return os.path.join(carpeta, elegida)


def recortar_vertical(imagen, ancho_final, alto_final):
    w, h = imagen.size
    ratio_objetivo = ancho_final / alto_final
    ratio_actual = w / h

    if ratio_actual > ratio_objetivo:
        nuevo_ancho = int(h * ratio_objetivo)
        izquierda = (w - nuevo_ancho) // 2
        imagen = imagen.crop((izquierda, 0, izquierda + nuevo_ancho, h))
    else:
        nuevo_alto = int(w / ratio_objetivo)
        arriba = (h - nuevo_alto) // 2
        imagen = imagen.crop((0, arriba, w, arriba + nuevo_alto))

    return imagen.resize((ancho_final, alto_final))


def poner_logo(img):
    logo_path = "logo/frbl.png"

    if not os.path.exists(logo_path):
        print("⚠️ No encontré logo/frbl.png")
        return img

    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((320, 320))

    img_rgba = img.convert("RGBA")
    img_rgba.paste(logo, (55, 55), logo)

    return img_rgba.convert("RGB")


def crear_post(categoria, artista, titulo, gancho, subtitulo, imagen_path):
    foto = Image.open(imagen_path).convert("RGB")
    img = recortar_vertical(foto, ANCHO, ALTO)

    capa_oscura = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    img = Image.blend(img, capa_oscura, 0.14)

    overlay = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    for y in range(ALTO):
        if y > 450:
            alpha = int(245 * ((y - 450) / (ALTO - 450)))
            alpha = min(alpha, 245)
            draw_overlay.line((0, y, ANCHO, y), fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    glow = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((650, -250, 1350, 450), fill=(145, 60, 255, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    img = poner_logo(img)
    draw = ImageDraw.Draw(img)

    fuente_cat = cargar_fuente(34)
    cat_text = categoria.upper()
    bbox = draw.textbbox((0, 0), cat_text, font=fuente_cat)
    cat_w = bbox[2] - bbox[0]

    draw.text(
        (ANCHO - cat_w - 55, 70),
        cat_text,
        font=fuente_cat,
        fill=MORADO
    )

    fuente_artista = cargar_fuente(78)
    fuente_gancho = cargar_fuente(92)
    fuente_subtitulo = cargar_fuente(40)

    draw.text(
        (55, 805),
        titulo.upper(),
        font=fuente_artista,
        fill=BLANCO
    )

    gancho_lineas = dividir_texto(
        gancho.upper(),
        fuente_gancho,
        950
    )

    y = 900

    for linea in gancho_lineas[:2]:
        draw.text(
            (55, y),
            linea,
            font=fuente_gancho,
            fill=MORADO
        )
        y += 100

    sub_lineas = dividir_texto(
        subtitulo,
        fuente_subtitulo,
        900
    )

    y += 25

    for linea in sub_lineas[:2]:
        draw.text(
            (55, y),
            linea,
            font=fuente_subtitulo,
            fill=BLANCO
        )
        y += 48

    draw.rectangle((55, 1285, 1025, 1292), fill=MORADO)

    os.makedirs("posts", exist_ok=True)

    nombre = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    salida = os.path.join("posts", nombre)

    img.save(salida)

    print("\n✅ Post creado:")
    print(salida)


print("\n🟣 FRESHBLOC IA\n")

texto = input("Pega la noticia:\n\n")

datos = analizar_noticia(texto)

print("\n🧠 Resultado IA:")
print(json.dumps(datos, indent=2, ensure_ascii=False))

imagen = elegir_foto(datos["artista"])

crear_post(
    datos["categoria"],
    datos["artista"],
    datos["titulo"],
    datos["gancho"],
    datos["subtitulo"],
    imagen
)

print("\n📲 CAPTION:\n")
print(datos["caption"])

print("\n#️⃣ HASHTAGS:\n")
print(" ".join(datos["hashtags"]))