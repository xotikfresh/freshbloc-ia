import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from groq import Groq
import os, json, io, base64
from datetime import datetime

st.set_page_config(page_title="Freshbloc IA", page_icon="FRBL", layout="centered")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

ANCHO, ALTO = 1080, 1350
MORADO = (145, 60, 255)
MORADO_OSCURO = (125, 40, 230)
NEGRO = (8, 8, 10)
BLANCO = (245, 245, 245)

st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#08080A,#13001F); color:white;}
.block-container {max-width:780px; padding:1rem;}
h1,h2,h3,p,label,span {color:white!important;}
.logo-title {display:flex; align-items:center; gap:16px; margin-bottom:10px;}
.logo-title img {width:160px; max-width:45vw;}
.logo-title .brand,.logo-title .ia {font-size:42px; font-weight:900;}
.logo-title .ia {color:#913CFF!important;}
.stTextArea textarea, .stTextInput input {
 background:#111!important; color:white!important; border:1px solid #913CFF!important;
 font-size:18px!important; border-radius:14px!important;
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
.small-box {
 background:#170020; border:1px solid #4d1d80; padding:13px; border-radius:14px;
 font-size:16px; line-height:1.45;
}
@media(max-width:600px){
 .logo-title img{width:115px;}
 .logo-title .brand,.logo-title .ia{font-size:32px;}
}
</style>
""", unsafe_allow_html=True)


def cargar_fuente(tamano, tipo="bold"):
    fuentes = [
        "assets/Anton-Regular.ttf" if tipo == "display" else "assets/Montserrat-Bold.ttf",
        "assets/Montserrat-Bold.ttf",
        "assets/Anton-Regular.ttf",
        "arialbd.ttf",
    ]

    for fuente in fuentes:
        try:
            return ImageFont.truetype(fuente, tamano)
        except Exception:
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
        ancho = d.textbbox((0, 0), prueba, font=fuente)[2]
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


def poner_logo(img, tamano=260, pos=(55, 55)):
    logo_path = "logo/frbl.png"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((tamano, tamano))
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo, pos, logo)
        return img_rgba.convert("RGB")

    d = ImageDraw.Draw(img)
    d.text(pos, "FRBL", font=cargar_fuente(76, "display"), fill=MORADO)
    return img


def fondo_con_foto(imagen):
    img = recortar_vertical(imagen, ANCHO, ALTO)
    img = Image.blend(img, Image.new("RGB", (ANCHO, ALTO), NEGRO), 0.22)

    overlay = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    for y in range(ALTO):
        if y > 420:
            a = min(int(245 * ((y - 420) / (ALTO - 420))), 245)
            d.line((0, y, ANCHO, y), fill=(0, 0, 0, a))

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def fondo_simple():
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, ANCHO, 430), fill=MORADO)
    d.ellipse((620, -250, 1350, 450), fill=(45, 15, 80))
    return img


def limpiar_datos(datos):
    campos = [
        "tipo", "titulo", "gancho", "subtitulo", "caption",
        "historia", "whatsapp", "hashtags", "cta", "idea_visual"
    ]

    for campo in campos:
        if campo not in datos:
            datos[campo] = [] if campo == "hashtags" else ""

    if not isinstance(datos["hashtags"], list):
        datos["hashtags"] = ["#NegocioLocal", "#Emprendimiento", "#Chile"]

    return datos


def analizar_publicacion(nombre_negocio, rubro, tono, tipo_publicacion, descripcion):
    prompt = f"""
Eres un community manager experto en pequeños negocios de Chile.

Tu tarea es crear contenido listo para publicar en Instagram, historias y WhatsApp.

Devuelve SOLO JSON válido. No agregues explicación.

Formato obligatorio:
{{
  "tipo":"",
  "titulo":"",
  "gancho":"",
  "subtitulo":"",
  "caption":"",
  "historia":"",
  "whatsapp":"",
  "hashtags":[],
  "cta":"",
  "idea_visual":""
}}

Datos del negocio:
- Nombre: {nombre_negocio}
- Rubro: {rubro}
- Tono de marca: {tono}
- Tipo de publicación: {tipo_publicacion}

Lo que quiere publicar:
{descripcion}

Reglas:
- No inventes precios, fechas, stock, descuentos ni direcciones.
- Usa solo los datos entregados.
- Si falta información, escribe de forma útil sin inventar.
- "titulo" debe ser el nombre del negocio o una versión corta.
- "gancho" máximo 4 palabras, en mayúsculas, fuerte y claro.
- "subtitulo" máximo 12 palabras.
- "caption" entre 45 y 90 palabras.
- "historia" debe ser corto, estilo story de Instagram.
- "whatsapp" debe ser un mensaje breve para enviar a clientes.
- "hashtags" entre 5 y 8, mezclando rubro + ciudad si aparece + negocio local.
- "cta" debe ser una llamada a la acción breve.
- "idea_visual" debe explicar cómo debería verse el diseño.
- No uses lenguaje robótico.
- No uses emojis excesivos.
- No repitas el nombre del negocio muchas veces.

Estilo:
- Profesional, vendible y humano.
- Debe sonar como negocio real, no como IA.
"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35,
        response_format={"type": "json_object"}
    )

    datos = json.loads(r.choices[0].message.content)
    return limpiar_datos(datos)


def plantilla_promocion(datos, imagen=None):
    img = fondo_con_foto(imagen) if imagen else fondo_simple()
    img = poner_logo(img)
    d = ImageDraw.Draw(img)

    f_cat = cargar_fuente(36, "display")
    f_titulo = cargar_fuente(82, "display")
    f_gancho = cargar_fuente(94, "display")
    f_sub = cargar_fuente(54, "bold")

    cat = datos["tipo"].upper()
    w = d.textbbox((0, 0), cat, font=f_cat)[2]
    d.text((ANCHO - w - 55, 70), cat, font=f_cat, fill=MORADO)

    d.text((55, 790), datos["titulo"].upper(), font=f_titulo, fill=BLANCO)

    y = 900
    for linea in dividir_texto(datos["gancho"].upper(), f_gancho, 780)[:2]:
        d.text((55, y), linea, font=f_gancho, fill=MORADO)
        y += 100

    y += 10
    for linea in dividir_texto(datos["subtitulo"], f_sub, 900)[:2]:
        d.text((55, y), linea, font=f_sub, fill=BLANCO)
        y += 62

    d.rectangle((55, 1285, 1025, 1292), fill=MORADO)
    return img


def plantilla_producto(datos, imagen=None):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(img)

    if imagen:
        fondo = recortar_vertical(imagen, ANCHO, ALTO).filter(ImageFilter.GaussianBlur(45))
        fondo = Image.blend(fondo, Image.new("RGB", (ANCHO, ALTO), NEGRO), 0.65)
        img.paste(fondo, (0, 0))

        producto = recortar_cuadrado(imagen, 620)
        img.paste(producto, (230, 105))
        d.rectangle((210, 85, 870, 745), outline=MORADO, width=10)
    else:
        d.rectangle((210, 85, 870, 745), outline=MORADO, width=10)
        d.text((280, 360), "TU PRODUCTO", font=cargar_fuente(72, "display"), fill=BLANCO)

    img = poner_logo(img, tamano=250, pos=(55, 55))
    d = ImageDraw.Draw(img)

    f_tag = cargar_fuente(48, "display")
    f_titulo = cargar_fuente(86, "display")
    f_gan = cargar_fuente(112, "display")
    f_sub = cargar_fuente(52, "bold")

    y = 770
    d.text((55, y), datos["tipo"].upper(), font=f_tag, fill=MORADO)
    y += 78

    d.text((55, y), datos["titulo"].upper(), font=f_titulo, fill=BLANCO)
    y += 112

    for linea in dividir_texto(datos["gancho"].upper(), f_gan, 850)[:2]:
        d.text((55, y), linea, font=f_gan, fill=BLANCO)
        y += 120

    y += 10
    for linea in dividir_texto(datos["subtitulo"], f_sub, 900)[:2]:
        d.text((55, y), linea, font=f_sub, fill=BLANCO)
        y += 58

    d.rectangle((55, 1285, 1025, 1292), fill=MORADO)
    return img


def plantilla_evento(datos, imagen=None):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, ANCHO, 430), fill=MORADO)
    d.text((55, 65), "FRBL", font=cargar_fuente(78, "display"), fill=(0, 0, 0))
    d.text((55, 155), datos["tipo"].upper(), font=cargar_fuente(88, "display"), fill=BLANCO)

    if imagen:
        foto = recortar_cuadrado(imagen, 650)
        img.paste(foto, (215, 255))
        d.rectangle((200, 240, 880, 920), outline=BLANCO, width=8)

    d.text((55, 940), datos["titulo"].upper(), font=cargar_fuente(82, "display"), fill=(220, 220, 220))

    y = 1040
    for linea in dividir_texto(datos["gancho"].upper(), cargar_fuente(58, "display"), 850)[:2]:
        d.text((55, y), linea, font=cargar_fuente(58, "display"), fill=MORADO)
        y += 66

    for linea in dividir_texto(datos["subtitulo"], cargar_fuente(48, "bold"), 900)[:2]:
        d.text((55, y + 10), linea, font=cargar_fuente(48, "bold"), fill=BLANCO)
        y += 56

    d.rectangle((55, 1285, 1025, 1292), fill=MORADO)
    return img


def plantilla_testimonio(datos, imagen=None):
    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, 470, ALTO), fill=MORADO_OSCURO)

    if imagen:
        foto = recortar_vertical(imagen, 620, ALTO)
        foto = Image.blend(foto, Image.new("RGB", (620, ALTO), NEGRO), 0.25)
        img.paste(foto, (460, 0))

    sombra = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sombra)
    for x in range(430, 720):
        a = int(210 * (1 - (x - 430) / 290))
        sd.line((x, 0, x, ALTO), fill=(0, 0, 0, a))

    img = Image.alpha_composite(img.convert("RGBA"), sombra).convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((55, 65), "FRBL", font=cargar_fuente(78, "display"), fill=(0, 0, 0))
    d.text((55, 220), datos["tipo"].upper(), font=cargar_fuente(36, "display"), fill=BLANCO)
    d.text((55, 340), "“", font=cargar_fuente(150, "display"), fill=BLANCO)

    cita = datos["gancho"].upper().strip()
    f_quote = cargar_fuente(58, "display")
    y = 475
    for linea in dividir_texto(cita, f_quote, 390)[:6]:
        d.text((55, y), linea, font=f_quote, fill=BLANCO)
        y += 66

    d.text((55, 930), datos["titulo"].upper(), font=cargar_fuente(54, "display"), fill=BLANCO)

    y = 1010
    for linea in dividir_texto(datos["subtitulo"], cargar_fuente(42, "bold"), 380)[:3]:
        d.text((55, y), linea, font=cargar_fuente(42, "bold"), fill=BLANCO)
        y += 54

    d.rectangle((55, 1285, 420, 1292), fill=BLANCO)
    return img


def generar_post(tipo_publicacion, datos, imagen):
    if tipo_publicacion == "Producto":
        return plantilla_producto(datos, imagen)
    if tipo_publicacion == "Evento":
        return plantilla_evento(datos, imagen)
    if tipo_publicacion == "Testimonio":
        return plantilla_testimonio(datos, imagen)
    return plantilla_promocion(datos, imagen)


if "post_buffer" not in st.session_state:
    st.session_state.post_buffer = None

if "datos" not in st.session_state:
    st.session_state.datos = None


if os.path.exists("logo/frbl.png"):
    logo_b64 = base64.b64encode(open("logo/frbl.png", "rb").read()).decode()
    st.markdown(f"""
    <div class="logo-title">
      <img src="data:image/png;base64,{logo_b64}">
      <span class="brand">freshbloc</span>
      <span class="ia">IA</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h1>freshbloc IA</h1>", unsafe_allow_html=True)

st.write("Tu contenido de Instagram listo en menos de 1 minuto.")

st.markdown("### Perfil del negocio")

nombre_negocio = st.text_input("Nombre del negocio", placeholder="Ej: Barbería El Corte")
rubro = st.selectbox("Rubro", [
    "Barbería",
    "Restaurante",
    "Cafetería",
    "Tienda de ropa",
    "Gimnasio",
    "Belleza / uñas",
    "Minimarket",
    "Delivery",
    "Otro"
])

tono = st.selectbox("Tono de marca", [
    "Cercano",
    "Juvenil",
    "Profesional",
    "Premium",
    "Divertido",
    "Urgente / venta rápida"
])

tipo_publicacion = st.selectbox("Tipo de publicación", [
    "Promoción",
    "Producto",
    "Evento",
    "Testimonio"
])

descripcion = st.text_area(
    "Describe qué quieres publicar",
    height=150,
    placeholder="Ej: Tenemos 20% de descuento en cortes + barba hasta este viernes para estudiantes."
)

rotacion_img = st.selectbox("Rotación de imagen", [0, 90, 180, 270], index=0)

imagen_subida = st.file_uploader(
    "Sube una imagen del producto, local, flyer o referencia",
    type=["jpg", "jpeg", "png", "webp"]
)

if st.button("GENERAR CONTENIDO"):
    if not nombre_negocio.strip():
        st.error("Escribe el nombre del negocio.")
    elif not descripcion.strip():
        st.error("Describe qué quieres publicar.")
    else:
        with st.spinner("Generando contenido con Freshbloc IA..."):
            datos = analizar_publicacion(
                nombre_negocio,
                rubro,
                tono,
                tipo_publicacion,
                descripcion
            )

            datos["tipo"] = tipo_publicacion.upper()

            imagen = None
            if imagen_subida is not None:
                imagen = abrir_imagen_segura(imagen_subida, rotacion_img)

            post = generar_post(tipo_publicacion, datos, imagen)

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
        file_name=f"freshbloc_negocio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        mime="image/png"
    )

if st.session_state.datos:
    datos = st.session_state.datos

    st.markdown("### Caption Instagram")
    st.markdown(f"<div class='caption-box'>{datos.get('caption','')}</div>", unsafe_allow_html=True)

    st.markdown("### Historia Instagram")
    st.markdown(f"<div class='small-box'>{datos.get('historia','')}</div>", unsafe_allow_html=True)

    st.markdown("### Mensaje WhatsApp")
    st.markdown(f"<div class='small-box'>{datos.get('whatsapp','')}</div>", unsafe_allow_html=True)

    st.markdown("### Hashtags")
    st.markdown(f"<div class='caption-box'>{' '.join(datos.get('hashtags', []))}</div>", unsafe_allow_html=True)

    st.markdown("### Idea visual")
    st.markdown(f"<div class='small-box'>{datos.get('idea_visual','')}</div>", unsafe_allow_html=True)
