from flask import render_template, redirect, url_for, flash, request, send_file
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, bcrypt
from app.models import User, Product, ProductCategory, PrintJob
from app.forms import LoginForm, RegisterForm, ProductForm, PrintForm, ProductSearchForm, CategoryForm, ProfileForm, UserForm
from app.sticker import create_sticker_pdf, Sticker
import io
from datetime import datetime, timedelta
from app.main import main
from flask_paginate import Pagination, get_page_parameter

# Constants for pagination
PER_PAGE = 10

@main.route('/')
@login_required
def index():
    num_products = Product.query.count()
    num_categories = ProductCategory.query.count()
    num_print_jobs = PrintJob.query.count()
    return render_template('index.html', num_products=num_products, num_categories=num_categories, num_print_jobs=num_print_jobs)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login Successful.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    admin_check = User.query.filter_by(role='store_admin').first()
    if not admin_check:
        flash('No admin user found. Please contact the administrator.', 'danger')
        return redirect(url_for('main.login'))

    if current_user.role != 'store_admin':
        flash('You do not have permission to register a new user.', 'danger')
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User has been created!', 'success')
        return redirect(url_for('main.index'))
    return render_template('register.html', form=form)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('user_profile.html', form=form)

@main.route('/user_management')
@login_required
def user_management():
    if current_user.role != 'store_admin':
        flash('You do not have permission to access user management.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get(get_page_parameter(), type=int, default=1)
    users_pagination = User.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    users = users_pagination.items
    pagination = Pagination(page=page, total=users_pagination.total, search=False, per_page=PER_PAGE, css_framework='bootstrap4')
    return render_template('user_management.html', users=users, pagination=pagination)

@main.route('/user_management/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if current_user.role != 'store_admin':
        flash('You do not have permission to create a new user.', 'danger')
        return redirect(url_for('main.user_management'))
    
    form = UserForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data,
            name=form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('New user has been created!', 'success')
        return redirect(url_for('main.user_management'))
    return render_template('user_form.html', form=form, title="Create New User")

import logging

@main.route('/user_management/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'store_admin':
        flash('You do not have permission to edit this user.', 'danger')
        return redirect(url_for('main.user_management'))

    user = User.query.get_or_404(user_id)
    form = UserForm()
    if form.validate_on_submit():
        # Update fields except password
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.name = form.name.data

        # Update password only if provided
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        
        db.session.commit()
        flash('User details have been updated!', 'success')
        return redirect(url_for('main.user_management'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.name.data = user.name
    return render_template('user_form.html', form=form, title="Edit User")



@main.route('/user_management/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'store_admin':
        flash('You do not have permission to delete this user.', 'danger')
        return redirect(url_for('main.user_management'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted!', 'success')
    return redirect(url_for('main.user_management'))
    
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
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
    category = ProductCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category has been deleted!', 'success')
    return redirect(url_for('main.list_categories'))

@main.route('/categories', methods=['GET'])
@login_required
def list_categories():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    categories_pagination = ProductCategory.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    categories = categories_pagination.items
    pagination = Pagination(page=page, total=categories_pagination.total, search=False, per_page=PER_PAGE, css_framework='bootstrap4')
    return render_template('categories.html', categories=categories, pagination=pagination)

@main.route('/search_products', methods=['POST'])
@login_required
def search_products():
    form = ProductSearchForm()
    if form.validate_on_submit():
        search_term = form.search.data
        products = Product.query.filter(Product.name.ilike(f'%{search_term}%')).all()
        return render_template('search.html', products=products, form=form)
    return redirect(url_for('main.list_products'))

@main.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in ProductCategory.query.all()]
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            category_id=form.category_id.data,
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
        
    return render_template('product.html', form=form, product=product, is_duplicate=is_duplicate)

@main.route('/products', methods=['GET'])
@login_required
def list_products():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    form = ProductSearchForm()  # Initialize the form
    products_pagination = Product.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    products = products_pagination.items
    pagination = Pagination(page=page, total=products_pagination.total, search=False, per_page=PER_PAGE, css_framework='bootstrap4')
    return render_template('products.html', products=products, pagination=pagination, form=form)

@main.route('/product/<int:product_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product has been deleted!', 'success')
    return redirect(url_for('main.list_products'))

@main.route('/product/<int:product_id>/duplicate', methods=['GET'])
@login_required
def duplicate_product(product_id):
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
    return redirect(url_for('main.edit_product', product_id=duplicate.id, is_duplicate='true'))

@main.route('/cancel_edit/<int:product_id>/<string:is_duplicate>')
@login_required
def cancel_edit(product_id, is_duplicate):
    product = Product.query.get_or_404(product_id)
    if is_duplicate == 'true':
        db.session.delete(product)
        db.session.commit()
        flash('Duplicate product discarded.', 'info')
    return redirect(url_for('main.list_products'))

def generate_batch_number(product_name):
    initials = ''.join([word[0] for word in product_name.split()]).upper()
    date_str = datetime.now().strftime('%d%m%y')
    return f'B{initials}{date_str}'

@main.route('/analytics')
@login_required
def analytics_dashboard():
    total_print_jobs = PrintJob.query.count()
    total_stickers = sum(job.quantity for job in PrintJob.query.all())

    # Calculate total value (number of stickers * value of product)
    total_value = 0
    print_jobs = PrintJob.query.all()
    for job in print_jobs:
        product = Product.query.filter_by(name=job.product_name).first()
        if product:
            total_value += job.quantity * float(product.rate)

    return render_template('analytics.html', total_print_jobs=total_print_jobs, total_stickers=total_stickers, total_value=total_value)


@main.route('/print', methods=['GET', 'POST'])
@login_required
def print_stickers():
    form = PrintForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]
    
    if request.method == 'POST' and form.validate_on_submit():
        product = Product.query.get(form.product_id.data)
        quantity = form.quantity.data

        mfg_date = form.mfg_date.data or datetime.now().date()
        exp_date = form.exp_date.data or mfg_date + timedelta(days=product.shelf_life)

        batch_number = generate_batch_number(product.name)

        stickers = [
            Sticker(
                product_name=product.name,
                rate=product.rate,
                mfg_date=mfg_date,
                exp_date=exp_date,
                net_weight=product.net_weight,
                ingredients=product.ingredients,
                nutritional_facts=product.nutritional_facts,
                batch_number=batch_number,
                allergen_information=product.allergen_information
            )
            for _ in range(quantity)
        ]

        pdf_output = io.BytesIO()
        create_sticker_pdf(stickers, pdf_output, 'static/bg.png')
        pdf_output.seek(0)

        print_job = PrintJob(
            product_name=product.name,
            quantity=quantity,
            printed_by=current_user.username,
            batch_number=batch_number,
        )
        db.session.add(print_job)
        db.session.commit()

        return send_file(pdf_output, as_attachment=True, download_name='stickers.pdf', mimetype='application/pdf')

    if request.method == 'GET':
        form.mfg_date.data = datetime.now().date()
        form.exp_date.data = None

    return render_template('print.html', form=form)

@main.route('/print/<int:product_id>', methods=['GET', 'POST'])
@login_required
def print_stickers_for_product(product_id):
    form = PrintForm()
    product = Product.query.get(product_id)
    form.product_id.choices = [(product.id, product.name)]

    if request.method == 'POST' and form.validate_on_submit():
        quantity = form.quantity.data

        mfg_date = form.mfg_date.data or datetime.now().date()
        exp_date = form.exp_date.data or mfg_date + timedelta(days=product.shelf_life)

        batch_number = generate_batch_number(product.name)

        stickers = [
            Sticker(
                product_name=product.name,
                rate=product.rate,
                mfg_date=mfg_date,
                exp_date=exp_date,
                net_weight=product.net_weight,
                ingredients=product.ingredients,
                nutritional_facts=product.nutritional_facts,
                batch_number=batch_number,
                allergen_information=product.allergen_information
            )
            for _ in range(quantity)
        ]

        pdf_output = io.BytesIO()
        create_sticker_pdf(stickers, pdf_output, 'static/bg.png')
        pdf_output.seek(0)

        print_job = PrintJob(
            product_name=product.name,
            quantity=quantity,
            printed_by=current_user.username,
            batch_number=batch_number,
        )
        db.session.add(print_job)
        db.session.commit()

        return send_file(pdf_output, as_attachment=True, download_name='stickers.pdf', mimetype='application/pdf')

    if request.method == 'GET':
        form.product_id.data = product.id
        form.mfg_date.data = datetime.now().date()
        form.exp_date.data = datetime.now().date() + timedelta(days=product.shelf_life)

    return render_template('print.html', form=form)

@main.route('/print_jobs', methods=['GET'])
@login_required
def print_jobs():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    print_jobs_pagination = PrintJob.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    print_jobs = print_jobs_pagination.items
    pagination = Pagination(page=page, total=print_jobs_pagination.total, search=False, per_page=PER_PAGE, css_framework='bootstrap4')
    return render_template('print_jobs.html', print_jobs=print_jobs, pagination=pagination)
