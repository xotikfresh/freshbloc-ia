import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from groq import Groq
import os, json, io, random
from datetime import datetime

st.set_page_config(page_title="Community Manager Virtual", page_icon="💜", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

DATA_DIR = "data"
PROFILE_PATH = os.path.join(DATA_DIR, "perfil_negocio.json")
HISTORY_PATH = os.path.join(DATA_DIR, "historial.json")
os.makedirs(DATA_DIR, exist_ok=True)

ANCHO, ALTO = 1080, 1080
MORADO = (145, 60, 255)

st.markdown("""
<style>
.stApp {background:linear-gradient(180deg,#ffffff,#f7f2ff); color:#15151a;}
.block-container {max-width:1350px; padding:1.5rem 2rem;}
h1,h2,h3,p,label,span {color:#15151a!important;}
.hero {background:linear-gradient(135deg,#ffffff,#efe3ff);border:1px solid #dccbff;border-radius:28px;padding:30px;margin-bottom:22px;}
.card {background:#fff;border:1px solid #e3d7ff;border-radius:22px;padding:20px;margin-bottom:16px;box-shadow:0 8px 24px rgba(90,50,150,.08);}
.purple {background:linear-gradient(135deg,#913CFF,#5f1ed6);color:white!important;border-radius:22px;padding:22px;margin-bottom:16px;}
.purple * {color:white!important;}
.stTextInput input,.stTextArea textarea {background:#fff!important;color:#15151a!important;border:1px solid #cdb8ff!important;border-radius:14px!important;font-size:17px!important;}
.stSelectbox div[data-baseweb="select"] > div {background:#fff!important;border:1px solid #cdb8ff!important;border-radius:14px!important;}
.stButton>button,.stDownloadButton>button {background:#913CFF!important;color:white!important;border:none!important;border-radius:16px!important;font-weight:900!important;padding:.9rem 1.2rem!important;}
[data-testid="stFileUploader"] {background:#fff;border:1px dashed #b894ff;border-radius:18px;padding:14px;}
.small {color:#555!important;font-size:15px;}
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
    for f in ["assets/Montserrat-Bold.ttf" if bold else "assets/Montserrat-Regular.ttf", "assets/Montserrat-Bold.ttf", "arialbd.ttf", "arial.ttf"]:
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

def generar_con_ia(perfil, descripcion, objetivo, historial):
    prompt = f"""
Eres un community manager profesional para negocios pequeños de Chile.

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
  "tipo_contenido_siguiente":"",
  "direccion_visual":{{
    "estilo_visual":"",
    "tipo_layout":"",
    "posicion_texto":"",
    "foto_ideal":"",
    "colores_recomendados":"",
    "texto_en_imagen":"",
    "que_evitar":""
  }}
}}

Perfil:
{json.dumps(perfil, ensure_ascii=False)}

Objetivo de publicación:
{objetivo}

Quiere comunicar:
{descripcion}

Historial reciente:
{json.dumps(historial[-8:], ensure_ascii=False)}

Reglas:
- No inventes precios, fechas, stock, descuentos, eventos ni dirección.
- Si el usuario da precio o fecha, úsalo.
- Usa solo servicios y material disponible del perfil.
- Gancho visual máximo 4 palabras, comercial y directo.
- Subtítulo visual máximo 8 palabras.
- El texto visual debe salir de lo que el usuario comunicó, no de una interpretación inventada.
- Si el usuario da producto, precio, horario o promoción, prioriza eso en gancho_visual.
- No inventes nombres creativos para productos.
- No escribas frases largas en el texto visual.
- No uses el nombre del negocio como gancho visual.
- No pongas el nombre del negocio dentro del texto de la imagen.
- Si la foto subida no sirve, dilo en idea_foto y sugiere una alternativa fácil.
- No recomiendes antes/después, testimonios o clientes si el perfil no dice que tiene ese material.
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
    data["hashtags"] = [h if str(h).startswith("#") else "#" + str(h).replace(" ", "") for h in data["hashtags"]]
    return data

def generar_plan_semanal(perfil, historial):
    prompt = f"""
Eres community manager para negocios pequeños de Chile.

Devuelve SOLO JSON válido.

Formato:
{{
 "resumen":"",
 "plan":[{{"dia":"","hora":"","tipo":"","idea":"","objetivo":""}}],
 "recomendacion_general":""
}}

Perfil:
{json.dumps(perfil, ensure_ascii=False)}

Historial:
{json.dumps(historial[-8:], ensure_ascii=False)}

Reglas:
- 4 publicaciones máximo.
- No inventes descuentos, eventos, rifas, testimonios, antes/después, fotos de clientes ni disponibilidad si el perfil no lo menciona.
- Usa solamente servicios reales del perfil.
- Usa solamente el material disponible indicado en el perfil.
- Ideas concretas y realizables para un dueño ocupado.
- Si no hay material visual específico, propone contenido fácil: servicio destacado, recordatorio de reservas, horario, beneficios, preguntas frecuentes o promoción simple.
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        response_format={"type": "json_object"}
    )
    return json.loads(r.choices[0].message.content)



def crear_imagen_base(perfil, data, foto=None, variante=0):
    rubro = perfil.get("rubro", "").lower()

    if "barber" in rubro:
        fondo, acento = (16, 16, 18), (210, 170, 90)
    elif "cafeter" in rubro or "comida" in rubro or "delivery" in rubro or "restaurante" in rubro:
        fondo, acento = (255, 248, 236), (190, 105, 35)
    elif "belleza" in rubro or "uñas" in rubro:
        fondo, acento = (252, 240, 246), (150, 80, 120)
    else:
        fondo, acento = (248, 245, 255), MORADO

    img = Image.new("RGB", (ANCHO, ALTO), fondo)
    d = ImageDraw.Draw(img)

    gancho = data.get("gancho_visual", "").upper().strip()
    subtitulo = data.get("subtitulo_visual", "").strip()

    if len(gancho) > 34:
        gancho = gancho[:34].strip()

    f_gancho = fuente(82, True)
    f_sub = fuente(38, True)

    layout = variante % 4

    if foto:
        foto_base = Image.open(foto)

        if layout == 0:
            # Foto arriba grande + bloque inferior
            main = recortar(foto_base, 1080, 700)
            img.paste(main, (0, 0))
            d.rectangle((0, 690, 1080, 1080), fill=fondo)
            x, y = 70, 760
            text_color = (20,20,24) if sum(fondo) > 450 else (250,250,250)
            sub_color = (70,70,75) if sum(fondo) > 450 else (225,225,225)

        elif layout == 1:
            # Foto completa + franja oscura inferior
            main = recortar(foto_base, 1080, 1080)
            img.paste(main, (0, 0))
            overlay = Image.new("RGBA", (1080,1080), (0,0,0,0))
            od = ImageDraw.Draw(overlay)
            od.rectangle((0, 650, 1080, 1080), fill=(0,0,0,210))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            d = ImageDraw.Draw(img)
            x, y = 70, 735
            text_color = (255,255,255)
            sub_color = (225,225,225)

        elif layout == 2:
            # Fondo claro, foto circular/rounded centrada
            d.rectangle((0, 0, 1080, 1080), fill=fondo)
            main = recortar(foto_base, 850, 620)
            mask = Image.new("L", (850,620), 0)
            md = ImageDraw.Draw(mask)
            md.rounded_rectangle((0,0,850,620), radius=45, fill=255)
            img.paste(main, (115, 90), mask)
            x, y = 90, 760
            text_color = (20,20,24) if sum(fondo) > 450 else (250,250,250)
            sub_color = (70,70,75) if sum(fondo) > 450 else (225,225,225)

        else:
            # Split editorial
            d.rectangle((0, 0, 1080, 1080), fill=fondo)
            main = recortar(foto_base, 540, 1080)
            img.paste(main, (540, 0))
            x, y = 65, 330
            text_color = (20,20,24) if sum(fondo) > 450 else (250,250,250)
            sub_color = (70,70,75) if sum(fondo) > 450 else (225,225,225)

    else:
        d.rounded_rectangle((55,55,1025,1025), radius=42, outline=acento, width=8)
        x, y = 85, 390
        text_color = (20,20,24)
        sub_color = (70,70,75)

    # Texto limpio, sin nombre del negocio ni botón
    for l in wrap(gancho, f_gancho, 900 if layout != 3 else 430)[:2]:
        d.text((x, y), l, font=f_gancho, fill=text_color)
        y += 88

    y += 10

    for l in wrap(subtitulo, f_sub, 880 if layout != 3 else 430)[:2]:
        d.text((x, y), l, font=f_sub, fill=sub_color)
        y += 44

    # Línea/acento visual discreto
    d.rounded_rectangle((x, min(y + 28, 1015), x + 180, min(y + 40, 1027)), radius=8, fill=acento)

    return img


perfil_default = {
    "nombre": "",
    "rubro": "Barbería",
    "tono": "Cercano",
    "publico": "",
    "productos": "",
    "material_disponible": "",
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

tab_inicio, tab_crear, tab_perfil, tab_historial = st.tabs(["Inicio", "Crear publicación", "Perfil del negocio", "Calendario / historial"])

with tab_inicio:
    st.markdown("## Panel principal")
    if perfil.get("nombre"):
        st.markdown(f"<div class='purple'><h3>{perfil['nombre']}</h3><p>{perfil['rubro']} · tono {perfil['tono']}</p><p>{perfil['dias_publicacion']} · {perfil['horario_preferido']}</p></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='purple'><h3>Completa primero el perfil del negocio</h3><p>Así el sistema trabajará personalizado.</p></div>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><h3>Próxima publicación</h3><p>{perfil.get('dias_publicacion')}<br><b>{perfil.get('horario_preferido')}</b></p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><h3>Publicaciones creadas</h3><p><b>{len(historial)}</b> publicaciones guardadas</p></div>", unsafe_allow_html=True)
    with c3:
        ultima = historial[-1]["gancho"] if historial else "Aún no hay contenido"
        st.markdown(f"<div class='card'><h3>Última idea</h3><p>{ultima}</p></div>", unsafe_allow_html=True)

    st.markdown("## Plan semanal")
    if st.button("GENERAR PLAN SEMANAL"):
        if not perfil.get("nombre"):
            st.error("Primero guarda el perfil.")
        else:
            with st.spinner("Preparando plan semanal..."):
                st.session_state["plan"] = generar_plan_semanal(perfil, historial)

    if "plan" in st.session_state:
        plan = st.session_state["plan"]
        st.markdown(f"<div class='purple'><b>{plan.get('resumen','')}</b><br>{plan.get('recomendacion_general','')}</div>", unsafe_allow_html=True)
        for item in plan.get("plan", []):
            st.markdown(f"<div class='card'><b>{item.get('dia')} · {item.get('hora')}</b><br><b>{item.get('tipo')}</b>: {item.get('idea')}<br><span class='small'>{item.get('objetivo')}</span></div>", unsafe_allow_html=True)

with tab_crear:
    izq, der = st.columns([0.9,1.1], gap="large")

    with izq:
        st.markdown("## Crear publicación")
        st.markdown(f"<div class='card'><b>Negocio:</b> {perfil.get('nombre') or 'Sin nombre'}<br><b>Rubro:</b> {perfil.get('rubro')}<br><b>Tono:</b> {perfil.get('tono')}<br><b>Días:</b> {perfil.get('dias_publicacion')} · {perfil.get('horario_preferido')}</div>", unsafe_allow_html=True)

        objetivo = st.selectbox("Objetivo de la publicación", [
            "Vender una promoción",
            "Mostrar un producto o servicio",
            "Avisar horario o disponibilidad",
            "Recordar que pueden reservar",
            "Llenar horas disponibles",
            "Anunciar algo nuevo",
            "Educar al cliente",
            "Hacer una historia interactiva",
            "Crear confianza",
            "Otro"
        ])

        descripcion = st.text_area("Qué quieres comunicar", height=150, placeholder="Ej: Cortes a $5000 solo por esta tarde.")
        foto = st.file_uploader("Sube foto del producto/local/persona", type=["jpg","jpeg","png","webp"])
        generar = st.button("GENERAR PUBLICACIÓN")

    with der:
        st.markdown("## Resultado")
        if generar:
            if not perfil.get("nombre"):
                st.error("Primero guarda el perfil del negocio.")
            elif not descripcion.strip():
                st.error("Escribe qué quieres comunicar.")
            else:
                with st.spinner("Tu Community Manager Virtual está preparando la publicación..."):
                    data = generar_con_ia(perfil, descripcion, objetivo, historial)
                    st.session_state['design_variant'] = 0
                    st.session_state['last_foto'] = foto
                    post = crear_imagen_base(perfil, data, foto, st.session_state['design_variant'])

                    buffer = io.BytesIO()
                    post.save(buffer, format="PNG")
                    buffer.seek(0)

                    st.session_state["post_buffer"] = buffer.getvalue()
                    st.session_state["data"] = data

                    historial.append({
                        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tipo": objetivo,
                        "descripcion": descripcion,
                        "dia_recomendado": data.get("dia_recomendado",""),
                        "hora_recomendada": data.get("hora_recomendada",""),
                        "gancho": data.get("gancho_visual","")
                    })
                    save_json(HISTORY_PATH, historial)

        if "post_buffer" in st.session_state:
            if st.button("REHACER DISEÑO"):
                st.session_state["design_variant"] = st.session_state.get("design_variant", 0) + 1
                post = crear_imagen_base(
                    perfil,
                    st.session_state["data"],
                    st.session_state.get("last_foto"),
                    st.session_state["design_variant"]
                )
                buffer = io.BytesIO()
                post.save(buffer, format="PNG")
                buffer.seek(0)
                st.session_state["post_buffer"] = buffer.getvalue()

            st.image(st.session_state["post_buffer"], use_container_width=True)
            st.download_button("DESCARGAR IMAGEN", data=st.session_state["post_buffer"], file_name=f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png", mime="image/png")

        if "data" in st.session_state:
            data = st.session_state["data"]
            visual = data.get("direccion_visual", {})

            st.markdown("### Caption Instagram")
            st.markdown(f"<div class='card'>{data.get('caption_instagram','')}</div>", unsafe_allow_html=True)

            st.markdown("### Historia Instagram")
            st.markdown(f"<div class='card'>{data.get('historia_instagram','')}</div>", unsafe_allow_html=True)

            st.markdown("### WhatsApp")
            st.markdown(f"<div class='card'>{data.get('mensaje_whatsapp','')}</div>", unsafe_allow_html=True)

            st.markdown("### Dirección visual del CM")
            st.markdown(f"""
            <div class="purple">
            <b>Foto ideal:</b> {visual.get('foto_ideal','')}<br>
            <b>Layout:</b> {visual.get('tipo_layout','')}<br>
            <b>Texto:</b> {visual.get('texto_en_imagen','')}<br>
            <b>Evitar:</b> {visual.get('que_evitar','')}<br>
            <b>Idea foto:</b> {data.get('idea_foto','')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### Cuándo publicar")
            st.markdown(f"<div class='card'><b>{data.get('dia_recomendado','')}</b> a las <b>{data.get('hora_recomendada','')}</b><br>{data.get('motivo_horario','')}</div>", unsafe_allow_html=True)

            st.markdown("### Recordatorio WhatsApp")
            st.markdown(f"<div class='card'>{data.get('recordatorio_whatsapp','')}</div>", unsafe_allow_html=True)

            st.markdown("### Hashtags")
            st.markdown(f"<div class='card'>{' '.join(data.get('hashtags', []))}</div>", unsafe_allow_html=True)

with tab_perfil:
    st.markdown("## Perfil único del negocio")
    c1,c2 = st.columns(2)
    with c1:
        perfil["nombre"] = st.text_input("Nombre del negocio", value=perfil.get("nombre",""))
        rubros = ["Barbería","Restaurante / comida","Delivery","Cafetería","Tienda de ropa","Gimnasio","Belleza / uñas","Minimarket","Otro"]
        perfil["rubro"] = st.selectbox("Rubro", rubros, index=rubros.index(perfil.get("rubro","Barbería")) if perfil.get("rubro","Barbería") in rubros else 0)
        tonos = ["Cercano","Juvenil","Profesional","Premium","Divertido","Urgente / venta rápida"]
        perfil["tono"] = st.selectbox("Tono de marca", tonos, index=tonos.index(perfil.get("tono","Cercano")) if perfil.get("tono","Cercano") in tonos else 0)
    with c2:
        perfil["publico"] = st.text_input("Público objetivo", value=perfil.get("publico",""), placeholder="Ej: hombres 18-35 de Viña")
        perfil["productos"] = st.text_area("Qué vende / servicios principales", value=perfil.get("productos",""), height=90)
        perfil["material_disponible"] = st.text_area("Qué material tiene para publicar", value=perfil.get("material_disponible",""), height=90, placeholder="Ej: fotos del local, fotos de cortes terminados, videos cortos, fotos de productos, no tenemos antes y después")
        perfil["dias_publicacion"] = st.text_input("Días ideales para publicar", value=perfil.get("dias_publicacion","Lunes, miércoles y viernes"))
        perfil["horario_preferido"] = st.text_input("Horario preferido", value=perfil.get("horario_preferido","19:00"))
        perfil["whatsapp"] = st.text_input("WhatsApp del negocio opcional", value=perfil.get("whatsapp",""))
    if st.button("GUARDAR PERFIL"):
        save_json(PROFILE_PATH, perfil)
        st.success("Perfil guardado.")

with tab_historial:
    st.markdown("## Calendario / historial")
    if not historial:
        st.info("Todavía no hay publicaciones creadas.")
    else:
        for item in reversed(historial[-20:]):
            st.markdown(f"<div class='card'><b>{item.get('tipo')}</b> · {item.get('fecha_creacion')}<br><b>Idea:</b> {item.get('descripcion')}<br><b>Publicar:</b> {item.get('dia_recomendado')} {item.get('hora_recomendada')}<br><b>Gancho:</b> {item.get('gancho')}</div>", unsafe_allow_html=True)
