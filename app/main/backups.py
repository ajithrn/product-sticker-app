from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from . import main
from app import db
import os
import csv
from datetime import datetime
import schedule
import time
from threading import Thread
from dotenv import load_dotenv
import subprocess
from .decorators import store_admin_required
import sqlalchemy as sa

# Load environment variables from .env file
load_dotenv()

# Determine the backup directory based on the environment
if os.environ.get('DOCKER_ENV') == 'true':
    BACKUP_DIR = '/app/backups'
else:
    BACKUP_DIR = os.path.join(os.getcwd(), 'backups')

BACKUP_LOG_FILE = os.path.join(BACKUP_DIR, 'backup_log.csv')

# PostgreSQL connection details
DB_NAME = os.getenv('POSTGRES_DB', 'product_sticker_app')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost' if not os.getenv('DOCKER_ENV') else 'db')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

if not os.path.exists(BACKUP_LOG_FILE):
    with open(BACKUP_LOG_FILE, 'w', newline='') as csvfile:
        log_writer = csv.writer(csvfile)
        log_writer.writerow(["type", "filename", "timestamp"])

def create_backup():
    """Create a PostgreSQL database backup using pg_dump"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_{timestamp}.sql'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        # Set PostgreSQL password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD

        # Create backup using pg_dump in plain SQL format
        command = [
            'pg_dump',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-U', DB_USER,
            '-F', 'p',  # Plain SQL format
            '-v',  # Verbose
            '--no-owner',  # Skip ownership commands
            '--no-privileges',  # Skip privilege commands
            '-f', backup_path,
            DB_NAME
        ]

        result = subprocess.run(command, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            log_backup(backup_filename, timestamp)
            current_app.logger.info(f'Backup created: {backup_filename}')
            return True
        else:
            current_app.logger.error(f'Error during backup: {result.stderr}')
            return False
    except Exception as e:
        current_app.logger.error(f'Error during backup creation: {e}')
        return False

def restore_backup_file(backup_path):
    """Restore a PostgreSQL database from backup"""
    try:
        # Set PostgreSQL password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD

        # Close all SQLAlchemy connections
        db.session.remove()
        db.engine.dispose()

        # Connect to postgres database to handle connection termination
        postgres_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
        engine = sa.create_engine(postgres_url)
        
        with engine.connect() as conn:
            # Terminate other connections
            conn.execute(sa.text(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE "
                f"datname = '{DB_NAME}' AND pid <> pg_backend_pid()"
            ))
            conn.execute(sa.text("COMMIT"))

        # Drop and recreate database
        with engine.connect() as conn:
            conn.execute(sa.text("COMMIT"))
            conn.execute(sa.text(f"DROP DATABASE IF EXISTS {DB_NAME}"))
            conn.execute(sa.text("COMMIT"))
            conn.execute(sa.text(f"CREATE DATABASE {DB_NAME}"))
            conn.execute(sa.text("COMMIT"))

        engine.dispose()

        # Wait a moment for connections to fully close
        time.sleep(2)

        # Restore using psql
        restore_command = [
            'psql',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-U', DB_USER,
            '-d', DB_NAME,
            '-v', 'ON_ERROR_STOP=1',  # Stop on first error
            '-f', backup_path
        ]

        result = subprocess.run(restore_command, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            current_app.logger.info('Backup restored successfully')
            return True, None
        else:
            current_app.logger.error(f'Error restoring backup: {result.stderr}')
            return False, result.stderr

    except Exception as e:
        current_app.logger.error(f'Error during backup restore: {e}')
        return False, str(e)
    finally:
        # Ensure we reconnect to the database
        db.session.remove()
        db.engine.dispose()

def log_backup(backup_filename, timestamp):
    with open(BACKUP_LOG_FILE, 'a', newline='') as csvfile:
        log_writer = csv.writer(csvfile)
        log_writer.writerow(["backup", backup_filename, timestamp])

def read_backup_logs():
    backups = []
    auto_backup_time = None
    if os.path.exists(BACKUP_LOG_FILE):
        with open(BACKUP_LOG_FILE, 'r') as csvfile:
            log_reader = csv.reader(csvfile)
            next(log_reader)  # Skip header
            for row in log_reader:
                if row[0] == "backup":
                    backups.append((row[1], datetime.strptime(row[2], '%Y%m%d_%H%M%S')))
                elif row[0] == "auto_backup_time":
                    auto_backup_time = row[2]
    # Sort backups by date in descending order
    backups.sort(key=lambda x: x[1], reverse=True)
    return backups, auto_backup_time

def read_auto_backup_time():
    _, auto_backup_time = read_backup_logs()
    return auto_backup_time

def set_auto_backup_time(time):
    updated_rows = []
    backup_exists = False

    if os.path.exists(BACKUP_LOG_FILE):
        with open(BACKUP_LOG_FILE, 'r', newline='') as csvfile:
            log_reader = csv.reader(csvfile)
            updated_rows.append(next(log_reader))  # Add header
            for row in log_reader:
                if row[0] == "auto_backup_time":
                    updated_rows.append(["auto_backup_time", "", time])
                    backup_exists = True
                else:
                    updated_rows.append(row)

    if not backup_exists:
        updated_rows.append(["auto_backup_time", "", time])

    with open(BACKUP_LOG_FILE, 'w', newline='') as csvfile:
        log_writer = csv.writer(csvfile)
        log_writer.writerows(updated_rows)

@main.route('/backups')
@login_required
@store_admin_required
def list_backups():
    """
    View function for listing all backups.
    Only store admin can access backups.
    """
    try:
        backups, _ = read_backup_logs()
        return render_template('backups.html', backups=backups)
    except Exception as e:
        current_app.logger.error(f'Error listing backups: {e}')
        flash('Error loading backup list.', 'danger')
        return redirect(url_for('main.index'))

@main.route('/backups/restore/<backup_name>', methods=['POST'])
@login_required
@store_admin_required
def restore_backup(backup_name):
    """
    View function for restoring a backup.
    Only store admin can restore backups.
    """
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        success, error = restore_backup_file(backup_path)
        
        if success:
            flash('Backup restored successfully.', 'success')
        else:
            flash(f'Error restoring backup: {error}', 'danger')
    except Exception as e:
        current_app.logger.error(f'Error during backup restore: {e}')
        flash(f'Error restoring backup: {str(e)}', 'danger')
    
    return redirect(url_for('main.list_backups'))

@main.route('/backups/delete/<backup_name>', methods=['POST'])
@login_required
@store_admin_required
def delete_backup(backup_name):
    """
    View function for deleting a backup.
    Only store admin can delete backups.
    """
    try:
        os.remove(os.path.join(BACKUP_DIR, backup_name))
        backups, auto_backup_time = read_backup_logs()
        backups = [backup for backup in backups if backup[0] != backup_name]
        
        with open(BACKUP_LOG_FILE, 'w', newline='') as csvfile:
            log_writer = csv.writer(csvfile)
            log_writer.writerow(["type", "filename", "timestamp"])  # Write header
            for backup in backups:
                log_writer.writerow(["backup", backup[0], backup[1].strftime('%Y%m%d_%H%M%S')])
            if auto_backup_time:
                log_writer.writerow(["auto_backup_time", "", auto_backup_time])
        
        flash('Backup deleted successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f'Error deleting backup: {e}')
        flash(f'Error deleting backup: {str(e)}', 'danger')
    
    return redirect(url_for('main.list_backups'))

@main.route('/backups/create', methods=['POST'])
@login_required
@store_admin_required
def manual_create_backup():
    """
    View function for manually creating a backup.
    Only store admin can create backups.
    """
    try:
        if create_backup():
            flash('Backup created successfully.', 'success')
        else:
            flash('Error creating backup.', 'danger')
    except Exception as e:
        current_app.logger.error(f'Error creating backup: {e}')
        flash(f'Error creating backup: {str(e)}', 'danger')
    
    return redirect(url_for('main.list_backups'))

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def init_scheduler(app):
    """Initialize the backup scheduler"""
    try:
        auto_backup_time = read_auto_backup_time()
        if auto_backup_time:
            schedule.every().day.at(auto_backup_time).do(create_backup)
            current_app.logger.info(f"Scheduled automatic backups at {auto_backup_time}")

        thread = Thread(target=run_schedule)
        thread.daemon = True
        thread.start()
    except Exception as e:
        current_app.logger.error(f'Error initializing scheduler: {e}')

def start_scheduler(app):
    """Start the backup scheduler"""
    with app.app_context():
        init_scheduler(app)
