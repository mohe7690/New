#!/usr/bin/env python3
"""
Fayda Digital ID screenshot data extractor.
Pipeline: OpenCV (ROI + preprocessing) -> Tesseract OCR -> OpenCV QR/Barcode decode.
Coordinates: [x_min, y_min, x_max, y_max] on 576x1280 screenshots.
"""
import os, json, re
import cv2
import numpy as np
import pytesseract
import zxingcpp

os.environ["TESSDATA_PREFIX"] = "/home/user/tessdata"   # eng + amh traineddata

UPLOADS = "/home/user/uploads"
PAD = 5          # px padding around each ROI
SCALE = 3        # upscale factor for OCR

# ---------------- field map ----------------
FRONT = {
    "file": "-6026087529066466458_121.jpg",
    "text_fields": {
        "full_name_amharic":   {"box": [104, 668, 232, 692], "lang": "amh",      "psm": 7},
        "full_name_english":   {"box": [104, 692, 288, 714], "lang": "eng",      "psm": 7},
        "date_of_birth":       {"box": [104, 738, 312, 762], "lang": "eng",      "psm": 7, "wl": "0123456789/|JFMAMJJASONDueglpbcy", "clean": "date"},
        "sex":                 {"box": [104, 772, 202, 794], "lang": "amh+eng",  "psm": 7},
        "date_of_expiry":      {"box": [104, 814, 312, 842], "lang": "eng",      "psm": 7, "wl": "0123456789/|JFMAMJJASONDueglpbcy", "clean": "date"},
        "fan_number":          {"box": [182, 855, 372, 880], "lang": "eng",      "psm": 8, "wl": "0123456789", "clean": "digits"},
        "date_of_issue_vert":  {"box": [468, 345, 502, 733], "lang": "eng",      "psm": 7, "rotate": True},
    },
    "barcode_roi": [172, 848, 385, 932],
    "qr_roi": [55, 1132, 525, 1280],
    "photo_hint": [242, 305, 442, 599],       # user-supplied hint -> auto-snapped
    "photo_out": "user_photo_card.jpg",
}
BACK = {
    "file": "-6026087529066466459_121.jpg",
    "text_fields": {
        "phone_number":  {"box": [95, 731, 200, 758], "lang": "eng",     "psm": 8, "wl": "0123456789", "clean": "digits"},
        "fin_number":    {"box": [327, 720, 490, 744], "lang": "eng",    "psm": 7},
        "nationality":   {"box": [95, 787, 262, 810], "lang": "amh+eng", "psm": 7},
        "address_block": {"box": [95, 830, 240, 952], "lang": "amh+eng", "psm": 6},
    },
    "qr_roi": [95, 305, 480, 692],
}
MODAL = {
    "file": "-6026087529066466460_121.jpg",
    "text_fields": {},
    "qr_roi": [105, 668, 470, 1043],   # sharpest QR of all screenshots
    "photo_hint": [203, 263, 490, 742],# user-supplied hint -> auto-snapped
    "photo_out": "user_photo.jpg",
    "avatar_roi": [58, 88, 205, 218],  # small circular profile avatar
    "avatar_out": "user_avatar.jpg",
}

# ---------------- helpers ----------------
def grab(img, box, pad=PAD):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = box
    return img[max(y1-pad,0):min(y2+pad,h), max(x1-pad,0):min(x2+pad,w)]

def preprocess(roi, mode="otsu"):
    """OpenCV preprocessing for OCR: gray -> upscale -> denoise -> binarize."""
    g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_CUBIC)
    g = cv2.fastNlMeansDenoising(g, None, 10, 7, 21)
    if mode == "adaptive":
        g = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 35, 11)
    else:
        g = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return g

def ocr(roi, lang, psm, wl=None):
    cfg = f"--psm {psm} --oem 1"
    if wl:
        cfg += f" -c tessedit_char_whitelist={wl}"
    # Otsu first; only fall back to adaptive threshold if it finds much more text
    best = pytesseract.image_to_string(preprocess(roi, "otsu"), lang=lang, config=cfg).strip()
    if len(best) < 4:
        alt = pytesseract.image_to_string(preprocess(roi, "adaptive"), lang=lang, config=cfg).strip()
        if len(alt) > len(best):
            best = alt
    return best

def _zxing_decode(img_bgr, formats=None):
    """Try zxing-cpp on several variants of the image."""
    variants = [img_bgr,
                cv2.resize(img_bgr, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)]
    g = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    variants.append(cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
    for v in variants:
        try:
            res = zxingcpp.read_barcodes(v, formats=formats)
        except TypeError:
            res = zxingcpp.read_barcodes(v)
        for r in res:
            if r.valid and r.text:
                try:
                    return r.text, str(r.format)
                except Exception:
                    return r.text, "?"
    return None, None

def read_qr(img, roi_box=None):
    target = grab(img, roi_box) if roi_box else img
    text, fmt = _zxing_decode(target, formats=zxingcpp.BarcodeFormat.QRCode)
    if not text:  # OpenCV fallback
        det = cv2.QRCodeDetector()
        data, _pts, _ = det.detectAndDecode(target)
        text = data or None
    return text

def read_barcode(img, roi_box):
    roi = grab(img, roi_box)
    text, fmt = _zxing_decode(roi)
    if not text:
        try:
            bd = cv2.barcode.BarcodeDetector()
            ok, decoded, _t, _p = bd.detectAndDecodeWithType(roi)
            if ok and decoded and decoded[0]:
                text = decoded[0]
        except Exception:
            pass
    return text

def post_clean(text, mode):
    if mode == "digits":
        return re.sub(r"\D", "", text)
    if mode == "date":
        t = text.replace(" ", "")
        t = re.sub(r"(?<=[/|\d])[Oo]", "0", t)   # OCR O/0 confusion in numeric dates
        t = re.sub(r"^[Oo](?=\d)", "0", t)
        return t
    return text

def snap_photo(img, hint_box, aspect=0.76):
    """Use hint box as search region; locate face with Haar, then reconstruct the
    ID-photo rectangle around it (fixed ~3:4 aspect, face occupies center-upper)."""
    H, W = img.shape[:2]
    hx1, hy1, hx2, hy2 = hint_box
    mx, my = int(0.7*(hx2-hx1)), int(0.5*(hy2-hy1))
    rx1, ry1 = max(hx1-mx, 0), max(hy1-my, 0)
    rx2, ry2 = min(hx2+mx, W), min(hy2+my, H)
    region = img[ry1:ry2, rx1:rx2]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cas.detectMultiScale(gray, 1.05, 4, minSize=(40, 40))
    if len(faces) == 0:
        return hint_box  # give up: return hint unchanged
    fx, fy, fw, fh = (int(v) for v in max(faces, key=lambda f: f[2]*f[3]))  # largest face
    ax1, ay1 = fx + rx1, fy + ry1
    photo_w = int(fw / 0.62)                    # face ~62% of photo width
    photo_h = int(photo_w / aspect)
    cx = ax1 + fw // 2
    x1 = max(cx - photo_w // 2, 0)
    y1 = max(ay1 - int(0.55*fh), 0)             # headroom above face
    # refine top edge: drop dark header/title rows above the photo's white area
    full_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    max_top = ay1 - int(0.15*fh)
    for y in range(y1, max(y1+1, min(y1+50, max_top))):
        row = full_gray[y, x1:x1+photo_w]
        if (row > 232).mean() >= 0.80:          # mostly photo-white -> real top edge
            y1 = y
            break
    return [x1, y1, min(x1+photo_w, W), min(y1+photo_h, H)]

def extract_photo(img, roi_box, out_path, pad=0):
    """Pure OpenCV ROI extraction for photos; verifies a face is present."""
    photo = grab(img, roi_box, pad=pad)
    face_ok = False
    try:
        cas = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        face_ok = len(cas.detectMultiScale(gray, 1.1, 5)) > 0
    except Exception:
        pass
    cv2.imwrite(out_path, photo, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return {"file": os.path.basename(out_path),
            "size_px": [int(photo.shape[1]), int(photo.shape[0])],
            "face_detected": bool(face_ok)}

def remove_background(photo_path, out_path, model="u2netp"):
    """rembg (U2-Net) person segmentation -> transparent PNG."""
    try:
        os.environ.setdefault("U2NET_HOME", "/home/user/.u2net")
        from rembg import remove, new_session
        img = cv2.imread(photo_path)
        out = remove(img, session=new_session(model))   # BGRA result
        cv2.imwrite(out_path, out)
        cov = float((out[:, :, 3] > 128).mean() * 100)
        return {"file": os.path.basename(out_path), "subject_coverage_pct": round(cov, 1)}
    except Exception as e:
        return {"file": None, "error": str(e)}

# ---------------- run ----------------
results = {}
for tag, spec in [("screenshot_1_card_front", FRONT),
                  ("screenshot_2_card_back", BACK),
                  ("screenshot_3_modal", MODAL)]:
    img = cv2.imread(os.path.join(UPLOADS, spec["file"]))
    out = {}
    for name, f in spec["text_fields"].items():
        roi = grab(img, f["box"])
        if f.get("rotate"):
            roi = cv2.rotate(roi, cv2.ROTATE_90_CLOCKWISE)   # vertical -> horizontal
        out[name] = post_clean(ocr(roi, f["lang"], f["psm"], f.get("wl")), f.get("clean"))
    if spec.get("barcode_roi"):
        out["fan_barcode_decoded"] = read_barcode(img, spec["barcode_roi"])
    if spec.get("qr_roi"):
        qr_full = read_qr(img, spec["qr_roi"])
        if qr_full:
            with open(f"/home/user/qr_payload_{tag}.txt", "w") as fq:
                fq.write(qr_full.encode("unicode_escape").decode())  # binary-safe dump
        out["qr_decoded_len"] = len(qr_full) if qr_full else 0
        out["qr_preview"] = (qr_full[:80].encode("unicode_escape").decode() + "...") if qr_full else None
    if spec.get("photo_hint"):
        snapped = snap_photo(img, spec["photo_hint"])
        out["user_photo_snapped_box"] = snapped
        out["user_photo"] = extract_photo(
            img, snapped, f"/home/user/{spec['photo_out']}")
        nobg = spec["photo_out"].rsplit(".", 1)[0] + "_nobg.png"
        out["user_photo_nobg"] = remove_background(
            f"/home/user/{spec['photo_out']}", f"/home/user/{nobg}")
    if spec.get("avatar_roi"):
        out["profile_avatar"] = extract_photo(
            img, spec["avatar_roi"], f"/home/user/{spec['avatar_out']}", pad=2)
    results[tag] = out

with open("/home/user/fayda_extracted_data.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

for k, v in results.items():
    print(f"\n=== {k} ===")
    for kk, vv in v.items():
        print(f"  {kk}: {vv}")
