"""
All bot-facing text lives here, keyed by language code.
Add new languages by adding a new top-level dict entry with the same keys.
"""
from config import DEFAULT_LANGUAGE

MESSAGES = {
    "en": {
        "choose_language_title": "🌐 Choose your language",
        "choose_language_body": "Tap a button below. You can change this later with /language.",
        "language_set": "✅ Language set to {language}.",
        "main_menu_title": "Main menu:",
        "settings_title": "⚙️ Output settings",
        "balance_title": "💰 Your Balance",
        "balance_body": "Credits: {credits}\n\nEach job costs 1 credit. Tap Top Up to add more.",
        "topup_title": "📦 Pick a package to top up",
        "topup_body": "Tap one to continue. You'll get payment account details next.",
        "no_jobs": "📭 You don't have any completed jobs in the last {hours}h to show.",
        "help_title": "📖 Available Commands",
        "cancelled": "❌ Cancelled.",
        "not_wired": "🔧 This action isn't wired up yet — plug in your handler logic here.",
        # --- ID grouping flow ---
        "group_start": "📷 Send a clear photo of the ID's FRONT side.",
        "group_got_front": "✅ Front received. Now send the BACK side.",
        "group_got_back_processing": "⚙️ Got both sides — enhancing and laying out your A4 sheet…",
        "group_pair_done": "✅ Pair {n} saved.",
        "group_done": "✅ Done! Here's your grouped A4 output ({credits} credits left).",
        "group_no_credits": "⛔ You're out of credits. Tap Top Up to add more before continuing.",
        "group_add_another": "Send the next ID's front photo, or tap Done to generate the sheet now.",
        "group_max_pairs": "📄 This sheet is full ({max} pairs). Tap Done to generate it.",
        "not_a_photo": "🤔 I was expecting a photo here. Send an image, or /cancel to stop.",
        "smart_import_start": "📷 Send a photo, screenshot, or PDF and I'll read it automatically.",
        "smart_import_result": "📝 Detected text:\n\n{text}",
        "smart_import_empty": "📝 I couldn't detect any readable text in that file.",
        "pdf_pages_found": "📄 Found {count} page(s) in that PDF — processing the first one.",
        # --- Payments / proof ---
        "topup_account_details": (
            "💎 <b>Top Up: {credits} Credits</b>\n"
            "💰 <b>Amount: {price} {currency}</b>\n\n"
            "<b>Choose a payment method and send the money:</b>\n\n"
            "📱 <b>Telebirr</b>\n"
            "Name: {telebirr_name}\n"
            "Number: <code>{telebirr_number}</code>\n\n"
            "🏦 <b>CBE Bank</b>\n"
            "Name: {cbe_name}\n"
            "Account: <code>{cbe_account}</code>\n\n"
            "👉 After paying, send a <b>screenshot</b> or the <b>transaction ID</b> below."
        ),
        "proof_forwarded": "✅ Proof sent to the admin for review. You'll be notified once it's approved.",
        "proof_not_awaiting": "ℹ️ You don't have a pending top-up. Tap Top Up first.",
        "payment_approved_user": "🎉 Your top-up of {credits} credits was approved! New balance: {balance}.",
        "payment_rejected_user": "❌ Your top-up request was rejected. Please contact support or resend valid proof.",
        "payment_admin_caption": (
            "💳 Payment proof from user {user_id}\n"
            "Package: {credits} credits — {price} {currency}\n"
            "Request #{request_id}"
        ),
        "payment_already_resolved": "This request was already {status}.",
        # --- Admin ---
        "admin_stats": (
            "📈 <b>Stats</b>\n\n"
            "Users: {users}\n"
            "Credits outstanding: {credits_outstanding}\n"
            "Jobs processed: {jobs_processed}\n"
            "Pending payments: {pending_payments}"
        ),
        "admin_broadcast_prompt": "📣 Send the message you want to broadcast to all users, or /cancel.",
        "admin_broadcast_done": "✅ Broadcast sent to {sent}/{total} users.",
        "admin_lookup_prompt": "🔍 Send the numeric Telegram user ID to look up, or /cancel.",
        "admin_lookup_not_found": "No record for user {user_id} yet.",
        "admin_lookup_result": (
            "👤 <b>User {user_id}</b>\n"
            "Credits: {credits}\n"
            "Language: {lang}\n"
            "Admin: {is_admin}\n"
            "Settings: {settings}"
        ),
        # --- Generate ID flow ---
        "gen_ask_portrait": "🪪 Let's generate a new ID card. Send a clear portrait photo to start.",
        "gen_ask_name_amh": "✍️ Send the full name in Amharic.",
        "gen_ask_name_eng": "✍️ Now send the full name in English.",
        "gen_ask_fan": "🔢 Send the FAN (numbers only).",
        "gen_ask_fin": "🔢 Send the FIN (numbers only).",
        "gen_ask_phone": "📞 Send the phone number.",
        "gen_ask_address": "🏠 Send the address.",
        "gen_digits_only": "🤔 That should be numbers only. Try again, or /cancel to stop.",
        "gen_text_only": "🤔 I was expecting text here. Try again, or /cancel to stop.",
        "gen_processing": "⚙️ Generating your ID card and laying it out for print…",
        "gen_done": "✅ Done! Here's your generated ID ({credits} credits left).",
        "gen_template_missing": (
            "⚠️ The blank ID templates (templates/front_blank.png / "
            "back_blank.png) aren't set up on this bot yet — contact the admin."
        ),
    },
    "am": {
        "choose_language_title": "🌐 ቋንቋን ይምረጡ",
        "choose_language_body": "ከታች ካሉት አንዱን ይምረጡ። በኋላ ላይ በ /language ትዕዛዝ መቀየር ይችላሉ።",
        "language_set": "✅ ቋንቋ ወደ {language} ተቀናብሯል።",
        "main_menu_title": "ዋና ማውጫ:",
        "settings_title": "⚙️ የውጤት ቅንብሮች",
        "balance_title": "💰 ቀሪ ሂሳብዎ",
        "balance_body": "ክሬዲት፦ {credits}\n\nእያንዳንዱ ስራ 1 ክሬዲት ያስከፍላል። ተጨማሪ ለመጨመር Top Up ይንኩ።",
        "topup_title": "📦 ጥቅል ይምረጡ",
        "topup_body": "ለመቀጠል አንዱን ይንኩ። ቀጥሎ የክፍያ አካውንት ዝርዝር ይላክልዎታል።",
        "no_jobs": "📭 ባለፉት {hours} ሰዓታት ውስጥ የተጠናቀቁ ስራዎች የሉዎትም።",
        "help_title": "📖 የሚገኙ ትዕዛዞች",
        "cancelled": "❌ ተሰርዟል።",
        "not_wired": "🔧 ይህ እርምጃ ገና አልተገናኘም — እዚህ ላይ የራስዎን ሎጂክ ያክሉ።",
        "group_start": "📷 የመታወቂያውን የፊት ገፅ ግልጽ ፎቶ ይላኩ።",
        "group_got_front": "✅ የፊት ገፅ ደርሷል። አሁን የኋላ ገፅን ይላኩ።",
        "group_got_back_processing": "⚙️ ሁለቱም ገፆች ደርሰዋል — የA4 ገፅ በማዘጋጀት ላይ…",
        "group_pair_done": "✅ ጥንድ {n} ተቀምጧል።",
        "group_done": "✅ ተጠናቅቋል! የ A4 ውጤትዎ ይኸውና ({credits} ክሬዲት ቀርቷል)።",
        "group_no_credits": "⛔ ክሬዲት አልቆብዎታል። ከመቀጠልዎ በፊት Top Up ይንኩ።",
        "group_add_another": "ቀጣዩን መታወቂያ የፊት ፎቶ ይላኩ፣ ወይም አሁኑኑ ገፅ ለማዘጋጀት Done ይንኩ።",
        "group_max_pairs": "📄 ይህ ገፅ ሞልቷል ({max} ጥንዶች)። ለማዘጋጀት Done ይንኩ።",
        "not_a_photo": "🤔 እዚህ ፎቶ ጠብቄ ነበር። ምስል ይላኩ፣ ወይም ለማቆም /cancel ይላኩ።",
        "smart_import_start": "📷 ፎቶ፣ screenshot ወይም PDF ይላኩ በራስ-ሰር አነባለሁ።",
        "smart_import_result": "📝 የተገኘ ጽሁፍ፦\n\n{text}",
        "smart_import_empty": "📝 በዚያ ፋይል ውስጥ ሊነበብ የሚችል ጽሁፍ አላገኘሁም።",
        "pdf_pages_found": "📄 በዚያ PDF ውስጥ {count} ገፅ(ች) ተገኝቷል — የመጀመሪያውን በማስኬድ ላይ።",
        "topup_account_details": (
            "💎 <b>Top Up: {credits} ክሬዲት</b>\n"
            "💰 <b>መጠን: {price} {currency}</b>\n\n"
            "<b>የክፍያ መንገድ ይምረጡና ይክፈሉ፦</b>\n\n"
            "📱 <b>ቴሌብር</b>\n"
            "ስም: {telebirr_name}\n"
            "ቁጥር: <code>{telebirr_number}</code>\n\n"
            "🏦 <b>የኢትዮጵያ ንግድ ባንክ</b>\n"
            "ስም: {cbe_name}\n"
            "አካውንት: <code>{cbe_account}</code>\n\n"
            "👉 ከከፈሉ በኋላ የክፍያ <b>screenshot</b> ወይም <b>transaction ID</b> ይላኩ።"
        ),
        "proof_forwarded": "✅ ማረጋገጫው ለአስተዳዳሪ ተልኳል። ሲፀድቅ ይነገርዎታል።",
        "proof_not_awaiting": "ℹ️ የሚጠባበቅ Top Up የለዎትም። መጀመሪያ Top Up ይንኩ።",
        "payment_approved_user": "🎉 የ{credits} ክሬዲት Top Up ጥያቄዎ ተፅድቋል! አዲስ ቀሪ ሂሳብ: {balance}።",
        "payment_rejected_user": "❌ የ Top Up ጥያቄዎ ውድቅ ተደርጓል። እባክዎ ድጋፍ ያግኙ ወይም ትክክለኛ ማረጋገጫ እንደገና ይላኩ።",
        "payment_admin_caption": (
            "💳 ከተጠቃሚ {user_id} የተላከ የክፍያ ማረጋገጫ\n"
            "ጥቅል: {credits} ክሬዲት — {price} {currency}\n"
            "ጥያቄ #{request_id}"
        ),
        "payment_already_resolved": "ይህ ጥያቄ አስቀድሞ {status} ነው።",
        "admin_stats": (
            "📈 <b>ስታትስቲክስ</b>\n\n"
            "ተጠቃሚዎች: {users}\n"
            "ያልተጠቀሙ ክሬዲቶች: {credits_outstanding}\n"
            "የተጠናቀቁ ስራዎች: {jobs_processed}\n"
            "በመጠባበቅ ላይ ያሉ ክፍያዎች: {pending_payments}"
        ),
        "admin_broadcast_prompt": "📣 ለሁሉም ተጠቃሚዎች መላክ የሚፈልጉትን መልእክት ይላኩ፣ ወይም /cancel።",
        "admin_broadcast_done": "✅ መልእክቱ ለ{sent}/{total} ተጠቃሚዎች ተልኳል።",
        "admin_lookup_prompt": "🔍 መፈለግ የሚፈልጉትን ቁጥር Telegram user ID ይላኩ፣ ወይም /cancel።",
        "admin_lookup_not_found": "ለተጠቃሚ {user_id} ገና ምንም መዝገብ የለም።",
        "admin_lookup_result": (
            "👤 <b>ተጠቃሚ {user_id}</b>\n"
            "ክሬዲት: {credits}\n"
            "ቋንቋ: {lang}\n"
            "አስተዳዳሪ: {is_admin}\n"
            "ቅንብሮች: {settings}"
        ),
    },
    "om": {
        "choose_language_title": "🌐 Afaan keessan filadhaa",
        "choose_language_body": "Filannoowwan armaan gadii keessaa tokko tuqaa. Booda ajaja /language fayyadamuun jijjiiruu dandeessu.",
        "language_set": "✅ Afaan gara {language} jijjiirameera.",
        "main_menu_title": "Menu guddaa:",
        "settings_title": "⚙️ Qindaayina bay'insaa",
        "balance_title": "💰 Baalaansii keessan",
        "balance_body": "Krediitii: {credits}\n\nHojiin tokkoon tokkoon krediitii 1 fudhata. Dabalata argachuuf Top Up tuqaa.",
        "topup_title": "📦 Paakeejii filadhaa",
        "topup_body": "Itti fufuuf tokko tuqaa. Itti aansuudhaan odeeffannoo akkaawuntii kaffaltii argattu.",
        "no_jobs": "📭 Sa'aatii {hours} keessatti hojii xumurame hin qabdan.",
        "help_title": "📖 Ajajawwan jiran",
        "cancelled": "❌ Haqameera.",
        "not_wired": "🔧 Gochi kun ammatti hin qindoofne — logic keessan asitti dabalaa.",
        "group_start": "📷 Suuraa fuula duraa ID keessanii ergaa.",
        "group_got_front": "✅ Fuulli duraa argameera. Amma fuula duubaa ergaa.",
        "group_got_back_processing": "⚙️ Fuulli lachanuu argameera — ergaa A4 qopheessaa jira…",
        "group_pair_done": "✅ Lakkoofsa {n} olkaa'ameera.",
        "group_done": "✅ Xumurameera! Kunoo ergaa A4 keessan ({credits} krediitii hafe).",
        "group_no_credits": "⛔ Krediitiin isin dhumeera. Itti fufuu dura Top Up tuqaa.",
        "group_add_another": "Suuraa fuula duraa ID itti aanu ergaa, yookaan ergaa amma qopheessuuf Done tuqaa.",
        "group_max_pairs": "📄 Ergaan kun guuteera (lakkoobsa {max}). Qopheessuuf Done tuqaa.",
        "not_a_photo": "🤔 Asitti suuraan eegamaa ture. Suuraa ergaa, yookaan dhaabuuf /cancel ergaa.",
        "smart_import_start": "📷 Suuraa, screenshot, yookaan PDF ergaa; ofumaan nan dubbisa.",
        "smart_import_result": "📝 Barreeffama argame:\n\n{text}",
        "smart_import_empty": "📝 Faayilii sana keessatti barreeffama dubbifamu hin argine.",
        "pdf_pages_found": "📄 PDF sana keessatti fuula {count} argameera — isa jalqabaa adeemsisaa jira.",
        "topup_account_details": (
            "💎 <b>Top Up: Krediitii {credits}</b>\n"
            "💰 <b>Hanga: {price} {currency}</b>\n\n"
            "<b>Mala kaffaltii filadhaa kaffalaa:</b>\n\n"
            "📱 <b>Telebirr</b>\n"
            "Maqaa: {telebirr_name}\n"
            "Lakkoofsa: <code>{telebirr_number}</code>\n\n"
            "🏦 <b>Baankii CBE</b>\n"
            "Maqaa: {cbe_name}\n"
            "Akkaawuntii: <code>{cbe_account}</code>\n\n"
            "👉 Erga kaffaltanii booda screenshot yookaan transaction ID ergaa."
        ),
        "proof_forwarded": "✅ Ragaan gara admin-itti ergameera. Yeroo mirkanaa'utti ni beeksifamtu.",
        "proof_not_awaiting": "ℹ️ Top Up eegamu hin qabdan. Duraan dursa Top Up tuqaa.",
        "payment_approved_user": "🎉 Gaaffiin Top Up krediitii {credits} mirkanaa'eera! Baalaansii haaraa: {balance}።",
        "payment_rejected_user": "❌ Gaaffiin Top Up keessan didameera. Deeggarsa qunnamaa yookaan ragaa sirrii ergaa.",
        "payment_admin_caption": (
            "💳 Ragaa kaffaltii fayyadamaa {user_id} irraa\n"
            "Paakeejii: krediitii {credits} — {price} {currency}\n"
            "Gaaffii #{request_id}"
        ),
        "payment_already_resolved": "Gaaffiin kun duraan {status} ta'eera.",
        "admin_stats": (
            "📈 <b>Istaatistiksii</b>\n\n"
            "Fayyadamtoota: {users}\n"
            "Krediitii hafe: {credits_outstanding}\n"
            "Hojii xumurame: {jobs_processed}\n"
            "Kaffaltii eegamaa jiru: {pending_payments}"
        ),
        "admin_broadcast_prompt": "📣 Ergaa fayyadamtoota hundaaf ergamu barreessaa, yookaan /cancel.",
        "admin_broadcast_done": "✅ Ergaan fayyadamtoota {sent}/{total} f ergameera.",
        "admin_lookup_prompt": "🔍 Lakkoofsa ID Telegram barbaaddan ergaa, yookaan /cancel.",
        "admin_lookup_not_found": "Fayyadamaa {user_id} irratti galmeen hin jiru.",
        "admin_lookup_result": (
            "👤 <b>Fayyadamaa {user_id}</b>\n"
            "Krediitii: {credits}\n"
            "Afaan: {lang}\n"
            "Admin: {is_admin}\n"
            "Qindaayina: {settings}"
        ),
    },
}


def t(user_id_lang: str, key: str, **kwargs) -> str:
    """
    Translate a message key into the given language, falling back to
    DEFAULT_LANGUAGE, then to the key itself if nothing is found.
    """
    lang = user_id_lang if user_id_lang in MESSAGES else DEFAULT_LANGUAGE
    template = MESSAGES.get(lang, {}).get(key) or MESSAGES[DEFAULT_LANGUAGE].get(key, key)
    return template.format(**kwargs) if kwargs else template
