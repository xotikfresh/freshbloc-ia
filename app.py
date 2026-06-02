import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from groq import Groq
import os, json, io
from datetime import datetime

st.set_page_config(page_title="CM IA", page_icon="⚡", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

DATA_DIR = "data"
PROFILE_PATH = os.path.join(DATA_DIR, "perfil_negocio.json")
HISTORY_PATH = os.path.join(DATA_DIR, "historial.json")
os.makedirs(DATA_DIR, exist_ok=True)

ANCHO, ALTO = 1080, 1350

st.markdown("""
<style>
.stApp {background:#08080A;color:white;}
.block-container {max-width:1350px;padding:1.2rem;}
h1,h2,h3,p,label,span {color:white!important;}
.stTextInput input,.stTextArea textarea {
 background:#111!important;color:white!important;border:1px solid #444!important;
 border-radius:14px!important;font-size:17px!important;
}
.stButton>button,.stDownloadButton>button {
 background:#ffffff;color:#08080A;border:none;border-radius:14px;
 font-weight:900;padding:0.9rem 1.2rem;width:100%;
}
.card {
 background:#111;border:1px solid #2b2b2b;border-radius:18px;
 padding:18px;margin-bottom:14px;
}
.good {border-color:#2f8f46;}
.warn {border-color:#9c7a21;}
</style>
""", unsafe_allow_html=True)


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fuente(tam, bold=True):
    opciones = [
        "assets/Montserrat-Bold.ttf" if bold else "assets/Montserrat-Regular.ttf",
        "assets/Montserrat-Bold.ttf",
        "arialbd.ttf",
        "arial.ttf"
    ]
    for f in opciones:
        try:
            return ImageFont.truetype(f, tam)
        except Exception:
            pass
    return ImageFont.load_default()


def recortar(img, w_final, h_final):
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    r_obj = w_final / h_final
    r = w / h

    if r > r_obj:
        nw = int(h * r_obj)
        x = (w - nw) // 2
        img = img.crop((x, 0, x + nw, h))
    else:
        nh = int(w / r_obj)
        y = (h - nh) // 2
        img = img.crop((0, y, w, y + nh))

    return img.resize((w_final, h_final))


def wrap(texto, font, max_w):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    palabras = str(texto or "").split()
    lineas, actual = [], ""

    for p in palabras:
        prueba = actual + " " + p if actual else p
        if d.textbbox((0, 0), prueba, font=font)[2] <= max_w:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p

    if actual:
        lineas.append(actual)

    return lineas


def generar_con_ia(perfil, descripcion, tipo, historial):
    prompt = f"""
Eres un community manager profesional para negocios pequeños de Chile.

No eres diseñador de Canva. Eres un CM que decide qué comunicar, cuándo publicarlo y cómo decirlo.

Devuelve SOLO JSON válido.

Formato:
{{
  "titulo_post":"",
  "gancho_visual":"",
  "subtitulo_visual":"",
  "caption_instagram":"",
  "historia_instagram":"",
  "mensaje_whatsapp":"",
  "hashtags":[],
  "dia_recomendado":"",
  "hora_recomendada":"",
  "motivo_horario":"",
  "recordatorio_whatsapp":"",
  "idea_foto":"",
  "tipo_contenido_siguiente":""
}}

Perfil del negocio:
{json.dumps(perfil, ensure_ascii=False)}

Tipo de publicación actual:
{tipo}

El usuario quiere comunicar:
{descripcion}

Historial reciente:
{json.dumps(historial[-8:], ensure_ascii=False)}

Reglas:
- No inventes precios, fechas, stock ni dirección.
- Usa solo los datos entregados.
- Si hay precio en el texto, úsalo.
- Gancho visual máximo 4 palabras.
- Subtítulo visual máximo 12 palabras.
- Caption humano, vendedor y breve.
- Historia Instagram muy corta.
- WhatsApp directo, natural y útil.
- Hashtags con #, máximo 8.
- Recomienda día y hora según el perfil.
- Crea un recordatorio tipo: "Hoy a las 18:00 sube..."
- Evita repetir ideas del historial.
- Habla como CM real, no como robot.
"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.45,
        response_format={"type": "json_object"}
    )

    data = json.loads(r.choices[0].message.content)

    if not isinstance(data.get("hashtags"), list):
        data["hashtags"] = ["#NegocioLocal", "#Chile"]

    data["hashtags"] = [
        h if str(h).startswith("#") else "#" + str(h).replace(" ", "")
        for h in data["hashtags"]
    ]

    return data


def crear_imagen_simple(perfil, data, foto=None):
    rubro = perfil.get("rubro", "").lower()

    if "comida" in rubro or "delivery" in rubro or "restaurante" in rubro:
        fondo = (18, 12, 8)
        acento = (245, 155, 30)
    elif "barber" in rubro:
        fondo = (12, 12, 12)
        acento = (210, 170, 90)
    elif "belleza" in rubro or "uñas" in rubro:
        fondo = (245, 235, 238)
        acento = (150, 90, 120)
    elif "ropa" in rubro:
        fondo = (235, 235, 230)
        acento = (20, 20, 20)
    else:
        fondo = (14, 14, 16)
        acento = (240, 240, 240)

    texto = (245, 245, 245) if sum(fondo) < 380 else (15, 15, 15)

    img = Image.new("RGB", (ANCHO, ALTO), fondo)
    d = ImageDraw.Draw(img)

    if foto:
        foto_base = Image.open(foto)
        bg = recortar(foto_base, ANCHO, ALTO).filter(ImageFilter.GaussianBlur(28))
        bg = Image.blend(bg, Image.new("RGB", (ANCHO, ALTO), fondo), 0.55)
        img.paste(bg, (0, 0))

        principal = recortar(foto_base, 860, 720)
        img.paste(principal, (110, 120))

        overlay = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle((0, 760, ANCHO, ALTO), fill=(0, 0, 0, 190))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        d = ImageDraw.Draw(img)
        texto = (245, 245, 245)
        y = 825
    else:
        d.rectangle((70, 90, 1010, 1260), outline=acento, width=8)
        d.ellipse((720, -160, 1240, 360), fill=acento)
        y = 470

    f_negocio = fuente(44)
    f_gancho = fuente(96)
    f_sub = fuente(44, False)
    f_cta = fuente(34)

    negocio = perfil.get("nombre", "NEGOCIO").upper()
    gancho = data.get("gancho_visual", "").upper()
    subtitulo = data.get("subtitulo_visual", "")
    cta = "PUBLICAR HOY"

    d.text((80, 60), negocio[:28], font=f_negocio, fill=acento)

    for linea in wrap(gancho, f_gancho, 900)[:3]:
        d.text((80, y), linea, font=f_gancho, fill=texto)
        y += 100

    y += 10
    for linea in wrap(subtitulo, f_sub, 900)[:3]:
        d.text((80, y), linea, font=f_sub, fill=(220, 220, 220) if sum(texto) > 400 else (55, 55, 55))
        y += 54

    d.rounded_rectangle((80, 1180, 430, 1250), radius=28, fill=acento)
    d.text((112, 1198), cta, font=f_cta, fill=fondo)

    return img


perfil_default = {
    "nombre": "",
    "rubro": "Barbería",
    "tono": "Cercano",
    "publico": "",
    "productos": "",
    "dias_publicacion": "Lunes, miércoles y viernes",
    "horario_preferido": "19:00",
    "whatsapp": ""
}

perfil = load_json(PROFILE_PATH, perfil_default)
historial = load_json(HISTORY_PATH, [])

st.markdown("<h1>CM IA para negocios</h1>", unsafe_allow_html=True)
st.write("La app que te dice qué publicar, cuándo publicarlo y te deja el contenido listo.")

tab1, tab2, tab3 = st.tabs(["Crear publicación", "Perfil del negocio", "Calendario / historial"])

with tab2:
    st.markdown("## Perfil único del negocio")

    c1, c2 = st.columns(2)

    with c1:
        perfil["nombre"] = st.text_input("Nombre del negocio", value=perfil.get("nombre", ""))
        perfil["rubro"] = st.selectbox(
            "Rubro",
            ["Barbería", "Restaurante / comida", "Delivery", "Cafetería", "Tienda de ropa", "Gimnasio", "Belleza / uñas", "Minimarket", "Otro"],
            index=["Barbería", "Restaurante / comida", "Delivery", "Cafetería", "Tienda de ropa", "Gimnasio", "Belleza / uñas", "Minimarket", "Otro"].index(perfil.get("rubro", "Barbería")) if perfil.get("rubro", "Barbería") in ["Barbería", "Restaurante / comida", "Delivery", "Cafetería", "Tienda de ropa", "Gimnasio", "Belleza / uñas", "Minimarket", "Otro"] else 0
        )
        perfil["tono"] = st.selectbox(
            "Tono de marca",
            ["Cercano", "Juvenil", "Profesional", "Premium", "Divertido", "Urgente / venta rápida"],
            index=["Cercano", "Juvenil", "Profesional", "Premium", "Divertido", "Urgente / venta rápida"].index(perfil.get("tono", "Cercano")) if perfil.get("tono", "Cercano") in ["Cercano", "Juvenil", "Profesional", "Premium", "Divertido", "Urgente / venta rápida"] else 0
        )

    with c2:
        perfil["publico"] = st.text_input("Público objetivo", value=perfil.get("publico", ""), placeholder="Ej: hombres 18-35 de Viña")
        perfil["productos"] = st.text_area("Qué vende / servicios principales", value=perfil.get("productos", ""), height=100)
        perfil["dias_publicacion"] = st.text_input("Días ideales para publicar", value=perfil.get("dias_publicacion", "Lunes, miércoles y viernes"))
        perfil["horario_preferido"] = st.text_input("Horario preferido", value=perfil.get("horario_preferido", "19:00"))
        perfil["whatsapp"] = st.text_input("WhatsApp del negocio opcional", value=perfil.get("whatsapp", ""))

    if st.button("GUARDAR PERFIL"):
        save_json(PROFILE_PATH, perfil)
        st.success("Perfil guardado. Ahora la IA usará esta información siempre.")

with tab1:
    izq, der = st.columns([0.9, 1.1], gap="large")

    with izq:
        st.markdown("## Crear publicación")

        st.markdown(f"""
        <div class="card good">
        <b>Negocio:</b> {perfil.get("nombre") or "Sin nombre"}<br>
        <b>Rubro:</b> {perfil.get("rubro")}<br>
        <b>Tono:</b> {perfil.get("tono")}<br>
        <b>Días:</b> {perfil.get("dias_publicacion")} · {perfil.get("horario_preferido")}
        </div>
        """, unsafe_allow_html=True)

        tipo = st.selectbox("Tipo de publicación", ["Promoción", "Producto", "Evento", "Testimonio", "Informativo", "Recordatorio", "Sorteo"])
        descripcion = st.text_area("Qué quieres comunicar", height=150, placeholder="Ej: Para las primeras 40 personas, completos a $1500 por delivery.")
        foto = st.file_uploader("Sube foto del producto/local/persona", type=["jpg", "jpeg", "png", "webp"])
        generar = st.button("GENERAR POST + CALENDARIO")

    with der:
        st.markdown("## Resultado")

        if generar:
            if not perfil.get("nombre"):
                st.error("Primero guarda el perfil del negocio.")
            elif not descripcion.strip():
                st.error("Escribe qué quieres comunicar.")
            else:
                with st.spinner("El CM IA está pensando la publicación..."):
                    data = generar_con_ia(perfil, descripcion, tipo, historial)
                    post = crear_imagen_simple(perfil, data, foto)

                    buffer = io.BytesIO()
                    post.save(buffer, format="PNG")
                    buffer.seek(0)

                    st.session_state["post_buffer"] = buffer.getvalue()
                    st.session_state["data"] = data

                    historial.append({
                        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tipo": tipo,
                        "descripcion": descripcion,
                        "dia_recomendado": data.get("dia_recomendado", ""),
                        "hora_recomendada": data.get("hora_recomendada", ""),
                        "gancho": data.get("gancho_visual", "")
                    })
                    save_json(HISTORY_PATH, historial)

        if "post_buffer" in st.session_state:
            st.image(st.session_state["post_buffer"], use_container_width=True)
            st.download_button(
                "DESCARGAR IMAGEN",
                data=st.session_state["post_buffer"],
                file_name=f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png"
            )

        if "data" in st.session_state:
            data = st.session_state["data"]

            st.markdown("### Caption Instagram")
            st.markdown(f"<div class='card'>{data.get('caption_instagram','')}</div>", unsafe_allow_html=True)

            st.markdown("### Historia Instagram")
            st.markdown(f"<div class='card'>{data.get('historia_instagram','')}</div>", unsafe_allow_html=True)

            st.markdown("### Mensaje WhatsApp")
            st.markdown(f"<div class='card'>{data.get('mensaje_whatsapp','')}</div>", unsafe_allow_html=True)

            st.markdown("### Hashtags")
            st.markdown(f"<div class='card'>{' '.join(data.get('hashtags', []))}</div>", unsafe_allow_html=True)

            st.markdown("### Cuándo publicar")
            st.markdown(f"""
            <div class='card warn'>
            <b>{data.get('dia_recomendado','')}</b> a las <b>{data.get('hora_recomendada','')}</b><br>
            {data.get('motivo_horario','')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### Recordatorio para WhatsApp")
            st.markdown(f"<div class='card'>{data.get('recordatorio_whatsapp','')}</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("## Calendario / historial")

    if not historial:
        st.info("Todavía no hay publicaciones creadas.")
    else:
        for item in reversed(historial[-15:]):
            st.markdown(f"""
            <div class="card">
            <b>{item.get('tipo')}</b> · {item.get('fecha_creacion')}<br>
            <b>Idea:</b> {item.get('descripcion')}<br>
            <b>Publicar:</b> {item.get('dia_recomendado')} {item.get('hora_recomendada')}<br>
            <b>Gancho:</b> {item.get('gancho')}
            </div>
            """, unsafe_allow_html=True)
