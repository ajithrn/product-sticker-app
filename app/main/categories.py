from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import desc

from app import db
from app.models import ProductCategory
from app.forms import CategoryForm

from . import main

# Constants for pagination
PER_PAGE = 10

@main.route('/categories')
@login_required
def list_categories():
    """
    View function for listing all product categories.
    Orders by last updated first.
    """
    page = request.args.get(get_page_parameter(), type=int, default=1)
    categories_pagination = ProductCategory.query.order_by(
        desc(ProductCategory.updated_at)
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )
    
    return render_template(
        'categories.html',
        categories=categories_pagination.items,
        pagination=Pagination(
            page=page,
            total=categories_pagination.total,
            search=False,
            per_page=PER_PAGE,
            css_framework='bootstrap4'
        )
    )

@main.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """
    View function for creating a new product category.
    """
    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category = ProductCategory(name=form.name.data)
            db.session.add(category)
            db.session.commit()
            flash('Category has been created!', 'success')
            return redirect(url_for('main.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'danger')
    return render_template('category.html', form=form)

@main.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """
    View function for editing an existing product category.
    """
    category = ProductCategory.query.get_or_404(category_id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        try:
            category.name = form.name.data
            db.session.commit()
            flash('Category has been updated!', 'success')
            return redirect(url_for('main.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.name.data = category.name
    
    return render_template('category.html', form=form)

@main.route('/category/delete/<int:category_id>', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    """
    View function for deleting a product category.
    Products in this category will also be deleted due to cascade.
    """
    category = ProductCategory.query.get_or_404(category_id)
    try:
        # Count products that will be affected
        products_count = len(category.products)
        
        db.session.delete(category)
        db.session.commit()
        
        flash(f'Category and {products_count} associated products have been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')
    
    return redirect(url_for('main.list_categories'))

@main.route('/search_categories')
@login_required
def search_categories():
    """
    View function for searching categories.
    This handles AJAX requests to search for categories as the user types.
    Returns a JSON response with the matching categories.
    """
    search_term = request.args.get('q')
    if search_term:
        categories = ProductCategory.query.filter(
            ProductCategory.name.ilike(f'%{search_term}%')
        ).order_by(ProductCategory.name).all()
        
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'product_count': len(c.products)
        } for c in categories])
    return jsonify([])

@main.route('/add_category', methods=['POST'])
@login_required
def add_category():
    """
    View function for adding a new category via AJAX.
    This handles AJAX requests to add a new category when the user types a category that doesn't exist.
    Returns a JSON response with the new category's details.
    """
    category_name = request.form.get('name')
    if not category_name:
        return jsonify({'error': 'Category name is required'}), 400
        
    try:
        # Check if category already exists
        existing_category = ProductCategory.query.filter(
            ProductCategory.name.ilike(category_name)
        ).first()
        
        if existing_category:
            return jsonify({'error': 'Category already exists'}), 400
            
        # Create new category
        category = ProductCategory(name=category_name)
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'id': category.id,
            'name': category.name,
            'product_count': 0
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
