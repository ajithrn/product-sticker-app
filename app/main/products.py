from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required
from flask_paginate import Pagination, get_page_parameter
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import desc
import random
import string

from app import db
from app.models import Product, ProductCategory
from app.forms import ProductForm, ProductSearchForm
from .utils import get_api_key, generate_ingredients, generate_nutritional_facts, generate_allergen_info

from . import main

# Constants for pagination
PER_PAGE = 10

def generate_batch_number(product_name):
    """
    Helper function to generate a unique batch number for a product.
    Format: B<Product Initials><Date><Time><Random>
    """
    # Get product initials
    initials = ''.join([word[0] for word in product_name.split()]).upper()
    
    # Get current timestamp with seconds
    timestamp = datetime.now().strftime('%d%H%M')
    
    # Add random characters to ensure uniqueness
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    
    return f'B{initials}{timestamp}{random_chars}'

@main.route('/products', methods=['GET'])
@login_required
def list_products():
    """
    View function for listing all products.
    Handles AJAX search and regular page display with table layout.
    """
    page = request.args.get(get_page_parameter(), type=int, default=1)
    form = ProductSearchForm()

    search_term = request.args.get('q') 

    if search_term is not None:  # Check if search_term is provided
        # AJAX search request
        if search_term:  # Check if search_term is not empty
            products = Product.query.filter(
                Product.name.ilike(f'%{search_term}%')
            ).order_by(Product.name).all()
            return jsonify([{
                'id': p.id,
                'name': p.name,
                'category': p.category.name if p.category else 'N/A',
                'net_weight': p.net_weight,
                'rate': str(p.rate)
            } for p in products])
        return jsonify([])
    
    # Regular product listing with pagination
    products_pagination = Product.query.order_by(
        desc(Product.updated_at)
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )
    
    return render_template(
        'products.html',
        products=products_pagination.items,
        pagination=Pagination(
            page=page,
            total=products_pagination.total,
            search=False,
            per_page=PER_PAGE,
            css_framework='bootstrap4'
        ),
        form=form
    )

@main.route('/search_products', methods=['GET', 'POST']) 
@login_required
def search_products_post():
    """
    Handles both GET (for AJAX) and POST requests for product search.
    Includes shelf life and net_weight in the response for AJAX.
    """
    form = ProductSearchForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            return redirect(url_for('main.list_products', q=form.search.data))
        return redirect(url_for('main.list_products'))
    
    search_term = request.args.get('q')
    if search_term:
        products = Product.query.filter(
            Product.name.ilike(f'%{search_term}%')
        ).order_by(Product.name).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'shelf_life': p.shelf_life,
            'category': p.category.name if p.category else 'N/A',
            'net_weight': p.net_weight,
            'rate': str(p.rate)
        } for p in products])
    return jsonify([])

@main.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """
    View function for creating a new product.
    """
    form = ProductForm()
    categories = ProductCategory.query.order_by(ProductCategory.name).all()
    form.category_id.choices = [(str(c.id), c.name) for c in categories]
    
    if form.validate_on_submit():
        try:
            category_name = form.category_id.data
            category = ProductCategory.query.filter_by(name=category_name).first()
            if not category:
                category = ProductCategory(name=category_name)
                db.session.add(category)
                db.session.commit()
            
            product = Product(
                name=form.name.data,
                category_id=category.id,
                rate=form.rate.data,
                net_weight=form.net_weight.data,
                shelf_life=form.shelf_life.data,
                ingredients=form.ingredients.data,
                nutritional_facts=form.nutritional_facts.data,
                allergen_information=form.allergen_information.data
            )
            db.session.add(product)
            db.session.commit()
            flash('Product has been created!', 'success')
            return redirect(url_for('main.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating product: {str(e)}', 'danger')
    
    return render_template('product.html', form=form)

@main.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """
    View function for editing an existing product.
    """
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    is_duplicate = request.args.get('is_duplicate', 'false') == 'true'

    if form.validate_on_submit():
        try:
            category_name = form.category_id.data
            category = ProductCategory.query.filter_by(name=category_name).first()
            if not category:
                category = ProductCategory(name=category_name)
                db.session.add(category)
                db.session.commit()
            
            product.name = form.name.data
            product.category_id = category.id
            product.rate = form.rate.data
            product.net_weight = form.net_weight.data
            product.shelf_life = form.shelf_life.data
            product.ingredients = form.ingredients.data
            product.nutritional_facts = form.nutritional_facts.data
            product.allergen_information = form.allergen_information.data
            
            db.session.commit()
            flash('Product has been updated!', 'success')
            return redirect(url_for('main.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.name.data = product.name
        form.category_id.data = product.category.name if product.category else ''
        form.rate.data = product.rate
        form.net_weight.data = product.net_weight
        form.shelf_life.data = product.shelf_life
        form.ingredients.data = product.ingredients
        form.nutritional_facts.data = product.nutritional_facts
        form.allergen_information.data = product.allergen_information

    return render_template(
        'product.html',
        form=form,
        product=product,
        is_duplicate=is_duplicate
    )

@main.route('/product/<int:product_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    """
    View function for deleting a product.
    """
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product has been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')
    return redirect(url_for('main.list_products'))

@main.route('/product/<int:product_id>/duplicate', methods=['GET'])
@login_required
def duplicate_product(product_id):
    """
    View function for duplicating a product.
    """
    product = Product.query.get_or_404(product_id)
    try:
        duplicate = Product(
            name=product.name + " (Copy)",
            category_id=product.category_id,
            rate=product.rate,
            net_weight=product.net_weight,
            shelf_life=product.shelf_life,
            ingredients=product.ingredients,
            nutritional_facts=product.nutritional_facts,
            allergen_information=product.allergen_information
        )
        db.session.add(duplicate)
        db.session.commit()
        return redirect(url_for('main.edit_product', product_id=duplicate.id, is_duplicate='true'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error duplicating product: {str(e)}', 'danger')
        return redirect(url_for('main.list_products'))

@main.route('/cancel_edit/<int:product_id>/<string:is_duplicate>')
@login_required
def cancel_edit(product_id, is_duplicate):
    """
    View function for canceling the edit of a product.
    If the product is a duplicate, it will be deleted.
    """
    product = Product.query.get_or_404(product_id)
    if is_duplicate == 'true':
        try:
            db.session.delete(product)
            db.session.commit()
            flash('Duplicate product discarded.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Error discarding duplicate: {str(e)}', 'danger')
    return redirect(url_for('main.list_products'))

# AI Generation routes
@main.route('/auto_generate_ingredients')
@login_required
def auto_generate_ingredients():
    """
    Route to automatically generate ingredients for a given product name.
    """
    product_name = request.args.get('product_name')
    api_key = get_api_key()

    if not api_key:
        return jsonify({'error': 'API key not found or decryption failed'}), 500

    try:
        ingredients = generate_ingredients(product_name, api_key)
        return jsonify({'ingredients': ingredients})
    except Exception as e:
        current_app.logger.error(f"Error generating ingredients: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/auto_generate_nutritional_facts', methods=['POST'])
@login_required
def auto_generate_nutritional_facts():
    """
    Generate nutritional facts based on provided ingredients.
    """
    ingredients = request.json.get('ingredients')
    api_key = get_api_key()

    if not api_key:
        return jsonify({'error': 'API key not found or decryption failed'}), 500

    try:
        nutritional_facts = generate_nutritional_facts(ingredients, api_key)
        return jsonify({'nutritional_facts': nutritional_facts})
    except Exception as e:
        current_app.logger.error(f"Error generating nutritional facts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/auto_generate_allergen_info', methods=['POST'])
@login_required
def auto_generate_allergen_info():
    """
    Generate allergen information based on provided ingredients.
    """
    ingredients = request.json.get('ingredients')
    api_key = get_api_key()

    if not api_key:
        return jsonify({'error': 'API key not found or decryption failed'}), 500

    try:
        allergen_info = generate_allergen_info(ingredients, api_key)
        return jsonify({'allergen_info': allergen_info})
    except Exception as e:
        current_app.logger.error(f"Error generating allergen info: {str(e)}")
        return jsonify({'error': str(e)}), 500
