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
- Multi-product sticker printing with AJAX search, inline editing, and batch printing
- Analytics dashboard
- User management (Store Admin and Staff roles)
- Profile management
- Store Info and Customization Options
- Auto Backup Options
- Pagination for products, categories, print jobs, and users
- AI Integration to auto generate Ingredients, Nutritional Facts and Allergen Information
- Database backup management:
  - Manual and automatic scheduled backups
  - View, restore, and delete backups
  - Store backup logs and settings in a CSV file for reliability

## Prerequisites

- Docker
- Docker Compose

That's it! You don't need Python, PostgreSQL, or any other dependencies installed locally since everything runs inside Docker containers.

## Quick Start

1. **Clone the repository**:
   ```sh
   git clone https://github.com/ajithrn/product-sticker-app.git
   cd product-sticker-app
   ```

2. **Set up environment variables**:
   Copy `.env.example` to `.env`:
   ```sh
   cp .env.example .env
   ```
   
   The following environment variables are available:

   ```plaintext
   # Required - Must be set in .env
   SECRET_KEY=your-secret-key-here        # Application secret key
   SUPER_ADMIN_USERNAME=admin             # Initial admin username
   SUPER_ADMIN_PASSWORD=admin_password    # Initial admin password
   SUPER_ADMIN_EMAIL=admin@example.com    # Initial admin email

   # Optional - Have defaults in Docker
   FLASK_ENV=development                  # development or production (default: development)
   POSTGRES_USER=postgres                 # Database user (default: postgres)
   POSTGRES_PASSWORD=postgres             # Database password (default: postgres)
   POSTGRES_DB=product_sticker_app        # Database name (default: product_sticker_app)
   ```

   Note: The database connection URL is automatically configured by Docker Compose, you don't need to set DATABASE_URL manually.

3. **Start the application**:
   ```sh
   docker-compose up --build
   ```

4. **Access the application**:
   Open your browser and navigate to `http://localhost:5000`

That's it! The application is now running with:
- Flask web application
- PostgreSQL database
- Automatic database migrations
- Live code reloading for development

## Development Workflow

### Starting/Stopping the Application

- **Start containers**:
  ```sh
  docker-compose up
  ```

- **Start in background**:
  ```sh
  docker-compose up -d
  ```

- **Stop containers**:
  ```sh
  docker-compose down
  ```

- **View logs**:
  ```sh
  docker-compose logs -f
  ```

### Database Management

Database migrations are handled automatically when the container starts. If you make changes to the database models:

1. **Create a migration**:
   ```sh
   docker-compose exec web flask db migrate -m "Description of changes"
   ```

2. **Apply migration**:
   ```sh
   docker-compose exec web flask db upgrade
   ```

### Backup Management

The application includes a robust backup system for PostgreSQL:
- Backups are stored in a dedicated Docker volume
- Manual backups can be created through the web interface
- Automatic scheduled backups can be configured
- Backups can be viewed, restored, and managed through the web interface

### Development Features

- **Live Reloading**: Code changes are automatically detected and the application reloads
- **Debug Mode**: Detailed error pages and debugging tools are enabled
- **Volume Mounting**: Local files are mounted into the container for immediate updates

## Production Deployment

For production deployment:

1. Update `.env` file:
   ```plaintext
   # Required settings
   FLASK_ENV=production
   SECRET_KEY=<strong-secret-key>
   SUPER_ADMIN_USERNAME=<admin-username>
   SUPER_ADMIN_PASSWORD=<secure-password>
   SUPER_ADMIN_EMAIL=<admin-email>

   # Optional - Using defaults
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=product_sticker_app
   ```

2. Start the containers:
   ```sh
   docker-compose up -d
   ```

## PDF Generation and Printing

Stickers are generated as PDFs with custom dimensions (85mm x 95mm) including margins (2.5mm each side) and sent directly to the printer. Generated stickers will open in a new tab for printing.

## Technologies Used

- **Backend**:
  - Flask (Python web framework)
  - PostgreSQL (Database)
  - SQLAlchemy (ORM)
  - Flask-Login (Authentication)
  - Flask-WTF (Forms)
  - Flask-Migrate (Database migrations)
  - ReportLab (PDF generation)

- **Frontend**:
  - Bootstrap (CSS framework)
  - JavaScript/jQuery
  - AJAX for dynamic updates

- **Infrastructure**:
  - Docker (Containerization)
  - Docker Compose (Container orchestration)

## License

This project is licensed under the MIT License.
