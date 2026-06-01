import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from groq import Groq
import os, random, json, io, base64
from datetime import datetime

st.set_page_config(page_title="Freshbloc IA", page_icon="FRBL", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

ANCHO, ALTO = 1080, 1350

MORADO = (145, 60, 255)
MORADO_ENTREVISTA = (125, 40, 230)
NEGRO = (8, 8, 10)
NEGRO_LOGO = (0, 0, 0)
BLANCO = (245, 245, 245)
GRIS = (190, 190, 190)

EXTENSIONES = (".jpg", ".jpeg", ".png", ".webp")
MAX_CITA = 65

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #08080A 0%, #13001F 100%);
    color: white;
}

.block-container {
    max-width: 760px;
    padding-top: 1.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

h1, h2, h3, p, label, span {
    color: white !important;
}

.logo-title {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
}

.logo-title img {
    width: 180px;
    max-width: 45vw;
}

.logo-title .brand {
    color: white;
    font-size: 48px;
    font-weight: 900;
    letter-spacing: -2px;
}

.logo-title .ia {
    color: #913CFF;
    font-size: 48px;
    font-weight: 900;
    letter-spacing: -2px;
}

.stTextArea textarea {
    background-color: #111 !important;
    color: white !important;
    border: 1px solid #913CFF !important;
    font-size: 20px !important;
    line-height: 1.45 !important;
    border-radius: 14px !important;
}

[data-testid="stFileUploader"] {
    background-color: #3a0f70;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #913CFF;
}

[data-testid="stFileUploader"] section {
    background-color: #26084f;
    border-radius: 14px;
}

.stButton>button {
    background-color: #913CFF;
    color: white;
    border-radius: 16px;
    border: none;
    padding: 0.95rem 1.4rem;
    font-weight: 900;
    width: 100%;
    font-size: 18px;
}

.stDownloadButton>button {
    background-color: #913CFF;
    color: white;
    border-radius: 18px;
    border: none;
    padding: 1.15rem 1.5rem;
    font-weight: 900;
    width: 100%;
    font-size: 21px;
}

.caption-box {
    background: #111;
    border: 1px solid #913CFF;
    padding: 16px;
    border-radius: 14px;
    color: white;
    font-size: 17px;
    line-height: 1.45;
}

@media (max-width: 600px) {
    .logo-title img {
        width: 120px;
    }

    .logo-title .brand,
    .logo-title .ia {
        font-size: 34px;
    }

    .stTextArea textarea {
        font-size: 18px !important;
    }
}
</style>
""", unsafe_allow_html=True)


def cargar_fuente(tamano):
    try:
        return ImageFont.truetype("arialbd.ttf", tamano)
    except:
        return ImageFont.load_default()


def abrir_imagen_segura(origen):
    img = Image.open(origen)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def dividir_texto(texto, fuente, max_ancho):
    texto = str(texto or "").strip()
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
            if linea:
                lineas.append(linea)
            linea = palabra

    if linea:
        lineas.append(linea)

    return lineas


def recortar_vertical(imagen, ancho_final, alto_final):
    imagen = ImageOps.exif_transpose(imagen.convert("RGB"))
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


def recortar_cuadrado(imagen, tamano):
    imagen = ImageOps.exif_transpose(imagen.convert("RGB"))
    w, h = imagen.size
    lado = min(w, h)
    x = (w - lado) // 2
    y = (h - lado) // 2
    return imagen.crop((x, y, x + lado, y + lado)).resize((tamano, tamano))


def poner_logo(img, tamano=320, pos=(55, 55)):
    logo_path = "logo/frbl.png"

    if not os.path.exists(logo_path):
        draw = ImageDraw.Draw(img)
        draw.text(pos, "FRBL", font=cargar_fuente(78), fill=MORADO)
        return img

    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((tamano, tamano))

    img_rgba = img.convert("RGBA")
    img_rgba.paste(logo, pos, logo)

    return img_rgba.convert("RGB")


def fondo_foto(imagen):
    img = recortar_vertical(imagen, ANCHO, ALTO)

    capa_oscura = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    img = Image.blend(img, capa_oscura, 0.16)

    overlay = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    for y in range(ALTO):
        if y > 430:
            alpha = int(245 * ((y - 430) / (ALTO - 430)))
            alpha = min(alpha, 245)
            draw_overlay.line((0, y, ANCHO, y), fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    glow = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((650, -250, 1350, 450), fill=(145, 60, 255, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(90))

    return Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")


def obtener_artistas():
    if not os.path.exists("fotos"):
        return []

    return [
        nombre for nombre in os.listdir("fotos")
        if os.path.isdir(os.path.join("fotos", nombre))
    ]


def elegir_foto(artista):
    carpeta = os.path.join("fotos", artista)

    if not os.path.exists(carpeta):
        raise Exception(f"No existe la carpeta fotos/{artista}")

    imagenes = [
        archivo for archivo in os.listdir(carpeta)
        if archivo.lower().endswith(EXTENSIONES)
    ]

    if not imagenes:
        raise Exception(f"No hay fotos en {carpeta}")

    return os.path.join(carpeta, random.choice(imagenes))


def analizar_noticia(texto, plantilla, cita_manual=""):
    artistas = obtener_artistas()

    base = f"""
Artistas disponibles:
{artistas}

Devuelve SOLO JSON válido.

Formato obligatorio:
{{
 "categoria":"",
 "artista":"",
 "titulo":"",
 "gancho":"",
 "subtitulo":"",
 "caption":"",
 "hashtags":[]
}}

Reglas generales:
- artista debe coincidir EXACTAMENTE con una carpeta disponible.
- titulo debe ser el nombre visible del artista.
- No inventes datos.
- No inventes fechas.
- No inventes colaboraciones.
- No inventes nombres de canciones.
- Usa solamente información presente en el texto.
- caption nunca puede venir vacío.
- hashtags nunca puede venir vacío.
- hashtags debe tener entre 3 y 6 hashtags.
- caption debe sonar humano, con contexto y tono de medio urbano chileno.
"""

    if plantilla == "Quote / Entrevista":
        prompt = f"""
Eres editor de entrevistas de Freshbloc.

La plantilla elegida es ENTREVISTA.
Hay un campo de cita exacta. Si existe, NO la cambies.

{base}

Cita exacta entregada:
{cita_manual}

Reglas de entrevista:
- categoria debe ser "ENTREVISTA".
- Si hay cita exacta, gancho debe ser EXACTAMENTE esa cita, sin inventar ni parafrasear.
- Si no hay cita exacta, gancho debe ser un resumen SIN comillas.
- NO inventes citas.
- NO parafrasees declaraciones delicadas.
- subtitulo debe explicar el contexto de la frase en máximo 15 palabras.
- caption debe aclarar el contexto de la entrevista o declaración.

Información:
{texto}
"""

    elif plantilla == "Lanzamiento / Portada":
        prompt = f"""
Eres editor musical de Freshbloc.

La plantilla elegida es LANZAMIENTO.
Debes convertir la información en un post de lanzamiento.

{base}

REGLAS OBLIGATORIAS DE LANZAMIENTO:
- categoria debe ser "LANZAMIENTO".
- NO inventes colaboraciones.
- NO inventes fechas.
- NO inventes nombres de canciones.
- NO escribas "junte" si el texto no menciona colaboración.
- NO escribas "colaboración" si el texto no menciona colaboración.
- NO escribas "preparativos" si el texto no lo menciona.
- Si el texto dice "disco", usa "disco".
- Si el texto dice "álbum", usa "álbum".
- Si el texto dice "tema", usa "tema".
- Si falta fecha, NO inventes fecha.

GANCHO:
- máximo 5 palabras.
- debe resumir exactamente el anuncio.
- ejemplos válidos:
  "ANUNCIA NUEVO DISCO"
  "NUEVO ÁLBUM CONFIRMADO"
  "ESTRENO EN CAMINO"
  "LANZA NUEVO TEMA"

SUBTITULO:
- máximo 12 palabras.
- debe explicar exactamente qué ocurrió.
- Si no hay fecha, usa "El artista adelantó su próximo proyecto".
- Si hay fecha, inclúyela.

CAPTION:
- entre 40 y 90 palabras.
- explicar el lanzamiento con contexto real.
- tono medio urbano chileno.
- sin exageraciones falsas.

Información:
{texto}
"""

    elif plantilla == "Radar / Emergente":
        prompt = f"""
Eres curador de Freshbloc Radar.

La plantilla elegida es RADAR.
Sirve para recomendar artistas, canciones o nombres emergentes.

{base}

Reglas de radar:
- categoria debe ser "RADAR".
- gancho debe sonar como descubrimiento.
- subtitulo debe explicar por qué mirarlo en máximo 15 palabras.
- Prefiere: "OJO CON ESTE NOMBRE", "PROMESA EN ASCENSO", "NUEVA CARA DEL BLOQUE".
- No inventes ciudad, edad ni números si no aparecen.

Información:
{texto}
"""

    else:
        prompt = f"""
Eres editor de Freshbloc, medio chileno de música urbana.

La plantilla elegida es NOTICIA.
Debe parecer post noticioso de Instagram.

{base}

Reglas de noticia:
- categoria puede ser NOTICIA, LANZAMIENTO, TENDENCIA, EVENTO o RADAR.
- gancho debe ser emocional, fuerte y noticioso.
- subtitulo debe explicar el hecho concreto en máximo 15 palabras.
- Si hay otro artista importante, úsalo en el subtitulo.
- Prefiere: "PRENDIÓ LAS REDES", "YA ES OFICIAL", "JUNTE PESADO", "DESTAPÓ EL PLAN".
- No uses "junte" si no hay colaboración.

Información:
{texto}
"""

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35,
        response_format={"type": "json_object"}
    )

    datos = json.loads(respuesta.choices[0].message.content)

    if plantilla == "Quote / Entrevista" and cita_manual.strip():
        datos["gancho"] = cita_manual.strip()

    if plantilla == "Lanzamiento / Portada":
        raw = texto.lower()

        if "colab" not in raw and "junte" not in raw and "junto" not in raw:
            prohibidas = ["junte", "colaboración", "colaboracion", "colabora", "junto"]
            for palabra in prohibidas:
                if palabra in datos.get("subtitulo", "").lower():
                    datos["subtitulo"] = "El artista adelantó su próximo proyecto"

        if "disco" in raw and "disco" not in datos.get("gancho", "").lower():
            datos["gancho"] = "ANUNCIA NUEVO DISCO"

        if "álbum" in raw or "album" in raw:
            if "álbum" not in datos.get("gancho", "").lower() and "album" not in datos.get("gancho", "").lower():
                datos["gancho"] = "NUEVO ÁLBUM CONFIRMADO"

        if "tema" in raw and "tema" not in datos.get("gancho", "").lower():
            datos["gancho"] = "LANZA NUEVO TEMA"

    if not datos.get("caption"):
        datos["caption"] = f"{datos.get('titulo', 'El artista')} vuelve a mover la conversación dentro de la escena urbana."

    if not datos.get("hashtags"):
        datos["hashtags"] = ["#Freshbloc", "#UrbanoChileno", "#GeneroUrbano"]

    return datos


def plantilla_noticia(datos, imagen):
    img = fondo_foto(imagen)
    img = poner_logo(img)

    draw = ImageDraw.Draw(img)

    fuente_cat = cargar_fuente(34)
    fuente_artista = cargar_fuente(78)
    fuente_gancho = cargar_fuente(92)
    fuente_sub = cargar_fuente(40)

    cat = datos["categoria"].upper()
    cat_w = draw.textbbox((0, 0), cat, font=fuente_cat)[2]
    draw.text((ANCHO - cat_w - 55, 70), cat, font=fuente_cat, fill=MORADO)

    draw.text((55, 805), datos["titulo"].upper(), font=fuente_artista, fill=BLANCO)

    y = 900
    for linea in dividir_texto(datos["gancho"].upper(), fuente_gancho, 950)[:2]:
        draw.text((55, y), linea, font=fuente_gancho, fill=MORADO)
        y += 100

    y += 25
    for linea in dividir_texto(datos["subtitulo"], fuente_sub, 900)[:3]:
        draw.text((55, y), linea, font=fuente_sub, fill=BLANCO)
        y += 48

    draw.rectangle((55, 1285, 1025, 1292), fill=MORADO)
    return img


def plantilla_lanzamiento(datos, imagen):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)

    fondo = recortar_vertical(imagen, ANCHO, ALTO)
    fondo = fondo.filter(ImageFilter.GaussianBlur(48))
    fondo = Image.blend(fondo, Image.new("RGB", (ANCHO, ALTO), NEGRO), 0.62)
    img.paste(fondo, (0, 0))

    draw = ImageDraw.Draw(img)

    portada = recortar_cuadrado(imagen, 660)
    img.paste(portada, (210, 135))

    draw.rectangle((190, 115, 890, 815), outline=MORADO, width=10)

    img = poner_logo(img, tamano=260, pos=(55, 55))
    draw = ImageDraw.Draw(img)

    fuente_tag = cargar_fuente(42)
    fuente_artista = cargar_fuente(66)
    fuente_gancho = cargar_fuente(82)
    fuente_sub = cargar_fuente(42)

    y = 850

    draw.text(
        (55, y),
        "LANZAMIENTO",
        font=fuente_tag,
        fill=MORADO,
        stroke_width=1,
        stroke_fill=NEGRO
    )

    y += 62

    draw.text(
        (55, y),
        datos["titulo"].upper(),
        font=fuente_artista,
        fill=BLANCO,
        stroke_width=2,
        stroke_fill=NEGRO
    )

    y += 82

    for linea in dividir_texto(datos["gancho"].upper(), fuente_gancho, 950)[:2]:
        draw.text(
            (55, y),
            linea,
            font=fuente_gancho,
            fill=BLANCO,
            stroke_width=2,
            stroke_fill=NEGRO
        )
        y += 86

    y += 12

    for linea in dividir_texto(datos["subtitulo"], fuente_sub, 900)[:2]:
        draw.text(
            (55, y),
            linea,
            font=fuente_sub,
            fill=GRIS,
            stroke_width=1,
            stroke_fill=NEGRO
        )
        y += 48

    draw.rectangle((55, 1285, 1025, 1292), fill=MORADO)

    return img


def plantilla_quote(datos, imagen):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, 470, ALTO), fill=MORADO_ENTREVISTA)

    foto = recortar_vertical(imagen, 620, ALTO)
    foto = Image.blend(foto, Image.new("RGB", (620, ALTO), NEGRO), 0.25)
    img.paste(foto, (460, 0))

    sombra = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sombra)

    for x in range(430, 720):
        alpha = int(210 * (1 - (x - 430) / 290))
        sd.line((x, 0, x, ALTO), fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img.convert("RGBA"), sombra).convert("RGB")
    draw = ImageDraw.Draw(img)

    draw.text((55, 65), "FRBL", font=cargar_fuente(78), fill=NEGRO_LOGO)

    fuente_tag = cargar_fuente(34)
    fuente_quote = cargar_fuente(48)
    fuente_autor = cargar_fuente(42)
    fuente_sub = cargar_fuente(34)

    draw.text((55, 220), "ENTREVISTA", font=fuente_tag, fill=BLANCO)
    draw.text((55, 340), "“", font=cargar_fuente(150), fill=BLANCO)

    y = 500
    for linea in dividir_texto(datos["gancho"].upper(), fuente_quote, 390)[:5]:
        draw.text((55, y), linea, font=fuente_quote, fill=BLANCO)
        y += 58

    draw.text((55, 950), f"— {datos['titulo'].upper()}", font=fuente_autor, fill=NEGRO)

    y = 1020
    for linea in dividir_texto(datos["subtitulo"], fuente_sub, 380)[:3]:
        draw.text((55, y), linea, font=fuente_sub, fill=NEGRO)
        y += 42

    draw.rectangle((55, 1285, 420, 1292), fill=NEGRO)
    return img


def plantilla_radar(datos, imagen):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, ANCHO, 420), fill=MORADO)
    draw.rectangle((0, 420, ANCHO, ALTO), fill=NEGRO)

    foto = recortar_cuadrado(imagen, 650)
    img.paste(foto, (215, 250))

    draw.rectangle((200, 235, 880, 915), outline=BLANCO, width=8)

    img = poner_logo(img, tamano=260, pos=(55, 55))
    draw = ImageDraw.Draw(img)

    fuente_titulo = cargar_fuente(86)
    fuente_gancho = cargar_fuente(62)
    fuente_sub = cargar_fuente(38)

    draw.text((55, 150), "RADAR", font=cargar_fuente(90), fill=BLANCO)
    draw.text((55, 925), datos["titulo"].upper(), font=fuente_titulo, fill=BLANCO)

    y = 1030
    for linea in dividir_texto(datos["gancho"].upper(), fuente_gancho, 950)[:2]:
        draw.text((55, y), linea, font=fuente_gancho, fill=MORADO)
        y += 70

    for linea in dividir_texto(datos["subtitulo"], fuente_sub, 900)[:3]:
        draw.text((55, y + 10), linea, font=fuente_sub, fill=BLANCO)
        y += 45

    draw.rectangle((55, 1285, 1025, 1292), fill=MORADO)
    return img


def generar_post(plantilla, datos, imagen):
    if plantilla == "Noticia / Foto artista":
        return plantilla_noticia(datos, imagen)

    if plantilla == "Lanzamiento / Portada":
        return plantilla_lanzamiento(datos, imagen)

    if plantilla == "Quote / Entrevista":
        return plantilla_quote(datos, imagen)

    if plantilla == "Radar / Emergente":
        return plantilla_radar(datos, imagen)

    return plantilla_noticia(datos, imagen)


if "post_buffer" not in st.session_state:
    st.session_state.post_buffer = None

if "datos" not in st.session_state:
    st.session_state.datos = None

if os.path.exists("logo/frbl.png"):
    logo_b64 = base64.b64encode(open("logo/frbl.png", "rb").read()).decode()
    st.markdown(
        f"""
        <div class="logo-title">
            <img src="data:image/png;base64,{logo_b64}">
            <span class="brand">freshbloc</span>
            <span class="ia">IA</span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown("<h1>freshbloc IA</h1>", unsafe_allow_html=True)

st.write("Generador de publicaciones urbanas para Instagram.")

plantilla = st.selectbox(
    "Escoge plantilla",
    [
        "Noticia / Foto artista",
        "Lanzamiento / Portada",
        "Quote / Entrevista",
        "Radar / Emergente"
    ]
)

noticia = st.text_area(
    "Pega la noticia",
    placeholder="Ej: Gino Mella anuncia nuevo disco para este año...",
    height=150
)

cita_manual = ""

if plantilla == "Quote / Entrevista":
    cita_manual = st.text_area(
        f"Cita exacta del artista — máximo {MAX_CITA} caracteres",
        placeholder="Ej: Estoy buscando artistas jóvenes para mi firma",
        height=110,
        max_chars=MAX_CITA
    )

modo_imagen = st.radio(
    "Imagen para el post",
    ["Subir imagen manual", "Usar foto aleatoria del artista"]
)

imagen_subida = None

if modo_imagen == "Subir imagen manual":
    imagen_subida = st.file_uploader(
        "Sube portada, foto, flyer o screenshot",
        type=["jpg", "jpeg", "png", "webp"]
    )

generar = st.button("GENERAR POST")

if generar:
    if not noticia.strip():
        st.error("Pega una noticia primero.")
    elif plantilla == "Quote / Entrevista" and not cita_manual.strip():
        st.error("Para entrevista, pega una cita exacta del artista.")
    else:
        with st.spinner("Generando con Freshbloc IA..."):
            datos = analizar_noticia(noticia, plantilla, cita_manual)

            if modo_imagen == "Subir imagen manual":
                if imagen_subida is None:
                    st.error("Sube una imagen manual primero.")
                    st.stop()
                imagen = abrir_imagen_segura(imagen_subida)
            else:
                ruta = elegir_foto(datos["artista"])
                imagen = abrir_imagen_segura(ruta)

            post = generar_post(plantilla, datos, imagen)

            buffer = io.BytesIO()
            post.save(buffer, format="PNG")
            buffer.seek(0)

            st.session_state.post_buffer = buffer.getvalue()
            st.session_state.datos = datos

if st.session_state.post_buffer:
    st.image(
        st.session_state.post_buffer,
        caption="Post generado",
        use_container_width=True
    )

    st.download_button(
        "DESCARGAR POST",
        data=st.session_state.post_buffer,
        file_name=f"freshbloc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        mime="image/png"
    )

if st.session_state.datos:
    datos = st.session_state.datos

    st.markdown("### Caption")
    st.markdown(
        f"<div class='caption-box'>{datos.get('caption','')}</div>",
        unsafe_allow_html=True
    )

    st.markdown("### Hashtags")
    st.markdown(
        f"<div class='caption-box'>{' '.join(datos.get('hashtags', []))}</div>",
        unsafe_allow_html=True
    )
