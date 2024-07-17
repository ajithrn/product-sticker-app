from app import create_app, db
from flask_migrate import Migrate
from app.models import User, Product, PrintJob, ProductCategory
from app.main.backups import start_scheduler
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
    # Use environment variable for port or fallback to port 5000
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Make the server publicly available

    if app.debug:
        # Set up livereload server only in debug mode
        from livereload import Server
        server = Server(app.wsgi_app)
        server.watch('**/*.html')
        server.watch('**/*.css')
        server.watch('**/*.js')
        server.serve(port=port, host=host, restart_delay=1)
    else:
        app.run(port=port, host=host)

if __name__ == '__main__':
    start_app()
