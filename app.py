import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from groq import Groq
import os, json, io, random
from datetime import datetime

st.set_page_config(page_title="Content IA", page_icon="⚡", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

ANCHO, ALTO = 1080, 1350
BLANCO = (245, 245, 245)
NEGRO = (10, 10, 12)

st.markdown("""
<style>
.stApp {background:#08080A; color:white;}
.block-container {max-width:1300px; padding:1.2rem;}
h1,h2,h3,p,label,span {color:white!important;}
.stTextArea textarea, .stTextInput input {
 background:#111!important; color:white!important; border:1px solid #555!important;
 font-size:18px!important; border-radius:14px!important;
}
.stButton>button,.stDownloadButton>button {
 background:white; color:black; border-radius:16px; border:none;
 padding:1rem 1.5rem; font-weight:900; width:100%; font-size:18px;
}
.box {
 background:#111; border:1px solid #333; padding:16px; border-radius:14px;
 font-size:17px; line-height:1.45;
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


def hex_rgb(h):
    h = str(h).replace("#", "").strip()
    if len(h) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (255, 255, 255)


def analizar(nombre, rubro, tono, tipo, descripcion):
    prompt = f"""
Eres director creativo y community manager para negocios en Chile.

Crea una publicación personalizada. NO uses plantillas genéricas.
Debes decidir el estilo visual según el negocio, rubro, tono y publicación.

Devuelve SOLO JSON válido.

Formato:
{{
 "titulo":"",
 "gancho":"",
 "subtitulo":"",
 "caption":"",
 "historia":"",
 "whatsapp":"",
 "hashtags":[],
 "cta":"",
 "direccion_arte":{{
   "estilo":"",
   "color_fondo":"#000000",
   "color_principal":"#FFFFFF",
   "color_secundario":"#CCCCCC",
   "color_texto":"#FFFFFF",
   "layout":"",
   "tratamiento_imagen":"",
   "sensacion":""
 }}
}}

Negocio: {nombre}
Rubro: {rubro}
Tono: {tono}
Tipo de publicación: {tipo}
Descripción: {descripcion}

Reglas de contenido:
- No inventes precio, fecha, stock, dirección ni descuento.
- Gancho máximo 4 palabras.
- Subtítulo máximo 12 palabras.
- Caption corto, humano y vendedor.
- Hashtags con #.
- No repitas mucho el nombre del negocio.
- Evita “no te lo pierdas”.
- Que suene a negocio real, no a IA.

Reglas visuales:
- NO uses morado por defecto.
- NO uses Freshbloc.
- NO uses FRBL.
- Decide colores según el rubro.
- Para barbería usa colores como negro, crema, blanco, gris, dorado, azul oscuro o rojo oscuro.
- Para comida usa colores cálidos.
- Para ropa usa colores editoriales.
- Para belleza usa colores suaves o premium.
- El layout debe ser distinto según el caso.
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.55,
        response_format={"type": "json_object"}
    )
    datos = json.loads(r.choices[0].message.content)

    if "hashtags" not in datos or not isinstance(datos["hashtags"], list):
        datos["hashtags"] = ["#NegocioLocal", "#Chile", "#Emprendimiento"]

    for i, h in enumerate(datos["hashtags"]):
        h = str(h).replace(" ", "")
        datos["hashtags"][i] = h if h.startswith("#") else "#" + h

    return datos


def crear_post(datos, imagen=None):
    arte = datos.get("direccion_arte", {})
    fondo = hex_rgb(arte.get("color_fondo", "#111111"))
    principal = hex_rgb(arte.get("color_principal", "#FFFFFF"))
    secundario = hex_rgb(arte.get("color_secundario", "#CCCCCC"))
    texto = hex_rgb(arte.get("color_texto", "#FFFFFF"))

    img = Image.new("RGB", (ANCHO, ALTO), fondo)
    d = ImageDraw.Draw(img)

    layout = random.choice(["full", "magazine", "split", "poster"])

    if imagen:
        if layout == "full":
            foto = recortar(imagen, ANCHO, ALTO)
            foto = Image.blend(foto, Image.new("RGB", (ANCHO, ALTO), fondo), 0.28)
            img.paste(foto, (0, 0))
            overlay = Image.new("RGBA", (ANCHO, ALTO), (0,0,0,0))
            od = ImageDraw.Draw(overlay)
            for y in range(ALTO):
                if y > 530:
                    a = min(int(230 * ((y - 530) / (ALTO - 530))), 230)
                    od.line((0, y, ANCHO, y), fill=(0,0,0,a))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            d = ImageDraw.Draw(img)
            text_y = 820

        elif layout == "magazine":
            foto = recortar(imagen, 820, 720)
            img.paste(foto, (130, 110))
            d.rectangle((80, 70, 1000, 880), outline=principal, width=8)
            text_y = 920

        elif layout == "split":
            foto = recortar(imagen, 520, ALTO)
            img.paste(foto, (560, 0))
            d.rectangle((0, 0, 540, ALTO), fill=fondo)
            d.rectangle((55, 70, 500, 1280), outline=principal, width=6)
            text_y = 520

        else:
            foto = recortar(imagen, 740, 740)
            img.paste(foto, (170, 170))
            d.rectangle((0, 0, ANCHO, 95), fill=principal)
            d.rectangle((0, 1255, ANCHO, ALTO), fill=principal)
            text_y = 950
    else:
        d.rectangle((70, 70, 1010, 1280), outline=principal, width=8)
        d.ellipse((700, -200, 1250, 350), fill=secundario)
        text_y = 500

    f_marca = fuente(46, True)
    f_gancho = fuente(118, True)
    f_sub = fuente(48, False)
    f_cta = fuente(38, False)

    if layout == "split":
        x = 90
        max_w = 390
    else:
        x = 80
        max_w = 900

    d.text((x, 90 if layout != "magazine" else 920), datos.get("titulo","").upper(), font=f_marca, fill=principal)

    y = text_y
    for l in lineas(datos.get("gancho","").upper(), f_gancho, max_w)[:3]:
        d.text((x, y), l, font=f_gancho, fill=texto)
        y += 118

    y += 10
    for l in lineas(datos.get("subtitulo",""), f_sub, max_w)[:3]:
        d.text((x, y), l, font=f_sub, fill=secundario)
        y += 56

    cta = datos.get("cta", "")
    if cta:
        d.rounded_rectangle((x, min(y + 30, 1210), x + 430, min(y + 105, 1285)), radius=30, fill=principal)
        d.text((x + 32, min(y + 48, 1230)), cta.upper()[:28], font=f_cta, fill=fondo)

    return img


if "post_buffer" not in st.session_state:
    st.session_state.post_buffer = None
if "datos" not in st.session_state:
    st.session_state.datos = None

st.markdown("<h1 style='text-align:center;'>Content IA para negocios</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Crea publicaciones personalizadas sin plantillas fijas.</p>", unsafe_allow_html=True)

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
        placeholder="Ej: Inauguración de barbería en el centro. Queremos invitar gente este viernes."
    )
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
            with st.spinner("Generando diseño personalizado..."):
                datos = analizar(nombre, rubro, tono, tipo, descripcion)
                imagen = abrir_img(imagen_subida, rotacion) if imagen_subida else None

                post = crear_post(datos, imagen)

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
            file_name=f"post_negocio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png"
        )
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

        arte = datos.get("direccion_arte", {})
        st.markdown("### Dirección visual IA")
        st.markdown(f"<div class='box'>{arte.get('estilo','')}<br>{arte.get('sensacion','')}<br>{arte.get('tratamiento_imagen','')}</div>", unsafe_allow_html=True)
