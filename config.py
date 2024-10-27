import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    
    # Use Docker database URL if in Docker environment, otherwise use local
    if os.environ.get('DOCKER_ENV') == 'true':
        SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@db:5432/product_sticker_app'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/product_sticker_app'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Choose the appropriate configuration based on the FLASK_ENV
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
