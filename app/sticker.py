import os
from flask import current_app
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
import io

if os.name == 'nt':
    import win32print
    import win32api
else:
    import cups

class Sticker:
    def __init__(self, product_name, rate, mfg_date, exp_date, net_weight, ingredients, nutritional_facts, batch_number, allergen_information):
        self.product_name = product_name
        self.rate = rate
        self.mfg_date = mfg_date
        self.exp_date = exp_date
        self.net_weight = net_weight
        self.ingredients = ingredients
        self.nutritional_facts = nutritional_facts
        self.batch_number = batch_number
        self.allergen_information = allergen_information

def create_sticker_pdf(stickers, pdf_output, bg_image_path):
    # Custom page size and margins
    PAGE_WIDTH = 85 * mm
    PAGE_HEIGHT = 95 * mm
    MARGIN = 2.5 * mm

    c = canvas.Canvas(pdf_output, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    bg_image_path = os.path.join(current_app.root_path, 'static', 'images/bg.png')
    bg_image = ImageReader(bg_image_path)

    # Register the custom font
    regular_font_path = os.path.join(current_app.root_path, 'static', 'fonts', 'RobotoCondensed-Regular.ttf')
    pdfmetrics.registerFont(TTFont('RobotoCondensed', regular_font_path))

    for sticker in stickers:
        c.saveState()
        c.translate(MARGIN, MARGIN)
        draw_sticker(c, sticker, PAGE_WIDTH - 2 * MARGIN, PAGE_HEIGHT - 2 * MARGIN, bg_image)
        c.restoreState()
        c.showPage()

    c.save()

def draw_sticker(c, sticker, width, height, bg_image):
    # Draw the background image
    c.drawImage(bg_image, 0, 0, width=width, height=height)

    # Convert dates to strings
    mfg_date_str = sticker.mfg_date.strftime('%d-%m-%Y')
    exp_date_str = sticker.exp_date.strftime('%d-%m-%Y')

    # Use the custom font that supports ₹ symbol
    draw_wrapped_text(c, sticker.product_name, 36*mm, height - 42*mm, max_width=30*mm, font_size=8, bold=True)
    draw_wrapped_text(c, "MRP: ₹" + sticker.rate, 36*mm, height - 47*mm, max_width=30*mm, font_size=6)
    draw_wrapped_text(c, "Net Weight: " + sticker.net_weight + "g", 36*mm, height - 49.5*mm, max_width=30*mm, font_size=6)
    draw_wrapped_text(c, "MFG Date: " + mfg_date_str, 36*mm, height - 52*mm, max_width=30*mm, font_size=6)
    draw_wrapped_text(c, "EXP Date: " + exp_date_str, 36*mm, height - 54.5*mm, max_width=30*mm, font_size=6)
    draw_wrapped_text(c, "Batch No: " + sticker.batch_number, 36*mm, height - 57*mm, max_width=30*mm, font_size=6)

    # Nutritional Facts box
    nutritional_lines = sticker.nutritional_facts.split("\n")
    draw_multiline_text(c, nutritional_lines, 8*mm, height - 50*mm, max_width=30*mm, font_size=6)

    # Allergen Information box
    allergen_lines = sticker.allergen_information.split("\n")
    text_y_position = height - 50*mm - (len(nutritional_lines) * 8)  # Adjusting the height based on nutritional facts
    draw_multiline_text(c, ["Allergen Information:"], 8*mm, text_y_position, max_width=30*mm, font_size=7, bold=True)
    draw_multiline_text(c, allergen_lines, 8*mm, text_y_position - 3*mm, max_width=30*mm, font_size=6)

    # Ingredients box
    ingredients_lines = sticker.ingredients.split("\n")
    draw_multiline_text(c, ingredients_lines, 36*mm, height - 68*mm, max_width=40*mm, font_size=6)

def draw_multiline_text(c, lines, x, y, max_width, font_size, bold=False):
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'RobotoCondensed'
    styleN.fontSize = font_size
    if bold:
        styleN.fontWeight = 'bolder'  # Apply bold style
    for line in lines:
        draw_wrapped_text(c, line, x, y, max_width, font_size)
        y -= font_size * 1.2  # Adjust the line spacing as needed

def draw_wrapped_text(c, text, x, y, max_width, font_size, bold=False):  # Add font_size parameter
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'RobotoCondensed'
    styleN.fontSize = font_size  # Set the font size here
    styleN.leading = 8.5  # Adjust leading for better spacing if needed
    if bold:
        styleN.fontWeight = 'bolder'  # Apply bold style

    # Create a Paragraph with the text
    p = Paragraph(text, styleN)

    # Calculate the width and height of the Paragraph
    w, h = p.wrap(max_width, 100*mm)

    # Draw the Paragraph
    p.drawOn(c, x, y - h)

def print_stickers(stickers):
    # Create a PDF in memory
    pdf_output = io.BytesIO()
    bg_image_path = os.path.join(current_app.root_path, 'static', 'images/bg.png')
    create_sticker_pdf(stickers, pdf_output, bg_image_path)
    pdf_output.seek(0)
    
    if os.name == 'nt':  # On Windows
        print_pdf_windows(pdf_output)
    else:  # On Linux/Mac
        print_pdf_cups(pdf_output)

def print_pdf_windows(pdf_output):
    printer_name = win32print.GetDefaultPrinter()
    temp_pdf_path = os.path.join(os.getcwd(), 'temp_stickers.pdf')
    with open(temp_pdf_path, 'wb') as f:
        f.write(pdf_output.getvalue())
    win32api.ShellExecute(
        0,
        "print",
        temp_pdf_path,
        None,
        ".",
        0
    )

def print_pdf_cups(pdf_output):
    conn = cups.Connection()
    printers = conn.getPrinters()
    default_printer = list(printers.keys())[0]  # Use the first printer found
    temp_pdf_path = os.path.join(os.getcwd(), 'temp_stickers.pdf')
    with open(temp_pdf_path, 'wb') as f:
        f.write(pdf_output.getvalue())
    conn.printFile(default_printer, temp_pdf_path, "Sticker Print Job", {})
