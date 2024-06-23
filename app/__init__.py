from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash

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
    def before_request_func():
        global admin_initialized
        if not admin_initialized:
            with app.app_context():
                admin = User.query.filter_by(role='store_admin').first()
                if not admin:
                    print("No admin user found. Please create an admin user.")
                    from getpass import getpass

                    admin_username = input('Enter admin username: ')
                    admin_email = input('Enter admin email: ')
                    admin_password = getpass('Enter admin password: ')
                    hashed_password = generate_password_hash(admin_password)
                    new_admin = User(
                        username=admin_username,
                        email=admin_email,
                        password=hashed_password,
                        role='store_admin'
                    )
                    db.session.add(new_admin)
                    db.session.commit()
                    print("Admin user created successfully.")
            admin_initialized = True

    return app
