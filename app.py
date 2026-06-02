import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from groq import Groq
import os, json, io, base64, random
from datetime import datetime

st.set_page_config(page_title="Freshbloc IA", page_icon="FRBL", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

ANCHO, ALTO = 1080, 1350
MORADO = (145, 60, 255)
NEGRO = (8, 8, 10)
BLANCO = (245, 245, 245)

st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#08080A,#120018); color:white;}
.block-container {max-width:1250px; padding:1.2rem;}
h1,h2,h3,p,label,span {color:white!important;}
.stTextArea textarea, .stTextInput input {
 background:#111!important; color:white!important; border:1px solid #913CFF!important;
 font-size:18px!important; border-radius:14px!important;
}
.stButton>button,.stDownloadButton>button {
 background:#913CFF; color:white; border-radius:18px; border:none;
 padding:1rem 1.5rem; font-weight:900; width:100%; font-size:18px;
}
.box {
 background:#111; border:1px solid #913CFF; padding:16px; border-radius:14px;
 font-size:17px; line-height:1.45;
}
.preview-card {
 background:#0d0d10; border:1px solid #2d0d48; padding:18px; border-radius:20px;
}
</style>
""", unsafe_allow_html=True)


def fuente(tam, display=False):
    opciones = [
        "assets/Anton-Regular.ttf" if display else "assets/Montserrat-Bold.ttf",
        "assets/Montserrat-Bold.ttf",
        "assets/Anton-Regular.ttf",
        "arialbd.ttf"
    ]
    for f in opciones:
        try:
            return ImageFont.truetype(f, tam)
        except:
            pass
    return ImageFont.load_default()


def abrir_img(origen, rotacion=0):
    img = Image.open(origen)
    img = ImageOps.exif_transpose(img).convert("RGB")
    if rotacion == 90:
        img = img.rotate(-90, expand=True)
    elif rotacion == 180:
        img = img.rotate(180, expand=True)
    elif rotacion == 270:
        img = img.rotate(90, expand=True)
    return img


def recortar(imagen, w_final, h_final):
    imagen = imagen.convert("RGB")
    w, h = imagen.size
    r_obj = w_final / h_final
    r = w / h
    if r > r_obj:
        nw = int(h * r_obj)
        x = (w - nw) // 2
        imagen = imagen.crop((x, 0, x + nw, h))
    else:
        nh = int(w / r_obj)
        y = (h - nh) // 2
        imagen = imagen.crop((0, y, w, y + nh))
    return imagen.resize((w_final, h_final))


def lineas(texto, f, max_w):
    texto = str(texto or "").strip()
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    palabras = texto.split()
    out, actual = [], ""
    for p in palabras:
        prueba = actual + " " + p if actual else p
        if d.textbbox((0, 0), prueba, font=f)[2] <= max_w:
            actual = prueba
        else:
            if actual:
                out.append(actual)
            actual = p
    if actual:
        out.append(actual)
    return out


def poner_logo(img):
    logo_path = "logo/frbl.png"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((230, 230))
        base = img.convert("RGBA")
        base.paste(logo, (55, 55), logo)
        return base.convert("RGB")
    d = ImageDraw.Draw(img)
    d.text((55, 55), "FRBL", font=fuente(76, True), fill=MORADO)
    return img


def limpiar(datos):
    campos = ["tipo", "titulo", "gancho", "subtitulo", "caption", "historia", "whatsapp", "hashtags", "cta"]
    for c in campos:
        if c not in datos:
            datos[c] = [] if c == "hashtags" else ""
    if not isinstance(datos["hashtags"], list):
        datos["hashtags"] = ["#NegocioLocal", "#Emprendimiento", "#Chile"]
    datos["hashtags"] = [
        h if str(h).startswith("#") else "#" + str(h).replace(" ", "")
        for h in datos["hashtags"]
    ]
    return datos


def analizar(nombre, rubro, tono, tipo, descripcion):
    prompt = f"""
Eres community manager para pequeños negocios de Chile.

Devuelve SOLO JSON válido.

Formato:
{{
 "tipo":"",
 "titulo":"",
 "gancho":"",
 "subtitulo":"",
 "caption":"",
 "historia":"",
 "whatsapp":"",
 "hashtags":[],
 "cta":""
}}

Negocio: {nombre}
Rubro: {rubro}
Tono: {tono}
Tipo de publicación: {tipo}
Descripción: {descripcion}

Reglas:
- No inventes precio, fecha, stock, dirección ni descuento.
- Gancho máximo 4 palabras, en mayúsculas.
- Subtítulo máximo 12 palabras.
- Caption corto, humano y vendedor.
- Historia muy corta.
- WhatsApp directo y natural.
- Hashtags deben venir con #.
- No repitas mucho el nombre del negocio.
- Evita frases genéricas como "no te lo pierdas".
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35,
        response_format={"type": "json_object"}
    )
    return limpiar(json.loads(r.choices[0].message.content))


def crear_diseno(datos, imagen=None, estilo=None):
    if estilo is None:
        estilo = random.choice(["editorial", "producto", "bloque", "minimal"])

    img = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(img)

    if imagen:
        fondo = recortar(imagen, ANCHO, ALTO).filter(ImageFilter.GaussianBlur(35))
        fondo = Image.blend(fondo, Image.new("RGB", (ANCHO, ALTO), NEGRO), 0.62)
        img.paste(fondo, (0, 0))

    if estilo == "editorial":
        if imagen:
            foto = recortar(imagen, 760, 760)
            img.paste(foto, (160, 145))
            d.rectangle((140, 125, 940, 925), outline=MORADO, width=10)
        d.rectangle((0, 1040, ANCHO, ALTO), fill=MORADO)

    elif estilo == "producto":
        d.rectangle((0, 0, 360, ALTO), fill=MORADO)
        if imagen:
            foto = recortar(imagen, 690, 880)
            img.paste(foto, (330, 110))
            d.rectangle((310, 90, 1040, 1010), outline=BLANCO, width=8)

    elif estilo == "bloque":
        d.rectangle((0, 0, ANCHO, 420), fill=MORADO)
        if imagen:
            foto = recortar(imagen, 780, 620)
            img.paste(foto, (150, 250))
            d.rectangle((130, 230, 950, 890), outline=BLANCO, width=8)

    else:
        if imagen:
            foto = recortar(imagen, 850, 650)
            img.paste(foto, (115, 120))
        d.rectangle((55, 55, 1025, 1295), outline=MORADO, width=8)

    img = poner_logo(img)
    d = ImageDraw.Draw(img)

    f_tipo = fuente(42, True)
    f_titulo = fuente(82, True)
    f_gancho = fuente(112, True)
    f_sub = fuente(48, False)

    y = 930 if estilo in ["editorial", "bloque", "minimal"] else 1010

    if estilo == "producto":
        x = 70
        color_gancho = BLANCO
    else:
        x = 70
        color_gancho = MORADO if estilo != "editorial" else BLANCO

    d.text((x, y), datos["tipo"].upper(), font=f_tipo, fill=MORADO if estilo != "editorial" else NEGRO)
    y += 70

    d.text((x, y), datos["titulo"].upper(), font=f_titulo, fill=BLANCO if estilo != "editorial" else NEGRO)
    y += 105

    for l in lineas(datos["gancho"].upper(), f_gancho, 900)[:2]:
        d.text((x, y), l, font=f_gancho, fill=color_gancho)
        y += 115

    for l in lineas(datos["subtitulo"], f_sub, 900)[:2]:
        d.text((x, y + 10), l, font=f_sub, fill=BLANCO if estilo != "editorial" else NEGRO)
        y += 55

    return img


if "post_buffer" not in st.session_state:
    st.session_state.post_buffer = None
if "datos" not in st.session_state:
    st.session_state.datos = None

st.markdown("<h1 style='text-align:center;'>FRBL · freshbloc IA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Tu contenido de Instagram listo en menos de 1 minuto.</p>", unsafe_allow_html=True)

izq, der = st.columns([0.9, 1.1], gap="large")

with izq:
    st.markdown("## Perfil del negocio")

    nombre = st.text_input("Nombre del negocio", placeholder="Ej: Barbería El Corte")
    rubro = st.selectbox("Rubro", [
        "Barbería", "Restaurante", "Cafetería", "Tienda de ropa",
        "Gimnasio", "Belleza / uñas", "Minimarket", "Delivery", "Otro"
    ])
    tono = st.selectbox("Tono de marca", [
        "Cercano", "Juvenil", "Profesional", "Premium", "Divertido", "Urgente / venta rápida"
    ])
    tipo = st.selectbox("Tipo de publicación", [
        "Promoción", "Producto", "Evento", "Testimonio", "Informativo", "Sorteo"
    ])
    descripcion = st.text_area(
        "Describe qué quieres publicar",
        height=150,
        placeholder="Ej: Shampoo que deja el pelo suave y brillante."
    )
    estilo = st.selectbox("Estilo visual", [
        "Aleatorio", "Editorial", "Producto", "Bloque", "Minimal"
    ])
    rotacion = st.selectbox("Rotación de imagen", [0, 90, 180, 270], index=0)
    imagen_subida = st.file_uploader("Sube imagen del producto, local o referencia", type=["jpg", "jpeg", "png", "webp"])

    generar = st.button("GENERAR CONTENIDO")

with der:
    st.markdown("## Vista previa")

    if generar:
        if not nombre.strip():
            st.error("Escribe el nombre del negocio.")
        elif not descripcion.strip():
            st.error("Describe qué quieres publicar.")
        else:
            with st.spinner("Generando..."):
                datos = analizar(nombre, rubro, tono, tipo, descripcion)
                datos["tipo"] = tipo.upper()

                imagen = abrir_img(imagen_subida, rotacion) if imagen_subida else None
                estilo_real = None if estilo == "Aleatorio" else estilo.lower()

                post = crear_diseno(datos, imagen, estilo_real)

                buffer = io.BytesIO()
                post.save(buffer, format="PNG")
                buffer.seek(0)

                st.session_state.post_buffer = buffer.getvalue()
                st.session_state.datos = datos

    if st.session_state.post_buffer:
        st.markdown("<div class='preview-card'>", unsafe_allow_html=True)
        st.image(st.session_state.post_buffer, caption="Post generado", use_container_width=True)
        st.download_button(
            "DESCARGAR POST",
            data=st.session_state.post_buffer,
            file_name=f"freshbloc_negocio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Completa los datos y genera tu primer post.")

if st.session_state.datos:
    datos = st.session_state.datos

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Caption Instagram")
        st.markdown(f"<div class='box'>{datos.get('caption','')}</div>", unsafe_allow_html=True)

        st.markdown("### Historia Instagram")
        st.markdown(f"<div class='box'>{datos.get('historia','')}</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("### Mensaje WhatsApp")
        st.markdown(f"<div class='box'>{datos.get('whatsapp','')}</div>", unsafe_allow_html=True)

        st.markdown("### Hashtags")
        st.markdown(f"<div class='box'>{' '.join(datos.get('hashtags', []))}</div>", unsafe_allow_html=True)
