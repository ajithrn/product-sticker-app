from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from flask_paginate import Pagination, get_page_parameter
from datetime import datetime, timedelta

from app import db
from app.models import Product, ProductCategory
from app.forms import ProductForm, ProductSearchForm

from . import main

# Constants for pagination
PER_PAGE = 10

def generate_batch_number(product_name):
    """
    Helper function to generate a batch number for a product.
    The batch number now includes the hour.
    """
    initials = ''.join([word[0] for word in product_name.split()]).upper()
    date_str = datetime.now().strftime('%d%m%y%H')  
    return f'B{initials}{date_str}'

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
            products = Product.query.filter(Product.name.ilike(f'%{search_term}%')).all()
            return jsonify([{'id': p.id, 'name': p.name, 'category': p.category.name} for p in products])
        else:
            # Empty search term, return empty JSON array
            return jsonify([])  
    else:
        # Regular product listing with pagination
        products_pagination = Product.query.order_by(
            Product.id.desc()
        ).paginate(
            page=page,
            per_page=PER_PAGE,
            error_out=False
        )
        products = products_pagination.items
        pagination = Pagination(
            page=page,
            total=products_pagination.total,
            search=False,
            per_page=PER_PAGE,
            css_framework='bootstrap4'
        )
        return render_template(
            'products.html',
            products=products,
            pagination=pagination,
            form=form
        )


@main.route('/search_products', methods=['GET', 'POST']) 
@login_required
def search_products_post():
    """
    Handles both GET (for AJAX) and POST requests for product search.
    Includes shelf life in the response for AJAX.
    """
    form = ProductSearchForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            search_term = form.search.data
            return redirect(url_for('main.list_products', q=search_term))
        return redirect(url_for('main.list_products'))
    elif request.method == 'GET':
        search_term = request.args.get('q')
        if search_term:
            products = Product.query.filter(Product.name.ilike(f'%{search_term}%')).all()
            return jsonify([{'id': p.id, 'name': p.name, 'shelf_life': p.shelf_life} for p in products])
        return jsonify([])


@main.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """
    View function for creating a new product.
    """
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in ProductCategory.query.all()]
    if form.validate_on_submit():
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
    return render_template('product.html', form=form)


@main.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """
    View function for editing an existing product.
    """
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in ProductCategory.query.all()]
    is_duplicate = request.args.get('is_duplicate', 'false') == 'true'

    if form.validate_on_submit():
        product.name = form.name.data
        product.category_id = form.category_id.data
        product.rate = form.rate.data
        product.net_weight = form.net_weight.data
        product.shelf_life = form.shelf_life.data
        product.ingredients = form.ingredients.data
        product.nutritional_facts = form.nutritional_facts.data
        product.allergen_information = form.allergen_information.data
        db.session.commit()
        flash('Product has been updated!', 'success')
        return redirect(url_for('main.list_products'))
    elif request.method == 'GET':
        form.name.data = product.name
        form.category_id.data = product.category_id
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
    db.session.delete(product)
    db.session.commit()
    flash('Product has been deleted!', 'success')
    return redirect(url_for('main.list_products'))


@main.route('/product/<int:product_id>/duplicate', methods=['GET'])
@login_required
def duplicate_product(product_id):
    """
    View function for duplicating a product.
    """
    product = Product.query.get_or_404(product_id)
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
    return redirect(
        url_for(
            'main.edit_product',
            product_id=duplicate.id,
            is_duplicate='true'
        )
    )


@main.route('/cancel_edit/<int:product_id>/<string:is_duplicate>')
@login_required
def cancel_edit(product_id, is_duplicate):
    """
    View function for canceling the edit of a product.
    If the product is a duplicate, it will be deleted.
    """
    product = Product.query.get_or_404(product_id)
    if is_duplicate == 'true':
        db.session.delete(product)
        db.session.commit()
        flash('Duplicate product discarded.', 'info')
    return redirect(url_for('main.list_products'))