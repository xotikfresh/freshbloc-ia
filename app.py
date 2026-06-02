import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from groq import Groq
import os, json, io
from datetime import datetime

st.set_page_config(page_title="Community Manager Virtual", page_icon="💜", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

DATA_DIR = "data"
PROFILE_PATH = os.path.join(DATA_DIR, "perfil_negocio.json")
HISTORY_PATH = os.path.join(DATA_DIR, "historial.json")
os.makedirs(DATA_DIR, exist_ok=True)

ANCHO, ALTO = 1080, 1350
MORADO = (145, 60, 255)
NEGRO = (20, 20, 24)
BLANCO = (250, 250, 252)


st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg,#ffffff,#f7f3ff);
    color:#18181b;
}
.block-container {
    max-width:1350px;
    padding:1.5rem 2rem;
}
h1,h2,h3,p,label,span {
    color:#18181b!important;
}
.hero {
    background: linear-gradient(135deg,#ffffff,#efe4ff);
    border:1px solid #ded0ff;
    border-radius:28px;
    padding:28px;
    margin-bottom:22px;
}
.card {
    background:#ffffff;
    border:1px solid #e6ddff;
    border-radius:22px;
    padding:20px;
    margin-bottom:16px;
    box-shadow:0 8px 22px rgba(80,40,140,.08);
}
.card-purple {
    background:linear-gradient(135deg,#913CFF,#5f1ed6);
    color:white!important;
    border-radius:22px;
    padding:20px;
    margin-bottom:16px;
    box-shadow:0 10px 26px rgba(145,60,255,.25);
}
.card-purple * {
    color:white!important;
}
.stTextInput input,.stTextArea textarea {
    background:#ffffff!important;
    color:#18181b!important;
    border:1px solid #cdb8ff!important;
    border-radius:14px!important;
    font-size:17px!important;
}
.stSelectbox div[data-baseweb="select"] > div {
    background:#ffffff!important;
    border:1px solid #cdb8ff!important;
    border-radius:14px!important;
}
.stButton>button,.stDownloadButton>button {
    background:#913CFF!important;
    color:white!important;
    border:none!important;
    border-radius:16px!important;
    font-weight:900!important;
    padding:0.9rem 1.2rem!important;
    width:100%!important;
    font-size:16px!important;
}
[data-testid="stFileUploader"] {
    background:#ffffff;
    border:1px dashed #b894ff;
    border-radius:18px;
    padding:14px;
}
.small {
    color:#555!important;
    font-size:15px;
}
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

Tu trabajo es decir qué publicar, cómo comunicarlo, cuándo publicarlo y dejar el contenido listo.

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
- Si el usuario escribe precio o fecha, úsalo.
- Gancho visual máximo 4 palabras.
- Subtítulo visual máximo 12 palabras.
- Caption humano, vendedor y breve.
- Historia Instagram muy corta.
- WhatsApp directo, natural y útil.
- Hashtags con #, máximo 8.
- Recomienda día y hora según el perfil.
- Evita repetir ideas del historial.
- Habla como community manager real.
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


def generar_plan_semanal(perfil, historial):
    prompt = f"""
Eres un community manager para negocios pequeños de Chile.

Crea un plan semanal simple y útil para este negocio.

Devuelve SOLO JSON válido.

Formato:
{{
 "resumen":"",
 "plan":[
   {{"dia":"","hora":"","tipo":"","idea":"","objetivo":""}}
 ],
 "recomendacion_general":""
}}

Perfil del negocio:
{json.dumps(perfil, ensure_ascii=False)}

Historial reciente:
{json.dumps(historial[-8:], ensure_ascii=False)}

Reglas:
- 4 publicaciones máximo.
- Evita repetir ideas del historial.
- Usa días y horario preferido del negocio.
- Ideas concretas, no genéricas.
- Habla como community manager real.
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.45,
        response_format={"type": "json_object"}
    )
    return json.loads(r.choices[0].message.content)


def crear_imagen_simple(perfil, data, foto=None):
    rubro = perfil.get("rubro", "").lower()

    if "comida" in rubro or "delivery" in rubro or "restaurante" in rubro:
        fondo = (25, 18, 12)
        acento = (245, 140, 35)
    elif "barber" in rubro:
        fondo = (18, 18, 20)
        acento = (205, 168, 90)
    elif "belleza" in rubro or "uñas" in rubro:
        fondo = (250, 236, 242)
        acento = (150, 80, 120)
    elif "ropa" in rubro:
        fondo = (245, 245, 242)
        acento = (20, 20, 20)
    else:
        fondo = (24, 20, 32)
        acento = MORADO

    texto = (245, 245, 245) if sum(fondo) < 390 else (18, 18, 20)

    img = Image.new("RGB", (ANCHO, ALTO), fondo)
    d = ImageDraw.Draw(img)

    if foto:
        foto_base = Image.open(foto)
        bg = recortar(foto_base, ANCHO, ALTO).filter(ImageFilter.GaussianBlur(30))
        bg = Image.blend(bg, Image.new("RGB", (ANCHO, ALTO), fondo), 0.55)
        img.paste(bg, (0, 0))

        principal = recortar(foto_base, 880, 720)
        img.paste(principal, (100, 120))

        overlay = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle((0, 760, ANCHO, ALTO), fill=(0, 0, 0, 190))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        d = ImageDraw.Draw(img)
        texto = (245, 245, 245)
        y = 835
    else:
        d.rounded_rectangle((70, 90, 1010, 1260), radius=40, outline=acento, width=8)
        d.ellipse((720, -160, 1240, 360), fill=acento)
        y = 470

    f_negocio = fuente(42)
    f_gancho = fuente(92)
    f_sub = fuente(42, False)
    f_cta = fuente(32)

    negocio = perfil.get("nombre", "NEGOCIO").upper()
    gancho = data.get("gancho_visual", "").upper()
    subtitulo = data.get("subtitulo_visual", "")
    cta = "PUBLICAR HOY"

    d.text((80, 60), negocio[:28], font=f_negocio, fill=acento)

    for linea in wrap(gancho, f_gancho, 900)[:3]:
        d.text((80, y), linea, font=f_gancho, fill=texto)
        y += 96

    y += 10
    sub_color = (220, 220, 220) if sum(texto) > 400 else (55, 55, 55)
    for linea in wrap(subtitulo, f_sub, 900)[:3]:
        d.text((80, y), linea, font=f_sub, fill=sub_color)
        y += 52

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

st.markdown("""
<div class="hero">
<h1>Community Manager Virtual</h1>
<p class="small">Te dice qué publicar, cuándo publicarlo y te deja el contenido listo.</p>
</div>
""", unsafe_allow_html=True)

tab_inicio, tab_crear, tab_perfil, tab_historial = st.tabs([
    "Inicio",
    "Crear publicación",
    "Perfil del negocio",
    "Calendario / historial"
])


with tab_inicio:
    st.markdown("## Panel principal")

    if not perfil.get("nombre"):
        st.markdown("""
        <div class="card-purple">
        <h3>Completa primero el perfil del negocio</h3>
        <p>Así el Community Manager Virtual podrá trabajar con el tono, horarios y servicios reales de la empresa.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="card-purple">
        <h3>{perfil.get("nombre")}</h3>
        <p>{perfil.get("rubro")} · tono {perfil.get("tono")}</p>
        <p>Publica idealmente: {perfil.get("dias_publicacion")} · {perfil.get("horario_preferido")}</p>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="card">
        <h3>Próxima publicación</h3>
        <p>{perfil.get("dias_publicacion")}<br><b>{perfil.get("horario_preferido")}</b></p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
        <h3>Publicaciones creadas</h3>
        <p><b>{len(historial)}</b> publicaciones guardadas</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        ultima = historial[-1]["gancho"] if historial else "Aún no hay contenido"
        st.markdown(f"""
        <div class="card">
        <h3>Última idea</h3>
        <p>{ultima}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("## Plan semanal")

    if st.button("GENERAR PLAN SEMANAL"):
        if not perfil.get("nombre"):
            st.error("Primero guarda el perfil del negocio.")
        else:
            with st.spinner("Preparando plan semanal..."):
                st.session_state["plan_semanal"] = generar_plan_semanal(perfil, historial)

    if "plan_semanal" in st.session_state:
        plan = st.session_state["plan_semanal"]
        st.markdown(f"""
        <div class="card-purple">
        <b>{plan.get('resumen','')}</b><br>
        {plan.get('recomendacion_general','')}
        </div>
        """, unsafe_allow_html=True)

        for item in plan.get("plan", []):
            st.markdown(f"""
            <div class="card">
            <b>{item.get('dia','')} · {item.get('hora','')}</b><br>
            <b>{item.get('tipo','')}</b>: {item.get('idea','')}<br>
            <span class="small">{item.get('objetivo','')}</span>
            </div>
            """, unsafe_allow_html=True)


with tab_crear:
    izq, der = st.columns([0.9, 1.1], gap="large")

    with izq:
        st.markdown("## Crear publicación")

        st.markdown(f"""
        <div class="card">
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
                with st.spinner("Tu Community Manager Virtual está preparando la publicación..."):
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
            <div class='card-purple'>
            <b>{data.get('dia_recomendado','')}</b> a las <b>{data.get('hora_recomendada','')}</b><br>
            {data.get('motivo_horario','')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### Recordatorio para WhatsApp")
            st.markdown(f"<div class='card'>{data.get('recordatorio_whatsapp','')}</div>", unsafe_allow_html=True)


with tab_perfil:
    st.markdown("## Perfil único del negocio")

    c1, c2 = st.columns(2)

    with c1:
        perfil["nombre"] = st.text_input("Nombre del negocio", value=perfil.get("nombre", ""))
        rubros = ["Barbería", "Restaurante / comida", "Delivery", "Cafetería", "Tienda de ropa", "Gimnasio", "Belleza / uñas", "Minimarket", "Otro"]
        perfil["rubro"] = st.selectbox("Rubro", rubros, index=rubros.index(perfil.get("rubro", "Barbería")) if perfil.get("rubro", "Barbería") in rubros else 0)

        tonos = ["Cercano", "Juvenil", "Profesional", "Premium", "Divertido", "Urgente / venta rápida"]
        perfil["tono"] = st.selectbox("Tono de marca", tonos, index=tonos.index(perfil.get("tono", "Cercano")) if perfil.get("tono", "Cercano") in tonos else 0)

    with c2:
        perfil["publico"] = st.text_input("Público objetivo", value=perfil.get("publico", ""), placeholder="Ej: hombres 18-35 de Viña")
        perfil["productos"] = st.text_area("Qué vende / servicios principales", value=perfil.get("productos", ""), height=100)
        perfil["dias_publicacion"] = st.text_input("Días ideales para publicar", value=perfil.get("dias_publicacion", "Lunes, miércoles y viernes"))
        perfil["horario_preferido"] = st.text_input("Horario preferido", value=perfil.get("horario_preferido", "19:00"))
        perfil["whatsapp"] = st.text_input("WhatsApp del negocio opcional", value=perfil.get("whatsapp", ""))

    if st.button("GUARDAR PERFIL"):
        save_json(PROFILE_PATH, perfil)
        st.success("Perfil guardado. Ahora el Community Manager Virtual usará esta información siempre.")


with tab_historial:
    st.markdown("## Calendario / historial")

    if not historial:
        st.info("Todavía no hay publicaciones creadas.")
    else:
        for item in reversed(historial[-20:]):
            st.markdown(f"""
            <div class="card">
            <b>{item.get('tipo')}</b> · {item.get('fecha_creacion')}<br>
            <b>Idea:</b> {item.get('descripcion')}<br>
            <b>Publicar:</b> {item.get('dia_recomendado')} {item.get('hora_recomendada')}<br>
            <b>Gancho:</b> {item.get('gancho')}
            </div>
            """, unsafe_allow_html=True)
