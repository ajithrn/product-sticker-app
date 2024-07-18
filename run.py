from app import create_app, db
from flask_migrate import Migrate
from app.models import User, Product, PrintJob, ProductCategory
from app.main.backups import start_scheduler
from dotenv import load_dotenv
import os
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file
load_dotenv()

# Create app with the appropriate configuration
app = create_app(os.getenv('FLASK_ENV') or 'default')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Product': Product, 'PrintJob': PrintJob, 'ProductCategory': ProductCategory}

def start_app():
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'

    # Check both FLASK_ENV and FLASK_DEBUG
    is_debug = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1'

    if is_debug:
        from livereload import Server
        server = Server(app.wsgi_app)
        server.watch('**/*.*')
        server.serve(port=port, host=host, restart_delay=1)
    else:
        app.run(port=port, host=host)

if __name__ == '__main__':
    start_app()
