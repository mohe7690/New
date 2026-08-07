"""
Central, hard-coded settings & constants.
Keep every 'magic value' here so nothing is scattered across handlers.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", os.getenv("TOKEN", ""))

# --- Roles / access control --------------------------------------------
# Telegram numeric user IDs allowed to see the admin menu. Populate via
# .env (comma-separated) so you don't hard-code IDs into source control.
# ADMIN_ID (singular, from the old Ggg bot) is also honored for convenience.
ADMIN_IDS = {
    int(uid) for uid in os.getenv("ADMIN_IDS", "").split(",") if uid.strip().isdigit()
}
if os.getenv("ADMIN_ID", "").strip().isdigit():
    ADMIN_IDS.add(int(os.getenv("ADMIN_ID")))

# --- Languages -------------------------------------------------------------
SUPPORTED_LANGUAGES = {
    "en": "English",
    "am": "አማርኛ",
    "om": "Afaan Oromoo",
}
DEFAULT_LANGUAGE = "en"

# --- Credit / top-up packages ------------------------------------------------
# (credits, price, currency, optional discount label)
CREDIT_PACKAGES = [
    {"id": "pkg_9", "credits": 9, "price": 200, "currency": "ETB"},
    {"id": "pkg_23", "credits": 23, "price": 500, "currency": "ETB"},
    {"id": "pkg_50", "credits": 50, "price": 900, "currency": "ETB", "was": 1000},
    {"id": "pkg_110", "credits": 110, "price": 2000, "currency": "ETB"},
    {"id": "pkg_170", "credits": 170, "price": 3000, "currency": "ETB"},
    {"id": "pkg_300", "credits": 300, "price": 5000, "currency": "ETB"},
    {"id": "pkg_630", "credits": 630, "price": 10000, "currency": "ETB"},
]

# --- Manual payment accounts (screenshot / TX-ID proof flow) ---------------
# Filled from .env so real account details never live in source control.
TELEBIRR_NAME = os.getenv("TELEBIRR_NAME", "")
TELEBIRR_NUMBER = os.getenv("TELEBIRR_NUMBER", "")
CBE_NAME = os.getenv("CBE_NAME", "")
CBE_ACCOUNT = os.getenv("CBE_ACCOUNT", os.getenv("CBE_ACC", ""))

# New users start with a couple of free credits so they can try the bot.
SIGNUP_BONUS_CREDITS = int(os.getenv("SIGNUP_BONUS_CREDITS", "2"))

# --- Output settings toggles -------------------------------------------------
OUTPUT_FORMATS = ["JPEG", "PNG", "PDF"]
COLOR_MODES = ["Both", "Color only", "B&W only"]

# --- Generic feature list (labels only for nav; real logic lives in handlers)
FEATURES = {
    "bulk_upload": {
        "title": "📁 Bulk Upload",
        "body": "Upload multiple ID pairs at once and group them together on one A4 sheet.",
    },
    "grouped_layout": {
        "title": "🗂️ Grouped Layout",
        "body": "Front + mirrored back of your ID(s) arranged on a single A4 page with cut/fold guides.",
    },
    "one_click_output": {
        "title": "🖨️ One-Click Output",
        "body": "Generate the final JPEG/PNG/PDF with a single tap once your pages are collected.",
    },
    "color_modes": {
        "title": "🎨 Light & Dark Output",
        "body": "Choose full color or black & white output in Settings.",
    },
    "smart_import": {
        "title": "📷 Smart Import",
        "body": "Send a photo, screenshot, or PDF and the bot reads it automatically (OCR, Amharic + English).",
    },
    "auto_enhance": {
        "title": "✨ Auto Enhance",
        "body": "Automatically straightens, sharpens and cleans up every imported image.",
    },
}

# Image processing ------------------------------------------------------------
CANVAS_SIZE_A4 = (2480, 3508)   # 300dpi A4
ID_CARD_SIZE = (1012, 638)
OCR_LANGS = "amh+eng"
TESSDATA_DIR = os.path.join(os.path.dirname(__file__), "tessdata")
FONT_AMHARIC = os.path.join(os.path.dirname(__file__), "templates", "nyala.ttf")
FONT_LATIN = os.path.join(os.path.dirname(__file__), "templates", "roboto.ttf")

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")

# Number of items in the template gallery (UI-only placeholder count).
TEMPLATE_GALLERY_SIZE = 12

# Max ID pairs grouped onto a single A4 sheet (matches the physical layout).
MAX_PAIRS_PER_SHEET = 3

# --- Admin menu entries -----------------------------------------------------
ADMIN_ACTIONS = {
    "broadcast": {"title": "📣 Broadcast", "body": "Send a message to all users."},
    "user_lookup": {"title": "🔍 User lookup", "body": "Look up a user by ID."},
    "stats": {"title": "📈 Stats", "body": "View usage stats and totals."},
    "manage_admins": {"title": "🛡️ Manage admins", "body": "Add or remove admin users."},
    "system_status": {"title": "🩺 System status", "body": "Check bot/service health."},
}

# --- Misc ---------------------------------------------------------------
JOBS_HISTORY_WINDOW_HOURS = 72
