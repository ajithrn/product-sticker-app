from flask import render_template, redirect, url_for, flash, request, send_file, Response, current_app
from flask_login import login_required, current_user
from cryptography.fernet import Fernet, InvalidToken
import schedule
import base64
import csv
import io
import json
from decimal import Decimal

from app import db
from app.models import Setting, StoreInfo, Product, ProductCategory, StickerDesign
from app.forms import StoreInfoForm
from .backups import read_auto_backup_time, create_backup, set_auto_backup_time
from .utils import encrypt_key, decrypt_key, generate_ingredients, generate_nutritional_facts, generate_allergen_info
from .decorators import store_admin_required
from . import main

def to_bool(value):
    return str(value).lower() in ('true', 't', 'yes', 'y', '1')

def to_float(value):
    try:
        return float(value) if value else None
    except ValueError:
        return None

def to_decimal(value):
    try:
        return Decimal(str(value)) if value else Decimal('0.00')
    except (ValueError, TypeError):
        return Decimal('0.00')

def to_json(value):
    if not value:
        return None
    try:
        valid_json = value.replace("'", '"')
        return json.loads(valid_json)
    except json.JSONDecodeError:
        return None

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
            partial_api_key = f'{"*" * 12}{decrypted_key[-4:]}'
        except Exception as e:
            partial_api_key = 'Error decoding key'

    if request.method == 'POST':
        if 'set_backup_time' in request.form:
            new_backup_time = request.form['time']
            if new_backup_time:
                try:
                    schedule.clear() 
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
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    
    headers = ['name', 'category', 'rate', 'net_weight', 'shelf_life', 'ingredients', 'nutritional_facts', 'allergen_information']
    writer.writerow(headers)
    
    for product in products:
        category_name = product.category.name if product.category else 'Uncategorized'
        writer.writerow([
            product.name,
            category_name,
            str(product.rate),  # Convert Decimal to string for CSV
            product.net_weight,
            product.shelf_life,
            product.ingredients,
            product.nutritional_facts,
            product.allergen_information
        ])
    
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
        try:
            category_name = row['category']
            category = ProductCategory.query.filter_by(name=category_name).first()
            if not category:
                category = ProductCategory(name=category_name)
                db.session.add(category)
                db.session.commit()

            # Convert rate to Decimal
            rate = to_decimal(row['rate'])
            
            product = Product(
                name=row['name'],
                category_id=category.id,
                rate=rate,
                net_weight=row['net_weight'],
                shelf_life=int(row['shelf_life']),
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

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error importing product {row.get('name')}: {str(e)}")
            flash(f"Error importing product {row.get('name')}: {str(e)}", 'danger')

def export_data(model, filename, csv_headers=None):
    data = model.query.all()
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)

    if csv_headers:
        writer.writerow(csv_headers)
    else:
        writer.writerow([column.name for column in model.__mapper__.columns])

    for item in data:
        row = []
        for column in model.__mapper__.columns:
            value = getattr(item, column.name)
            if isinstance(value, Decimal):
                value = str(value)
            elif isinstance(value, dict):
                value = json.dumps(value)
            row.append(value)
        writer.writerow(row)

    csv_output.seek(0)
    return Response(
        csv_output,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def import_data(model, data_stream, mapper):
    reader = csv.DictReader(data_stream)
    for row in reader:
        try:
            mapped_data = mapper(row)
            existing_item = model.query.get(mapped_data.id)

            if existing_item:
                for key, value in mapped_data.__dict__.items():
                    if key != '_sa_instance_state':
                        setattr(existing_item, key, value)
            else:
                db.session.add(mapped_data)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error importing data: {str(e)}")
            flash(f"Error importing data: {str(e)}", 'danger')

def sticker_design_mapper(row):
    return StickerDesign(
        id=int(row['id']),  
        page_size=to_json(row['page_size']),
        product_name_position=to_json(row['product_name_position']),
        mrp_position=to_json(row['mrp_position']),
        net_weight_position=to_json(row['net_weight_position']),
        mfg_date_position=to_json(row['mfg_date_position']),
        exp_date_position=to_json(row['exp_date_position']),
        batch_no_position=to_json(row['batch_no_position']),
        ingredients_position=to_json(row['ingredients_position']),
        nutritional_facts_position=to_json(row['nutritional_facts_position']),
        allergen_info_position=to_json(row['allergen_info_position']),
        heading_font_size=to_float(row['heading_font_size']),
        content_font_size=to_float(row['content_font_size']),
        bg_image=row['bg_image'],
        use_bg_image=to_bool(row['use_bg_image']),
        print_nutritional_heading=to_bool(row['print_nutritional_heading']),
        print_allergen_heading=to_bool(row['print_allergen_heading']),
        print_ingredients_heading=to_bool(row['print_ingredients_heading']),
        nutritional_heading_text=row['nutritional_heading_text'],
        allergen_heading_text=row['allergen_heading_text'],
        ingredients_heading_text=row['ingredients_heading_text'],
        nutritional_heading_font_size=to_float(row['nutritional_heading_font_size']),
        allergen_heading_font_size=to_float(row['allergen_heading_font_size']),
        ingredients_heading_font_size=to_float(row['ingredients_heading_font_size']),
        mrp_font_size=to_float(row['mrp_font_size']),
        ingredients_font_size=to_float(row['ingredients_font_size']),
        allergen_info_font_size=to_float(row['allergen_info_font_size']),
        nutritional_facts_font_size=to_float(row['nutritional_facts_font_size']),
        printer_type=row['printer_type'],
        paper_size=row['paper_size'],
        custom_paper_width=to_float(row['custom_paper_width']),
        custom_paper_height=to_float(row['custom_paper_height']),
        paper_orientation=row['paper_orientation']
    )
