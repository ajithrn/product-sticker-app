from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import (
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

from app import db
from app.models import User, Product, ProductCategory, PrintJob, StoreInfo, StickerDesign
from app.forms import LoginForm, RegisterForm, StoreInfoForm
from .backups import read_auto_backup_time, set_auto_backup_time, create_backup

from . import main
import schedule

def store_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'store_admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main.context_processor
def inject_store_info():
    store_info = StoreInfo.query.first()
    return dict(store_info=store_info)

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
    store_info = StoreInfo.query.first()
    return render_template(
        'index.html',
        num_products=num_products,
        num_categories=num_categories,
        num_print_jobs=num_print_jobs,
        store_info=store_info
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
@store_admin_required
def register():
    """
    View function for the registration page.
    Handles new user registration. Only accessible by the store admin.
    """
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

@main.route('/settings', methods=['GET', 'POST'])
@login_required
@store_admin_required
def settings():
    auto_backup_time = read_auto_backup_time()
    store_info = StoreInfo.query.first()
    
    if store_info is None:
        store_info_form = StoreInfoForm()
    else:
        store_info_form = StoreInfoForm(obj=store_info)

    if request.method == 'POST':
        if 'set_backup_time' in request.form:
            hour, minute = request.form['time'].split(':')
            schedule.clear()  # Clear existing schedule
            schedule.every().day.at(f"{hour}:{minute}").do(create_backup)

            # Store the scheduled time
            set_auto_backup_time(f"{hour}:{minute}")

            flash('Automatic backup scheduled.', 'success')
        elif 'store_info_submit' in request.form:
            if store_info_form.validate_on_submit():
                if store_info is None:
                    store_info = StoreInfo()
                    db.session.add(store_info)
                store_info_form.populate_obj(store_info)
                db.session.commit()
                flash('Store information updated successfully.', 'success')
            else:
                flash('Error updating store information. Please check the form.', 'danger')
        
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html', auto_backup_time=auto_backup_time, store_info_form=store_info_form, store_info=store_info)

@main.route('/sticker-design', methods=['GET', 'POST'])
@login_required
@store_admin_required
def sticker_design():
    """
    View function for the sticker design page.
    Handles updating the sticker design settings.
    """
    design = StickerDesign.query.first()
    if design is None:
        design = StickerDesign()
        db.session.add(design)
        db.session.commit()

    if request.method == 'POST':
        try:
            # Update page size
            design.page_size = {
                "width": float(request.form['page_size_width']),
                "height": float(request.form['page_size_height']),
                "margin": float(request.form['page_size_margin'])
            }

            # Update positions of various elements
            element_positions = ['product_name', 'mrp', 'net_weight', 'mfg_date', 'exp_date', 'batch_no', 'ingredients', 'nutritional_facts', 'allergen_info']
            for element in element_positions:
                position = {
                    "top": float(request.form[f'{element}_position_top']),
                    "left": float(request.form[f'{element}_position_left']),
                    "max_width": float(request.form[f'{element}_position_max_width'])
                }
                setattr(design, f'{element}_position', position)

            design.heading_font_size = float(request.form['heading_font_size'])
            design.content_font_size = float(request.form['content_font_size'])
            design.use_bg_image = 'use_bg_image' in request.form

            if 'bg_image' in request.files:
                bg_image = request.files['bg_image']
                if bg_image.filename != '':
                    bg_image.save(os.path.join(current_app.root_path, 'static', 'images', bg_image.filename))
                    design.bg_image = bg_image.filename

            db.session.commit()
            flash('Sticker design updated successfully.', 'success')
        except ValueError:
            flash('Invalid input. Please ensure all fields contain valid numbers.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('main.sticker_design'))

    return render_template('sticker_design.html', design=design)