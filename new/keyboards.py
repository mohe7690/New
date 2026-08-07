"""
Telegram inline/reply keyboard layouts.
Pure UI — no business logic. Callback_data strings are the contract your
handlers listen for; keep them short and stable.
"""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import SUPPORTED_LANGUAGES, CREDIT_PACKAGES, OUTPUT_FORMATS, COLOR_MODES


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in SUPPORTED_LANGUAGES.items():
        builder.button(text=label, callback_data=f"lang:{code}")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Core ID-processing actions
    builder.button(text="🪪 Group ID to A4", callback_data="group_start")
    builder.button(text="📷 Smart Import", callback_data="smart_import")
    builder.button(text="📁 Bulk Upload", callback_data="bulk_upload")
    builder.button(text="🖨️ Print Style", callback_data="print_style")
    builder.button(text="🆕 Generate ID", callback_data="generate_id")
    # Account actions
    builder.button(text="💰 Balance", callback_data="balance")
    builder.button(text="📦 Top Up", callback_data="topup")
    builder.button(text="📊 My Jobs", callback_data="jobs")
    builder.button(text="⚙️ Settings", callback_data="settings")
    builder.button(text="✨ Features", callback_data="features")
    builder.button(text="❓ Help", callback_data="help")
    rows = [2, 2, 2, 2, 2, 1]

    if is_admin:
        builder.button(text="🛠️ Admin panel", callback_data="admin")
        rows.append(1)

    builder.adjust(*rows)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancel", callback_data="cancel")
    return builder.as_markup()


def topup_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pkg in CREDIT_PACKAGES:
        label = f"{pkg['credits']} credits — {pkg['price']} {pkg['currency']}"
        if "was" in pkg:
            label += f" (was {pkg['was']} {pkg['currency']})"
        builder.button(text=label, callback_data=f"topup:{pkg['id']}")
    builder.adjust(1)
    return builder.as_markup()


def balance_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Top Up", callback_data="topup")
    builder.button(text="📊 My Jobs", callback_data="jobs")
    builder.adjust(1)
    return builder.as_markup()


def settings_keyboard(current: dict) -> InlineKeyboardMarkup:
    """`current` = db.get_settings(user_id), so toggles reflect ON/OFF state."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"🪞 Mirror back layout — {'ON' if current.get('mirror_layout') else 'OFF'}",
        callback_data="settings:mirror_layout",
    )
    builder.button(
        text=f"📐 Fit to size — {'ON' if current.get('fit_to_size') else 'OFF'}",
        callback_data="settings:fit_to_size",
    )
    builder.button(
        text=f"🔳 Regenerate QR — {'ON' if current.get('regenerate_qr') else 'OFF'}",
        callback_data="settings:regenerate_qr",
    )

    for fmt in OUTPUT_FORMATS:
        mark = "✅ " if current.get("file_type") == fmt else ""
        builder.button(text=f"{mark}{fmt}", callback_data=f"settings:format:{fmt}")

    for mode in COLOR_MODES:
        mark = "✅ " if current.get("color_mode") == mode else ""
        builder.button(text=f"{mark}{mode}", callback_data=f"settings:color:{mode}")

    builder.button(text="🌐 Change language", callback_data="settings:language")

    builder.adjust(1, 1, 1, len(OUTPUT_FORMATS), len(COLOR_MODES), 1)
    return builder.as_markup()


def help_keyboard(commands: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """`commands` = list of (label, /command) tuples, rendered as a list."""
    builder = InlineKeyboardBuilder()
    for label, cmd in commands:
        builder.button(text=f"{label}  {cmd}", callback_data=f"noop:{cmd}")
    builder.adjust(1)
    return builder.as_markup()


# --- Feature list UI ---------------------------------------------------------
def features_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Bulk Upload", callback_data="feature:bulk_upload")
    builder.button(text="🗂️ Grouped Layout", callback_data="feature:grouped_layout")
    builder.button(text="🖨️ One-Click Output", callback_data="feature:one_click_output")
    builder.button(text="🎨 Light & Dark Output", callback_data="feature:color_modes")
    builder.button(text="📷 Smart Import", callback_data="feature:smart_import")
    builder.button(text="✨ Auto Enhance", callback_data="feature:auto_enhance")
    builder.adjust(1)
    return builder.as_markup()


def feature_detail_keyboard(key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Get Started", callback_data=f"feature_start:{key}")
    builder.button(text="◀️ Back to features", callback_data="features")
    builder.adjust(1)
    return builder.as_markup()


def print_style_keyboard(selected: str = "color") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    mark_color = "✅ " if selected == "color" else ""
    mark_bw = "✅ " if selected == "bw" else ""
    builder.button(text=f"{mark_color}🌈 Full Color", callback_data="print_style:color")
    builder.button(text=f"{mark_bw}⬛ Black & White", callback_data="print_style:bw")
    builder.adjust(2)
    return builder.as_markup()


def bulk_upload_keyboard() -> InlineKeyboardMarkup:
    """Buttons shown while a bulk-upload batch of ID pairs is being collected."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Done — generate sheet", callback_data="bulk:done")
    builder.button(text="❌ Cancel", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


# --- Payment proof (admin approval) ------------------------------------------
def payment_approval_keyboard(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Approve", callback_data=f"pay_approve:{request_id}")
    builder.button(text="❌ Reject", callback_data=f"pay_reject:{request_id}")
    builder.adjust(2)
    return builder.as_markup()


# --- Admin menu ---------------------------------------------------------------
def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📣 Broadcast", callback_data="admin:broadcast")
    builder.button(text="🔍 User lookup", callback_data="admin:user_lookup")
    builder.button(text="📈 Stats", callback_data="admin:stats")
    builder.button(text="🛡️ Manage admins", callback_data="admin:manage_admins")
    builder.button(text="🩺 System status", callback_data="admin:system_status")
    builder.button(text="◀️ Back to main menu", callback_data="menu")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def admin_detail_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Back to admin panel", callback_data="admin")
    builder.adjust(1)
    return builder.as_markup()
