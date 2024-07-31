from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_paginate import Pagination, get_page_parameter

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
    """
    page = request.args.get(get_page_parameter(), type=int, default=1)
    categories_pagination = ProductCategory.query.order_by(
        ProductCategory.id.desc()
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )
    categories = categories_pagination.items
    pagination = Pagination(
        page=page,
        total=categories_pagination.total,
        search=False,
        per_page=PER_PAGE,
        css_framework='bootstrap4'
    )
    return render_template(
        'categories.html',
        categories=categories,
        pagination=pagination
    )

@main.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """
    View function for creating a new product category.
    """
    form = CategoryForm()
    if form.validate_on_submit():
        category = ProductCategory(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('Category has been created!', 'success')
        return redirect(url_for('main.list_categories'))
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
        category.name = form.name.data
        db.session.commit()
        flash('Category has been updated!', 'success')
        return redirect(url_for('main.list_categories'))
    elif request.method == 'GET':
        form.name.data = category.name
    return render_template('category.html', form=form)

@main.route('/category/delete/<int:category_id>', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    """
    View function for deleting a product category.
    """
    category = ProductCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category has been deleted!', 'success')
    return redirect(url_for('main.list_categories'))

@main.route('/search_categories')
@login_required
def search_categories():
    """
    View function for searching categories.
    This handles AJAX requests to search for categories as the user types into the category field.
    Returns a JSON response with the matching categories.
    """
    search_term = request.args.get('q')
    if search_term:
        categories = ProductCategory.query.filter(ProductCategory.name.ilike(f'%{search_term}%')).all()
        return jsonify([{'id': c.id, 'name': c.name} for c in categories])
    return jsonify([])


@main.route('/add_category', methods=['POST'])
@login_required
def add_category():
    """
    View function for adding a new category.
    This handles AJAX requests to add a new category when the user types a category that doesn't exist.
    Returns a JSON response with the new category's details.
    """
    category_name = request.form.get('name')
    if category_name:
        category = ProductCategory.query.filter_by(name=category_name).first()
        if not category:
            category = ProductCategory(name=category_name)
            db.session.add(category)
            db.session.commit()
            return jsonify({'id': category.id, 'name': category.name})
    return jsonify({'error': 'Category already exists or name is invalid'}), 400
