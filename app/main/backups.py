from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from . import main
from app import db
import os
import shutil
import csv
from datetime import datetime
import schedule
import time
from threading import Thread
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Determine the backup directory based on the environment
if os.environ.get('DOCKER_ENV') == 'true':
    BACKUP_DIR = os.path.join(os.getcwd(), '/app/backups')

BACKUP_DIR = os.path.join(os.getcwd(), 'backups')
BACKUP_LOG_FILE = os.path.join(BACKUP_DIR, 'backup_log.csv')
DB_NAME = os.getenv('DB_NAME', 'product_sticker_app.db')

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

if not os.path.exists(BACKUP_LOG_FILE):
    with open(BACKUP_LOG_FILE, 'w', newline='') as csvfile:
        log_writer = csv.writer(csvfile)
        log_writer.writerow(["type", "filename", "timestamp"])

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_{timestamp}.db'
    src = os.path.join(os.getcwd(), 'instance', DB_NAME)
    dest = os.path.join(BACKUP_DIR, backup_filename)

    try:
        shutil.copyfile(src, dest)
        log_backup(backup_filename, timestamp)
        print(f'Backup created: {backup_filename}')
    except Exception as e:
        print(f'Error during backup creation: {e}')

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
def list_backups():
    backups, _ = read_backup_logs()
    return render_template('backups.html', backups=backups)

@main.route('/backups/restore/<backup_name>', methods=['POST'])
@login_required
def restore_backup(backup_name):
    try:
        src = os.path.join(BACKUP_DIR, backup_name)
        dest = os.path.join(os.getcwd(), 'instance', DB_NAME)
        shutil.copyfile(src, dest)
        flash('Backup restored successfully.', 'success')
    except Exception as e:
        flash(f'Error restoring backup: {e}', 'danger')
    return redirect(url_for('main.list_backups'))

@main.route('/backups/delete/<backup_name>', methods=['POST'])
@login_required
def delete_backup(backup_name):
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
        flash(f'Error deleting backup: {e}', 'danger')
    return redirect(url_for('main.list_backups'))

@main.route('/backups/create', methods=['POST'])
@login_required
def manual_create_backup():
    create_backup()
    flash('Backup created successfully.', 'success')
    return redirect(url_for('main.list_backups'))

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    auto_backup_time = read_auto_backup_time()
    if request.method == 'POST':
        hour, minute = request.form['time'].split(':')
        schedule.clear()  # Clear existing schedule
        schedule.every().day.at(f"{hour}:{minute}").do(create_backup)

        # Store the scheduled time
        set_auto_backup_time(f"{hour}:{minute}")

        flash('Automatic backup scheduled.', 'success')
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html', auto_backup_time=auto_backup_time)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Initialize the scheduler
def init_scheduler(app):
    auto_backup_time = read_auto_backup_time()
    if auto_backup_time:
        schedule.every().day.at(auto_backup_time).do(create_backup)
        print(f"Scheduled automatic backups at {auto_backup_time}")

    thread = Thread(target=run_schedule)
    thread.daemon = True
    thread.start()

# Call this function when the app starts, not during initialization
def start_scheduler(app):
    with app.app_context():
        init_scheduler(app)
