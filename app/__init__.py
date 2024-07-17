from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

admin_initialized = False  # Flag to ensure initialization runs once

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Import User model locally to avoid circular imports
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def create_super_admin():
        """Create the super admin user if it doesn't exist."""
        global admin_initialized
        if not admin_initialized:
            admin_username = os.getenv('SUPER_ADMIN_USERNAME')
            admin_email = os.getenv('SUPER_ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.getenv('SUPER_ADMIN_PASSWORD')

            if not admin_username or not admin_password:
                raise ValueError("SUPER_ADMIN_USERNAME and SUPER_ADMIN_PASSWORD must be set in .env")

            existing_admin = User.query.filter_by(username=admin_username).first()
            if not existing_admin:
                hashed_password = generate_password_hash(admin_password)
                super_admin = User(
                    username=admin_username,
                    email=admin_email,
                    password=hashed_password,
                    role='store_admin'
                )
                db.session.add(super_admin)
                db.session.commit()
                print("Super admin user created successfully.")
            admin_initialized = True  # Set flag to True after first execution

    return app
