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
