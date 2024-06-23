from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.units import mm as mm_unit
import os
from flask import current_app

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
    c = canvas.Canvas(pdf_output, pagesize=(80*mm, 90*mm))
    bg_image_path = os.path.join(current_app.root_path, 'static', 'images/bg.png')
    width, height = 80*mm, 90*mm
    bg_image = ImageReader(bg_image_path)

    for sticker in stickers:
        draw_sticker(c, sticker, width, height, bg_image)
        c.showPage()

    c.save()

def draw_sticker(c, sticker, width, height, bg_image):
    # Draw the background image
    c.drawImage(bg_image, 0, 0, width=width, height=height)

    # Convert dates to strings
    mfg_date_str = sticker.mfg_date.strftime('%Y-%m-%d')
    exp_date_str = sticker.exp_date.strftime('%Y-%m-%d')

    # Product Name, MRP, Net Weight, MFG Date, EXP Date, and Batch Number in top right white column
    c.setFont("Helvetica-Bold", 7)
    draw_wrapped_text(c, sticker.product_name, 36*mm, height - 42*mm, max_width=30*mm)
    c.setFont("Helvetica", 6)
    draw_wrapped_text(c, "MRP: ₹" + sticker.rate, 36*mm, height - 45*mm, max_width=30*mm)
    draw_wrapped_text(c, "Net Weight: " + sticker.net_weight + "g", 36*mm, height - 48*mm, max_width=30*mm)
    draw_wrapped_text(c, "MFG Date: " + mfg_date_str, 36*mm, height - 51*mm, max_width=30*mm)
    draw_wrapped_text(c, "EXP Date: " + exp_date_str, 36*mm, height - 54*mm, max_width=30*mm)
    draw_wrapped_text(c, "Batch No: " + sticker.batch_number, 36*mm, height - 57*mm, max_width=30*mm)

    # Nutritional Facts box
    nutritional_lines = sticker.nutritional_facts.split("\n")
    draw_multiline_text(c, nutritional_lines, 8*mm, height - 50*mm, max_width=30*mm, font_size=6)

    # Allergen Information box
    allergen_lines = sticker.allergen_information.split("\n")
    text_y_position = height - 50*mm - (len(nutritional_lines) * 8)  # Adjusting the height based on nutritional facts
    draw_multiline_text(c, ["Allergen Information:"] + allergen_lines, 8*mm, text_y_position, max_width=30*mm, font_size=6)

    # Ingredients box
    ingredients_lines = sticker.ingredients.split("\n")
    draw_multiline_text(c, ingredients_lines, 36*mm, height - 68*mm, max_width=40*mm, font_size=6)

def draw_multiline_text(c, lines, x, y, max_width, font_size):
    c.setFont("Helvetica", font_size)
    for line in lines:
        draw_wrapped_text(c, line, x, y, max_width)
        y -= font_size * 1.2  # Adjust the line spacing as needed

def draw_wrapped_text(c, text, x, y, max_width):
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'Helvetica'
    styleN.fontSize = 6
    styleN.leading = 8

    # Create a Paragraph with the text
    p = Paragraph(text, styleN)

    # Calculate the width and height of the Paragraph
    w, h = p.wrap(max_width, 100*mm)

    # Draw the Paragraph
    p.drawOn(c, x, y - h)

def draw_wrapped_text(c, text, x, y, max_width):
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'Helvetica'
    styleN.fontSize = 6
    styleN.leading = 8

    # Create a Paragraph with the text
    p = Paragraph(text, styleN)

    # Calculate the width and height of the Paragraph
    w, h = p.wrap(max_width, 100*mm)

    # Draw the Paragraph
    p.drawOn(c, x, y - h)
