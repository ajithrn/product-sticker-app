from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db  # Import db from app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='staff')  # Add role field
    name = db.Column(db.String(150))  # Additional profile info
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=False)
    rate = db.Column(db.String(100), nullable=False)
    net_weight = db.Column(db.String(20), nullable=False)
    shelf_life = db.Column(db.Integer, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    nutritional_facts = db.Column(db.Text, nullable=False)
    allergen_information = db.Column(db.Text, nullable=False)

class PrintJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    printed_by = db.Column(db.String(150), nullable=False)
    print_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    batch_number = db.Column(db.String(150), nullable=False)

class StoreInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    gst_number = db.Column(db.String(20), nullable=False)
    fssai_number = db.Column(db.String(20), nullable=False)

class StickerDesign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_width = db.Column(db.Float, nullable=False, default=85.0)
    page_height = db.Column(db.Float, nullable=False, default=95.0)
    page_margin = db.Column(db.Float, nullable=False, default=2.5)
    mrp_top = db.Column(db.Float, nullable=False, default=42.0)
    mrp_left = db.Column(db.Float, nullable=False, default=36.0)
    mrp_max_width = db.Column(db.Float, nullable=False, default=30.0)
    net_weight_top = db.Column(db.Float, nullable=False, default=49.5)
    net_weight_left = db.Column(db.Float, nullable=False, default=36.0)
    net_weight_max_width = db.Column(db.Float, nullable=False, default=30.0)
    mfg_top = db.Column(db.Float, nullable=False, default=52.0)
    mfg_left = db.Column(db.Float, nullable=False, default=36.0)
    mfg_max_width = db.Column(db.Float, nullable=False, default=30.0)
    exp_top = db.Column(db.Float, nullable=False, default=54.5)
    exp_left = db.Column(db.Float, nullable=False, default=36.0)
    exp_max_width = db.Column(db.Float, nullable=False, default=30.0)
    batch_no_top = db.Column(db.Float, nullable=False, default=57.0)
    batch_no_left = db.Column(db.Float, nullable=False, default=36.0)
    batch_no_max_width = db.Column(db.Float, nullable=False, default=30.0)
    ingredients_top = db.Column(db.Float, nullable=False, default=68.0)
    ingredients_left = db.Column(db.Float, nullable=False, default=36.0)
    ingredients_max_width = db.Column(db.Float, nullable=False, default=40.0)
    nutritional_facts_top = db.Column(db.Float, nullable=False, default=50.0)
    nutritional_facts_left = db.Column(db.Float, nullable=False, default=8.0)
    nutritional_facts_max_width = db.Column(db.Float, nullable=False, default=30.0)
    allergen_info_top = db.Column(db.Float, nullable=False, default=62.0)
    allergen_info_left = db.Column(db.Float, nullable=False, default=8.0)
    allergen_info_max_width = db.Column(db.Float, nullable=False, default=30.0)
    heading_font_size = db.Column(db.Float, nullable=False, default=8.0)
    content_font_size = db.Column(db.Float, nullable=False, default=6.0)
    bg_image = db.Column(db.String(255))
    use_bg_image = db.Column(db.Boolean, default=False)