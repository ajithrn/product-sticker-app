from flask import render_template, redirect, url_for, flash, request
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
