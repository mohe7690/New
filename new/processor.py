import os
import cv2
import fitz  # PyMuPDF
import qrcode
import barcode
import pytesseract
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- CONSTANTS FOR 300 DPI PRINTING ---
CANVAS_SIZE = (2480, 3508)  # A4 Resolution
ID_SIZE = (1012, 638)       # Standard 85.6mm x 54mm
CENTER_X = 1240             # Vertical Fold Line
Y_START = 350               # Margin from top
Y_GAP = 60                  # Gap between ID rows

class IDProcessor:
    def __init__(self):
        # Paths to your resources
        self.temp_dir = "temp"
        self.output_dir = "outputs"
        self.font_amh = "templates/nyala.ttf"
        self.font_eng = "templates/roboto.ttf"
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    # --- 1. DATA EXTRACTION (OCR) ---
    def extract_text(self, image_path):
        """Extracts Amharic and English text from an image."""
        img = cv2.imread(image_path)
        # Pre-processing: Grayscale and Thresholding improves OCR accuracy
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Use amh+eng language pack
        text = pytesseract.image_to_string(gray, lang='amh+eng')
        return text

    def extract_from_pdf(self, pdf_path):
        """Extracts high-res images and text layers from official PDFs."""
        doc = fitz.open(pdf_path)
        page = doc[0]
        text = page.get_text("text")
        # Logic to extract the portrait image from the PDF stream would go here
        return text

    # --- 2. ASSET GENERATION ---
    def generate_barcode(self, fan_number):
        """Generates a sharp Code-128 barcode."""
        Code128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        # Set background to transparent or white
        bar = Code128(fan_number, writer=writer)
        return bar.render(writer_options={"module_height": 5, "text_distance": 1, "font_size": 1})

    def generate_qr(self, fin_number):
        """Generates a high-contrast QR code for the back side."""
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(f"https://verify.id.et/{fin_number}")
        return qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # --- 3. RENDERING ---
    def render_id_side(self, data, side="front"):
        """
        data: dictionary containing 'name_amh', 'name_eng', 'fan', 'portrait', etc.
        side: 'front' or 'back'
        """
        template_path = f"templates/{side}_blank.png"
        card = Image.open(template_path).convert("RGB").resize(ID_SIZE)
        draw = ImageDraw.Draw(card)
        
        f_amh = ImageFont.truetype(self.font_amh, 32)
        f_eng = ImageFont.truetype(self.font_eng, 26)

        if side == "front":
            # Paste Portrait
            portrait = data['portrait'].resize((310, 390))
            card.paste(portrait, (70, 210))
            # Write Text
            draw.text((430, 230), data['name_amh'], font=f_amh, fill="black")
            draw.text((430, 275), data['name_eng'], font=f_eng, fill="black")
            # Paste Barcode
            bc = self.generate_barcode(data['fan']).resize((420, 80))
            card.paste(bc, (480, 710))
        else:
            # Paste QR
            qr_img = self.generate_qr(data['fin']).resize((300, 300))
            card.paste(qr_img, (80, 180))
            # Write Address
            draw.text((480, 200), data['phone'], font=f_eng, fill="black")
            draw.text((480, 350), data['address'], font=f_amh, fill="black")

        return card

    # --- 4. A4 LAYOUT ENGINE ---
    def draw_guidelines(self, draw, x1, y1, x2, y2):
        """Draws L-shaped crop marks at corners."""
        length = 30
        color = (180, 180, 180) # Light grey
        # Top Left
        draw.line([(x1, y1), (x1 + length, y1)], fill=color, width=2)
        draw.line([(x1, y1), (x1, y1 + length)], fill=color, width=2)
        # Top Right, Bottom Left, Bottom Right... (repeat logic)

    def build_a4_batch(self, id_list, user_id):
        """
        id_list: list of dicts [{'front': PIL, 'back': PIL}, ...]
        Creates the mirrored layout for up to 3 IDs.
        """
        canvas = Image.new("RGB", CANVAS_SIZE, "white")
        draw = ImageDraw.Draw(canvas)
        
        for i, id_pair in enumerate(id_list[:3]):
            y_offset = Y_START + (i * (ID_SIZE[1] + Y_GAP))
            
            # 1. Back Side (Left Column - MIRRORED)
            back_mirrored = ImageOps.mirror(id_pair['back'])
            canvas.paste(back_mirrored, (CENTER_X - ID_SIZE[0], y_offset))
            
            # 2. Front Side (Right Column)
            canvas.paste(id_pair['front'], (CENTER_X, y_offset))
            
            # 3. Guidelines
            self.draw_guidelines(draw, CENTER_X - ID_SIZE[0], y_offset, CENTER_X + ID_SIZE[0], y_offset + ID_SIZE[1])

        # --- GRID LINES ---
        # Vertical Fold Line (Dashed)
        for y in range(150, 3300, 40):
            draw.line([(CENTER_X, y), (CENTER_X, y + 20)], fill="grey", width=2)
            
        # Horizontal Cut Lines (Between rows)
        for i in range(1, len(id_list)):
            line_y = Y_START + (i * ID_SIZE[1]) + (i * Y_GAP) - (Y_GAP // 2)
            draw.line([(100, line_y), (2380, line_y)], fill="lightgrey", width=1)

        output_path = os.path.join(self.output_dir, f"print_{user_id}.pdf")
        canvas.save(output_path, "PDF", resolution=300.0)
        return output_path
