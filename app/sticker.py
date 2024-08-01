import os
from flask import current_app
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from app.models import StickerDesign

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

def create_sticker_pdf(stickers, pdf_output):
    # Get the sticker design from the database
    design = StickerDesign.query.first()
    if not design:
        raise ValueError("Sticker design not found in the database")

    # Custom page size and margins
    PAGE_WIDTH = design.page_size['width'] * mm
    PAGE_HEIGHT = design.page_size['height'] * mm
    MARGIN = design.page_size['margin'] * mm

    c = canvas.Canvas(pdf_output, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    if design.use_bg_image and design.bg_image:
        bg_image_path = os.path.join(current_app.root_path, 'static', 'images', design.bg_image)
        bg_image = ImageReader(bg_image_path)
    else:
        bg_image = None

    # Register the custom font
    regular_font_path = os.path.join(current_app.root_path, 'static', 'fonts', 'RobotoCondensed-Regular.ttf')
    pdfmetrics.registerFont(TTFont('RobotoCondensed', regular_font_path))

    for sticker in stickers:
        c.saveState()
        c.translate(MARGIN, MARGIN)
        draw_sticker(c, sticker, PAGE_WIDTH - 2 * MARGIN, PAGE_HEIGHT - 2 * MARGIN, bg_image, design)
        c.restoreState()
        c.showPage()

    c.save()

def draw_sticker(c, sticker, width, height, bg_image, design):
    # Draw the background image if it exists
    if bg_image:
        c.drawImage(bg_image, 0, 0, width=width, height=height)

    # Convert dates to strings
    mfg_date_str = sticker.mfg_date.strftime('%d-%m-%Y')
    exp_date_str = sticker.exp_date.strftime('%d-%m-%Y')
    usp_rate     = round(float(sticker.rate) / float(sticker.net_weight), 2)

    # Use the custom font that supports ₹ symbol
    draw_wrapped_text(c, sticker.product_name, design.product_name_position['left']*mm, height - design.product_name_position['top']*mm, max_width=design.product_name_position['max_width']*mm, font_size=design.heading_font_size, bold=True)
    draw_wrapped_text(c, f"MRP: ₹{sticker.rate}   (₹{usp_rate:.2f}/g)", design.mrp_position['left']*mm, height - (design.mrp_position['top']+5)*mm, max_width=design.mrp_position['max_width']*mm, font_size=design.content_font_size)
    draw_wrapped_text(c, "Net Weight: " + sticker.net_weight + "g", design.net_weight_position['left']*mm, height - design.net_weight_position['top']*mm, max_width=design.net_weight_position['max_width']*mm, font_size=design.content_font_size)
    draw_wrapped_text(c, "MFG Date: " + mfg_date_str, design.mfg_date_position['left']*mm, height - design.mfg_date_position['top']*mm, max_width=design.mfg_date_position['max_width']*mm, font_size=design.content_font_size)
    draw_wrapped_text(c, "EXP Date: " + exp_date_str, design.exp_date_position['left']*mm, height - design.exp_date_position['top']*mm, max_width=design.exp_date_position['max_width']*mm, font_size=design.content_font_size)
    draw_wrapped_text(c, "Batch No: " + sticker.batch_number, design.batch_no_position['left']*mm, height - design.batch_no_position['top']*mm, max_width=design.batch_no_position['max_width']*mm, font_size=design.content_font_size)

    # Nutritional Facts box
    nutritional_lines = sticker.nutritional_facts.split("\n")
    draw_multiline_text(c, nutritional_lines, design.nutritional_facts_position['left']*mm, height - design.nutritional_facts_position['top']*mm, max_width=design.nutritional_facts_position['max_width']*mm, font_size=design.content_font_size)

    # Allergen Information box
    allergen_lines = sticker.allergen_information.split("\n")
    draw_multiline_text(c, ["Allergen Info:"], design.allergen_info_position['left']*mm, height - design.allergen_info_position['top']*mm, max_width=design.allergen_info_position['max_width']*mm, font_size=design.heading_font_size, bold=True)
    draw_multiline_text(c, allergen_lines, design.allergen_info_position['left']*mm, height - (design.allergen_info_position['top']+3.5)*mm, max_width=design.allergen_info_position['max_width']*mm, font_size=design.content_font_size)

    # Ingredients box
    ingredients_lines = sticker.ingredients.split("\n")
    draw_multiline_text(c, ingredients_lines, design.ingredients_position['left']*mm, height - design.ingredients_position['top']*mm, max_width=design.ingredients_position['max_width']*mm, font_size=design.content_font_size)

def draw_multiline_text(c, lines, x, y, max_width, font_size, bold=False):
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'RobotoCondensed'
    styleN.fontSize = font_size
    if bold:
        styleN.fontWeight = 'bolder'  # Apply bold style
    for line in lines:
        draw_wrapped_text(c, line, x, y, max_width, font_size, bold)
        y -= font_size * 1.15  # Adjust the line spacing as needed

def draw_wrapped_text(c, text, x, y, max_width, font_size, bold=False):
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'RobotoCondensed'
    styleN.fontSize = font_size
    styleN.leading = font_size + 0.7  # Adjust leading for better spacing if needed
    if bold:
        styleN.fontWeight = 'bolder'  # Apply bold style

    # Create a Paragraph with the text
    p = Paragraph(text, styleN)

    # Calculate the width and height of the Paragraph
    w, h = p.wrap(max_width, 100*mm)

    # Draw the Paragraph
    p.drawOn(c, x, y - h)

def create_stickers_pdf(stickers):
    # Create a PDF file in the root directory
    pdf_path = os.path.join(current_app.root_path, '..', 'stickers_to_print.pdf')
    create_sticker_pdf(stickers, pdf_path)
    return pdf_path