# Product and Sticker Management App

This is a web application for managing food products and printing stickers for them. The application allows you to:
- Add, edit, duplicate, and delete products and categories.
- Print stickers with detailed product information.
- View an analytics dashboard with insights on print jobs and product statistics.
- Manage users with different roles (Store Admin and Staff).
- Pagination for product, category, print job, and user listings.

## Features
- User authentication (register, login, logout)
- Product and category management with pagination
- Individual sticker printing from product page
- Multi-product sticker printing with AJAX search, inline editing, and batch printing.
- Analytics dashboard
- User management (Store Admin and Staff roles)
- Profile management
- Pagination for products, categories, print jobs, and users

## Setup Instructions

### Prerequisites
- Python 3.6+
- Pip (Python package installer)
- Virtual environment (recommended)

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
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///your-database.db
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
Stickers are generated as PDFs with custom dimensions (85mm x 95mm) including margins (2.5mm each side) and sent directly to the printer. Ensure your printer is set up correctly and you have the necessary permissions.

### For Windows:
Ensure you have `pywin32` installed:
```sh
pip install pywin32
```
Make sure your default printer is set up in the system settings.

### For Linux/Mac:
Ensure CUPS is correctly installed and configured, and you have `pycups` installed:
```sh
pip install pycups
```

## Usage
- Register a new user account.
- Log in with the created account.
- Navigate through the categories, products, and print stickers pages.
- Use the analytics dashboard to view insights.
- Store Admin can manage users and assign roles.

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
- p0ywin32 (Windows printing)
- pycups (Linux/Mac printing)
- LiveReload (Development live reloading)

## License
This project is licensed under the MIT License.