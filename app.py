import streamlit as st
from PIL import Image, ImageOps, ImageFilter
from groq import Groq
import os, json, html, io, hmac, hashlib
from datetime import datetime
import requests

st.set_page_config(page_title="Dago", page_icon="💜", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_PATH = os.path.join(DATA_DIR, "usuarios.json")
PROFILE_PATH = os.path.join(DATA_DIR, "perfil_negocio.json")
HISTORY_PATH = os.path.join(DATA_DIR, "historial.json")
os.makedirs(DATA_DIR, exist_ok=True)

GROQ_MODEL = "llama-3.3-70b-versatile"
RECRAFT_MODEL = "recraftv4"
RECRAFT_EDIT_MODEL = "recraftv3"
RECRAFT_URL = "https://external.api.recraft.ai/v1/images/generations"
RECRAFT_IMAGE_TO_IMAGE_URL = "https://external.api.recraft.ai/v1/images/imageToImage"
MAX_RECRAFT_IMAGE_BYTES = 4_800_000
MIN_RECRAFT_IMAGE_SIDE = 256
MAX_RECRAFT_IMAGE_SIDE = 4090
MAX_RECRAFT_IMAGE_PIXELS = 15_500_000
INSTAGRAM_POST_SIZE = (1080, 1080)
INSTAGRAM_STORY_SIZE = (1080, 1920)
MAX_HISTORY_ITEMS = 200
HISTORY_CONTEXT_ITEMS = 8
SUPABASE_TIMEOUT = 12

Image.MAX_IMAGE_PIXELS = 40_000_000

st.markdown("""
<style>
:root {
    --bg:#f5f6fa;
    --surface:#ffffff;
    --surface-soft:#f9fafc;
    --ink:#171821;
    --muted:#646b78;
    --line:#dde2ea;
    --primary:#5b4df1;
    --primary-dark:#4434d4;
    --teal:#0f9f8a;
    --amber:#b7791f;
    --rose:#c6426e;
    --shadow:0 10px 26px rgba(18, 24, 40, .075);
}
.stApp {
    background:
        linear-gradient(180deg, #fafbff 0%, var(--bg) 42%, #f3f5f8 100%);
    color:var(--ink);
}
[data-testid="stHeader"] {background:transparent;}
.block-container {
    max-width:1240px;
    padding:1.25rem 1.5rem 2.5rem;
}
h1,h2,h3,p,label,span {color:var(--ink)!important;}
h2 {
    font-size:28px!important;
    letter-spacing:0!important;
    margin-top:.55rem!important;
    margin-bottom:.85rem!important;
}
h3 {
    font-size:18px!important;
    letter-spacing:0!important;
}
.hero {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:16px;
    background:var(--surface);
    border:1px solid var(--line);
    border-radius:10px;
    padding:16px 18px;
    margin-bottom:18px;
    box-shadow:var(--shadow);
}
.brand-lockup {
    display:flex;
    align-items:center;
    gap:14px;
}
.brand-mark {
    width:46px;
    height:46px;
    border-radius:10px;
    display:grid;
    place-items:center;
    background:#171821;
    color:#fff!important;
    font-size:24px;
    font-weight:900;
    line-height:1;
}
.hero h1 {
    font-size:27px!important;
    line-height:1.1!important;
    margin:0!important;
    letter-spacing:0!important;
}
.hero p {
    font-size:14px!important;
    margin:3px 0 0!important;
    color:var(--muted)!important;
}
.status-pill {
    border:1px solid #b9ece3;
    background:#effcf8;
    color:#087c6c!important;
    border-radius:999px;
    padding:8px 12px;
    font-size:13px;
    font-weight:850;
    white-space:nowrap;
}
@media (max-width: 760px) {
    .block-container {padding:1rem!important;}
    .hero {align-items:flex-start; flex-direction:column; padding:14px!important;}
    .hero h1 {font-size:24px!important;}
    .brand-mark {width:42px;height:42px;font-size:22px;}
    h2 {font-size:24px!important;}
    h3 {font-size:18px!important;}
}
.home-card {
    background:var(--surface);
    border:1px solid var(--line);
    border-radius:8px;
    padding:18px;
    min-height:132px;
    box-shadow:var(--shadow);
}
.home-main {
    background:var(--surface);
    border:1px solid var(--line);
    border-left:4px solid var(--primary);
    border-radius:8px;
    padding:20px;
    margin-bottom:18px;
    box-shadow:var(--shadow);
}
.home-main h2 {margin-top:0!important;}
.home-card h3 {margin-top:0!important;margin-bottom:10px!important;}
.home-card p {color:var(--muted)!important;}
.card-kicker {
    display:block;
    color:var(--muted)!important;
    font-size:12px;
    font-weight:850;
    letter-spacing:.04em;
    text-transform:uppercase;
    margin-bottom:8px;
}
.metric-value {
    display:block;
    font-size:25px;
    line-height:1.1;
    font-weight:900;
    color:var(--ink)!important;
    margin-top:8px;
}
.accent-teal {border-top:3px solid var(--teal);}
.accent-amber {border-top:3px solid var(--amber);}
.accent-rose {border-top:3px solid var(--rose);}
.card {
    background:var(--surface);
    border:1px solid var(--line);
    border-radius:8px;
    padding:18px;
    margin-bottom:16px;
    box-shadow:var(--shadow);
}
.purple {
    background:#172033;
    color:white!important;
    border-radius:8px;
    padding:20px;
    margin-bottom:16px;
    box-shadow:0 12px 28px rgba(23,32,51,.16);
}
.purple * {color:white!important;}
.stTextInput input,.stTextArea textarea {
    background:#fff!important;
    color:var(--ink)!important;
    border:1px solid #cfd6e3!important;
    border-radius:8px!important;
    font-size:16px!important;
    box-shadow:0 1px 2px rgba(17,24,39,.04)!important;
}
.stTextInput input:focus,.stTextArea textarea:focus {
    border-color:var(--primary)!important;
    box-shadow:0 0 0 3px rgba(91,77,241,.12)!important;
}
.stSelectbox div[data-baseweb="select"] > div {
    background:#fff!important;
    border:1px solid #cfd6e3!important;
    border-radius:8px!important;
}
.stButton>button,.stDownloadButton>button {
    background:var(--primary)!important;
    color:white!important;
    border:none!important;
    border-radius:8px!important;
    font-weight:850!important;
    padding:.82rem 1.05rem!important;
    box-shadow:0 9px 18px rgba(91,77,241,.20)!important;
    transition:transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.stButton>button *,.stDownloadButton>button * {
    color:white!important;
}
.stButton>button:hover,.stDownloadButton>button:hover {
    background:var(--primary-dark)!important;
    transform:translateY(-1px);
    box-shadow:0 11px 22px rgba(91,77,241,.25)!important;
}
.stButton>button:active,.stDownloadButton>button:active {
    transform:translateY(0);
}
.stTabs [data-baseweb="tab-list"] {
    gap:8px;
    border-bottom:1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
    height:42px;
    border-radius:8px 8px 0 0;
    padding:0 14px;
    font-weight:780;
}
.stTabs [aria-selected="true"] {
    background:#fff;
    border:1px solid var(--line);
    border-bottom-color:#fff;
    box-shadow:0 -2px 12px rgba(18,24,40,.05);
}
.idea-card {
    background:var(--surface);
    border:1px solid var(--line);
    border-radius:8px;
    padding:18px;
    min-height:260px;
    box-shadow:var(--shadow);
    cursor:pointer;
}
.idea-card b {
    font-size:18px;
}

[data-testid="stFileUploader"] {
    background:#fff;
    border:1px dashed #9da8ff;
    border-radius:8px;
    padding:16px;
}
[data-testid="stFileUploader"] section {
    border:0!important;
}
[data-testid="stAlert"] {
    border-radius:8px;
}
.small {color:var(--muted)!important;font-size:15px;}
[data-testid="stTextAreaCharCounter"] {
    color:#8a90a0!important;
    font-size:12px!important;
    opacity:.55!important;
}
.step-title {
    font-size:18px;
    font-weight:850;
    margin-bottom:6px;
}
.step-badge {
    display:inline-flex;
    align-items:center;
    gap:8px;
    background:#eefcf8;
    border:1px solid #b9ece3;
    color:#087c6c!important;
    border-radius:999px;
    padding:7px 11px;
    font-size:13px;
    font-weight:850;
    margin:6px 0 8px;
}
.step-dot {
    width:8px;
    height:8px;
    border-radius:999px;
    background:var(--teal);
}
.soft-note {
    color:var(--muted)!important;
    font-size:14px;
    margin-top:-6px;
    margin-bottom:12px;
}
.big-question {
    font-size:30px;
    font-weight:900;
    margin-top:22px;
    margin-bottom:10px;
}

.summary-box {
    background:#ffffff;
    border:1px solid var(--line);
    border-left:4px solid var(--teal);
    border-radius:8px;
    padding:18px;
    margin-bottom:14px;
    box-shadow:var(--shadow);
}
div[data-testid="stImage"] img {
    border-radius:8px;
    border:1px solid var(--line);
}
.stSlider [data-baseweb="slider"] {
    padding-top:8px;
}

/* Visual v2: morado, llamativo y organizado */
.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(145,60,255,.20), transparent 31rem),
        radial-gradient(circle at 92% 10%, rgba(95,30,214,.15), transparent 28rem),
        linear-gradient(180deg,#fbf8ff 0%,#f3edff 52%,#ffffff 100%)!important;
}
.block-container {
    max-width:1180px!important;
}
.hero {
    position:relative;
    overflow:hidden;
    min-height:150px;
    padding:26px 28px!important;
    border:0!important;
    border-radius:0 22px 0 22px!important;
    background:
        linear-gradient(135deg,#3b168f 0%,#7b2ff7 52%,#b24cff 100%)!important;
    box-shadow:0 22px 48px rgba(91,77,241,.28)!important;
}
.hero:before {
    content:"";
    position:absolute;
    inset:auto -70px -95px auto;
    width:260px;
    height:260px;
    border-radius:50%;
    background:rgba(255,255,255,.15);
}
.hero:after {
    content:"";
    position:absolute;
    top:0;
    right:0;
    width:35%;
    height:100%;
    background:linear-gradient(135deg,transparent 0%,rgba(255,255,255,.17) 100%);
    clip-path:polygon(32% 0,100% 0,100% 100%,0 100%);
}
.brand-lockup,.status-pill {position:relative;z-index:1;}
.brand-mark {
    width:58px!important;
    height:58px!important;
    border-radius:0 16px 0 16px!important;
    background:#ffffff!important;
    color:#6422e7!important;
    box-shadow:0 14px 28px rgba(25,9,71,.25)!important;
}
.hero h1 {
    color:#fff!important;
    font-size:36px!important;
}
.hero p {
    color:#efe6ff!important;
    font-size:16px!important;
}
.status-pill {
    background:rgba(255,255,255,.16)!important;
    color:#fff!important;
    border:1px solid rgba(255,255,255,.36)!important;
    border-radius:0 14px 0 14px!important;
    backdrop-filter:blur(8px);
}
.home-main,.summary-box {
    position:relative;
    overflow:hidden;
    border:0!important;
    border-radius:0 18px 0 18px!important;
    background:#ffffff!important;
    box-shadow:0 18px 40px rgba(72,38,138,.13)!important;
}
.home-main:before,.summary-box:before {
    content:"";
    position:absolute;
    left:0;
    top:0;
    width:100%;
    height:6px;
    background:linear-gradient(90deg,#6d28d9,#a855f7,#22c7aa);
}
.home-card {
    position:relative;
    overflow:hidden;
    border:0!important;
    border-radius:0 18px 0 18px!important;
    padding:22px!important;
    min-height:152px!important;
    background:#fff!important;
    box-shadow:0 18px 38px rgba(72,38,138,.14)!important;
}
.home-card:before {
    content:"";
    position:absolute;
    top:0;
    right:0;
    width:74px;
    height:74px;
    background:linear-gradient(135deg,#7c3aed,#c084fc);
    clip-path:polygon(100% 0,100% 100%,0 0);
}
.home-card:after {
    content:"";
    position:absolute;
    left:0;
    bottom:0;
    width:100%;
    height:4px;
    background:linear-gradient(90deg,#7c3aed,#c084fc);
}
.accent-teal:after {background:linear-gradient(90deg,#7c3aed,#0f9f8a)!important;}
.accent-amber:after {background:linear-gradient(90deg,#7c3aed,#f59e0b)!important;}
.accent-rose:after {background:linear-gradient(90deg,#7c3aed,#e11d74)!important;}
.metric-value {
    color:#5b21b6!important;
    font-size:32px!important;
}
.card-kicker {
    color:#7c3aed!important;
}
.action-card {
    position:relative;
    overflow:hidden;
    min-height:118px;
    padding:20px;
    margin-bottom:10px;
    border-radius:0 18px 0 18px;
    color:#fff!important;
    box-shadow:0 18px 38px rgba(72,38,138,.16);
}
.action-card * {color:#fff!important;}
.action-card b {
    display:block;
    font-size:19px;
    margin-bottom:7px;
}
.action-card span {
    display:block;
    color:#f2e9ff!important;
    font-size:14px;
}
.action-card:after {
    content:"";
    position:absolute;
    right:-36px;
    bottom:-42px;
    width:150px;
    height:150px;
    border-radius:50%;
    background:rgba(255,255,255,.16);
}
.action-primary {
    background:linear-gradient(135deg,#5b21b6,#8b5cf6);
}
.action-secondary {
    background:linear-gradient(135deg,#312e81,#7c3aed);
}
.stButton>button,.stDownloadButton>button {
    border-radius:0 14px 0 14px!important;
    background:linear-gradient(135deg,#6d28d9,#9333ea)!important;
    box-shadow:0 14px 26px rgba(109,40,217,.28)!important;
}
.stButton>button:hover,.stDownloadButton>button:hover {
    background:linear-gradient(135deg,#581c87,#7e22ce)!important;
}
.stTabs [data-baseweb="tab-list"] {
    background:#ffffff;
    border:1px solid #eadcff!important;
    border-radius:0 16px 0 16px;
    padding:8px;
    box-shadow:0 12px 28px rgba(72,38,138,.10);
}
.stTabs [data-baseweb="tab"] {
    border-radius:0 12px 0 12px!important;
}
.stTabs [aria-selected="true"] {
    background:#6d28d9!important;
    border:0!important;
}
.stTabs [aria-selected="true"] p {
    color:#fff!important;
}
.card,.purple {
    border:0!important;
    border-radius:0 18px 0 18px!important;
    box-shadow:0 18px 38px rgba(72,38,138,.13)!important;
}
.purple {
    background:linear-gradient(135deg,#4c1d95,#7e22ce)!important;
}
.step-badge {
    background:#6d28d9!important;
    border:0!important;
    color:#fff!important;
    border-radius:0 14px 0 14px!important;
    box-shadow:0 10px 22px rgba(109,40,217,.25);
}
.step-dot {background:#d8b4fe!important;}
.big-question {
    color:#3b168f!important;
    font-size:34px!important;
}
[data-testid="stFileUploader"] {
    border:2px dashed #a855f7!important;
    background:#fbf7ff!important;
    border-radius:0 18px 0 18px!important;
}
.stTextInput input,.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    border-radius:0 12px 0 12px!important;
    border-color:#d8b4fe!important;
}
@media (max-width:760px) {
    .hero {min-height:unset;border-radius:0 18px 0 18px!important;}
    .hero h1 {font-size:30px!important;}
    .home-card,.action-card,.home-main,.summary-box {border-radius:0 16px 0 16px!important;}
}

/* Visual v3: estudio mas claro y mas llamativo */
.hero.app-hero {
    align-items:stretch!important;
    min-height:190px!important;
    padding:28px!important;
}
.hero.app-hero .brand-lockup {
    align-items:flex-start!important;
    flex:1;
}
.hero-copy {
    max-width:640px;
}
.hero-eyebrow {
    display:inline-flex;
    margin-bottom:8px;
    color:#f5d0fe!important;
    font-size:12px!important;
    font-weight:900;
    letter-spacing:.08em!important;
    text-transform:uppercase;
}
.hero.app-hero h1 {
    max-width:720px;
    font-size:42px!important;
    line-height:1.03!important;
    margin-bottom:8px!important;
}
.hero-stats {
    position:relative;
    z-index:1;
    display:grid;
    grid-template-columns:1fr;
    gap:10px;
    min-width:178px;
    align-self:center;
}
.hero-stat {
    background:rgba(255,255,255,.15);
    border:1px solid rgba(255,255,255,.28);
    border-radius:0 16px 0 16px;
    padding:12px 14px;
    backdrop-filter:blur(10px);
}
.hero-stat b {
    display:block;
    color:#fff!important;
    font-size:24px;
    line-height:1;
}
.hero-stat span {
    display:block;
    color:#f4eaff!important;
    font-size:12px;
    font-weight:800;
    margin-top:5px;
}
.session-bar {
    display:flex;
    align-items:center;
    gap:10px;
    margin:-6px 0 18px;
    color:#6b587d!important;
    font-size:14px;
}
.session-dot {
    width:10px;
    height:10px;
    border-radius:999px;
    background:#10b981;
    box-shadow:0 0 0 5px rgba(16,185,129,.12);
}
.section-title {
    margin:6px 0 14px;
}
.section-title span {
    color:#7c3aed!important;
    font-size:12px!important;
    font-weight:900;
    letter-spacing:.07em!important;
    text-transform:uppercase;
}
.section-title h2 {
    margin:.15rem 0 0!important;
    color:#251144!important;
}
.dashboard-intro {
    min-height:190px;
    padding:26px!important;
}
.dashboard-intro h2 {
    font-size:34px!important;
    color:#24103f!important;
}
.chip-row {
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    margin-top:14px;
}
.chip-row span {
    display:inline-flex;
    align-items:center;
    min-height:30px;
    padding:7px 10px;
    background:#f4ecff;
    border:1px solid #e7d7ff;
    border-radius:999px;
    color:#5b21b6!important;
    font-size:12px;
    font-weight:850;
}
.studio-card {
    position:relative;
    overflow:hidden;
    min-height:180px;
    padding:24px;
    margin-bottom:12px;
    color:#fff!important;
    clip-path:polygon(0 0,calc(100% - 24px) 0,100% 24px,100% 100%,24px 100%,0 calc(100% - 24px));
    box-shadow:0 22px 45px rgba(72,38,138,.20);
}
.studio-card * {color:#fff!important;}
.studio-card:before {
    content:"";
    position:absolute;
    inset:0;
    background:linear-gradient(130deg,rgba(255,255,255,.18),transparent 44%);
}
.studio-card:after {
    content:"";
    position:absolute;
    right:-60px;
    bottom:-72px;
    width:220px;
    height:220px;
    border-radius:50%;
    background:rgba(255,255,255,.13);
}
.studio-card b,.studio-card span,.studio-card p {position:relative;z-index:1;}
.studio-card b {
    display:block;
    font-size:23px;
    line-height:1.12;
    margin:10px 0 8px;
}
.studio-card > span:first-child {
    display:inline-flex;
    font-size:12px;
    font-weight:900;
    letter-spacing:.07em;
    text-transform:uppercase;
    color:#f5d0fe!important;
}
.studio-card b + span {
    display:block;
    color:#f5ecff!important;
    font-size:14px;
    font-weight:600;
    letter-spacing:0!important;
    line-height:1.45;
    text-transform:none;
}
.studio-card p {
    color:#f5ecff!important;
    font-size:14px;
    margin:0;
}
.studio-primary {background:linear-gradient(135deg,#4c1d95 0%,#7c3aed 52%,#c026d3 100%);}
.studio-secondary {background:linear-gradient(135deg,#312e81 0%,#6d28d9 58%,#0f9f8a 100%);}
.format-tile {
    position:relative;
    overflow:hidden;
    background:#fff;
    border:1px solid #eadcff;
    border-radius:0 18px 0 18px;
    padding:20px;
    min-height:164px;
    margin-bottom:10px;
    box-shadow:0 16px 34px rgba(72,38,138,.12);
}
.format-tile:before {
    content:"";
    position:absolute;
    inset:0 auto 0 0;
    width:6px;
    background:linear-gradient(180deg,#7c3aed,#22c7aa);
}
.format-tile b {
    display:block;
    color:#251144!important;
    font-size:22px;
    margin-bottom:8px;
}
.format-tile span {
    display:inline-flex;
    margin-bottom:10px;
    color:#7c3aed!important;
    font-size:12px;
    font-weight:900;
    letter-spacing:.06em;
    text-transform:uppercase;
}
.format-tile p {
    color:#645471!important;
    margin:0!important;
}
.profile-banner {
    background:linear-gradient(135deg,#ffffff,#fbf7ff);
    border:1px solid #eadcff;
    border-radius:0 18px 0 18px;
    padding:20px;
    margin-bottom:18px;
    box-shadow:0 16px 34px rgba(72,38,138,.10);
}
.profile-banner b {
    color:#251144!important;
    font-size:22px;
}
.profile-banner p {
    color:#756281!important;
    margin:.35rem 0 0!important;
}
@media (max-width:760px) {
    .hero.app-hero {padding:20px!important;min-height:unset!important;}
    .hero.app-hero h1 {font-size:32px!important;}
    .hero-stats {width:100%;grid-template-columns:1fr 1fr;}
    .dashboard-intro h2 {font-size:28px!important;}
    .studio-card,.format-tile,.profile-banner {clip-path:none;border-radius:0 16px 0 16px!important;}
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

def h(valor):
    return html.escape(str(valor or ""), quote=True)

def h_lineas(valor):
    return h(valor).replace("\n", "<br>")

def leer_secreto(nombre):
    try:
        return st.secrets.get(nombre) or os.getenv(nombre, "")
    except Exception:
        return os.getenv(nombre, "")

def supabase_config():
    url = leer_secreto("SUPABASE_URL").strip().rstrip("/")
    key = (
        leer_secreto("SUPABASE_SECRET_KEY").strip()
        or leer_secreto("SUPABASE_SERVICE_ROLE_KEY").strip()
        or leer_secreto("SUPABASE_KEY").strip()
    )
    return url, key

def supabase_activo():
    url, key = supabase_config()
    return bool(url and key)

def supabase_headers(prefer=""):
    _, key = supabase_config()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers

def supabase_request(method, tabla, params=None, payload=None, prefer=""):
    url, _ = supabase_config()
    if not url:
        raise RuntimeError("Falta configurar SUPABASE_URL.")
    endpoint = f"{url}/rest/v1/{tabla}"
    try:
        response = requests.request(
            method,
            endpoint,
            headers=supabase_headers(prefer),
            params=params,
            json=payload,
            timeout=SUPABASE_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError("No pude conectar con Supabase. Revisa la URL y la clave.") from exc

    if response.status_code >= 400:
        detalle = response.text[:240] if response.text else response.reason
        raise RuntimeError(f"Supabase respondio con error {response.status_code}: {detalle}")
    if not response.text:
        return None
    try:
        return response.json()
    except ValueError:
        return None

def supabase_obtener_usuario(usuario):
    rows = supabase_request(
        "GET",
        "dago_users",
        params={
            "select": "username,salt,password_hash,nombre_negocio,creado",
            "username": f"eq.{usuario}",
            "limit": "1",
        },
    )
    return rows[0] if rows else None

def supabase_insertar_usuario(usuario, registro):
    payload = {
        "username": usuario,
        "salt": registro["salt"],
        "password_hash": registro["password_hash"],
        "nombre_negocio": registro.get("nombre_negocio", ""),
        "creado": registro.get("creado", ""),
    }
    supabase_request("POST", "dago_users", payload=payload)

def supabase_cargar_json(tabla, usuario, default):
    rows = supabase_request(
        "GET",
        tabla,
        params={"select": "data", "username": f"eq.{usuario}", "limit": "1"},
    )
    if not rows:
        return default
    data = rows[0].get("data", default)
    return data if data is not None else default

def supabase_guardar_json(tabla, usuario, data):
    payload = {
        "username": usuario,
        "data": data,
        "updated_at": datetime.utcnow().isoformat(),
    }
    supabase_request(
        "POST",
        tabla,
        payload=payload,
        prefer="resolution=merge-duplicates",
    )

def normalizar_usuario(usuario):
    limpio = "".join(c for c in str(usuario or "").strip().lower() if c.isalnum() or c in ("_", "-", "."))
    return limpio[:40]

def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt.encode("utf-8"),
        120_000
    ).hex()
    return salt, digest

def verificar_password(password, salt, digest):
    _, candidato = hash_password(password, salt)
    return hmac.compare_digest(candidato, digest)

def cargar_usuarios():
    data = load_json(USERS_PATH, {"usuarios": {}})
    if not isinstance(data, dict):
        data = {"usuarios": {}}
    if not isinstance(data.get("usuarios"), dict):
        data["usuarios"] = {}
    return data

def guardar_usuarios(data):
    save_json(USERS_PATH, data)

def crear_usuario(usuario, password, nombre_negocio=""):
    usuario = normalizar_usuario(usuario)
    if len(usuario) < 3:
        raise ValueError("El usuario debe tener al menos 3 caracteres.")
    if len(str(password or "")) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")

    salt, digest = hash_password(password)
    registro = {
        "salt": salt,
        "password_hash": digest,
        "nombre_negocio": str(nombre_negocio or "").strip(),
        "creado": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    if supabase_activo():
        if supabase_obtener_usuario(usuario):
            raise ValueError("Ese usuario ya existe.")
        supabase_insertar_usuario(usuario, registro)
        return usuario

    data = cargar_usuarios()
    if usuario in data["usuarios"]:
        raise ValueError("Ese usuario ya existe.")

    data["usuarios"][usuario] = registro
    guardar_usuarios(data)
    return usuario

def autenticar_usuario(usuario, password):
    usuario = normalizar_usuario(usuario)
    if supabase_activo():
        registro = supabase_obtener_usuario(usuario)
    else:
        data = cargar_usuarios()
        registro = data["usuarios"].get(usuario)
    if not registro:
        return None
    if verificar_password(password, registro.get("salt", ""), registro.get("password_hash", "")):
        return usuario
    return None

def rutas_usuario(usuario):
    usuario = normalizar_usuario(usuario)
    carpeta = os.path.join(DATA_DIR, "cuentas", usuario)
    os.makedirs(carpeta, exist_ok=True)
    return (
        os.path.join(carpeta, "perfil_negocio.json"),
        os.path.join(carpeta, "historial.json"),
    )

def migrar_datos_iniciales(usuario):
    profile_path, history_path = rutas_usuario(usuario)
    if supabase_activo():
        perfil_online = supabase_cargar_json("dago_profiles", usuario, {})
        if not perfil_online and os.path.exists(os.path.join(DATA_DIR, "perfil_negocio.json")):
            perfil_existente = load_json(os.path.join(DATA_DIR, "perfil_negocio.json"), {})
            if isinstance(perfil_existente, dict) and perfil_existente:
                supabase_guardar_json("dago_profiles", usuario, perfil_existente)

        historial_online = supabase_cargar_json("dago_histories", usuario, [])
        if not historial_online and os.path.exists(os.path.join(DATA_DIR, "historial.json")):
            historial_existente = load_json(os.path.join(DATA_DIR, "historial.json"), [])
            if isinstance(historial_existente, list):
                supabase_guardar_json("dago_histories", usuario, historial_existente)
        return

    if not os.path.exists(profile_path) and os.path.exists(os.path.join(DATA_DIR, "perfil_negocio.json")):
        perfil_existente = load_json(os.path.join(DATA_DIR, "perfil_negocio.json"), {})
        if isinstance(perfil_existente, dict) and perfil_existente:
            save_json(profile_path, perfil_existente)
    if not os.path.exists(history_path) and os.path.exists(os.path.join(DATA_DIR, "historial.json")):
        historial_existente = load_json(os.path.join(DATA_DIR, "historial.json"), [])
        if isinstance(historial_existente, list):
            save_json(history_path, historial_existente)

def cargar_perfil_usuario(usuario, profile_path):
    if supabase_activo():
        data = supabase_cargar_json("dago_profiles", usuario, {})
        return data if isinstance(data, dict) else {}
    return load_json(profile_path, {})

def guardar_perfil_usuario(usuario, profile_path, perfil):
    if supabase_activo():
        supabase_guardar_json("dago_profiles", usuario, perfil)
        return
    save_json(profile_path, perfil)

def cargar_historial_usuario(usuario, history_path):
    if supabase_activo():
        data = supabase_cargar_json("dago_histories", usuario, [])
        return data if isinstance(data, list) else []
    return load_json(history_path, [])

def guardar_historial_usuario(usuario, history_path, historial):
    if supabase_activo():
        supabase_guardar_json("dago_histories", usuario, historial)
        return
    save_json(history_path, historial)

def cerrar_sesion():
    for key in [
        "auth_user",
        "mostrar_creador",
        "crear_step",
        "ideas_sugeridas",
        "descripcion_actual",
        "descripcion_final",
        "idea_elegida_desc",
        "post_buffer",
        "data",
        "recraft_url",
        "recraft_prompt",
    ]:
        st.session_state.pop(key, None)
    st.rerun()

def render_login():
    st.markdown("""
    <div class="hero login-hero">
      <div class="brand-lockup">
        <div class="brand-mark">D</div>
        <div>
          <h1>Dago</h1>
          <p class="small">Entra o crea una cuenta para administrar tu contenido.</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_info, col_form = st.columns([0.95, 1.05], gap="large")
    with col_info:
        st.markdown("""
        <div class="home-main">
        <span class="card-kicker">Tu espacio de trabajo</span>
        <h2>Contenido separado por cuenta</h2>
        <p class="small">Cada usuario guarda su propio perfil, historial y piezas generadas. Ideal para empezar simple y luego crecer a muchos negocios.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="home-card accent-teal">
        <span class="card-kicker">Flujo</span>
        <h3>Sube una foto real</h3>
        <p>Dago usa la imagen del producto o local como base para editarla con Recraft.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        tab_login, tab_registro = st.tabs(["Iniciar sesión", "Crear cuenta"])

        with tab_login:
            with st.form("login_form"):
                usuario = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("ENTRAR", use_container_width=True)

            if submit:
                auth_user = autenticar_usuario(usuario, password)
                if auth_user:
                    st.session_state["auth_user"] = auth_user
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        with tab_registro:
            with st.form("registro_form"):
                nuevo_usuario = st.text_input("Usuario nuevo")
                nombre_negocio = st.text_input("Nombre del negocio opcional")
                nuevo_password = st.text_input("Contraseña", type="password")
                confirmar_password = st.text_input("Confirmar contraseña", type="password")
                crear = st.form_submit_button("CREAR CUENTA", use_container_width=True)

            if crear:
                if nuevo_password != confirmar_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        auth_user = crear_usuario(nuevo_usuario, nuevo_password, nombre_negocio)
                        migrar_datos_iniciales(auth_user)
                        st.session_state["auth_user"] = auth_user
                        st.success("Cuenta creada.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

def requerir_login():
    if "auth_user" not in st.session_state:
        render_login()
        st.stop()
    return st.session_state["auth_user"]

@st.cache_resource(show_spinner=False)
def crear_cliente_groq(api_key):
    return Groq(api_key=api_key)

def cliente_groq():
    api_key = leer_secreto("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Falta configurar GROQ_API_KEY en .streamlit/secrets.toml.")
    return crear_cliente_groq(api_key)

def pedir_json_ia(prompt, temperature=0.3):
    try:
        r = cliente_groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        return json.loads(r.choices[0].message.content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("La IA respondió en un formato inválido. Intenta generar de nuevo.") from exc
    except Exception as exc:
        raise RuntimeError(f"No pude conectar con la IA: {exc}") from exc

def texto_corto(valor, limite=220):
    texto = str(valor or "").strip()
    return texto[:limite].strip()

def tamano_recraft(formato_contenido):
    return "768x1344" if formato_contenido == "Historia" else "1024x1024"

def mensaje_error_recraft(response, data):
    error = data.get("error") if isinstance(data, dict) else None
    if isinstance(error, dict):
        return error.get("message") or error.get("detail") or response.text[:300]
    if error:
        return str(error)
    if isinstance(data, dict):
        return data.get("message") or data.get("detail") or response.text[:300]
    return response.text[:300]

def extension_imagen(mime):
    return {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(mime, "png")

def tamano_instagram(formato_contenido):
    return INSTAGRAM_STORY_SIZE if formato_contenido == "Historia" else INSTAGRAM_POST_SIZE

def preparar_canvas_instagram(img, formato_contenido):
    target_w, target_h = tamano_instagram(formato_contenido)
    fondo = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS)
    fitted = ImageOps.contain(img, (target_w, target_h), method=Image.Resampling.LANCZOS)

    fondo = fondo.filter(ImageFilter.GaussianBlur(22))
    sombra = Image.new("RGB", (target_w, target_h), (20, 8, 45))
    canvas = Image.blend(fondo, sombra, 0.22)

    x = (target_w - fitted.width) // 2
    y = (target_h - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas

def datos_clave_descripcion():
    campos = [
        ("Producto/servicio", st.session_state.get("promo_producto")),
        ("Precio/oferta", st.session_state.get("promo_precio")),
        ("Vigencia/fecha", st.session_state.get("promo_vigencia")),
        ("Condición/dato clave", st.session_state.get("promo_condicion")),
    ]
    lineas = []
    for etiqueta, valor in campos:
        valor = str(valor or "").strip()
        if valor:
            lineas.append(f"{etiqueta}: {valor}")
    return lineas

def descripcion_con_datos_clave(base):
    texto = str(base or "").strip()
    lineas_extra = []
    for linea in datos_clave_descripcion():
        etiqueta = linea.split(":", 1)[0]
        if etiqueta not in texto:
            lineas_extra.append(linea)
    if lineas_extra:
        return (texto + "\n" if texto else "") + "\n".join(lineas_extra)
    return texto

def asegurar_tamano_recraft(img):
    w, h_img = img.size
    escala_bajada = min(
        1,
        MAX_RECRAFT_IMAGE_SIDE / max(w, h_img),
        (MAX_RECRAFT_IMAGE_PIXELS / max(w * h_img, 1)) ** 0.5,
    )
    if escala_bajada < 1:
        nuevo_tamano = (max(1, int(w * escala_bajada)), max(1, int(h_img * escala_bajada)))
        img = img.resize(nuevo_tamano, Image.Resampling.LANCZOS)

    w, h_img = img.size
    if min(w, h_img) >= MIN_RECRAFT_IMAGE_SIDE:
        return img

    escala_subida = MIN_RECRAFT_IMAGE_SIDE / max(1, min(w, h_img))
    puede_escalar = (
        max(w, h_img) * escala_subida <= MAX_RECRAFT_IMAGE_SIDE
        and w * h_img * (escala_subida ** 2) <= MAX_RECRAFT_IMAGE_PIXELS
    )

    if puede_escalar:
        nuevo_tamano = (
            max(MIN_RECRAFT_IMAGE_SIDE, int(w * escala_subida)),
            max(MIN_RECRAFT_IMAGE_SIDE, int(h_img * escala_subida)),
        )
        return img.resize(nuevo_tamano, Image.Resampling.LANCZOS)

    canvas_w = max(w, MIN_RECRAFT_IMAGE_SIDE)
    canvas_h = max(h_img, MIN_RECRAFT_IMAGE_SIDE)
    lienzo = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    lienzo.paste(img, ((canvas_w - w) // 2, (canvas_h - h_img) // 2))
    return lienzo

def preparar_imagen_para_recraft(uploaded_file, formato_contenido):
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    try:
        with Image.open(uploaded_file) as original:
            img = ImageOps.exif_transpose(original)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            if img.mode == "RGBA":
                fondo = Image.new("RGB", img.size, (255, 255, 255))
                fondo.paste(img, mask=img.getchannel("A"))
                img = fondo
            else:
                img = img.convert("RGB")
    except Exception as exc:
        raise RuntimeError("No pude leer la foto. Sube una imagen JPG, PNG o WEBP.") from exc

    img = preparar_canvas_instagram(img, formato_contenido)
    img = asegurar_tamano_recraft(img)

    calidad = 92
    buffer = io.BytesIO()
    while True:
        buffer.seek(0)
        buffer.truncate(0)
        img.save(buffer, format="JPEG", quality=calidad, optimize=True)
        if buffer.tell() <= MAX_RECRAFT_IMAGE_BYTES or calidad <= 70:
            break
        calidad -= 6

    while buffer.tell() > MAX_RECRAFT_IMAGE_BYTES and max(img.size) > MIN_RECRAFT_IMAGE_SIDE:
        nuevo_tamano = (
            max(MIN_RECRAFT_IMAGE_SIDE, int(img.width * 0.9)),
            max(MIN_RECRAFT_IMAGE_SIDE, int(img.height * 0.9)),
        )
        if nuevo_tamano == img.size:
            break
        img = img.resize(nuevo_tamano, Image.Resampling.LANCZOS)
        img = asegurar_tamano_recraft(img)
        buffer.seek(0)
        buffer.truncate(0)
        img.save(buffer, format="JPEG", quality=76, optimize=True)

    if buffer.tell() > MAX_RECRAFT_IMAGE_BYTES:
        raise RuntimeError("La foto sigue siendo demasiado pesada para Recraft. Prueba con una imagen más liviana.")

    return {
        "bytes": buffer.getvalue(),
        "filename": "producto_dago.jpg",
        "mime": "image/jpeg",
        "size": img.size,
    }

def normalizar_salida_instagram(image_bytes, formato_contenido):
    try:
        with Image.open(io.BytesIO(image_bytes)) as original:
            img = ImageOps.exif_transpose(original).convert("RGB")
    except Exception:
        return image_bytes, "image/png"

    img = ImageOps.fit(img, tamano_instagram(formato_contenido), method=Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=94, optimize=True)
    return buffer.getvalue(), "image/jpeg"

def prompt_recraft(perfil, data, descripcion, objetivo, formato_contenido, mostrar_direccion=False, variante=0):
    visual = data.get("direccion_visual", {})
    if not isinstance(visual, dict):
        visual = {}

    rubro = texto_corto(perfil.get("rubro"), 80)
    tono = texto_corto(perfil.get("tono"), 80)
    publico = texto_corto(perfil.get("publico"), 160)
    productos = texto_corto(perfil.get("productos"), 220)
    material = texto_corto(perfil.get("material_disponible"), 220)
    direccion = texto_corto(perfil.get("direccion"), 120) if mostrar_direccion else ""

    gancho = texto_corto(data.get("gancho_visual") or data.get("titulo_post") or objetivo, 42)
    subtitulo = texto_corto(data.get("subtitulo_visual") or visual.get("texto_en_imagen"), 70)
    estilo = texto_corto(visual.get("estilo_visual"), 160)
    layout = texto_corto(visual.get("tipo_layout"), 160)
    foto_ideal = texto_corto(visual.get("foto_ideal") or data.get("idea_foto"), 220)
    colores = texto_corto(visual.get("colores_recomendados"), 120)

    formato = "vertical Instagram story 9:16" if formato_contenido == "Historia" else "square Instagram post 1:1"
    variantes = [
        "premium commercial ad, clean hierarchy, realistic product photography",
        "modern editorial social media design, bold readable headline, elegant spacing",
        "minimal high-end campaign, strong central product, refined contrast",
        "fresh local business ad, warm realistic lighting, professional Instagram finish",
    ]
    estilo_variante = variantes[variante % len(variantes)]

    direccion_linea = f'Small location text: "{direccion}"' if direccion else "No address text."
    subtitulo_linea = f'Supporting text: "{subtitulo}"' if subtitulo else "No supporting text."

    return f"""
Create a professional, publish-ready {formato} for a small Chilean business.

BUSINESS CONTEXT:
Business type: {rubro}
Brand tone: {tono}
Target audience: {publico}
Products/services: {productos}
Available visual material: {material}

CONTENT GOAL:
Objective: {objetivo}
User brief: {descripcion}

VISUAL DIRECTION:
Style: {estilo or estilo_variante}
Layout: {layout}
Ideal photo/content: {foto_ideal}
Recommended colors: {colores or "white, purple accents, clean commercial palette"}
Variant: {estilo_variante}

TEXT THAT MUST APPEAR:
Main headline: "{gancho}"
{subtitulo_linea}
{direccion_linea}

STRICT RULES:
- Use Spanish text exactly as provided above.
- Do not invent prices, discounts, schedules, stock, testimonials, events, logos or brand names.
- No fake logo.
- No watermark.
- No random extra text.
- No misspelled text.
- Make the headline large and readable.
- Keep the design clean, modern and commercial.
- Make it look like a designer-made Instagram asset ready to publish.
""".strip()

def prompt_edicion_recraft(perfil, data, descripcion, objetivo, formato_contenido, mostrar_direccion=False, variante=0):
    visual = data.get("direccion_visual", {})
    if not isinstance(visual, dict):
        visual = {}

    formato = "Instagram story 9:16" if formato_contenido == "Historia" else "Instagram square post 1:1"
    gancho = texto_corto(data.get("gancho_visual") or data.get("titulo_post") or objetivo, 38)
    subtitulo = texto_corto(data.get("subtitulo_visual") or visual.get("texto_en_imagen"), 58)
    direccion = texto_corto(perfil.get("direccion"), 80) if mostrar_direccion else ""
    estilo = texto_corto(visual.get("estilo_visual"), 90)
    rubro = texto_corto(perfil.get("rubro"), 60)
    productos = texto_corto(perfil.get("productos"), 120)
    brief = texto_corto(descripcion, 160)
    variantes = [
        "clean premium commercial ad",
        "modern editorial social media design",
        "minimal product-focused campaign",
        "fresh local business ad with warm lighting",
    ]

    prompt = f"""
Edit the uploaded real product/business photo into a professional {formato}.
Preserve the exact product, food, service and identity from the photo. Do not replace it.
Improve lighting, contrast, background, composition and commercial polish.
Business: {rubro}. Products/services: {productos}.
Goal: {objetivo}. Brief: {brief}.
Style: {estilo or variantes[variante % len(variantes)]}.
Readable Spanish headline: "{gancho}".
Supporting text: "{subtitulo}".
{f'Address text: "{direccion}".' if direccion else 'No address text.'}
Rules: no fake logo, no watermark, no random extra text, no invented prices, no fake discounts, no fake stock. If text is difficult, prioritize a clean edited product photo with space for caption.
""".strip()
    return prompt[:950]

def generar_imagen_recraft(perfil, data, descripcion, objetivo, formato_contenido, mostrar_direccion=False, variante=0):
    api_key = leer_secreto("RECRAFT_API_KEY")
    if not api_key:
        raise RuntimeError("Falta configurar RECRAFT_API_KEY en .streamlit/secrets.toml.")

    prompt = prompt_recraft(
        perfil,
        data,
        descripcion,
        objetivo,
        formato_contenido,
        mostrar_direccion=mostrar_direccion,
        variante=variante,
    )

    try:
        response = requests.post(
            RECRAFT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "model": RECRAFT_MODEL,
                "size": tamano_recraft(formato_contenido),
                "n": 1,
                "response_format": "url",
            },
            timeout=120,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"No pude conectar con Recraft: {exc}") from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        raise RuntimeError(f"Recraft rechazó la generación: {mensaje_error_recraft(response, payload)}")

    try:
        image_url = payload["data"][0]["url"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Recraft no devolvió una imagen válida.") from exc

    try:
        image_response = requests.get(image_url, timeout=120)
        image_response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Recraft generó la imagen, pero no pude descargarla: {exc}") from exc

    image_bytes, mime = normalizar_salida_instagram(image_response.content, formato_contenido)
    return image_bytes, image_url, prompt, mime

def generar_edicion_recraft(foto_info, perfil, data, descripcion, objetivo, formato_contenido, mostrar_direccion=False, variante=0, fuerza=0.35):
    api_key = leer_secreto("RECRAFT_API_KEY")
    if not api_key:
        raise RuntimeError("Falta configurar RECRAFT_API_KEY en .streamlit/secrets.toml.")

    prompt = prompt_edicion_recraft(
        perfil,
        data,
        descripcion,
        objetivo,
        formato_contenido,
        mostrar_direccion=mostrar_direccion,
        variante=variante,
    )

    try:
        response = requests.post(
            RECRAFT_IMAGE_TO_IMAGE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={
                "image": (
                    foto_info["filename"],
                    foto_info["bytes"],
                    foto_info["mime"],
                )
            },
            data={
                "prompt": prompt,
                "strength": str(fuerza),
                "n": "1",
                "model": RECRAFT_EDIT_MODEL,
                "response_format": "url",
            },
            timeout=120,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"No pude conectar con Recraft: {exc}") from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        raise RuntimeError(f"Recraft rechazó la edición: {mensaje_error_recraft(response, payload)}")

    try:
        image_url = payload["data"][0]["url"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Recraft no devolvió una imagen editada válida.") from exc

    try:
        image_response = requests.get(image_url, timeout=120)
        image_response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Recraft editó la imagen, pero no pude descargarla: {exc}") from exc

    image_bytes, mime = normalizar_salida_instagram(image_response.content, formato_contenido)
    return image_bytes, image_url, prompt, mime

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
{json.dumps(historial[-HISTORY_CONTEXT_ITEMS:], ensure_ascii=False)}

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
- Nunca digas "precio no disponible", "fecha no disponible" ni "stock no disponible". Omite ese dato.
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
- Nunca escribas "precio no disponible". Si no hay precio, simplemente no menciones precio.
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
    data = pedir_json_ia(prompt, temperature=0.28)
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("direccion_visual"), dict):
        data["direccion_visual"] = {}
    if not isinstance(data.get("hashtags"), list):
        data["hashtags"] = ["#NegocioLocal", "#Chile"]
    data["hashtags"] = [
        h if str(h).startswith("#") else "#" + str(h).replace(" ", "")
        for h in data["hashtags"]
        if str(h).strip()
    ]
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
{json.dumps(historial[-HISTORY_CONTEXT_ITEMS:], ensure_ascii=False)}

Reglas:
- 4 publicaciones máximo.
- No inventes descuentos, eventos, rifas, testimonios, antes/después, fotos de clientes ni disponibilidad si el perfil no lo menciona.
- Usa solamente servicios reales del perfil.
- Usa solamente el material disponible indicado en el perfil.
- Ideas concretas y realizables para un dueño ocupado.
- Si no hay material visual específico, propone contenido fácil: servicio destacado, recordatorio de reservas, horario, beneficios, preguntas frecuentes o promoción simple.
"""
    data = pedir_json_ia(prompt, temperature=0.4)
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("plan"), list):
        data["plan"] = []
    return data



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
{json.dumps(historial[-HISTORY_CONTEXT_ITEMS:], ensure_ascii=False)}

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
    data = pedir_json_ia(prompt, temperature=0.25)
    if not isinstance(data, dict):
        data = {}
    if "ideas" not in data or not isinstance(data["ideas"], list):
        data["ideas"] = []
    return data

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

usuario_actual = requerir_login()
PROFILE_PATH, HISTORY_PATH = rutas_usuario(usuario_actual)

perfil_guardado = cargar_perfil_usuario(usuario_actual, PROFILE_PATH)
perfil = {**perfil_default, **perfil_guardado} if isinstance(perfil_guardado, dict) else perfil_default.copy()

historial = cargar_historial_usuario(usuario_actual, HISTORY_PATH)
if not isinstance(historial, list):
    historial = []
historial = [item for item in historial if isinstance(item, dict)]

modo_datos = "Base online activa" if supabase_activo() else "Modo local"

st.markdown(f"""
<div class="hero app-hero">
  <div class="brand-lockup">
    <div class="brand-mark">D</div>
    <div class="hero-copy">
      <span class="hero-eyebrow">Dago Studio</span>
      <h1>Contenido que se ve listo para vender</h1>
      <p>Crea publicaciones e historias con foto real, texto comercial y formato Instagram en un solo flujo.</p>
    </div>
  </div>
  <div class="hero-stats">
    <div class="hero-stat">
      <b>{len(historial)}</b>
      <span>Piezas creadas</span>
    </div>
    <div class="hero-stat">
      <b>1080</b>
      <span>Formato Instagram</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

top_user_col, top_logout_col = st.columns([0.82, 0.18])
with top_user_col:
    st.markdown(f"<p class='soft-note'>Sesión activa: <b>{h(usuario_actual)}</b></p>", unsafe_allow_html=True)
with top_logout_col:
    if st.button("CERRAR SESIÓN", use_container_width=True):
        cerrar_sesion()



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

    st.markdown("## Crear contenido con Dago")

    if step < 4:
        st.markdown(f"<div class='step-badge'><span class='step-dot'></span>Paso {step} de 4</div>", unsafe_allow_html=True)

        if step == 1:
            st.markdown("<div class='big-question'>¿Qué quieres crear?</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("""
                <div class="format-tile">
                  <span>Feed</span>
                  <b>Publicacion cuadrada</b>
                  <p>Ideal para promocion, producto, anuncio o pieza que queda en el perfil. Salida 1080 x 1080.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("PUBLICACIÓN", use_container_width=True):
                    st.session_state["crear_formato"] = "Publicación"
                    st.session_state["crear_step"] = 2
                    st.rerun()
            with c2:
                st.markdown("""
                <div class="format-tile">
                  <span>Story</span>
                  <b>Historia vertical</b>
                  <p>Perfecta para urgencia, encuesta, disponibilidad o recordatorio rapido. Salida 1080 x 1920.</p>
                </div>
                """, unsafe_allow_html=True)
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

            st.markdown("<div class='step-title'>Datos clave opcionales</div>", unsafe_allow_html=True)
            st.markdown("<p class='soft-note'>Agrega precio, vigencia o condiciones para que Dago no invente nada. Puedes completarlo antes o después de pedir ideas.</p>", unsafe_allow_html=True)

            pc1, pc2 = st.columns(2)
            with pc1:
                st.text_input("Producto o servicio", key="promo_producto", placeholder="Ej: café + medialuna")
                st.text_input("Precio u oferta", key="promo_precio", placeholder="Ej: $4.500 / 2x1 / desde $10.000")
            with pc2:
                st.text_input("Vigencia, fecha u horario", key="promo_vigencia", placeholder="Ej: hasta las 10:00 / solo hoy")
                st.text_input("Condición o dato clave", key="promo_condicion", placeholder="Ej: retiro en local / pagando en efectivo")

            b1, b2 = st.columns(2)
            with b1:
                if st.button("NO SÉ QUÉ PUBLICAR", use_container_width=True):
                    if not perfil.get("nombre"):
                        st.error("Primero guarda el perfil del negocio.")
                    else:
                        with st.spinner("Buscando ideas para este negocio..."):
                            try:
                                st.session_state["ideas_sugeridas"] = generar_ideas_con_ia(
                                    perfil,
                                    formato_contenido,
                                    objetivo,
                                    historial
                                )
                                st.rerun()
                            except RuntimeError as exc:
                                st.error(str(exc))

            with b2:
                if st.button("USAR MI TEXTO", use_container_width=True):
                    base = st.session_state.get("descripcion_actual", "").strip()
                    base = descripcion_con_datos_clave(base)

                    if not base:
                        st.error("Escribe algo, pide ideas o completa algún dato clave.")
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
                            final_desc = descripcion_con_datos_clave(desc)
                            st.session_state["idea_elegida_desc"] = desc
                            st.session_state["descripcion_final"] = final_desc
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
            <b>Formato:</b> {h(formato_contenido)}<br>
            <b>Objetivo:</b> {h(objetivo)}<br>
            <b>Idea:</b> {h_lineas(descripcion)}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='step-title'>Datos comerciales</div>", unsafe_allow_html=True)
            st.markdown("<p class='soft-note'>Puedes ajustar estos datos antes de generar la imagen final.</p>", unsafe_allow_html=True)
            dc1, dc2 = st.columns(2)
            with dc1:
                st.text_input("Producto o servicio", key="promo_producto")
                st.text_input("Precio u oferta", key="promo_precio")
            with dc2:
                st.text_input("Vigencia, fecha u horario", key="promo_vigencia")
                st.text_input("Condición o dato clave", key="promo_condicion")

            st.markdown("<div class='step-title'>Foto del producto o local</div>", unsafe_allow_html=True)
            st.markdown("<p class='soft-note'>Sube una foto real. Dago la usará como base y Recraft la editará para que se vea más publicable.</p>", unsafe_allow_html=True)

            foto_producto = st.file_uploader(
                "Foto del producto o local",
                type=["jpg", "jpeg", "png", "webp"],
                label_visibility="collapsed",
                key="foto_producto_recraft"
            )

            if foto_producto:
                st.image(foto_producto, caption="Foto base para editar", use_container_width=True)

            fuerza_edicion = st.slider(
                "Cambio visual",
                min_value=0.15,
                max_value=0.75,
                value=st.session_state.get("fuerza_edicion", 0.35),
                step=0.05,
                help="Más bajo conserva más la foto original. Más alto deja que Recraft rediseñe más la escena."
            )
            st.session_state["fuerza_edicion"] = fuerza_edicion

            mostrar_dir = st.checkbox(
                "Incluir dirección en la imagen",
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
                descripcion_generacion = descripcion_con_datos_clave(descripcion)
                if not perfil.get("nombre"):
                    st.error("Primero guarda el perfil del negocio.")
                elif not descripcion_generacion.strip():
                    st.error("Escribe qué quieres comunicar.")
                elif not foto_producto:
                    st.error("Sube una foto real del producto o local para que Recraft la edite.")
                else:
                    with st.spinner("Dago está preparando tu contenido..."):
                        st.session_state["design_variant"] = 0
                        try:
                            foto_info = preparar_imagen_para_recraft(foto_producto, formato_contenido)
                            data = generar_con_ia(perfil, descripcion_generacion, objetivo, formato_contenido, historial)
                            imagen, recraft_url, recraft_prompt, post_mime = generar_edicion_recraft(
                                foto_info,
                                perfil,
                                data,
                                descripcion_generacion,
                                objetivo,
                                formato_contenido,
                                mostrar_dir,
                                st.session_state["design_variant"],
                                fuerza_edicion,
                            )
                        except RuntimeError as exc:
                            st.error(str(exc))
                            return
                        st.session_state["last_formato"] = formato_contenido
                        st.session_state["last_objetivo"] = objetivo
                        st.session_state["last_descripcion"] = descripcion_generacion
                        st.session_state["last_mostrar_direccion"] = mostrar_dir
                        st.session_state["last_foto_info"] = foto_info
                        st.session_state["last_fuerza_edicion"] = fuerza_edicion

                        st.session_state["post_buffer"] = imagen
                        st.session_state["data"] = data
                        st.session_state["recraft_url"] = recraft_url
                        st.session_state["recraft_prompt"] = recraft_prompt
                        st.session_state["post_mime"] = post_mime

                        historial.append({
                            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "formato": formato_contenido,
                            "tipo": objetivo,
                            "descripcion": descripcion_generacion,
                            "dia_recomendado": data.get("dia_recomendado",""),
                            "hora_recomendada": data.get("hora_recomendada",""),
                            "gancho": data.get("gancho_visual","")
                        })
                        del historial[:-MAX_HISTORY_ITEMS]
                        guardar_historial_usuario(usuario_actual, HISTORY_PATH, historial)

            if "post_buffer" in st.session_state:
                cbtn1, cbtn2 = st.columns(2)

                with cbtn1:
                    if st.button("REHACER EN RECRAFT", use_container_width=True):
                        st.session_state["design_variant"] = st.session_state.get("design_variant", 0) + 1
                        with st.spinner("Recraft está creando otro diseño..."):
                            try:
                                foto_info = st.session_state.get("last_foto_info")
                                if not foto_info:
                                    raise RuntimeError("Sube una foto y genera de nuevo antes de rehacer el diseño.")
                                imagen, recraft_url, recraft_prompt, post_mime = generar_edicion_recraft(
                                    foto_info,
                                    perfil,
                                    st.session_state["data"],
                                    st.session_state.get("last_descripcion", ""),
                                    st.session_state.get("last_objetivo", ""),
                                    st.session_state.get("last_formato", "Publicación"),
                                    st.session_state.get("last_mostrar_direccion", False),
                                    st.session_state["design_variant"],
                                    st.session_state.get("last_fuerza_edicion", 0.35),
                                )
                                st.session_state["post_buffer"] = imagen
                                st.session_state["recraft_url"] = recraft_url
                                st.session_state["recraft_prompt"] = recraft_prompt
                                st.session_state["post_mime"] = post_mime
                            except RuntimeError as exc:
                                st.error(str(exc))

                with cbtn2:
                    post_mime = st.session_state.get("post_mime", "image/png")
                    st.download_button(
                        "DESCARGAR",
                        data=st.session_state["post_buffer"],
                        file_name=f"contenido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension_imagen(post_mime)}",
                        mime=post_mime,
                        use_container_width=True
                    )

                st.image(st.session_state["post_buffer"], use_container_width=True)

            if "data" in st.session_state:
                data = st.session_state["data"]
                visual = data.get("direccion_visual", {})
                if not isinstance(visual, dict):
                    visual = {}
                hashtags = data.get("hashtags", [])
                if not isinstance(hashtags, list):
                    hashtags = [hashtags]

                st.markdown("### Texto principal")
                if st.session_state.get("last_formato") == "Historia":
                    st.markdown(f"<div class='card'>{h_lineas(data.get('historia_instagram',''))}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='card'>{h_lineas(data.get('caption_instagram',''))}</div>", unsafe_allow_html=True)

                st.markdown("### WhatsApp")
                st.markdown(f"<div class='card'>{h_lineas(data.get('mensaje_whatsapp',''))}</div>", unsafe_allow_html=True)

                st.markdown("### Dirección visual sugerida")
                st.markdown(f"""
                <div class="purple">
                <b>Foto ideal:</b> {h_lineas(visual.get('foto_ideal',''))}<br>
                <b>Layout:</b> {h_lineas(visual.get('tipo_layout',''))}<br>
                <b>Texto:</b> {h_lineas(visual.get('texto_en_imagen',''))}<br>
                <b>Evitar:</b> {h_lineas(visual.get('que_evitar',''))}<br>
                <b>Idea foto:</b> {h_lineas(data.get('idea_foto',''))}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### Cuándo subirlo")
                st.markdown(f"<div class='card'><b>{h(data.get('dia_recomendado',''))}</b> a las <b>{h(data.get('hora_recomendada',''))}</b><br>{h_lineas(data.get('motivo_horario',''))}</div>", unsafe_allow_html=True)

                st.markdown("### Hashtags")
                st.markdown(f"<div class='card'>{h(' '.join(str(tag) for tag in hashtags))}</div>", unsafe_allow_html=True)



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
        st.markdown("""
        <div class="section-title">
          <span>Panel de control</span>
          <h2>Tu estudio de contenido</h2>
        </div>
        """, unsafe_allow_html=True)

        if perfil.get("nombre"):
            negocio = perfil.get("nombre")
            rubro = perfil.get("rubro")
            tono = perfil.get("tono")

            st.markdown(f"""
            <div class="home-main">
            <span class="card-kicker">Negocio activo</span>
            <h2>Hola, {h(negocio)}</h2>
            <div class="chip-row">
              <span>{h(rubro)}</span>
              <span>Tono {h(tono)}</span>
              <span>{len(historial)} piezas</span>
            </div>
            <p class="small">Dago está listo para crear contenido para tu {h(str(rubro).lower())} con tono {h(str(tono).lower())}.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="home-main">
            <span class="card-kicker">Primer paso</span>
            <h2>Configura tu negocio</h2>
            <p class="small">Completa el perfil para que Dago pueda crear ideas, publicaciones e historias personalizadas.</p>
            </div>
            """, unsafe_allow_html=True)

        cta1, cta2 = st.columns([1,1])

        with cta1:
            st.markdown("""
            <div class="studio-card studio-primary">
            <span>Creacion rapida</span>
            <b>Crear una pieza nueva</b>
            <span>Sube una foto real, define el objetivo y deja que Dago prepare texto + edición visual.</span>
            </div>
            """, unsafe_allow_html=True)
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
            st.markdown("""
            <div class="studio-card studio-secondary">
            <span>Planificacion</span>
            <b>Ordenar la semana</b>
            <span>Genera una guía simple de qué publicar, cuándo hacerlo y con qué intención.</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("GENERAR PLAN SEMANAL", use_container_width=True):
                if not perfil.get("nombre"):
                    st.error("Primero guarda el perfil.")
                else:
                    with st.spinner("Preparando plan semanal..."):
                        try:
                            st.session_state["plan"] = generar_plan_semanal(perfil, historial)
                        except RuntimeError as exc:
                            st.error(str(exc))

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="home-card accent-teal">
            <span class="card-kicker">Calendario</span>
            <h3>Próxima idea</h3>
            <p>{h_lineas(perfil.get('dias_publicacion','Define tus días'))}</p>
            <span class="metric-value">{h(perfil.get('horario_preferido','19:00'))}</span>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="home-card accent-amber">
            <span class="card-kicker">Historial</span>
            <h3>Contenido creado</h3>
            <span class="metric-value">{len(historial)}</span>
            <p>piezas guardadas</p>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            ultima = historial[-1].get("gancho", "Aún no hay ideas") if historial else "Aún no hay ideas"
            st.markdown(f"""
            <div class="home-card accent-rose">
            <span class="card-kicker">Último resultado</span>
            <h3>Última idea</h3>
            <p>{h_lineas(ultima)}</p>
            </div>
            """, unsafe_allow_html=True)

        if "plan" in st.session_state:
            plan = st.session_state["plan"]
            st.markdown("## Plan recomendado")
            st.markdown(f"""
            <div class="home-main">
            <b>{h_lineas(plan.get('resumen',''))}</b><br>
            <span class="small">{h_lineas(plan.get('recomendacion_general',''))}</span>
            </div>
            """, unsafe_allow_html=True)

            for item in plan.get("plan", []):
                st.markdown(f"""
                <div class="home-card">
                <b>{h(item.get('dia'))} · {h(item.get('hora'))}</b><br>
                <b>{h(item.get('tipo'))}</b>: {h_lineas(item.get('idea'))}<br>
                <span class="small">{h_lineas(item.get('objetivo'))}</span>
                </div>
                """, unsafe_allow_html=True)


with tab_perfil:
    st.markdown("## Perfil único del negocio")
    st.markdown("""
    <div class="profile-banner">
      <b>Datos que hacen que Dago no invente</b>
      <p>Mientras mas claro este el rubro, publico, servicios y horarios, mejores salen las ideas, captions e imagenes.</p>
    </div>
    """, unsafe_allow_html=True)
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
        guardar_perfil_usuario(usuario_actual, PROFILE_PATH, perfil)
        st.success("Perfil guardado.")

with tab_historial:
    st.markdown("## Calendario / historial")
    if not historial:
        st.info("Todavía no hay publicaciones creadas.")
    else:
        for item in reversed(historial[-20:]):
            st.markdown(f"<div class='card'><b>{h(item.get('tipo'))}</b> · {h(item.get('fecha_creacion'))}<br><b>Idea:</b> {h_lineas(item.get('descripcion'))}<br><b>Publicar:</b> {h(item.get('dia_recomendado'))} {h(item.get('hora_recomendada'))}<br><b>Gancho:</b> {h_lineas(item.get('gancho'))}</div>", unsafe_allow_html=True)
