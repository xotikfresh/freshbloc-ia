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



def elegir_fuente_visual():
    opciones_display = [
        "assets/Montserrat-Bold.ttf",
        "arialbd.ttf",
        "assets/Anton-Regular.ttf"
    ]
    opciones_texto = [
        "assets/Montserrat-Bold.ttf",
        "arial.ttf",
        "arialbd.ttf"
    ]
    return opciones_display, opciones_texto


def font_random(tam, fuerte=True):
    display, texto = elegir_fuente_visual()
    opciones = display if fuerte else texto
    random.shuffle(opciones)
    for f in opciones:
        try:
            return ImageFont.truetype(f, tam)
        except:
            pass
    return ImageFont.load_default()


def color_contraste(rgb):
    r, g, b = rgb
    brillo = (r * 299 + g * 587 + b * 114) / 1000
    return (10, 10, 12) if brillo > 150 else (245, 245, 245)


def crear_post(datos, imagen=None):
    arte = datos.get("direccion_arte", {})

    fondo = hex_rgb(arte.get("color_fondo", "#111111"))
    principal = hex_rgb(arte.get("color_principal", "#FFFFFF"))
    secundario = hex_rgb(arte.get("color_secundario", "#CCCCCC"))

    # Paletas de respaldo para evitar look Freshbloc
    paletas = [
        ((16, 16, 16), (238, 232, 220), (185, 150, 90)),
        ((245, 241, 232), (20, 20, 20), (120, 70, 40)),
        ((22, 30, 40), (240, 240, 235), (180, 40, 40)),
        ((235, 229, 218), (35, 35, 35), (90, 90, 90)),
        ((12, 22, 18), (235, 230, 210), (190, 160, 85)),
        ((250, 248, 242), (25, 25, 25), (160, 50, 40)),
    ]

    if principal == (255, 255, 255) and fondo == (17, 17, 17):
        fondo, principal, secundario = random.choice(paletas)

    img = Image.new("RGB", (ANCHO, ALTO), fondo)
    d = ImageDraw.Draw(img)

    texto_color = color_contraste(fondo)
    estilo = random.choice([
        "hero_foto",
        "editorial_limpio",
        "catalogo",
        "story_premium",
        "poster_texto",
        "split_creativo"
    ])

    if imagen:
        if estilo == "hero_foto":
            foto = recortar(imagen, ANCHO, ALTO)
            foto = Image.blend(foto, Image.new("RGB", (ANCHO, ALTO), fondo), random.uniform(0.18, 0.38))
            img.paste(foto, (0, 0))

            overlay = Image.new("RGBA", (ANCHO, ALTO), (0,0,0,0))
            od = ImageDraw.Draw(overlay)
            inicio = random.randint(450, 700)
            for y in range(ALTO):
                if y > inicio:
                    a = min(int(230 * ((y - inicio) / (ALTO - inicio))), 230)
                    od.line((0, y, ANCHO, y), fill=(0,0,0,a))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            d = ImageDraw.Draw(img)
            x = random.randint(55, 120)
            y = random.randint(760, 900)
            max_w = random.randint(760, 930)
            texto_color = (250, 250, 250)

        elif estilo == "editorial_limpio":
            d.rectangle((0, 0, ANCHO, ALTO), fill=fondo)
            foto_w = random.randint(700, 900)
            foto_h = random.randint(620, 820)
            foto = recortar(imagen, foto_w, foto_h)
            fx = (ANCHO - foto_w) // 2
            fy = random.randint(90, 180)
            img.paste(foto, (fx, fy))

            if random.choice([True, False]):
                d.rectangle((fx-18, fy-18, fx+foto_w+18, fy+foto_h+18), outline=principal, width=random.randint(4, 9))

            x = random.randint(70, 130)
            y = fy + foto_h + random.randint(55, 100)
            max_w = 900

        elif estilo == "catalogo":
            d.rectangle((0, 0, ANCHO, ALTO), fill=fondo)
            d.rectangle((0, 0, ANCHO, random.randint(170, 280)), fill=principal)
            foto = recortar(imagen, random.randint(560, 760), random.randint(620, 800))
            fx = random.randint(250, 430)
            fy = random.randint(220, 350)
            img.paste(foto, (fx, fy))

            x = random.randint(55, 100)
            y = random.randint(850, 980)
            max_w = 850
            texto_color = color_contraste(fondo)

        elif estilo == "story_premium":
            d.rectangle((40, 40, ANCHO-40, ALTO-40), outline=principal, width=5)
            foto = recortar(imagen, 860, 860)
            mask = Image.new("L", (860, 860), 0)
            md = ImageDraw.Draw(mask)
            md.rounded_rectangle((0, 0, 860, 860), radius=random.randint(25, 70), fill=255)
            fx, fy = 110, random.randint(90, 170)
            img.paste(foto, (fx, fy), mask)

            x = random.randint(75, 130)
            y = random.randint(980, 1070)
            max_w = 850

        elif estilo == "poster_texto":
            foto = recortar(imagen, ANCHO, ALTO)
            foto = Image.blend(foto, Image.new("RGB", (ANCHO, ALTO), fondo), 0.55)
            img.paste(foto, (0, 0))
            d.rectangle((random.randint(40,80), random.randint(80,160), random.randint(880,1040), random.randint(310,430)), fill=principal)
            x = random.randint(70, 130)
            y = random.randint(720, 880)
            max_w = 850
            texto_color = (245, 245, 245)

        else:
            d.rectangle((0, 0, ANCHO, ALTO), fill=fondo)
            lado = random.choice(["izq", "der"])
            foto_w = random.randint(480, 600)
            foto = recortar(imagen, foto_w, ALTO)
            fx = 0 if lado == "izq" else ANCHO - foto_w
            img.paste(foto, (fx, 0))

            if lado == "izq":
                x = foto_w + random.randint(55, 95)
                max_w = ANCHO - x - 55
            else:
                x = random.randint(55, 95)
                max_w = ANCHO - foto_w - 90
            y = random.randint(430, 620)
    else:
        # Sin foto: composición gráfica aleatoria
        for _ in range(random.randint(3, 7)):
            shape_color = random.choice([principal, secundario])
            x1 = random.randint(-100, 900)
            y1 = random.randint(-100, 1100)
            x2 = x1 + random.randint(120, 420)
            y2 = y1 + random.randint(120, 420)
            if random.choice([True, False]):
                d.ellipse((x1, y1, x2, y2), fill=shape_color)
            else:
                d.rectangle((x1, y1, x2, y2), fill=shape_color)
        x = random.randint(70, 140)
        y = random.randint(460, 720)
        max_w = 850

    # Tipografías menos Freshbloc y con tamaños variables
    f_marca = font_random(random.randint(34, 48), fuerte=False)
    f_gancho = font_random(random.randint(70, 105), fuerte=True)
    f_sub = font_random(random.randint(34, 46), fuerte=False)
    f_cta = font_random(random.randint(28, 36), fuerte=False)

    marca = datos.get("titulo", "").upper()
    gancho = datos.get("gancho", "").upper()
    subtitulo = datos.get("subtitulo", "")
    cta = datos.get("cta", "")

    # Marca en posiciones variables, no logo fijo
    marca_pos = random.choice([
        (x, random.randint(60, 130)),
        (random.randint(55, 140), random.randint(60, 150)),
        (random.randint(600, 760), random.randint(70, 150))
    ])
    d.text(marca_pos, marca[:28], font=f_marca, fill=principal)

    # Texto principal
    y_actual = y
    for l in lineas(gancho, f_gancho, max_w)[:3]:
        d.text((x, y_actual), l, font=f_gancho, fill=texto_color)
        y_actual += random.randint(78, 108)

    y_actual += random.randint(8, 25)
    for l in lineas(subtitulo, f_sub, max_w)[:3]:
        d.text((x, y_actual), l, font=f_sub, fill=secundario)
        y_actual += random.randint(42, 55)

    if cta:
        cta_y = min(y_actual + 35, 1220)
        cta_w = min(520, max(300, len(cta) * 18))
        d.rounded_rectangle(
            (x, cta_y, x + cta_w, cta_y + 72),
            radius=24,
            fill=principal
        )
        d.text((x + 28, cta_y + 18), cta.upper()[:30], font=f_cta, fill=fondo)

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
