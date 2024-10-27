from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)  # Increased length for scrypt hash
    role = db.Column(db.String(50), nullable=False, default='staff')
    name = db.Column(db.String(100))
    print_jobs = db.relationship('PrintJob', backref='user', lazy=True)

    __table_args__ = (
        db.CheckConstraint('length(username) >= 3', name='check_username_length'),
        db.CheckConstraint('length(password) >= 8', name='check_password_length'),
        db.CheckConstraint("role IN ('staff', 'store_admin')", name='check_valid_role'),
    )

class ProductCategory(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')

class Product(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id', ondelete='CASCADE'), nullable=False)
    rate = db.Column(db.Numeric(10, 2), nullable=False)
    net_weight = db.Column(db.String(20), nullable=False)
    shelf_life = db.Column(db.Integer, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    nutritional_facts = db.Column(db.Text, nullable=False)
    allergen_information = db.Column(db.Text, nullable=False)
    print_jobs = db.relationship('PrintJob', backref='product', lazy=True)

    __table_args__ = (
        db.CheckConstraint('rate >= 0', name='check_rate_positive'),
        db.CheckConstraint('shelf_life > 0', name='check_shelf_life_positive'),
    )

class PrintJob(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='SET NULL'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    print_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    batch_number = db.Column(db.String(50), nullable=False, unique=True, index=True)

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_quantity_positive'),
    )

class StoreInfo(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    gst_number = db.Column(db.String(20), nullable=False, unique=True)
    fssai_number = db.Column(db.String(20), nullable=False, unique=True)

    __table_args__ = (
        db.CheckConstraint('length(phone_number) >= 10', name='check_phone_number_length'),
        db.CheckConstraint('length(gst_number) >= 15', name='check_gst_number_length'),
        db.CheckConstraint('length(fssai_number) >= 14', name='check_fssai_number_length'),
    )

class StickerDesign(TimestampMixin, db.Model):
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
    print_nutritional_heading = db.Column(db.Boolean, default=True)
    print_allergen_heading = db.Column(db.Boolean, default=True)
    print_ingredients_heading = db.Column(db.Boolean, default=True)
    nutritional_heading_text = db.Column(db.String(100), nullable=False, default="Nutritional Facts:\nServing size 100g")
    allergen_heading_text = db.Column(db.String(100), nullable=False, default="Allergen Information:")
    ingredients_heading_text = db.Column(db.String(100), nullable=False, default="Ingredients:")
    nutritional_heading_font_size = db.Column(db.Float, nullable=False, default=8.0)
    allergen_heading_font_size = db.Column(db.Float, nullable=False, default=8.0)
    ingredients_heading_font_size = db.Column(db.Float, nullable=False, default=8.0)
    mrp_font_size = db.Column(db.Float, nullable=False, default=6.0)
    ingredients_font_size = db.Column(db.Float, nullable=False, default=6.0)
    allergen_info_font_size = db.Column(db.Float, nullable=False, default=6.0)
    nutritional_facts_font_size = db.Column(db.Float, nullable=False, default=6.0)
    printer_type = db.Column(db.String(20), nullable=False, default='label')
    paper_size = db.Column(db.String(20), nullable=False, default='A4')
    custom_paper_width = db.Column(db.Float, nullable=True)
    custom_paper_height = db.Column(db.Float, nullable=True)
    paper_orientation = db.Column(db.String(20), nullable=False, default='portrait')

    __table_args__ = (
        db.CheckConstraint('heading_font_size > 0', name='check_heading_font_size_positive'),
        db.CheckConstraint('content_font_size > 0', name='check_content_font_size_positive'),
        db.CheckConstraint('custom_paper_width > 0', name='check_custom_paper_width_positive'),
        db.CheckConstraint('custom_paper_height > 0', name='check_custom_paper_height_positive'),
        db.CheckConstraint("printer_type IN ('label', 'normal')", name='check_valid_printer_type'),
        db.CheckConstraint("paper_size IN ('A4', 'A5', 'custom')", name='check_valid_paper_size'),
        db.CheckConstraint("paper_orientation IN ('portrait', 'landscape')", name='check_valid_paper_orientation'),
    )

class Setting(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auto_backup_time = db.Column(db.String(5), nullable=True)
    gpt_api_key_hash = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "auto_backup_time ~ '^([01]?[0-9]|2[0-3]):[0-5][0-9]$'",
            name='check_time_format'
        ),
    )
