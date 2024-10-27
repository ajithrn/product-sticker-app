from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import (
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os

from app import db
from app.models import User, Product, ProductCategory, PrintJob, StoreInfo, StickerDesign
from app.forms import LoginForm, RegisterForm, StoreInfoForm

from . import main

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
            # Handle clear background image
            if 'clear_bg_image' in request.form:
                if design.bg_image:
                    bg_path = os.path.join(current_app.root_path, 'static', design.bg_image)
                    if os.path.exists(bg_path):
                        os.remove(bg_path)
                    design.bg_image = None
                    design.use_bg_image = False
                db.session.commit()
                flash('Background image cleared successfully.', 'success')
                return redirect(url_for('main.sticker_design'))

            # Update page size (now sticker size)
            design.page_size = {
                "width": float(request.form['sticker_size_width']),
                "height": float(request.form['sticker_size_height']),
                "margin": float(request.form['sticker_size_margin'])
            }

            # Update printer settings
            design.printer_type = request.form['printer_type']
            design.paper_size = request.form['paper_size']
            design.paper_orientation = request.form['paper_orientation']

            if design.paper_size == 'custom':
                design.custom_paper_width = float(request.form['custom_paper_width'])
                design.custom_paper_height = float(request.form['custom_paper_height'])
            else:
                design.custom_paper_width = None
                design.custom_paper_height = None

            # Update store info positions and toggles
            store_elements = ['store_logo', 'store_name', 'store_address', 'store_phone', 'store_gst', 'store_fssai', 'store_email']
            for element in store_elements:
                position = {
                    "top": float(request.form[f'{element}_position_top']),
                    "left": float(request.form[f'{element}_position_left']),
                    "max_width": float(request.form[f'{element}_position_max_width']),
                    "font_size": float(request.form.get(f'{element}_position_font_size', design.content_font_size))
                }
                setattr(design, f'{element}_position', position)
                setattr(design, f'print_{element}', request.form.get(f'print_{element}', 'off') == 'on')

            # Update product info positions
            product_elements = ['product_name', 'mrp', 'net_weight', 'mfg_date', 'exp_date', 'batch_no', 'ingredients', 'nutritional_facts', 'allergen_info']
            for element in product_elements:
                position = {
                    "top": float(request.form[f'{element}_position_top']),
                    "left": float(request.form[f'{element}_position_left']),
                    "max_width": float(request.form[f'{element}_position_max_width']),
                    "font_size": float(request.form.get(f'{element}_position_font_size', design.content_font_size))
                }
                setattr(design, f'{element}_position', position)

            design.heading_font_size = float(request.form['heading_font_size'])
            design.content_font_size = float(request.form['content_font_size'])
            design.use_bg_image = request.form.get('use_bg_image', 'off') == 'on'

            # Update heading options
            for heading in ['nutritional', 'allergen', 'ingredients']:
                print_heading = request.form.get(f'print_{heading}_heading', 'off') == 'on'
                setattr(design, f'print_{heading}_heading', print_heading)
                setattr(design, f'{heading}_heading_text', request.form.get(f'{heading}_heading_text', ''))
                setattr(design, f'{heading}_heading_font_size', float(request.form.get(f'{heading}_heading_font_size', design.heading_font_size)))

            # Handle background image upload
            if 'bg_image' in request.files:
                bg_image = request.files['bg_image']
                if bg_image.filename != '':
                    # Delete old background image if it exists
                    if design.bg_image:
                        old_bg_path = os.path.join(current_app.root_path, 'static', design.bg_image)
                        if os.path.exists(old_bg_path):
                            os.remove(old_bg_path)
                    
                    # Create the uploads directory if it doesn't exist
                    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'backgrounds')
                    os.makedirs(uploads_dir, exist_ok=True)
                    
                    # Save the file to the uploads directory
                    filename = secure_filename(bg_image.filename)
                    bg_image.save(os.path.join(uploads_dir, filename))
                    design.bg_image = os.path.join('uploads', 'backgrounds', filename)

            db.session.commit()
            flash('Sticker design updated successfully.', 'success')
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid input. Please ensure all fields contain valid numbers. Error: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('main.sticker_design'))

    return render_template('sticker_design.html', design=design)
