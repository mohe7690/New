# ID Converter Bot (merged)

This is `Fbot` (a clean aiogram 3.x skeleton — menus, i18n, credits, admin
panel) and `Ggg` (a rougher prototype with the actual ID-scanning logic —
Tesseract OCR, PyMuPDF, image layout, manual payment-proof flow) combined
into one working bot. Fbot supplied the architecture; Ggg's real feature
code was ported in and wired up in place of the old "not wired yet" stubs.

## What actually works now

- **Group ID → A4** (`🪪 Group ID to A4` / `/group`): send an ID's front
  photo, then its back — the bot auto-enhances both, mirrors the back, and
  lays them out on a print-ready A4 sheet with cut/fold guides (ported from
  `Ggg/processor.py`). Works in bulk for up to `MAX_PAIRS_PER_SHEET` (3)
  ID pairs on one sheet — send another front to keep going, or tap **Done**.
- **Smart Import** (`📷 Smart Import`): send a photo, screenshot, or PDF and
  the bot OCRs it with Tesseract (Amharic + English, using the trained data
  copied from `Ggg/tesserdata/`) and replies with the detected text.
- **Settings**: mirror layout, fit-to-size, QR regeneration, output format
  (JPEG/PNG/PDF), and color mode (Full color / B&W), all persisted per user.
- **Manual top-up**: pick a credit package → bot shows Telebirr/CBE account
  details from `.env` → user sends a screenshot or transaction ID → it's
  forwarded to every admin with **Approve/Reject** buttons → approving
  credits the user's account and notifies them (ported from `Ggg/Handlers.py`
  and `Ggg/main1.py`, which had this half-written and never wired in).
- **Admin panel**: real stats (users, outstanding credits, jobs processed,
  pending payments), broadcast to all users, user lookup, `/promote` and
  `/demote` to manage other admins, and a system-status check for whether
  Tesseract/PyMuPDF are actually installed on the host.
- **Persistent storage**: SQLite (`data/bot.db`) replaces both the
  in-memory `USER_STORE` from Fbot and the two incomplete `database.py` /
  `database1.py` drafts from Ggg — one schema, credits and settings survive
  restarts.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in BOT_TOKEN, ADMIN_IDS, payment accounts
python main.py
```

OCR and PDF rendering need system packages the pip installs don't cover:

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-amh
```

Or just use Docker, which installs these automatically:

```bash
cp .env.example .env
docker compose up --build
```

If Tesseract isn't installed, Smart Import degrades gracefully (it returns
an empty result and logs a warning) instead of crashing — check
`🛠️ Admin panel → System status` to confirm what's available.

## Structure

```
IDBot/
├── config.py         # settings: languages, packages, payment accounts, image sizes
├── database.py        # SQLite: users, settings, jobs, payment requests
├── processor.py        # IDProcessor: A4 layout, enhance, OCR, PDF import, QR
├── keyboards.py         # inline/reply keyboards
├── messages.py           # i18n text (en / am / om)
├── utils.py                # generic helpers + thin wrappers over database.py
├── handlers/
│   ├── states.py            # FSM state groups (GroupFlow, SmartImportFlow, ...)
│   ├── start.py               # /start + language picker
│   ├── menu.py                  # /menu, /help, /cancel
│   ├── settings.py                # output settings, persisted per user
│   ├── payment.py                   # top-up + payment-proof flow
│   ├── features.py                    # feature list, routes "Get Started" to real handlers
│   ├── admin.py                         # payment approval, broadcast, stats, lookup
│   └── uploads.py                         # the real ID-grouping + OCR pipeline
├── tessdata/          # Amharic + English Tesseract trained data (from Ggg)
├── templates/           # Nyala (Amharic) + Roboto fonts (from Ggg, for future captions)
├── data/ temp/ outputs/ logs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Notes / things to double check before going live

- **Rotate the bot token.** The original `Ggg/.env` you uploaded contained a
  live-looking bot token and payment account numbers. That file was **not**
  copied into this merged project — only `.env.example` with placeholders
  was — but since the token was already sitting in a zip file, it's worth
  regenerating it via @BotFather (`/revoke`) if you haven't already,
  rather than reusing the one from the old `.env`.
- Credits are spent when a job actually runs (one grouped sheet, or one
  Smart Import) — refunded automatically if sheet generation throws.
- `ADMIN_IDS` in `.env` are always admins; `/promote` and `/demote` manage
  additional admins stored in the database on top of that list.
