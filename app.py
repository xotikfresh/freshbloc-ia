import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from groq import Groq
import os, json, io, random
from datetime import datetime

st.set_page_config(page_title="Dago", page_icon="💜", layout="wide")

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
.hero {
    background:linear-gradient(135deg,#ffffff,#f2eaff);
    border:1px solid #e2d3ff;
    border-radius:26px;
    padding:24px;
    margin-bottom:18px;
}
.hero h1 {
    font-size:42px!important;
    margin-bottom:8px!important;
}
.hero p {
    font-size:17px!important;
}
@media (max-width: 760px) {
    .block-container {padding:1rem!important;}
    .hero h1 {font-size:30px!important;}
    .hero {padding:18px!important;}
    h2 {font-size:26px!important;}
    h3 {font-size:21px!important;}
}
.home-card {
    background:#fff;
    border:1px solid #eadfff;
    border-radius:22px;
    padding:18px;
    box-shadow:0 8px 22px rgba(90,50,150,.07);
}
.home-main {
    background:#fff;
    border:1px solid #e4d7ff;
    border-radius:26px;
    padding:24px;
    margin-bottom:18px;
    box-shadow:0 10px 28px rgba(90,50,150,.08);
}

.card {background:#fff;border:1px solid #e3d7ff;border-radius:22px;padding:20px;margin-bottom:16px;box-shadow:0 8px 24px rgba(90,50,150,.08);}
.purple {background:linear-gradient(135deg,#913CFF,#5f1ed6);color:white!important;border-radius:22px;padding:22px;margin-bottom:16px;}
.purple * {color:white!important;}
.stTextInput input,.stTextArea textarea {background:#fff!important;color:#15151a!important;border:1px solid #cdb8ff!important;border-radius:14px!important;font-size:17px!important;}
.stSelectbox div[data-baseweb="select"] > div {background:#fff!important;border:1px solid #cdb8ff!important;border-radius:14px!important;}
.stButton>button,.stDownloadButton>button {
    background:#913CFF!important;
    color:white!important;
    border:none!important;
    border-radius:16px!important;
    font-weight:900!important;
    padding:.9rem 1.2rem!important;
}
.stButton>button *,.stDownloadButton>button * {
    color:white!important;
}
.idea-card {
    background:#fff;
    border:1px solid #d8c6ff;
    border-radius:24px;
    padding:22px;
    min-height:260px;
    box-shadow:0 8px 24px rgba(90,50,150,.08);
    cursor:pointer;
}
.idea-card b {
    font-size:18px;
}

[data-testid="stFileUploader"] {background:#fff;border:1px dashed #b894ff;border-radius:18px;padding:14px;}
.small {color:#555!important;font-size:15px;}
[data-testid="stTextAreaCharCounter"] {
    color:#9b8bbd!important;
    font-size:12px!important;
    opacity:.55!important;
}
.step-title {
    font-size:18px;
    font-weight:900;
    margin-bottom:6px;
}
.soft-note {
    color:#7b6a99!important;
    font-size:14px;
    margin-top:-6px;
    margin-bottom:12px;
}
.big-question {
    font-size:34px;
    font-weight:900;
    margin-top:22px;
    margin-bottom:10px;
}

.summary-box {
    background:#ffffff;
    border:1px solid #e3d7ff;
    border-radius:22px;
    padding:18px;
    margin-bottom:14px;
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

def generar_con_ia(perfil, descripcion, objetivo, formato_contenido, historial):
    prompt = f"""
Actúa como Dago, un Community Manager profesional para negocios pequeños de Chile.

Tu trabajo NO es escribir frases bonitas al azar.
Tu trabajo es crear contenido útil para un dueño ocupado que necesita vender, informar o mantener activa su cuenta.

PERFIL DEL NEGOCIO:
{json.dumps(perfil, ensure_ascii=False)}

FORMATO:
{formato_contenido}

OBJETIVO:
{objetivo}

INFORMACIÓN ENTREGADA POR EL USUARIO:
{descripcion}

HISTORIAL RECIENTE:
{json.dumps(historial[-8:], ensure_ascii=False)}

DEVUELVE SOLO JSON VÁLIDO:
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

REGLAS DURAS:
- No inventes precios.
- No inventes descuentos.
- No inventes stock.
- No inventes eventos.
- No inventes horarios.
- No inventes fechas.
- No inventes disponibilidad.
- No inventes testimonios.
- No inventes antes/después.
- Si el usuario dio precio, producto, horario o condición, úsalo exactamente.
- Si falta un dato, no lo inventes: redacta de forma útil usando solo lo disponible.
- No uses el nombre del negocio como gancho visual.
- No pongas el nombre del negocio dentro de la imagen.
- Usa lenguaje chileno natural, claro y profesional.
- El texto de imagen debe ser corto y legible.

SI EL OBJETIVO ES "Vender una promoción":
- El contenido debe sonar como PROMOCIÓN real, no branding.
- El gancho visual debe priorizar producto + precio/beneficio si existe.
- Ejemplos buenos:
  "CAFÉ + MEDIALUNA"
  "CORTES A $5.000"
  "COMBO DESAYUNO"
  "PROMO HASTA HOY"
- Ejemplos malos:
  "DESCUBRE SABORES"
  "EXPERIENCIA ÚNICA"
  "CONOCE NUESTRA VARIEDAD"
- El caption debe responder:
  qué se ofrece,
  cuánto cuesta si existe,
  hasta cuándo dura si existe,
  cómo pedir/reservar.
- Si no hay precio, no inventes precio.
- Si no hay vigencia, no inventes urgencia falsa.

SI EL FORMATO ES "Historia":
- Debe ser breve.
- Puede tener encuesta, pregunta, sticker o llamado a responder.
- Máximo 1 idea principal.
- Gancho visual máximo 4 palabras.
- Subtítulo máximo 7 palabras.

SI EL FORMATO ES "Publicación":
- Puede explicar un poco más.
- Caption de 2 a 4 líneas.
- Gancho visual máximo 4 palabras.
- Subtítulo máximo 9 palabras.

DIRECCIÓN VISUAL:
- Sugiere diseño simple y realista.
- Si la foto no sirve, dilo en idea_foto.
- Evita exceso de texto.
- El texto_en_imagen debe ser corto.

HASHTAGS:
- Máximo 8.
- Rubro + ciudad si existe + intención.
- Sin hashtags ridículos.

Antes de responder revisa:
1. ¿Respeta el objetivo?
2. ¿Inventé algo?
3. ¿Esto lo subiría un negocio real?
4. ¿El texto visual es corto?
5. ¿Ayuda a vender, informar o activar audiencia?

Devuelve SOLO JSON válido.
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.28,
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



def generar_ideas_con_ia(perfil, formato_contenido, objetivo, historial):
    prompt = f"""
Actúa como Dago, un Community Manager estratégico para negocios pequeños de Chile.

El usuario NO sabe qué publicar.
Tu trabajo es darle 4 caminos concretos y útiles, sin inventar datos.

PERFIL:
{json.dumps(perfil, ensure_ascii=False)}

FORMATO:
{formato_contenido}

OBJETIVO:
{objetivo}

HISTORIAL:
{json.dumps(historial[-8:], ensure_ascii=False)}

DEVUELVE SOLO JSON:
{{
 "ideas":[
   {{"titulo":"","descripcion":"","por_que_funciona":""}},
   {{"titulo":"","descripcion":"","por_que_funciona":""}},
   {{"titulo":"","descripcion":"","por_que_funciona":""}},
   {{"titulo":"","descripcion":"","por_que_funciona":""}}
 ]
}}

REGLAS DURAS:
- No inventes precio.
- No inventes descuento.
- No inventes stock.
- No inventes horario.
- No inventes evento.
- No inventes testimonio.
- No inventes antes/después.
- No inventes disponibilidad.
- No inventes clientes.
- Usa solo productos, servicios y material disponible del perfil.

SI OBJETIVO = "Vender una promoción":
Las 4 ideas deben ser PROMOCIONES accionables, no branding.
No escribas ideas como “conoce nuestra variedad”.
Cada idea debe indicar qué dato comercial falta completar si falta.

Buenas ideas:
1. Promo producto estrella: elegir un producto/servicio real y agregar precio real.
2. Combo simple: juntar dos productos/servicios reales sin inventar precio.
3. Promo por horario: usar horario real entregado por el negocio.
4. Beneficio limitado: solo si el dueño luego confirma condición.

Cada descripción debe sonar así:
"Promocionar [producto/servicio real] usando precio real y una condición clara. Ideal para comunicar una oferta directa sin inventar descuentos."

Si el perfil no tiene producto claro, pide elegir producto:
"Elegir un producto principal del negocio, agregar precio real y vigencia."

SI OBJETIVO = "Mostrar un producto o servicio":
- Ideas para destacar calidad, beneficio o uso.
- No lo conviertas en promoción.

SI OBJETIVO = "Avisar horario o disponibilidad":
- Ideas claras.
- No inventes cupos.

SI OBJETIVO = "Recordar que pueden reservar":
- Ideas para reservas por WhatsApp o mensaje.
- No digas últimos cupos si no está confirmado.

SI OBJETIVO = "Educar al cliente":
- Tips, cuidados, errores comunes, beneficios.

SI OBJETIVO = "Crear confianza":
- Proceso, cuidado, calidad, experiencia.
- Sin testimonios inventados.

SI FORMATO = "Historia":
- Ideas para interacción rápida.
- Encuesta, pregunta, sticker, recordatorio, responder por interno.
- Debe poder hacerse en menos de 1 minuto.

SI FORMATO = "Publicación":
- Ideas para feed.
- Más enfocadas en claridad, venta o posicionamiento.

ESTRUCTURA:
titulo:
- máximo 5 palabras
- concreto

descripcion:
- instrucción directa para crear contenido
- debe incluir qué comunicar
- si falta precio, horario o condición, dilo explícitamente

por_que_funciona:
- máximo 18 palabras
- lógica de negocio real

VARIEDAD:
Entrega 4 ideas distintas:
1. venta directa
2. confianza/calidad
3. interacción
4. acción rápida

Devuelve SOLO JSON válido.
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
        response_format={"type": "json_object"}
    )
    data = json.loads(r.choices[0].message.content)
    if "ideas" not in data or not isinstance(data["ideas"], list):
        data["ideas"] = []
    return data

def crear_imagen_base(perfil, data, foto=None, variante=0, formato_contenido='Publicación', mostrar_direccion=False):
    rubro = perfil.get("rubro", "").lower()

    if "barber" in rubro:
        fondo, acento = (16, 16, 18), (210, 170, 90)
    elif "cafeter" in rubro or "comida" in rubro or "delivery" in rubro or "restaurante" in rubro:
        fondo, acento = (255, 248, 236), (190, 105, 35)
    elif "belleza" in rubro or "uñas" in rubro:
        fondo, acento = (252, 240, 246), (150, 80, 120)
    else:
        fondo, acento = (248, 245, 255), MORADO

    ancho_final = 1080
    alto_final = 1920 if formato_contenido == "Historia" else 1080

    img = Image.new("RGB", (ancho_final, alto_final), fondo)
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
            main = recortar(foto_base, ancho_final, 1180 if formato_contenido == 'Historia' else 700)
            img.paste(main, (0, 0))
            d.rectangle((0, 1160 if formato_contenido == 'Historia' else 690, ancho_final, alto_final), fill=fondo)
            x, y = 70, 1260 if formato_contenido == 'Historia' else 760
            text_color = (20,20,24) if sum(fondo) > 450 else (250,250,250)
            sub_color = (70,70,75) if sum(fondo) > 450 else (225,225,225)

        elif layout == 1:
            # Foto completa + franja oscura inferior
            main = recortar(foto_base, ancho_final, alto_final)
            img.paste(main, (0, 0))
            overlay = Image.new("RGBA", (ancho_final, alto_final), (0,0,0,0))
            od = ImageDraw.Draw(overlay)
            od.rectangle((0, 1260 if formato_contenido == 'Historia' else 650, ancho_final, alto_final), fill=(0,0,0,210))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            d = ImageDraw.Draw(img)
            x, y = 70, 1340 if formato_contenido == 'Historia' else 735
            text_color = (255,255,255)
            sub_color = (225,225,225)

        elif layout == 2:
            # Fondo claro, foto circular/rounded centrada
            d.rectangle((0, 0, ancho_final, alto_final), fill=fondo)
            main = recortar(foto_base, 850, 620)
            mask = Image.new("L", (850,620), 0)
            md = ImageDraw.Draw(mask)
            md.rounded_rectangle((0,0,850,620), radius=45, fill=255)
            img.paste(main, (115, 90), mask)
            x, y = 90, 1260 if formato_contenido == 'Historia' else 760
            text_color = (20,20,24) if sum(fondo) > 450 else (250,250,250)
            sub_color = (70,70,75) if sum(fondo) > 450 else (225,225,225)

        else:
            # Split editorial
            d.rectangle((0, 0, ancho_final, alto_final), fill=fondo)
            main = recortar(foto_base, 540, alto_final)
            img.paste(main, (540, 0))
            x, y = 65, 620 if formato_contenido == 'Historia' else 330
            text_color = (20,20,24) if sum(fondo) > 450 else (250,250,250)
            sub_color = (70,70,75) if sum(fondo) > 450 else (225,225,225)

    else:
        d.rounded_rectangle((55,55,1025,alto_final-55), radius=42, outline=acento, width=8)
        x, y = 85, 760 if formato_contenido == 'Historia' else 390
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
    d.rounded_rectangle((x, min(y + 28, alto_final-65), x + 180, min(y + 40, alto_final-53)), radius=8, fill=acento)

    if mostrar_direccion and perfil.get("direccion"):
        marca = perfil.get("direccion", "").strip()
        if marca:
            f_dir = fuente(24, True)
            bbox = d.textbbox((0, 0), marca, font=f_dir)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x_dir = ancho_final - tw - 55
            y_dir = alto_final - th - 45
            d.rounded_rectangle(
                (x_dir - 22, y_dir - 12, x_dir + tw + 22, y_dir + th + 12),
                radius=22,
                fill=(255, 255, 255)
            )
            d.text((x_dir, y_dir), marca, font=f_dir, fill=(35, 25, 55))

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
    "whatsapp": "",
    "direccion": ""
}

perfil = load_json(PROFILE_PATH, perfil_default)
historial = load_json(HISTORY_PATH, [])

st.markdown("""
<div class="hero">
<h1>Dago</h1>
<p class="small">Tu Community Manager en un click.</p>
</div>
""", unsafe_allow_html=True)



def render_creador():
    if "crear_step" not in st.session_state:
        st.session_state["crear_step"] = 1
    if "crear_formato" not in st.session_state:
        st.session_state["crear_formato"] = "Publicación"
    if "crear_objetivo" not in st.session_state:
        st.session_state["crear_objetivo"] = ""
    if "descripcion_actual" not in st.session_state:
        st.session_state["descripcion_actual"] = ""
    if "ideas_sugeridas" not in st.session_state:
        st.session_state["ideas_sugeridas"] = None
    if "mostrar_direccion" not in st.session_state:
        st.session_state["mostrar_direccion"] = False

    step = st.session_state["crear_step"]
    generar = False
    foto = None

    st.markdown("## Crear contenido con Dago")

    if step < 4:
        st.markdown(f"<p class='soft-note'>Paso {step} de 4</p>", unsafe_allow_html=True)

        if step == 1:
            st.markdown("<div class='big-question'>¿Qué quieres crear?</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("PUBLICACIÓN", use_container_width=True):
                    st.session_state["crear_formato"] = "Publicación"
                    st.session_state["crear_step"] = 2
                    st.rerun()
            with c2:
                if st.button("HISTORIA", use_container_width=True):
                    st.session_state["crear_formato"] = "Historia"
                    st.session_state["crear_step"] = 2
                    st.rerun()

        elif step == 2:
            formato_contenido = st.session_state["crear_formato"]
            st.markdown("<div class='big-question'>¿Cuál es el objetivo?</div>", unsafe_allow_html=True)

            if formato_contenido == "Historia":
                objetivos = [
                    "Mantener activa la cuenta",
                    "Hacer una encuesta",
                    "Avisar disponibilidad",
                    "Recordar reservas",
                    "Mostrar algo rápido",
                    "Generar interacción",
                    "Última oportunidad",
                    "Otro"
                ]
            else:
                objetivos = [
                    "Vender una promoción",
                    "Mostrar un producto o servicio",
                    "Avisar horario o disponibilidad",
                    "Recordar que pueden reservar",
                    "Llenar horas disponibles",
                    "Anunciar algo nuevo",
                    "Educar al cliente",
                    "Crear confianza",
                    "Otro"
                ]

            cols = st.columns(3)
            for i, obj in enumerate(objetivos):
                with cols[i % 3]:
                    if st.button(obj, key=f"obj_{i}", use_container_width=True):
                        st.session_state["crear_objetivo"] = obj
                        st.session_state["crear_step"] = 3
                        st.session_state["ideas_sugeridas"] = None
                        st.rerun()

            if st.button("ATRÁS", key="back_step_2"):
                st.session_state["crear_step"] = 1
                st.rerun()

        elif step == 3:
            formato_contenido = st.session_state["crear_formato"]
            objetivo = st.session_state["crear_objetivo"]

            st.markdown("<div class='big-question'>¿Qué quieres comunicar?</div>", unsafe_allow_html=True)
            st.markdown("<p class='soft-note'>Escribe una idea o pídele a Dago que piense por ti.</p>", unsafe_allow_html=True)

            descripcion = st.text_area(
                "Mensaje",
                height=120,
                max_chars=260,
                placeholder="Ej: Quiero avisar que hoy quedan horas disponibles para reservar.",
                key="descripcion_actual",
                label_visibility="collapsed"
            )

            if objetivo == "Vender una promoción":
                st.markdown("<div class='step-title'>Datos de la promoción</div>", unsafe_allow_html=True)
                st.markdown("<p class='soft-note'>Para que Dago no invente ofertas, completa lo que tengas. Si algo no aplica, déjalo vacío.</p>", unsafe_allow_html=True)

                pc1, pc2 = st.columns(2)
                with pc1:
                    st.text_input("Producto o servicio en promo", key="promo_producto", placeholder="Ej: café + medialuna")
                    st.text_input("Precio real", key="promo_precio", placeholder="Ej: $4.500")
                with pc2:
                    st.text_input("Vigencia", key="promo_vigencia", placeholder="Ej: hasta las 10:00 / solo hoy")
                    st.text_input("Condición", key="promo_condicion", placeholder="Ej: retiro en local / pagando en efectivo")

            b1, b2 = st.columns(2)
            with b1:
                if st.button("NO SÉ QUÉ PUBLICAR", use_container_width=True):
                    if not perfil.get("nombre"):
                        st.error("Primero guarda el perfil del negocio.")
                    else:
                        with st.spinner("Buscando ideas para este negocio..."):
                            st.session_state["ideas_sugeridas"] = generar_ideas_con_ia(
                                perfil,
                                formato_contenido,
                                objetivo,
                                historial
                            )
                        st.rerun()

            with b2:
                if st.button("USAR MI TEXTO", use_container_width=True):
                    base = st.session_state.get("descripcion_actual", "").strip()
                    if objetivo == "Vender una promoción":
                        extras = []
                        if st.session_state.get("promo_producto"):
                            extras.append(f"Producto/servicio en promoción: {st.session_state.get('promo_producto')}")
                        if st.session_state.get("promo_precio"):
                            extras.append(f"Precio real: {st.session_state.get('promo_precio')}")
                        if st.session_state.get("promo_vigencia"):
                            extras.append(f"Vigencia: {st.session_state.get('promo_vigencia')}")
                        if st.session_state.get("promo_condicion"):
                            extras.append(f"Condición: {st.session_state.get('promo_condicion')}")
                        if extras:
                            base = (base + "\n" if base else "") + "\n".join(extras)

                    if not base:
                        st.error("Escribe algo, pide ideas o completa datos de la promoción.")
                    else:
                        st.session_state["descripcion_final"] = base
                        st.session_state["crear_step"] = 4
                        st.rerun()

            if st.session_state.get("ideas_sugeridas"):
                st.markdown("<div class='step-title'>Elige una idea</div>", unsafe_allow_html=True)
                st.markdown("<p class='soft-note'>Haz click en una tarjeta completa para continuar.</p>", unsafe_allow_html=True)

                ideas = st.session_state["ideas_sugeridas"].get("ideas", [])
                cols = st.columns(4)

                for i, idea in enumerate(ideas[:4]):
                    titulo = idea.get("titulo", f"Idea {i+1}")
                    desc = idea.get("descripcion", "")
                    razon = idea.get("por_que_funciona", "")

                    with cols[i]:
                        texto_boton = f"{titulo}\n\n{razon}\n\n{desc[:140]}..."
                        if st.button(texto_boton, key=f"idea_click_{i}", use_container_width=True):
                            st.session_state["idea_elegida_desc"] = desc
                            st.session_state["descripcion_final"] = desc
                            st.session_state["crear_step"] = 4
                            st.rerun()

            if st.button("ATRÁS", key="back_step_3"):
                st.session_state["crear_step"] = 2
                st.rerun()

    else:
        izq, der = st.columns([0.8, 1.2], gap="large")

        with izq:
            formato_contenido = st.session_state["crear_formato"]
            objetivo = st.session_state["crear_objetivo"]
            descripcion = st.session_state.get("descripcion_final") or st.session_state.get("idea_elegida_desc") or st.session_state.get("descripcion_actual", "")

            st.markdown("## Resumen")
            st.markdown(f"""
            <div class='summary-box'>
            <b>Formato:</b> {formato_contenido}<br>
            <b>Objetivo:</b> {objetivo}<br>
            <b>Idea:</b> {descripcion}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='step-title'>Sube una foto opcional</div>", unsafe_allow_html=True)

            foto = st.file_uploader(
                "Foto",
                type=["jpg","jpeg","png","webp"],
                label_visibility="collapsed",
                key="foto_crear"
            )

            mostrar_dir = st.checkbox(
                "Agregar dirección como marca de agua",
                value=st.session_state.get("mostrar_direccion", False)
            )
            st.session_state["mostrar_direccion"] = mostrar_dir

            c1, c2 = st.columns(2)
            with c1:
                if st.button("ATRÁS", key="atras_4", use_container_width=True):
                    if st.session_state.get("idea_elegida_desc"):
                        st.session_state["descripcion_actual"] = st.session_state["idea_elegida_desc"]
                        st.session_state["idea_elegida_desc"] = ""
                    st.session_state["crear_step"] = 3
                    st.rerun()
            with c2:
                generar = st.button("GENERAR", use_container_width=True)

        with der:
            st.markdown("## Resultado")

            if generar:
                if not perfil.get("nombre"):
                    st.error("Primero guarda el perfil del negocio.")
                elif not descripcion.strip():
                    st.error("Escribe qué quieres comunicar.")
                else:
                    with st.spinner("Dago está preparando tu contenido..."):
                        data = generar_con_ia(perfil, descripcion, objetivo, formato_contenido, historial)
                        st.session_state["design_variant"] = 0
                        st.session_state["last_foto"] = foto
                        st.session_state["last_formato"] = formato_contenido
                        st.session_state["last_mostrar_direccion"] = mostrar_dir

                        post = crear_imagen_base(
                            perfil,
                            data,
                            foto,
                            st.session_state["design_variant"],
                            formato_contenido,
                            mostrar_dir
                        )

                        buffer = io.BytesIO()
                        post.save(buffer, format="PNG")
                        buffer.seek(0)

                        st.session_state["post_buffer"] = buffer.getvalue()
                        st.session_state["data"] = data

                        historial.append({
                            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "formato": formato_contenido,
                            "tipo": objetivo,
                            "descripcion": descripcion,
                            "dia_recomendado": data.get("dia_recomendado",""),
                            "hora_recomendada": data.get("hora_recomendada",""),
                            "gancho": data.get("gancho_visual","")
                        })
                        save_json(HISTORY_PATH, historial)

            if "post_buffer" in st.session_state:
                cbtn1, cbtn2 = st.columns(2)

                with cbtn1:
                    if st.button("REHACER DISEÑO", use_container_width=True):
                        st.session_state["design_variant"] = st.session_state.get("design_variant", 0) + 1
                        post = crear_imagen_base(
                            perfil,
                            st.session_state["data"],
                            st.session_state.get("last_foto"),
                            st.session_state["design_variant"],
                            st.session_state.get("last_formato", "Publicación"),
                            st.session_state.get("last_mostrar_direccion", False)
                        )
                        buffer = io.BytesIO()
                        post.save(buffer, format="PNG")
                        buffer.seek(0)
                        st.session_state["post_buffer"] = buffer.getvalue()

                with cbtn2:
                    st.download_button(
                        "DESCARGAR",
                        data=st.session_state["post_buffer"],
                        file_name=f"contenido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png",
                        use_container_width=True
                    )

                st.image(st.session_state["post_buffer"], use_container_width=True)

            if "data" in st.session_state:
                data = st.session_state["data"]
                visual = data.get("direccion_visual", {})

                st.markdown("### Texto principal")
                if st.session_state.get("last_formato") == "Historia":
                    st.markdown(f"<div class='card'>{data.get('historia_instagram','')}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='card'>{data.get('caption_instagram','')}</div>", unsafe_allow_html=True)

                st.markdown("### WhatsApp")
                st.markdown(f"<div class='card'>{data.get('mensaje_whatsapp','')}</div>", unsafe_allow_html=True)

                st.markdown("### Dirección visual sugerida")
                st.markdown(f"""
                <div class="purple">
                <b>Foto ideal:</b> {visual.get('foto_ideal','')}<br>
                <b>Layout:</b> {visual.get('tipo_layout','')}<br>
                <b>Texto:</b> {visual.get('texto_en_imagen','')}<br>
                <b>Evitar:</b> {visual.get('que_evitar','')}<br>
                <b>Idea foto:</b> {data.get('idea_foto','')}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### Cuándo subirlo")
                st.markdown(f"<div class='card'><b>{data.get('dia_recomendado','')}</b> a las <b>{data.get('hora_recomendada','')}</b><br>{data.get('motivo_horario','')}</div>", unsafe_allow_html=True)

                st.markdown("### Hashtags")
                st.markdown(f"<div class='card'>{' '.join(data.get('hashtags', []))}</div>", unsafe_allow_html=True)



tab_inicio, tab_perfil, tab_historial = st.tabs(["Inicio", "Perfil del negocio", "Calendario / historial"])

with tab_inicio:
    if "mostrar_creador" not in st.session_state:
        st.session_state["mostrar_creador"] = False

    if st.session_state["mostrar_creador"]:
        ctop1, ctop2 = st.columns([0.22, 0.78])
        with ctop1:
            if st.button("← VOLVER", use_container_width=True):
                st.session_state["mostrar_creador"] = False
                st.rerun()

        render_creador()

    else:
        st.markdown("## Inicio")

        if perfil.get("nombre"):
            negocio = perfil.get("nombre")
            rubro = perfil.get("rubro")
            tono = perfil.get("tono")

            st.markdown(f"""
            <div class="home-main">
            <h2>Hola, {negocio}</h2>
            <p class="small">Dago está listo para crear contenido para tu {rubro.lower()} con tono {tono.lower()}.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="home-main">
            <h2>Configura tu negocio</h2>
            <p class="small">Completa el perfil para que Dago pueda crear ideas, publicaciones e historias personalizadas.</p>
            </div>
            """, unsafe_allow_html=True)

        cta1, cta2 = st.columns([1,1])

        with cta1:
            if st.button("CREAR CONTENIDO AHORA", use_container_width=True):
                st.session_state["mostrar_creador"] = True
                st.session_state["crear_step"] = 1
                st.session_state["ideas_sugeridas"] = None
                st.session_state["descripcion_actual"] = ""
                st.session_state["idea_elegida_desc"] = ""
                st.session_state["descripcion_final"] = ""
                for k in ["promo_producto","promo_precio","promo_vigencia","promo_condicion"]:
                    st.session_state[k] = ""
                st.rerun()

        with cta2:
            if st.button("GENERAR PLAN SEMANAL", use_container_width=True):
                if not perfil.get("nombre"):
                    st.error("Primero guarda el perfil.")
                else:
                    with st.spinner("Preparando plan semanal..."):
                        st.session_state["plan"] = generar_plan_semanal(perfil, historial)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="home-card">
            <h3>Próxima idea</h3>
            <p>{perfil.get('dias_publicacion','Define tus días')}</p>
            <b>{perfil.get('horario_preferido','19:00')}</b>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="home-card">
            <h3>Contenido creado</h3>
            <p><b>{len(historial)}</b> piezas guardadas</p>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            ultima = historial[-1]["gancho"] if historial else "Aún no hay ideas"
            st.markdown(f"""
            <div class="home-card">
            <h3>Última idea</h3>
            <p>{ultima}</p>
            </div>
            """, unsafe_allow_html=True)

        if "plan" in st.session_state:
            plan = st.session_state["plan"]
            st.markdown("## Plan recomendado")
            st.markdown(f"""
            <div class="home-main">
            <b>{plan.get('resumen','')}</b><br>
            <span class="small">{plan.get('recomendacion_general','')}</span>
            </div>
            """, unsafe_allow_html=True)

            for item in plan.get("plan", []):
                st.markdown(f"""
                <div class="home-card">
                <b>{item.get('dia')} · {item.get('hora')}</b><br>
                <b>{item.get('tipo')}</b>: {item.get('idea')}<br>
                <span class="small">{item.get('objetivo')}</span>
                </div>
                """, unsafe_allow_html=True)


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
        perfil["direccion"] = st.text_input("Dirección del negocio opcional", value=perfil.get("direccion",""), placeholder="Ej: 5 Norte 123, Viña del Mar")
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
