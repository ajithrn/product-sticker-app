from flask import render_template, redirect, url_for, flash, request, send_file, Response, current_app
from flask_login import login_required, current_user
from functools import wraps
from cryptography.fernet import Fernet, InvalidToken
import schedule
import base64
import csv
import io

from app import db
from app.models import Setting, StoreInfo, Product, ProductCategory, StickerDesign
from app.forms import StoreInfoForm
from .backups import read_auto_backup_time, create_backup, set_auto_backup_time
from .utils import encrypt_key, decrypt_key, generate_ingredients, generate_nutritional_facts, generate_allergen_info
from . import main

def store_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'store_admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/settings', methods=['GET', 'POST'])
@login_required
@store_admin_required
def settings():
    auto_backup_time = read_auto_backup_time()

    settings = Setting.query.first()
    if not settings:
        settings = Setting()
        db.session.add(settings)
        db.session.commit()

    store_info = StoreInfo.query.first()
    
    if store_info is None:
        store_info_form = StoreInfoForm()
    else:
        store_info_form = StoreInfoForm(obj=store_info)

    partial_api_key = None
    if settings.gpt_api_key_hash:
        try:
            decrypted_key = decrypt_key(settings.gpt_api_key_hash)
            # Generate a masked version with the last 4 characters visible
            partial_api_key = f'{"*" * 12}{decrypted_key[-4:]}'
        except Exception as e:
            partial_api_key = 'Error decoding key'

    if request.method == 'POST':
        if 'set_backup_time' in request.form:
            new_backup_time = request.form['time']
            if new_backup_time:
                try:
                    schedule.clear()  # Clear existing schedule
                    schedule.every().day.at(new_backup_time).do(create_backup)
                    set_auto_backup_time(new_backup_time)
                    flash('Automatic backup scheduled successfully.', 'success')
                except Exception as e:
                    flash('Error scheduling automatic backup.', 'danger')
            else:
                flash('Please enter a valid time for automatic backup.', 'danger')
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
        elif 'set_gpt_key' in request.form:
            gpt_api_key = request.form['gpt_api_key']
            if gpt_api_key and gpt_api_key != partial_api_key:
                # Encrypt the API key using the SECRET_KEY from the config
                encrypted_key = encrypt_key(gpt_api_key)
                settings.gpt_api_key_hash = encrypted_key
                db.session.commit()
                flash('OpenAI API key saved securely.', 'success')
        
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html', auto_backup_time=auto_backup_time, store_info_form=store_info_form, store_info=store_info, partial_api_key=partial_api_key)

@main.route('/tools/import-export', methods=['GET', 'POST'])
@login_required
@store_admin_required
def import_export():
    if request.method == 'POST':
        if 'export' in request.form:
            export_type = request.form.get('export_type')
            if export_type == 'product_categories':
                return export_product_and_categories()
            elif export_type == 'sticker_design':
                return export_data(StickerDesign, 'sticker_design.csv')
            else:
                flash('Invalid export type selected.', 'danger')
        elif 'import' in request.form:
            import_type = request.form.get('import_type')
            file = request.files.get('file')
            auto_generate = request.form.get('auto_generate') == 'on'
            if file and file.filename.endswith('.csv'):
                try:
                    data = file.read().decode('utf-8')
                    if import_type == 'product_categories':
                        import_product_and_categories(io.StringIO(data), auto_generate)
                    elif import_type == 'sticker_design':
                        import_data(StickerDesign, io.StringIO(data), sticker_design_mapper)
                    else:
                        flash('Invalid import type selected.', 'danger')
                    flash(f'{import_type.replace("_", " ").capitalize()} data imported successfully.', 'success')
                except Exception as e:
                    flash(f'Error importing data: {e}', 'danger')
            else:
                flash('Please upload a valid CSV file.', 'danger')
        return redirect(url_for('main.import_export'))
    return render_template('import_export.html')

def export_product_and_categories():
    products = Product.query.all()
    categories_map = {category.id: category.name for category in ProductCategory.query.all()}
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    
    headers = ['name', 'category', 'rate', 'net_weight', 'shelf_life', 'ingredients', 'nutritional_facts', 'allergen_information']
    writer.writerow(headers)
    
    for product in products:
        category_name = categories_map.get(product.category_id, 'Uncategorized')
        writer.writerow([product.name, category_name, product.rate, product.net_weight, product.shelf_life, product.ingredients, product.nutritional_facts, product.allergen_information])
    
    csv_output.seek(0)
    return Response(
        csv_output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=products_and_categories.csv"}
    )

def import_product_and_categories(data_stream, auto_generate):
    reader = csv.DictReader(data_stream)
    api_key = get_api_key() if auto_generate else None

    for row in reader:
        category_name = row['category']

        category = ProductCategory.query.filter_by(name=category_name).first()
        if not category:
            category = ProductCategory(name=category_name)
            db.session.add(category)
            db.session.commit()

        product = Product(
            name=row['name'],
            category_id=category.id,
            rate=row['rate'],
            net_weight=row['net_weight'],
            shelf_life=row['shelf_life'],
            ingredients=row.get('ingredients', ''),
            nutritional_facts=row.get('nutritional_facts', ''),
            allergen_information=row.get('allergen_information', '')
        )
        db.session.add(product)
        db.session.commit()

        if auto_generate and api_key:
            if not product.ingredients:
                product.ingredients = generate_ingredients(product.name, api_key)
                db.session.commit()

            if not product.nutritional_facts:
                product.nutritional_facts = generate_nutritional_facts(product.ingredients, api_key)
                db.session.commit()

            if not product.allergen_information:
                product.allergen_information = generate_allergen_info(product.ingredients, api_key)
                db.session.commit()

def export_data(model, filename, csv_headers=None):
    data = model.query.all()
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)

    if csv_headers:
        writer.writerow(csv_headers)
    else:
        writer.writerow([column.name for column in model.__mapper__.columns])

    for item in data:
        writer.writerow([getattr(item, column.name) for column in model.__mapper__.columns])

    csv_output.seek(0)
    return Response(
        csv_output,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def import_data(model, data_stream, mapper):
    reader = csv.DictReader(data_stream)
    for row in reader:
        item = mapper(row)
        db.session.add(item)
    db.session.commit()

def sticker_design_mapper(row):
    return StickerDesign(
        id=row['id'],
        page_size=row['page_size'],
        product_name_position=row['product_name_position'],
        mrp_position=row['mrp_position'],
        net_weight_position=row['net_weight_position'],
        mfg_date_position=row['mfg_date_position'],
        exp_date_position=row['exp_date_position'],
        batch_no_position=row['batch_no_position'],
        ingredients_position=row['ingredients_position'],
        nutritional_facts_position=row['nutritional_facts_position'],
        allergen_info_position=row['allergen_info_position'],
        heading_font_size=row['heading_font_size'],
        content_font_size=row['content_font_size'],
        bg_image=row['bg_image'],
        use_bg_image=row['use_bg_image']
    )
