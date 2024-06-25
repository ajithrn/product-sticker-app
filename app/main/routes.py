from flask import render_template, redirect, url_for, flash, request
from flask_login import (
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User, Product, ProductCategory, PrintJob
from app.forms import LoginForm, RegisterForm

from . import main

@main.route('/')
@login_required
def index():
    """
    View function for the index page.
    It displays a dashboard with the total number of products, categories, and print jobs.
    """
    num_products = Product.query.count()
    num_categories = ProductCategory.query.count()
    num_print_jobs = PrintJob.query.count()
    return render_template(
        'index.html',
        num_products=num_products,
        num_categories=num_categories,
        num_print_jobs=num_print_jobs
    )


@main.route('/login', methods=['GET', 'POST'])
def login():
    """
    View function for the login page.
    Handles user login.
    """
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
    """
    View function for the registration page.
    Handles new user registration. Only accessible by the store admin.
    """
    if not current_user.is_authenticated or current_user.role != 'store_admin':
        flash('You do not have permission to access this page.', 'danger')
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


@main.route('/logout')
@login_required
def logout():
    """
    View function for logging out the current user.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

