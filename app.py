import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from groq import Groq
import os, random, json, io, base64
from datetime import datetime

st.set_page_config(page_title="Freshbloc IA", page_icon="FRBL", layout="centered")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

ANCHO, ALTO = 1080, 1350
MORADO = (145, 60, 255)
MORADO_ENTREVISTA = (125, 40, 230)
NEGRO = (8, 8, 10)
BLANCO = (245, 245, 245)
GRIS = (190, 190, 190)
MAX_CITA = 65
EXTENSIONES = (".jpg", ".jpeg", ".png", ".webp")

st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#08080A,#13001F); color:white;}
.block-container {max-width:760px; padding:1rem;}
h1,h2,h3,p,label,span {color:white!important;}
.logo-title {display:flex; align-items:center; gap:16px; margin-bottom:10px;}
.logo-title img {width:170px; max-width:45vw;}
.logo-title .brand,.logo-title .ia {font-size:44px; font-weight:900;}
.logo-title .ia {color:#913CFF!important;}
.stTextArea textarea {
 background:#111!important; color:white!important; border:1px solid #913CFF!important;
 font-size:20px!important; border-radius:14px!important;
}
[data-testid="stFileUploader"] {
 background:#3a0f70; padding:18px; border-radius:18px; border:1px solid #913CFF;
}
.stButton>button,.stDownloadButton>button {
 background:#913CFF; color:white; border-radius:18px; border:none;
 padding:1rem 1.5rem; font-weight:900; width:100%; font-size:19px;
}
.caption-box {
 background:#111; border:1px solid #913CFF; padding:16px; border-radius:14px;
 font-size:17px; line-height:1.45;
}
@media(max-width:600px){
 .logo-title img{width:115px;}
 .logo-title .brand,.logo-title .ia{font-size:32px;}
}
</style>
""", unsafe_allow_html=True)

def cargar_fuente(tamano, tipo="bold"):
    if tipo == "display":
        fuentes = [
            "assets/Anton-Regular.ttf",
            "assets/Montserrat-Bold.ttf",
            "arialbd.ttf",
        ]
    else:
        fuentes = [
            "assets/Montserrat-Bold.ttf",
            "assets/Anton-Regular.ttf",
            "arialbd.ttf",
        ]

    for fuente in fuentes:
        try:
            return ImageFont.truetype(fuente, tamano)
        except:
            pass

    return ImageFont.load_default()


def abrir_imagen_segura(origen, rotacion=0):
    img = Image.open(origen)
    img = ImageOps.exif_transpose(img).convert("RGB")
    if rotacion == 90:
        img = img.rotate(-90, expand=True)
    elif rotacion == 180:
        img = img.rotate(180, expand=True)
    elif rotacion == 270:
        img = img.rotate(90, expand=True)
    return img

def dividir_texto(texto, fuente, max_ancho):
    texto = str(texto or "").strip()
    palabras = texto.split()
    lineas, linea = [], ""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for p in palabras:
        prueba = linea + " " + p if linea else p
        ancho = d.textbbox((0,0), prueba, font=fuente)[2]
        if ancho <= max_ancho:
            linea = prueba
        else:
            if linea:
                lineas.append(linea)
            linea = p
    if linea:
        lineas.append(linea)
    return lineas

def recortar_vertical(imagen, ancho_final, alto_final):
    imagen = imagen.convert("RGB")
    w, h = imagen.size
    r_obj = ancho_final / alto_final
    r = w / h
    if r > r_obj:
        nw = int(h * r_obj)
        x = (w - nw) // 2
        imagen = imagen.crop((x, 0, x + nw, h))
    else:
        nh = int(w / r_obj)
        y = (h - nh) // 2
        imagen = imagen.crop((0, y, w, y + nh))
    return imagen.resize((ancho_final, alto_final))

def recortar_cuadrado(imagen, tamano):
    imagen = imagen.convert("RGB")
    w, h = imagen.size
    lado = min(w, h)
    x = (w - lado) // 2
    y = (h - lado) // 2
    return imagen.crop((x, y, x + lado, y + lado)).resize((tamano, tamano))

def poner_logo(img, tamano=280, pos=(55,55)):
    logo_path = "logo/frbl.png"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((tamano, tamano))
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo, pos, logo)
        return img_rgba.convert("RGB")
    d = ImageDraw.Draw(img)
    d.text(pos, "FRBL", font=cargar_fuente(76), fill=MORADO)
    return img

def obtener_artistas():
    if not os.path.exists("fotos"):
        return []
    return [n for n in os.listdir("fotos") if os.path.isdir(os.path.join("fotos", n))]

def elegir_foto(artista):
    carpeta = os.path.join("fotos", artista)
    imgs = [a for a in os.listdir(carpeta) if a.lower().endswith(EXTENSIONES)]
    return os.path.join(carpeta, random.choice(imgs))

def fondo_foto(imagen):
    img = recortar_vertical(imagen, ANCHO, ALTO)
    img = Image.blend(img, Image.new("RGB", (ANCHO, ALTO), NEGRO), 0.18)

    overlay = Image.new("RGBA", (ANCHO, ALTO), (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    for y in range(ALTO):
        if y > 430:
            a = min(int(245 * ((y - 430) / (ALTO - 430))), 245)
            d.line((0,y,ANCHO,y), fill=(0,0,0,a))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def analizar_noticia(texto, plantilla, cita_manual=""):
    artistas = obtener_artistas()

    base = f"""
Artistas disponibles:
{artistas}

Devuelve SOLO JSON válido con:
{{
   "categoria":"",
    "titulo":"",
    "gancho":"",
    "subtitulo":"",
    "caption":"",
    "hashtags":[],
    "fecha":"",
    "tema":"",
    "album":"",
    "ep":"",
    "colaboracion":"",
    "productor":""
    "fecha":"",
    "tema":"",
    "album":"",
    "ep":"",
    "colaboracion":"",
    "productor":""
}}

Reglas:
- artista debe ser EXACTAMENTE una carpeta disponible.
- titulo debe ser el nombre visible del artista.
- No inventes datos, fechas, colaboraciones ni canciones.
- Usa solamente la información del texto.
- caption entre 35 y 80 palabras.
- hashtags entre 3 y 6.
"""

    if plantilla == "Lanzamiento / Portada":
        prompt = f"""
Eres editor musical de Freshbloc.

{base}

Plantilla: LANZAMIENTO.

REGLAS OBLIGATORIAS:

- categoria = LANZAMIENTO.
- NO inventes colaboraciones.
- NO inventes canciones.
- NO inventes fechas.
- NO inventes discos.
- Si el texto menciona una fecha, úsala.
- Si menciona un EP, usa EP.
- Si menciona un álbum, usa ÁLBUM.
- Si menciona un sencillo, usa TEMA.
- No uses frases genéricas.

PROHIBIDO escribir:
- "El artista presenta su nuevo proyecto"
- "El artista adelanta su próximo proyecto"
- "Nueva etapa para el artista"
- "El artista sorprende"
- "Se viene música nueva"

GANCHO:
- máximo 4 palabras.
- debe ser impactante.
- todo en mayúsculas.

SUBTITULO:
- máximo 14 palabras.
- debe contener el dato concreto más importante.
- no repetir el gancho.

BUENOS EJEMPLOS:

Texto:
"AK420 estrena tema el 20 de junio"

Gancho:
"FECHA CONFIRMADA"

Subtitulo:
"El lanzamiento quedó fijado para el 20 de junio"

Texto:
"Jere Klein anuncia nuevo EP"

Gancho:
"NUEVO EP"

Subtitulo:
"El proyecto fue anunciado oficialmente esta semana"

Texto:
"King Savagge estrena colaboración con XXX"

Gancho:
"SE ACTIVA EL JUNTE"

Subtitulo:
"La colaboración fue confirmada por ambos artistas"

ESTILO FRESHBLOC:

Escribe como una página urbana de Instagram.

Busca titulares que generen curiosidad.

Prefiere:
- PRENDE LAS REDES
- FECHA CONFIRMADA
- NUEVO EP
- VUELVE CON MÚSICA
- ROMPE EL SILENCIO
- YA ES OFICIAL
- SE ACTIVA EL ESTRENO
- SORPRENDE A SUS FANS
- PREPARA EL GOLPE
- CALIENTA MOTORES

Evita:
- LANZA NUEVO TEMA
- NUEVA CANCIÓN
- PRESENTA SU PROYECTO
- NUEVO PROYECTO
- MÚSICA NUEVA

EXTRACCIÓN DE DATOS:

Identifica si existen:

- fecha de lanzamiento
- nombre del tema
- nombre del álbum
- nombre del EP
- colaboración
- productor

Si un dato no existe, devuelve "".

Ejemplo:

Texto:
"AK420 estrena No Me Llamen junto a Julianno Sosa el 20 de junio"

Respuesta:

{
 "fecha":"20 de junio",
 "tema":"No Me Llamen",
 "colaboracion":"Julianno Sosa"
}

Información:
{text}
"""
    elif plantilla == "Quote / Entrevista":
        prompt = f"""
Eres editor de entrevistas de Freshbloc.

{base}

Plantilla: ENTREVISTA.
Cita exacta:
{cita_manual}

Reglas:
- categoria = ENTREVISTA.
- Si hay cita exacta, gancho debe ser EXACTAMENTE esa cita.
- No inventes citas.
- subtitulo debe dar contexto en máximo 15 palabras.

Información:
{texto}
"""
    elif plantilla == "Radar / Emergente":
        prompt = f"""
Eres curador de Freshbloc Radar.

{base}

Plantilla: RADAR.
- categoria = RADAR.
- gancho debe sonar como descubrimiento.
- subtitulo debe decir por qué mirar al artista.

Información:
{texto}
"""
    else:
        prompt = f"""
Eres editor de Freshbloc, medio urbano chileno.

{base}

Plantilla: NOTICIA.
- gancho noticioso y fuerte.
- subtitulo con el hecho concreto.
- No uses junte si no hay colaboración.

Información:
{texto}
"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    datos = json.loads(r.choices[0].message.content)

    if plantilla == "Quote / Entrevista" and cita_manual.strip():
        datos["gancho"] = cita_manual.strip()

    if plantilla == "Lanzamiento / Portada":
    raw = texto.lower()

    datos.setdefault("fecha", "")
    datos.setdefault("tema", "")
    datos.setdefault("album", "")
    datos.setdefault("ep", "")
    datos.setdefault("colaboracion", "")
    datos.setdefault("productor", "")

    if datos["fecha"] and datos["tema"]:
        datos["gancho"] = "FECHA CONFIRMADA"
        datos["subtitulo"] = f"{datos['tema']} llega el {datos['fecha']}"

    elif datos["fecha"] and datos["colaboracion"]:
        datos["gancho"] = "SE ACTIVA EL JUNTE"
        datos["subtitulo"] = f"Junto a {datos['colaboracion']} este {datos['fecha']}"

    elif datos["fecha"]:
        datos["gancho"] = "FECHA CONFIRMADA"
        datos["subtitulo"] = f"El estreno quedó fijado para el {datos['fecha']}"

    elif datos["colaboracion"]:
        datos["gancho"] = "SE ACTIVA EL JUNTE"
        datos["subtitulo"] = f"Junto a {datos['colaboracion']}"

    elif datos["album"]:
        datos["gancho"] = "NUEVO ÁLBUM"
        datos["subtitulo"] = f"{datos['album']} marca una nueva etapa"

    elif datos["ep"]:
        datos["gancho"] = "NUEVO EP"
        datos["subtitulo"] = f"{datos['ep']} ya empieza a moverse"

    elif "disco" in raw:
        datos["gancho"] = "ANUNCIA NUEVO DISCO"
        datos["subtitulo"] = "El anuncio encendió la expectativa en redes"

    elif "album" in raw or "álbum" in raw:
        datos["gancho"] = "NUEVO ÁLBUM"
        datos["subtitulo"] = "El proyecto ya empieza a generar movimiento"

    elif "tema" in raw:
        datos["gancho"] = "VUELVE CON MÚSICA"
        datos["subtitulo"] = "El estreno comienza a moverse entre sus seguidores"

    if not any(x in raw for x in ["colab", "junte", "junto", "ft", "feat"]):
        if any(p in datos.get("subtitulo", "").lower() for p in ["junte", "colaboración", "colaboracion", "junto"]):
            datos["subtitulo"] = "El estreno comienza a moverse entre sus seguidores"

    if not datos.get("caption"):
        datos["caption"] = f"{datos.get('titulo','El artista')} volvió a mover la conversación dentro de la escena urbana."
    if not datos.get("hashtags"):
        datos["hashtags"] = ["#Freshbloc", "#UrbanoChileno", "#GeneroUrbano"]

    return datos

def plantilla_noticia(datos, imagen):
    img = fondo_foto(imagen)
    img = poner_logo(img)
    d = ImageDraw.Draw(img)

    f_cat = cargar_fuente(36)
    f_art = cargar_fuente(82)
    f_gan = cargar_fuente(92)
    f_sub = cargar_fuente(42)

    cat = datos["categoria"].upper()
    w = d.textbbox((0,0), cat, font=f_cat)[2]
    d.text((ANCHO-w-55,70), cat, font=f_cat, fill=MORADO)

    d.text((55,805), datos["titulo"].upper(), font=f_art, fill=BLANCO)

    y = 905
    for linea in dividir_texto(datos["gancho"].upper(), f_gan, 950)[:2]:
        d.text((55,y), linea, font=f_gan, fill=MORADO)
        y += 98

    y += 20
    for linea in dividir_texto(datos["subtitulo"], f_sub, 900)[:2]:
        d.text((55,y), linea, font=f_sub, fill=BLANCO)
        y += 48

    d.rectangle((55,1285,1025,1292), fill=MORADO)
    return img

def plantilla_lanzamiento(datos, imagen):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)

    fondo = recortar_vertical(imagen, ANCHO, ALTO).filter(ImageFilter.GaussianBlur(45))
    fondo = Image.blend(fondo, Image.new("RGB", (ANCHO, ALTO), NEGRO), 0.62)
    img.paste(fondo, (0,0))

    d = ImageDraw.Draw(img)

    portada = recortar_cuadrado(imagen, 620)
    img.paste(portada, (230, 105))
    d.rectangle((210, 85, 870, 745), outline=MORADO, width=10)

    img = poner_logo(img, tamano=260, pos=(55,55))
    d = ImageDraw.Draw(img)

    f_tag = cargar_fuente(48, "display")
    f_art = cargar_fuente(95, "display")
    f_gan = cargar_fuente(125, "display")
    f_sub = cargar_fuente(46, "bold")

    y = 770

    d.text((55, y), "LANZAMIENTO", font=f_tag, fill=MORADO, stroke_width=1, stroke_fill=NEGRO)
    y += 78

    d.text((55, y), datos["titulo"].upper(), font=f_art, fill=BLANCO, stroke_width=2, stroke_fill=NEGRO)
    y += 120

    for linea in dividir_texto(datos["gancho"].upper(), f_gan, 950)[:2]:
        d.text((55, y), linea, font=f_gan, fill=BLANCO, stroke_width=2, stroke_fill=NEGRO)
        y += 135

    y += 20

   for linea in dividir_texto(datos["subtitulo"], f_sub, 900)[:2]:
     d.text((55, y), linea, font=f_sub, fill=BLANCO)
     y += 56

    d.rectangle((55, 1285, 1025, 1292), fill=MORADO)
    return img

def plantilla_quote(datos, imagen):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(img)

    d.rectangle((0,0,470,ALTO), fill=MORADO_ENTREVISTA)

    foto = recortar_vertical(imagen, 620, ALTO)
    foto = Image.blend(foto, Image.new("RGB",(620,ALTO),NEGRO), 0.25)
    img.paste(foto, (460,0))

    sombra = Image.new("RGBA",(ANCHO,ALTO),(0,0,0,0))
    sd = ImageDraw.Draw(sombra)
    for x in range(430,720):
        a = int(210 * (1 - (x-430)/290))
        sd.line((x,0,x,ALTO), fill=(0,0,0,a))
    img = Image.alpha_composite(img.convert("RGBA"), sombra).convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((55,65), "FRBL", font=cargar_fuente(78, "display"), fill=(0,0,0))
    d.text((55,220), "ENTREVISTA", font=cargar_fuente(36, "display"), fill=BLANCO)
    d.text((55,340), "“", font=cargar_fuente(150, "display"), fill=BLANCO)

    y = 500
    f_quote = cargar_fuente(54, "display")
    for linea in dividir_texto(datos["gancho"].upper(), f_quote, 390)[:5]:
        d.text((55,y), linea, font=f_quote, fill=BLANCO)
        y += 58

    d.text((55,950), f"— {datos['titulo'].upper()}", font=cargar_fuente(42), fill=NEGRO)

    y = 1020
    for linea in dividir_texto(datos["subtitulo"], cargar_fuente(34), 380)[:3]:
        d.text((55,y), linea, font=cargar_fuente(34), fill=NEGRO)
        y += 42

    d.rectangle((55,1285,420,1292), fill=NEGRO)
    return img

def plantilla_radar(datos, imagen):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(img)

    d.rectangle((0,0,ANCHO,420), fill=MORADO)
    d.rectangle((0,420,ANCHO,ALTO), fill=NEGRO)

    foto = recortar_cuadrado(imagen, 650)
    img.paste(foto, (215,250))
    d.rectangle((200,235,880,915), outline=BLANCO, width=8)

    img = poner_logo(img, tamano=260, pos=(55,55))
    d = ImageDraw.Draw(img)

    d.text((55,150), "RADAR", font=cargar_fuente(90), fill=BLANCO)
    d.text((55,925), datos["titulo"].upper(), font=cargar_fuente(86), fill=BLANCO)

    y = 1030
    for linea in dividir_texto(datos["gancho"].upper(), cargar_fuente(62), 950)[:2]:
        d.text((55,y), linea, font=cargar_fuente(62), fill=MORADO)
        y += 70

    for linea in dividir_texto(datos["subtitulo"], cargar_fuente(38), 900)[:3]:
        d.text((55,y+10), linea, font=cargar_fuente(38), fill=BLANCO)
        y += 45

    d.rectangle((55,1285,1025,1292), fill=MORADO)
    return img

def generar_post(plantilla, datos, imagen):
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
    logo_b64 = base64.b64encode(open("logo/frbl.png","rb").read()).decode()
    st.markdown(f"""
    <div class="logo-title">
      <img src="data:image/png;base64,{logo_b64}">
      <span class="brand">freshbloc</span>
      <span class="ia">IA</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h1>freshbloc IA</h1>", unsafe_allow_html=True)

st.write("Generador de publicaciones urbanas para Instagram.")

plantilla = st.selectbox("Escoge plantilla", [
    "Noticia / Foto artista",
    "Lanzamiento / Portada",
    "Quote / Entrevista",
    "Radar / Emergente"
])

noticia = st.text_area("Pega la noticia", height=150)

cita_manual = ""
if plantilla == "Quote / Entrevista":
    cita_manual = st.text_area(
        f"Cita exacta del artista — máximo {MAX_CITA} caracteres",
        height=110,
        max_chars=MAX_CITA
    )

modo_imagen = st.radio("Imagen para el post", ["Subir imagen manual", "Usar foto aleatoria del artista"])

rotacion_img = st.selectbox("Rotación de imagen", [0, 90, 180, 270], index=0)

imagen_subida = None
if modo_imagen == "Subir imagen manual":
    imagen_subida = st.file_uploader("Sube portada, foto, flyer o screenshot", type=["jpg","jpeg","png","webp"])

if st.button("GENERAR POST"):
    if not noticia.strip():
        st.error("Pega una noticia primero.")
    elif plantilla == "Quote / Entrevista" and not cita_manual.strip():
        st.error("Para entrevista, pega una cita exacta.")
    else:
        with st.spinner("Generando con Freshbloc IA..."):
            datos = analizar_noticia(noticia, plantilla, cita_manual)

            if modo_imagen == "Subir imagen manual":
                if imagen_subida is None:
                    st.error("Sube una imagen primero.")
                    st.stop()
                imagen = abrir_imagen_segura(imagen_subida, rotacion_img)
            else:
                ruta = elegir_foto(datos["artista"])
                imagen = abrir_imagen_segura(ruta, rotacion_img)

            post = generar_post(plantilla, datos, imagen)

            buffer = io.BytesIO()
            post.save(buffer, format="PNG")
            buffer.seek(0)

            st.session_state.post_buffer = buffer.getvalue()
            st.session_state.datos = datos

if st.session_state.post_buffer:
    st.image(st.session_state.post_buffer, caption="Post generado", use_container_width=True)

    st.download_button(
        "DESCARGAR POST",
        data=st.session_state.post_buffer,
        file_name=f"freshbloc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        mime="image/png"
    )

if st.session_state.datos:
    datos = st.session_state.datos
    st.markdown("### Caption")
    st.markdown(f"<div class='caption-box'>{datos.get('caption','')}</div>", unsafe_allow_html=True)

    st.markdown("### Hashtags")
    st.markdown(f"<div class='caption-box'>{' '.join(datos.get('hashtags', []))}</div>", unsafe_allow_html=True)
