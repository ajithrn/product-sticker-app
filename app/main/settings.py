from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from functools import wraps
from cryptography.fernet import Fernet, InvalidToken
import schedule
import base64

from app import db
from app.models import Setting, StoreInfo
from app.forms import StoreInfoForm
from .backups import read_auto_backup_time, create_backup
from . import main

def store_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'store_admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def ensure_fernet_key(secret_key):
    # Ensure secret_key is 32 bytes
    if len(secret_key) < 32:
        secret_key += '=' * (32 - len(secret_key))
    secret_key_bytes = base64.urlsafe_b64encode(secret_key.encode())
    return Fernet(secret_key_bytes)

def encrypt_key(key):
    cipher_suite = ensure_fernet_key(current_app.config['SECRET_KEY'])
    return cipher_suite.encrypt(key.encode()).decode()

def decrypt_key(encrypted_key):
    cipher_suite = ensure_fernet_key(current_app.config['SECRET_KEY'])
    return cipher_suite.decrypt(encrypted_key.encode()).decode()

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
            hour, minute = request.form['time'].split(':')
            schedule.clear()  # Clear existing schedule
            schedule.every().day.at(f"{hour}:{minute}").do(create_backup)

            # Store the scheduled time
            settings.auto_backup_time = f"{hour}:{minute}"
            db.session.commit()

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
        elif 'set_gpt_key' in request.form:
            gpt_api_key = request.form['gpt_api_key']
            if gpt_api_key and gpt_api_key != partial_api_key:
                # Encrypt the API key using the SECRET_KEY from the config
                encrypted_key = encrypt_key(gpt_api_key)
                settings.gpt_api_key_hash = encrypted_key
                db.session.commit()
                flash('GPT-3.5 API key saved securely.', 'success')
        
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html', auto_backup_time=auto_backup_time, store_info_form=store_info_form, store_info=store_info, partial_api_key=partial_api_key)