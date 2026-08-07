#!/usr/bin/env python3
"""
Fayda ID PRINT-LAYOUT extractor (front+back on one A4 page, mirrored).
OpenCV: detect card halves -> auto un-mirror -> ROI OCR (Tesseract) -> QR/barcode.
Field boxes are PROPORTIONAL (fractions of card w/h) so they work at any DPI.
"""
import os, re, json
import cv2
import numpy as np
import pytesseract
import zxingcpp

os.environ["TESSDATA_PREFIX"] = "/home/user/tessdata"

# ---- proportional field boxes: [fx1, fy1, fx2, fy2] measured on 1605x1025 card ----
FRONT_FIELDS = {
    "portrait_photo":     {"box": [0.065, 0.258, 0.377, 0.859], "kind": "photo", "out": "print_user_photo.jpg"},
    "ghost_photo":        {"box": [0.778, 0.712, 0.869, 0.878], "kind": "photo", "out": "print_ghost_photo.jpg"},
    "full_name_amharic":  {"box": [0.383, 0.298, 0.585, 0.342], "lang": "amh",     "psm": 7},
    "full_name_english":  {"box": [0.383, 0.338, 0.680, 0.382], "lang": "eng",     "psm": 7},
    "date_of_birth":      {"box": [0.385, 0.445, 0.718, 0.500], "lang": "eng",     "psm": 7, "wl": "0123456789/|JFMAMJJASONDueglpbcy", "clean": "date", "select": "date"},
    "sex":                {"box": [0.385, 0.538, 0.550, 0.600], "lang": "amh+eng", "psm": 7},
    "date_of_expiry":     {"box": [0.385, 0.642, 0.738, 0.702], "lang": "eng",     "psm": 7, "wl": "0123456789/|JFMAMJJASONDueglpbcy", "clean": "date", "select": "date"},
    "fan_number":         {"box": [0.395, 0.752, 0.705, 0.806], "lang": "eng",     "psm": 7, "wl": "0123456789", "clean": "digits"},
    "date_of_issue_vert": {"box": [0.028, 0.055, 0.068, 0.900], "lang": "eng",     "psm": 7, "rotate": "auto", "clean": "issue"},
}
FRONT_BARCODE = [0.458, 0.795, 0.705, 0.885]

BACK_FIELDS = {
    "phone_number":  {"box": [0.048, 0.163, 0.210, 0.208], "lang": "eng",     "psm": 8, "wl": "0123456789", "clean": "digits"},
    "nationality":   {"box": [0.050, 0.305, 0.310, 0.360], "lang": "amh+eng", "psm": 7, "clean": "nation"},
    "address_block": {"box": [0.048, 0.445, 0.220, 0.716], "lang": "amh+eng", "psm": 6, "clean": "addr", "select": "lines"},
    "fin_number":    {"box": [0.034, 0.785, 0.315, 0.840], "lang": "eng",     "psm": 7, "clean": "findigits"},
    "serial_number": {"box": [0.740, 0.850, 0.950, 0.950], "lang": "eng",     "psm": 7, "clean": "sn"},
}
BACK_QR = [0.40, 0.05, 0.95, 0.88]

# ---------------------------------------------------------------- helpers
def rel_box(box, w, h, pad=0):
    x1, y1 = int(box[0]*w), int(box[1]*h)
    x2, y2 = int(box[2]*w), int(box[3]*h)
    return [max(x1-pad,0), max(y1-pad,0), min(x2+pad,w), min(y2+pad,h)]

def grab(img, box, pad=0):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = box
    return img[max(y1-pad,0):min(y2+pad,h), max(x1-pad,0):min(x2+pad,w)]

def _variants(roi):
    g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    g = cv2.fastNlMeansDenoising(g, None, 10, 7, 21)
    otsu = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    big = cv2.threshold(cv2.resize(g, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC),
                        0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    return [g, otsu, big]   # gray / otsu / 3x-equivalent otsu

def ocr_all(roi, lang, psm, wl=None, mwf=0):
    """Return [(text, mean_conf)] for each preprocessing variant.
    mwf = drop words with mean conf below this threshold (kills guilloche garbage)."""
    cfg = f"--psm {psm} --oem 1"
    if wl:
        cfg += f" -c tessedit_char_whitelist={wl}"
    out = []
    for im in _variants(roi):
        d = pytesseract.image_to_data(im, lang=lang, config=cfg,
                                      output_type=pytesseract.Output.DICT)
        lines, confs = {}, []
        for i, t in enumerate(d["text"]):
            if not t.strip():
                continue
            if mwf and isinstance(d["conf"][i], (int, float)) and 0 <= d["conf"][i] < mwf:
                continue
            key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
            lines.setdefault(key, []).append(t)
            if d["conf"][i] > 0:
                confs.append(d["conf"][i])
        text = "\n".join(" ".join(w) for w in lines.values()).strip()
        out.append((text, sum(confs)/len(confs) if confs else 0.0))
    return out

def ocr(roi, lang, psm, wl=None, select="conf", mwf=0):
    cands = ocr_all(roi, lang, psm, wl, mwf)
    if select == "date":
        # prefer: most valid date patterns -> most plausible years (1900-2099) -> conf
        def key(tc):
            txt = tc[0]
            pats = len(re.findall(r"\d{4}\s*/\s*[0-9A-Za-z]{2,}", txt))
            yrs = sum(1900 <= int(y) <= 2099 for y in re.findall(r"\b\d{4}\b", txt))
            return (pats, yrs, tc[1])
        return max(cands, key=key)[0]
    if select == "lines":   # multi-line blocks: take variant with most confident content
        return max(cands, key=lambda tc: tc[1]*len(tc[0].split()))[0]
    return max(cands, key=lambda tc: tc[1])[0]

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def post_clean(text, mode):
    if mode == "digits":
        return re.sub(r"\D", "", text)
    if mode == "date":
        t = text.replace(" ", "")
        t = re.sub(r"(?<=[/|\d])[Oo]", "0", t)
        t = re.sub(r"^[Oo](?=\d)", "0", t)
        def complete_month(m):       # e.g. "Au" -> "Aug", "Auc" -> "Aug"
            tok = m.group(2).capitalize()[:3]
            hits = [mn for mn in MONTHS if mn.startswith(tok[:2]) and mn[:len(tok)] == tok] \
                   or [mn for mn in MONTHS if mn.startswith(tok[:2])]
            return m.group(1) + "/" + (hits[0] if len(hits) == 1 else m.group(2)) + "/" + m.group(3)
        t = re.sub(r"(\d{4})/([A-Za-z]{2,3})/(\d{2})", complete_month, t)
        return t
    if mode == "issue":
        dates = re.findall(r"\d{4}/(?:\d{2}|[A-Za-z]{3})/\d{2}", text)
        return " | ".join(dates) if dates else text
    if mode == "nation":
        t = re.sub(r"Ethio[A-Za-z]{3,}", "Ethiopian", text)
        return t
    if mode == "addr":
        return "\n".join(l for l in (x.strip() for x in text.splitlines()) if l)
    if mode == "sn":
        runs = re.findall(r"\d{5,}", text)
        return runs[-1] if runs else re.sub(r"\D", "", text)
    if mode == "findigits":
        d = re.sub(r"\D", "", text)
        return " ".join(d[i:i+4] for i in range(0, len(d), 4))
    return text

def decode_codes(img):
    """zxing-cpp on several variants; returns list of (format, text)."""
    out = []
    variants = [img, cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)]
    for v in variants:
        try:
            for r in zxingcpp.read_barcodes(v):
                if r.valid and r.text:
                    t = (str(r.format), r.text)
                    if t not in out:
                        out.append(t)
        except Exception:
            pass
        if out:
            break
    return out

def detect_cards(page):
    """Find the two card halves on the A4 print page."""
    gray = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
    mask = (gray < 235).astype(np.uint8)*255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((25,25), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = page.shape[:2]
    boxes = [cv2.boundingRect(c) for c in cnts]
    boxes = [b for b in boxes if b[2] > w*0.2 and b[3] > h*0.09]
    boxes.sort(key=lambda b: b[0])
    return [page[y:y+ch, x:x+cw] for (x, y, cw, ch) in boxes[:2]]

def unmirror(card):
    """Choose orientation by OCR confidence on a wide probe band —
    mirrored text scores near-zero confidence, correct text scores high."""
    h, w = card.shape[:2]
    box = [int(0.25*w), int(0.25*h), int(0.78*w), int(0.50*h)]
    def conf(im):
        g = cv2.cvtColor(grab(im, box), cv2.COLOR_BGR2GRAY)
        g = cv2.resize(g, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        d = pytesseract.image_to_data(g, lang="eng", config="--psm 6",
                                      output_type=pytesseract.Output.DICT)
        cs = [c for c in d["conf"] if isinstance(c, (int, float)) and c > 0]
        return sum(cs)/len(cs) if cs else 0.0
    flipped = cv2.flip(card, 1)
    return card if conf(card) >= conf(flipped) else flipped

def is_back(card):
    """Card back = the half that contains the big decodable QR."""
    h, w = card.shape[:2]
    roi = grab(card, [int(0.40*w), int(0.05*h), int(0.95*w), int(0.88*h)])
    return len(decode_codes(roi)) > 0

def remove_background(photo_path, out_path):
    try:
        os.environ.setdefault("U2NET_HOME", "/home/user/.u2net")
        from rembg import remove, new_session
        out = remove(cv2.imread(photo_path), session=new_session("u2netp"))
        cv2.imwrite(out_path, out)
        return os.path.basename(out_path)
    except Exception:
        return None

# ---------------------------------------------------------------- main
def extract_print(page_path, tag):
    page = cv2.imread(page_path)
    cards = [unmirror(c) for c in detect_cards(page)]
    if len(cards) < 2:
        raise RuntimeError(f"expected 2 card halves, found {len(cards)}")
    front, back = (cards[1], cards[0]) if is_back(cards[0]) else (cards[0], cards[1])
    res = {}

    fh, fw = front.shape[:2]
    cv2.imwrite(f"/home/user/print_front_{tag}.jpg", front)
    for name, f in FRONT_FIELDS.items():
        box = rel_box(f["box"], fw, fh, pad=4)
        roi = grab(front, box)
        if f.get("kind") == "photo":
            cv2.imwrite(f"/home/user/{f['out']}", roi, [cv2.IMWRITE_JPEG_QUALITY, 95])
            res[name] = {"file": f["out"], "size_px": [roi.shape[1], roi.shape[0]]}
            nobg = f["out"].rsplit(".", 1)[0] + "_nobg.png"
            rb = remove_background(f"/home/user/{f['out']}", f"/home/user/{nobg}")
            if rb:
                res[name]["nobg_file"] = rb
            continue
        if f.get("rotate") == "auto":
            best, best_hits = "", 0
            for rot in (cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_90_CLOCKWISE):
                t = ocr(cv2.rotate(roi, rot), f["lang"], f["psm"], f.get("wl"))
                hits = len(re.findall(r"\d{4}", t))
                if hits > best_hits:
                    best, best_hits = t, hits
            res[name] = post_clean(best, f.get("clean"))
            continue
        res[name] = post_clean(ocr(roi, f["lang"], f["psm"], f.get("wl"),
                                   f.get("select", "conf"), f.get("mwf", 0)), f.get("clean"))
    codes = decode_codes(grab(front, rel_box(FRONT_BARCODE, fw, fh, pad=6)))
    res["fan_barcode_decoded"] = codes[0][1] if codes else None

    bh, bw = back.shape[:2]
    cv2.imwrite(f"/home/user/print_back_{tag}.jpg", back)
    for name, f in BACK_FIELDS.items():
        box = rel_box(f["box"], bw, bh, pad=4)
        res[name] = post_clean(ocr(grab(back, box), f["lang"], f["psm"], f.get("wl"),
                                   f.get("select", "conf"), f.get("mwf", 0)), f.get("clean"))
    qrc = decode_codes(grab(back, rel_box(BACK_QR, bw, bh, pad=6)))
    res["qr_decoded_len"] = len(qrc[0][1]) if qrc else 0
    if qrc:
        with open(f"/home/user/qr_payload_print_{tag}.txt", "w") as fq:
            fq.write(qrc[0][1].encode("unicode_escape").decode())
    return {f"print_{tag}_front": {k: v for k, v in res.items() if k in
                ["portrait_photo","ghost_photo","full_name_amharic","full_name_english",
                 "date_of_birth","sex","date_of_expiry","fan_number","date_of_issue_vert",
                 "fan_barcode_decoded"]},
            f"print_{tag}_back": {k: v for k, v in res.items() if k in
                ["phone_number","nationality","address_block","fin_number",
                 "serial_number","qr_decoded_len"]}}

results = {}
for tag, fname in [("color", "Ramadan_Tafari_Tufa_print_color.jpg"),
                   ("bw",    "Ramadan_Tafari_Tufa_print_bw.jpg")]:
    results.update(extract_print(f"/home/user/uploads/{fname}", tag))

with open("/home/user/fayda_print_extracted_data.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(json.dumps(results, indent=2, ensure_ascii=False))
