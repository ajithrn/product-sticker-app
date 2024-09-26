import os
import re
from flask import current_app
from reportlab.lib.pagesizes import mm, A4, A5, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.colors import black
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

def get_page_size(design):
    if design.printer_type == 'label':
        page_size = (design.page_size['width'] * mm, design.page_size['height'] * mm)
    elif design.paper_size == 'A4':
        page_size = A4
    elif design.paper_size == 'A5':
        page_size = A5
    else:  # custom size
        page_size = (design.custom_paper_width * mm, design.custom_paper_height * mm)
    
    if design.paper_orientation == 'landscape':
        return landscape(page_size)
    return page_size

def create_sticker_pdf(stickers, pdf_output):
    design = StickerDesign.query.first()
    if not design:
        raise ValueError("Sticker design not found in the database")

    PAGE_WIDTH, PAGE_HEIGHT = get_page_size(design)
    STICKER_WIDTH, STICKER_HEIGHT = design.page_size['width'] * mm, design.page_size['height'] * mm
    MARGIN = design.page_size['margin'] * mm

    c = canvas.Canvas(pdf_output, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    if design.use_bg_image and design.bg_image:
        bg_image_path = os.path.join(current_app.root_path, 'static', 'images', design.bg_image)
        bg_image = ImageReader(bg_image_path)
    else:
        bg_image = None

    regular_font_path = os.path.join(current_app.root_path, 'static', 'fonts', 'RobotoCondensed-Bold.ttf')
    pdfmetrics.registerFont(TTFont('RobotoCondensed', regular_font_path))

    if design.printer_type == 'label':
        for sticker in stickers:
            c.saveState()
            draw_sticker(c, sticker, STICKER_WIDTH, STICKER_HEIGHT, bg_image, design, 0, 0)
            c.restoreState()
            c.showPage()
    else:
        x, y = 0, PAGE_HEIGHT - STICKER_HEIGHT
        for sticker in stickers:
            if y < 0:
                c.showPage()
                x, y = 0, PAGE_HEIGHT - STICKER_HEIGHT

            c.saveState()
            draw_sticker(c, sticker, STICKER_WIDTH, STICKER_HEIGHT, bg_image, design, x, y)
            c.restoreState()

            x += STICKER_WIDTH
            if x + STICKER_WIDTH > PAGE_WIDTH:
                x = 0
                y -= STICKER_HEIGHT

        c.showPage()

    c.save()

def draw_sticker(c, sticker, width, height, bg_image, design, x, y):
    margin = design.page_size['margin'] * mm

    # Draw a white rectangle as the sticker background (including margins)
    c.setFillColorRGB(1, 1, 1)  # White color
    c.rect(x, y, width, height, fill=True, stroke=False)
    
    # Draw the background image if it exists (only for the sticker area, excluding margins)
    if bg_image:
        c.drawImage(bg_image, x + margin, y + margin, width=width - 2*margin, height=height - 2*margin)

    # Apply margin to the content
    content_x, content_y = x + margin, y + margin
    content_width, content_height = width - 2 * margin, height - 2 * margin

    # Convert dates to strings
    mfg_date_str = sticker.mfg_date.strftime('%d-%m-%Y')
    exp_date_str = sticker.exp_date.strftime('%d-%m-%Y')
    usp_rate     = round(float(sticker.rate) / float(sticker.net_weight), 2)

    # Use the custom font that supports ₹ symbol
    draw_wrapped_text(c, sticker.product_name.upper(), content_x + design.product_name_position['left']*mm, content_y + content_height - design.product_name_position['top']*mm, max_width=design.product_name_position['max_width']*mm, font_size=design.heading_font_size, bold=True)
    draw_wrapped_text(c, f"MRP: ₹{sticker.rate}   (₹{usp_rate:.2f}/g)", content_x + design.mrp_position['left']*mm, content_y + content_height - (design.mrp_position['top'])*mm, max_width=design.mrp_position['max_width']*mm, font_size=design.mrp_font_size)
    draw_wrapped_text(c, "Net Weight: " + sticker.net_weight + "g", content_x + design.net_weight_position['left']*mm, content_y + content_height - design.net_weight_position['top']*mm, max_width=design.net_weight_position['max_width']*mm, font_size=design.content_font_size)
    draw_wrapped_text(c, "MFG Date: " + mfg_date_str, content_x + design.mfg_date_position['left']*mm, content_y + content_height - design.mfg_date_position['top']*mm, max_width=design.mfg_date_position['max_width']*mm, font_size=design.content_font_size)
    draw_wrapped_text(c, "EXP Date: " + exp_date_str, content_x + design.exp_date_position['left']*mm, content_y + content_height - design.exp_date_position['top']*mm, max_width=design.exp_date_position['max_width']*mm, font_size=design.content_font_size)
    draw_wrapped_text(c, "Batch No: " + sticker.batch_number, content_x + design.batch_no_position['left']*mm, content_y + content_height - design.batch_no_position['top']*mm, max_width=design.batch_no_position['max_width']*mm, font_size=design.content_font_size)

    # Nutritional Facts box
    nutritional_lines = sticker.nutritional_facts.split("\n")
    if design.print_nutritional_heading:
        draw_nutritional_heading(c, design.nutritional_heading_text, content_x + design.nutritional_facts_position['left']*mm, content_y + content_height - design.nutritional_facts_position['top']*mm, max_width=design.nutritional_facts_position['max_width']*mm, font_size=design.nutritional_heading_font_size)
        draw_multiline_text(c, nutritional_lines, content_x + design.nutritional_facts_position['left']*mm, content_y + content_height - (design.nutritional_facts_position['top'] + (design.nutritional_facts_font_size*0.7))*mm, max_width=design.nutritional_facts_position['max_width']*mm, font_size=design.nutritional_facts_font_size)
    else:
        draw_multiline_text(c, nutritional_lines, content_x + design.nutritional_facts_position['left']*mm, content_y + content_height - design.nutritional_facts_position['top']*mm, max_width=design.nutritional_facts_position['max_width']*mm, font_size=design.nutritional_facts_font_size)

    # Allergen Information box
    allergen_lines = sticker.allergen_information.split("\n")
    if design.print_allergen_heading:
        draw_wrapped_text(c, design.allergen_heading_text, content_x + design.allergen_info_position['left']*mm, content_y + content_height - design.allergen_info_position['top']*mm, max_width=design.allergen_info_position['max_width']*mm, font_size=design.allergen_heading_font_size)
        draw_multiline_text(c, allergen_lines, content_x + design.allergen_info_position['left']*mm, content_y + content_height - (design.allergen_info_position['top'] + (design.allergen_info_font_size*0.7))*mm, max_width=design.allergen_info_position['max_width']*mm, font_size=design.allergen_info_font_size)
    else:
        draw_multiline_text(c, allergen_lines, content_x + design.allergen_info_position['left']*mm, content_y + content_height - design.allergen_info_position['top']*mm, max_width=design.allergen_info_position['max_width']*mm, font_size=design.allergen_info_font_size)

    # Ingredients box
    ingredients_lines = sticker.ingredients.split("\n")
    if design.print_ingredients_heading:
        draw_wrapped_text(c, design.ingredients_heading_text, content_x + design.ingredients_position['left']*mm, content_y + content_height - design.ingredients_position['top']*mm, max_width=design.ingredients_position['max_width']*mm, font_size=design.ingredients_heading_font_size)
        draw_multiline_text(c, ingredients_lines, content_x + design.ingredients_position['left']*mm, content_y + content_height - (design.ingredients_position['top'] + (design.ingredients_font_size*0.7))*mm, max_width=design.ingredients_position['max_width']*mm, font_size=design.ingredients_font_size)
    else:
        draw_multiline_text(c, ingredients_lines, content_x + design.ingredients_position['left']*mm, content_y + content_height - design.ingredients_position['top']*mm, max_width=design.ingredients_position['max_width']*mm, font_size=design.ingredients_font_size)

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

def draw_nutritional_heading(c, text, x, y, max_width, font_size):
    lines = text.split('\n')
    if len(lines) != 2:
        raise ValueError("Nutritional heading must have exactly two lines")

    # Set the text color to black
    c.setFillColor(black)

    # Draw the first line (Nutritional Facts) with the larger font size
    c.setFont('RobotoCondensed', font_size)
    c.drawString(x, y, lines[0])

    # Draw the second line (Serving size) with a slightly smaller font size
    c.setFont('RobotoCondensed', font_size - 1.5)
    c.drawString(x, y - font_size * 1.0, lines[1])

def create_stickers_pdf(stickers):
    # Create a PDF file in the root directory
    pdf_path = os.path.join(current_app.root_path, '..', 'stickers_to_print.pdf')
    create_sticker_pdf(stickers, pdf_path)
    return pdf_path