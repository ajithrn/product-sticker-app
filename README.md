# Product and Sticker Management App

This is a web application for managing food products and printing stickers for them. The application allows you to:
- Add, edit, duplicate, and delete products and categories.
- Print stickers with detailed product information.
- View an analytics dashboard with insights on print jobs and product statistics.
- Manage users with different roles (Store Admin and Staff).
- Pagination for product, category, print job, and user listings.
- Manage database backups, including automatic scheduled backups.

## Features
- User authentication (register, login, logout)
- Product and category management with pagination
- Individual sticker printing from the product page
- Multi-product sticker printing with AJAX search, inline editing, and batch printing.
- Analytics dashboard
- User management (Store Admin and Staff roles)
- Profile management
- Store Info and Customization Options
- Auto Backup Options
- Pagination for products, categories, print jobs, and users
- Database backup management:
  - Manual and automatic scheduled backups
  - View, restore, and delete backups
  - Store backup logs and settings in a CSV file for reliability

## Setup Instructions

### Prerequisites
- Python 3.6+
- Pip (Python package installer)
- Virtual environment (recommended)
- Docker and Docker Compose (for containerized deployment)

### Installation

1. **Clone the repository**:

   ```sh
   git clone https://github.com/ajithrn/product-sticker-app.git
   cd product-sticker-app
   ```

2. **Create and activate a virtual environment**:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages**:

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up the environment variables**:
   Create a `.env` file in the root directory and add the following content:
   ```plaintext
   SECRET_KEY=your-secret-key #Make sure its length is 32
   DATABASE_URL=sqlite:///instance/product_sticker_app.db
   DB_NAME=product_sticker_app.db
   SUPER_ADMIN_USERNAME=admin
   SUPER_ADMIN_PASSWORD=admin_password
   SUPER_ADMIN_EMAIL=admin@example.com
   FLASK_ENV=development
   FLASK_DEBUG=1
   ```

5. **Initialize the database**:
   ```sh
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

6. **Run the application**:
   ```sh
   flask run
   ```

7. **Open your web browser and navigate to** `http://127.0.0.1:5000/`.

## Running with Docker

To run this application using Docker, follow these steps:

1. Make sure you have Docker and Docker Compose installed on your system.

2. Build the Docker image:
   ```
   docker-compose build
   ```

3. Run the Docker container:
   ```
   docker-compose up
   ```

4. The application will be available at `http://localhost:5000`.

5. To stop the container, use CTRL+C in the terminal where it's running, or run:
   ```
   docker-compose down
   ```

## Docker and Database Migrations

The Docker setup is configured to automatically apply any pending database migrations when the container starts. This means:

1. When you run `docker-compose up`, it will automatically apply any pending migrations before starting the Flask application.

2. If you make changes to your database models:
   a. Create a new migration:
      ```
      docker-compose run web flask db migrate -m "Description of changes"
      ```
   b. The next time you run `docker-compose up`, these migrations will be automatically applied.

3. If you need to apply migrations manually, you can run:
   ```
   docker-compose run web flask db upgrade
   ```

This setup ensures that your database schema is always up-to-date with your model definitions when running the application in Docker.

## Development with Live Reloading
For live reloading during development, ensure that you set the `FLASK_ENV` environment variable to `development`. The application will automatically watch for changes in your files and reload the browser as needed.

1. **Set the environment variable**:
    - On Unix-based systems (Linux, macOS):
      ```sh
      export FLASK_ENV=development
      ```
    - On Windows:
      ```sh
      set FLASK_ENV=development
      ```

2. **Run the application**:
    ```sh
    python run.py
    ```

This will enable the Flask development server with live reloading when code changes are detected.

## Production Mode
For production, make sure the `FLASK_ENV` environment variable is set to `production` (or simply not set to `development`). The application will run normally without live reloading.

```sh
export FLASK_ENV=production
python run.py # Or flask run
```

## PDF Generation and Printing
Stickers are generated as PDFs with custom dimensions (85mm x 95mm) including margins (2.5mm each side) and sent directly to the printer. Ensure your printer is set up correctly and you have the necessary permissions. Generates stickers will open in new tab and users can print from there.


## Usage
- Register a new user account or use the default super admin account.
- Log in with the created account or super admin credentials.
- Once login change the super admin password.
- Navigate through the categories, products, and print stickers pages.
- Use the analytics dashboard to view insights.
- Store Admin can manage users and assign roles.
- Manage database backups via the `/backups` route.

## Technologies Used
- Flask (Python web framework)
- SQLAlchemy (ORM)
- Flask-Login (User authentication)
- Flask-WTF (Form handling)
- Flask-Bcrypt (Password hashing)
- Flask-Migrate (Database migrations)
- ReportLab (PDF generation)
- Flask-Paginate (Pagination)
- Bootstrap (CSS framework)
- pywin32 (Windows printing)
- pycups (Linux/Mac printing)
- schedule (Python library for scheduling tasks)
- LiveReload (Development live reloading)
- Docker (Containerization)

## License
This project is licensed under the MIT License.