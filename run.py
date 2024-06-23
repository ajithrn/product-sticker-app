from app import create_app, db
from flask_migrate import Migrate
from app.models import User, Product, PrintJob, ProductCategory
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = create_app()
migrate = Migrate(app, db)  # Initialize migrate with app and db

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Product': Product, 'PrintJob': PrintJob, 'ProductCategory': ProductCategory}

def start_app():
    # Set environment variables for development
    if os.getenv('FLASK_ENV') == 'development':
        app.debug = True
        # Use environment variable for port or fallback to port 5000
        port = int(os.environ.get('PORT', 5000))
        host = '127.0.0.1'
        # Set up livereload server
        from livereload import Server
        server = Server(app.wsgi_app)
        server.watch('**/*.html')  # Watch all HTML files for changes
        server.watch('**/*.css')   # Optional: watch CSS files
        server.watch('**/*.js')    # Optional: watch JS files
        server.serve(port=port, host=host, restart_delay=1)
    else:
        app.debug = False
        # Use environment variable for port or fallback to port 5000
        port = int(os.environ.get('PORT', 5000))
        app.run(port=port)

if __name__ == '__main__':
    start_app()
