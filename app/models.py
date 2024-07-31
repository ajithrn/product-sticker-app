from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db  # Import db from app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='staff')
    name = db.Column(db.String(150))
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
    page_size = db.Column(db.JSON, nullable=False, default={"width": 85.0, "height": 95.0, "margin": 2.5})
    product_name_position = db.Column(db.JSON, nullable=False, default={"top": 43.0, "left": 36.0, "max_width": 30.0})
    mrp_position = db.Column(db.JSON, nullable=False, default={"top": 47.0, "left": 36.0, "max_width": 30.0})
    net_weight_position = db.Column(db.JSON, nullable=False, default={"top": 49.5, "left": 36.0, "max_width": 30.0})
    mfg_date_position = db.Column(db.JSON, nullable=False, default={"top": 52.0, "left": 36.0, "max_width": 30.0})
    exp_date_position = db.Column(db.JSON, nullable=False, default={"top": 54.5, "left": 36.0, "max_width": 30.0})
    batch_no_position = db.Column(db.JSON, nullable=False, default={"top": 57.0, "left": 36.0, "max_width": 30.0})
    ingredients_position = db.Column(db.JSON, nullable=False, default={"top": 68.0, "left": 36.0, "max_width": 40.0})
    nutritional_facts_position = db.Column(db.JSON, nullable=False, default={"top": 50.0, "left": 8.0, "max_width": 30.0})
    allergen_info_position = db.Column(db.JSON, nullable=False, default={"top": 74.0, "left": 8.0, "max_width": 30.0})
    heading_font_size = db.Column(db.Float, nullable=False, default=8.0)
    content_font_size = db.Column(db.Float, nullable=False, default=6.0)
    bg_image = db.Column(db.String(255))
    use_bg_image = db.Column(db.Boolean, default=False)